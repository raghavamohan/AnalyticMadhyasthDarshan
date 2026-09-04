#!/usr/bin/env python3
"""Verify generated PDFs and publish changed objects to Cloudflare R2."""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import fitz

from _common import BASE, configure_utf8_stdio
from _generated_pdf_inventory import (
    GeneratedPdfSpec,
    generated_pdf_specs,
    inventory_errors,
    spec_by_key,
)
from _presentation_pipeline import sha256_file
from _r2_s3 import R2S3Client, load_r2_config

CACHE_CONTROL = "public, max-age=300, s-maxage=3600"


class ObjectClient(Protocol):
    def head_object(self, key: str) -> dict[str, str] | None: ...
    def put_object(
        self, key: str, body: bytes, *, metadata: dict[str, str],
        cache_control: str, content_disposition: str,
    ) -> dict[str, str]: ...


@dataclass(frozen=True)
class VerifiedArtifact:
    spec: GeneratedPdfSpec
    path: Path
    sha256: str
    source_sha256: str
    pages: int
    renderer_profile: str = ""


def mapped_path(root: Path, configured: Path) -> Path:
    return root.resolve() / configured.resolve().relative_to(BASE.resolve())


def _presentation_provenance(root: Path) -> dict[str, dict]:
    path = root.resolve() / "presentation-build-provenance.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    profile = str(data.get("rendererProfile") or "")
    records: dict[str, dict] = {}
    for artifact in data.get("artifacts") or []:
        for field in ("slidesPdf", "notesPdf"):
            key = artifact.get(field)
            digest = artifact.get(field + "Sha256")
            if key and digest:
                records[str(key)] = {"sha256": str(digest), "profile": profile}
    return records


def verify_artifacts(specs: tuple[GeneratedPdfSpec, ...], root: Path) -> list[VerifiedArtifact]:
    provenance = _presentation_provenance(root)
    verified: list[VerifiedArtifact] = []
    errors: list[str] = []
    for spec in specs:
        path = mapped_path(root, spec.output)
        if not path.is_file():
            errors.append(f"missing generated PDF: {spec.key}")
            continue
        try:
            with fitz.open(path) as document:
                if len(document) == 0:
                    errors.append(f"empty generated PDF: {spec.key}")
                    continue
                blank = [
                    str(index)
                    for index, page in enumerate(document, 1)
                    if not (page.get_text("text").strip() or page.get_images() or page.get_drawings())
                ]
                if blank:
                    errors.append(f"blank PDF pages in {spec.key}: {', '.join(blank)}")
                    continue
                pages = len(document)
        except Exception as exc:  # noqa: BLE001 - verification boundary
            errors.append(f"invalid generated PDF {spec.key}: {exc}")
            continue
        digest = sha256_file(path)
        renderer_profile = ""
        if spec.kind.startswith("presentation-"):
            record = provenance.get(spec.key)
            if record is None:
                errors.append(f"presentation provenance missing for {spec.key}")
                continue
            if record["sha256"] != digest:
                errors.append(f"presentation provenance hash mismatch for {spec.key}")
                continue
            renderer_profile = record["profile"]
        verified.append(VerifiedArtifact(
            spec, path, digest, sha256_file(spec.source), pages, renderer_profile
        ))
    if errors:
        raise ValueError("Generated PDF verification failed:\n  - " + "\n  - ".join(errors))
    return verified


def publish_artifacts(
    artifacts: list[VerifiedArtifact],
    client: ObjectClient | None,
    *,
    dry_run: bool,
    offline: bool = False,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for artifact in artifacts:
        remote = None if offline else client.head_object(artifact.spec.key)  # type: ignore[union-attr]
        if remote and remote.get("x-amz-meta-sha256", "").lower() == artifact.sha256:
            results.append((artifact.spec.key, "unchanged"))
            continue
        if dry_run:
            results.append((artifact.spec.key, "would-upload"))
            continue
        metadata = {
            "sha256": artifact.sha256,
            "source-sha256": artifact.source_sha256,
            "kind": artifact.spec.kind,
            "schema": "1",
        }
        if artifact.renderer_profile:
            metadata["renderer-profile"] = artifact.renderer_profile
        verified = client.put_object(  # type: ignore[union-attr]
            artifact.spec.key,
            artifact.path.read_bytes(),
            metadata=metadata,
            cache_control=CACHE_CONTROL,
            content_disposition=f'inline; filename="{artifact.path.name}"',
        )
        if verified.get("x-amz-meta-sha256", "").lower() != artifact.sha256:
            raise RuntimeError(f"R2 checksum metadata mismatch after upload: {artifact.spec.key}")
        if int(verified.get("content-length", "-1")) != artifact.path.stat().st_size:
            raise RuntimeError(f"R2 size mismatch after upload: {artifact.spec.key}")
        results.append((artifact.spec.key, "uploaded"))
    return results


def stale_object_keys(client: R2S3Client) -> list[str]:
    declared = {spec.key for spec in generated_pdf_specs()}
    remote = {
        key
        for prefix in ("Studies/", "Applications/")
        for key in client.list_objects(prefix)
        if key.lower().endswith(".pdf")
    }
    return sorted(remote - declared)


def removed_object_keys(
    base_ref: str,
    *,
    diff_text: str | None = None,
    base_manifest_text: str | None = None,
    current_specs: tuple[GeneratedPdfSpec, ...] | None = None,
) -> list[str]:
    """Return generated PDF keys retired by a Git diff, excluding live outputs."""
    if diff_text is None:
        result = subprocess.run(
            ["git", "diff", "--diff-filter=D", "--name-only", f"{base_ref}..HEAD"],
            cwd=BASE,
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"Could not diff {base_ref}..HEAD")
        diff_text = result.stdout
    deleted = {line.strip().replace("\\", "/") for line in diff_text.splitlines() if line.strip()}
    retired: set[str] = set()
    for path_text in deleted:
        path = Path(path_text)
        if (
            len(path.parts) >= 3
            and path.parts[0] in {"Studies", "Applications"}
            and path.suffix.lower() == ".md"
            and not path.stem.startswith("Research-Template-")
        ):
            retired.add(path.with_suffix(".pdf").as_posix())

    if base_manifest_text is None:
        result = subprocess.run(
            ["git", "show", f"{base_ref}:Scripts/presentation-pipeline.json"],
            cwd=BASE,
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or f"Could not read presentation manifest at {base_ref}"
            )
        base_manifest_text = result.stdout
    if base_manifest_text:
        try:
            base_manifest = json.loads(base_manifest_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Could not parse presentation manifest at {base_ref}: {exc}") from exc
        for deck in base_manifest.get("decks", []):
            source = str(deck.get("source") or "").replace("\\", "/")
            if source in deleted:
                for field in ("slidesPdf", "notesPdf"):
                    key = str(deck.get(field) or "").replace("\\", "/")
                    if key:
                        retired.add(key)

    selected_specs = current_specs if current_specs is not None else generated_pdf_specs()
    live = {spec.key for spec in selected_specs}
    return sorted(retired - live)


def delete_removed_objects(
    keys: list[str],
    client: R2S3Client,
    *,
    dry_run: bool,
) -> list[tuple[str, str]]:
    """Delete only explicit retired keys and verify each deletion."""
    results: list[tuple[str, str]] = []
    for key in keys:
        if client.head_object(key) is None:
            results.append((key, "absent"))
            continue
        if dry_run:
            results.append((key, "would-delete"))
            continue
        client.delete_object(key)
        if client.head_object(key) is not None:
            raise RuntimeError(f"R2 object still exists after delete: {key}")
        results.append((key, "deleted"))
    return results


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Verify generated PDFs and publish changed checksums to Cloudflare R2."
    )
    parser.add_argument("--artifact-root", type=Path, default=BASE)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true", help="Require and sync every inventory item")
    selection.add_argument("--changed", action="store_true", help="Sync inventory items present under the root")
    selection.add_argument("--artifact", action="append", default=[], metavar="KEY")
    selection.add_argument(
        "--kind", action="append", choices=("markdown", "presentation-slides", "presentation-notes"),
        help="Sync every inventory artifact of this kind; may be repeated",
    )
    selection.add_argument("--list-stale", action="store_true", help="List remote PDF keys absent from inventory")
    selection.add_argument("--delete-stale", action="store_true", help="Delete remote PDF keys absent from inventory")
    selection.add_argument(
        "--delete-removed-since",
        metavar="GIT_REF",
        help="Delete only generated PDF keys whose source was removed since GIT_REF",
    )
    parser.add_argument(
        "--confirm-stale-count", type=int,
        help="Required exact stale-key count for a non-dry-run --delete-stale",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--offline", action="store_true",
        help="Do not contact R2; valid only with --dry-run",
    )
    args = parser.parse_args(argv)
    if args.offline and not args.dry_run:
        raise SystemExit("--offline requires --dry-run")
    if args.offline and (args.list_stale or args.delete_stale or args.delete_removed_since):
        raise SystemExit("stale-object modes require R2 access")

    errors = inventory_errors()
    if errors:
        raise SystemExit("Generated PDF inventory errors:\n  - " + "\n  - ".join(errors))
    root = args.artifact_root.expanduser().resolve()
    if args.delete_removed_since:
        try:
            client = R2S3Client(load_r2_config())
            keys = removed_object_keys(args.delete_removed_since)
            results = delete_removed_objects(keys, client, dry_run=args.dry_run)
            for key, action in results:
                print(f"{action:12} {key}")
            print(f"Retired generated PDF objects: {len(keys)}")
        except (OSError, RuntimeError, ValueError) as exc:
            print(str(exc))
            return 1
        return 0
    if args.list_stale or args.delete_stale:
        try:
            client = R2S3Client(load_r2_config())
            stale = stale_object_keys(client)
            for key in stale:
                print(key)
            print(f"Stale generated PDF objects: {len(stale)}")
            if args.delete_stale and not args.dry_run:
                if args.confirm_stale_count is None:
                    raise ValueError(
                        "--delete-stale requires --confirm-stale-count with the exact listed count"
                    )
                if args.confirm_stale_count != len(stale):
                    raise ValueError(
                        f"stale count changed: confirmed {args.confirm_stale_count}, found {len(stale)}"
                    )
                for key in stale:
                    client.delete_object(key)
                    if client.head_object(key) is not None:
                        raise RuntimeError(f"R2 object still exists after delete: {key}")
                print(f"Deleted and verified {len(stale)} stale generated PDF objects")
        except (OSError, RuntimeError, ValueError) as exc:
            print(str(exc))
            return 1
        return 0
    if args.all:
        specs = generated_pdf_specs()
    elif args.changed:
        specs = tuple(spec for spec in generated_pdf_specs() if mapped_path(root, spec.output).is_file())
        if not specs:
            raise SystemExit("No generated inventory PDFs are present under --artifact-root")
    elif args.kind:
        requested = set(args.kind)
        specs = tuple(spec for spec in generated_pdf_specs() if spec.kind in requested)
    else:
        try:
            specs = tuple(spec_by_key(key) for key in args.artifact)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc

    try:
        artifacts = verify_artifacts(specs, root)
        client = None if args.offline else R2S3Client(load_r2_config())
        results = publish_artifacts(
            artifacts, client, dry_run=args.dry_run, offline=args.offline
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(str(exc))
        return 1
    for key, action in results:
        print(f"{action:12} {key}")
    counts: dict[str, int] = {}
    for _, action in results:
        counts[action] = counts.get(action, 0) + 1
    print("Summary: " + ", ".join(f"{name}={count}" for name, count in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build and verify every normalized reference PDF declared in the manifest."""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

from _build_reference_pdf import build
from _common import BASE, configure_utf8_stdio
from _reference_artifacts import load_manifest, manifest_errors
from _reference_store import ReferenceStore


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def public_rows() -> list[dict]:
    return [
        row
        for row in load_manifest()["artifacts"]
        if (row.get("target") or {}).get("storage") == "r2-public"
        and str((row.get("target") or {}).get("r2_key", "")).lower().endswith(".pdf")
    ]


def build_all(output_root: Path) -> None:
    manifest = load_manifest()
    errors = manifest_errors(manifest)
    if errors:
        raise ValueError("reference manifest is invalid:\n  - " + "\n  - ".join(errors))
    rows = public_rows()
    if not rows:
        raise ValueError("reference manifest contains no normalized PDF rows")
    artifact_root = output_root.resolve()
    store = ReferenceStore()
    for row in rows:
        expected = artifact_root / row["repo_path"]
        if row.get("kind") == "normalized-reference-pdf":
            markdown_path = BASE / row["generation"]["source_markdown"]
            _, pdf_path = build(markdown_path, artifact_root / "References")
        else:
            source_path = store.resolve(row["repo_path"], allow_download=True)
            expected.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, expected)
            pdf_path = expected
        source = row["source"]
        actual_size = pdf_path.stat().st_size
        if actual_size != source["bytes"]:
            raise ValueError(
                "generated PDF size differs from manifest: "
                f"{row['repo_path']} (expected {source['bytes']}, actual {actual_size})"
            )
        actual_hash = _sha256(pdf_path)
        if actual_hash != source["sha256"]:
            raise ValueError(
                "generated PDF checksum differs from manifest: "
                f"{row['repo_path']} (expected {source['sha256']}, actual {actual_hash})"
            )
        if pdf_path != expected:
            raise ValueError(f"generated PDF path differs from manifest: {pdf_path} != {expected}")
    print(f"Staged and verified {len(rows)} public reference PDFs under {artifact_root}.")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        build_all(args.output_root)
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Reference PDF batch build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

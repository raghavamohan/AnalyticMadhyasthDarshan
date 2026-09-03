#!/usr/bin/env python3
"""Provision, probe, upload, and verify the private R2 reference bucket."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from dataclasses import replace
from pathlib import Path

import _cloudflare_performance as cf
from _common import BASE, configure_utf8_stdio, write_text_lf
from _r2_s3 import R2S3Client, load_r2_config
from _reference_artifacts import (
    MANIFEST_PATH,
    _canonical_json,
    artifact_local_path,
    load_manifest,
    manifest_errors,
)

DEFAULT_BUCKET = "amd-reference-archive"


def bucket_name() -> str:
    return os.environ.get("AMD_REFERENCE_R2_BUCKET", DEFAULT_BUCKET).strip() or DEFAULT_BUCKET


def _account_id(token: str) -> str:
    zone_id = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    payload = cf._api_request("GET", f"/zones/{zone_id}", token)
    account_id = ((payload or {}).get("result") or {}).get("account", {}).get("id")
    if not account_id:
        raise RuntimeError("Cloudflare zone response did not include its account ID")
    return str(account_id)


def _bucket_names(payload: dict) -> set[str]:
    result = payload.get("result") or {}
    rows = result.get("buckets", []) if isinstance(result, dict) else result
    return {str(row.get("name")) for row in rows if isinstance(row, dict) and row.get("name")}


def control_plane_buckets(token: str, account_id: str) -> set[str]:
    payload = cf._api_request("GET", f"/accounts/{account_id}/r2/buckets", token)
    return _bucket_names(payload)


def create_bucket(token: str, account_id: str, name: str) -> None:
    if name in control_plane_buckets(token, account_id):
        print(f"R2 bucket already exists: {name}")
        return
    cf._api_request(
        "POST",
        f"/accounts/{account_id}/r2/buckets",
        token,
        {"name": name},
    )
    if name not in control_plane_buckets(token, account_id):
        raise RuntimeError(f"Cloudflare accepted bucket creation but {name!r} is not listed")
    print(f"Created private R2 bucket: {name}")


def s3_client(name: str) -> R2S3Client:
    config = replace(load_r2_config(), bucket=name)
    return R2S3Client(config)


def probe_s3_access(client: R2S3Client) -> None:
    key = f"_probes/reference-access-{uuid.uuid4().hex}.pdf"
    body = b"%PDF-1.4\n% R2 reference access probe; safe to delete.\n"
    client.put_object(
        key,
        body,
        metadata={"sha256": hashlib.sha256(body).hexdigest(), "purpose": "access-probe"},
        cache_control="private, no-store",
        content_disposition='attachment; filename="reference-access-probe.pdf"',
    )
    headers = client.head_object(key)
    if headers is None:
        raise RuntimeError("R2 access probe disappeared after upload")
    client.delete_object(key)
    if client.head_object(key) is not None:
        raise RuntimeError("R2 access probe still exists after delete")
    print("R2 S3 write/read/delete probe passed; temporary object removed.")


def _uploadable_rows(*, include_review_required: bool) -> list[dict]:
    data = load_manifest()
    errors = manifest_errors(data)
    if errors:
        raise RuntimeError("manifest/local gate failed:\n  - " + "\n  - ".join(errors))
    rows: list[dict] = []
    for row in data["artifacts"]:
        target = row.get("target") or {}
        if target.get("storage") not in {"r2-public", "r2-private-original"}:
            continue
        if row.get("state") not in {"git-source", "generated-local", "r2-published"}:
            continue
        private_archive = target.get("storage") == "r2-private-original"
        if (
            not include_review_required
            and not private_archive
            and (row.get("rights") or {}).get("status") == "review-required"
        ):
            continue
        rows.append(row)
    return rows


def _source_path(row: dict, artifact_root: Path | None) -> Path:
    # CI's combined artifact tree also contains generated reading HTML beside
    # normalized PDFs.  That HTML is not the archived third-party original and
    # must never shadow a private-original manifest row with the same repo path.
    if artifact_root is not None and Path(row["repo_path"]).suffix.lower() == ".pdf":
        candidate = artifact_root.resolve() / row["repo_path"]
        if candidate.is_file():
            return candidate
    return artifact_local_path(row)


def _verify_local_source(row: dict, path: Path) -> None:
    source = row["source"]
    if not path.is_file():
        raise RuntimeError(f"local artifact is missing: {row['repo_path']} ({path})")
    if path.stat().st_size != source["bytes"]:
        raise RuntimeError(f"local artifact size differs from manifest: {row['repo_path']}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != source["sha256"]:
        raise RuntimeError(f"local artifact checksum differs from manifest: {row['repo_path']}")


def _object_matches_manifest(headers: dict[str, str] | None, source: dict) -> bool:
    return bool(
        headers is not None
        and headers.get("x-amz-meta-sha256") == source["sha256"]
        and headers.get("content-length") == str(source["bytes"])
    )


def upload_rows(client: R2S3Client, rows: list[dict], artifact_root: Path | None = None) -> None:
    uploaded = 0
    total_bytes = 0
    for row in rows:
        source = row["source"]
        target = row["target"]
        headers = client.head_object(target["r2_key"])
        if _object_matches_manifest(headers, source):
            print(f"SKIP {target['r2_key']} (already verified)")
            continue
        path = _source_path(row, artifact_root)
        _verify_local_source(row, path)
        key = target["r2_key"]
        private = target["storage"] == "r2-private-original"
        client.put_object(
            key,
            path.read_bytes(),
            metadata={
                "sha256": source["sha256"],
                "repo-path": row["repo_path"],
                "rights-status": row["rights"]["status"],
            },
            cache_control="private, no-store" if private else "public, max-age=3600",
            content_disposition=f'attachment; filename="{path.name}"',
            content_type=source["media_type"],
        )
        headers = client.head_object(key)
        if headers is None or headers.get("x-amz-meta-sha256") != source["sha256"]:
            raise RuntimeError(f"uploaded object failed metadata verification: {key}")
        uploaded += 1
        total_bytes += source["bytes"]
        print(f"OK {key} ({source['bytes']} bytes)")
    print(f"Uploaded and verified {uploaded} artifact(s), {total_bytes / 1024 / 1024:.2f} MiB.")


def verify_rows(client: R2S3Client, rows: list[dict]) -> None:
    errors: list[str] = []
    for row in rows:
        key = row["target"]["r2_key"]
        source = row["source"]
        headers = client.head_object(key)
        if headers is None:
            errors.append(f"missing R2 object: {key}")
            continue
        if headers.get("x-amz-meta-sha256") != source["sha256"]:
            errors.append(f"checksum metadata differs from manifest: {key}")
        try:
            size = int(headers.get("content-length", "-1"))
        except ValueError:
            size = -1
        if size != source["bytes"]:
            errors.append(f"size differs from manifest: {key}")
    if errors:
        raise RuntimeError("R2 verification failed:\n  - " + "\n  - ".join(errors))
    print(f"Verified {len(rows)} uploaded reference artifact(s).")


def record_published(rows: list[dict]) -> None:
    selected = {row["repo_path"] for row in rows}
    data = load_manifest()
    changed = 0
    for row in data["artifacts"]:
        if row["repo_path"] in selected and row.get("state") != "r2-published":
            row["state"] = "r2-published"
            changed += 1
    errors = manifest_errors(data)
    if errors:
        raise RuntimeError("published-state update failed:\n  - " + "\n  - ".join(errors))
    write_text_lf(MANIFEST_PATH, _canonical_json(data))
    print(f"Recorded {changed} newly published reference artifact(s) in the manifest.")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--status", action="store_true", help="Show control-plane bucket status.")
    actions.add_argument("--create-bucket", action="store_true", help="Create the private bucket if absent.")
    actions.add_argument(
        "--probe-s3-access",
        action="store_true",
        help="Write, read, and delete one uniquely named temporary probe object.",
    )
    actions.add_argument(
        "--upload-approved",
        action="store_true",
        help="Upload only artifacts whose rights status is already recorded as publishable.",
    )
    actions.add_argument(
        "--upload-all-reviewed",
        action="store_true",
        help="Upload all planned artifacts after an explicit rights review.",
    )
    actions.add_argument(
        "--verify-approved",
        action="store_true",
        help="Verify private archive objects and rights-approved public objects in R2.",
    )
    actions.add_argument(
        "--record-approved-published",
        action="store_true",
        help="Verify approved objects and record their manifest state as r2-published.",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="Root containing CI-built PDF artifacts at their repository paths.",
    )
    args = parser.parse_args()

    try:
        cf.load_repo_env()
        token = cf.cloudflare_api_token()
        if not token:
            raise RuntimeError("CLOUDFLARE_API_TOKEN is required")
        account_id = _account_id(token)
        name = bucket_name()
        if args.status:
            names = control_plane_buckets(token, account_id)
            print(f"Reference bucket {name}: {'present' if name in names else 'absent'}")
        elif args.create_bucket:
            create_bucket(token, account_id, name)
        elif args.probe_s3_access:
            if name not in control_plane_buckets(token, account_id):
                raise RuntimeError(f"reference bucket does not exist: {name}")
            probe_s3_access(s3_client(name))
        elif args.upload_approved:
            upload_rows(
                s3_client(name),
                _uploadable_rows(include_review_required=False),
                args.artifact_root,
            )
        elif args.upload_all_reviewed:
            if os.environ.get("AMD_REFERENCE_RIGHTS_REVIEWED") != "1":
                raise RuntimeError(
                    "set AMD_REFERENCE_RIGHTS_REVIEWED=1 only after completing the manifest rights review"
                )
            upload_rows(
                s3_client(name),
                _uploadable_rows(include_review_required=True),
                args.artifact_root,
            )
        elif args.verify_approved:
            verify_rows(s3_client(name), _uploadable_rows(include_review_required=False))
        elif args.record_approved_published:
            rows = _uploadable_rows(include_review_required=False)
            verify_rows(s3_client(name), rows)
            record_published(rows)
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Reference R2 publisher error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

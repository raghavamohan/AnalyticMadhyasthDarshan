"""Read-only R2 snapshots, split archives, and credential-free recovery checks.

Upload the completed snapshot's manifest and ZIP parts with the connected Drive
plugin. No Drive OAuth token or R2 write permission is needed by this command.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

from _common import BASE, configure_utf8_stdio, write_text_lf
from _r2_s3 import R2S3Client, load_r2_config

DEFAULT_BUCKETS = ("amd-public-pdfs", "amd-reference-archive")
SCHEMA = "amd-r2-backup-v1"
SHA256 = re.compile(r"[0-9a-f]{64}")
RESTORE_HEADERS = {"content-type", "cache-control", "content-disposition",
                   "content-encoding", "content-language", "expires"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: dict) -> None:
    write_text_lf(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def hashes(path: Path) -> dict:
    sha = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
            md5.update(chunk)
            size += len(chunk)
    return {"bytes": size, "sha256": sha.hexdigest(), "md5": md5.hexdigest()}


def inventory(client: R2S3Client) -> list[dict]:
    rows = []
    token = ""
    seen_tokens = set()
    while True:
        query = {"list-type": "2"}
        if token:
            query["continuation-token"] = token
        _, _, body = client._request("GET", "/" + client.bucket(), query=query)
        root = ET.fromstring(body)
        for node in root.findall("./{*}Contents"):
            key = node.findtext("{*}Key")
            etag = node.findtext("{*}ETag")
            if not key or not etag:
                raise ValueError("R2 listing is missing an object key or ETag")
            rows.append({"bucket": client.bucket(), "key": key,
                         "bytes": int(node.findtext("{*}Size") or "0"),
                         "etag": etag, "last_modified": node.findtext("{*}LastModified")})
        if (root.findtext("{*}IsTruncated") or "").lower() != "true":
            break
        token = root.findtext("{*}NextContinuationToken") or ""
        if not token or token in seen_tokens:
            raise ValueError("R2 pagination is truncated or repeats a continuation token")
        seen_tokens.add(token)
    rows.sort(key=lambda row: row["key"])
    if len({row["key"] for row in rows}) != len(rows):
        raise ValueError("R2 listing contains duplicate keys")
    return rows


def cache_paths(root: Path, row: dict) -> tuple[Path, Path]:
    # Never map remote keys onto Windows filenames (case, traversal, long paths).
    name = hashlib.sha256((row["bucket"] + "\0" + row["key"]).encode()).hexdigest()
    return root / "_work" / (name + ".bin"), root / "_work" / (name + ".json")


def download(client: R2S3Client, root: Path, row: dict) -> dict:
    data_path, record_path = cache_paths(root, row)
    if data_path.is_file() and record_path.is_file():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if all(record.get(key) == value for key, value in row.items()):
            checksum = hashes(data_path)
            if checksum["bytes"] == row["bytes"] and checksum["sha256"] == record["sha256"]:
                return record
    _, headers, body = client._request(
        "GET", client._object_path(row["key"]), headers={"if-match": row["etag"]})
    if len(body) != row["bytes"] or headers.get("etag") != row["etag"]:
        raise ValueError(f"Object changed during backup: {row['bucket']}/{row['key']}")
    checksum = hashlib.sha256(body).hexdigest()
    declared = headers.get("x-amz-meta-sha256")
    if declared and declared != checksum:
        raise ValueError(f"Source SHA-256 mismatch: {row['bucket']}/{row['key']}")
    plain_etag = row["etag"].strip('"')
    if re.fullmatch(r"[0-9a-fA-F]{32}", plain_etag):
        if hashlib.md5(body, usedforsecurity=False).hexdigest() != plain_etag.lower():
            raise ValueError(f"Source MD5 mismatch: {row['bucket']}/{row['key']}")
    record = {**row, "sha256": checksum,
              "headers": {key: value for key, value in headers.items()
                          if key in RESTORE_HEADERS or key.startswith("x-amz-meta-")}}
    data_path.parent.mkdir(parents=True, exist_ok=True)
    temp = data_path.with_suffix(".partial")
    temp.write_bytes(body)
    temp.replace(data_path)
    write_json(record_path, record)
    return record


def package(root: Path, records: list[dict], part_bytes: int) -> list[dict]:
    unique = {}
    for row in records:
        unique.setdefault(row["sha256"], row)
    parts = []
    archive = None
    size = 0
    try:
        for digest, row in sorted(unique.items()):
            if archive is None or (size and size + row["bytes"] > part_bytes):
                if archive is not None:
                    archive.close()
                    parts[-1].update(hashes(root / parts[-1]["name"]))
                name = f"objects-{len(parts) + 1:03}.zip"
                archive = zipfile.ZipFile(root / name, "x", compression=zipfile.ZIP_STORED)
                parts.append({"name": name, "blobs": []})
                size = 0
            data_path, _ = cache_paths(root, row)
            archive.write(data_path, "objects/" + digest)
            parts[-1]["blobs"].append(digest)
            size += row["bytes"]
    finally:
        if archive is not None:
            archive.close()
    if parts:
        parts[-1].update(hashes(root / parts[-1]["name"]))
    return parts


def snapshot(root: Path, clients: dict, workers: int, part_bytes: int) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    if (root / "manifest.json").exists() or list(root.glob("objects-*.zip")):
        raise ValueError("Use a new snapshot directory; completed backups are never overwritten")
    rows = [row for client in clients.values() for row in inventory(client)]
    print(f"Inventory: {len(rows)} objects, {sum(r['bytes'] for r in rows):,} bytes", flush=True)
    source = {"schema": SCHEMA, "started_at": now(), "buckets": list(clients), "objects": rows}
    source_path = root / "inventory.json"
    if source_path.exists():
        previous = json.loads(source_path.read_text(encoding="utf-8"))
        if previous["buckets"] != source["buckets"] or previous["objects"] != rows:
            raise ValueError("R2 inventory changed since the interrupted backup; use a new directory")
        source = previous
    else:
        write_json(source_path, source)
    records = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [pool.submit(download, clients[row["bucket"]], root, row) for row in rows]
        for job in as_completed(jobs):
            records.append(job.result())
            if len(records) % 100 == 0 or len(records) == len(rows):
                print(f"Verified downloads: {len(records)}/{len(rows)}", flush=True)
    for bucket, client in clients.items():
        if inventory(client) != [row for row in rows if row["bucket"] == bucket]:
            raise ValueError(f"Bucket changed during backup: {bucket}; no completed manifest written")
    records.sort(key=lambda row: (row["bucket"], row["key"]))
    parts = package(root, records, part_bytes)
    manifest = {"schema": SCHEMA, "started_at": source["started_at"], "completed_at": now(),
                "buckets": list(clients), "object_count": len(records),
                "source_bytes": sum(row["bytes"] for row in records),
                "objects": records, "parts": parts}
    # The manifest is the completion marker; incomplete/unverified backups have none.
    verify(root, manifest)
    write_json(root / "manifest.json", manifest)
    return manifest


def verify(root: Path, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA:
        raise ValueError("Unsupported backup schema")
    rows = manifest["objects"]
    keys = [(row["bucket"], row["key"]) for row in rows]
    if len(keys) != len(set(keys)) or len(rows) != manifest["object_count"]:
        raise ValueError("Invalid object count or duplicate source keys")
    expected = {}
    for row in rows:
        digest = row["sha256"]
        if not SHA256.fullmatch(digest):
            raise ValueError("Invalid blob checksum")
        if digest in expected and expected[digest] != row["bytes"]:
            raise ValueError("Conflicting blob sizes")
        expected[digest] = row["bytes"]
    if sum(row["bytes"] for row in rows) != manifest["source_bytes"]:
        raise ValueError("Invalid source byte total")
    seen = set()
    names = set()
    for part in manifest["parts"]:
        if not re.fullmatch(r"objects-[0-9]{3,}\.zip", part["name"]) or part["name"] in names:
            raise ValueError("Invalid or duplicate archive filename")
        names.add(part["name"])
        path = root / part["name"]
        if hashes(path) != {key: part[key] for key in ("bytes", "sha256", "md5")}:
            raise ValueError(f"Archive checksum mismatch: {part['name']}")
        blobs = part["blobs"]
        if len(blobs) != len(set(blobs)):
            raise ValueError("Duplicate archive blob")
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) != len(blobs) or {entry.filename for entry in entries} != {
                    "objects/" + digest for digest in blobs}:
                raise ValueError("Archive entries differ from manifest")
            for digest in blobs:
                if digest in seen or digest not in expected:
                    raise ValueError("Unexpected or repeated blob")
                sha = hashlib.sha256()
                size = 0
                with archive.open("objects/" + digest) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        sha.update(chunk)
                        size += len(chunk)
                if sha.hexdigest() != digest or size != expected[digest]:
                    raise ValueError("Restored blob checksum mismatch")
                seen.add(digest)
    if seen != set(expected):
        raise ValueError("Backup is missing blobs")
    print(f"Backup verified: {len(rows)} source objects, {len(seen)} unique blobs, "
          f"{len(names)} archive parts", flush=True)
    return manifest


def extract(root: Path, output: Path) -> None:
    manifest = verify(root)
    # Content-addressed extraction avoids unsafe/case-colliding remote paths.
    # The manifest retains the exact R2 keys for controlled recovery.
    output.mkdir(parents=True, exist_ok=False)
    for part in manifest["parts"]:
        with zipfile.ZipFile(root / part["name"]) as archive:
            for digest in part["blobs"]:
                path = output / "objects" / digest
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open("objects/" + digest) as source, path.open("xb") as target:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        target.write(chunk)
                if hashes(path)["sha256"] != digest:
                    raise ValueError("Extracted file checksum mismatch")
    write_json(output / "manifest.json", manifest)
    print(f"Recovery drill passed: extracted verified objects to {output}", flush=True)


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("snapshot", help="Download both R2 buckets; never writes to R2")
    create.add_argument("--output", type=Path)
    create.add_argument("--bucket", action="append", dest="buckets")
    create.add_argument("--workers", type=int, default=8)
    create.add_argument("--part-mib", type=int, default=64)
    check = commands.add_parser("verify", help="Check every archive and blob without credentials")
    check.add_argument("directory", type=Path)
    restore = commands.add_parser("extract", help="Credential-free local recovery drill")
    restore.add_argument("directory", type=Path)
    restore.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "snapshot":
        if not 1 <= args.workers <= 32 or not 1 <= args.part_mib <= 1024:
            parser.error("workers must be 1..32 and part-mib 1..1024")
        config = load_r2_config()
        buckets = args.buckets or list(DEFAULT_BUCKETS)
        if len(buckets) != len(set(buckets)):
            parser.error("Duplicate bucket selection")
        clients = {name: R2S3Client(replace(config, bucket=name)) for name in buckets}
        output = args.output or BASE / "tmp/r2-backup" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        snapshot(output, clients, args.workers, args.part_mib * 1024 * 1024)
        print(f"Upload manifest.json and objects-*.zip from {output} to Google Drive", flush=True)
    elif args.command == "verify":
        verify(args.directory)
    else:
        extract(args.directory, args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, zipfile.BadZipFile) as error:
        print(f"Backup failed: {error}", file=sys.stderr)
        raise SystemExit(1)

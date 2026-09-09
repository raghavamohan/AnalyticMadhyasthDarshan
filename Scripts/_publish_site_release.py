"""Stage, audit and promote complete site releases with immutable R2 objects.

Production routing is a separate one-time cutover. Normal publication never
changes routes or deletes objects; a failed audit rolls back the deployment.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen
import uuid

import _cloudflare_performance as cf
from _common import BASE
from _publish_generated_pdf_worker import _multipart_put, _zone_account_id, _workers_subdomain, KEYS_SOURCE, WORKER_SOURCE
from _publish_reference_artifacts import bucket_name as reference_bucket_name
from _r2_s3 import R2S3Client, load_r2_config
from _site_release import digest, encode, validate_bundle

WORKER = "amd-site"
CANARY = "amd-site-canary"
SOURCE = BASE / "infra/site-worker/src/index.js"


def put_verified(client, key: str, body: bytes, content_type: str, *, filename: str) -> None:
    checksum = digest(body)
    previous = client.head_object(key)
    if previous:
        if previous.get("x-amz-meta-sha256") != checksum or int(previous.get("content-length", "-1")) != len(body):
            raise ValueError(f"Immutable object collision: {key}")
        return
    headers = client.put_object(key, body, metadata={"sha256": checksum},
        cache_control="public, max-age=31536000, immutable", content_disposition=f'inline; filename="{filename}"', content_type=content_type)
    if headers.get("x-amz-meta-sha256") != checksum or int(headers.get("content-length", "-1")) != len(body):
        raise ValueError(f"Uploaded object did not verify: {key}")


def stage_objects(client, root: Path, manifest: dict) -> None:
    for path, record in manifest["files"].items():
        if record["archive"]:
            put_verified(client, record["key"], (root / "assets" / path.lstrip("/")).read_bytes(), record["type"], filename=Path(path).name)
    put_verified(client, f'site/releases/{manifest["revision"]}.json', encode(manifest), "application/json", filename="release.json")


def upload_assets(token: str, account: str, worker: str, root: Path, manifest: dict) -> str:
    files = {}
    for path, record in manifest["files"].items():
        if record["archive"] and path.endswith(".pdf"):
            continue
        for key in record.get("parts", [path]):
            file = root / "assets" / key.lstrip("/")
            raw = file.read_bytes()
            if len(raw) > 25 * 1024 * 1024:
                raise ValueError(f"Static asset exceeds 25 MiB: {key}")
            files[key] = (digest(raw)[:32], raw, record["type"])
    payload = {"manifest": {key: {"hash": value[0], "size": len(value[1])} for key, value in files.items()}}
    result = cf._api_request("POST", f"/accounts/{account}/workers/scripts/{worker}/assets-upload-session", token, payload)["result"]
    upload_token = result["jwt"]
    completion = upload_token if not result.get("buckets") else None
    by_hash = {value[0]: value for value in files.values()}
    for bucket in result.get("buckets", []):
        boundary = uuid.uuid4().hex
        parts = []
        for checksum in bucket:
            _, raw, mime = by_hash[checksum]
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{checksum}"; filename="{checksum}"\r\nContent-Type: {mime}\r\n\r\n').encode() + base64.b64encode(raw) + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        request = Request(f"{cf.API_BASE}/accounts/{account}/workers/assets/upload?base64=true", method="POST", data=b"".join(parts),
                          headers={"Authorization": f"Bearer {upload_token}", "Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urlopen(request, timeout=60) as response:
            uploaded = json.loads(response.read())
        if not uploaded.get("success"):
            raise ValueError("Static asset upload failed")
        completion = uploaded.get("result", {}).get("jwt") or completion
    if not completion:
        raise ValueError("Asset upload did not return a completion token")
    return completion


def deployments(token: str, account: str) -> list[dict]:
    response = cf._api_request("GET", f"/accounts/{account}/workers/scripts/{WORKER}/deployments", token, allow_404=True)
    return (response or {}).get("result", {}).get("deployments", [])


def deploy(token: str, account: str, worker: str, client, root: Path, manifest: dict, *, version_only: bool) -> str:
    assets = upload_assets(token, account, worker, root, manifest)
    metadata = {"main_module": "index.js", "compatibility_date": "2026-09-09",
                "assets": {"jwt": assets, "config": {"html_handling": "none", "run_worker_first": True}},
                "bindings": [{"type": "assets", "name": "ASSETS"},
                    {"type": "r2_bucket", "name": "GENERATED_PDFS", "bucket_name": client.bucket()},
                    {"type": "r2_bucket", "name": "REFERENCE_PDFS", "bucket_name": reference_bucket_name()}]}
    endpoint = f"{cf.API_BASE}/accounts/{account}/workers/scripts/{worker}"
    result = _multipart_put(endpoint + ("/versions" if version_only else ""), token,
        {"index.js": SOURCE.read_text(encoding="utf-8"), "release.js": "export default " + encode(manifest).decode() + ";\n",
         "pdf.js": WORKER_SOURCE.read_text(encoding="utf-8"), "generated-pdf-keys.js": KEYS_SOURCE.read_text(encoding="utf-8")},
        metadata, method="POST" if version_only else "PUT")
    if not result.get("success"):
        raise ValueError("Site Worker upload failed")
    if not version_only:
        cf._api_request("POST", f"/accounts/{account}/workers/scripts/{worker}/subdomain", token, {"enabled": True, "previews_enabled": True})
        # The script PUT returns a script name as `id`, not a rollback version.
        current = cf._api_request("GET", f"/accounts/{account}/workers/scripts/{worker}/deployments", token)
        version = current['result']['deployments'][0]['versions'][0]['version_id']
    else:
        version = result['result']['id']
    if not version:
        raise ValueError('Worker upload did not resolve a deployment version')
    return version


def public_state(base: str) -> dict:
    with urlopen(base.rstrip("/") + "/.well-known/publication.json", timeout=30) as response:
        return json.loads(response.read())


def audit(base: str, root: Path, manifest: dict) -> None:
    if public_state(base)["revision"] != manifest["revision"]:
        raise ValueError("The endpoint is serving another release")
    # Download every document and discovery surface; HEAD the remaining assets.
    for path, record in manifest["files"].items():
        from urllib.parse import quote
        full = path.endswith((".html", ".pdf", ".json", ".txt"))
        request = Request(base.rstrip("/") + quote(path, safe="/") + "?r=" + manifest["revision"], method="GET" if full else "HEAD")
        with urlopen(request, timeout=60) as response:
            if response.status != 200:
                raise ValueError(f"Release URL failed: {path}")
            if full and digest(response.read()) != record["sha256"]:
                raise ValueError(f"Public checksum mismatch: {path}")
            if not full and int(response.headers.get("Content-Length", "-1")) != record["bytes"]:
                raise ValueError(f"Public size mismatch: {path}")
    print(f'Audited {len(manifest["files"])} release URLs at {base}')


def audit_public_if_active(token: str, zone: str, root: Path, manifest: dict) -> None:
    routes = cf.list_worker_routes(token, zone)
    if any(route.get('pattern') == f'{cf.SITE_HOST}/*' and route.get('script') == WORKER for route in routes):
        audit(f'https://{cf.SITE_HOST}', root, manifest)


def activate_version(token: str, account: str, version: str) -> None:
    cf._api_request("POST", f"/accounts/{account}/workers/scripts/{WORKER}/deployments", token,
                    {"strategy": "percentage", "versions": [{"version_id": version, "percentage": 100}]})


def assert_forward(previous: dict, candidate: dict) -> None:
    if previous["sourceSha"] == candidate["sourceSha"]:
        if previous.get('revision') and candidate.get('revision') and previous['revision'] != candidate['revision']:
            raise ValueError('The published commit rebuilt with different bytes; pin the changed renderer in a new commit before publication.')
        return
    check = subprocess.run(["git", "merge-base", "--is-ancestor", previous["sourceSha"], candidate["sourceSha"]], cwd=BASE)
    if check.returncode:
        raise ValueError("An older or unrelated release cannot replace the active revision; use explicit rollback.")


def publish(root: Path, *, promote: bool) -> None:
    manifest = validate_bundle(root)
    from _generated_pdf_inventory import generated_pdf_specs
    if set(manifest["pdfs"]) != {"/" + spec.key for spec in generated_pdf_specs()}:
        raise ValueError("Publication requires the complete verified PDF inventory")
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    if not token:
        raise ValueError("CLOUDFLARE_API_TOKEN is required")
    zone = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    account = _zone_account_id(token, zone)
    subdomain = _workers_subdomain(token, account)
    client = R2S3Client(load_r2_config())
    prior = deployments(token, account)
    active = public_state(f"https://{WORKER}.{subdomain}.workers.dev") if prior else None
    if active:
        assert_forward(active, manifest)
        if active["revision"] == manifest["revision"]:
            audit(f"https://{WORKER}.{subdomain}.workers.dev", root, manifest)
            audit_public_if_active(token, zone, root, manifest)
            record_deployment(client, manifest, prior[0]['versions'][0]['version_id'])
            print("This release is already published.")
            return
    stage_objects(client, root, manifest)
    deploy(token, account, CANARY, client, root, manifest, version_only=False)
    audit(f"https://{CANARY}.{subdomain}.workers.dev", root, manifest)
    if not promote:
        print("Canary verified. Production has not been promoted.")
        return
    # The workflow serializes promotion. Re-read state to reject a superseded
    # candidate before changing production, even after a long staging run.
    if active and public_state(f"https://{WORKER}.{subdomain}.workers.dev")["revision"] != active["revision"]:
        raise ValueError("Active release moved during staging; retry against current publication state")
    version = deploy(token, account, WORKER, client, root, manifest, version_only=bool(prior))
    if prior:
        activate_version(token, account, version)
    try:
        audit(f"https://{WORKER}.{subdomain}.workers.dev", root, manifest)
        audit_public_if_active(token, zone, root, manifest)
    except Exception:
        if prior:
            previous_version = prior[0]["versions"][0]["version_id"]
            activate_version(token, account, previous_version)
        raise
    record_deployment(client, manifest, deployments(token, account)[0]['versions'][0]['version_id'])
    print(f'Published coherent site release {manifest["revision"]}')


def record_deployment(client, manifest: dict, version: str) -> None:
    key = f'site/deployments/{manifest["revision"]}.json'
    if not client.head_object(key):
        receipt = {'revision':manifest['revision'], 'sourceSha':manifest['sourceSha'], 'version':version}
        put_verified(client,key,encode(receipt),'application/json',filename='deployment.json')


def rollback(revision: str) -> None:
    if not re.fullmatch(r'[a-f0-9]{64}', revision):
        raise ValueError('Rollback requires an explicit retained revision.')
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    zone = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    account = _zone_account_id(token, zone)
    subdomain = _workers_subdomain(token, account)
    client = R2S3Client(load_r2_config())
    manifest = json.loads(client.get_object(f'site/releases/{revision}.json'))
    receipt = json.loads(client.get_object(f'site/deployments/{revision}.json'))
    if manifest.get('revision') != revision or receipt.get('revision') != revision or not receipt.get('version'):
        raise ValueError('Retained release or deployment receipt is invalid.')
    prior = deployments(token, account)[0]['versions'][0]['version_id']
    activate_version(token, account, receipt['version'])
    try:
        audit(f'https://{WORKER}.{subdomain}.workers.dev', BASE, manifest)
        audit_public_if_active(token, zone, BASE, manifest)
    except Exception:
        activate_version(token, account, prior)
        raise
    print(f'Rolled back to complete retained release {revision}.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--release-root", type=Path)
    selection.add_argument('--rollback', metavar='REVISION')
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    if args.rollback:
        if args.promote:
            parser.error('--rollback and --promote cannot be combined')
        rollback(args.rollback)
    else:
        publish(args.release_root, promote=args.promote)

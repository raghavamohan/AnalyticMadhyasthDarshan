"""Publish the MCP Server Card via a Cloudflare Worker.

Snippets cannot currently be created with the zone token used for Transform
Rules, so this path deploys Worker `amd-mcp`. The canonical card remains at
`.well-known/mcp/server-card.json` for GitHub Pages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cloudflare_performance as cf

WORKER_NAME = "amd-mcp"
WORKER_ROUTE = f"{cf.SITE_HOST}/.well-known/mcp/*"
WORKER_SRC = cf.BASE / "infra" / "mcp-worker" / "src" / "index.js"
RUNTIME_SRC = cf.BASE / "infra" / "mcp-worker" / "src" / "runtime.js"
CARD_PATH = cf.BASE / ".well-known" / "mcp" / "server-card.json"
START_HERE_PATH = cf.BASE / "Studies" / "start-here.json"
COMPATIBILITY_DATE = "2024-03-01"


def worker_js(card: dict) -> str:
    body = json.dumps(card, separators=(",", ":"), ensure_ascii=False)
    etag = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    if not RUNTIME_SRC.is_file():
        raise FileNotFoundError(RUNTIME_SRC)
    if not START_HERE_PATH.is_file():
        raise FileNotFoundError(START_HERE_PATH)
    runtime = RUNTIME_SRC.read_text(encoding="utf-8").replace("\r\n", "\n")
    start_here = json.loads(START_HERE_PATH.read_text(encoding="utf-8"))
    preamble = (
        f"const CARD = {json.dumps(card, ensure_ascii=False)};\n"
        f"const CARD_BODY = {json.dumps(body)};\n"
        f"const CARD_ETAG = {json.dumps(etag)};\n"
        f"const START_HERE = {json.dumps(start_here, ensure_ascii=False)};\n"
    )
    return preamble + runtime


def multipart_put(url: str, token: str, filename: str, content: str, metadata: dict) -> dict:
    boundary = uuid.uuid4().hex
    parts = []
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"metadata\"; "
        f"filename=\"metadata.json\"\r\nContent-Type: application/json\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
    )
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{filename}\"; "
        f"filename=\"{filename}\"\r\nContent-Type: application/javascript+module\r\n\r\n"
        f"{content}\r\n"
    )
    parts.append(f"--{boundary}--\r\n")
    body = "".join(parts).encode("utf-8")
    req = Request(
        url,
        data=body,
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def resolve_account_id(token: str) -> str:
    configured = cf.cloudflare_account_id()
    if configured:
        return configured
    payload = cf._api_request("GET", "/accounts?per_page=20", token)
    accounts = (payload or {}).get("result") or []
    if not accounts:
        raise RuntimeError("CLOUDFLARE_API_TOKEN cannot list accounts.")
    return accounts[0]["id"]


def ensure_route(token: str, zone: str, script: str, pattern: str) -> None:
    payload = cf._api_request("GET", f"/zones/{zone}/workers/routes", token)
    routes = (payload or {}).get("result") or []
    for route in routes:
        if route.get("pattern") == pattern:
            if route.get("script") == script:
                print(f"Worker route already configured: {pattern}")
                return
            cf._api_request(
                "PUT",
                f"/zones/{zone}/workers/routes/{route['id']}",
                token,
                {"pattern": pattern, "script": script},
            )
            print(f"Updated worker route {pattern} -> {script}")
            return
    cf._api_request(
        "POST",
        f"/zones/{zone}/workers/routes",
        token,
        {"pattern": pattern, "script": script},
    )
    print(f"Created worker route {pattern} -> {script}")


def generate_worker_source() -> str:
    if not CARD_PATH.is_file():
        raise RuntimeError("missing .well-known/mcp/server-card.json")
    card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    js = worker_js(card)
    WORKER_SRC.parent.mkdir(parents=True, exist_ok=True)
    WORKER_SRC.write_text(js, encoding="utf-8", newline="\n")
    print(f"Wrote {WORKER_SRC.relative_to(cf.BASE)}")
    return js


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Write the gitignored Worker bundle without uploading it.",
    )
    args = parser.parse_args(argv)
    try:
        js = generate_worker_source()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.generate_only:
        return 0

    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    if not token:
        print("CLOUDFLARE_API_TOKEN is required.", file=sys.stderr)
        return 1
    zone = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    account = resolve_account_id(token)
    print(f"Uploading worker {WORKER_NAME!r} to account {account}...")
    result = multipart_put(
        f"{cf.API_BASE}/accounts/{account}/workers/scripts/{WORKER_NAME}",
        token,
        "index.js",
        js,
        {"main_module": "index.js", "compatibility_date": COMPATIBILITY_DATE},
    )
    print(json.dumps(result.get("result") or result, indent=2)[:2000])
    try:
        cf._api_request(
            "POST",
            f"/accounts/{account}/workers/scripts/{WORKER_NAME}/subdomain",
            token,
            {"enabled": True, "previews_enabled": True},
        )
        print("Enabled workers.dev subdomain for the script.")
    except RuntimeError as exc:
        print(f"workers.dev subdomain enable skipped: {exc}")
    try:
        ensure_route(token, zone, WORKER_NAME, WORKER_ROUTE)
    except RuntimeError as exc:
        print(
            "Zone worker route was not created (token may lack Workers Routes Edit). "
            f"{exc}"
        )
    cf.apply_mcp_server_card_redirect(token, zone)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

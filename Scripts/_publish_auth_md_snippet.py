"""Publish Auth.md via a Cloudflare Worker.

Snippets cannot currently be created or updated with the zone token used for
Transform Rules, so this path deploys Worker `amd-auth-md`. The canonical
document remains at `auth.md` for GitHub Pages. A leftover Snippet still wins
on the apex until it can be unbound; a Redirect Rule can temporarily send the
request to workers.dev.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cloudflare_performance as cf
from _common import write_text_lf

WORKER_NAME = "amd-auth-md"
WORKER_SRC = cf.BASE / "infra" / "auth-md-worker" / "src" / "index.js"
AUTH_MD_PATH = cf.BASE / "auth.md"
COMPATIBILITY_DATE = "2024-03-01"
WORKER_ROUTE = f"{cf.SITE_HOST}/auth.md*"
RETIRED_WORKER_ROUTES = (
    f"{cf.SITE_HOST}/.well-known/oauth-protected-resource*",
    f"{cf.SITE_HOST}/.well-known/oauth-authorization-server*",
    f"{cf.SITE_HOST}/agent/auth*",
    f"{cf.SITE_HOST}/oauth2/token",
)
LIVE_URL = f"https://{cf.SITE_HOST}/auth.md"


def worker_js(auth_md: str) -> str:
    return f"""\
const AUTH_MD = {json.dumps(auth_md)};

function responseHeaders() {{
  return {{
    "content-type": {json.dumps(cf.AUTH_MD_CONTENT_TYPE)},
    "cache-control": "public, max-age=3600",
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, HEAD, OPTIONS",
  }};
}}

function respond(request) {{
  const headers = responseHeaders();
  if (request.method === "OPTIONS") {{
    return new Response(null, {{ status: 204, headers }});
  }}
  if (request.method !== "GET" && request.method !== "HEAD") {{
    headers.allow = "GET, HEAD, OPTIONS";
    return new Response(null, {{ status: 405, headers }});
  }}
  if (request.method === "HEAD") {{
    return new Response(null, {{ status: 200, headers }});
  }}
  return new Response(AUTH_MD, {{ status: 200, headers }});
}}

export default {{
  async fetch(request) {{
    const path = new URL(request.url).pathname;
    if (path === "/auth.md" || path === "/auth.md/") {{
      return respond(request);
    }}
    return new Response("Not Found", {{ status: 404 }});
  }}
}};
"""


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


def remove_retired_routes(token: str, zone: str) -> None:
    payload = cf._api_request("GET", f"/zones/{zone}/workers/routes", token)
    routes = (payload or {}).get("result") or []
    retired = set(RETIRED_WORKER_ROUTES)
    for route in routes:
        if route.get("pattern") not in retired or not route.get("id"):
            continue
        cf._api_request(
            "DELETE",
            f"/zones/{zone}/workers/routes/{route['id']}",
            token,
        )
        print(f"Removed retired worker route {route['pattern']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the Auth.md Worker.")
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Write the Worker bundle without deploying it.",
    )
    args = parser.parse_args()
    if not AUTH_MD_PATH.is_file():
        print("missing auth.md", file=sys.stderr)
        return 1
    js = worker_js(AUTH_MD_PATH.read_text(encoding="utf-8"))
    WORKER_SRC.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(WORKER_SRC, js)
    print(f"Wrote {WORKER_SRC.relative_to(cf.BASE)}")
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
    from _worker_deployment import deploy_source
    result = deploy_source(token, account, WORKER_NAME, js,
                           {"main_module": "index.js", "compatibility_date": COMPATIBILITY_DATE}, multipart_put)
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
        remove_retired_routes(token, zone)
    except RuntimeError as exc:
        print(
            "Zone worker route was not created (token may lack Workers Routes Edit). "
            f"{exc}"
        )
    cf.apply_auth_md_redirect(token, zone)
    try:
        cf.purge_cache_files(token, zone, [LIVE_URL])
    except RuntimeError as exc:
        print(f"Cache purge skipped: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

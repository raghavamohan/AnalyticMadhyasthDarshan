"""Publish Auth.md and OAuth discovery documents via a Cloudflare Worker.

Snippets cannot currently be created or updated with the zone token used for
Transform Rules, so this path deploys Worker `amd-auth-md`. The canonical
documents remain at `auth.md` and `.well-known/oauth-*` for GitHub Pages.
A leftover Snippet still wins on the apex until it can be unbound; Redirect
Rules run first, so a 302 to workers.dev serves the current documents.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cloudflare_performance as cf

WORKER_NAME = "amd-auth-md"
WORKER_SRC = cf.BASE / "infra" / "auth-md-worker" / "src" / "index.js"
AUTH_MD_PATH = cf.BASE / "auth.md"
PRM_PATH = cf.BASE / ".well-known" / "oauth-protected-resource"
AS_PATH = cf.BASE / ".well-known" / "oauth-authorization-server"
COMPATIBILITY_DATE = "2024-03-01"
WORKER_ROUTES = (
    f"{cf.SITE_HOST}/auth.md*",
    f"{cf.SITE_HOST}/.well-known/oauth-protected-resource*",
    f"{cf.SITE_HOST}/.well-known/oauth-authorization-server*",
    f"{cf.SITE_HOST}/agent/auth*",
    f"{cf.SITE_HOST}/oauth2/token",
)
LIVE_URLS = (
    f"https://{cf.SITE_HOST}/auth.md",
    f"https://{cf.SITE_HOST}/.well-known/oauth-protected-resource",
    f"https://{cf.SITE_HOST}/.well-known/oauth-authorization-server",
)
STUB_BODY = json.dumps(
    {
        "error": "not_implemented",
        "error_description": (
            "This site does not issue OAuth credentials to agents. "
            "See https://analyticmadhyasthdarshan.org/auth.md"
        ),
    },
    separators=(",", ":"),
)


def worker_js(auth_md: str, prm: str, as_metadata: str) -> str:
    return f"""\
const AUTH_MD = {json.dumps(auth_md)};
const PRM = {json.dumps(prm)};
const AS_METADATA = {json.dumps(as_metadata)};
const STUB = {json.dumps(STUB_BODY)};

function jsonHeaders(contentType) {{
  return {{
    "content-type": contentType,
    "cache-control": "public, max-age=3600",
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, HEAD, OPTIONS, POST",
  }};
}}

function respond(request, body, contentType, status) {{
  const headers = jsonHeaders(contentType);
  if (request.method === "OPTIONS") {{
    return new Response(null, {{ status: 204, headers }});
  }}
  if (request.method === "HEAD") {{
    return new Response(null, {{ status: status, headers }});
  }}
  return new Response(body, {{ status: status, headers }});
}}

export default {{
  async fetch(request) {{
    const path = new URL(request.url).pathname;
    if (path === "/auth.md" || path === "/auth.md/") {{
      return respond(request, AUTH_MD, {json.dumps(cf.AUTH_MD_CONTENT_TYPE)}, 200);
    }}
    if (path === "/.well-known/oauth-protected-resource") {{
      return respond(request, PRM, {json.dumps(cf.OAUTH_METADATA_CONTENT_TYPE)}, 200);
    }}
    if (path === "/.well-known/oauth-authorization-server") {{
      return respond(request, AS_METADATA, {json.dumps(cf.OAUTH_METADATA_CONTENT_TYPE)}, 200);
    }}
    if (path === "/agent/auth" || path === "/agent/auth/claim" || path === "/oauth2/token") {{
      return respond(request, STUB, {json.dumps(cf.OAUTH_METADATA_CONTENT_TYPE)}, 501);
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


def main() -> int:
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    if not token:
        print("CLOUDFLARE_API_TOKEN is required.", file=sys.stderr)
        return 1
    for path in (AUTH_MD_PATH, PRM_PATH, AS_PATH):
        if not path.is_file():
            print(f"missing {path.relative_to(cf.BASE)}", file=sys.stderr)
            return 1
    zone = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    account = resolve_account_id(token)
    js = worker_js(
        AUTH_MD_PATH.read_text(encoding="utf-8"),
        PRM_PATH.read_text(encoding="utf-8"),
        AS_PATH.read_text(encoding="utf-8"),
    )
    WORKER_SRC.parent.mkdir(parents=True, exist_ok=True)
    WORKER_SRC.write_text(js, encoding="utf-8", newline="\n")
    print(f"Wrote {WORKER_SRC.relative_to(cf.BASE)}")
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
        for pattern in WORKER_ROUTES:
            ensure_route(token, zone, WORKER_NAME, pattern)
    except RuntimeError as exc:
        print(
            "Zone worker route was not created (token may lack Workers Routes Edit). "
            f"{exc}"
        )
    cf.apply_auth_md_redirect(token, zone)
    try:
        cf.purge_cache_files(token, zone, list(LIVE_URLS))
    except RuntimeError as exc:
        print(f"Cache purge skipped: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

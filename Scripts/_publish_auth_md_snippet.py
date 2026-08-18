"""Publish Auth.md and OAuth discovery documents via a Cloudflare Snippet."""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cloudflare_performance as cf

SNIPPET_NAME = "amd_auth_md"
AUTH_MD_PATH = cf.BASE / "auth.md"
PRM_PATH = cf.BASE / ".well-known" / "oauth-protected-resource"
AS_PATH = cf.BASE / ".well-known" / "oauth-authorization-server"
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


def snippet_js(auth_md: str, prm: str, as_metadata: str) -> str:
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
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"metadata\"\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
    )
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{filename}\"\r\n"
        f"Content-Type: application/javascript\r\n\r\n{content}\r\n"
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
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def main() -> int:
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    if not token:
        print("CLOUDFLARE_API_TOKEN is required.", file=sys.stderr)
        return 1
    zone = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    auth_md = AUTH_MD_PATH.read_text(encoding="utf-8")
    prm = PRM_PATH.read_text(encoding="utf-8")
    as_metadata = AS_PATH.read_text(encoding="utf-8")
    js = snippet_js(auth_md, prm, as_metadata)
    print(f"Uploading snippet {SNIPPET_NAME!r} to zone {zone}...")
    result = multipart_put(
        f"{cf.API_BASE}/zones/{zone}/snippets/{SNIPPET_NAME}",
        token,
        "main.js",
        js,
        {"main_module": "main.js"},
    )
    print(json.dumps(result.get("result") or result, indent=2))

    existing = cf._api_request(
        "GET", f"/zones/{zone}/snippets/snippet_rules", token, allow_404=True
    )
    rules = []
    if existing:
        result = existing.get("result")
        if isinstance(result, list):
            rules = result
        elif isinstance(result, dict):
            rules = result.get("rules") or []
    kept = [rule for rule in rules if rule.get("snippet_name") != SNIPPET_NAME]
    kept.append(
        {
            "description": "Auth.md and OAuth discovery documents",
            "enabled": True,
            "expression": cf.AUTH_MD_SNIPPET_EXPRESSION,
            "snippet_name": SNIPPET_NAME,
        }
    )
    updated = cf._api_request(
        "PUT",
        f"/zones/{zone}/snippets/snippet_rules",
        token,
        {"rules": kept},
    )
    print("Snippet rules updated.")
    print(json.dumps((updated or {}).get("result") or updated, indent=2)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

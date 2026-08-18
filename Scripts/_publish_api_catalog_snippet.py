"""One-shot: publish RFC 9727 api-catalog via a Cloudflare Snippet (zone token)."""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cloudflare_performance as cf

SNIPPET_NAME = "amd_api_catalog"
CATALOG_PATH = cf.BASE / ".well-known" / "api-catalog"


def snippet_js(catalog: dict) -> str:
    body = json.dumps(catalog, separators=(",", ":"))
    return f"""\
const BODY = {json.dumps(body)};
const HEADERS = {{
  "content-type": {json.dumps(cf.API_CATALOG_CONTENT_TYPE)},
  "link": {json.dumps(cf.API_CATALOG_LINK)},
  "cache-control": "public, max-age=3600",
  "access-control-allow-origin": "*"
}};

export default {{
  async fetch(request) {{
    if (request.method === "OPTIONS") {{
      return new Response(null, {{ status: 204, headers: HEADERS }});
    }}
    if (request.method === "HEAD") {{
      return new Response(null, {{ status: 200, headers: HEADERS }});
    }}
    return new Response(BODY, {{ status: 200, headers: HEADERS }});
  }}
}};
"""


def multipart_put(url: str, token: str, filename: str, content: str, metadata: dict) -> dict:
    boundary = uuid.uuid4().hex
    parts = []
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"metadata\"\r\n\r\n{json.dumps(metadata)}\r\n")
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
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    js = snippet_js(catalog)
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
            "description": "RFC 9727 api-catalog well-known URI",
            "enabled": True,
            "expression": cf.API_CATALOG_HEADERS_EXPRESSION,
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

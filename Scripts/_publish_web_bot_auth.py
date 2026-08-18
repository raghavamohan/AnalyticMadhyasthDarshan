"""Publish the Web Bot Auth JWKS directory via a Cloudflare Worker.

Snippets cannot currently be created with the zone token used for Transform
Rules, so this path deploys Worker `amd-web-bot-auth`. The public JWKS remains
at `.well-known/http-message-signatures-directory` for GitHub Pages.
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
from _web_bot_auth import DIRECTORY_CONTENT_TYPE, DIRECTORY_PATH, private_jwk_from_env

WORKER_NAME = "amd-web-bot-auth"
WORKER_ROUTE = f"{cf.SITE_HOST}/.well-known/http-message-signatures-directory"
WORKER_SRC = cf.BASE / "infra" / "web-bot-auth-worker" / "src" / "index.js"
COMPATIBILITY_DATE = "2024-09-23"


def worker_js(directory: dict, private_jwk: dict) -> str:
    body = json.dumps(directory, separators=(",", ":"), ensure_ascii=False)
    return f"""\
const BODY = {json.dumps(body)};
const PRIVATE_JWK = {json.dumps(private_jwk)};
const CONTENT_TYPE = {json.dumps(DIRECTORY_CONTENT_TYPE)};
function b64(bytes) {{
  let binary = "";
  const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  for (const value of view) binary += String.fromCharCode(value);
  return btoa(binary);
}}

function randomNonce() {{
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return b64(bytes);
}}

async function importSigningKey() {{
  return crypto.subtle.importKey(
    "jwk",
    {{
      kty: PRIVATE_JWK.kty,
      crv: PRIVATE_JWK.crv,
      x: PRIVATE_JWK.x,
      d: PRIVATE_JWK.d,
      ext: true,
      key_ops: ["sign"]
    }},
    {{ name: "Ed25519" }},
    false,
    ["sign"]
  );
}}

async function signBase(key, signatureBase) {{
  const signature = await crypto.subtle.sign(
    {{ name: "Ed25519" }},
    key,
    new TextEncoder().encode(signatureBase)
  );
  return b64(signature);
}}

async function directoryHeaders(request) {{
  const created = Math.floor(Date.now() / 1000);
  const expires = created + 300;
  const nonce = randomNonce();
  const keyid = PRIVATE_JWK.kid;
  const authority = new URL(request.url).host;
  const params =
    `("@authority";req);alg="ed25519";keyid="${{keyid}}";nonce="${{nonce}}";` +
    `tag="http-message-signatures-directory";created=${{created}};expires=${{expires}}`;
  const signatureBase =
    `"@authority";req: ${{authority}}\\n` +
    `"@signature-params": ${{params}}`;
  const key = await importSigningKey();
  const signature = await signBase(key, signatureBase);
  return {{
    "content-type": CONTENT_TYPE,
    "cache-control": "public, max-age=300",
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, HEAD, OPTIONS",
    "access-control-expose-headers": "Signature, Signature-Input",
    "Signature-Input": `sig1=${{params}}`,
    "Signature": `sig1=:${{signature}}:`
  }};
}}

function directoryPath(pathname) {{
  return (pathname.replace(/\\/+$/, "") || "/") === "/.well-known/http-message-signatures-directory";
}}

export default {{
  async fetch(request) {{
    const url = new URL(request.url);
    if (directoryPath(url.pathname)) {{
      if (request.method === "OPTIONS") {{
        return new Response(null, {{
          status: 204,
          headers: await directoryHeaders(request)
        }});
      }}
      if (request.method === "HEAD") {{
        return new Response(null, {{
          status: 200,
          headers: await directoryHeaders(request)
        }});
      }}
      if (request.method === "GET") {{
        return new Response(BODY, {{
          status: 200,
          headers: await directoryHeaders(request)
        }});
      }}
      return new Response("Method Not Allowed", {{ status: 405 }});
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
    if not DIRECTORY_PATH.is_file():
        print("missing .well-known/http-message-signatures-directory", file=sys.stderr)
        return 1
    private = private_jwk_from_env()
    if not private or not private.get("d"):
        print("WEB_BOT_AUTH_PRIVATE_JWK is required in .env.", file=sys.stderr)
        return 1
    zone = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    account = resolve_account_id(token)
    directory = json.loads(DIRECTORY_PATH.read_text(encoding="utf-8"))
    js = worker_js(directory, private)
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
        ensure_route(token, zone, WORKER_NAME, WORKER_ROUTE)
    except RuntimeError as exc:
        print(
            "Zone worker route was not created (token may lack Workers Routes Edit). "
            f"{exc}"
        )
    cf.apply_web_bot_auth_redirect(token, zone)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

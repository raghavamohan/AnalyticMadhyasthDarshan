"""Validate the Web Bot Auth HTTP Message Signatures directory.

Run from the repository root:

    python Scripts/_test_web_bot_auth.py
    python Scripts/_test_web_bot_auth.py --live
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _cloudflare_performance import HOMEPAGE_LINK, load_repo_env
from _web_bot_auth import (
    DIRECTORY_CONTENT_TYPE,
    DIRECTORY_PATH,
    DIRECTORY_SITE_PATH,
    SIGNATURE_AGENT_ORIGIN,
    jwk_thumbprint,
    load_directory,
    private_jwk_from_env,
    public_keys,
    sign_outgoing_request,
)

SITE = "https://analyticmadhyasthdarshan.org"
LIVE_UA = "AnalyticMadhyasthDarshan-web-bot-auth-test/1.0"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check_directory() -> dict:
    if not DIRECTORY_PATH.is_file():
        fail("missing .well-known/http-message-signatures-directory")
    payload = load_directory()
    keys = public_keys(payload)
    if not keys:
        fail("JWKS keys must contain at least one public key")
    for key in keys:
        if key.get("kty") != "OKP" or key.get("crv") != "Ed25519" or not key.get("x"):
            fail("each key must be an Ed25519 OKP public JWK with x")
        if "d" in key:
            fail("public JWKS must not include the private d parameter")
        kid = key.get("kid")
        thumb = jwk_thumbprint(key)
        if kid and kid != thumb:
            fail(f"kid {kid!r} does not match JWK thumbprint {thumb!r}")
    print("OK: Web Bot Auth directory is a JWKS with an Ed25519 public key.")
    return payload


def check_homepage_link() -> None:
    if DIRECTORY_SITE_PATH not in HOMEPAGE_LINK:
        fail("HOMEPAGE_LINK does not advertise the Web Bot Auth directory")
    print("OK: homepage Link header advertises the Web Bot Auth directory.")


def check_outgoing_signature() -> None:
    load_repo_env()
    private = private_jwk_from_env()
    if private is None:
        print("SKIP: WEB_BOT_AUTH_PRIVATE_JWK is not set; outbound signing not checked.")
        return
    if "d" not in private:
        fail("WEB_BOT_AUTH_PRIVATE_JWK is missing d")
    headers = sign_outgoing_request("https://example.com/robots.txt", private)
    if headers.get("Signature-Agent") != f'"{SIGNATURE_AGENT_ORIGIN}"':
        fail(f"Signature-Agent is {headers.get('Signature-Agent')!r}")
    signature_input = headers.get("Signature-Input") or ""
    if 'tag="web-bot-auth"' not in signature_input:
        fail("Signature-Input is missing tag=web-bot-auth")
    if '"@authority"' not in signature_input or '"signature-agent"' not in signature_input:
        fail("Signature-Input must cover @authority and signature-agent")
    if not (headers.get("Signature") or "").startswith("sig1=:"):
        fail("Signature header is missing")
    print("OK: outbound bot requests get Signature-Agent and Signature-Input.")


def check_live() -> None:
    url = f"{SITE}{DIRECTORY_SITE_PATH}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": LIVE_UA,
            "Accept": DIRECTORY_CONTENT_TYPE + ", application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            content_type = response.headers.get("Content-Type") or ""
            signature = response.headers.get("Signature") or ""
            signature_input = response.headers.get("Signature-Input") or ""
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        fail(f"live Web Bot Auth directory returned HTTP {exc.code}")
    except urllib.error.URLError as exc:
        fail(f"live Web Bot Auth directory request failed: {exc}")
    if status != 200:
        fail(f"live Web Bot Auth directory returned HTTP {status}")
    if "json" not in content_type.lower():
        fail(f"live Web Bot Auth directory Content-Type is {content_type!r}")
    payload = json.loads(body)
    live_keys = public_keys(payload)
    if not live_keys:
        fail("live directory has no public keys")
    if any("d" in key for key in live_keys):
        fail("live directory includes a private d parameter")
    if signature_input and 'tag="http-message-signatures-directory"' not in signature_input:
        fail("live Signature-Input is missing the directory tag")
    if signature_input and not signature:
        fail("live directory sent Signature-Input without Signature")
    print("OK: live /.well-known/http-message-signatures-directory is a JWKS.")


def main() -> None:
    check_directory()
    check_homepage_link()
    check_outgoing_signature()
    if "--live" in sys.argv:
        check_live()


if __name__ == "__main__":
    main()

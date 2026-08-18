"""Web Bot Auth helpers: JWKS directory and outbound request signatures."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import time
from urllib.parse import urlparse

from _common import BASE

DIRECTORY_PATH = BASE / ".well-known" / "http-message-signatures-directory"
DIRECTORY_SITE_PATH = "/.well-known/http-message-signatures-directory"
DIRECTORY_CONTENT_TYPE = "application/http-message-signatures-directory+json"
SIGNATURE_AGENT_ORIGIN = "https://analyticmadhyasthdarshan.org"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def jwk_thumbprint(jwk: dict) -> str:
    canon = json.dumps(
        {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"]},
        separators=(",", ":"),
        sort_keys=True,
    )
    return b64url(hashlib.sha256(canon.encode("ascii")).digest())


def load_directory() -> dict:
    return json.loads(DIRECTORY_PATH.read_text(encoding="utf-8"))


def public_keys(directory: dict | None = None) -> list[dict]:
    payload = directory if directory is not None else load_directory()
    keys = payload.get("keys")
    if not isinstance(keys, list):
        return []
    return [key for key in keys if isinstance(key, dict)]


def private_jwk_from_env() -> dict | None:
    raw = os.environ.get("WEB_BOT_AUTH_PRIVATE_JWK")
    if not raw:
        return None
    data = json.loads(raw)
    return data if isinstance(data, dict) else None


def _node_sign(message: str, private_jwk: dict) -> str:
    script = (
        "const crypto=require('crypto');"
        "const jwk=JSON.parse(process.env.WEB_BOT_AUTH_SIGN_JWK);"
        "const key=crypto.createPrivateKey({key:jwk,format:'jwk'});"
        "const sig=crypto.sign(null,Buffer.from(process.env.WEB_BOT_AUTH_SIGN_MSG,'utf8'),key);"
        "process.stdout.write(sig.toString('base64'));"
    )
    env = os.environ.copy()
    env["WEB_BOT_AUTH_SIGN_JWK"] = json.dumps(private_jwk)
    env["WEB_BOT_AUTH_SIGN_MSG"] = message
    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    return completed.stdout.strip()


def sign_outgoing_request(
    url: str,
    private_jwk: dict,
    *,
    created: int | None = None,
    lifetime_sec: int = 60,
) -> dict[str, str]:
    """Return Signature-Agent, Signature-Input, and Signature for an outbound GET."""
    parsed = urlparse(url)
    authority = parsed.netloc
    created = int(time.time() if created is None else created)
    expires = created + lifetime_sec
    keyid = private_jwk.get("kid") or jwk_thumbprint(private_jwk)
    nonce = b64url(os.urandom(32))
    params = (
        f'("@authority" "signature-agent");created={created};keyid="{keyid}";'
        f'alg="ed25519";expires={expires};nonce="{nonce}";tag="web-bot-auth"'
    )
    signature_input = f"sig1={params}"
    signature_agent = f'"{SIGNATURE_AGENT_ORIGIN}"'
    signature_base = (
        f'"@authority": {authority}\n'
        f'"signature-agent": {signature_agent}\n'
        f'"@signature-params": {params}'
    )
    signature = _node_sign(signature_base, private_jwk)
    return {
        "Signature-Agent": signature_agent,
        "Signature-Input": signature_input,
        "Signature": f"sig1=:{signature}:",
    }

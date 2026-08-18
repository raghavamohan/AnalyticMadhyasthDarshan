"""Validate Auth.md and OAuth discovery documents.

Run from the repository root:

    python Scripts/_test_auth_md.py
    python Scripts/_test_auth_md.py --live
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE

SITE = "https://analyticmadhyasthdarshan.org"
AUTH_MD_PATH = BASE / "auth.md"
PRM_PATH = BASE / ".well-known" / "oauth-protected-resource"
AS_PATH = BASE / ".well-known" / "oauth-authorization-server"
ISSUER = f"{SITE}"
RESOURCE = f"{SITE}/"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(BASE)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail(f"{path.name} must be a JSON object")
    return data


def check_auth_md() -> str:
    if not AUTH_MD_PATH.is_file():
        fail("missing auth.md")
    text = AUTH_MD_PATH.read_text(encoding="utf-8")
    heading = next((line for line in text.splitlines() if line.startswith("#")), "")
    if "auth.md" not in heading.lower():
        fail("auth.md H1 must contain 'auth.md'")
    for needle in (
        "GitHub",
        "magic link",
        "https://analyticmadhyasthdarshan.org/.well-known/oauth-protected-resource",
        "https://analyticmadhyasthdarshan.org/.well-known/oauth-authorization-server",
        "https://analyticmadhyasthdarshan.org/.well-known/agent-card.json",
    ):
        if needle not in text:
            fail(f"auth.md should document {needle!r}")
    print("OK: auth.md has an auth.md heading and documents human provisioning.")
    return text


def check_prm(as_doc: dict) -> dict:
    prm = load_json(PRM_PATH)
    if prm.get("resource") != RESOURCE:
        fail(f"PRM resource is {prm.get('resource')!r}")
    servers = prm.get("authorization_servers")
    if not isinstance(servers, list) or ISSUER not in servers:
        fail("PRM authorization_servers must include the site issuer")
    scopes = prm.get("scopes_supported")
    if not isinstance(scopes, list) or not scopes:
        fail("PRM scopes_supported must be a non-empty array")
    methods = prm.get("bearer_methods_supported")
    if not isinstance(methods, list) or "header" not in methods:
        fail("PRM bearer_methods_supported must include 'header'")
    if as_doc.get("issuer") not in servers:
        fail("Authorization Server issuer is not listed in PRM authorization_servers")
    print("OK: Protected Resource Metadata lists resource, AS, scopes, and header bearer.")
    return prm


def check_as_metadata() -> dict:
    as_doc = load_json(AS_PATH)
    if as_doc.get("issuer") != ISSUER:
        fail(f"AS issuer is {as_doc.get('issuer')!r}")
    if as_doc.get("service_documentation") != f"{SITE}/auth.md":
        fail("AS metadata service_documentation must point at /auth.md")
    if not as_doc.get("token_endpoint"):
        fail("AS metadata is missing token_endpoint")
    agent_auth = as_doc.get("agent_auth")
    if not isinstance(agent_auth, dict):
        fail("AS metadata is missing agent_auth")
    if agent_auth.get("skill") != f"{SITE}/auth.md":
        fail("agent_auth.skill must point at /auth.md")
    register_uri = agent_auth.get("register_uri") or agent_auth.get("identity_endpoint")
    if not register_uri:
        fail("agent_auth must include register_uri")
    assertion = agent_auth.get("identity_assertion")
    if not isinstance(assertion, dict):
        fail("agent_auth is missing a complete identity_assertion method")
    types = assertion.get("assertion_types_supported")
    if not isinstance(types, list) or "verified_email" not in types:
        fail("identity_assertion.assertion_types_supported must include verified_email")
    creds = assertion.get("credential_types_supported")
    if not isinstance(creds, list) or not creds:
        fail("identity_assertion.credential_types_supported must be a non-empty array")
    claim_uri = agent_auth.get("claim_uri") or agent_auth.get("claim_endpoint")
    if not claim_uri:
        fail("verified_email registration requires claim_uri")
    supported = agent_auth.get("identity_types_supported")
    if not isinstance(supported, list) or "identity_assertion" not in supported:
        fail("identity_types_supported must include identity_assertion")
    print("OK: Authorization Server metadata has issuer, skill, register_uri, and verified_email.")
    return as_doc


def fetch(url: str) -> tuple[int, str, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AnalyticMadhyasthDarshan-auth-md-test/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return (
                response.status,
                response.headers.get("Content-Type") or "",
                response.read().decode("utf-8"),
            )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, (exc.headers.get("Content-Type") if exc.headers else "") or "", body
    except urllib.error.URLError as exc:
        fail(f"{url} request failed: {exc}")


def check_live() -> None:
    status, content_type, body = fetch(f"{SITE}/auth.md")
    if status != 200:
        fail(f"live /auth.md returned HTTP {status}")
    if "markdown" not in content_type and "text/plain" not in content_type:
        fail(f"live /auth.md Content-Type is {content_type!r}")
    if "auth.md" not in body.splitlines()[0].lower():
        fail("live /auth.md heading does not contain auth.md")

    status, content_type, body = fetch(f"{SITE}/.well-known/oauth-protected-resource")
    if status != 200:
        fail(f"live PRM returned HTTP {status}")
    if "json" not in content_type:
        fail(f"live PRM Content-Type is {content_type!r}")
    prm = json.loads(body)
    if prm.get("resource") != RESOURCE:
        fail("live PRM resource mismatch")

    status, content_type, body = fetch(f"{SITE}/.well-known/oauth-authorization-server")
    if status != 200:
        fail(f"live AS metadata returned HTTP {status}")
    if "json" not in content_type:
        fail(f"live AS metadata Content-Type is {content_type!r}")
    as_doc = json.loads(body)
    if as_doc.get("issuer") != ISSUER:
        fail("live AS issuer mismatch")
    if as_doc.get("service_documentation") != f"{SITE}/auth.md":
        fail("live AS metadata is missing service_documentation")
    if not as_doc.get("agent_auth", {}).get("register_uri"):
        fail("live AS metadata is missing agent_auth.register_uri")
    print("OK: live auth.md, PRM, and Authorization Server metadata.")


def main() -> None:
    check_auth_md()
    as_doc = check_as_metadata()
    check_prm(as_doc)
    print("OK: Auth.md discovery documents.")
    if "--live" in sys.argv:
        check_live()


if __name__ == "__main__":
    main()

"""Validate Auth.md as the canonical public identity policy.

Run from the repository root:

    python Scripts/_test_auth_md.py
    python Scripts/_test_auth_md.py --live
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE
from _publish_auth_md_snippet import worker_js

SITE = "https://analyticmadhyasthdarshan.org"
AUTH_MD_PATH = BASE / "auth.md"
RETIRED_PATHS = (
    BASE / ".well-known" / "agent-card.json",
    BASE / ".well-known" / "oauth-protected-resource",
    BASE / ".well-known" / "oauth-authorization-server",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


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
        "first-party cookie",
        "Content-Type: application/json",
        "https://analyticmadhyasthdarshan.org/.well-known/api-catalog",
        "https://analyticmadhyasthdarshan.org/.well-known/agent-skills/index.json",
        "https://analyticmadhyasthdarshan.org/.well-known/mcp/server-card.json",
        "https://analyticmadhyasthdarshan.org/.well-known/http-message-signatures-directory",
        "https://analyticmadhyasthdarshan.org/webmcp.js",
        "https://analyticmadhyasthdarshan.org/Studies/glossary.json",
        "https://analyticmadhyasthdarshan.org/Studies/catalog-all.json",
        "https://analyticmadhyasthdarshan.org/api/studies",
        "https://analyticmadhyasthdarshan.org/api/start-here",
        "https://analyticmadhyasthdarshan.org/api/cite/{slug}",
        "https://analyticmadhyasthdarshan.org/.well-known/agent-skills/index-maintainer.json",
        "/mcp",
        "get_cite",
        "_index._agents.analyticmadhyasthdarshan.org",
    ):
        if needle not in text:
            fail(f"auth.md should document {needle!r}")
    for forbidden in (
        "/.well-known/agent-card.json",
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-authorization-server",
        "register_uri",
        "claim_uri",
    ):
        if forbidden in text:
            fail(f"auth.md still advertises retired surface {forbidden!r}")
    for path in RETIRED_PATHS:
        if path.exists():
            fail(f"retired discovery document still exists: {path.relative_to(BASE)}")
    generated = worker_js(text)
    if "const AUTH_MD" not in generated or "OAuth discovery" in generated:
        fail("generated Auth.md Worker is missing Auth.md or still embeds OAuth discovery")
    print("OK: Auth.md documents the implemented identity policy only.")
    return text


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


def check_live(expected: str) -> None:
    status, content_type, body = fetch(f"{SITE}/auth.md")
    if status != 200:
        fail(f"live /auth.md returned HTTP {status}")
    if "markdown" not in content_type and "text/plain" not in content_type:
        fail(f"live /auth.md Content-Type is {content_type!r}")
    if body != expected:
        fail("live /auth.md does not exactly match the repository document")

    for path in (
        "/.well-known/agent-card.json",
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-authorization-server",
        "/agent/auth",
        "/agent/auth/claim",
        "/oauth2/token",
    ):
        status, _content_type, _body = fetch(f"{SITE}{path}")
        if status != 404:
            fail(f"retired endpoint {path} returned HTTP {status}, expected 404")
    print("OK: live Auth.md is exact and retired discovery endpoints return 404.")


def main() -> None:
    text = check_auth_md()
    if "--live" in sys.argv:
        check_live(text)


if __name__ == "__main__":
    main()

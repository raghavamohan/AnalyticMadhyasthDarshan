"""Validate the MCP Server Card (SEP-1649).

Run from the repository root:

    python Scripts/_test_mcp_server_card.py
    python Scripts/_test_mcp_server_card.py --live
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
from _cloudflare_performance import HOMEPAGE_LINK

SITE = "https://analyticmadhyasthdarshan.org"
CARD_PATH = BASE / ".well-known" / "mcp" / "server-card.json"
CARD_SITE_PATH = "/.well-known/mcp/server-card.json"
LIVE_UA = "AnalyticMadhyasthDarshan-mcp-server-card-test/1.0"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_card() -> dict:
    if not CARD_PATH.is_file():
        fail("missing .well-known/mcp/server-card.json")
    data = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("server-card.json must be a JSON object")
    return data


def check_card(card: dict) -> None:
    server_info = card.get("serverInfo")
    if not isinstance(server_info, dict):
        fail("serverInfo must be an object")
    if not server_info.get("name") or not server_info.get("version"):
        fail("serverInfo.name and serverInfo.version must be non-empty")
    transport = card.get("transport")
    if not isinstance(transport, dict):
        fail("transport must be an object")
    if not transport.get("type"):
        fail("transport.type must be non-empty")
    endpoint = transport.get("endpoint") or card.get("url")
    if not endpoint:
        fail("transport.endpoint or url must name the Streamable HTTP path")
    capabilities = card.get("capabilities")
    if not isinstance(capabilities, dict) or not capabilities:
        fail("capabilities must be a non-empty object")
    for key in ("tools", "resources", "prompts"):
        if key not in capabilities:
            fail(f"capabilities is missing {key!r}")
    print("OK: MCP Server Card has serverInfo, transport endpoint, and capabilities.")


def check_homepage_link() -> None:
    if CARD_SITE_PATH not in HOMEPAGE_LINK:
        fail("HOMEPAGE_LINK does not advertise /.well-known/mcp/server-card.json")
    if '</mcp>; rel="describedby"' not in HOMEPAGE_LINK:
        fail("HOMEPAGE_LINK does not advertise /mcp")
    runtime = BASE / "infra" / "mcp-worker" / "src" / "runtime.js"
    if not runtime.is_file():
        fail("missing infra/mcp-worker/src/runtime.js")
    text = runtime.read_text(encoding="utf-8")
    for needle in (
        "search_studies",
        "list_studies",
        "get_study",
        "get_study_outline",
        "get_glossary",
        "get_start_here",
        "get_cite",
        "/api/studies",
        "/api/glossary",
        "/api/start-here",
        "handleCite",
        "loadStartHere",
        "studies://study/",
    ):
        if needle not in text:
            fail(f"MCP runtime is missing {needle!r}")
    print("OK: homepage Link header advertises the MCP Server Card and /mcp.")


def check_live() -> None:
    url = f"{SITE}{CARD_SITE_PATH}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": LIVE_UA, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            content_type = response.headers.get("Content-Type") or ""
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        fail(f"live MCP Server Card returned HTTP {exc.code}")
    except urllib.error.URLError as exc:
        fail(f"live MCP Server Card request failed: {exc}")
    if status != 200:
        fail(f"live MCP Server Card returned HTTP {status}")
    if "json" not in content_type.lower():
        fail(f"live MCP Server Card Content-Type is {content_type!r}")
    payload = json.loads(body)
    check_card(payload)
    print("OK: live /.well-known/mcp/server-card.json is MCP Server Card JSON.")


def main() -> None:
    check_card(load_card())
    check_homepage_link()
    if "--live" in sys.argv:
        check_live()


if __name__ == "__main__":
    main()

"""Validate WebMCP tool registration for in-browser agents.

Run from the repository root:

    python Scripts/_test_webmcp.py
    python Scripts/_test_webmcp.py --live
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _cloudflare_performance import HOMEPAGE_LINK
from _common import BASE

SITE = "https://analyticmadhyasthdarshan.org"
SCRIPT_PATH = BASE / "webmcp.js"
SCRIPT_SITE_PATH = "/webmcp.js"
INDEX_HTML = BASE / "index.html"
API_DOCS = BASE / "api-docs.html"
STUDIES_INDEX = BASE / "Studies" / "index.html"
INDEX_TEMPLATE = BASE / "Scripts" / "_build_studies_index.py"
SCRIPT_SRC = '<script src="/webmcp.js"></script>'
REQUIRED_TOOLS = (
    "search_studies",
    "list_studies",
    "get_study",
    "open_study",
    "open_page",
)
LIVE_UA = "AnalyticMadhyasthDarshan-webmcp-test/1.0"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check_script() -> str:
    if not SCRIPT_PATH.is_file():
        fail("missing webmcp.js")
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    if "navigator.modelContext.registerTool" not in text:
        fail("webmcp.js must call navigator.modelContext.registerTool")
    if "AbortController" not in text:
        fail("webmcp.js must use AbortController to unregister tools")
    if "inputSchema" not in text:
        fail("webmcp.js tools must declare inputSchema")
    if "execute:" not in text and "execute :" not in text:
        fail("webmcp.js tools must declare an execute callback")
    missing = [name for name in REQUIRED_TOOLS if f'name: "{name}"' not in text]
    if missing:
        fail(f"webmcp.js is missing tools {missing}")
    print("OK: webmcp.js registers catalog search, retrieval, and navigation tools.")
    return text


def check_pages() -> None:
    template = INDEX_TEMPLATE.read_text(encoding="utf-8")
    if SCRIPT_SRC not in template:
        fail("INDEX_TEMPLATE must load /webmcp.js on the studies landing page")
    for path in (INDEX_HTML, API_DOCS, STUDIES_INDEX):
        if not path.is_file():
            fail(f"missing {path.relative_to(BASE)}")
        html = path.read_text(encoding="utf-8")
        if SCRIPT_SRC not in html:
            fail(f"{path.relative_to(BASE)} must load /webmcp.js on page load")
    print("OK: homepage, studies catalog, and api-docs load /webmcp.js.")


def check_homepage_link() -> None:
    if SCRIPT_SITE_PATH not in HOMEPAGE_LINK:
        fail("HOMEPAGE_LINK does not advertise /webmcp.js")
    print("OK: homepage Link header advertises /webmcp.js.")


def fetch(url: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": LIVE_UA, "Accept": "*/*"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.headers.get("Content-Type") or "", response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type") or "", exc.read()


def check_live() -> None:
    status, content_type, body = fetch(f"{SITE}{SCRIPT_SITE_PATH}")
    if status != 200:
        fail(f"live /webmcp.js returned HTTP {status}")
    text = body.decode("utf-8", errors="replace")
    if "navigator.modelContext.registerTool" not in text:
        fail("live /webmcp.js does not call navigator.modelContext.registerTool")
    if "javascript" not in content_type.lower() and "ecmascript" not in content_type.lower():
        print(f"NOTE: live /webmcp.js Content-Type is {content_type!r}")
    for path in ("/", "/Studies/index.html", "/api-docs.html"):
        page_status, _page_type, page_body = fetch(f"{SITE}{path}")
        if page_status not in (200, 301, 302):
            fail(f"live {path} returned HTTP {page_status}")
        page_text = page_body.decode("utf-8", errors="replace")
        if SCRIPT_SRC not in page_text and "webmcp.js" not in page_text:
            fail(f"live {path} does not load /webmcp.js")
    print("OK: live /webmcp.js and catalog pages register WebMCP tools.")


def main() -> None:
    check_script()
    check_pages()
    check_homepage_link()
    if "--live" in sys.argv:
        check_live()


if __name__ == "__main__":
    main()

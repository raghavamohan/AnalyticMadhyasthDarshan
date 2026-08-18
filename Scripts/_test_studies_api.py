"""Validate unified catalog JSON, the change feed, llms.txt, and catalog search.

Run from the repository root:

    python Scripts/_test_studies_api.py
    python Scripts/_test_studies_api.py --live
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE, STUDIES
from _study_catalog import (
    CATALOG_ALL_PATH,
    CATALOG_TABLES,
    LLMS_FULL_TXT_PATH,
    LLMS_TXT_PATH,
    STUDIES_FEED_PATH,
    StudyStatus,
    catalog_json_path,
)

SITE = "https://analyticmadhyasthdarshan.org"
WORKER = "https://amd-mcp.raghavamohan.workers.dev"
LIVE_UA = "AnalyticMadhyasthDarshan-studies-api-test/1.0"
DOCUMENT_KEYS = ("html", "pdf", "md")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json(path: Path) -> object:
    if not path.is_file():
        fail(f"missing {path.relative_to(BASE)}")
    return json.loads(path.read_text(encoding="utf-8"))


def matches_query(entry: dict, query: str) -> bool:
    if not query:
        return True
    haystack = " ".join(
        [
            str(entry.get("slug") or ""),
            str(entry.get("title") or ""),
            str(entry.get("description") or ""),
            str(entry.get("category") or ""),
            " ".join(entry.get("categories") or []),
        ]
    ).lower()
    return query.lower() in haystack


def check_catalog_all() -> list[dict]:
    payload = load_json(CATALOG_ALL_PATH)
    if not isinstance(payload, list) or not payload:
        fail("catalog-all.json must be a non-empty array")
    by_table: dict[str, list[dict]] = {}
    for table in CATALOG_TABLES:
        entries = load_json(catalog_json_path(table))
        if not isinstance(entries, list):
            fail(f"{catalog_json_path(table).name} must be an array")
        by_table[table.value] = entries
    expected = sum(len(rows) for rows in by_table.values())
    if len(payload) != expected:
        fail(f"catalog-all.json has {len(payload)} rows, expected {expected}")
    collections = {"topical", "formal", "applied"}
    seen: set[tuple[str, str]] = set()
    for row in payload:
        if not isinstance(row, dict):
            fail("catalog-all.json rows must be objects")
        collection = row.get("collection")
        slug = row.get("slug")
        if collection not in collections:
            fail(f"{slug}: collection {collection!r} is invalid")
        if not slug:
            fail("catalog-all.json row is missing slug")
        key = (collection, slug)
        if key in seen:
            fail(f"duplicate catalog-all row {key}")
        seen.add(key)
        status = row.get("status")
        if status == StudyStatus.ONGOING.value:
            offending = [key_name for key_name in DOCUMENT_KEYS if row.get(key_name)]
            if offending:
                fail(f"{slug}: ongoing row still has {offending}")
        else:
            if not row.get("md"):
                fail(f"{slug}: draft/released row is missing md")
            if not row.get("html"):
                fail(f"{slug}: draft/released row is missing html")
    print("OK: catalog-all.json tags every row and advertises md on published studies.")
    return payload


def check_feed(rows: list[dict]) -> None:
    feed = load_json(STUDIES_FEED_PATH)
    if not isinstance(feed, dict):
        fail("feed.json must be an object")
    if feed.get("version") != "https://jsonfeed.org/version/1.1":
        fail(f"feed.json version is {feed.get('version')!r}")
    items = feed.get("items")
    if not isinstance(items, list) or not items:
        fail("feed.json items must be a non-empty array")
    published = [row for row in rows if row.get("status") != StudyStatus.ONGOING.value]
    if len(items) != len(published):
        fail(f"feed.json has {len(items)} items, expected {len(published)} published rows")
    dates = [item.get("date_modified") or "" for item in items]
    if dates != sorted(dates, reverse=True):
        fail("feed.json items are not newest-first by date_modified")
    print("OK: Studies/feed.json is JSON Feed 1.1, newest Edited-on first.")


def check_llms(rows: list[dict]) -> None:
    if not LLMS_TXT_PATH.is_file():
        fail("missing llms.txt")
    if not LLMS_FULL_TXT_PATH.is_file():
        fail("missing llms-full.txt")
    text = LLMS_TXT_PATH.read_text(encoding="utf-8")
    full = LLMS_FULL_TXT_PATH.read_text(encoding="utf-8")
    if not text.startswith("# Analytic Madhyasth Darshan"):
        fail("llms.txt must start with the site title")
    published = [row for row in rows if row.get("status") != StudyStatus.ONGOING.value]
    missing = [row["slug"] for row in published if row["slug"] not in full]
    if missing:
        fail(f"llms-full.txt is missing slugs {missing[:5]}")
    for needle in (
        "/Studies/catalog-all.json",
        "/Studies/glossary.json",
        "/Studies/feed.json",
        "/.well-known/api-catalog",
    ):
        if needle not in text:
            fail(f"llms.txt should link {needle}")
    print("OK: llms.txt and llms-full.txt list published studies.")


def check_search(rows: list[dict]) -> None:
    ontology = [row for row in rows if matches_query(row, "ontology")]
    if not ontology:
        fail("expected catalog-all.json to contain ontology matches")
    by_slug = [row for row in rows if row.get("slug") == "The-Ontology-of-Coexistence"]
    if len(by_slug) != 1:
        fail("expected exactly one The-Ontology-of-Coexistence row")
    print("OK: catalog search matching agrees with WebMCP substring rules.")


def fetch_live(url: str, *, method: str = "GET", data: bytes | None = None) -> tuple[int, dict, str]:
    headers = {
        "User-Agent": LIVE_UA,
        "Accept": "application/json",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, dict(response.headers.items()), response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        header_map = dict(exc.headers.items()) if exc.headers else {}
        return exc.code, header_map, body
    except urllib.error.URLError as exc:
        fail(f"{url} request failed: {exc}")


def check_live() -> None:
    init = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "studies-api-test", "version": "1.0"},
            },
        }
    ).encode("utf-8")
    status, _headers, body = fetch_live(f"{SITE}/mcp", method="POST", data=init)
    if status != 200:
        status, _headers, body = fetch_live(f"{WORKER}/mcp", method="POST", data=init)
    if status != 200:
        fail(f"MCP initialize returned HTTP {status}: {body[:300]}")
    payload = json.loads(body)
    result = payload.get("result") or {}
    if not result.get("protocolVersion"):
        fail(f"MCP initialize missing protocolVersion: {body[:300]}")
    if not ((result.get("capabilities") or {}).get("tools") is not None):
        fail("MCP initialize must advertise tools")
    print("OK: live POST /mcp initialize returns MCP capabilities.")

    tools_req = json.dumps(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    ).encode("utf-8")
    status, _headers, body = fetch_live(f"{SITE}/mcp", method="POST", data=tools_req)
    if status != 200:
        status, _headers, body = fetch_live(f"{WORKER}/mcp", method="POST", data=tools_req)
    if status != 200:
        fail(f"MCP tools/list returned HTTP {status}: {body[:300]}")
    names = {tool.get("name") for tool in ((json.loads(body).get("result") or {}).get("tools") or [])}
    missing = {"search_studies", "list_studies", "get_study"} - names
    if missing:
        fail(f"MCP tools/list missing {missing}")
    print("OK: live MCP tools/list exposes catalog read tools.")

    status, _headers, body = fetch_live(f"{SITE}/api/studies?q=ontology")
    if status != 200:
        status, _headers, body = fetch_live(f"{WORKER}/api/studies?q=ontology")
    if status != 200:
        fail(f"GET /api/studies returned HTTP {status}: {body[:300]}")
    search = json.loads(body)
    if not search.get("count") or not search.get("studies"):
        fail(f"GET /api/studies?q=ontology returned no hits: {body[:300]}")
    print("OK: live GET /api/studies?q=ontology returns catalog hits.")


def main() -> None:
    rows = check_catalog_all()
    check_feed(rows)
    check_llms(rows)
    check_search(rows)
    glossary = STUDIES / "glossary.json"
    if not glossary.is_file():
        fail("missing Studies/glossary.json")
    terms = load_json(glossary)
    if not isinstance(terms, dict) or not terms.get("terms"):
        fail("glossary.json must contain a terms array")
    print("OK: Studies/glossary.json is present.")
    if "--live" in sys.argv:
        check_live()


if __name__ == "__main__":
    main()

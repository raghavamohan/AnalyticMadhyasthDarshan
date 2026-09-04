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
    for row in published:
        md_url = row.get("md")
        if not md_url:
            fail(f"published study {row['slug']} is missing md")
        if not md_url.endswith(".md"):
            fail(f"published study {row['slug']} md is {md_url!r}")
        if f"{row['slug']}/{row['slug']}.md" not in text:
            fail(f"llms.txt should link markdown for {row['slug']}")
        html_link = f"{row['slug']}/{row['slug']}.html)"
        if html_link in text.split("## Studies", 1)[-1].split("## Optional", 1)[0]:
            fail(f"llms.txt Studies section still links HTML for {row['slug']}")
    print("OK: llms.txt and llms-full.txt list published studies.")


def check_start_here(rows: list[dict]) -> None:
    path = STUDIES / "start-here.json"
    payload = load_json(path)
    if not isinstance(payload, dict):
        fail("start-here.json must be an object")
    stages = payload.get("stages")
    if not isinstance(stages, list) or len(stages) < 5:
        fail("start-here.json must list the five path stages")
    catalog_slugs = {row["slug"] for row in rows}
    slugs: set[str] = set()
    for stage in stages:
        core = (stage or {}).get("core") or {}
        if not core.get("slug") or not stage.get("reason"):
            fail("each start-here stage needs a core slug and reason")
        slugs.add(core["slug"])
        for related in stage.get("related") or []:
            slugs.add(related["slug"])
    parallel = payload.get("parallelTrack") or {}
    for item in parallel.get("studies") or []:
        slugs.add(item["slug"])
    missing = sorted(slugs - catalog_slugs)
    if missing:
        fail(f"start-here.json slugs missing from catalog-all.json: {missing}")
    template = (SCRIPTS / "_build_studies_index.py").read_text(encoding="utf-8")
    for slug in slugs:
        if slug not in template:
            fail(f"Start here landing-page template is missing slug {slug}")
    print("OK: Studies/start-here.json matches catalog slugs and the landing-page path.")


def check_live_start_here(payload: dict) -> None:
    """Verify the enriched API path without mistaking enrichment for drift."""
    expected = load_json(STUDIES / "start-here.json")
    if not isinstance(expected, dict):
        fail("Studies/start-here.json must be an object")
    for key in ("title", "intro"):
        if payload.get(key) != expected.get(key):
            fail(f"live GET /api/start-here has stale {key}")

    actual_stages = payload.get("stages") or []
    expected_stages = expected.get("stages") or []
    if len(actual_stages) != len(expected_stages):
        fail("live GET /api/start-here has a stale stage count")
    for actual, source in zip(actual_stages, expected_stages, strict=True):
        for key in ("number", "domain", "question", "reason", "blurb", "next"):
            if actual.get(key) != source.get(key):
                fail(
                    "live GET /api/start-here differs from Studies/start-here.json "
                    f"at stage {source.get('number')} field {key}"
                )
        if (actual.get("core") or {}).get("slug") != (source.get("core") or {}).get("slug"):
            fail(f"live GET /api/start-here has a stale core at stage {source.get('number')}")
        if (actual.get("core") or {}).get("role") != (source.get("core") or {}).get("role"):
            fail(f"live GET /api/start-here has a stale core role at stage {source.get('number')}")
        actual_related = [item.get("slug") for item in actual.get("related") or []]
        source_related = [item.get("slug") for item in source.get("related") or []]
        if actual_related != source_related:
            fail(f"live GET /api/start-here has stale related studies at stage {source.get('number')}")

    actual_parallel = payload.get("parallelTrack") or {}
    expected_parallel = expected.get("parallelTrack") or {}
    for key in ("label", "question", "reason"):
        if actual_parallel.get(key) != expected_parallel.get(key):
            fail(f"live GET /api/start-here has a stale parallelTrack {key}")
    actual_parallel_slugs = [item.get("slug") for item in actual_parallel.get("studies") or []]
    expected_parallel_slugs = [item.get("slug") for item in expected_parallel.get("studies") or []]
    if actual_parallel_slugs != expected_parallel_slugs:
        fail("live GET /api/start-here has stale parallel-track studies")

    refs = [
        *(stage.get("core") or {} for stage in actual_stages),
        *(item for stage in actual_stages for item in stage.get("related") or []),
        *(actual_parallel.get("studies") or []),
    ]
    for ref in refs:
        if not all(ref.get(key) for key in ("slug", "title", "collection", "status")):
            fail(f"live GET /api/start-here did not enrich study reference {ref.get('slug')!r}")


def check_search(rows: list[dict]) -> None:
    ontology = [row for row in rows if matches_query(row, "ontology")]
    if not ontology:
        fail("expected catalog-all.json to contain ontology matches")
    by_slug = [row for row in rows if row.get("slug") == "The-Ontology-of-Coexistence"]
    if len(by_slug) != 1:
        fail("expected exactly one The-Ontology-of-Coexistence row")
    print("OK: catalog search matching agrees with WebMCP substring rules.")


def check_openapi() -> None:
    spec = load_json(BASE / "openapi" / "studies.json")
    if not isinstance(spec, dict) or spec.get("openapi") != "3.1.0":
        fail("openapi/studies.json must declare OpenAPI 3.1.0")
    paths = spec.get("paths") or {}
    for path in (
        "/api/studies",
        "/api/studies/{slug}",
        "/api/glossary",
        "/api/start-here",
        "/api/cite/{slug}",
    ):
        if path not in paths:
            fail(f"openapi/studies.json is missing {path}")
    print("OK: openapi/studies.json documents catalog read endpoints.")


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
    missing = {
        "search_studies",
        "list_studies",
        "get_study",
        "get_study_outline",
        "get_glossary",
        "get_start_here",
        "get_cite",
    } - names
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

    slug = "The-Ontology-of-Coexistence"
    status, _headers, body = fetch_live(f"{SITE}/api/studies/{slug}")
    if status != 200:
        status, _headers, body = fetch_live(f"{WORKER}/api/studies/{slug}")
    if status != 200:
        fail(f"GET /api/studies/{slug} returned HTTP {status}: {body[:300]}")
    detail = json.loads(body)
    if detail.get("slug") != slug or not detail.get("outline"):
        fail(f"GET /api/studies/{slug} missing slug or outline: {body[:300]}")
    headings = [item.get("heading") for item in detail.get("outline") or []]
    if "Standpoint and scope" not in headings:
        fail(f"GET /api/studies/{slug} outline is missing Standpoint and scope")
    print(f"OK: live GET /api/studies/{slug} returns a heading outline.")

    status, _headers, body = fetch_live(f"{SITE}/api/glossary?q=jeevan")
    if status != 200:
        status, _headers, body = fetch_live(f"{WORKER}/api/glossary?q=jeevan")
    if status != 200:
        fail(f"GET /api/glossary returned HTTP {status}: {body[:300]}")
    glossary_hits = json.loads(body)
    ids = {term.get("id") for term in glossary_hits.get("terms") or []}
    if "jeevan" not in ids:
        fail(f"GET /api/glossary?q=jeevan missed jeevan: {body[:300]}")
    print("OK: live GET /api/glossary?q=jeevan returns glossary terms.")

    status, _headers, body = fetch_live(f"{SITE}/api/start-here")
    if status != 200:
        status, _headers, body = fetch_live(f"{WORKER}/api/start-here")
    if status != 200:
        fail(f"GET /api/start-here returned HTTP {status}: {body[:300]}")
    path = json.loads(body)
    check_live_start_here(path)
    cores = [stage.get("core", {}).get("slug") for stage in path.get("stages") or []]
    if "The-Ontology-of-Coexistence" not in cores:
        fail(f"GET /api/start-here missing ontology core: {body[:400]}")
    print("OK: live GET /api/start-here matches the canonical reading path.")

    status, _headers, body = fetch_live(f"{SITE}/api/cite/{slug}")
    if status != 200:
        status, _headers, body = fetch_live(f"{WORKER}/api/cite/{slug}")
    if status != 200:
        fail(f"GET /api/cite/{slug} returned HTTP {status}: {body[:300]}")
    cite = json.loads(body)
    if slug not in (cite.get("citation") or "") or not cite.get("mdUrl"):
        fail(f"GET /api/cite/{slug} citation is incomplete: {body[:300]}")
    print(f"OK: live GET /api/cite/{slug} returns a citation line.")


def main() -> None:
    rows = check_catalog_all()
    check_feed(rows)
    check_llms(rows)
    check_start_here(rows)
    check_search(rows)
    check_openapi()
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

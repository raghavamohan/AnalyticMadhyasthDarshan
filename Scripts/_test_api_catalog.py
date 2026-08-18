"""Validate the RFC 9727 API catalog document and its OpenAPI targets.

Run from the repository root:

    python Scripts/_test_api_catalog.py
    python Scripts/_test_api_catalog.py --live
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE, site_base_url
from _cloudflare_performance import HOMEPAGE_LINK
from _build_sitemap import DISCOVERY_PAGES, SITEMAP_PATH, collect_sitemap_entries

CATALOG_PATH = BASE / ".well-known" / "api-catalog"
WORKER_CATALOG_PATH = BASE / "infra" / "api-catalog-worker" / "src" / "api-catalog.json"
WORKER_INDEX_PATH = BASE / "infra" / "api-catalog-worker" / "src" / "index.js"
REQUIRED_RELS = ("service-desc", "service-doc")
OPTIONAL_RELS = ("status", "describedby")
AGENT_CARD_HREF = "https://analyticmadhyasthdarshan.org/.well-known/agent-card.json"
AGENT_SKILLS_HREF = (
    "https://analyticmadhyasthdarshan.org/.well-known/agent-skills/index.json"
)
MCP_SERVER_CARD_HREF = (
    "https://analyticmadhyasthdarshan.org/.well-known/mcp/server-card.json"
)
WEB_BOT_AUTH_HREF = (
    "https://analyticmadhyasthdarshan.org/.well-known/http-message-signatures-directory"
)
WEBMCP_HREF = "https://analyticmadhyasthdarshan.org/webmcp.js"
STUDIES_CATALOG_HREFS = (
    "https://analyticmadhyasthdarshan.org/Studies/catalog-topical.json",
    "https://analyticmadhyasthdarshan.org/Studies/catalog-formal.json",
    "https://analyticmadhyasthdarshan.org/Studies/catalog-applied.json",
    "https://analyticmadhyasthdarshan.org/Studies/catalog-all.json",
    "https://analyticmadhyasthdarshan.org/openapi/studies.json",
)
DYNAMIC_CATALOG_HREFS = {
    "https://analyticmadhyasthdarshan.org/mcp",
    "https://analyticmadhyasthdarshan.org/api/studies",
}
HOMEPAGE_LINK_RELS = ("api-catalog", "describedby", "service-desc", "service-doc")
HOMEPAGE_LINK_HREFS = (
    "/.well-known/api-catalog",
    "/.well-known/agent-card.json",
    "/.well-known/agent-skills/index.json",
    "/.well-known/mcp/server-card.json",
    "/.well-known/http-message-signatures-directory",
    "/webmcp.js",
    "/auth.md",
    "/.well-known/oauth-protected-resource",
    "/Studies/catalog-topical.json",
    "/Studies/catalog-formal.json",
    "/Studies/catalog-applied.json",
    "/Studies/catalog-all.json",
    "/Studies/feed.json",
    "/Studies/glossary.json",
    "/llms.txt",
    "/mcp",
    "/api/studies",
    "/openapi/submissions.json",
    "/openapi/discussions.json",
    "/openapi/studies.json",
    "/api-docs.html",
)
HOMEPAGE_LINK_URLS = (
    "https://analyticmadhyasthdarshan.org/",
    "https://analyticmadhyasthdarshan.org/Studies/index.html",
)
RFC9727_PROFILE = 'profile="https://www.rfc-editor.org/rfc/rfc9727"'
RESOURCE_METADATA_URL = (
    "https://analyticmadhyasthdarshan.org/.well-known/oauth-protected-resource"
)
LIVE_UA = "AnalyticMadhyasthDarshan-api-catalog-test/1.0"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json(path: Path) -> object:
    if not path.is_file():
        fail(f"missing {path.relative_to(BASE)}")
    return json.loads(path.read_text(encoding="utf-8"))


def site_path(url: str) -> Path | None:
    prefix = "https://analyticmadhyasthdarshan.org/"
    if not url.startswith(prefix):
        return None
    return BASE / url[len(prefix) :]


def check_link_array(entry: dict, rel: str, *, required: bool, check_local: bool = True) -> None:
    value = entry.get(rel)
    if value is None:
        if required:
            fail(f"catalog entry {entry.get('anchor')!r} is missing {rel}")
        return
    if not isinstance(value, list) or not value:
        fail(f"{rel} on {entry.get('anchor')!r} must be a non-empty array")
    for link in value:
        href = link.get("href")
        if not href or not isinstance(href, str):
            fail(f"{rel} link on {entry.get('anchor')!r} is missing href")
        if not check_local:
            continue
        if href in DYNAMIC_CATALOG_HREFS:
            continue
        local = site_path(href)
        if local is not None and not local.is_file():
            fail(f"{rel} href {href} is not a file in this repository")


def fetch_live(url: str, *, method: str = "GET", data: bytes | None = None) -> tuple[int, dict[str, str], str]:
    headers = {
        "User-Agent": LIVE_UA,
        "Accept": "application/json, application/linkset+json, */*",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            return response.status, dict(response.headers.items()), body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        header_map = dict(exc.headers.items()) if exc.headers else {}
        return exc.code, header_map, body
    except urllib.error.URLError as exc:
        fail(f"{url} request failed: {exc}")


def header_value(headers: dict[str, str], name: str) -> str:
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value or ""
    return ""


def check_worker_discovery_hooks() -> None:
    submissions = (BASE / "infra" / "worker" / "src" / "index.js").read_text(encoding="utf-8")
    discussions = (BASE / "infra" / "discussions-worker" / "src" / "index.js").read_text(
        encoding="utf-8"
    )
    for name, src in (("submissions", submissions), ("discussions", discussions)):
        if "WWW-Authenticate" not in src or "resource_metadata=" not in src:
            fail(f"{name} worker 401 responses must include WWW-Authenticate resource_metadata")
        if RESOURCE_METADATA_URL not in src:
            fail(f"{name} worker must point WWW-Authenticate at the apex PRM")
    if "RESERVED_SLUGS" not in discussions or "'health'" not in discussions:
        fail("discussions worker must reserve health and stats slugs")
    if "router.get('/api/health'" not in submissions:
        fail("submissions worker is missing GET /api/health")
    if "router.get('/api/discussions/health'" not in discussions:
        fail("discussions worker is missing GET /api/discussions/health")
    print("OK: workers advertise health routes and RFC 6750 WWW-Authenticate on 401.")


def check_rfc9727_profile() -> None:
    worker_src = WORKER_INDEX_PATH.read_text(encoding="utf-8")
    if RFC9727_PROFILE not in worker_src:
        fail("api-catalog worker Content-Type must use the /rfc/rfc9727 profile URL")
    if "info/rfc9727" in worker_src:
        fail("api-catalog worker still uses the /info/rfc9727 profile URL")
    print("OK: api-catalog worker RFC 9727 profile URL matches the Transform Rule.")


def check_sitemap_discovery() -> None:
    locs = {entry[0] for entry in collect_sitemap_entries()}
    sitemap_xml = SITEMAP_PATH.read_text(encoding="utf-8")
    base = site_base_url().rstrip("/")
    missing = []
    for path in DISCOVERY_PAGES:
        loc = f"{base}/{path.lstrip('/')}"
        if loc not in locs:
            missing.append(loc)
        elif loc not in sitemap_xml:
            missing.append(f"{loc} (not in sitemap.xml; run Scripts/_build_sitemap.py)")
    if missing:
        fail(f"sitemap is missing discovery URLs: {missing}")
    print(
        "OK: sitemap lists Auth.md, OpenAPI, api-catalog, Agent Card, "
        "Agent Skills, MCP Server Card, Web Bot Auth, WebMCP, and OAuth well-known URIs."
    )


def check_live_catalog() -> dict:
    url = "https://analyticmadhyasthdarshan.org/.well-known/api-catalog"
    status, headers, body = fetch_live(url)
    content_type = header_value(headers, "Content-Type")
    if status != 200:
        fail(f"live catalog returned HTTP {status}")
    if "application/linkset+json" not in content_type:
        fail(f"live catalog Content-Type is {content_type!r}")
    payload = json.loads(body)
    if len(payload.get("linkset") or []) < 3:
        fail("live catalog should list studies catalogs plus the two write APIs")
    print("OK: live /.well-known/api-catalog is RFC 9727 linkset JSON.")
    return payload


def check_live_status_links(catalog: dict) -> None:
    status_hrefs = [
        link.get("href")
        for entry in catalog.get("linkset") or []
        for link in entry.get("status") or []
    ]
    if not status_hrefs:
        fail("live catalog has no status links to verify")
    for href in status_hrefs:
        status, _headers, body = fetch_live(href)
        if status != 200:
            fail(f"catalog status {href} returned HTTP {status}: {body[:200]}")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            fail(f"catalog status {href} is not JSON: {body[:200]}")
        if payload.get("status") != "ok":
            fail(f"catalog status {href} is not a health payload: {payload}")
        if "comments" in payload:
            fail(f"catalog status {href} looks like a discussion thread, not health")
    print("OK: catalog status hrefs return {status: ok}.")


def check_live_www_authenticate() -> None:
    checks = (
        ("https://api.analyticmadhyasthdarshan.org/api/me/submissions", "GET", None),
        (
            "https://analyticmadhyasthdarshan.org/api/discussions/The-Ontology-of-Coexistence/comments",
            "POST",
            b"{}",
        ),
    )
    for url, method, data in checks:
        status, headers, body = fetch_live(url, method=method, data=data)
        if status != 401:
            fail(f"{method} {url} returned HTTP {status}, expected 401: {body[:200]}")
        www = header_value(headers, "WWW-Authenticate")
        if "Bearer" not in www or "resource_metadata=" not in www:
            fail(f"{url} 401 is missing RFC 6750 WWW-Authenticate: {www!r}")
        if RESOURCE_METADATA_URL not in www:
            fail(f"{url} WWW-Authenticate does not point at apex PRM: {www!r}")
    print("OK: unauthenticated write-API 401s advertise Protected Resource Metadata.")


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check_live_homepage_link_headers() -> None:
    opener = urllib.request.build_opener(_NoRedirectHandler())
    for url in HOMEPAGE_LINK_URLS:
        request = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "AnalyticMadhyasthDarshan-api-catalog-test/1.0"},
        )
        try:
            with opener.open(request, timeout=20) as response:
                status = response.status
                link = response.headers.get("Link") or ""
        except urllib.error.HTTPError as exc:
            status = exc.code
            link = (exc.headers.get("Link") if exc.headers else "") or ""
        except urllib.error.URLError as exc:
            fail(f"homepage Link check failed for {url}: {exc}")
        missing = [rel for rel in HOMEPAGE_LINK_RELS if f'rel="{rel}"' not in link]
        if missing:
            fail(f"{url} HTTP {status} is missing Link rels {missing}; Link={link!r}")
        missing_hrefs = [href for href in HOMEPAGE_LINK_HREFS if href not in link]
        if missing_hrefs:
            fail(f"{url} HTTP {status} is missing Link hrefs {missing_hrefs}; Link={link!r}")
    print("OK: homepage Link headers advertise api-catalog, describedby, service-desc, service-doc.")


def main() -> None:
    catalog = load_json(CATALOG_PATH)
    worker_catalog = load_json(WORKER_CATALOG_PATH)
    if catalog != worker_catalog:
        fail("infra/api-catalog-worker/src/api-catalog.json differs from .well-known/api-catalog")

    if not isinstance(catalog, dict) or not isinstance(catalog.get("linkset"), list):
        fail("catalog must be an object with a linkset array")
    linkset = catalog["linkset"]
    if not linkset:
        fail("linkset must list at least one API")

    for entry in linkset:
        if not isinstance(entry, dict) or not entry.get("anchor"):
            fail("each linkset entry needs an anchor URL")
        for rel in REQUIRED_RELS:
            check_link_array(entry, rel, required=True)
        for rel in OPTIONAL_RELS:
            check_link_array(entry, rel, required=False, check_local=False)

    desc_hrefs = {
        link.get("href")
        for entry in linkset
        for link in entry.get("service-desc") or []
    }
    missing = [href for href in STUDIES_CATALOG_HREFS if href not in desc_hrefs]
    if missing:
        fail(f"api-catalog is missing studies catalog JSON: {missing}")
    described = {
        link.get("href")
        for entry in linkset
        for link in entry.get("describedby") or []
    }
    if AGENT_CARD_HREF not in described:
        fail("api-catalog is missing the A2A Agent Card describedby link")
    if AGENT_SKILLS_HREF not in described:
        fail("api-catalog is missing the Agent Skills Discovery describedby link")
    if MCP_SERVER_CARD_HREF not in described:
        fail("api-catalog is missing the MCP Server Card describedby link")
    if WEB_BOT_AUTH_HREF not in described:
        fail("api-catalog is missing the Web Bot Auth directory describedby link")
    if WEBMCP_HREF not in described:
        fail("api-catalog is missing the WebMCP script describedby link")

    for spec in (BASE / "openapi" / "submissions.json", BASE / "openapi" / "discussions.json"):
        data = load_json(spec)
        if data.get("openapi") != "3.1.0":
            fail(f"{spec.name} must declare OpenAPI 3.1.0")
        if not data.get("paths"):
            fail(f"{spec.name} has no paths")

    print("OK: RFC 9727 api-catalog and OpenAPI files.")
    missing_rels = [rel for rel in HOMEPAGE_LINK_RELS if f'rel="{rel}"' not in HOMEPAGE_LINK]
    if missing_rels:
        fail(f"HOMEPAGE_LINK is missing rels {missing_rels}")
    missing_hrefs = [href for href in HOMEPAGE_LINK_HREFS if href not in HOMEPAGE_LINK]
    if missing_hrefs:
        fail(f"HOMEPAGE_LINK is missing hrefs {missing_hrefs}")
    print("OK: homepage Link header lists api-catalog, describedby, service-desc, service-doc.")
    check_rfc9727_profile()
    check_worker_discovery_hooks()
    check_sitemap_discovery()
    if "--live" in sys.argv:
        catalog = check_live_catalog()
        check_live_homepage_link_headers()
        check_live_status_links(catalog)
        check_live_www_authenticate()


if __name__ == "__main__":
    main()

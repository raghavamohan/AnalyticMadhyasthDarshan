"""Validate the RFC 9727 API catalog document and its OpenAPI targets.

Run from the repository root:

    python Scripts/_test_api_catalog.py
    python Scripts/_test_api_catalog.py --live
    python Scripts/_test_api_catalog.py --live-catalog-only
"""
from __future__ import annotations

import argparse
import json
import re
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
SYNTHETICS_PATH = BASE / "Scripts" / "_api_synthetics.py"
SYNTHETICS_WORKFLOW_PATH = BASE / ".github" / "workflows" / "api-synthetics.yml"
REQUIRED_RELS = ("service-desc", "service-doc")
OPTIONAL_RELS = ("status", "describedby")
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
    "https://analyticmadhyasthdarshan.org/api/glossary",
    "https://analyticmadhyasthdarshan.org/api/start-here",
}
HOMEPAGE_LINK_RELS = ("api-catalog", "describedby", "service-desc", "service-doc")
HOMEPAGE_LINK_HREFS = (
    "/.well-known/api-catalog",
    "/.well-known/agent-skills/index.json",
    "/.well-known/mcp/server-card.json",
    "/.well-known/http-message-signatures-directory",
    "/webmcp.js",
    "/auth.md",
    "/Studies/catalog-topical.json",
    "/Studies/catalog-formal.json",
    "/Studies/catalog-applied.json",
    "/Studies/catalog-all.json",
    "/Studies/feed.json",
    "/Studies/glossary.json",
    "/llms.txt",
    "/mcp",
    "/api/studies",
    "/api/glossary",
    "/api/start-here",
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
LIVE_UA = "AnalyticMadhyasthDarshan-api-catalog-test/1.0"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
ROUTE_RE = re.compile(
    r"router\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]+)['\"]"
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_json(path: Path) -> object:
    if not path.is_file():
        fail(f"missing {path.relative_to(BASE)}")
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_runtime_route(path: str) -> str:
    return re.sub(r":([A-Za-z][A-Za-z0-9_]*)", r"{\1}", path)


def check_openapi_runtime_parity(spec_path: Path, runtime_path: Path) -> None:
    spec = load_json(spec_path)
    if not isinstance(spec, dict) or spec.get("openapi") != "3.1.0":
        fail(f"{spec_path.name} must declare OpenAPI 3.1.0")
    paths = spec.get("paths")
    if not isinstance(paths, dict) or not paths:
        fail(f"{spec_path.name} has no paths")
    documented = {
        (method.lower(), path)
        for path, path_item in paths.items()
        if isinstance(path_item, dict)
        for method in path_item
        if method.lower() in HTTP_METHODS
    }
    runtime_text = runtime_path.read_text(encoding="utf-8")
    implemented = {
        (method.lower(), normalize_runtime_route(path))
        for method, path in ROUTE_RE.findall(runtime_text)
        if path.startswith("/api/")
    }
    missing = sorted(implemented - documented)
    extra = sorted(documented - implemented)
    if missing or extra:
        fail(
            f"{spec_path.name} route drift versus {runtime_path.relative_to(BASE)}; "
            f"missing={missing}, extra={extra}"
        )
    for method, path in sorted(documented):
        operation = paths[path][method]
        responses = operation.get("responses") or {}
        if method == "post":
            missing_errors = sorted({"403", "415"} - set(responses))
            if missing_errors:
                fail(
                    f"{spec_path.name} POST {path} omits common responses "
                    f"{missing_errors}"
                )
        security = operation.get("security") or []
        uses_session = any("sessionCookie" in requirement for requirement in security)
        if uses_session and "401" not in responses:
            fail(f"{spec_path.name} {method.upper()} {path} omits session 401")
    if spec_path.name == "submissions.json":
        for path in ("/api/propose", "/api/revise", "/api/submit"):
            responses = paths[path]["post"].get("responses") or {}
            missing_errors = sorted({"409", "413", "429"} - set(responses))
            if missing_errors:
                fail(
                    f"{spec_path.name} POST {path} omits operation responses "
                    f"{missing_errors}"
                )
    schemas = ((spec.get("components") or {}).get("schemas") or {})
    serialized = json.dumps(spec)
    refs = set(re.findall(r'#/components/schemas/([A-Za-z0-9_-]+)', serialized))
    unresolved = sorted(refs - set(schemas))
    if unresolved:
        fail(f"{spec_path.name} has unresolved schema references: {unresolved}")
    component_responses = ((spec.get("components") or {}).get("responses") or {})
    response_refs = set(
        re.findall(r'#/components/responses/([A-Za-z0-9_-]+)', serialized)
    )
    unresolved_responses = sorted(response_refs - set(component_responses))
    if unresolved_responses:
        fail(
            f"{spec_path.name} has unresolved response references: "
            f"{unresolved_responses}"
        )
    print(
        f"OK: {spec_path.name} documents all {len(implemented)} runtime operations."
    )


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
    if method not in {"GET", "HEAD", "OPTIONS"}:
        headers["Origin"] = "https://analyticmadhyasthdarshan.org"
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
        if "WWW-Authenticate" in src or "resource_metadata=" in src:
            fail(f"{name} worker must not advertise bearer auth for cookie-only APIs")
    if "RESERVED_SLUGS" not in discussions or "'health'" not in discussions:
        fail("discussions worker must reserve health and stats slugs")
    if "router.get('/api/health'" not in submissions:
        fail("submissions worker is missing GET /api/health")
    if "router.get('/api/discussions/health'" not in discussions:
        fail("discussions worker is missing GET /api/discussions/health")
    print("OK: workers advertise health routes and use cookie-only 401 responses.")


def check_synthetic_contract() -> None:
    script = SYNTHETICS_PATH.read_text(encoding="utf-8")
    workflow = SYNTHETICS_WORKFLOW_PATH.read_text(encoding="utf-8")
    required_checks = (
        "/api/studies/health",
        "/api/health",
        "/api/discussions/health",
        "/api/studies?q=ontology",
        "/api/cite/",
        'mcp("initialize")',
        'mcp("tools/list")',
        "auth.submissions.reject",
        "auth.discussions.reject",
        "discovery.equality",
    )
    missing = [value for value in required_checks if value not in script]
    if missing:
        fail(f"production API synthetics omit checks: {missing}")
    workflow_requirements = (
        "schedule:",
        "workflow_dispatch:",
        "issues: write",
        "continue-on-error: true",
        "actions/upload-artifact@v7",
        "actions/github-script@v9",
        "[API synthetic] Production verification failed",
    )
    missing = [value for value in workflow_requirements if value not in workflow]
    if missing:
        fail(f"production API synthetic workflow omits controls: {missing}")
    print("OK: production synthetics cover API status, reads, MCP, auth, discovery, and incidents.")


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
        "OK: sitemap lists Auth.md, OpenAPI, api-catalog, Agent Skills, "
        "MCP Server Card, Web Bot Auth, and WebMCP."
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
    expected = load_json(CATALOG_PATH)
    if payload != expected:
        fail("live api-catalog does not match .well-known/api-catalog")
    if len(payload.get("linkset") or []) < 3:
        fail("live catalog should list studies catalogs plus the two write APIs")
    hrefs = {
        link.get("href")
        for entry in payload.get("linkset") or []
        for rel in ("service-desc", "describedby")
        for link in entry.get(rel) or []
        if link.get("href")
    }
    missing = [href for href in STUDIES_CATALOG_HREFS if href not in hrefs]
    if missing:
        fail(f"live catalog is missing service-desc hrefs: {missing}")
    missing_dynamic = [href for href in sorted(DYNAMIC_CATALOG_HREFS) if href not in hrefs]
    if missing_dynamic:
        fail(f"live catalog is missing describedby hrefs: {missing_dynamic}")
    print("OK: live /.well-known/api-catalog is RFC 9727 linkset JSON.")
    return payload


def check_live_openapi() -> None:
    for name in ("submissions.json", "discussions.json", "studies.json"):
        url = f"https://analyticmadhyasthdarshan.org/openapi/{name}"
        status, headers, body = fetch_live(url)
        if status != 200:
            fail(f"live openapi/{name} returned HTTP {status}")
        if "json" not in header_value(headers, "Content-Type").lower():
            fail(f"live openapi/{name} has a non-JSON Content-Type")
        if json.loads(body) != load_json(BASE / "openapi" / name):
            fail(f"live openapi/{name} does not match the repository contract")
    print("OK: live OpenAPI documents match the repository contracts.")


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


def check_live_cookie_auth() -> None:
    checks = (
        ("https://api.analyticmadhyasthdarshan.org/api/me/submissions", "GET", None),
        ("https://api.analyticmadhyasthdarshan.org/api/propose", "POST", b"{}"),
        ("https://api.analyticmadhyasthdarshan.org/api/revise", "POST", b"{}"),
        ("https://api.analyticmadhyasthdarshan.org/api/submit", "POST", b"{}"),
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
        if "json" not in header_value(headers, "Content-Type").lower():
            fail(f"{url} 401 is not JSON")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            fail(f"{url} 401 has invalid JSON: {body[:200]}")
        required = {"success", "code", "message", "requestId"}
        missing = sorted(required - set(payload))
        if missing:
            fail(f"{url} 401 error envelope is missing {missing}: {payload}")
        if payload.get("success") is not False or payload.get("code") != "authentication_required":
            fail(f"{url} 401 has the wrong error envelope: {payload}")
        if header_value(headers, "X-Request-ID") != payload.get("requestId"):
            fail(f"{url} 401 body/header request IDs differ")
        if header_value(headers, "Cache-Control").lower() != "private, no-store":
            fail(f"{url} 401 is not private/no-store")
        if header_value(headers, "Pragma").lower() != "no-cache":
            fail(f"{url} 401 is missing Pragma: no-cache")
        vary = {part.strip().lower() for part in header_value(headers, "Vary").split(",")}
        if not {"origin", "cookie"}.issubset(vary):
            fail(f"{url} 401 Vary must include Origin and Cookie")
        www = header_value(headers, "WWW-Authenticate")
        if www:
            fail(f"{url} 401 incorrectly advertises bearer authentication: {www!r}")
    print("OK: unauthenticated APIs return the private cookie-only 401 contract.")


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


def run_live_checks(*, catalog_only: bool) -> None:
    """Check the deployed catalog Worker, optionally followed by cross-owned surfaces."""
    catalog = check_live_catalog()
    if catalog_only:
        return
    check_live_openapi()
    check_live_homepage_link_headers()
    check_live_status_links(catalog)
    check_live_cookie_auth()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    live = parser.add_mutually_exclusive_group()
    live.add_argument(
        "--live",
        action="store_true",
        help="verify the catalog Worker and every linked live API/discovery surface",
    )
    live.add_argument(
        "--live-catalog-only",
        action="store_true",
        help="verify only the API catalog route owned by the catalog Worker",
    )
    args = parser.parse_args(argv)

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
    if AGENT_SKILLS_HREF not in described:
        fail("api-catalog is missing the Agent Skills Discovery describedby link")
    if MCP_SERVER_CARD_HREF not in described:
        fail("api-catalog is missing the MCP Server Card describedby link")
    if WEB_BOT_AUTH_HREF not in described:
        fail("api-catalog is missing the Web Bot Auth directory describedby link")
    if WEBMCP_HREF not in described:
        fail("api-catalog is missing the WebMCP script describedby link")
    missing_dynamic = [href for href in sorted(DYNAMIC_CATALOG_HREFS) if href not in described]
    if missing_dynamic:
        fail(f"api-catalog is missing describedby hrefs: {missing_dynamic}")

    check_openapi_runtime_parity(
        BASE / "openapi" / "submissions.json",
        BASE / "infra" / "worker" / "src" / "index.js",
    )
    check_openapi_runtime_parity(
        BASE / "openapi" / "discussions.json",
        BASE / "infra" / "discussions-worker" / "src" / "index.js",
    )

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
    check_synthetic_contract()
    check_sitemap_discovery()
    if args.live or args.live_catalog_only:
        run_live_checks(catalog_only=args.live_catalog_only)


if __name__ == "__main__":
    main()

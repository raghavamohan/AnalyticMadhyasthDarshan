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

from _common import BASE
from _cloudflare_performance import HOMEPAGE_LINK

CATALOG_PATH = BASE / ".well-known" / "api-catalog"
WORKER_CATALOG_PATH = BASE / "infra" / "api-catalog-worker" / "src" / "api-catalog.json"
REQUIRED_RELS = ("service-desc", "service-doc")
OPTIONAL_RELS = ("status",)
STUDIES_CATALOG_HREFS = (
    "https://analyticmadhyasthdarshan.org/Studies/catalog-topical.json",
    "https://analyticmadhyasthdarshan.org/Studies/catalog-formal.json",
    "https://analyticmadhyasthdarshan.org/Studies/catalog-applied.json",
)
HOMEPAGE_LINK_RELS = ("api-catalog", "describedby", "service-desc", "service-doc")
HOMEPAGE_LINK_URLS = (
    "https://analyticmadhyasthdarshan.org/",
    "https://analyticmadhyasthdarshan.org/Studies/index.html",
)


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
        local = site_path(href)
        if local is not None and not local.is_file():
            fail(f"{rel} href {href} is not a file in this repository")


def check_live_catalog() -> None:
    url = "https://analyticmadhyasthdarshan.org/.well-known/api-catalog"
    request = urllib.request.Request(url, headers={"Accept": "application/linkset+json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            content_type = response.headers.get("Content-Type") or ""
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        fail(f"live catalog returned HTTP {exc.code}")
    except urllib.error.URLError as exc:
        fail(f"live catalog request failed: {exc}")
    if status != 200:
        fail(f"live catalog returned HTTP {status}")
    if "application/linkset+json" not in content_type:
        fail(f"live catalog Content-Type is {content_type!r}")
    if len(payload.get("linkset") or []) < 3:
        fail("live catalog should list studies catalogs plus the two write APIs")
    print("OK: live /.well-known/api-catalog is RFC 9727 linkset JSON.")


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
    print("OK: homepage Link header lists api-catalog, describedby, service-desc, service-doc.")
    if "--live" in sys.argv:
        check_live_catalog()
        check_live_homepage_link_headers()


if __name__ == "__main__":
    main()

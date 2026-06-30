#!/usr/bin/env python3
"""Cloudflare performance setup for analyticmadhyasthdarshan.org (GitHub Pages + proxy).

Applies zone settings, cache rules, and the root-to-catalog redirect via API when
CLOUDFLARE_API_TOKEN is set (repo-root `.env`, `.env.local`, or the process environment).
Baseline RUM metrics: infra/cloudflare-rum-baseline.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Mapping

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent
BASELINE_PATH = BASE / "infra" / "cloudflare-rum-baseline.json"
SITE_HOST = "analyticmadhyasthdarshan.org"
ROOT_URL = f"https://{SITE_HOST}/"
CATALOG_PATH = "/Studies/index.html"
CATALOG_URL = f"https://{SITE_HOST}{CATALOG_PATH}"
API_BASE = "https://api.cloudflare.com/client/v4"
REDIRECT_PHASE = "http_request_dynamic_redirect"
CACHE_PHASE = "http_request_cache_settings"
ROOT_REDIRECT_REF = "analyticmadhyasth_root_to_catalog"
CACHE_RULE_REFS = (
    "amd_cache_pdfs",
    "amd_cache_images",
    "amd_cache_catalog_json",
    "amd_cache_studies_index",
    "amd_cache_html",
)
REDIRECT_STATUSES = frozenset({301, 302, 307, 308})
VERIFY_USER_AGENT = "AnalyticMadhyasthDarshan-cloudflare-verify/1.0"
SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600
SECONDS_PER_MONTH = 30 * SECONDS_PER_DAY


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _unquote_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE pairs into os.environ without overriding existing variables."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _unquote_env_value(value)


def load_repo_env() -> None:
    """Load `.env` then `.env.local` from the repository root."""
    load_env_file(BASE / ".env")
    load_env_file(BASE / ".env.local")


def cloudflare_api_token() -> str | None:
    return os.environ.get("CLOUDFLARE_API_TOKEN")


def cloudflare_zone_id() -> str | None:
    return os.environ.get("CLOUDFLARE_ZONE_ID")


def _api_request(
    method: str,
    path: str,
    token: str,
    payload: dict | None = None,
    *,
    allow_404: bool = False,
) -> dict | None:
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        if allow_404 and exc.code == 404:
            return None
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            raise RuntimeError(f"HTTP {exc.code}: {raw}") from exc
        if not body.get("success"):
            raise RuntimeError(json.dumps(body.get("errors", body), indent=2))
        return body
    if not body.get("success"):
        raise RuntimeError(json.dumps(body.get("errors", body), indent=2))
    return body


def resolve_zone_id(token: str, zone_id: str | None) -> str:
    if zone_id:
        return zone_id
    body = _api_request(
        "GET",
        f"/zones?name={SITE_HOST}",
        token,
    )
    zones = body.get("result", [])
    if not zones:
        raise RuntimeError(f"No Cloudflare zone found for {SITE_HOST}")
    return zones[0]["id"]


def apply_zone_setting(token: str, zone_id: str, setting_id: str, value) -> None:
    _api_request(
        "PATCH",
        f"/zones/{zone_id}/settings/{setting_id}",
        token,
        {"value": value},
    )
    print(f"Set zone setting {setting_id} = {value!r}")


DISCUSSIONS_WORKER = "amd-discussions"
DISCUSSIONS_ROUTE_PATTERNS = (
    f"{SITE_HOST}/api/discussions/*",
    f"{SITE_HOST}/api/discuss-auth/*",
)


def list_worker_routes(token: str, zone_id: str) -> list[dict]:
    body = _api_request("GET", f"/zones/{zone_id}/workers/routes", token)
    return body.get("result", []) if body else []


def ensure_worker_route(token: str, zone_id: str, pattern: str, script: str) -> None:
    routes = list_worker_routes(token, zone_id)
    for route in routes:
        if route.get("pattern") == pattern:
            if route.get("script") == script:
                print(f"Worker route already set: {pattern} -> {script}")
                return
            route_id = route.get("id")
            if route_id:
                _api_request(
                    "PUT",
                    f"/zones/{zone_id}/workers/routes/{route_id}",
                    token,
                    {"pattern": pattern, "script": script},
                )
                print(f"Updated worker route: {pattern} -> {script}")
                return
    _api_request(
        "POST",
        f"/zones/{zone_id}/workers/routes",
        token,
        {"pattern": pattern, "script": script},
    )
    print(f"Created worker route: {pattern} -> {script}")


def apply_discussions_api_routes(token: str, zone_id: str | None) -> None:
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    for pattern in DISCUSSIONS_ROUTE_PATTERNS:
        ensure_worker_route(token, zone, pattern, DISCUSSIONS_WORKER)
    print("Discussions worker routes applied.")


def apply_api_settings(token: str, zone_id: str | None) -> None:
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    apply_zone_setting(token, zone, "http3", "on")
    apply_zone_setting(token, zone, "brotli", "on")
    print(
        "Skipped minify: Cloudflare deprecated Auto Minify in August 2024; "
        "the API no longer enables it."
    )
    print("Zone optimization settings applied.")


def root_redirect_rule_body() -> dict:
    return {
        "ref": ROOT_REDIRECT_REF,
        "expression": f'(http.host eq "{SITE_HOST}" and http.request.uri.path eq "/")',
        "description": "Redirect site root to studies catalog (AnalyticMadhyasthDarshan).",
        "action": "redirect",
        "enabled": True,
        "action_parameters": {
            "from_value": {
                "target_url": {"value": CATALOG_URL},
                "status_code": 301,
                "preserve_query_string": True,
            }
        },
    }


def _sanitize_rule_for_put(rule: dict) -> dict:
    keep = ("ref", "expression", "description", "action", "action_parameters", "enabled")
    cleaned = {key: rule[key] for key in keep if key in rule}
    if "ref" not in cleaned:
        ref = rule.get("ref") or rule.get("id")
        if ref:
            cleaned["ref"] = ref
    return cleaned


def _redirect_target_url(rule: dict) -> str:
    from_value = rule.get("action_parameters", {}).get("from_value", {})
    target = from_value.get("target_url", {})
    if isinstance(target, dict):
        return str(target.get("value") or target.get("expression") or "")
    return ""


def _root_redirect_rule_is_correct(rule: dict) -> bool:
    if rule.get("action") != "redirect":
        return False
    if not _location_targets_catalog(_redirect_target_url(rule)):
        return False
    from_value = rule.get("action_parameters", {}).get("from_value", {})
    if from_value.get("status_code") != 301:
        return False
    expression = rule.get("expression", "")
    return "http.request.uri.path eq \"/\"" in expression.replace(" ", "")


def _find_root_redirect_rule(rules: list[dict]) -> dict | None:
    for rule in rules:
        if rule.get("ref") == ROOT_REDIRECT_REF:
            return rule
    return None


def get_phase_entrypoint_ruleset(token: str, zone_id: str, phase: str) -> dict | None:
    body = _api_request(
        "GET",
        f"/zones/{zone_id}/rulesets/phases/{phase}/entrypoint",
        token,
        allow_404=True,
    )
    if body is None:
        return None
    return body.get("result")


def get_redirect_entrypoint_ruleset(token: str, zone_id: str) -> dict | None:
    return get_phase_entrypoint_ruleset(token, zone_id, REDIRECT_PHASE)


def get_cache_entrypoint_ruleset(token: str, zone_id: str) -> dict | None:
    return get_phase_entrypoint_ruleset(token, zone_id, CACHE_PHASE)


def _cache_rule_body(
    ref: str,
    description: str,
    expression: str,
    *,
    edge_ttl_seconds: int,
    browser_ttl_seconds: int,
) -> dict:
    return {
        "ref": ref,
        "expression": expression,
        "description": description,
        "action": "set_cache_settings",
        "enabled": True,
        "action_parameters": {
            "cache": True,
            "edge_ttl": {
                "mode": "override_origin",
                "default": edge_ttl_seconds,
            },
            "browser_ttl": {
                "mode": "override_origin",
                "default": browser_ttl_seconds,
            },
        },
    }


def cache_rules_spec() -> list[dict]:
    """Cache rules for GitHub Pages static assets (most specific first)."""
    host = f'http.host eq "{SITE_HOST}"'
    return [
        _cache_rule_body(
            CACHE_RULE_REFS[0],
            "Cache PDFs at edge for one month",
            f"({host} and ends_with(http.request.uri.path, \".pdf\"))",
            edge_ttl_seconds=SECONDS_PER_MONTH,
            browser_ttl_seconds=SECONDS_PER_DAY,
        ),
        _cache_rule_body(
            CACHE_RULE_REFS[1],
            "Cache images at edge for one month",
            (
                f"({host} and ("
                'ends_with(http.request.uri.path, ".png") or '
                'ends_with(http.request.uri.path, ".jpg") or '
                'ends_with(http.request.uri.path, ".jpeg") or '
                'ends_with(http.request.uri.path, ".webp") or '
                'ends_with(http.request.uri.path, ".svg")))'
            ),
            edge_ttl_seconds=SECONDS_PER_MONTH,
            browser_ttl_seconds=7 * SECONDS_PER_DAY,
        ),
        _cache_rule_body(
            CACHE_RULE_REFS[2],
            "Cache studies catalog JSON",
            (
                f"({host} and ("
                'http.request.uri.path eq "/Studies/catalog-topical.json" or '
                'http.request.uri.path eq "/Studies/catalog-formal.json" or '
                'http.request.uri.path eq "/Studies/catalog-applied.json"))'
            ),
            edge_ttl_seconds=SECONDS_PER_HOUR,
            browser_ttl_seconds=5 * 60,
        ),
        _cache_rule_body(
            CACHE_RULE_REFS[3],
            "Short cache for studies catalog shell",
            f'({host} and http.request.uri.path eq "/Studies/index.html")',
            edge_ttl_seconds=5 * 60,
            browser_ttl_seconds=2 * 60,
        ),
        _cache_rule_body(
            CACHE_RULE_REFS[4],
            "Cache study HTML pages",
            (
                f"({host} and ("
                'ends_with(http.request.uri.path, ".html") or '
                'http.request.uri.path eq "/Studies/"))'
            ),
            edge_ttl_seconds=2 * SECONDS_PER_HOUR,
            browser_ttl_seconds=10 * 60,
        ),
    ]


def _cache_rule_is_correct(rule: dict, expected: dict) -> bool:
    if rule.get("action") != "set_cache_settings":
        return False
    if rule.get("expression") != expected.get("expression"):
        return False
    actual_params = rule.get("action_parameters", {})
    expected_params = expected.get("action_parameters", {})
    return (
        actual_params.get("cache") is True
        and actual_params.get("edge_ttl") == expected_params.get("edge_ttl")
        and actual_params.get("browser_ttl") == expected_params.get("browser_ttl")
    )


def purge_cache_files(token: str, zone_id: str | None, urls: list[str]) -> None:
    """Purge specific URLs from Cloudflare edge cache."""
    zone = resolve_zone_id(token, zone_id)
    if not urls:
        raise ValueError("At least one URL is required to purge.")
    body = _api_request(
        "POST",
        f"/zones/{zone}/purge_cache",
        token,
        {"files": urls},
    )
    if body is None:
        raise RuntimeError("Cloudflare purge_cache returned no response.")
    print(f"Purged {len(urls)} URL(s) from Cloudflare cache for zone {zone}.")


def apply_cache_rules(token: str, zone_id: str | None) -> None:
    """Create or update zone cache rules for static HTML, JSON, images, and PDFs."""
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    expected_rules = cache_rules_spec()
    ruleset = get_cache_entrypoint_ruleset(token, zone)

    if ruleset is None:
        _api_request(
            "POST",
            f"/zones/{zone}/rulesets",
            token,
            {
                "name": "AnalyticMadhyasthDarshan cache rules",
                "kind": "zone",
                "phase": CACHE_PHASE,
                "rules": expected_rules,
            },
        )
        print(f"Created {CACHE_PHASE} ruleset with {len(expected_rules)} cache rules.")
        return

    ruleset_id = ruleset["id"]
    existing_by_ref = {rule.get("ref"): rule for rule in ruleset.get("rules", []) if rule.get("ref")}

    if all(
        ref in existing_by_ref and _cache_rule_is_correct(existing_by_ref[ref], expected)
        for ref, expected in zip(CACHE_RULE_REFS, expected_rules, strict=True)
    ):
        print("Cache rules already configured.")
        return

    updated_rules: list[dict] = []
    for expected in expected_rules:
        ref = expected["ref"]
        existing = existing_by_ref.get(ref)
        if existing and _cache_rule_is_correct(existing, expected):
            updated_rules.append(_sanitize_rule_for_put(existing))
        else:
            updated_rules.append(expected)

    _api_request(
        "PUT",
        f"/zones/{zone}/rulesets/{ruleset_id}",
        token,
        {
            "name": ruleset.get("name", "AnalyticMadhyasthDarshan cache rules"),
            "kind": "zone",
            "phase": CACHE_PHASE,
            "rules": updated_rules,
        },
    )
    print(f"Updated cache ruleset with {len(updated_rules)} rules.")


def check_cache_rules(token: str, zone_id: str | None) -> tuple[bool, list[str]]:
    """Return whether expected cache rules are present and correct."""
    zone = resolve_zone_id(token, zone_id)
    ruleset = get_cache_entrypoint_ruleset(token, zone)
    issues: list[str] = []
    if ruleset is None:
        issues.append("No http_request_cache_settings ruleset found.")
        return False, issues

    existing_by_ref = {rule.get("ref"): rule for rule in ruleset.get("rules", []) if rule.get("ref")}
    ok = True
    for expected in cache_rules_spec():
        ref = expected["ref"]
        rule = existing_by_ref.get(ref)
        if rule is None:
            ok = False
            issues.append(f"Missing cache rule ref {ref!r}.")
            continue
        if not rule.get("enabled", True):
            ok = False
            issues.append(f"Cache rule {ref!r} is disabled.")
            continue
        if not _cache_rule_is_correct(rule, expected):
            ok = False
            issues.append(f"Cache rule {ref!r} does not match expected TTLs/expression.")
    return ok, issues


def print_check_cache_rules(token: str, zone_id: str | None) -> bool:
    print("Cache rules check:")
    try:
        ok, issues = check_cache_rules(token, zone_id)
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"  ERROR: {exc}")
        return False
    if ok:
        print(f"  OK: {len(CACHE_RULE_REFS)} cache rules configured for {SITE_HOST}.")
        return True
    for issue in issues:
        print(f"  {issue}")
    return False


def apply_root_redirect(token: str, zone_id: str | None) -> None:
    """Create or update the zone redirect rule: / -> /Studies/index.html (301)."""
    zone = resolve_zone_id(token, zone_id)
    ruleset = get_redirect_entrypoint_ruleset(token, zone)
    rule_body = root_redirect_rule_body()

    if ruleset is None:
        _api_request(
            "POST",
            f"/zones/{zone}/rulesets",
            token,
            {
                "name": "AnalyticMadhyasthDarshan redirect rules",
                "kind": "zone",
                "phase": REDIRECT_PHASE,
                "rules": [rule_body],
            },
        )
        print(f"Created {REDIRECT_PHASE} ruleset with root -> catalog redirect.")
        return

    ruleset_id = ruleset["id"]
    rules = ruleset.get("rules", [])
    existing = _find_root_redirect_rule(rules)
    if existing and _root_redirect_rule_is_correct(existing):
        print("Root redirect rule already configured.")
        return

    if existing:
        updated_rules: list[dict] = []
        for rule in rules:
            if rule.get("ref") == ROOT_REDIRECT_REF:
                updated_rules.append(rule_body)
            else:
                updated_rules.append(_sanitize_rule_for_put(rule))
        _api_request(
            "PUT",
            f"/zones/{zone}/rulesets/{ruleset_id}",
            token,
            {
                "name": ruleset.get("name", "Redirect rules"),
                "kind": "zone",
                "phase": REDIRECT_PHASE,
                "rules": updated_rules,
            },
        )
        print("Updated root redirect rule in existing redirect ruleset.")
        return

    _api_request(
        "POST",
        f"/zones/{zone}/rulesets/{ruleset_id}/rules",
        token,
        rule_body,
    )
    print("Added root redirect rule to existing redirect ruleset.")


def _header_lookup(headers: Mapping[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


def _fetch_root_without_redirect(url: str) -> tuple[int, Mapping[str, str]]:
    opener = urllib.request.build_opener(_NoRedirectHandler())
    headers = {"User-Agent": VERIFY_USER_AGENT}
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with opener.open(req, timeout=30) as resp:
                return resp.status, resp.headers
        except urllib.error.HTTPError as exc:
            if exc.code == 405 and method == "HEAD":
                continue
            return exc.code, exc.headers
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Request failed: {exc.reason}") from exc
    raise RuntimeError("Could not fetch root URL (HEAD and GET both failed).")


def _location_targets_catalog(location: str) -> bool:
    if not location:
        return False
    lower = location.lower()
    return "studies/index.html" in lower


def verify_root_redirect() -> tuple[bool, str]:
    """Check that the site root redirects to the studies catalog (Cloudflare 301)."""
    try:
        status, headers = _fetch_root_without_redirect(ROOT_URL)
    except RuntimeError as exc:
        return False, str(exc)

    location = _header_lookup(headers, "Location")

    if status in REDIRECT_STATUSES:
        if _location_targets_catalog(location):
            return True, f"OK: {status} redirect from {ROOT_URL} to {location}"
        return (
            False,
            f"Got {status} but Location is {location!r}; expected a URL containing "
            f"{CATALOG_PATH}",
        )

    if status == 200:
        return (
            False,
            f"Got {status} on {ROOT_URL} (no server redirect). "
            "Add the Cloudflare redirect rule, or the site is using the repo "
            "meta-refresh/JS redirect only.",
        )

    return (
        False,
        f"Got {status} on {ROOT_URL}; expected {sorted(REDIRECT_STATUSES)} to "
        f"{CATALOG_PATH}",
    )


def print_verify_root_redirect() -> bool:
    print("Root redirect check:")
    ok, detail = verify_root_redirect()
    print(f"  {detail}")
    if not ok:
        print(
            "  Manual check (PowerShell; do not use curl -I, which aliases to "
            "Invoke-WebRequest):"
        )
        print(
            "    try { Invoke-WebRequest -Uri '"
            + ROOT_URL
            + "' -Method Head -MaximumRedirection 0 } catch { "
            + "$_.Exception.Response.StatusCode.value__; "
            + "$_.Exception.Response.Headers['Location'] }"
        )
    return ok


def print_dashboard_steps() -> None:
    print(
        f"""
Cloudflare dashboard steps for {SITE_HOST} (GitHub Pages origin, orange-cloud proxy):

1. DNS - confirm A/CNAME for {SITE_HOST} is Proxied (orange cloud).

2. Rules -> Redirect Rules (or run: python Scripts/_cloudflare_performance.py --apply-redirect)
   Root 301 to https://{SITE_HOST}/Studies/index.html (API uses ref {ROOT_REDIRECT_REF})

3. Caching -> Cache Rules (or run: python Scripts/_cloudflare_performance.py --apply-cache-rules)
   Order matters; more specific rules first — PDFs, images, catalog JSON, HTML.
   The script applies the same TTLs documented here via API when a token is set.

4. Speed -> Optimization - Brotli and HTTP/3 (run: python Scripts/_cloudflare_performance.py --apply-api).
   Auto Minify was deprecated by Cloudflare in 2024 and is not applied via API.

5. After deploy, verify the root redirect (this script runs the check by default):
   python Scripts/_cloudflare_performance.py --verify-only

6. Re-check RUM after 7 days against infra/cloudflare-rum-baseline.json
   Targets: LCP P99 < 2500 ms, LCP poor % near 0.
"""
    )


def print_baseline_summary() -> None:
    if not BASELINE_PATH.is_file():
        print(f"Baseline file not found: {BASELINE_PATH}")
        return
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    lcp = data.get("core_web_vitals", {}).get("lcp", {})
    print("RUM baseline (pre-optimization):")
    print(
        f"  LCP good {lcp.get('good_pct')}% | poor {lcp.get('poor_pct')}% | "
        f"P50 {lcp.get('p50_ms')}ms P99 {lcp.get('p99_ms')}ms"
    )


def main() -> int:
    load_repo_env()

    parser = argparse.ArgumentParser(description="Cloudflare performance setup helper.")
    parser.add_argument(
        "--apply-api",
        action="store_true",
        help="Apply HTTP/3 and Brotli and ensure root redirect via Cloudflare API.",
    )
    parser.add_argument(
        "--apply-cache-rules",
        action="store_true",
        help="Create or update Cache Rules for HTML, JSON, images, and PDFs.",
    )
    parser.add_argument(
        "--check-cache-rules",
        action="store_true",
        help="Verify Cache Rules match the repository spec.",
    )
    parser.add_argument(
        "--apply-discussions-api",
        action="store_true",
        help="Create or update Worker routes for amd-discussions on the custom domain.",
    )
    parser.add_argument(
        "--apply-redirect",
        action="store_true",
        help="Create or update the root -> catalog 301 redirect rule only.",
    )
    parser.add_argument(
        "--zone-id",
        default=None,
        help="Zone ID (default: CLOUDFLARE_ZONE_ID from .env or lookup by hostname).",
    )
    parser.add_argument(
        "--purge-cache",
        action="store_true",
        help="Purge Cloudflare edge cache for the studies index and catalog JSON files.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only run the root redirect check (no dashboard steps).",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip the root redirect check at the end.",
    )
    args = parser.parse_args()
    zone_id = args.zone_id or cloudflare_zone_id()
    token = cloudflare_api_token()

    if args.purge_cache:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --purge-cache "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            purge_cache_files(
                token,
                zone_id,
                [
                    CATALOG_URL,
                    f"https://{SITE_HOST}/Studies/catalog-topical.json",
                    f"https://{SITE_HOST}/Studies/catalog-formal.json",
                    f"https://{SITE_HOST}/Studies/catalog-applied.json",
                ],
            )
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if args.verify_only:
        return 0 if print_verify_root_redirect() else 1

    if args.check_cache_rules:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --check-cache-rules "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        ok = print_check_cache_rules(token, zone_id)
        return 0 if ok else 1

    print_baseline_summary()

    api_error = False

    if args.apply_discussions_api:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-discussions-api "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_discussions_api_routes(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if args.apply_redirect:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-redirect "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_root_redirect(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if args.apply_cache_rules:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-cache-rules "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_cache_rules(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if args.apply_api:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-api "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_api_settings(token, zone_id)
            apply_root_redirect(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if api_error:
        return 1

    if not args.apply_api and not args.apply_redirect and not args.apply_discussions_api and not args.apply_cache_rules:
        print_dashboard_steps()

    if not args.skip_verify:
        print()
        verify_ok = print_verify_root_redirect()
        if token and (args.apply_cache_rules or args.apply_api):
            verify_ok = print_check_cache_rules(token, zone_id) and verify_ok
        if not verify_ok:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Cloudflare performance setup for analyticmadhyasthdarshan.org (GitHub Pages + proxy).

Applies zone settings, cache rules, the root-to-catalog redirect, and portal edge
security (Super Bot Fight Mode + WAF skip for GitHub Actions notify) via API when
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
API_HOST = f"api.{SITE_HOST}"
PORTAL_NOTIFY_URL = f"https://{API_HOST}/api/notify"
ROOT_URL = f"https://{SITE_HOST}/"
CATALOG_PATH = "/Studies/index.html"
CATALOG_URL = f"https://{SITE_HOST}{CATALOG_PATH}"
API_BASE = "https://api.cloudflare.com/client/v4"
REDIRECT_PHASE = "http_request_dynamic_redirect"
CACHE_PHASE = "http_request_cache_settings"
WAF_CUSTOM_PHASE = "http_request_firewall_custom"
RATE_LIMIT_PHASE = "http_ratelimit"
RESPONSE_HEADERS_PHASE = "http_response_headers_transform"
NOTIFY_SKIP_REF = "amd_skip_sbfm_portal_notify"
PROBE_BLOCK_REF = "amd_block_common_probes"
SECURITY_HEADERS_REF = "amd_security_headers_static"
EDGE_API_RATE_LIMIT_REF = "amd_rl_edge_api"
WAF_CUSTOM_MANAGED_REFS = (PROBE_BLOCK_REF, NOTIFY_SKIP_REF)
EDGE_API_RATE_LIMIT_REFS = (EDGE_API_RATE_LIMIT_REF,)
HSTS_MAX_AGE_SEC = 31536000
CSP_REPORT_ONLY = (
    "default-src 'self'; "
    "script-src 'self' https://challenges.cloudflare.com 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self' https://api.analyticmadhyasthdarshan.org https://challenges.cloudflare.com; "
    "frame-src https://challenges.cloudflare.com; "
    "base-uri 'self'; "
    "form-action 'self'"
)
NOTIFY_SKIP_EXPRESSION = (
    f'(http.host eq "{API_HOST}" and starts_with(http.request.uri.path, "/api/notify"))'
)
PROBE_BLOCK_EXPRESSION = (
    f'(http.host in {{"{SITE_HOST}" "{API_HOST}"}}) '
    'and (starts_with(http.request.uri.path, "/wp-") '
    'or starts_with(http.request.uri.path, "/.env") '
    'or starts_with(http.request.uri.path, "/.git") '
    'or http.request.uri.path eq "/xmlrpc.php" '
    'or http.request.uri.path eq "/phpmyadmin")'
)
SECURITY_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and not starts_with(http.request.uri.path, "/api/"))'
)
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


def notify_skip_rule_body() -> dict:
    return {
        "ref": NOTIFY_SKIP_REF,
        "expression": NOTIFY_SKIP_EXPRESSION,
        "description": (
            "Skip Super Bot Fight Mode for GitHub Actions portal email notify "
            "(datacenter IP; worker enforces X-Notify-Secret)."
        ),
        "action": "skip",
        "enabled": True,
        "action_parameters": {
            "phases": ["http_request_sbfm"],
        },
    }


def _notify_skip_rule_is_correct(rule: dict) -> bool:
    if rule.get("action") != "skip":
        return False
    if rule.get("expression") != NOTIFY_SKIP_EXPRESSION:
        return False
    phases = rule.get("action_parameters", {}).get("phases", [])
    return "http_request_sbfm" in phases


def get_waf_custom_entrypoint_ruleset(token: str, zone_id: str) -> dict | None:
    return get_phase_entrypoint_ruleset(token, zone_id, WAF_CUSTOM_PHASE)


def super_bot_fight_mode_spec() -> dict:
    """Pro-plan Super Bot Fight Mode: challenge definitely automated traffic."""
    return {
        "enable_js": True,
        "sbfm_definitely_automated": "managed_challenge",
        "sbfm_verified_bots": "allow",
    }


def _bot_management_matches(current: dict, expected: dict) -> tuple[bool, list[str]]:
    issues: list[str] = []
    for key, value in expected.items():
        if current.get(key) != value:
            issues.append(
                f"bot_management {key} is {current.get(key)!r}, expected {value!r}."
            )
    fight_mode = current.get("fight_mode")
    if fight_mode is True:
        issues.append(
            "bot_management fight_mode is True; disable legacy Bot Fight Mode when using SBFM."
        )
    return not issues, issues


def get_bot_management_config(token: str, zone_id: str) -> dict:
    body = _api_request("GET", f"/zones/{zone_id}/bot_management", token)
    return body.get("result", {}) if body else {}


def apply_super_bot_fight_mode(token: str, zone_id: str | None) -> None:
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    expected = super_bot_fight_mode_spec()
    current = get_bot_management_config(token, zone)
    ok, _ = _bot_management_matches(current, expected)
    if ok:
        print("Super Bot Fight Mode already configured.")
        return
    payload = {**expected, "fight_mode": False}
    _api_request("PUT", f"/zones/{zone}/bot_management", token, payload)
    print(
        "Super Bot Fight Mode enabled "
        f"(sbfm_definitely_automated={expected['sbfm_definitely_automated']!r})."
    )


def check_portal_edge_security(token: str, zone_id: str | None) -> tuple[bool, list[str]]:
    """Verify SBFM and the /api/notify WAF skip rule."""
    zone = resolve_zone_id(token, zone_id)
    issues: list[str] = []
    ok = True

    ruleset = get_waf_custom_entrypoint_ruleset(token, zone)
    skip_rule = None
    if ruleset:
        skip_rule = next(
            (rule for rule in ruleset.get("rules", []) if rule.get("ref") == NOTIFY_SKIP_REF),
            None,
        )
    if skip_rule is None:
        ok = False
        issues.append(f"Missing WAF skip rule ref {NOTIFY_SKIP_REF!r}.")
    elif not skip_rule.get("enabled", True):
        ok = False
        issues.append(f"WAF skip rule {NOTIFY_SKIP_REF!r} is disabled.")
    elif not _notify_skip_rule_is_correct(skip_rule):
        ok = False
        issues.append(
            f"WAF skip rule {NOTIFY_SKIP_REF!r} does not match expected expression/phases."
        )

    expected = super_bot_fight_mode_spec()
    current = get_bot_management_config(token, zone)
    bot_ok, bot_issues = _bot_management_matches(current, expected)
    ok = ok and bot_ok
    issues.extend(bot_issues)
    return ok, issues


def print_check_portal_edge_security(token: str, zone_id: str | None) -> bool:
    print("Portal edge security check:")
    try:
        ok, issues = check_portal_edge_security(token, zone_id)
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"  ERROR: {exc}")
        return False
    if ok:
        print(
            f"  OK: Super Bot Fight Mode on with WAF skip for {PORTAL_NOTIFY_URL}."
        )
        return True
    for issue in issues:
        print(f"  {issue}")
    return False


def verify_notify_reachable() -> tuple[bool, str]:
    """POST /api/notify without secret; worker 401 means Cloudflare did not challenge."""
    payload = json.dumps({}).encode("utf-8")
    req = urllib.request.Request(
        PORTAL_NOTIFY_URL,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "GitHub-Actions/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read(500).decode("utf-8", errors="replace")
            if resp.status == 401:
                return True, f"OK: worker returned 401 (reachable through edge): {body[:120]}"
            return False, f"Unexpected {resp.status}: {body[:200]}"
    except urllib.error.HTTPError as exc:
        body = exc.read(500).decode("utf-8", errors="replace")
        if exc.code == 401:
            return True, f"OK: worker returned 401 (reachable through edge): {body[:120]}"
        if exc.code == 403 and "just a moment" in body.lower():
            return (
                False,
                "Cloudflare bot challenge blocked /api/notify (403). "
                "Add the WAF skip rule before enabling Super Bot Fight Mode.",
            )
        return False, f"HTTP {exc.code}: {body[:200]}"
    except urllib.error.URLError as exc:
        return False, f"Request failed: {exc.reason}"


def print_verify_notify_reachable() -> bool:
    print("Portal notify reachability check:")
    ok, message = verify_notify_reachable()
    print(f"  {message}")
    return ok


def apply_portal_edge_security(token: str, zone_id: str | None) -> None:
    """WAF skip for /api/notify first, then enable Super Bot Fight Mode."""
    apply_waf_custom_security_rules(token, zone_id)
    apply_super_bot_fight_mode(token, zone_id)


def get_zone_setting(token: str, zone_id: str, setting_id: str):
    body = _api_request("GET", f"/zones/{zone_id}/settings/{setting_id}", token)
    return body.get("result", {}).get("value") if body else None


def security_baseline_settings_spec() -> dict[str, object]:
    return {
        "min_tls_version": "1.2",
        "automatic_https_rewrites": "on",
        "browser_check": "off",
        "ssl": "full",
    }


def security_header_hsts_spec() -> dict:
    return {
        "strict_transport_security": {
            "enabled": True,
            "max_age": HSTS_MAX_AGE_SEC,
            "include_subdomains": True,
            "preload": False,
            "nosniff": False,
        },
    }


def apply_security_baseline(token: str, zone_id: str | None) -> None:
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    for setting_id, value in security_baseline_settings_spec().items():
        current = get_zone_setting(token, zone, setting_id)
        if current == value:
            print(f"Zone setting {setting_id} already {value!r}.")
            continue
        apply_zone_setting(token, zone, setting_id, value)
    hsts_spec = security_header_hsts_spec()
    current_hsts = get_zone_setting(token, zone, "security_header") or {}
    current_sts = current_hsts.get("strict_transport_security", {})
    expected_sts = hsts_spec["strict_transport_security"]
    if all(current_sts.get(key) == expected_sts.get(key) for key in expected_sts):
        print("HSTS already configured.")
    else:
        apply_zone_setting(token, zone, "security_header", hsts_spec)
        print("HSTS enabled (preload=false).")


def check_security_baseline(token: str, zone_id: str | None) -> tuple[bool, list[str]]:
    zone = resolve_zone_id(token, zone_id)
    issues: list[str] = []
    for setting_id, expected in security_baseline_settings_spec().items():
        current = get_zone_setting(token, zone, setting_id)
        if current != expected:
            issues.append(
                f"zone setting {setting_id} is {current!r}, expected {expected!r}."
            )
    current_hsts = get_zone_setting(token, zone, "security_header") or {}
    expected_sts = security_header_hsts_spec()["strict_transport_security"]
    current_sts = current_hsts.get("strict_transport_security", {})
    for key, expected in expected_sts.items():
        if current_sts.get(key) != expected:
            issues.append(
                f"HSTS {key} is {current_sts.get(key)!r}, expected {expected!r}."
            )
    return not issues, issues


def print_check_security_baseline(token: str, zone_id: str | None) -> bool:
    print("Security baseline check:")
    try:
        ok, issues = check_security_baseline(token, zone_id)
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"  ERROR: {exc}")
        return False
    if ok:
        print("  OK: TLS 1.2+, HSTS, HTTPS rewrites, browser_check off, ssl full.")
        return True
    for issue in issues:
        print(f"  {issue}")
    return False


def probe_block_rule_body() -> dict:
    return {
        "ref": PROBE_BLOCK_REF,
        "expression": PROBE_BLOCK_EXPRESSION,
        "description": "Block common scanner probe paths (WordPress, .env, .git).",
        "action": "block",
        "enabled": True,
    }


def _probe_block_rule_is_correct(rule: dict) -> bool:
    return (
        rule.get("action") == "block"
        and rule.get("expression") == PROBE_BLOCK_EXPRESSION
        and rule.get("enabled", True)
    )


def waf_custom_security_rules_spec() -> list[dict]:
    """Custom WAF rules in evaluation order (block probes before notify skip)."""
    return [probe_block_rule_body(), notify_skip_rule_body()]


def _waf_custom_rule_is_correct(rule: dict, expected: dict) -> bool:
    ref = expected.get("ref")
    if rule.get("ref") != ref:
        return False
    if ref == PROBE_BLOCK_REF:
        return _probe_block_rule_is_correct(rule)
    if ref == NOTIFY_SKIP_REF:
        return _notify_skip_rule_is_correct(rule)
    return False


def apply_waf_custom_security_rules(token: str, zone_id: str | None) -> None:
    """Upsert probe-path block and portal notify SBFM skip rules."""
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    expected_rules = waf_custom_security_rules_spec()
    ruleset = get_waf_custom_entrypoint_ruleset(token, zone)
    managed_refs = set(WAF_CUSTOM_MANAGED_REFS)

    if ruleset is None:
        _api_request(
            "POST",
            f"/zones/{zone}/rulesets",
            token,
            {
                "name": "AnalyticMadhyasthDarshan WAF custom rules",
                "kind": "zone",
                "phase": WAF_CUSTOM_PHASE,
                "rules": expected_rules,
            },
        )
        print(f"Created {WAF_CUSTOM_PHASE} ruleset with {len(expected_rules)} custom rules.")
        return

    ruleset_id = ruleset["id"]
    existing_by_ref = {rule.get("ref"): rule for rule in ruleset.get("rules", []) if rule.get("ref")}
    foreign_rules = [
        _sanitize_rule_for_put(rule)
        for rule in ruleset.get("rules", [])
        if rule.get("ref") not in managed_refs
    ]

    if all(
        ref in existing_by_ref and _waf_custom_rule_is_correct(existing_by_ref[ref], expected)
        for ref, expected in zip(WAF_CUSTOM_MANAGED_REFS, expected_rules, strict=True)
    ):
        print("WAF custom security rules already configured.")
        return

    updated_managed: list[dict] = []
    for expected in expected_rules:
        ref = expected["ref"]
        existing = existing_by_ref.get(ref)
        if existing and _waf_custom_rule_is_correct(existing, expected):
            updated_managed.append(_sanitize_rule_for_put(existing))
        else:
            updated_managed.append(expected)

    merged_rules = updated_managed + foreign_rules
    _api_request(
        "PUT",
        f"/zones/{zone}/rulesets/{ruleset_id}",
        token,
        {
            "name": ruleset.get("name", "AnalyticMadhyasthDarshan WAF custom rules"),
            "kind": "zone",
            "phase": WAF_CUSTOM_PHASE,
            "rules": merged_rules,
        },
    )
    print(f"Updated WAF custom ruleset ({len(updated_managed)} managed + {len(foreign_rules)} other).")


def apply_waf_probe_block(token: str, zone_id: str | None) -> None:
    apply_waf_custom_security_rules(token, zone_id)


def apply_notify_waf_skip(token: str, zone_id: str | None) -> None:
    apply_waf_custom_security_rules(token, zone_id)


def _rate_limit_rule(
    ref: str,
    description: str,
    expression: str,
    *,
    requests_per_period: int,
    period: int,
    mitigation_timeout: int | None = None,
) -> dict:
    timeout = mitigation_timeout if mitigation_timeout is not None else period
    return {
        "ref": ref,
        "expression": expression,
        "description": description,
        "action": "block",
        "enabled": True,
        "ratelimit": {
            "characteristics": ["ip.src", "cf.colo.id"],
            "period": period,
            "requests_per_period": requests_per_period,
            "mitigation_timeout": timeout,
        },
    }


def _rate_limit_rule_is_correct(rule: dict, expected: dict) -> bool:
    if rule.get("action") != "block":
        return False
    if rule.get("expression") != expected.get("expression"):
        return False
    return rule.get("ratelimit") == expected.get("ratelimit")


def get_rate_limit_entrypoint_ruleset(token: str, zone_id: str) -> dict | None:
    return get_phase_entrypoint_ruleset(token, zone_id, RATE_LIMIT_PHASE)


def edge_api_rate_limit_expression() -> str:
    """Single rate-limit match for portal (api. host) and discussions (apex /api/...)."""
    return (
        f'(http.host eq "{API_HOST}" and starts_with(http.request.uri.path, "/api/")) '
        f'or (http.host eq "{SITE_HOST}" and ('
        'starts_with(http.request.uri.path, "/api/discussions/") '
        'or http.request.uri.path eq "/api/discuss-auth/magic-link"))'
    )


def edge_api_rate_limit_rules_spec() -> list[dict]:
    """One combined API rate limit (Pro plan allows 2 rules in http_ratelimit phase)."""
    return [
        _rate_limit_rule(
            EDGE_API_RATE_LIMIT_REF,
            "Throttle portal and discussion API per IP",
            edge_api_rate_limit_expression(),
            requests_per_period=40,
            period=10,
        ),
    ]


def _is_legacy_portal_rate_limit_rule(rule: dict) -> bool:
    expression = rule.get("expression", "")
    return API_HOST in expression and "/api/" in expression and rule.get("ref") != EDGE_API_RATE_LIMIT_REF


def apply_discussions_rate_limits(token: str, zone_id: str | None) -> None:
    """Upsert combined portal + discussion API rate limit (Pro: max 2 rules in phase)."""
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    expected_rules = edge_api_rate_limit_rules_spec()
    managed_refs = set(EDGE_API_RATE_LIMIT_REFS)
    ruleset = get_rate_limit_entrypoint_ruleset(token, zone)

    if ruleset is None:
        _api_request(
            "POST",
            f"/zones/{zone}/rulesets",
            token,
            {
                "name": "AnalyticMadhyasthDarshan rate limits",
                "kind": "zone",
                "phase": RATE_LIMIT_PHASE,
                "rules": expected_rules,
            },
        )
        print(f"Created {RATE_LIMIT_PHASE} ruleset with edge API rate limit.")
        return

    ruleset_id = ruleset["id"]
    existing_by_ref = {rule.get("ref"): rule for rule in ruleset.get("rules", []) if rule.get("ref")}
    foreign_rules = [
        _sanitize_rule_for_put(rule)
        for rule in ruleset.get("rules", [])
        if rule.get("ref") not in managed_refs and not _is_legacy_portal_rate_limit_rule(rule)
    ]

    if all(
        ref in existing_by_ref and _rate_limit_rule_is_correct(existing_by_ref[ref], expected)
        for ref, expected in zip(EDGE_API_RATE_LIMIT_REFS, expected_rules, strict=True)
    ):
        print("Edge API rate-limit rule already configured.")
        return

    updated_managed: list[dict] = []
    for expected in expected_rules:
        ref = expected["ref"]
        existing = existing_by_ref.get(ref)
        if existing and _rate_limit_rule_is_correct(existing, expected):
            updated_managed.append(_sanitize_rule_for_put(existing))
        else:
            updated_managed.append(expected)

    merged_rules = foreign_rules + updated_managed
    if len(merged_rules) > 2:
        raise RuntimeError(
            f"http_ratelimit phase allows 2 rules on Pro; merged list has {len(merged_rules)}. "
            "Drop a foreign rule in the dashboard or consolidate limits."
        )
    _api_request(
        "PUT",
        f"/zones/{zone}/rulesets/{ruleset_id}",
        token,
        {
            "name": ruleset.get("name", "AnalyticMadhyasthDarshan rate limits"),
            "kind": "zone",
            "phase": RATE_LIMIT_PHASE,
            "rules": merged_rules,
        },
    )
    print(
        f"Updated rate-limit ruleset ({len(foreign_rules)} other + "
        f"{len(updated_managed)} edge API rule)."
    )


def check_discussions_rate_limits(token: str, zone_id: str | None) -> tuple[bool, list[str]]:
    zone = resolve_zone_id(token, zone_id)
    issues: list[str] = []
    ruleset = get_rate_limit_entrypoint_ruleset(token, zone)
    if ruleset is None:
        return False, [f"No {RATE_LIMIT_PHASE} ruleset found."]
    existing_by_ref = {rule.get("ref"): rule for rule in ruleset.get("rules", []) if rule.get("ref")}
    for expected in edge_api_rate_limit_rules_spec():
        ref = expected["ref"]
        rule = existing_by_ref.get(ref)
        if rule is None:
            issues.append(f"Missing rate-limit rule ref {ref!r}.")
            continue
        if not rule.get("enabled", True):
            issues.append(f"Rate-limit rule {ref!r} is disabled.")
            continue
        if not _rate_limit_rule_is_correct(rule, expected):
            issues.append(f"Rate-limit rule {ref!r} does not match expected expression/limits.")
    return not issues, issues


def print_check_discussions_rate_limits(token: str, zone_id: str | None) -> bool:
    print("Edge API rate-limit check:")
    try:
        ok, issues = check_discussions_rate_limits(token, zone_id)
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"  ERROR: {exc}")
        return False
    if ok:
        print("  OK: combined portal + discussion API rate limit configured.")
        return True
    for issue in issues:
        print(f"  {issue}")
    return False


def _header_set(value: str) -> dict:
    return {"operation": "set", "value": value}


def security_headers_rule_body() -> dict:
    return {
        "ref": SECURITY_HEADERS_REF,
        "expression": SECURITY_HEADERS_EXPRESSION,
        "description": "Security headers for static site pages (not Worker /api JSON).",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "X-Content-Type-Options": _header_set("nosniff"),
                "X-Frame-Options": _header_set("SAMEORIGIN"),
                "Referrer-Policy": _header_set("strict-origin-when-cross-origin"),
                "Permissions-Policy": _header_set("camera=(), microphone=(), geolocation=()"),
                "Content-Security-Policy-Report-Only": _header_set(CSP_REPORT_ONLY),
            },
        },
    }


def _security_headers_rule_is_correct(rule: dict) -> bool:
    if rule.get("action") != "rewrite":
        return False
    if rule.get("expression") != SECURITY_HEADERS_EXPRESSION:
        return False
    headers = rule.get("action_parameters", {}).get("headers", {})
    expected = security_headers_rule_body()["action_parameters"]["headers"]
    for name, spec in expected.items():
        actual = headers.get(name, {})
        if actual.get("operation") != "set" or actual.get("value") != spec["value"]:
            return False
    return True


def get_response_headers_entrypoint_ruleset(token: str, zone_id: str) -> dict | None:
    return get_phase_entrypoint_ruleset(token, zone_id, RESPONSE_HEADERS_PHASE)


def apply_security_headers(token: str, zone_id: str | None) -> None:
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    rule_body = security_headers_rule_body()
    ruleset = get_response_headers_entrypoint_ruleset(token, zone)

    if ruleset is None:
        _api_request(
            "POST",
            f"/zones/{zone}/rulesets",
            token,
            {
                "name": "AnalyticMadhyasthDarshan response security headers",
                "kind": "zone",
                "phase": RESPONSE_HEADERS_PHASE,
                "rules": [rule_body],
            },
        )
        print(f"Created {RESPONSE_HEADERS_PHASE} ruleset with CSP report-only headers.")
        return

    ruleset_id = ruleset["id"]
    rules = ruleset.get("rules", [])
    existing = next((rule for rule in rules if rule.get("ref") == SECURITY_HEADERS_REF), None)
    if existing and _security_headers_rule_is_correct(existing):
        print("Response security headers already configured.")
        return

    if existing:
        updated_rules: list[dict] = []
        for rule in rules:
            if rule.get("ref") == SECURITY_HEADERS_REF:
                updated_rules.append(rule_body)
            else:
                updated_rules.append(_sanitize_rule_for_put(rule))
    else:
        updated_rules = [_sanitize_rule_for_put(rule) for rule in rules] + [rule_body]

    _api_request(
        "PUT",
        f"/zones/{zone}/rulesets/{ruleset_id}",
        token,
        {
            "name": ruleset.get(
                "name", "AnalyticMadhyasthDarshan response security headers"
            ),
            "kind": "zone",
            "phase": RESPONSE_HEADERS_PHASE,
            "rules": updated_rules,
        },
    )
    print("Updated response security headers (CSP report-only).")


def check_security_headers(token: str, zone_id: str | None) -> tuple[bool, list[str]]:
    zone = resolve_zone_id(token, zone_id)
    ruleset = get_response_headers_entrypoint_ruleset(token, zone)
    if ruleset is None:
        return False, [f"No {RESPONSE_HEADERS_PHASE} ruleset found."]
    rule = next(
        (item for item in ruleset.get("rules", []) if item.get("ref") == SECURITY_HEADERS_REF),
        None,
    )
    if rule is None:
        return False, [f"Missing response header rule ref {SECURITY_HEADERS_REF!r}."]
    if not rule.get("enabled", True):
        return False, [f"Response header rule {SECURITY_HEADERS_REF!r} is disabled."]
    if not _security_headers_rule_is_correct(rule):
        return False, [f"Response header rule {SECURITY_HEADERS_REF!r} does not match spec."]
    return True, []


def print_check_security_headers(token: str, zone_id: str | None) -> bool:
    print("Response security headers check:")
    try:
        ok, issues = check_security_headers(token, zone_id)
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"  ERROR: {exc}")
        return False
    if ok:
        print("  OK: static-site security headers with CSP report-only.")
        return True
    for issue in issues:
        print(f"  {issue}")
    return False


def check_waf_custom_security(token: str, zone_id: str | None) -> tuple[bool, list[str]]:
    zone = resolve_zone_id(token, zone_id)
    issues: list[str] = []
    ruleset = get_waf_custom_entrypoint_ruleset(token, zone)
    if ruleset is None:
        return False, [f"No {WAF_CUSTOM_PHASE} ruleset found."]
    existing_by_ref = {rule.get("ref"): rule for rule in ruleset.get("rules", []) if rule.get("ref")}
    expected_rules = waf_custom_security_rules_spec()
    for expected in expected_rules:
        ref = expected["ref"]
        rule = existing_by_ref.get(ref)
        if rule is None:
            issues.append(f"Missing WAF custom rule ref {ref!r}.")
            continue
        if not rule.get("enabled", True):
            issues.append(f"WAF custom rule {ref!r} is disabled.")
            continue
        if not _waf_custom_rule_is_correct(rule, expected):
            issues.append(f"WAF custom rule {ref!r} does not match expected spec.")
    return not issues, issues


def print_check_waf_custom_security(token: str, zone_id: str | None) -> bool:
    print("WAF custom security check:")
    try:
        ok, issues = check_waf_custom_security(token, zone_id)
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"  ERROR: {exc}")
        return False
    if ok:
        print("  OK: probe-path block and portal notify SBFM skip configured.")
        return True
    for issue in issues:
        print(f"  {issue}")
    return False


def apply_edge_security(token: str, zone_id: str | None) -> None:
    """Apply full edge security stack from the hardening plan."""
    apply_security_baseline(token, zone_id)
    apply_waf_custom_security_rules(token, zone_id)
    apply_super_bot_fight_mode(token, zone_id)
    apply_discussions_rate_limits(token, zone_id)
    apply_security_headers(token, zone_id)


def print_check_edge_security(token: str, zone_id: str | None) -> bool:
    checks = [
        print_check_security_baseline(token, zone_id),
        print_check_waf_custom_security(token, zone_id),
        print_check_portal_edge_security(token, zone_id),
        print_check_discussions_rate_limits(token, zone_id),
        print_check_security_headers(token, zone_id),
        print_verify_notify_reachable(),
    ]
    return all(checks)


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
    keep = (
        "ref",
        "expression",
        "description",
        "action",
        "action_parameters",
        "enabled",
        "ratelimit",
    )
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

6. Portal edge security (Pro+): Super Bot Fight Mode with a WAF Skip for GitHub Actions
   POST /api/notify (see infra/worker/README.md):
   python Scripts/_cloudflare_performance.py --apply-portal-edge-security
   python Scripts/_cloudflare_performance.py --check-portal-edge-security

7. Full edge security hardening (TLS, HSTS, probe block, discussion rate limits,
   response headers with CSP report-only):
   python Scripts/_cloudflare_performance.py --apply-edge-security
   python Scripts/_cloudflare_performance.py --check-edge-security
   Operator next steps (CSP enforce, HSTS preload): infra/worker/README.md

8. Re-check RUM after 7 days against infra/cloudflare-rum-baseline.json
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
        "--apply-portal-edge-security",
        action="store_true",
        help=(
            "Enable Super Bot Fight Mode and add a WAF Skip rule for "
            "POST /api/notify (GitHub Actions email notify)."
        ),
    )
    parser.add_argument(
        "--check-portal-edge-security",
        action="store_true",
        help="Verify Super Bot Fight Mode and the portal notify WAF skip rule.",
    )
    parser.add_argument(
        "--apply-security-baseline",
        action="store_true",
        help="Apply TLS 1.2, HSTS, HTTPS rewrites, and disable browser_check.",
    )
    parser.add_argument(
        "--check-security-baseline",
        action="store_true",
        help="Verify zone TLS/HSTS/HTTPS rewrite baseline settings.",
    )
    parser.add_argument(
        "--apply-discussions-rate-limits",
        action="store_true",
        help="Add WAF rate limits for discussion magic-link and comment API routes.",
    )
    parser.add_argument(
        "--apply-security-headers",
        action="store_true",
        help="Add response security headers (CSP report-only) for static site pages.",
    )
    parser.add_argument(
        "--apply-waf-probe-block",
        action="store_true",
        help="Add WAF block rule for common scanner probe paths (with notify skip).",
    )
    parser.add_argument(
        "--apply-edge-security",
        action="store_true",
        help="Apply full edge security stack (baseline, WAF, SBFM, rate limits, headers).",
    )
    parser.add_argument(
        "--check-edge-security",
        action="store_true",
        help="Run all edge security checks (baseline, WAF, portal, rate limits, headers).",
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

    if args.check_edge_security:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --check-edge-security "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        return 0 if print_check_edge_security(token, zone_id) else 1

    if args.check_security_baseline:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --check-security-baseline "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        return 0 if print_check_security_baseline(token, zone_id) else 1

    if args.check_portal_edge_security:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --check-portal-edge-security "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        config_ok = print_check_portal_edge_security(token, zone_id)
        reach_ok = print_verify_notify_reachable()
        return 0 if config_ok and reach_ok else 1

    print_baseline_summary()

    api_error = False

    if args.apply_edge_security:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-edge-security "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_edge_security(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if args.apply_security_baseline:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-security-baseline "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_security_baseline(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if args.apply_discussions_rate_limits:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-discussions-rate-limits "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_discussions_rate_limits(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if args.apply_security_headers:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-security-headers "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_security_headers(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if args.apply_waf_probe_block:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-waf-probe-block "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_waf_probe_block(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

    if args.apply_portal_edge_security:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --apply-portal-edge-security "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            apply_portal_edge_security(token, zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            api_error = True

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

    apply_flags = (
        args.apply_api,
        args.apply_redirect,
        args.apply_discussions_api,
        args.apply_cache_rules,
        args.apply_portal_edge_security,
        args.apply_edge_security,
        args.apply_security_baseline,
        args.apply_discussions_rate_limits,
        args.apply_security_headers,
        args.apply_waf_probe_block,
    )
    if not any(apply_flags):
        print_dashboard_steps()

    if not args.skip_verify:
        print()
        verify_ok = print_verify_root_redirect()
        if token and (args.apply_cache_rules or args.apply_api):
            verify_ok = print_check_cache_rules(token, zone_id) and verify_ok
        if args.apply_edge_security:
            verify_ok = print_check_edge_security(token, zone_id) and verify_ok
        elif args.apply_portal_edge_security:
            verify_ok = print_check_portal_edge_security(token, zone_id) and verify_ok
            verify_ok = print_verify_notify_reachable() and verify_ok
        if not verify_ok:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

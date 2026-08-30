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
import stat
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
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
WEBMCP_SKIP_REF = "amd_skip_sbfm_webmcp"
PROBE_BLOCK_REF = "amd_block_common_probes"
SECURITY_HEADERS_REF = "amd_security_headers_static"
HOMEPAGE_LINK_HEADERS_REF = "amd_homepage_link_headers"
API_CATALOG_HEADERS_REF = "amd_api_catalog_content_type"
AGENT_CARD_HEADERS_REF = "amd_agent_card_content_type"
AGENT_SKILLS_INDEX_HEADERS_REF = "amd_agent_skills_content_type"
AGENT_SKILLS_MD_HEADERS_REF = "amd_agent_skills_md_content_type"
MCP_SERVER_CARD_HEADERS_REF = "amd_mcp_server_card_content_type"
WEB_BOT_AUTH_HEADERS_REF = "amd_web_bot_auth_content_type"
AUTH_MD_HEADERS_REF = "amd_auth_md_content_type"
OAUTH_METADATA_HEADERS_REF = "amd_oauth_metadata_content_type"
EDGE_API_RATE_LIMIT_REF = "amd_rl_edge_api"
WAF_CUSTOM_MANAGED_REFS = (PROBE_BLOCK_REF, NOTIFY_SKIP_REF, WEBMCP_SKIP_REF)
EDGE_API_RATE_LIMIT_REFS = (EDGE_API_RATE_LIMIT_REF,)
HSTS_MAX_AGE_SEC = 31536000
# Enforcing CSP for static pages. Allow Turnstile, in-browser Mermaid (jsDelivr),
# and Cloudflare Web Analytics (beacon). Study HTML still uses inline scripts.
CSP = (
    "default-src 'self'; "
    "script-src 'self' https://challenges.cloudflare.com https://cdn.jsdelivr.net "
    "https://static.cloudflareinsights.com 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self' https://api.analyticmadhyasthdarshan.org "
    "https://challenges.cloudflare.com https://cloudflareinsights.com "
    "https://static.cloudflareinsights.com; "
    "frame-src https://challenges.cloudflare.com; "
    "base-uri 'self'; "
    "form-action 'self'"
)
NOTIFY_SKIP_EXPRESSION = (
    f'(http.host eq "{API_HOST}" and starts_with(http.request.uri.path, "/api/notify"))'
)
WEBMCP_SKIP_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and ('
    'http.request.uri.path eq "/" or '
    'http.request.uri.path eq "/index.html" or '
    'http.request.uri.path eq "/Studies" or '
    'http.request.uri.path eq "/Studies/" or '
    'http.request.uri.path eq "/Studies/index.html" or '
    'http.request.uri.path eq "/webmcp.js" or '
    'http.request.uri.path eq "/api-docs.html" or '
    'http.request.uri.path eq "/mcp" or '
    'http.request.uri.path eq "/mcp/" or '
    'starts_with(http.request.uri.path, "/api/studies") or '
    'starts_with(http.request.uri.path, "/api/glossary") or '
    'http.request.uri.path eq "/api/start-here" or '
    'starts_with(http.request.uri.path, "/api/cite") or '
    'http.request.uri.path eq "/Studies/catalog-topical.json" or '
    'http.request.uri.path eq "/Studies/catalog-formal.json" or '
    'http.request.uri.path eq "/Studies/catalog-applied.json" or '
    'http.request.uri.path eq "/Studies/catalog-all.json" or '
    'http.request.uri.path eq "/Studies/feed.json" or '
    'http.request.uri.path eq "/Studies/glossary.json" or '
    'http.request.uri.path eq "/Studies/start-here.json"))'
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
API_CATALOG_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and http.request.uri.path eq "/.well-known/api-catalog")'
)
AGENT_CARD_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and http.request.uri.path eq "/.well-known/agent-card.json")'
)
AGENT_SKILLS_INDEX_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and ('
    'http.request.uri.path eq "/.well-known/agent-skills/index.json" or '
    'http.request.uri.path eq "/.well-known/agent-skills/index-maintainer.json"))'
)
AGENT_SKILLS_MD_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and starts_with(http.request.uri.path, "/.well-known/agent-skills/") '
    'and ends_with(http.request.uri.path, "/SKILL.md"))'
)
MCP_SERVER_CARD_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and http.request.uri.path eq "/.well-known/mcp/server-card.json")'
)
WEB_BOT_AUTH_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and http.request.uri.path eq "/.well-known/http-message-signatures-directory")'
)
AUTH_MD_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and http.request.uri.path eq "/auth.md")'
)
OAUTH_METADATA_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and ('
    'http.request.uri.path eq "/.well-known/oauth-protected-resource" or '
    'http.request.uri.path eq "/.well-known/oauth-authorization-server"))'
)
AUTH_MD_SNIPPET_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and ('
    'http.request.uri.path eq "/auth.md" or '
    'http.request.uri.path eq "/.well-known/oauth-protected-resource" or '
    'http.request.uri.path eq "/.well-known/oauth-authorization-server" or '
    'http.request.uri.path eq "/agent/auth" or '
    'http.request.uri.path eq "/agent/auth/claim" or '
    'http.request.uri.path eq "/oauth2/token"))'
)
AUTH_MD_CONTENT_TYPE = "text/markdown; charset=utf-8"
OAUTH_METADATA_CONTENT_TYPE = "application/json"
HOMEPAGE_LINK_HEADERS_EXPRESSION = (
    f'(http.host eq "{SITE_HOST}" and ('
    'http.request.uri.path eq "/" or '
    'http.request.uri.path eq "/index.html" or '
    'http.request.uri.path eq "/Studies" or '
    'http.request.uri.path eq "/Studies/" or '
    'http.request.uri.path eq "/Studies/index.html"))'
)
API_CATALOG_CONTENT_TYPE = (
    'application/linkset+json; profile="https://www.rfc-editor.org/rfc/rfc9727"'
)
AGENT_CARD_CONTENT_TYPE = "application/a2a+json"
AGENT_SKILLS_INDEX_CONTENT_TYPE = "application/json"
MCP_SERVER_CARD_CONTENT_TYPE = "application/json"
WEB_BOT_AUTH_CONTENT_TYPE = "application/http-message-signatures-directory+json"
API_CATALOG_LINK = (
    '</.well-known/api-catalog>; rel="api-catalog"; type="application/linkset+json"'
)
# RFC 8288 + RFC 9727 §3: advertise machine-readable surfaces on the homepage.
# Comma-separated values in one Link header are valid (so is multiple Link headers).
HOMEPAGE_LINK = (
    '</.well-known/api-catalog>; rel="api-catalog"; type="application/linkset+json", '
    '</.well-known/agent-card.json>; rel="describedby"; type="application/a2a+json", '
    '</.well-known/agent-skills/index.json>; rel="describedby"; type="application/json", '
    '</.well-known/mcp/server-card.json>; rel="describedby"; type="application/json", '
    '</.well-known/http-message-signatures-directory>; rel="describedby"; type="application/http-message-signatures-directory+json", '
    '</webmcp.js>; rel="describedby"; type="text/javascript", '
    '</auth.md>; rel="describedby"; type="text/markdown", '
    '</.well-known/oauth-protected-resource>; rel="describedby"; type="application/json", '
    '</Studies/catalog-topical.json>; rel="describedby"; type="application/json", '
    '</Studies/catalog-formal.json>; rel="describedby"; type="application/json", '
    '</Studies/catalog-applied.json>; rel="describedby"; type="application/json", '
    '</Studies/catalog-all.json>; rel="describedby"; type="application/json", '
    '</Studies/feed.json>; rel="describedby"; type="application/feed+json", '
    '</Studies/glossary.json>; rel="describedby"; type="application/json", '
    '</llms.txt>; rel="describedby"; type="text/plain", '
    '</mcp>; rel="describedby"; type="application/json", '
    '</api/studies>; rel="describedby"; type="application/json", '
    '</api/glossary>; rel="describedby"; type="application/json", '
    '</api/start-here>; rel="describedby"; type="application/json", '
    '</openapi/submissions.json>; rel="service-desc"; type="application/json", '
    '</openapi/discussions.json>; rel="service-desc"; type="application/json", '
    '</openapi/studies.json>; rel="service-desc"; type="application/json", '
    '</api-docs.html>; rel="service-doc"; type="text/html"'
)
HOMEPAGE_LINK_REQUIRED_RELS = (
    "api-catalog",
    "describedby",
    "service-desc",
    "service-doc",
)
HOMEPAGE_LINK_URLS = (ROOT_URL, CATALOG_URL)
ROOT_REDIRECT_REF = "analyticmadhyasth_root_to_catalog"
AGENT_SKILLS_REDIRECT_REF = "amd_agent_skills_redirect"
AGENT_SKILLS_WORKER_HOST = "amd-agent-skills.raghavamohan.workers.dev"
API_CATALOG_REDIRECT_REF = "amd_api_catalog_redirect"
API_CATALOG_WORKER_HOST = "amd-api-catalog.raghavamohan.workers.dev"
AGENT_CARD_REDIRECT_REF = "amd_agent_card_redirect"
AGENT_CARD_WORKER_HOST = "amd-agent-card.raghavamohan.workers.dev"
AUTH_MD_REDIRECT_REF = "amd_auth_md_redirect"
AUTH_MD_WORKER_HOST = "amd-auth-md.raghavamohan.workers.dev"
MCP_SERVER_CARD_REDIRECT_REF = "amd_mcp_server_card_redirect"
MCP_RUNTIME_REDIRECT_REF = "amd_mcp_runtime_redirect"
MCP_SERVER_CARD_WORKER_HOST = "amd-mcp.raghavamohan.workers.dev"
WEB_BOT_AUTH_REDIRECT_REF = "amd_web_bot_auth_redirect"
WEB_BOT_AUTH_WORKER_HOST = "amd-web-bot-auth.raghavamohan.workers.dev"
DISCOVERY_WORKER_ROUTES = (
    (f"{SITE_HOST}/.well-known/api-catalog*", "amd-api-catalog"),
    (f"{SITE_HOST}/.well-known/agent-card.json", "amd-agent-card"),
    (f"{SITE_HOST}/.well-known/agent-skills/*", "amd-agent-skills"),
    (f"{SITE_HOST}/.well-known/mcp/*", "amd-mcp"),
    (f"{SITE_HOST}/mcp*", "amd-mcp"),
    (f"{SITE_HOST}/api/studies*", "amd-mcp"),
    (f"{SITE_HOST}/api/glossary*", "amd-mcp"),
    (f"{SITE_HOST}/api/start-here*", "amd-mcp"),
    (f"{SITE_HOST}/api/cite*", "amd-mcp"),
    (f"{SITE_HOST}/.well-known/http-message-signatures-directory", "amd-web-bot-auth"),
    (f"{SITE_HOST}/auth.md*", "amd-auth-md"),
    (f"{SITE_HOST}/.well-known/oauth-protected-resource*", "amd-auth-md"),
    (f"{SITE_HOST}/.well-known/oauth-authorization-server*", "amd-auth-md"),
    (f"{SITE_HOST}/agent/auth*", "amd-auth-md"),
    (f"{SITE_HOST}/oauth2/token", "amd-auth-md"),
)
WORKER_DEV_REDIRECT_REFS = (
    AGENT_SKILLS_REDIRECT_REF,
    MCP_SERVER_CARD_REDIRECT_REF,
    MCP_RUNTIME_REDIRECT_REF,
    API_CATALOG_REDIRECT_REF,
    AGENT_CARD_REDIRECT_REF,
    AUTH_MD_REDIRECT_REF,
    WEB_BOT_AUTH_REDIRECT_REF,
)
# Leftover Snippets return HTTP 200 before Workers Routes. Unbind these
# before deleting the workers.dev 302s or the stale documents come back.
STALE_DISCOVERY_SNIPPETS = (
    "amd_api_catalog",
    "amd_agent_card",
    "amd_agent_skills",
    "amd_mcp",
    "amd_mcp_server_card",
    "amd_web_bot_auth",
    "amd_auth_md",
)
SNIPPET_GUARDED_REDIRECT_REFS = frozenset(
    {API_CATALOG_REDIRECT_REF, AGENT_CARD_REDIRECT_REF, AUTH_MD_REDIRECT_REF}
)
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


def cloudflare_account_id() -> str | None:
    return os.environ.get("CLOUDFLARE_ACCOUNT_ID")


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


def apply_discovery_worker_routes(token: str, zone_id: str | None) -> None:
    """Bind apex discovery paths to Workers so workers.dev 302s can be removed."""
    zone = resolve_zone_id(token, zone_id)
    for pattern, script in DISCOVERY_WORKER_ROUTES:
        ensure_worker_route(token, zone, pattern, script)
    print("Discovery worker routes applied.")


def _snippet_rules_list(payload: dict | None) -> list[dict]:
    if not payload:
        return []
    result = payload.get("result")
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return list(result.get("rules") or [])
    return []


def unbind_stale_discovery_snippets(token: str, zone_id: str | None) -> bool:
    """Drop leftover Snippet rules that would win over Workers Routes.

    Returns True when no guarded Snippet remains bound (or none existed).
    """
    zone = resolve_zone_id(token, zone_id)
    try:
        existing = _api_request(
            "GET", f"/zones/{zone}/snippets/snippet_rules", token, allow_404=True
        )
    except RuntimeError as exc:
        print(f"Could not list Snippet rules: {exc}")
        return False
    rules = _snippet_rules_list(existing)
    stale = set(STALE_DISCOVERY_SNIPPETS)
    active_stale = [
        rule.get("snippet_name")
        for rule in rules
        if rule.get("snippet_name") in stale and rule.get("enabled", True)
    ]
    if not active_stale:
        print("No enabled stale discovery Snippet rules bound.")
        return True
    kept = [
        rule
        for rule in rules
        if rule.get("snippet_name") not in stale
    ]
    try:
        _api_request(
            "PUT",
            f"/zones/{zone}/snippets/snippet_rules",
            token,
            {"rules": kept},
        )
        print(f"Unbound stale discovery Snippet rules: {active_stale}")
        return True
    except RuntimeError as exc:
        print(f"Could not unbind discovery Snippets (token may lack Snippets Edit): {exc}")
        return False


def remove_discovery_worker_redirects(
    token: str,
    zone_id: str | None,
    refs: tuple[str, ...] | None = None,
) -> None:
    """Remove workers.dev Redirect Rules after zone Workers Routes exist."""
    zone = resolve_zone_id(token, zone_id)
    ruleset = get_redirect_entrypoint_ruleset(token, zone)
    if ruleset is None:
        print("No redirect ruleset; nothing to remove.")
        return
    drop = set(refs or WORKER_DEV_REDIRECT_REFS)
    rules = [_sanitize_rule_for_put(rule) for rule in ruleset.get("rules", [])]
    kept = [rule for rule in rules if rule.get("ref") not in drop]
    removed = [rule.get("ref") for rule in rules if rule.get("ref") in drop]
    if not removed:
        print("Discovery workers.dev redirects already absent.")
        return
    _api_request(
        "PUT",
        f"/zones/{zone}/rulesets/{ruleset['id']}",
        token,
        {
            "name": ruleset.get("name", "Redirect rules"),
            "kind": "zone",
            "phase": REDIRECT_PHASE,
            "rules": kept,
        },
    )
    print(f"Removed workers.dev redirects: {removed}")


def serve_discovery_from_workers(token: str, zone_id: str | None) -> None:
    """Prefer zone Workers Routes over workers.dev Redirect Rules."""
    apply_discovery_worker_routes(token, zone_id)
    snippets_cleared = unbind_stale_discovery_snippets(token, zone_id)
    drop = list(WORKER_DEV_REDIRECT_REFS)
    if not snippets_cleared:
        for body in (
            api_catalog_redirect_rule_body(),
            agent_card_redirect_rule_body(),
            auth_md_redirect_rule_body(),
        ):
            ensure_redirect_rule(token, zone_id, body)
        drop = [ref for ref in drop if ref not in SNIPPET_GUARDED_REDIRECT_REFS]
        print(
            "Keeping api-catalog, Agent Card, and Auth.md 302s until leftover "
            "Snippets can be unbound (Snippets Edit)."
        )
    remove_discovery_worker_redirects(token, zone_id, tuple(drop))
    purge_urls = [
        f"https://{SITE_HOST}/.well-known/api-catalog",
        f"https://{SITE_HOST}/.well-known/api-catalog/",
        f"https://{SITE_HOST}/.well-known/agent-card.json",
        f"https://{SITE_HOST}/.well-known/agent-skills/index.json",
        f"https://{SITE_HOST}/.well-known/mcp/server-card.json",
        f"https://{SITE_HOST}/mcp",
        f"https://{SITE_HOST}/api/studies",
        f"https://{SITE_HOST}/.well-known/http-message-signatures-directory",
        f"https://{SITE_HOST}/auth.md",
        f"https://{SITE_HOST}/.well-known/oauth-protected-resource",
        f"https://{SITE_HOST}/.well-known/oauth-authorization-server",
    ]
    try:
        purge_cache_files(token, zone_id, purge_urls)
    except RuntimeError as exc:
        print(f"Cache purge skipped: {exc}")


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


def webmcp_skip_rule_body() -> dict:
    return {
        "ref": WEBMCP_SKIP_REF,
        "expression": WEBMCP_SKIP_EXPRESSION,
        "description": (
            "Skip Super Bot Fight Mode for WebMCP catalog pages, MCP Streamable "
            "HTTP at /mcp, and GET /api/studies, /api/glossary, /api/start-here, "
            "and /api/cite so agent scanners can call the read tools without a "
            "managed challenge."
        ),
        "action": "skip",
        "enabled": True,
        "action_parameters": {
            "phases": ["http_request_sbfm"],
        },
    }


def _webmcp_skip_rule_is_correct(rule: dict) -> bool:
    if rule.get("action") != "skip":
        return False
    if rule.get("expression") != WEBMCP_SKIP_EXPRESSION:
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
            "preload": True,
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
        print("HSTS enabled (preload=true).")


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
    """Custom WAF rules in evaluation order (block probes, then SBFM skips)."""
    return [probe_block_rule_body(), notify_skip_rule_body(), webmcp_skip_rule_body()]


def _waf_custom_rule_is_correct(rule: dict, expected: dict) -> bool:
    ref = expected.get("ref")
    if rule.get("ref") != ref:
        return False
    if ref == PROBE_BLOCK_REF:
        return _probe_block_rule_is_correct(rule)
    if ref == NOTIFY_SKIP_REF:
        return _notify_skip_rule_is_correct(rule)
    if ref == WEBMCP_SKIP_REF:
        return _webmcp_skip_rule_is_correct(rule)
    return False


def apply_waf_custom_security_rules(token: str, zone_id: str | None) -> None:
    """Upsert probe-path block, portal notify SBFM skip, and WebMCP SBFM skip."""
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
                "Permissions-Policy": _header_set(
                    "camera=(), microphone=(), geolocation=(), tools=(self)"
                ),
                "Content-Security-Policy": _header_set(CSP),
                "Content-Security-Policy-Report-Only": {"operation": "remove"},
            },
        },
    }


def api_catalog_headers_rule_body() -> dict:
    return {
        "ref": API_CATALOG_HEADERS_REF,
        "expression": API_CATALOG_HEADERS_EXPRESSION,
        "description": "RFC 9727 api-catalog Content-Type and Link header.",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "Content-Type": _header_set(API_CATALOG_CONTENT_TYPE),
                "Link": _header_set(API_CATALOG_LINK),
            },
        },
    }


def agent_card_headers_rule_body() -> dict:
    return {
        "ref": AGENT_CARD_HEADERS_REF,
        "expression": AGENT_CARD_HEADERS_EXPRESSION,
        "description": "A2A Agent Card Content-Type.",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "Content-Type": _header_set(AGENT_CARD_CONTENT_TYPE),
            },
        },
    }


def agent_skills_index_headers_rule_body() -> dict:
    return {
        "ref": AGENT_SKILLS_INDEX_HEADERS_REF,
        "expression": AGENT_SKILLS_INDEX_HEADERS_EXPRESSION,
        "description": "Agent Skills Discovery index Content-Type.",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "Content-Type": _header_set(AGENT_SKILLS_INDEX_CONTENT_TYPE),
            },
        },
    }


def agent_skills_md_headers_rule_body() -> dict:
    return {
        "ref": AGENT_SKILLS_MD_HEADERS_REF,
        "expression": AGENT_SKILLS_MD_HEADERS_EXPRESSION,
        "description": "Agent Skills SKILL.md Content-Type.",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "Content-Type": _header_set(AUTH_MD_CONTENT_TYPE),
            },
        },
    }


def mcp_server_card_headers_rule_body() -> dict:
    return {
        "ref": MCP_SERVER_CARD_HEADERS_REF,
        "expression": MCP_SERVER_CARD_HEADERS_EXPRESSION,
        "description": "MCP Server Card Content-Type.",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "Content-Type": _header_set(MCP_SERVER_CARD_CONTENT_TYPE),
            },
        },
    }


def web_bot_auth_headers_rule_body() -> dict:
    return {
        "ref": WEB_BOT_AUTH_HEADERS_REF,
        "expression": WEB_BOT_AUTH_HEADERS_EXPRESSION,
        "description": "Web Bot Auth directory Content-Type.",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "Content-Type": _header_set(WEB_BOT_AUTH_CONTENT_TYPE),
            },
        },
    }


def homepage_link_headers_rule_body() -> dict:
    return {
        "ref": HOMEPAGE_LINK_HEADERS_REF,
        "expression": HOMEPAGE_LINK_HEADERS_EXPRESSION,
        "description": "RFC 8288 Link headers on the homepage for agent discovery.",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "Link": _header_set(HOMEPAGE_LINK),
            },
        },
    }


def auth_md_headers_rule_body() -> dict:
    return {
        "ref": AUTH_MD_HEADERS_REF,
        "expression": AUTH_MD_HEADERS_EXPRESSION,
        "description": "Auth.md Markdown Content-Type.",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "Content-Type": _header_set(AUTH_MD_CONTENT_TYPE),
            },
        },
    }


def oauth_metadata_headers_rule_body() -> dict:
    return {
        "ref": OAUTH_METADATA_HEADERS_REF,
        "expression": OAUTH_METADATA_HEADERS_EXPRESSION,
        "description": "RFC 8414 / RFC 9728 OAuth metadata Content-Type.",
        "action": "rewrite",
        "enabled": True,
        "action_parameters": {
            "headers": {
                "Content-Type": _header_set(OAUTH_METADATA_CONTENT_TYPE),
            },
        },
    }


def managed_response_header_rules() -> list[dict]:
    # Catalog rule last so its Link header wins on /.well-known/api-catalog
    # if expressions ever overlap.
    return [
        security_headers_rule_body(),
        homepage_link_headers_rule_body(),
        auth_md_headers_rule_body(),
        oauth_metadata_headers_rule_body(),
        agent_card_headers_rule_body(),
        agent_skills_index_headers_rule_body(),
        agent_skills_md_headers_rule_body(),
        mcp_server_card_headers_rule_body(),
        web_bot_auth_headers_rule_body(),
        api_catalog_headers_rule_body(),
    ]


def _header_rule_is_correct(rule: dict, expected: dict) -> bool:
    if rule.get("action") != expected.get("action"):
        return False
    if rule.get("expression") != expected.get("expression"):
        return False
    headers = rule.get("action_parameters", {}).get("headers", {})
    expected_headers = expected.get("action_parameters", {}).get("headers", {})
    for name, spec in expected_headers.items():
        actual = headers.get(name, {})
        if actual.get("operation") != spec.get("operation") or actual.get("value") != spec.get(
            "value"
        ):
            return False
    return True


def _security_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, security_headers_rule_body())


def _api_catalog_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, api_catalog_headers_rule_body())


def _homepage_link_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, homepage_link_headers_rule_body())


def _auth_md_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, auth_md_headers_rule_body())


def _oauth_metadata_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, oauth_metadata_headers_rule_body())


def _agent_card_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, agent_card_headers_rule_body())


def _agent_skills_index_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, agent_skills_index_headers_rule_body())


def _agent_skills_md_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, agent_skills_md_headers_rule_body())


def _mcp_server_card_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, mcp_server_card_headers_rule_body())


def _web_bot_auth_headers_rule_is_correct(rule: dict) -> bool:
    return _header_rule_is_correct(rule, web_bot_auth_headers_rule_body())


def get_response_headers_entrypoint_ruleset(token: str, zone_id: str) -> dict | None:
    return get_phase_entrypoint_ruleset(token, zone_id, RESPONSE_HEADERS_PHASE)


def _upsert_response_header_rules(
    token: str,
    zone_id: str,
    managed_rules: list[dict],
) -> None:
    """Create or update managed response-header transform rules, preserving others."""
    managed_refs = {rule["ref"] for rule in managed_rules}
    ruleset = get_response_headers_entrypoint_ruleset(token, zone_id)

    if ruleset is None:
        _api_request(
            "POST",
            f"/zones/{zone_id}/rulesets",
            token,
            {
                "name": "AnalyticMadhyasthDarshan response security headers",
                "kind": "zone",
                "phase": RESPONSE_HEADERS_PHASE,
                "rules": managed_rules,
            },
        )
        print(
            f"Created {RESPONSE_HEADERS_PHASE} ruleset with {len(managed_rules)} header rules."
        )
        return

    existing_by_ref = {
        rule.get("ref"): rule for rule in ruleset.get("rules", []) if rule.get("ref")
    }
    foreign_rules = [
        _sanitize_rule_for_put(rule)
        for rule in ruleset.get("rules", [])
        if rule.get("ref") not in managed_refs
    ]
    if all(
        ref in existing_by_ref and _header_rule_is_correct(existing_by_ref[ref], expected)
        for expected in managed_rules
        for ref in (expected["ref"],)
    ):
        print("Response header transform rules already configured.")
        return

    updated_managed: list[dict] = []
    for expected in managed_rules:
        existing = existing_by_ref.get(expected["ref"])
        if existing and _header_rule_is_correct(existing, expected):
            updated_managed.append(_sanitize_rule_for_put(existing))
        else:
            updated_managed.append(expected)

    _api_request(
        "PUT",
        f"/zones/{zone_id}/rulesets/{ruleset['id']}",
        token,
        {
            "name": ruleset.get(
                "name", "AnalyticMadhyasthDarshan response security headers"
            ),
            "kind": "zone",
            "phase": RESPONSE_HEADERS_PHASE,
            "rules": updated_managed + foreign_rules,
        },
    )
    print(
        f"Updated response header rules ({len(updated_managed)} managed + {len(foreign_rules)} other)."
    )


def apply_security_headers(token: str, zone_id: str | None) -> None:
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    _upsert_response_header_rules(
        token,
        zone,
        managed_response_header_rules(),
    )


def check_security_headers(token: str, zone_id: str | None) -> tuple[bool, list[str]]:
    zone = resolve_zone_id(token, zone_id)
    ruleset = get_response_headers_entrypoint_ruleset(token, zone)
    if ruleset is None:
        return False, [f"No {RESPONSE_HEADERS_PHASE} ruleset found."]
    existing_by_ref = {
        rule.get("ref"): rule for rule in ruleset.get("rules", []) if rule.get("ref")
    }
    issues: list[str] = []
    for expected, correct in (
        (security_headers_rule_body(), _security_headers_rule_is_correct),
        (homepage_link_headers_rule_body(), _homepage_link_headers_rule_is_correct),
        (auth_md_headers_rule_body(), _auth_md_headers_rule_is_correct),
        (oauth_metadata_headers_rule_body(), _oauth_metadata_headers_rule_is_correct),
        (agent_card_headers_rule_body(), _agent_card_headers_rule_is_correct),
        (agent_skills_index_headers_rule_body(), _agent_skills_index_headers_rule_is_correct),
        (agent_skills_md_headers_rule_body(), _agent_skills_md_headers_rule_is_correct),
        (mcp_server_card_headers_rule_body(), _mcp_server_card_headers_rule_is_correct),
        (web_bot_auth_headers_rule_body(), _web_bot_auth_headers_rule_is_correct),
        (api_catalog_headers_rule_body(), _api_catalog_headers_rule_is_correct),
    ):
        ref = expected["ref"]
        rule = existing_by_ref.get(ref)
        if rule is None:
            issues.append(f"Missing response header rule ref {ref!r}.")
            continue
        if not rule.get("enabled", True):
            issues.append(f"Response header rule {ref!r} is disabled.")
            continue
        if not correct(rule):
            issues.append(f"Response header rule {ref!r} does not match spec.")
    return not issues, issues


def print_check_security_headers(token: str, zone_id: str | None) -> bool:
    print("Response security headers check:")
    try:
        ok, issues = check_security_headers(token, zone_id)
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"  ERROR: {exc}")
        return False
    if ok:
        print(
            "  OK: static-site security headers, homepage RFC 8288 Link, "
            "Auth.md / OAuth metadata Content-Type, A2A Agent Card Content-Type, "
            "Agent Skills Discovery Content-Type, RFC 9727 catalog Content-Type."
        )
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
        print("  OK: probe-path block, portal notify SBFM skip, and WebMCP SBFM skip configured.")
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


def agent_skills_redirect_rule_body() -> dict:
    return {
        "ref": AGENT_SKILLS_REDIRECT_REF,
        "expression": (
            f'(http.host eq "{SITE_HOST}" and '
            'starts_with(http.request.uri.path, "/.well-known/agent-skills/"))'
        ),
        "description": "Serve Agent Skills Discovery from the amd-agent-skills Worker.",
        "action": "redirect",
        "enabled": True,
        "action_parameters": {
            "from_value": {
                "status_code": 302,
                "preserve_query_string": True,
                "target_url": {
                    "expression": (
                        f'concat("https://{AGENT_SKILLS_WORKER_HOST}", http.request.uri.path)'
                    )
                },
            }
        },
    }


def mcp_server_card_redirect_rule_body() -> dict:
    return {
        "ref": MCP_SERVER_CARD_REDIRECT_REF,
        "expression": (
            f'(http.host eq "{SITE_HOST}" and '
            'starts_with(http.request.uri.path, "/.well-known/mcp/"))'
        ),
        "description": "Serve the MCP Server Card from the amd-mcp Worker.",
        "action": "redirect",
        "enabled": True,
        "action_parameters": {
            "from_value": {
                "status_code": 302,
                "preserve_query_string": True,
                "target_url": {
                    "expression": (
                        f'concat("https://{MCP_SERVER_CARD_WORKER_HOST}", http.request.uri.path)'
                    )
                },
            }
        },
    }


def api_catalog_redirect_rule_body() -> dict:
    return {
        "ref": API_CATALOG_REDIRECT_REF,
        "expression": (
            f'(http.host eq "{SITE_HOST}" and ('
            'http.request.uri.path eq "/.well-known/api-catalog" or '
            'http.request.uri.path eq "/.well-known/api-catalog/"))'
        ),
        "description": (
            "Serve RFC 9727 api-catalog from the amd-api-catalog Worker. "
            "302 skips the stale Snippet this token cannot update."
        ),
        "action": "redirect",
        "enabled": True,
        "action_parameters": {
            "from_value": {
                "status_code": 302,
                "preserve_query_string": True,
                "target_url": {
                    "expression": (
                        f'concat("https://{API_CATALOG_WORKER_HOST}", http.request.uri.path)'
                    )
                },
            }
        },
    }


def agent_card_redirect_rule_body() -> dict:
    return {
        "ref": AGENT_CARD_REDIRECT_REF,
        "expression": (
            f'(http.host eq "{SITE_HOST}" and '
            'http.request.uri.path eq "/.well-known/agent-card.json")'
        ),
        "description": (
            "Serve the A2A Agent Card from the amd-agent-card Worker. "
            "302 skips the stale Snippet this token cannot update."
        ),
        "action": "redirect",
        "enabled": True,
        "action_parameters": {
            "from_value": {
                "status_code": 302,
                "preserve_query_string": True,
                "target_url": {
                    "expression": (
                        f'concat("https://{AGENT_CARD_WORKER_HOST}", http.request.uri.path)'
                    )
                },
            }
        },
    }


def auth_md_redirect_rule_body() -> dict:
    return {
        "ref": AUTH_MD_REDIRECT_REF,
        "expression": AUTH_MD_SNIPPET_EXPRESSION,
        "description": (
            "Serve Auth.md and OAuth discovery from the amd-auth-md Worker. "
            "302 skips the stale Snippet this token cannot update."
        ),
        "action": "redirect",
        "enabled": True,
        "action_parameters": {
            "from_value": {
                "status_code": 302,
                "preserve_query_string": True,
                "target_url": {
                    "expression": (
                        f'concat("https://{AUTH_MD_WORKER_HOST}", http.request.uri.path)'
                    )
                },
            }
        },
    }


def mcp_runtime_redirect_rule_body() -> dict:
    return {
        "ref": MCP_RUNTIME_REDIRECT_REF,
        "expression": (
            f'(http.host eq "{SITE_HOST}" and ('
            'http.request.uri.path eq "/mcp" or '
            'http.request.uri.path eq "/mcp/" or '
            'http.request.uri.path eq "/api/studies"))'
        ),
        "description": (
            "Serve MCP Streamable HTTP and GET /api/studies from the amd-mcp "
            "Worker. 308 keeps POST bodies for JSON-RPC."
        ),
        "action": "redirect",
        "enabled": True,
        "action_parameters": {
            "from_value": {
                "status_code": 308,
                "preserve_query_string": True,
                "target_url": {
                    "expression": (
                        f'concat("https://{MCP_SERVER_CARD_WORKER_HOST}", http.request.uri.path)'
                    )
                },
            }
        },
    }


def web_bot_auth_redirect_rule_body() -> dict:
    return {
        "ref": WEB_BOT_AUTH_REDIRECT_REF,
        "expression": (
            f'(http.host eq "{SITE_HOST}" and '
            'http.request.uri.path eq "/.well-known/http-message-signatures-directory")'
        ),
        "description": "Serve the Web Bot Auth directory from the amd-web-bot-auth Worker.",
        "action": "redirect",
        "enabled": True,
        "action_parameters": {
            "from_value": {
                "status_code": 302,
                "preserve_query_string": True,
                "target_url": {
                    "expression": (
                        f'concat("https://{WEB_BOT_AUTH_WORKER_HOST}", http.request.uri.path)'
                    )
                },
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


def _redirect_rule_matches(existing: dict | None, expected: dict) -> bool:
    if not existing:
        return False
    if existing.get("expression") != expected.get("expression"):
        return False
    existing_from = (existing.get("action_parameters") or {}).get("from_value", {})
    expected_from = (expected.get("action_parameters") or {}).get("from_value", {})
    if existing_from.get("status_code") != expected_from.get("status_code"):
        return False
    existing_target = existing_from.get("target_url") or {}
    expected_target = expected_from.get("target_url") or {}
    if not isinstance(existing_target, dict) or not isinstance(expected_target, dict):
        return existing_target == expected_target
    return existing_target.get("expression") == expected_target.get("expression")


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


def ensure_redirect_rule(token: str, zone_id: str | None, rule_body: dict) -> None:
    """Insert or update one Redirect Rule by ref without dropping other rules."""
    zone = resolve_zone_id(token, zone_id)
    ruleset = get_redirect_entrypoint_ruleset(token, zone)
    ref = rule_body["ref"]
    if ruleset is None:
        rules = [root_redirect_rule_body()]
        if ref != ROOT_REDIRECT_REF:
            rules.append(rule_body)
        _api_request(
            "POST",
            f"/zones/{zone}/rulesets",
            token,
            {
                "name": "AnalyticMadhyasthDarshan redirect rules",
                "kind": "zone",
                "phase": REDIRECT_PHASE,
                "rules": rules,
            },
        )
        print(f"Created redirect ruleset including {ref}.")
        return

    rules = ruleset.get("rules") or []
    existing = next((rule for rule in rules if rule.get("ref") == ref), None)
    if (
        existing
        and existing.get("enabled", True)
        and _redirect_rule_matches(existing, rule_body)
    ):
        print(f"Redirect rule already configured: {ref}")
        return

    updated: list[dict] = []
    found = False
    for rule in rules:
        if rule.get("ref") == ref:
            updated.append(rule_body)
            found = True
        else:
            updated.append(_sanitize_rule_for_put(rule))
    if not found:
        updated.append(rule_body)
    _api_request(
        "PUT",
        f"/zones/{zone}/rulesets/{ruleset['id']}",
        token,
        {
            "name": ruleset.get("name", "AnalyticMadhyasthDarshan redirect rules"),
            "kind": "zone",
            "phase": REDIRECT_PHASE,
            "rules": updated,
        },
    )
    print(f"Updated redirect rule {ref}.")


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
                'http.request.uri.path eq "/Studies/catalog-applied.json" or '
                'http.request.uri.path eq "/Studies/catalog-all.json" or '
                'http.request.uri.path eq "/Studies/feed.json" or '
                'http.request.uri.path eq "/Studies/glossary.json"))'
            ),
            edge_ttl_seconds=SECONDS_PER_HOUR,
            browser_ttl_seconds=5 * 60,
        ),
        _cache_rule_body(
            CACHE_RULE_REFS[3],
            "Cache studies catalog shell",
            f'({host} and http.request.uri.path eq "/Studies/index.html")',
            edge_ttl_seconds=2 * SECONDS_PER_HOUR,
            browser_ttl_seconds=10 * 60,
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


def apply_agent_skills_redirect(token: str, zone_id: str | None) -> None:
    """Bind discovery Workers on the apex; drop workers.dev redirects."""
    serve_discovery_from_workers(token, zone_id)


def apply_mcp_server_card_redirect(token: str, zone_id: str | None) -> None:
    """Bind discovery Workers on the apex; drop workers.dev redirects."""
    serve_discovery_from_workers(token, zone_id)


def apply_api_catalog_redirect(token: str, zone_id: str | None) -> None:
    """Bind discovery Workers on the apex; drop workers.dev redirects."""
    serve_discovery_from_workers(token, zone_id)


def apply_agent_card_redirect(token: str, zone_id: str | None) -> None:
    """Bind discovery Workers on the apex; drop workers.dev redirects."""
    serve_discovery_from_workers(token, zone_id)


def apply_auth_md_redirect(token: str, zone_id: str | None) -> None:
    """Bind Auth.md Worker routes; keep a 302 while the leftover Snippet wins."""
    serve_discovery_from_workers(token, zone_id)


def apply_web_bot_auth_redirect(token: str, zone_id: str | None) -> None:
    """Bind discovery Workers on the apex; drop workers.dev redirects."""
    serve_discovery_from_workers(token, zone_id)


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
    getter = getattr(headers, "get", None)
    if callable(getter):
        value = getter(name)
        if value:
            return value
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


def _fetch_root_without_redirect(
    url: str,
    methods: tuple[str, ...] = ("HEAD", "GET"),
) -> tuple[int, Mapping[str, str]]:
    opener = urllib.request.build_opener(_NoRedirectHandler())
    headers = {"User-Agent": VERIFY_USER_AGENT}
    for method in methods:
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


def _missing_link_rels(link_header: str) -> list[str]:
    return [rel for rel in HOMEPAGE_LINK_REQUIRED_RELS if f'rel="{rel}"' not in link_header]


def verify_homepage_link_headers() -> tuple[bool, list[str]]:
    """Check that homepage responses advertise RFC 8288 / RFC 9727 Link relations."""
    issues: list[str] = []
    for url in HOMEPAGE_LINK_URLS:
        try:
            status, headers = _fetch_root_without_redirect(url, methods=("GET", "HEAD"))
        except RuntimeError as exc:
            issues.append(f"{url}: {exc}")
            continue
        link = _header_lookup(headers, "Link")
        missing = _missing_link_rels(link)
        if missing:
            issues.append(
                f"{url} HTTP {status} is missing Link rels {missing}; Link={link!r}"
            )
    return not issues, issues


def print_verify_homepage_link_headers() -> bool:
    print("Homepage Link header check:")
    ok, issues = verify_homepage_link_headers()
    if ok:
        print(
            "  OK: homepage advertises api-catalog, describedby, service-desc, "
            "and service-doc."
        )
        return True
    for issue in issues:
        print(f"  {issue}")
    return False


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


def _graphql(token: str, query: str, variables: dict | None = None) -> dict:
    """POST to Cloudflare GraphQL. Unlike REST, the body has data/errors, not success."""
    payload = {"query": query, "variables": variables or {}}
    req = urllib.request.Request(
        f"{API_BASE}/graphql",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    errors = body.get("errors")
    if errors:
        raise RuntimeError(json.dumps(errors, indent=2))
    return body.get("data") or {}


def resolve_account_id(token: str, zone_id: str | None) -> str:
    account = cloudflare_account_id()
    if account:
        return account
    zone = resolve_zone_id(token, zone_id)
    body = _api_request("GET", f"/zones/{zone}", token)
    account_id = ((body or {}).get("result") or {}).get("account", {}).get("id")
    if not account_id:
        raise RuntimeError("Could not resolve Cloudflare account ID from the zone.")
    return account_id


def _us_to_ms(value) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if numeric < 0:
        return None
    return round(numeric / 1000.0, 1)


def _cls_value(value) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if numeric < 0:
        return None
    return round(numeric, 4)


def _rating_counts(values: list[float], good: float, needs: float) -> dict:
    total = len(values)
    if not total:
        return {
            "good_pct": None,
            "needs_improvement_pct": None,
            "poor_pct": None,
            "n": 0,
        }
    good_n = sum(1 for v in values if v <= good)
    needs_n = sum(1 for v in values if good < v <= needs)
    poor_n = total - good_n - needs_n
    return {
        "good_pct": round(100 * good_n / total, 1),
        "needs_improvement_pct": round(100 * needs_n / total, 1),
        "poor_pct": round(100 * poor_n / total, 1),
        "n": total,
    }


def _quantiles_to_vitals(quantiles: dict | None) -> dict:
    q = quantiles or {}
    return {
        "lcp_p75_ms": _us_to_ms(q.get("largestContentfulPaintP75")),
        "inp_p75_ms": _us_to_ms(q.get("interactionToNextPaintP75")),
        "cls_p75": _cls_value(q.get("cumulativeLayoutShiftP75")),
        "ttfb_p75_ms": _us_to_ms(q.get("timeToFirstByteP75")),
    }


def export_rum_baseline(token: str, zone_id: str | None) -> Path:
    """Re-export Web Analytics Core Web Vitals into infra/cloudflare-rum-baseline.json."""
    account_id = resolve_account_id(token, zone_id)
    end = datetime.now(timezone.utc).replace(microsecond=0)
    start = end - timedelta(days=7)
    start_iso = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    variables = {
        "accountTag": account_id,
        "start": start_iso,
        "end": end_iso,
    }

    groups_query = """
query ($accountTag: string, $start: Time, $end: Time) {
  viewer {
    accounts(filter: {accountTag: $accountTag}) {
      overall: rumWebVitalsEventsAdaptiveGroups(
        filter: {datetime_geq: $start, datetime_leq: $end}
        limit: 1
      ) {
        count
        quantiles {
          largestContentfulPaintP50
          largestContentfulPaintP75
          largestContentfulPaintP90
          largestContentfulPaintP99
          interactionToNextPaintP75
          cumulativeLayoutShiftP75
          timeToFirstByteP75
        }
      }
      byPath: rumWebVitalsEventsAdaptiveGroups(
        filter: {datetime_geq: $start, datetime_leq: $end}
        limit: 20
        orderBy: [count_DESC]
      ) {
        count
        dimensions { requestPath }
        quantiles {
          largestContentfulPaintP75
          interactionToNextPaintP75
          cumulativeLayoutShiftP75
          timeToFirstByteP75
        }
      }
    }
  }
}
"""
    data = _graphql(token, groups_query, variables)
    accounts = ((data.get("viewer") or {}).get("accounts") or [])
    if not accounts:
        raise RuntimeError("GraphQL returned no accounts for RUM export.")
    account = accounts[0]
    overall_rows = account.get("overall") or []
    overall = overall_rows[0] if overall_rows else {}
    overall_q = _quantiles_to_vitals(overall.get("quantiles"))
    sample_n = int(overall.get("count") or 0)

    by_path = []
    catalog_n = 0
    catalog_vitals = {}
    for row in account.get("byPath") or []:
        path = ((row.get("dimensions") or {}).get("requestPath")) or ""
        vitals = _quantiles_to_vitals(row.get("quantiles"))
        count = int(row.get("count") or 0)
        entry = {"request_path": path, "pageviews": count, **vitals}
        by_path.append(entry)
        if path in ("/Studies/index.html", "/Studies/", "/Studies"):
            catalog_n += count
            if path == "/Studies/index.html":
                catalog_vitals = vitals

    ratings: dict[str, dict] = {}
    rating_note = (
        "Cloudflare GraphQL has no LCP/INP per-event fields and no lcpRating "
        "dimension, so LCP/INP good/needs/poor % cannot be recomputed from the "
        "API. The June dashboard export remains under previous."
    )
    events_query = """
query ($accountTag: string, $start: Time, $end: Time) {
  viewer {
    accounts(filter: {accountTag: $accountTag}) {
      rumWebVitalsEventsAdaptive(
        filter: {datetime_geq: $start, datetime_leq: $end}
        limit: 5000
      ) {
        cumulativeLayoutShift
        requestPath
      }
    }
  }
}
"""
    try:
        events_data = _graphql(token, events_query, variables)
        events_accounts = ((events_data.get("viewer") or {}).get("accounts") or [])
        events = (
            (events_accounts[0].get("rumWebVitalsEventsAdaptive") or [])
            if events_accounts
            else []
        )
        cls_vals = [
            v
            for v in (_cls_value(e.get("cumulativeLayoutShift")) for e in events)
            if v is not None
        ]
        if cls_vals:
            ratings["cls"] = _rating_counts(cls_vals, 0.1, 0.25)
            rating_note = (
                "LCP/INP good/needs/poor % are not in GraphQL (no per-event LCP "
                "and no rating dimension). CLS % is computed from "
                "rumWebVitalsEventsAdaptive samples using thresholds 0.1 / 0.25. "
                "The June dashboard LCP/INP/CLS percentages remain under previous. "
                "Sample is small; treat percentages as directional."
            )
    except (RuntimeError, urllib.error.URLError) as exc:
        rating_note = (
            "GraphQL has no LCP/INP rating buckets. Event CLS query failed "
            f"({exc}). June dashboard good/needs/poor % remain under previous."
        )

    existing: dict = {}
    if BASELINE_PATH.is_file():
        existing = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    previous = existing.get("previous")
    if previous is None and existing.get("period", {}).get("start", "").startswith("2026-06-24"):
        previous = {k: v for k, v in existing.items() if k != "previous"}
    elif previous is None and existing.get("core_web_vitals"):
        previous = {k: v for k, v in existing.items() if k != "previous"}

    lcp_block = {
        "good_pct": (ratings.get("lcp") or {}).get("good_pct"),
        "needs_improvement_pct": (ratings.get("lcp") or {}).get("needs_improvement_pct"),
        "poor_pct": (ratings.get("lcp") or {}).get("poor_pct"),
        "p50_ms": _us_to_ms((overall.get("quantiles") or {}).get("largestContentfulPaintP50")),
        "p75_ms": overall_q["lcp_p75_ms"],
        "p90_ms": _us_to_ms((overall.get("quantiles") or {}).get("largestContentfulPaintP90")),
        "p99_ms": _us_to_ms((overall.get("quantiles") or {}).get("largestContentfulPaintP99")),
    }
    payload = {
        "site": SITE_HOST,
        "captured_from": "Cloudflare GraphQL rumWebVitalsEventsAdaptiveGroups",
        "captured_at": end_iso,
        "account_id": account_id,
        "period": {"start": start_iso, "end": end_iso},
        "filters": {
            "exclude_bots": True,
            "note": "RUM beacons only. GraphQL groups have no extra bot-filter dimension.",
        },
        "sample": {
            "pageviews": sample_n,
            "catalog_pageviews": catalog_n,
            "note": (
                "n is small; do not treat this week as a confirmed regression "
                "against the June dashboard export."
            ),
        },
        "core_web_vitals": {
            "lcp": lcp_block,
            "inp": {
                "good_pct": (ratings.get("inp") or {}).get("good_pct"),
                "needs_improvement_pct": (ratings.get("inp") or {}).get("needs_improvement_pct"),
                "poor_pct": (ratings.get("inp") or {}).get("poor_pct"),
                "p75_ms": overall_q["inp_p75_ms"],
            },
            "cls": {
                "good_pct": (ratings.get("cls") or {}).get("good_pct"),
                "needs_improvement_pct": (ratings.get("cls") or {}).get("needs_improvement_pct"),
                "poor_pct": (ratings.get("cls") or {}).get("poor_pct"),
                "p75": overall_q["cls_p75"],
            },
            "ttfb": {"p75_ms": overall_q["ttfb_p75_ms"]},
        },
        "catalog": {
            "request_path": "/Studies/index.html",
            **catalog_vitals,
        },
        "by_path": by_path,
        "rating_method": rating_note,
        "verification": {
            "recheck_after_days": 7,
            "targets": {
                "lcp_p99_ms_max": 2500,
                "lcp_poor_pct_max": 0,
                "cls_p75_max": 0.1,
            },
            "notes": (
                "Re-run python Scripts/_cloudflare_performance.py "
                "--export-rum-baseline after the landing-page changes have been "
                "cached at the edge for a week. Compare LCP P75/P90/P99, CLS p75, "
                "and rating percentages when event samples exist."
            ),
        },
    }
    if previous:
        payload["previous"] = previous

    if BASELINE_PATH.exists():
        BASELINE_PATH.chmod(stat.S_IWRITE | stat.S_IREAD)
    with BASELINE_PATH.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"Wrote RUM baseline to {BASELINE_PATH.relative_to(BASE)} ({sample_n} pageviews).")
    return BASELINE_PATH


def print_dashboard_steps() -> None:
    print(
        f"""
Cloudflare dashboard steps for {SITE_HOST} (GitHub Pages origin, orange-cloud proxy):

1. DNS - confirm A/CNAME for {SITE_HOST} is Proxied (orange cloud).

2. Rules -> Redirect Rules (or run: python Scripts/_cloudflare_performance.py --apply-redirect)
   Root 301 to https://{SITE_HOST}/Studies/index.html (API uses ref {ROOT_REDIRECT_REF})

   3. Caching -> Cache Rules (or run: python Scripts/_cloudflare_performance.py --apply-cache-rules)
   Order matters; more specific rules first — PDFs, images, catalog JSON,
   catalog shell, then other HTML. The catalog shell
   (/Studies/index.html) uses a 2-hour edge TTL and a 10-minute browser TTL
   (same as other HTML); purge the catalog URL on deploy.

4. Speed -> Optimization - Brotli and HTTP/3 (run: python Scripts/_cloudflare_performance.py --apply-api).
   Auto Minify was deprecated by Cloudflare in 2024 and is not applied via API.

5. After deploy, verify the root redirect (this script runs the check by default):
   python Scripts/_cloudflare_performance.py --verify-only

6. Portal edge security (Pro+): Super Bot Fight Mode with a WAF Skip for GitHub Actions
   POST /api/notify (see infra/worker/README.md):
   python Scripts/_cloudflare_performance.py --apply-portal-edge-security
   python Scripts/_cloudflare_performance.py --check-portal-edge-security

7. Full edge security hardening (TLS, HSTS, probe block, discussion rate limits,
   response headers with enforcing CSP):
   python Scripts/_cloudflare_performance.py --apply-edge-security
   python Scripts/_cloudflare_performance.py --check-edge-security
   Optional remaining steps (HSTS preload list, human smoke tests): infra/worker/README.md

8. Re-check RUM after 7 days:
   python Scripts/_cloudflare_performance.py --export-rum-baseline
   Targets: LCP P99 < 2500 ms, LCP poor % near 0, CLS p75 <= 0.1.
"""
    )


def print_baseline_summary() -> None:
    if not BASELINE_PATH.is_file():
        print(f"Baseline file not found: {BASELINE_PATH}")
        return
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    lcp = data.get("core_web_vitals", {}).get("lcp", {})
    sample = data.get("sample") or {}
    print("RUM baseline:")
    source = data.get("captured_from")
    if source:
        print(f"  source: {source}")
    pageviews = sample.get("pageviews")
    if pageviews is not None:
        print(f"  sample: {pageviews} pageviews")
    parts = []
    if lcp.get("good_pct") is not None:
        parts.append(f"good {lcp.get('good_pct')}%")
    if lcp.get("poor_pct") is not None:
        parts.append(f"poor {lcp.get('poor_pct')}%")
    if lcp.get("p75_ms") is not None:
        parts.append(f"P75 {lcp.get('p75_ms')}ms")
    if lcp.get("p50_ms") is not None:
        parts.append(f"P50 {lcp.get('p50_ms')}ms")
    if lcp.get("p99_ms") is not None:
        parts.append(f"P99 {lcp.get('p99_ms')}ms")
    if parts:
        print("  LCP " + " | ".join(parts))
    cls = data.get("core_web_vitals", {}).get("cls", {})
    if cls.get("p75") is not None:
        print(f"  CLS p75 {cls.get('p75')}")


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
        "--export-rum-baseline",
        action="store_true",
        help="Re-export Web Analytics Core Web Vitals into infra/cloudflare-rum-baseline.json.",
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
        help=(
            "Add response security headers (enforcing CSP), homepage RFC 8288 "
            "Link headers, Auth.md / OAuth metadata Content-Type, A2A Agent Card "
            "Content-Type, Agent Skills Discovery Content-Type, and RFC 9727 "
            "api-catalog Content-Type."
        ),
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
                    f"https://{SITE_HOST}/webmcp.js",
                    f"https://{SITE_HOST}/api-docs.html",
                    f"https://{SITE_HOST}/index.html",
                    f"https://{SITE_HOST}/Studies/catalog-topical.json",
                    f"https://{SITE_HOST}/Studies/catalog-formal.json",
                    f"https://{SITE_HOST}/Studies/catalog-applied.json",
                    f"https://{SITE_HOST}/Studies/catalog-all.json",
                    f"https://{SITE_HOST}/Studies/feed.json",
                    f"https://{SITE_HOST}/Studies/glossary.json",
                    f"https://{SITE_HOST}/llms.txt",
                    f"https://{SITE_HOST}/llms-full.txt",
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

    if args.export_rum_baseline:
        if not token:
            print(
                "CLOUDFLARE_API_TOKEN is required for --export-rum-baseline "
                "(set in .env or the process environment).",
                file=sys.stderr,
            )
            return 1
        try:
            export_rum_baseline(token, zone_id)
        except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            return 1
        print_baseline_summary()
        return 0

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
            serve_discovery_from_workers(token, zone_id)
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
            serve_discovery_from_workers(token, zone_id)
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
        if args.apply_security_headers or args.apply_edge_security:
            verify_ok = print_verify_homepage_link_headers() and verify_ok
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

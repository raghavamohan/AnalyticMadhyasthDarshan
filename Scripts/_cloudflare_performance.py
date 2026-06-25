#!/usr/bin/env python3
"""Cloudflare performance setup for analyticmadhyasthdarshan.org (GitHub Pages + proxy).

Applies zone settings via API when CLOUDFLARE_API_TOKEN is set, and always prints
dashboard steps for redirect and cache rules that require the Rules UI or advanced API.

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

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent
BASELINE_PATH = BASE / "infra" / "cloudflare-rum-baseline.json"
SITE_HOST = "analyticmadhyasthdarshan.org"
API_BASE = "https://api.cloudflare.com/client/v4"


def _api_request(
    method: str,
    path: str,
    token: str,
    payload: dict | None = None,
) -> dict:
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
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
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


def apply_api_settings(token: str, zone_id: str | None) -> None:
    zone = resolve_zone_id(token, zone_id)
    print(f"Zone ID: {zone}")
    apply_zone_setting(token, zone, "minify", {"css": "on", "html": "on", "js": "on"})
    apply_zone_setting(token, zone, "http3", "on")
    apply_zone_setting(token, zone, "brotli", "on")
    print("Zone optimization settings applied.")


def print_dashboard_steps() -> None:
    print(
        f"""
Cloudflare dashboard steps for {SITE_HOST} (GitHub Pages origin, orange-cloud proxy):

1. DNS - confirm A/CNAME for {SITE_HOST} is Proxied (orange cloud).

2. Rules -> Redirect Rules — single 301 (preserve query string):
   If: Host equals {SITE_HOST} AND URI Path equals /
   Then: Static redirect to https://{SITE_HOST}/Studies/index.html (301)

3. Caching -> Cache Rules (order matters; more specific first):
   a) PDFs - If URI Path ends with .pdf
      Cache eligibility: eligible | Edge TTL: 1 month | Browser TTL: 1 day
   b) Images - If URI Path matches *.png OR *.jpg OR *.webp OR *.svg
      Cache eligibility: eligible | Edge TTL: 1 month | Browser TTL: 7 days
   c) Catalog JSON - If URI Path is /Studies/catalog-topical.json OR
      /Studies/catalog-formal.json OR /Studies/catalog-applied.json
      Edge TTL: 1 hour | Browser TTL: 5 minutes
   d) HTML - If URI Path ends with .html OR URI Path is /Studies/
      Edge TTL: 2 hours | Browser TTL: 10 minutes

4. Speed -> Optimization - Auto Minify: HTML, CSS, JS; Brotli on; HTTP/3 on.

5. After deploy, verify:
   curl -I https://{SITE_HOST}/
   (expect 301 to /Studies/index.html from Cloudflare redirect rule)

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
    parser = argparse.ArgumentParser(description="Cloudflare performance setup helper.")
    parser.add_argument(
        "--apply-api",
        action="store_true",
        help="Apply minify/http3/brotli via Cloudflare API (needs CLOUDFLARE_API_TOKEN).",
    )
    parser.add_argument(
        "--zone-id",
        default=os.environ.get("CLOUDFLARE_ZONE_ID"),
        help="Zone ID (default: CLOUDFLARE_ZONE_ID env or lookup by hostname).",
    )
    args = parser.parse_args()

    print_baseline_summary()

    if args.apply_api:
        token = os.environ.get("CLOUDFLARE_API_TOKEN")
        if not token:
            print("CLOUDFLARE_API_TOKEN is required for --apply-api.", file=sys.stderr)
            return 1
        try:
            apply_api_settings(token, args.zone_id)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"API error: {exc}", file=sys.stderr)
            return 1

    print_dashboard_steps()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

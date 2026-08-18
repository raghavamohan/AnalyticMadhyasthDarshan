"""Publish DNS for AI Discovery (DNS-AID) records on analyticmadhyasthdarshan.org.

Creates ServiceMode HTTPS records under `_agents` (RFC 9460) and enables
DNSSEC so validating resolvers return authenticated answers.

    python Scripts/_publish_dns_aid.py
    python Scripts/_publish_dns_aid.py --check

Token scopes: Zone:DNS:Edit. DNSSEC enable also needs Zone:DNSSEC:Edit.
If the domain is not at Cloudflare Registrar, copy the printed DS record
to the registrar so the parent zone can complete the chain of trust.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cloudflare_performance as cf

ZONE = cf.SITE_HOST
TTL = 3600
COMMENT = "DNS-AID — agent discovery"
INDEX_NAME = f"_index._agents.{ZONE}"
A2A_NAME = f"_a2a._agents.{ZONE}"
# Private-use SvcParamKeys until IANA registers DNS-AID names (dns-aid-core).
KEY_CAP = "key65400"
KEY_WELL_KNOWN = "key65409"
INDEX_CAP = f"https://{ZONE}/.well-known/api-catalog"
A2A_CAP = f"https://{ZONE}/.well-known/agent-card.json"

RECORDS = (
    {
        "name": INDEX_NAME,
        "type": "HTTPS",
        "priority": 1,
        "target": ZONE,
        "value": f'alpn="h3,h2" port=443 {KEY_CAP}="{INDEX_CAP}"',
    },
    {
        "name": A2A_NAME,
        "type": "HTTPS",
        "priority": 1,
        "target": ZONE,
        "value": (
            f'alpn="a2a" port=443 mandatory="alpn,port" '
            f'{KEY_CAP}="{A2A_CAP}" {KEY_WELL_KNOWN}="agent-card.json"'
        ),
    },
)


def _record_payload(record: dict) -> dict:
    return {
        "type": record["type"],
        "name": record["name"],
        "ttl": TTL,
        "comment": COMMENT,
        "data": {
            "priority": record["priority"],
            "target": record["target"],
            "value": record["value"],
        },
    }


def find_record(token: str, zone_id: str, record: dict) -> dict | None:
    name = quote(record["name"])
    rtype = quote(record["type"])
    body = cf._api_request(
        "GET",
        f"/zones/{zone_id}/dns_records?type={rtype}&name={name}",
        token,
    )
    results = (body or {}).get("result") or []
    return results[0] if results else None


def upsert_record(token: str, zone_id: str, record: dict) -> dict:
    existing = find_record(token, zone_id, record)
    payload = _record_payload(record)
    if existing:
        body = cf._api_request(
            "PUT",
            f"/zones/{zone_id}/dns_records/{existing['id']}",
            token,
            payload,
        )
        verb = "Updated"
    else:
        body = cf._api_request(
            "POST",
            f"/zones/{zone_id}/dns_records",
            token,
            payload,
        )
        verb = "Created"
    result = (body or {}).get("result") or {}
    content = result.get("content") or record["value"]
    print(f"{verb} {record['type']} {record['name']} -> {content}")
    return result


def get_dnssec(token: str, zone_id: str) -> dict:
    body = cf._api_request("GET", f"/zones/{zone_id}/dnssec", token)
    return (body or {}).get("result") or {}


def enable_dnssec(token: str, zone_id: str) -> dict:
    current = get_dnssec(token, zone_id)
    status = str(current.get("status") or "").lower()
    if status in {"active", "pending"}:
        print(f"DNSSEC already {status}.")
        return current
    body = cf._api_request(
        "PATCH",
        f"/zones/{zone_id}/dnssec",
        token,
        {"status": "active"},
    )
    result = (body or {}).get("result") or {}
    print(f"DNSSEC status: {result.get('status')}")
    return result


def print_dnssec(result: dict) -> None:
    status = result.get("status")
    ds = result.get("ds")
    print(f"DNSSEC status: {status}")
    if ds:
        print("DS record (Cloudflare Registrar submits this via CDS/CDNSKEY; allow 1-2 days):")
        print(f"  {ds}")
    key_tag = result.get("key_tag")
    if key_tag is not None:
        print(
            f"  Key tag: {key_tag}; algorithm: {result.get('algorithm')}; "
            f"digest type: {result.get('digest_type')}"
        )
    if str(status or "").lower() == "pending":
        print(
            "DNSSEC is pending the parent DS. Cloudflare Registrar scans CDS/CDNSKEY "
            "and publishes DS at the .org registry; validating resolvers return AD=true after that."
        )


def check_records(token: str, zone_id: str) -> int:
    failed = 0
    for record in RECORDS:
        existing = find_record(token, zone_id, record)
        if not existing:
            print(f"MISSING {record['type']} {record['name']}")
            failed += 1
            continue
        content = str(existing.get("content") or "")
        print(f"OK {existing.get('type')} {existing.get('name')} {content}")
        if "alpn" not in content.lower() or "port=" not in content.lower():
            print("  missing alpn or port")
            failed += 1
        data = existing.get("data") or {}
        priority = data.get("priority")
        if priority is None and content.split()[:1]:
            try:
                priority = int(content.split()[0])
            except ValueError:
                priority = None
        try:
            priority_n = int(priority)
        except (TypeError, ValueError):
            priority_n = 0
        if priority_n < 1:
            print(f"  expected ServiceMode priority >= 1, got {priority!r}")
            failed += 1
    dnssec = get_dnssec(token, zone_id)
    print_dnssec(dnssec)
    status = str(dnssec.get("status") or "").lower()
    if status not in {"active", "pending"}:
        print("DNSSEC is not enabled.")
        failed += 1
    return failed


def apply_records(token: str, zone_id: str, *, enable_sec: bool) -> int:
    for record in RECORDS:
        upsert_record(token, zone_id, record)
    if enable_sec:
        try:
            print_dnssec(enable_dnssec(token, zone_id))
        except RuntimeError as exc:
            print(f"DNSSEC enable failed: {exc}", file=sys.stderr)
            print(
                "Publish the HTTPS records anyway. Enable DNSSEC in the "
                "Cloudflare dashboard and add the DS record at the registrar.",
                file=sys.stderr,
            )
            return 1
    print()
    print("Verify with:")
    print(f"  python Scripts/_test_dns_aid.py --live")
    print(
        "  POST https://isitagentready.com/api/scan "
        f'{{"url":"https://{ZONE}"}}'
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish DNS-AID HTTPS records.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="List existing DNS-AID records and DNSSEC status; do not write.",
    )
    parser.add_argument(
        "--no-dnssec",
        action="store_true",
        help="Skip enabling DNSSEC (records only).",
    )
    args = parser.parse_args()
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    if not token:
        print("CLOUDFLARE_API_TOKEN is required.", file=sys.stderr)
        return 1
    zone_id = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    if args.check:
        return 1 if check_records(token, zone_id) else 0
    return apply_records(token, zone_id, enable_sec=not args.no_dnssec)


if __name__ == "__main__":
    raise SystemExit(main())

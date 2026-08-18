"""Validate DNS for AI Discovery (DNS-AID) records.

Run from the repository root:

    python Scripts/_test_dns_aid.py
    python Scripts/_test_dns_aid.py --live
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE
from _publish_dns_aid import (
    A2A_CAP,
    A2A_NAME,
    INDEX_CAP,
    INDEX_NAME,
    KEY_CAP,
    KEY_WELL_KNOWN,
    RECORDS,
    ZONE,
)

DOH_CLOUDFLARE = "https://cloudflare-dns.com/dns-query"
DOH_GOOGLE = "https://dns.google/resolve"
LIVE_UA = "AnalyticMadhyasthDarshan-dns-aid-test/1.0"
HTTPS_TYPE = 65
DS_TYPE = 43


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check_records_spec() -> None:
    names = {record["name"] for record in RECORDS}
    if INDEX_NAME not in names:
        fail(f"RECORDS must include {INDEX_NAME}")
    if A2A_NAME not in names:
        fail(f"RECORDS must include {A2A_NAME}")
    if any("_mcp._agents" in record["name"] for record in RECORDS):
        fail("do not advertise _mcp._agents under DNS-AID")
    for record in RECORDS:
        if record["type"] not in {"HTTPS", "SVCB"}:
            fail(f"{record['name']} must be HTTPS or SVCB, got {record['type']}")
        if int(record["priority"]) < 1:
            fail(f"{record['name']} must be ServiceMode (priority >= 1)")
        if record["target"] != ZONE:
            fail(f"{record['name']} target must be {ZONE}, not a vendor hostname")
        value = record["value"]
        if "alpn=" not in value or "port=" not in value:
            fail(f"{record['name']} must set alpn and port")
        if " cap=" in f" {value}" or " well-known=" in f" {value}":
            fail(f"{record['name']} must use numeric {KEY_CAP}/{KEY_WELL_KNOWN}, not unregistered names")
        if KEY_CAP not in value:
            fail(f"{record['name']} must carry experimental {KEY_CAP} (cap)")
    index_value = next(record["value"] for record in RECORDS if record["name"] == INDEX_NAME)
    a2a_value = next(record["value"] for record in RECORDS if record["name"] == A2A_NAME)
    if INDEX_CAP not in index_value:
        fail("index cap must point at the RFC 9727 api-catalog")
    if A2A_CAP not in a2a_value:
        fail("A2A cap must point at the Agent Card")
    if 'alpn="a2a"' not in a2a_value:
        fail('A2A record must set alpn="a2a"')
    if "mandatory=" not in a2a_value:
        fail("A2A record must set mandatory=alpn,port")
    print("OK: DNS-AID records are ServiceMode HTTPS under _agents with alpn, port, and key65400.")


def check_docs() -> None:
    auth = (BASE / "auth.md").read_text(encoding="utf-8")
    if INDEX_NAME not in auth or A2A_NAME not in auth:
        fail("auth.md must document _index._agents and _a2a._agents")
    if "DNS-AID" not in auth and "DNS for AI Discovery" not in auth:
        fail("auth.md must name DNS-AID")
    docs = (BASE / "api-docs.html").read_text(encoding="utf-8")
    if INDEX_NAME not in docs:
        fail("api-docs.html must document _index._agents")
    print("OK: auth.md and api-docs.html document DNS-AID.")


def _doh_url(resolver: str, name: str, rtype: str | int) -> str:
    parsed = urllib.parse.urlparse(resolver)
    query = urllib.parse.parse_qs(parsed.query)
    query["name"] = [name]
    query["type"] = [str(rtype)]
    query["do"] = ["1"]
    return urllib.parse.urlunparse(
        parsed._replace(query=urllib.parse.urlencode(query, doseq=True))
    )


def doh_query(name: str, rtype: str | int, resolver: str | None = None) -> dict:
    resolvers = [resolver] if resolver else [DOH_CLOUDFLARE, DOH_GOOGLE]
    last_error: Exception | None = None
    for index, url_base in enumerate(resolvers):
        url = _doh_url(url_base, name, rtype)
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/dns-json", "User-Agent": LIVE_UA},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as exc:
            last_error = exc
            if resolver or index == len(resolvers) - 1:
                fail(f"DoH query failed for {name} {rtype} via {url_base}: {exc}")
            print(f"NOTE: {url_base} failed ({exc}); trying fallback resolver.")
            continue
        if not isinstance(payload, dict):
            last_error = RuntimeError("DoH response is not an object")
            continue
        return payload
    fail(f"DoH query failed for {name} {rtype}: {last_error}")
    raise AssertionError("unreachable")


def _https_answers(payload: dict) -> list[str]:
    answers = payload.get("Answer") or []
    rdata = []
    for answer in answers:
        if not isinstance(answer, dict):
            continue
        if answer.get("type") not in {HTTPS_TYPE, "HTTPS", 65}:
            continue
        data = answer.get("data")
        if isinstance(data, str) and data.strip():
            rdata.append(data.strip())
    return rdata


def _priority(rdata: str) -> int:
    token = rdata.split()[0] if rdata.split() else ""
    try:
        return int(token)
    except ValueError:
        return 0


def check_live(resolver: str | None = None) -> None:
    index = doh_query(INDEX_NAME, "HTTPS", resolver)
    answers = _https_answers(index)
    if not answers:
        fail(f"DoH HTTPS lookup for {INDEX_NAME} returned no ServiceMode record")
    for rdata in answers:
        if _priority(rdata) < 1:
            fail(f"{INDEX_NAME} is AliasMode or missing priority: {rdata}")
        lower = rdata.lower()
        if "alpn" not in lower:
            fail(f"{INDEX_NAME} is missing alpn: {rdata}")
        if "port" not in lower:
            fail(f"{INDEX_NAME} is missing port: {rdata}")
    print(f"OK: live HTTPS {INDEX_NAME} -> {answers[0]}")

    a2a = doh_query(A2A_NAME, "HTTPS", resolver)
    a2a_answers = _https_answers(a2a)
    if not a2a_answers:
        fail(f"DoH HTTPS lookup for {A2A_NAME} returned no ServiceMode record")
    if _priority(a2a_answers[0]) < 1:
        fail(f"{A2A_NAME} is AliasMode: {a2a_answers[0]}")
    print(f"OK: live HTTPS {A2A_NAME} -> {a2a_answers[0]}")

    ds = doh_query(ZONE, "DS", resolver)
    ds_answers = [
        item.get("data")
        for item in (ds.get("Answer") or [])
        if isinstance(item, dict) and item.get("type") in {DS_TYPE, "DS", 43}
    ]
    has_rrsig = any(
        isinstance(item, dict) and item.get("type") in {46, "RRSIG"}
        for item in (index.get("Answer") or [])
    )
    if not has_rrsig:
        fail(f"HTTPS answer for {INDEX_NAME} has no RRSIG; the discovery zone is not DNSSEC-signed")
    if not ds_answers:
        fail(
            f"no DS record for {ZONE} at the parent yet. Cloudflare has signed the zone "
            "(RRSIG is present) and published CDS/CDNSKEY; Cloudflare Registrar submits DS "
            "within 1-2 days. Re-run --live after DS appears so validating resolvers set AD."
        )
    if not index.get("AD"):
        fail(
            f"HTTPS answer for {INDEX_NAME} is not DNSSEC-authenticated "
            f"(AD={index.get('AD')!r}); wait for DS propagation"
        )
    print(f"OK: DNSSEC DS is published for {ZONE} and the HTTPS answer is authenticated.")


def main() -> None:
    check_records_spec()
    check_docs()
    if "--live" in sys.argv:
        resolver = None
        if "--doh" in sys.argv:
            index = sys.argv.index("--doh")
            if index + 1 >= len(sys.argv):
                fail("--doh requires a resolver URL")
            resolver = sys.argv[index + 1]
        check_live(resolver)


if __name__ == "__main__":
    main()

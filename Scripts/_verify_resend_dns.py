#!/usr/bin/env python3
"""Verify Resend sending DNS for the site domain (DKIM, SPF, MX, DMARC).

Used by the discussions worker magic-link email path. Cloudflare's DMARC
dashboard probes only common DKIM selectors; Resend uses ``resend._domainkey``,
which this script checks explicitly.

Optional live send test (requires RESEND_API_KEY):

  $env:RESEND_API_KEY = "re_..."
  python Scripts/_verify_resend_dns.py --send-test you@example.com
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import string
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOMAIN = (REPO_ROOT / "CNAME").read_text(encoding="utf-8").strip()
DEV_VARS_PATH = REPO_ROOT / "infra" / "discussions-worker" / ".dev.vars"
SEND_SUBDOMAIN = "send"
DKIM_SELECTOR = "resend"
EXPECTED_SPF = "v=spf1 include:amazonses.com ~all"
EXPECTED_MX_HOST = "feedback-smtp.us-east-1.amazonses.com"
DEFAULT_FROM = f"Discussions <discussions@{DEFAULT_DOMAIN}>"


def _load_dev_vars() -> None:
    if not DEV_VARS_PATH.is_file():
        return
    for line in DEV_VARS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _run_dns_json(ps_command: str) -> list[dict]:
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_command],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    raw = json.loads(proc.stdout)
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def _resolve_txt(name: str) -> list[str]:
    """Return TXT record strings for *name* using PowerShell Resolve-DnsName."""
    ps = (
        f"$r = Resolve-DnsName -Type TXT -Name '{name}' -ErrorAction SilentlyContinue; "
        "if ($r) { $r | ConvertTo-Json -Compress }"
    )
    values: list[str] = []
    for row in _run_dns_json(ps):
        strings = row.get("Strings") or row.get("Text") or []
        if isinstance(strings, str):
            strings = [strings]
        for item in strings:
            text = str(item).strip()
            if text:
                values.append(text)
    return values


def _resolve_mx(name: str) -> list[tuple[int, str]]:
    ps = (
        f"$r = Resolve-DnsName -Type MX -Name '{name}' -ErrorAction SilentlyContinue; "
        "if ($r) { $r | ConvertTo-Json -Compress }"
    )
    records: list[tuple[int, str]] = []
    for row in _run_dns_json(ps):
        host = str(row.get("NameExchange", "")).rstrip(".").lower()
        if not host:
            continue
        try:
            records.append((int(row.get("Preference", 0)), host))
        except (TypeError, ValueError):
            continue
    return records


def verify_dns(domain: str) -> list[str]:
    errors: list[str] = []

    dkim_name = f"{DKIM_SELECTOR}._domainkey.{domain}"
    dkim_values = _resolve_txt(dkim_name)
    dkim_joined = "".join(dkim_values)
    if not dkim_values:
        errors.append(f"Missing DKIM TXT at {dkim_name}")
    elif not re.search(r"p=MIG[A-Za-z0-9+/=]+", dkim_joined):
        errors.append(f"DKIM TXT at {dkim_name} does not look like a Resend RSA public key")

    spf_name = f"{SEND_SUBDOMAIN}.{domain}"
    spf_values = _resolve_txt(spf_name)
    spf_norm = EXPECTED_SPF.replace(" ", "")
    if not any(spf_norm in v.replace(" ", "") for v in spf_values):
        errors.append(
            f"Missing or wrong SPF at {spf_name} (expected '{EXPECTED_SPF}')"
        )

    mx_records = _resolve_mx(spf_name)
    mx_hosts = {host for _, host in mx_records}
    if EXPECTED_MX_HOST not in mx_hosts:
        errors.append(
            f"Missing or wrong MX at {spf_name} (expected host {EXPECTED_MX_HOST})"
        )

    dmarc_name = f"_dmarc.{domain}"
    dmarc_values = _resolve_txt(dmarc_name)
    if not any(v.startswith("v=DMARC1") for v in dmarc_values):
        errors.append(f"Missing DMARC TXT at {dmarc_name}")

    return errors


def send_test_email(domain: str, to: str, api_key: str) -> None:
    from_addr = DEFAULT_FROM.replace(DEFAULT_DOMAIN, domain)
    payload = {
        "from": from_addr,
        "to": [to],
        "subject": "Resend DKIM verification test",
        "html": "<p>Automated DKIM verification test from Scripts/_verify_resend_dns.py</p>",
        "text": "Automated DKIM verification test from Scripts/_verify_resend_dns.py",
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Resend API error ({exc.code}): {detail}") from exc

    message_id = body.get("id") or body.get("messageId") or "(unknown)"
    print(f"Sent test email to {to} (Resend id: {message_id}).")
    print("Inspect headers for: DKIM-Signature s=resend; d=" + domain)
    print("  Authentication-Results: ... dkim=pass ... header.s=resend")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Resend DNS for site email.")
    parser.add_argument(
        "--domain",
        default=DEFAULT_DOMAIN,
        help=f"Apex domain (default: {DEFAULT_DOMAIN} from CNAME)",
    )
    parser.add_argument(
        "--send-test",
        metavar="EMAIL",
        help="Send a test message via Resend to this address (requires RESEND_API_KEY)",
    )
    parser.add_argument(
        "--mail-tester",
        action="store_true",
        help="Send a test message to mail-tester.com and poll for dkim=pass (requires RESEND_API_KEY)",
    )
    args = parser.parse_args()
    _load_dev_vars()
    domain = args.domain.strip().lower()

    errors = verify_dns(domain)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(f"Resend DNS verification passed for {domain}.")
    print(f"  DKIM: {DKIM_SELECTOR}._domainkey.{domain}")
    print(f"  SPF/MX: {SEND_SUBDOMAIN}.{domain}")
    print(f"  DMARC: _dmarc.{domain}")
    print(
        "Note: Cloudflare DMARC dashboard may still show DKIM Fail - it does not probe "
        f"the '{DKIM_SELECTOR}' selector."
    )


def _fetch_mail_tester_address() -> str:
    req = urllib.request.Request(
        "https://www.mail-tester.com/",
        headers={"User-Agent": "MadhyasthDarshan-DKIM-Verify/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    prefix_match = re.search(r'id="email"[^>]*data-prefix="([^"]+)"', html)
    domain_match = re.search(r'data-domain="([^"]+)"', html)
    if not prefix_match or not domain_match:
        raise RuntimeError("Could not parse mail-tester.com address template from homepage.")
    prefix = prefix_match.group(1)
    domain = domain_match.group(1)
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=9))
    return f"{prefix}-{suffix}@{domain}"


def _poll_mail_tester(token: str, timeout_s: int = 120) -> str:
    """Poll mail-tester result page until a score appears or timeout."""
    url = f"https://www.mail-tester.com/test-{token}"
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "MadhyasthDarshan-DKIM-Verify/1.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        if "dkim=pass" in html.lower() or "your dkim signature is valid" in html.lower():
            return html
        if "please wait" not in html.lower() and "score" in html.lower():
            return html
        time.sleep(5)
    raise RuntimeError(f"Timed out waiting for mail-tester result at {url}")


def run_mail_tester(domain: str, api_key: str) -> None:
    to_addr = _fetch_mail_tester_address()
    token = to_addr.split("@")[0].removeprefix("test-")
    print(f"mail-tester address: {to_addr}")
    send_test_email(domain, to_addr, api_key)
    print("Waiting for mail-tester to receive and score the message...")
    html = _poll_mail_tester(token)
    if "dkim=pass" in html.lower() or "your dkim signature is valid" in html.lower():
        print("mail-tester: dkim=pass (DKIM signature valid).")
        return
    if "dkim=fail" in html.lower():
        raise RuntimeError("mail-tester reported dkim=fail.")
    print("mail-tester result received; open the result URL to inspect headers:")
    print(f"  https://www.mail-tester.com/test-{token}")

    if args.send_test or args.mail_tester:
        api_key = os.environ.get("RESEND_API_KEY", "").strip()
        if not api_key:
            print(
                "RESEND_API_KEY is not set; skip --send-test / --mail-tester or export the key first.",
                file=sys.stderr,
            )
            return 1
        if args.mail_tester:
            run_mail_tester(domain, api_key)
        else:
            send_test_email(domain, args.send_test.strip(), api_key)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

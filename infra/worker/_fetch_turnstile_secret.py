"""Fetch Turnstile widget secret and write temp file for wrangler secret put."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"
ACCOUNT_ID = "04965e67bdd14748e755e19f40dbacbf"
SITEKEY = "0x4AAAAAADoBfrNV5lPeJQWO"


def load_token() -> str:
    if os.environ.get("CLOUDFLARE_API_TOKEN"):
        return os.environ["CLOUDFLARE_API_TOKEN"]
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("CLOUDFLARE_API_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("No token")


def main() -> None:
    token = load_token()
    request = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/challenges/widgets/{SITEKEY}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HTTP {exc.code}: {exc.read().decode()[:500]}") from exc

    if not body.get("success"):
        raise SystemExit(json.dumps(body, indent=2))

    result = body["result"]
    secret = result.get("secret")
    if not secret:
        raise SystemExit("Secret not returned; token may lack Account.Turnstile:Read")

    secret_path = Path(__file__).resolve().parent / ".turnstile-secret.tmp"
    secret_path.write_text(secret, encoding="utf-8")
    print(json.dumps({
        "sitekey": SITEKEY,
        "clearance_level": result.get("clearance_level", "no_clearance"),
        "domains": result.get("domains", []),
        "secret_file": str(secret_path),
    }))


if __name__ == "__main__":
    main()

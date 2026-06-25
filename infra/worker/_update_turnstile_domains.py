"""Update Turnstile widget domains for the submission portal."""
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
DOMAINS = [
    "localhost",
    "127.0.0.1",
    "analyticmadhyasthdarshan.org",
    "www.analyticmadhyasthdarshan.org",
]


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
    payload = {
        "name": "AnalyticMadhyasthDarshan submission portal",
        "domains": DOMAINS,
        "mode": "managed",
    }
    request = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/challenges/widgets/{SITEKEY}",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HTTP {exc.code}: {exc.read().decode()[:500]}") from exc

    if not body.get("success"):
        raise SystemExit(json.dumps(body, indent=2))

    print(json.dumps({"sitekey": SITEKEY, "domains": DOMAINS}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify generated PDF delivery through workers.dev or the public site."""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import _cloudflare_performance as cf
from _common import BASE, configure_utf8_stdio
from _generated_pdf_inventory import generated_pdf_specs
from _publish_generated_pdf_worker import (
    CANARY_WORKER_NAME,
    _workers_subdomain,
    _zone_account_id,
)

REPRESENTATIVE_KEYS = (
    "Studies/Nature-Of-Time/Nature-Of-Time.pdf",
    "Studies/A-State-Dynamic-Model-Of-Coexistence/Technical-Note-MD-TOPOS-And-The-State-Dynamic-Model.pdf",
    "Studies/A-State-Dynamic-Model-Of-Coexistence/A-State-Dynamic-Model-Of-Coexistence-Madhyasth-Darshan.pdf",
    "Studies/A-State-Dynamic-Model-Of-Coexistence/A-State-Dynamic-Model-Of-Coexistence-Madhyasth-Darshan-notes.pdf",
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _request(url: str, *, method: str = "GET", headers: dict[str, str] | None = None):
    request = urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": "AMD-generated-PDF-delivery-verifier/1.0", **(headers or {})},
    )
    result = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = (
                    response.status,
                    {k.lower(): v for k, v in response.headers.items()},
                    response.read(),
                )
        except urllib.error.HTTPError as exc:
            result = (exc.code, {k.lower(): v for k, v in exc.headers.items()}, exc.read())
        if result[0] < 500 or attempt == 2:
            return result
        time.sleep(1)
    raise AssertionError("unreachable")


def _local_path(key: str, roots: list[Path]) -> Path:
    for root in roots:
        candidate = root / Path(key)
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"local artifact not found in configured roots: {key}")


def _base_url(workers_dev: bool, worker_name: str) -> str:
    if not workers_dev:
        return f"https://{cf.SITE_HOST}"
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    if not token:
        raise ValueError("CLOUDFLARE_API_TOKEN is required to resolve the workers.dev host")
    zone_id = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    account_id = _zone_account_id(token, zone_id)
    return f"https://{worker_name}.{_workers_subdomain(token, account_id)}.workers.dev"


def verify_artifact(
    base_url: str,
    key: str,
    path: Path,
    *,
    wait_for_ready: bool = False,
) -> list[str]:
    errors: list[str] = []
    url = base_url.rstrip("/") + "/" + urllib.parse.quote(key, safe="/")
    expected_size = path.stat().st_size
    expected_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open("rb") as handle:
        expected_prefix = handle.read(16)

    status, headers, body = _request(url, method="HEAD")
    if wait_for_ready:
        for _attempt in range(9):
            if status != 404 or headers.get("x-amd-pdf-origin") == "r2":
                break
            time.sleep(2)
            status, headers, body = _request(url, method="HEAD")
    if status != 200:
        errors.append(f"HEAD {key}: expected 200, got {status}")
        return errors
    checks = {
        "content-type": "application/pdf",
        "x-amd-pdf-origin": "r2",
        "x-amd-pdf-sha256": expected_sha,
        "accept-ranges": "bytes",
        "content-length": str(expected_size),
    }
    for name, expected in checks.items():
        if headers.get(name) != expected:
            errors.append(f"HEAD {key}: {name}={headers.get(name)!r}, expected {expected!r}")
    if not headers.get("etag"):
        errors.append(f"HEAD {key}: missing ETag")
    if not headers.get("content-disposition"):
        errors.append(f"HEAD {key}: missing Content-Disposition")
    if body:
        errors.append(f"HEAD {key}: response unexpectedly has a body")

    status, headers, body = _request(url, headers={"Range": "bytes=0-15"})
    if status != 206:
        errors.append(f"range GET {key}: expected 206, got {status}")
    if headers.get("content-range") != f"bytes 0-15/{expected_size}":
        errors.append(f"range GET {key}: invalid Content-Range {headers.get('content-range')!r}")
    if body != expected_prefix:
        errors.append(f"range GET {key}: first 16 bytes differ from local artifact")
    return errors


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--workers-dev", action="store_true")
    target.add_argument("--public-canary", action="store_true")
    target.add_argument("--public", action="store_true")
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--all", action="store_true", help="Verify every generated PDF inventory key")
    parser.add_argument("--artifact-root", action="append", type=Path, default=[])
    parser.add_argument(
        "--worker-name",
        default=CANARY_WORKER_NAME,
        help=f"workers.dev script name (default: {CANARY_WORKER_NAME})",
    )
    args = parser.parse_args(argv)

    roots = [path.expanduser().resolve() for path in args.artifact_root] or [BASE]
    if args.all and args.artifact:
        parser.error("--all cannot be combined with --artifact")
    keys = (
        tuple(spec.key for spec in generated_pdf_specs())
        if args.all
        else tuple(args.artifact) or REPRESENTATIVE_KEYS
    )
    try:
        base_url = _base_url(args.workers_dev, args.worker_name)
        errors: list[str] = []
        for index, key in enumerate(keys):
            path = _local_path(key, roots)
            item_errors = verify_artifact(
                base_url,
                key,
                path,
                wait_for_ready=args.workers_dev and index == 0,
            )
            if item_errors:
                errors.extend(item_errors)
            else:
                print(f"OK {key}")

        unknown = base_url.rstrip("/") + "/Studies/__worker_probe__/unknown.pdf"
        status, headers, _ = _request(unknown)
        if status != 404:
            errors.append("unknown generated PDF did not return 404")
        elif not args.public_canary and headers.get("cache-control") != "no-store":
            errors.append("unknown generated PDF did not return the controlled no-store 404")

        if args.public or args.public_canary:
            status, headers, body = _request(base_url.rstrip("/") + "/Studies/index.html")
            if status != 200 or headers.get("x-amd-pdf-origin") == "r2" or not body:
                errors.append("non-PDF Studies request did not pass through to GitHub Pages")
        if errors:
            print("Generated PDF delivery verification failed:\n  - " + "\n  - ".join(errors))
            return 1
        print(f"Generated PDF delivery verified via {base_url}")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

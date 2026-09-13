"""Run safe, read-only production checks across every supported API runtime."""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

# Keep scheduled checks runnable with only the Python standard library.
# _common also imports PDF tooling, which the monitoring runner does not install.
BASE = Path(__file__).resolve().parent.parent

SITE = "https://analyticmadhyasthdarshan.org"
SUBMISSIONS = "https://api.analyticmadhyasthdarshan.org"
USER_AGENT = "AnalyticMadhyasthDarshan-api-synthetic/1.0"


@dataclass
class CheckResult:
    name: str
    ok: bool
    latency_ms: int
    request_id: str | None = None
    detail: str | None = None


def request(url: str, *, method: str = "GET", payload: object | None = None) -> tuple[int, dict, bytes, int]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
        headers["Origin"] = SITE
    started = time.monotonic()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, dict(response.headers.items()), response.read(), round((time.monotonic() - started) * 1000)
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read(), round((time.monotonic() - started) * 1000)


def header(headers: dict, name: str) -> str | None:
    return next((value for key, value in headers.items() if key.lower() == name.lower()), None)


def json_body(body: bytes) -> object:
    return json.loads(body.decode("utf-8"))


def run_check(name: str, callback) -> CheckResult:
    started = time.monotonic()
    try:
        request_id, detail = callback()
        return CheckResult(name, True, round((time.monotonic() - started) * 1000), request_id, detail)
    except Exception as error:  # each check must produce a result for the incident record
        return CheckResult(name, False, round((time.monotonic() - started) * 1000), detail=str(error)[:500])


def expect_json(url: str, *, status: int = 200, method: str = "GET", payload: object | None = None) -> tuple[dict, str | None, int]:
    actual, headers, body, latency = request(url, method=method, payload=payload)
    if actual != status:
        raise AssertionError(f"HTTP {actual}, expected {status}: {body[:200].decode('utf-8', 'replace')}")
    parsed = json_body(body)
    if not isinstance(parsed, dict):
        raise AssertionError("response is not a JSON object")
    return parsed, header(headers, "X-Request-ID"), latency


def status_check(url: str, service: str):
    def check():
        payload, request_id, _ = expect_json(url)
        if payload.get("service") != service or payload.get("status") != "ok":
            raise AssertionError(f"{service} readiness is {payload.get('status')!r}: {payload.get('checks')}")
        if not request_id:
            raise AssertionError("X-Request-ID is missing")
        return request_id, None
    return check


def catalog_search():
    payload, request_id, _ = expect_json(f"{SITE}/api/studies?q=ontology")
    studies = payload.get("studies") or []
    if not any(study.get("status") != "ongoing" for study in studies):
        raise AssertionError("ontology search returned no published studies")
    if not request_id:
        raise AssertionError("X-Request-ID is missing")
    return request_id, next(study["slug"] for study in studies if study.get("status") != "ongoing")


def published_ontology_slug() -> str:
    search, _, _ = expect_json(f"{SITE}/api/studies?q=ontology")
    published = next(
        (study for study in search.get("studies") or [] if study.get("status") != "ongoing"),
        None,
    )
    if not published:
        raise AssertionError("ontology search returned no published studies")
    return published["slug"]


def study_detail():
    slug = published_ontology_slug()
    payload, request_id, _ = expect_json(f"{SITE}/api/studies/{slug}")
    if payload.get("slug") != slug or not payload.get("outline"):
        raise AssertionError("study detail is incomplete")
    if not request_id:
        raise AssertionError("X-Request-ID is missing")
    return request_id, slug


def citation():
    slug = published_ontology_slug()
    payload, request_id, _ = expect_json(f"{SITE}/api/cite/{slug}")
    if payload.get("slug") != slug or not payload.get("citation"):
        raise AssertionError("citation response is incomplete")
    if not request_id:
        raise AssertionError("X-Request-ID is missing")
    return request_id, slug


def mcp(method: str):
    def check():
        params = {} if method != "initialize" else {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "api-synthetic", "version": "1.0"},
        }
        payload, request_id, _ = expect_json(f"{SITE}/mcp", method="POST", payload={
            "jsonrpc": "2.0", "id": 1, "method": method, "params": params,
        })
        if payload.get("jsonrpc") != "2.0" or "result" not in payload:
            raise AssertionError(f"invalid MCP {method} response")
        if not request_id:
            raise AssertionError("X-Request-ID is missing")
        return request_id, method
    return check


def auth_rejection(url: str, *, method: str = "GET"):
    def check():
        payload, request_id, _ = expect_json(
            url,
            status=401,
            method=method,
            payload={} if method == "POST" else None,
        )
        if payload.get("code") != "authentication_required" or payload.get("requestId") != request_id:
            raise AssertionError("authentication error envelope/request ID mismatch")
        return request_id, None
    return check


def discovery_equality():
    paths = [
        ".well-known/api-catalog",
        "openapi/studies.json",
        "openapi/submissions.json",
        "openapi/discussions.json",
    ]
    for path in paths:
        status, _headers, body, _ = request(f"{SITE}/{path}")
        if status != 200:
            raise AssertionError(f"{path} returned HTTP {status}")
        expected = (BASE / path).read_bytes()
        if json.loads(body) != json.loads(expected):
            raise AssertionError(f"{path} differs from the checked-out canonical file")
    return None, f"{len(paths)} canonical documents"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, help="write the complete machine-readable result")
    args = parser.parse_args(argv)
    checks = [
        ("status.studies", status_check(f"{SITE}/api/studies/health", "studies")),
        ("status.submissions", status_check(f"{SUBMISSIONS}/api/health", "submissions")),
        ("status.discussions", status_check(f"{SITE}/api/discussions/health", "discussions")),
        ("studies.search", catalog_search),
        ("studies.detail", study_detail),
        ("studies.citation", citation),
        ("mcp.initialize", mcp("initialize")),
        ("mcp.tools.list", mcp("tools/list")),
        ("auth.submissions.reject", auth_rejection(f"{SUBMISSIONS}/api/me/submissions")),
        ("auth.discussions.reject", auth_rejection(
            f"{SITE}/api/discussions/synthetic/comments", method="POST",
        )),
        ("discovery.equality", discovery_equality),
    ]
    results = [run_check(name, callback) for name, callback in checks]
    report = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "success": all(result.ok for result in results),
        "checks": [asdict(result) for result in results],
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

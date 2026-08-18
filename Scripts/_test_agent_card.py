"""Validate the A2A Agent Card document.

Run from the repository root:

    python Scripts/_test_agent_card.py
    python Scripts/_test_agent_card.py --live
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE
from _cloudflare_performance import AGENT_CARD_CONTENT_TYPE, HOMEPAGE_LINK

SITE = "https://analyticmadhyasthdarshan.org"
CARD_PATH = BASE / ".well-known" / "agent-card.json"
REQUIRED_FIELDS = (
    "name",
    "description",
    "version",
    "supportedInterfaces",
    "capabilities",
    "defaultInputModes",
    "defaultOutputModes",
    "skills",
)
INTERFACE_FIELDS = ("url", "protocolBinding", "protocolVersion")
SKILL_FIELDS = ("id", "name", "description", "tags")
KNOWN_BINDINGS = ("JSONRPC", "GRPC", "HTTP+JSON")
LIVE_UA = "AnalyticMadhyasthDarshan-agent-card-test/1.0"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_card() -> dict:
    if not CARD_PATH.is_file():
        fail("missing .well-known/agent-card.json")
    data = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("agent-card.json must be a JSON object")
    return data


def check_card(card: dict) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in card]
    if missing:
        fail(f"agent card is missing {missing}")
    if not card.get("name") or not card.get("description") or not card.get("version"):
        fail("name, description, and version must be non-empty")
    interfaces = card.get("supportedInterfaces")
    if not isinstance(interfaces, list) or not interfaces:
        fail("supportedInterfaces must be a non-empty array")
    for interface in interfaces:
        if not isinstance(interface, dict):
            fail("each supportedInterfaces entry must be an object")
        missing_iface = [field for field in INTERFACE_FIELDS if not interface.get(field)]
        if missing_iface:
            fail(f"supportedInterfaces entry is missing {missing_iface}")
        if not str(interface["url"]).startswith("https://"):
            fail(f"interface url must be https: {interface['url']!r}")
        if interface["protocolBinding"] not in KNOWN_BINDINGS:
            fail(f"unknown protocolBinding {interface['protocolBinding']!r}")
    capabilities = card.get("capabilities")
    if not isinstance(capabilities, dict):
        fail("capabilities must be an object")
    skills = card.get("skills")
    if not isinstance(skills, list) or not skills:
        fail("skills must be a non-empty array")
    for skill in skills:
        if not isinstance(skill, dict):
            fail("each skill must be an object")
        missing_skill = [field for field in SKILL_FIELDS if not skill.get(field)]
        if missing_skill:
            fail(f"skill {skill.get('id')!r} is missing {missing_skill}")
        tags = skill.get("tags")
        if not isinstance(tags, list) or not tags:
            fail(f"skill {skill.get('id')!r} tags must be a non-empty array")
    print("OK: A2A Agent Card has name, version, interfaces, capabilities, and skills.")


def check_homepage_link() -> None:
    if "/.well-known/agent-card.json" not in HOMEPAGE_LINK:
        fail("HOMEPAGE_LINK does not advertise /.well-known/agent-card.json")
    print("OK: homepage Link header advertises the Agent Card.")


def check_live() -> None:
    url = f"{SITE}/.well-known/agent-card.json"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": LIVE_UA, "Accept": "application/a2a+json, application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            content_type = response.headers.get("Content-Type") or ""
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        fail(f"live Agent Card returned HTTP {exc.code}")
    except urllib.error.URLError as exc:
        fail(f"live Agent Card request failed: {exc}")
    if status != 200:
        fail(f"live Agent Card returned HTTP {status}")
    if "json" not in content_type.lower():
        fail(f"live Agent Card Content-Type is {content_type!r}")
    if AGENT_CARD_CONTENT_TYPE.split(";")[0] not in content_type and "application/json" not in content_type:
        fail(f"live Agent Card Content-Type is {content_type!r}")
    payload = json.loads(body)
    check_card(payload)
    repo = load_card()
    if payload.get("version") != repo.get("version"):
        fail(
            f"live Agent Card version is {payload.get('version')!r}, "
            f"git has {repo.get('version')!r}"
        )
    live_urls = {
        interface.get("url")
        for interface in payload.get("supportedInterfaces") or []
        if interface.get("url")
    }
    repo_urls = {
        interface.get("url")
        for interface in repo.get("supportedInterfaces") or []
        if interface.get("url")
    }
    missing_urls = sorted(repo_urls - live_urls)
    if missing_urls:
        fail(f"live Agent Card is missing interfaces: {missing_urls}")
    print("OK: live /.well-known/agent-card.json is A2A Agent Card JSON.")
    first_url = payload["supportedInterfaces"][0]["url"]
    iface_request = urllib.request.Request(
        first_url,
        headers={"User-Agent": LIVE_UA, "Accept": "application/json, application/linkset+json"},
    )
    try:
        with urllib.request.urlopen(iface_request, timeout=20) as response:
            iface_status = response.status
    except urllib.error.HTTPError as exc:
        fail(f"supportedInterfaces[0].url returned HTTP {exc.code}")
    except urllib.error.URLError as exc:
        fail(f"supportedInterfaces[0].url request failed: {exc}")
    if iface_status != 200:
        fail(f"supportedInterfaces[0].url returned HTTP {iface_status}")
    print("OK: preferred supportedInterfaces URL returns HTTP 200.")


def main() -> None:
    check_card(load_card())
    check_homepage_link()
    if "--live" in sys.argv:
        check_live()


if __name__ == "__main__":
    main()

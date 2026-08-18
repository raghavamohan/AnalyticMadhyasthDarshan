"""Validate the Agent Skills Discovery index (RFC v0.2.0).

Run from the repository root:

    python Scripts/_test_agent_skills.py
    python Scripts/_test_agent_skills.py --live
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _build_agent_skills_index import (
    INDEX_PATH,
    INDEX_SITE_PATH,
    NAME_RE,
    PUBLISH_ROOT,
    SCHEMA_URI,
    check_publish_files,
    expected_publish_files,
    sha256_digest,
)
from _cloudflare_performance import HOMEPAGE_LINK

SITE = "https://analyticmadhyasthdarshan.org"
DIGEST_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
SKILL_FIELDS = ("name", "type", "description", "url", "digest")
LIVE_UA = "AnalyticMadhyasthDarshan-agent-skills-test/1.0"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load_index() -> dict:
    if not INDEX_PATH.is_file():
        fail("missing .well-known/agent-skills/index.json")
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("index.json must be a JSON object")
    return data


def artifact_path(url: str) -> Path | None:
    prefix = "/.well-known/agent-skills/"
    if url.startswith(prefix) and url.endswith("/SKILL.md"):
        return PUBLISH_ROOT / url[len(prefix) :]
    site_prefix = f"{SITE}/.well-known/agent-skills/"
    if url.startswith(site_prefix) and url.endswith("/SKILL.md"):
        return PUBLISH_ROOT / url[len(site_prefix) :]
    return None


def check_index(index: dict) -> None:
    if index.get("$schema") != SCHEMA_URI:
        fail(f"$schema is {index.get('$schema')!r}")
    skills = index.get("skills")
    if not isinstance(skills, list) or not skills:
        fail("skills must be a non-empty array")
    names: list[str] = []
    for skill in skills:
        if not isinstance(skill, dict):
            fail("each skill must be an object")
        missing = [field for field in SKILL_FIELDS if not skill.get(field)]
        if missing:
            fail(f"skill {skill.get('name')!r} is missing {missing}")
        name = skill["name"]
        if not NAME_RE.fullmatch(name) or not 1 <= len(name) <= 64:
            fail(f"skill name {name!r} is not a valid skill identifier")
        if skill["type"] not in {"skill-md", "archive"}:
            fail(f"skill {name!r} has unknown type {skill['type']!r}")
        if len(skill["description"]) > 1024:
            fail(f"skill {name!r} description exceeds 1024 characters")
        if not DIGEST_RE.fullmatch(skill["digest"]):
            fail(f"skill {name!r} digest is not sha256:{{64 hex}}")
        url = skill["url"]
        if skill["type"] == "skill-md":
            local = artifact_path(url)
            if local is None:
                fail(f"skill {name!r} url must point at a published SKILL.md")
            if not local.is_file():
                fail(f"skill {name!r} artifact is missing: {local}")
            body = local.read_bytes()
            digest = "sha256:" + hashlib.sha256(body).hexdigest()
            if digest != skill["digest"]:
                fail(f"skill {name!r} digest does not match {local}")
            if sha256_digest(body) != skill["digest"]:
                fail(f"skill {name!r} digest helper mismatch")
        names.append(name)
    if len(names) != len(set(names)):
        fail("skill names must be unique")
    if names != sorted(names):
        fail("skills array must be sorted by name")
    print("OK: Agent Skills Discovery index has $schema, skills, urls, and digests.")


def check_published_copies() -> None:
    errors = check_publish_files(expected_publish_files())
    if errors:
        fail("; ".join(errors))
    print("OK: published SKILL.md copies match .agents/skills.")


def check_homepage_link() -> None:
    if INDEX_SITE_PATH not in HOMEPAGE_LINK:
        fail("HOMEPAGE_LINK does not advertise /.well-known/agent-skills/index.json")
    print("OK: homepage Link header advertises the Agent Skills index.")


def fetch(url: str, accept: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": LIVE_UA, "Accept": accept},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.headers.get("Content-Type") or "", response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read()
        content_type = (exc.headers.get("Content-Type") if exc.headers else "") or ""
        return exc.code, content_type, body
    except urllib.error.URLError as exc:
        fail(f"{url} request failed: {exc}")


def check_live() -> None:
    url = f"{SITE}{INDEX_SITE_PATH}"
    status, content_type, body = fetch(url, "application/json")
    if status != 200:
        fail(f"live Agent Skills index returned HTTP {status}")
    if "json" not in content_type.lower():
        fail(f"live Agent Skills index Content-Type is {content_type!r}")
    payload = json.loads(body.decode("utf-8"))
    check_index(payload)
    print("OK: live /.well-known/agent-skills/index.json is discovery JSON.")
    for skill in payload["skills"]:
        skill_url = skill["url"]
        if skill_url.startswith("/"):
            skill_url = f"{SITE}{skill_url}"
        skill_status, skill_type, skill_body = fetch(
            skill_url, "text/markdown, text/plain, */*"
        )
        if skill_status != 200:
            fail(f"skill {skill['name']!r} returned HTTP {skill_status} at {skill_url}")
        if skill["type"] == "skill-md":
            if "markdown" not in skill_type.lower() and "text/plain" not in skill_type.lower():
                fail(
                    f"skill {skill['name']!r} Content-Type is {skill_type!r}"
                )
        digest = "sha256:" + hashlib.sha256(skill_body).hexdigest()
        if digest != skill["digest"]:
            fail(f"live digest mismatch for skill {skill['name']!r}")
    print("OK: live skill artifacts match advertised digests.")


def main() -> None:
    check_published_copies()
    check_index(load_index())
    check_homepage_link()
    if "--live" in sys.argv:
        check_live()


if __name__ == "__main__":
    main()

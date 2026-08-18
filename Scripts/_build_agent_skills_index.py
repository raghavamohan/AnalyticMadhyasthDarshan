#!/usr/bin/env python3
"""Publish Agent Skills Discovery index and SKILL.md copies.

Canonical maintainer skills live in `.agents/skills/<name>/SKILL.md`.
Reader skills for catalog agents live in `infra/reader-skills/<name>/SKILL.md`
and are not copied into `.cursor/skills/`. This writes:

  .well-known/agent-skills/index.json
  .well-known/agent-skills/<name>/SKILL.md

per the Agent Skills Discovery RFC v0.2.0
(https://github.com/cloudflare/agent-skills-discovery-rfc).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE  # noqa: E402

SCHEMA_URI = "https://schemas.agentskills.io/discovery/0.2.0/schema.json"
SKILLS_SOURCE = BASE / ".agents" / "skills"
READER_SKILLS_SOURCE = BASE / "infra" / "reader-skills"
SKILLS_SOURCE_DIRS = (SKILLS_SOURCE, READER_SKILLS_SOURCE)
PUBLISH_ROOT = BASE / ".well-known" / "agent-skills"
INDEX_PATH = PUBLISH_ROOT / "index.json"
INDEX_SITE_PATH = "/.well-known/agent-skills/index.json"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)
BLOCK_INDICATORS = {">", ">-", "|", "|-"}


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(normalize_text(text))
    if not match:
        raise ValueError("missing YAML frontmatter delimited by ---")
    lines = match.group(1).split("\n")
    fields: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if ":" not in line or line.startswith(" ") or line.startswith("\t"):
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest in BLOCK_INDICATORS:
            block: list[str] = []
            index += 1
            while index < len(lines):
                continuation = lines[index]
                if continuation and not continuation[0].isspace():
                    break
                block.append(continuation)
                index += 1
            stripped = [item.strip() for item in block]
            while stripped and not stripped[0]:
                stripped.pop(0)
            while stripped and not stripped[-1]:
                stripped.pop()
            if rest.startswith(">"):
                fields[key] = " ".join(item for item in stripped if item)
            else:
                fields[key] = "\n".join(stripped)
            continue
        if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in {"'", '"'}:
            rest = rest[1:-1]
        fields[key] = rest
        index += 1
    return fields


def sha256_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def validate_name(name: str) -> None:
    if not 1 <= len(name) <= 64:
        raise ValueError(f"skill name {name!r} must be 1-64 characters")
    if not NAME_RE.fullmatch(name):
        raise ValueError(
            f"skill name {name!r} must be lowercase alphanumeric with single hyphens"
        )


def validate_description(description: str) -> None:
    if not description or not description.strip():
        raise ValueError("skill description must be non-empty")
    if len(description) > 1024:
        raise ValueError("skill description exceeds 1024 characters")


def iter_source_skills() -> list[Path]:
    skills: list[Path] = []
    seen: set[str] = set()
    for source in SKILLS_SOURCE_DIRS:
        if not source.is_dir():
            continue
        for skill_dir in sorted(source.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            name = skill_dir.name
            if name in seen:
                raise SystemExit(
                    f"Duplicate skill name {name!r} under {source} and an earlier source"
                )
            seen.add(name)
            skills.append(skill_file)
    if not skills:
        raise SystemExit(
            "No SKILL.md files under " + ", ".join(str(path) for path in SKILLS_SOURCE_DIRS)
        )
    return skills


def collect_skills() -> tuple[list[dict[str, str]], dict[str, str]]:
    entries: list[dict[str, str]] = []
    artifacts: dict[str, str] = {}
    for skill_file in iter_source_skills():
        text = normalize_text(skill_file.read_text(encoding="utf-8"))
        if not text.endswith("\n"):
            text += "\n"
        fields = parse_frontmatter(text)
        name = fields.get("name") or skill_file.parent.name
        description = fields.get("description") or ""
        validate_name(name)
        validate_description(description)
        if name != skill_file.parent.name:
            raise ValueError(
                f"{skill_file.relative_to(BASE)} frontmatter name {name!r} "
                f"does not match directory {skill_file.parent.name!r}"
            )
        relative_url = f"/.well-known/agent-skills/{name}/SKILL.md"
        entries.append(
            {
                "name": name,
                "type": "skill-md",
                "description": description,
                "url": relative_url,
                "digest": sha256_digest(text.encode("utf-8")),
            }
        )
        artifacts[name] = text
    entries.sort(key=lambda item: item["name"])
    return entries, artifacts


def render_index(entries: list[dict[str, str]]) -> str:
    payload = {"$schema": SCHEMA_URI, "skills": entries}
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def expected_publish_files() -> dict[Path, str]:
    entries, artifacts = collect_skills()
    files = {INDEX_PATH: render_index(entries)}
    for name, text in artifacts.items():
        files[PUBLISH_ROOT / name / "SKILL.md"] = text
    return files


def write_publish_files(files: dict[Path, str]) -> list[str]:
    PUBLISH_ROOT.mkdir(parents=True, exist_ok=True)
    expected_paths = set(files)
    for extra in PUBLISH_ROOT.rglob("*"):
        if extra.is_dir():
            continue
        if extra not in expected_paths:
            extra.unlink()
    written: list[str] = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        written.append(str(path.relative_to(BASE)))
    for directory in sorted(PUBLISH_ROOT.rglob("*"), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    return written


def check_publish_files(files: dict[Path, str] | None = None) -> list[str]:
    expected = files if files is not None else expected_publish_files()
    errors: list[str] = []
    for path, content in expected.items():
        relative = path.relative_to(BASE)
        if not path.is_file():
            errors.append(f"missing {relative}")
            continue
        actual = normalize_text(path.read_text(encoding="utf-8"))
        if actual != content:
            errors.append(f"stale {relative} (run _build_agent_skills_index.py)")
    for extra in PUBLISH_ROOT.rglob("SKILL.md") if PUBLISH_ROOT.is_dir() else []:
        name = extra.parent.name
        if (PUBLISH_ROOT / name / "SKILL.md") not in expected:
            errors.append(f"orphan {extra.relative_to(BASE)}")
    if INDEX_PATH.is_file() and INDEX_PATH not in expected:
        errors.append(f"orphan {INDEX_PATH.relative_to(BASE)}")
    return errors


def publish() -> list[str]:
    return write_publish_files(expected_publish_files())


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Agent Skills Discovery index.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify published files match .agents/skills without writing.",
    )
    args = parser.parse_args()
    if args.check:
        errors = check_publish_files()
        if errors:
            print("Agent skills discovery files are out of sync:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            print("Run: python Scripts/_build_agent_skills_index.py", file=sys.stderr)
            return 1
        print("OK: Agent Skills Discovery index matches .agents/skills")
        return 0

    written = publish()
    print("Published Agent Skills Discovery files:")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

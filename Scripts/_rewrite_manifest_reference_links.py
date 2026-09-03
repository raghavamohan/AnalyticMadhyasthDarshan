#!/usr/bin/env python3
"""Rewrite Markdown links for migrated references to their delivery URLs."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

from _common import APPLICATIONS, BASE, REFERENCES, STUDIES, configure_utf8_stdio, write_text_lf
from _reference_artifacts import load_manifest

LINK_RE = re.compile(r"(?P<prefix>\]\()(?P<href>[^)\s]+)(?P<suffix>[^)]*\))")


def delivery_map() -> dict[str, str]:
    data = load_manifest()
    by_path = {row["repo_path"]: row for row in data["artifacts"]}
    result: dict[str, str] = {}
    for row in data["artifacts"]:
        target = row.get("target") or {}
        storage = target.get("storage")
        url = target.get("public_url")
        delivery_path = (row.get("delivery") or {}).get("artifact_repo_path")
        if delivery_path:
            delivered = by_path.get(delivery_path) or {}
            delivered_target = delivered.get("target") or {}
            storage = delivered_target.get("storage")
            url = delivered_target.get("public_url")
        if storage not in {"r2-public", "external-only-rights-review"} or not url:
            continue
        result[row["repo_path"]] = str(url)
        if PurePosixPath(row["repo_path"]).suffix.lower() == ".pdf":
            result[str(PurePosixPath(row["repo_path"]).with_suffix(".md"))] = str(url)
    return result


def _repo_reference_path(href: str, source: Path) -> tuple[str, str] | None:
    parsed = urlsplit(unquote(href))
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    if parsed.scheme in {"http", "https"}:
        path = parsed.path.lstrip("/")
        return (path, fragment) if path.startswith("References/") else None
    clean = parsed.path.replace("\\", "/")
    marker = "References/"
    index = clean.find(marker)
    if index >= 0:
        return clean[index:], fragment
    if source.parent == REFERENCES and not clean.startswith(("/", "#")):
        normalized = str(PurePosixPath("References") / PurePosixPath(clean))
        return normalized, fragment
    return None


def rewrite_text(text: str, mapping: dict[str, str], source: Path) -> tuple[str, int]:
    changed = 0
    in_fence = False
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            output.append(line)
            continue
        if in_fence:
            output.append(line)
            continue

        def replace(match: re.Match[str]) -> str:
            nonlocal changed
            target = _repo_reference_path(match.group("href"), source)
            if target is None:
                return match.group(0)
            repo_path, fragment = target
            if (
                source.parent == REFERENCES
                and PurePosixPath(repo_path).suffix.lower() == ".md"
                and (BASE / repo_path).is_file()
            ):
                return match.group(0)
            url = mapping.get(repo_path)
            if not url:
                return match.group(0)
            replacement = (
                f"{match.group('prefix')}{url}{fragment}{match.group('suffix')}"
            )
            if replacement == match.group(0):
                return match.group(0)
            changed += 1
            return replacement

        output.append(LINK_RE.sub(replace, line))
    return "".join(output), changed


def markdown_paths() -> list[Path]:
    paths = list(STUDIES.glob("*/*.md")) + list(APPLICATIONS.glob("*/*.md"))
    paths.extend([REFERENCES / "README.md", REFERENCES / "MANIFEST.md"])
    return sorted(
        path
        for path in paths
        if path.is_file() and not _is_pre_catalog_placeholder(path)
    )


def _is_pre_catalog_placeholder(path: Path) -> bool:
    if path.parent.parent not in {STUDIES, APPLICATIONS}:
        return False
    if path.stem != path.parent.name:
        return False
    return "**Status:**" not in path.read_text(encoding="utf-8")


def run(*, write: bool) -> tuple[int, list[Path]]:
    mapping = delivery_map()
    count = 0
    changed_paths: list[Path] = []
    for path in markdown_paths():
        original = path.read_text(encoding="utf-8")
        updated, replacements = rewrite_text(original, mapping, path)
        if not replacements:
            continue
        changed_paths.append(path)
        count += replacements
        if write:
            write_text_lf(path, updated)
    action = "Rewrote" if write else "Would rewrite"
    print(f"{action} {count} migrated reference link(s) in {len(changed_paths)} file(s).")
    for path in changed_paths:
        print(path.relative_to(BASE).as_posix())
    return count, changed_paths


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        count, _ = run(write=args.write)
        if args.check and count:
            print("Migrated reference links still require rewriting.", file=sys.stderr)
            return 1
        return 0
    except (OSError, ValueError) as exc:
        print(f"Reference link rewrite failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Verify SVG figures referenced from study markdown.

Invalid UTF-8 in an SVG (for example Windows-1252 section signs in a UTF-8 file)
breaks XML parsing and Chromium rendering in the PDF pipeline.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from _common import iter_study_md_paths

FIGURE_REF = re.compile(r"!\[[^\]]*\]\(([^)]+)\)", re.MULTILINE)


def find_svg_refs(md_text: str, md_dir: Path) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for match in FIGURE_REF.finditer(md_text):
        ref = match.group(1).strip()
        if ref.startswith(("http://", "https://", "data:")):
            continue
        candidate = (md_dir / ref.split("#")[0]).resolve()
        if candidate.suffix.lower() != ".svg":
            continue
        if candidate not in seen:
            seen.add(candidate)
            paths.append(candidate)
    return paths


def verify_svg_file(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"{path}: file missing"]

    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        hint = (
            "Use numeric XML entities in SVG text "
            "(§ → &#167;, · → &#183;, — → &#8212;) and save as UTF-8."
        )
        return [f"{path}: not valid UTF-8 ({exc}). {hint}"]

    if "\ufffd" in text:
        errors.append(f"{path}: contains U+FFFD replacement characters")

    try:
        ET.fromstring(text)
    except ET.ParseError as exc:
        errors.append(f"{path}: malformed SVG/XML ({exc})")

    return errors


def verify_study_svgs(md_path: Path) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    svgs = find_svg_refs(md_text, md_path.parent)
    errors: list[str] = []
    for svg in svgs:
        errors.extend(verify_svg_file(svg))
    if errors:
        joined = "\n".join(f"  - {err}" for err in errors)
        raise SystemExit(f"Study SVG figure check failed for {md_path.name}:\n{joined}")


def verify_all_study_svgs() -> list[str]:
    errors: list[str] = []
    for md_path in sorted(iter_study_md_paths()):
        if md_path.name == "README.md":
            continue
        for svg in find_svg_refs(md_path.read_text(encoding="utf-8"), md_path.parent):
            errors.extend(verify_svg_file(svg))
    return errors


def main() -> None:
    if len(sys.argv) == 2:
        md_path = Path(sys.argv[1]).resolve()
        verify_study_svgs(md_path)
        print(f"OK: SVG figure check passed for {md_path.name}")
        return

    if len(sys.argv) != 1:
        raise SystemExit("Usage: python Scripts/_verify_study_svgs.py [<study.md>]")

    errors = verify_all_study_svgs()
    if errors:
        joined = "\n".join(f"  - {err}" for err in errors)
        raise SystemExit(f"Study SVG figure check failed:\n{joined}")
    print("OK: all study SVG figures passed validation")


if __name__ == "__main__":
    main()

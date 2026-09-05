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

    # Figures must remain static even when their public URL is opened directly.
    # Reject active SVG, foreign namespaces, and external CSS/resource loading.
    allowed_tags = {
        "svg", "g", "defs", "title", "desc", "style", "path", "rect", "circle",
        "ellipse", "line", "polyline", "polygon", "text", "tspan", "textPath",
        "marker", "clipPath", "mask", "pattern", "linearGradient", "radialGradient",
        "stop", "use", "symbol", "filter", "feDropShadow", "feGaussianBlur",
        "feOffset", "feMerge", "feMergeNode", "feBlend", "feColorMatrix",
        "feComposite", "feFlood",
    }
    def unsafe_css(value: str) -> bool:
        value = re.sub(r"/\*.*?\*/", "", value, flags=re.S)
        if "\\" in value or re.search(r"@import|expression\s*\(|-moz-binding", value, re.I):
            return True
        return any(not url.strip(" \t\r\n\"'").startswith("#")
                   for url in re.findall(r"url\s*\((.*?)\)", value, re.I | re.S))

    if re.search(r"<!DOCTYPE|<!ENTITY|<\?xml-stylesheet", text, re.I):
        errors.append(f"{path}: SVG declarations or external stylesheets are not allowed")
    try:
        root = ET.fromstring(text)
        if root.tag not in ("svg", "{http://www.w3.org/2000/svg}svg"):
            errors.append(f"{path}: root must be an SVG element")
        for element in root.iter():
            tag = element.tag.rsplit("}", 1)[-1]
            if tag not in allowed_tags or (element.tag.startswith("{") and not element.tag.startswith("{http://www.w3.org/2000/svg}")):
                errors.append(f"{path}: active or unsupported SVG element {tag}")
            for key, value in element.attrib.items():
                attr = key.rsplit("}", 1)[-1].lower()
                if attr.startswith("on") or attr in {"base", "src"}:
                    errors.append(f"{path}: unsafe SVG attribute {attr}")
                if attr == "href" and not value.strip().startswith("#"):
                    errors.append(f"{path}: SVG references must be local fragments")
                if unsafe_css(value):
                    errors.append(f"{path}: external or executable SVG style")
            if tag == "style" and unsafe_css("".join(element.itertext())):
                errors.append(f"{path}: external or executable SVG stylesheet")
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

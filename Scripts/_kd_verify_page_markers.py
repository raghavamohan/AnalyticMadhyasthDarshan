"""Verify [p. N] page markers in KD English markdown."""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from _common import BASE

DEFAULT_MD = (
    BASE
    / "References"
    / "Madhyasth-Darshan"
    / "KD-Karm-Darshan-English"
    / "KD-Karm-Darshan-English.md"
)

MARKER_RE = re.compile(r"^\[(?:blank )?p\.\s*(\d+)\]", re.IGNORECASE | re.MULTILINE)

SECTION_RE = re.compile(r"^## 3\.(\d+)", re.MULTILINE)

SUB_TOC_PAGES = {
    "3.1": 53,
    "3.2": 57,
    "3.3": 59,
    "3.4": 63,
    "3.5": 68,
    "3.6": 69,
    "3.7": 72,
    "3.8": 83,
    "3.9": 87,
    "3.10": 99,
    "3.11": 101,
    "3.12": 109,
    "3.13": 117,
    "3.14": 124,
    "3.15": 133,
    "3.16": 135,
    "3.17": 145,
    "3.18": 150,
}


def verify_markers(text: str) -> int:
    markers = [int(m.group(1)) for m in MARKER_RE.finditer(text)]
    if not markers:
        print("ERROR: no page markers found")
        return 1

    counts = Counter(markers)
    blanks = len(re.findall(r"^\[blank p\.", text, re.MULTILINE | re.IGNORECASE))
    print(f"Total markers: {len(markers)} ({blanks} blank)")
    print(f"Range: {min(markers)} – {max(markers)}")

    missing = [p for p in range(1, 154) if p not in counts and p not in {50}]
    if missing:
        print(f"Missing printed pages (no marker): {missing[:20]}{'...' if len(missing) > 20 else ''}")

    duplicates = {p: c for p, c in counts.items() if c > 1}
    if duplicates:
        print(f"Duplicate markers (expected in front matter restart): {len(duplicates)} pages")

    # Section boundary report
    lines = text.splitlines()
    section_markers: dict[str, int | None] = {}
    last_marker: int | None = None
    for line in lines:
        m = MARKER_RE.match(line)
        if m:
            last_marker = int(m.group(1))
        sec = SECTION_RE.match(line)
        if sec:
            section_markers[f"3.{sec.group(1)}"] = last_marker

    print("\nSection vs sub-TOC start pages:")
    mismatches = 0
    for sec, expected in SUB_TOC_PAGES.items():
        actual = section_markers.get(sec)
        status = "OK" if actual is not None and actual <= expected + 2 else "CHECK"
        if status == "CHECK":
            mismatches += 1
        print(f"  {sec}: marker before heading = {actual}, sub-TOC = {expected} [{status}]")

    print(f"\nEstimated distinct body pages with markers: {len(set(p for p in markers if p <= 153))}")
    print(f"Front-matter marker pages (1-25): {sorted(p for p in counts if p <= 25)}")

    if missing or mismatches > 5:
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify KD page markers.")
    parser.add_argument("--file", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    text = args.file.resolve().read_text(encoding="utf-8")
    raise SystemExit(verify_markers(text))


if __name__ == "__main__":
    main()

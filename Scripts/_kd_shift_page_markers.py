"""Shift [p. N] and [blank p. N] markers in KD English markdown by a delta."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import BASE

DEFAULT_MD = (
    BASE
    / "References"
    / "Madhyasth-Darshan"
    / "KD-Karm-Darshan-English"
    / "KD-Karm-Darshan-English.md"
)

MARKER_RE = re.compile(
    r"(\[(?:blank )?p\.\s*)(\d+)(\])",
    re.IGNORECASE,
)


def shift_markers(
    text: str,
    *,
    from_page: int,
    delta: int,
    max_page: int | None = None,
    cap_final: int | None = None,
) -> str:
    """Shift page numbers >= from_page by delta (high to low to avoid double-shift)."""
    matches = list(MARKER_RE.finditer(text))
    if not matches:
        return text

    replacements: list[tuple[int, int, str]] = []
    for match in matches:
        page = int(match.group(2))
        if page < from_page:
            continue
        if max_page is not None and page > max_page:
            continue
        new_page = page + delta
        replacements.append((match.start(), match.end(), f"{match.group(1)}{new_page}{match.group(3)}"))

    if cap_final is not None and replacements:
        last_start, last_end, last_repl = replacements[-1]
        capped = re.sub(r"(\d+)(\])$", rf"{cap_final}\2", last_repl)
        replacements[-1] = (last_start, last_end, capped)

    for start, end, repl in reversed(replacements):
        text = text[:start] + repl + text[end:]
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Shift KD page markers in English markdown.")
    parser.add_argument("--file", type=Path, default=DEFAULT_MD)
    parser.add_argument("--from", dest="from_page", type=int, required=True)
    parser.add_argument("--delta", type=int, required=True)
    parser.add_argument("--max", dest="max_page", type=int, default=None)
    parser.add_argument(
        "--cap-final",
        type=int,
        default=None,
        help="Cap the last shifted marker to this page number (e.g. 153).",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    path = args.file.resolve()
    text = path.read_text(encoding="utf-8")
    updated = shift_markers(
        text,
        from_page=args.from_page,
        delta=args.delta,
        max_page=args.max_page,
        cap_final=args.cap_final,
    )
    if updated == text:
        print("No markers changed.")
        return

    if args.dry_run:
        print(updated)
        return

    path.write_text(updated, encoding="utf-8", newline="\n")
    changed = sum(
        1
        for a, b in zip(MARKER_RE.findall(text), MARKER_RE.findall(updated), strict=False)
        if a != b
    )
    print(f"Updated {path} ({changed} marker(s) shifted)")


if __name__ == "__main__":
    main()

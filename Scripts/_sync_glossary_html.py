#!/usr/bin/env python3
"""Synchronize shared glossary tooltip markup in tracked study reader HTML."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from _common import BASE, configure_utf8_stdio, write_text_lf
from _glossary_tooltips import load_glossary, refresh_document_tooltips


def tracked_reader_html(root: Path = BASE) -> tuple[Path, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--", "Studies/**/*.html", "Applications/**/*.html"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git ls-files failed: {detail}")
    names = completed.stdout.decode("utf-8").split("\0")
    candidates = (root / name for name in names if name)
    return tuple(
        path
        for path in candidates
        if '<meta name="amd-source-version"' in path.read_text(encoding="utf-8")
    )


def stale_reader_html(root: Path = BASE, *, write: bool = False) -> tuple[Path, ...]:
    terms = load_glossary(root / "Studies" / "glossary.json")
    stale: list[Path] = []
    for path in tracked_reader_html(root):
        original = path.read_text(encoding="utf-8")
        refreshed = refresh_document_tooltips(original, terms)
        if refreshed == original:
            continue
        stale.append(path)
        if write:
            write_text_lf(path, refreshed)
    return tuple(stale)


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        stale = stale_reader_html(write=args.write)
    except (OSError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if stale and args.check:
        print("Generated study HTML has stale shared-glossary tooltips:", file=sys.stderr)
        for path in stale:
            print(f"  - {path.relative_to(BASE).as_posix()}", file=sys.stderr)
        print("Run: python Scripts/_sync_glossary_html.py --write", file=sys.stderr)
        return 1
    action = "Updated" if args.write else "Verified"
    print(f"{action} shared glossary tooltips in {len(tracked_reader_html())} tracked HTML files"
          f" ({len(stale)} changed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

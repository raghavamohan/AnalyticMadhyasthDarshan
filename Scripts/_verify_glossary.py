#!/usr/bin/env python3
"""Validate Studies/glossary.json structure."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _glossary_tooltips import GLOSSARY_PATH, validate_glossary  # noqa: E402


def main() -> int:
    issues = validate_glossary(GLOSSARY_PATH)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1
    print(f"OK: {GLOSSARY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

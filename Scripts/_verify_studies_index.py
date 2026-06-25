#!/usr/bin/env python3
"""Verify Studies catalog JSON files and landing-page shell."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _build_studies_index import verify_index_shell_sync  # noqa: E402
from _study_catalog import verify_all_catalog_sync  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Studies catalog JSON files and index.html landing-page shell.",
    )
    parser.add_argument(
        "--shell-only",
        action="store_true",
        help="Verify only the HTML/CSS/JS shell (skip catalog JSON vs README).",
    )
    parser.add_argument(
        "--catalog-only",
        action="store_true",
        help="Verify only catalog JSON vs README.md (skip shell).",
    )
    args = parser.parse_args()

    errors: list[str] = []
    if not args.shell_only:
        errors.extend(verify_all_catalog_sync())
    if not args.catalog_only:
        errors.extend(verify_index_shell_sync())

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("Studies index verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

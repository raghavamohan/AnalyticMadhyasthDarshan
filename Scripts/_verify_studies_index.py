#!/usr/bin/env python3
"""Verify Studies catalog JSON files and landing-page shell."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _build_studies_index import (  # noqa: E402
    verify_catalog_bootstrap_sync,
    verify_index_shell_sync,
)
from _build_discussion_pages import verify_discussion_pages  # noqa: E402
from _study_catalog import verify_all_catalog_sync  # noqa: E402


def collect_index_errors(*, shell: bool = True, catalog: bool = True) -> list[str]:
    """Every Studies-index check, in one place.

    Single source of truth so the PR-time gate and the master-push gate cannot
    drift apart. They did: _ci_study_pr.py ran only verify_all_catalog_sync()
    and verify_index_shell_sync(), and the latter calls strip_catalog_blocks(),
    so it structurally cannot see the inlined bootstrap. A status change that
    left Studies/index.html stale therefore passed its PR and failed only on the
    push to master, after the merge (#343). Add new checks here, not in a caller.
    """
    errors: list[str] = []
    if catalog:
        errors.extend(verify_all_catalog_sync())
    if shell:
        errors.extend(verify_index_shell_sync())
        errors.extend(verify_catalog_bootstrap_sync())
        errors.extend(verify_discussion_pages())
    return errors


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

    errors = collect_index_errors(
        shell=not args.catalog_only,
        catalog=not args.shell_only,
    )

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("Studies index verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

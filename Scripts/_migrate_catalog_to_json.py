#!/usr/bin/env python3
"""Migrate Studies/index.html catalog blocks from HTML table rows to JSON."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _common import STUDIES  # noqa: E402
from _study_catalog import (  # noqa: E402
    CATALOG_TABLES,
    StudyTable,
    parse_catalog_json,
    parse_md_rows,
    verify_all_catalog_sync,
    write_studies_catalog,
)


def main() -> int:
    index_path = STUDIES / "index.html"
    readme_path = STUDIES / "README.md"
    index_text = index_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")

    for table in CATALOG_TABLES:
        rows = parse_catalog_json(index_text, table)
        if not rows:
            print(f"No rows found for {table.value} catalog.", file=sys.stderr)
            return 1
        write_studies_catalog(rows, table)
        print(f"Migrated {len(rows)} {table.value} studies to JSON.")

    index_text = index_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")

    for table in CATALOG_TABLES:
        json_rows = parse_catalog_json(index_text, table)
        md_rows = parse_md_rows(readme_text, table)
        if [r.slug for r in json_rows] != [r.slug for r in md_rows]:
            print(f"Slug order mismatch after migration for {table.value}.", file=sys.stderr)
            return 1

    errors = verify_all_catalog_sync()
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("Catalog JSON migration verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

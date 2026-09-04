#!/usr/bin/env python3
"""Build the explicit study -> companion-note/presentation registry.

The registry is consumed by My Submissions so contributors can select an
existing companion file without recovering its name from an old issue or pull
request. Repository paths remain authoritative; this generated map makes that
inventory cheap and stable to read from the portal.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from _common import APPLICATIONS, BASE, STUDIES, write_text_lf


OUTPUT = STUDIES / "companion-artifacts.json"
CATALOGS = (
    (STUDIES / "catalog-topical.json", STUDIES, "Studies"),
    (STUDIES / "catalog-formal.json", STUDIES, "Studies"),
    (STUDIES / "catalog-applied.json", APPLICATIONS, "Applications"),
)
NOTE_NAME_RE = re.compile(r"(?:Technical|Research)-Note-[A-Za-z0-9][A-Za-z0-9-]*\.md")


def build_registry() -> dict:
    entries: dict[str, dict] = {}
    for catalog_path, root_path, root_name in CATALOGS:
        rows = json.loads(catalog_path.read_text(encoding="utf-8"))
        for row in rows:
            slug = row.get("slug")
            if not slug or str(row.get("status") or "").lower() not in {"draft", "released"}:
                continue
            directory = root_path / slug
            canonical = directory / f"{slug}.md"
            if not canonical.is_file():
                continue
            notes = sorted(
                path.name
                for path in directory.glob("*.md")
                if path.name != canonical.name and NOTE_NAME_RE.fullmatch(path.name)
            )
            presentations = sorted(
                path.name
                for path in directory.glob("*.pptx")
                if not path.name.startswith("~$")
            )
            entries[slug] = {
                "slug": slug,
                "title": row.get("title") or slug.replace("-", " "),
                "root": root_name,
                "notes": notes,
                "presentations": presentations,
            }
    return {
        "schemaVersion": 1,
        "studies": [entries[slug] for slug in sorted(entries, key=str.casefold)],
    }


def render_registry() -> str:
    return json.dumps(build_registry(), ensure_ascii=False, indent=2) + "\n"


def write_registry() -> bool:
    """Write the current registry and return whether its bytes changed."""
    return write_text_lf(OUTPUT, render_registry())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when Studies/companion-artifacts.json is missing or stale.",
    )
    args = parser.parse_args()
    rendered = render_registry()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else None
        if current != rendered:
            raise SystemExit(
                "Studies/companion-artifacts.json is stale; run "
                "python Scripts/_companion_artifacts.py"
            )
        print("Companion artifact registry verification passed.")
        return
    changed = write_registry()
    action = "Updated" if changed else "Unchanged"
    print(f"{action}: {OUTPUT.relative_to(BASE).as_posix()}")


if __name__ == "__main__":
    main()

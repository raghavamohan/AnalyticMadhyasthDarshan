"""One-time migration: Studies/<Slug>.{md,pdf,...} -> Studies/<Slug>/<Slug>.{md,pdf,...}

Also rewrites cross-study links, catalog hrefs, and References paths.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from _common import (
    REFERENCES,
    STUDIES,
    iter_study_md_paths,
    known_study_slugs,
    study_dir,
    study_md,
    study_pdf_href,
    study_pdf_ref_path,
)

CATALOG_MARKERS = (
    ("<!-- studies-catalog -->", "<!-- /studies-catalog -->"),
    ("<!-- formal-studies-catalog -->", "<!-- /formal-studies-catalog -->"),
)


def discover_flat_study_slugs() -> list[str]:
    slugs = sorted(
        path.stem
        for path in STUDIES.glob("*.md")
        if path.name != "README.md"
    )
    return slugs


def move_study_files(slug: str) -> None:
    dest = study_dir(slug)
    dest.mkdir(parents=True, exist_ok=True)
    for name in (f"{slug}.md", f"{slug}.pdf", f"{slug}.html"):
        src = STUDIES / name
        if src.is_file():
            target = dest / name
            if target.exists():
                target.unlink()
            shutil.move(str(src), str(target))
            print(f"Moved {src} -> {target}")
    for src in sorted(STUDIES.glob(f"{slug}-*")):
        if src.is_file():
            target = dest / src.name
            if target.exists():
                target.unlink()
            shutil.move(str(src), str(target))
            print(f"Moved {src} -> {target}")


def move_orphan_svgs_to_wie() -> None:
    wie_dir = study_dir("The-Ontology-of-Coexistence")
    if not wie_dir.is_dir():
        return
    for src in sorted(STUDIES.glob("*.svg")):
        target = wie_dir / src.name
        if target.exists():
            target.unlink()
        shutil.move(str(src), str(target))
        print(f"Moved {src} -> {target}")


def fix_cross_study_links() -> None:
    slugs = known_study_slugs()
    slug_pattern = "|".join(re.escape(slug) for slug in slugs)
    link_re = re.compile(rf"\]\(({slug_pattern})\.pdf\)")
    for md_path in iter_study_md_paths():
        text = md_path.read_text(encoding="utf-8")
        updated = link_re.sub(lambda m: f"](../{m.group(1)}/{m.group(1)}.pdf)", text)
        if updated != text:
            md_path.write_text(updated, encoding="utf-8")
            print(f"Updated cross-links in {md_path}")


def fix_catalog_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    updated = text
    for slug in known_study_slugs():
        updated = updated.replace(f'href="{slug}.pdf"', f'href="{study_pdf_href(slug)}"')
        updated = updated.replace(f"]({slug}.pdf)", f"]({study_pdf_href(slug)})")
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        print(f"Updated catalog links in {path}")


def fix_references_files() -> None:
    for path in (REFERENCES / "README.md", REFERENCES / "MANIFEST.md"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        updated = text
        for slug in discover_flat_study_slugs() + known_study_slugs():
            old = f"../Studies/{slug}.pdf"
            new = study_pdf_ref_path(slug)
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            print(f"Updated reference paths in {path}")


def main() -> None:
    slugs = discover_flat_study_slugs()
    if not slugs:
        print("No flat study markdown files found; checking nested layout...")
        slugs = known_study_slugs()
        if slugs:
            print(f"Found nested studies: {', '.join(slugs)}")
            fix_cross_study_links()
            fix_catalog_file(STUDIES / "index.html")
            fix_catalog_file(STUDIES / "README.md")
            fix_references_files()
        return

    print(f"Migrating {len(slugs)} studies...")
    for slug in slugs:
        move_study_files(slug)
    move_orphan_svgs_to_wie()
    fix_cross_study_links()
    fix_catalog_file(STUDIES / "index.html")
    fix_catalog_file(STUDIES / "README.md")
    fix_references_files()
    print("Migration complete.")


if __name__ == "__main__":
    main()

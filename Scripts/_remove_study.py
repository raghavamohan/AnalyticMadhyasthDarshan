"""Remove a study from Studies/ and update catalog files.

Usage:
  python Scripts\\_remove_study.py Study-Slug
  python Scripts\\_remove_study.py Why-Humans-Are-Not-Just-Material --dry-run
  python Scripts\\_remove_study.py Study-Slug --yes

Deletes the study .md, .pdf, and local .html (if present), and updates index.html,
Studies/README.md, References/README.md, and References/MANIFEST.md.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from _common import REFERENCES, STUDIES, known_study_slugs, study_dir, study_html, study_md, study_pdf, study_pdf_ref_path
from _study_catalog import (
    StudyTable,
    find_study_table,
    parse_html_rows,
    parse_references_readme_rows,
    remove_manifest_paper_block,
    remove_study_row,
    write_references_readme_row,
    write_studies_catalog,
)

MANIFEST_LABELS: dict[str, str] = {
    "Why-Humans-Are-Not-Just-Material": "Why-Humans",
    "How-To-Form-Self-Sustaining-Organizations": "How-To-Form",
    "Human-Behavior-And-Society": "Human-Behavior",
    "The-Coexistence-Template": "Coexistence-Template",
    "Category-Theory-Explained": "Category-Theory",
}


def normalize_slug(value: str) -> str:
    slug = value.strip().removesuffix(".md").removesuffix(".pdf").removesuffix(".html")
    if not slug:
        raise ValueError("Study slug must not be empty.")
    return slug


def manifest_label(slug: str) -> str:
    if slug in MANIFEST_LABELS:
        return MANIFEST_LABELS[slug]
    if slug.startswith("The-"):
        return slug[4:]
    if "Category-Theory" in slug:
        return "Category-Theory"
    if slug.startswith("How-To-Form"):
        return "How-To-Form"
    if slug.startswith("Why-Humans"):
        return "Why-Humans"
    if slug.startswith("Human-Behavior"):
        return "Human-Behavior"
    parts = slug.split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else slug


def study_files(slug: str) -> list[Path]:
    directory = study_dir(slug)
    if directory.is_dir():
        return sorted(directory.iterdir())
    return [study_md(slug), study_pdf(slug), study_html(slug)]


def strip_cited_in(value: str, removed_label: str, remaining_labels: list[str]) -> str:
    text = value.strip()
    if text == "all Studies papers above":
        return text
    if text.startswith(removed_label):
        return "(none — review MANIFEST.md)"
    parts = [part.strip() for part in text.split(",")]
    kept = [
        part
        for part in parts
        if part
        and not part.startswith(removed_label)
        and removed_label not in part.split()[0:1]
    ]
    if not kept:
        return "(none — review MANIFEST.md)"
    return ", ".join(kept)


def update_manifest_tag_section(
    content: str,
    removed_label: str,
    remaining_labels: list[str],
) -> str:
    start = content.find("## By tag")
    end = content.find("## Summary")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Could not find MANIFEST '## By tag' / '## Summary' section.")

    before = content[:start]
    section = content[start:end]
    after = content[end:]

    updated_lines: list[str] = []
    for line in section.splitlines():
        if not line.startswith("| **"):
            updated_lines.append(line)
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            updated_lines.append(line)
            continue
        cells[2] = strip_cited_in(cells[2], removed_label, remaining_labels)
        updated_lines.append("| " + " | ".join(cells) + " |")

    return before + "\n".join(updated_lines) + "\n" + after


def confirm_removal(slug: str, paths: list[Path]) -> bool:
    print(f"Study slug: {slug}")
    print("Files to delete:")
    for path in paths:
        status = path if path.exists() else f"{path} (missing)"
        print(f"  - {status}")
    print("Catalog updates:")
    print("  - Studies/index.html")
    print("  - Studies/README.md")
    print("  - References/README.md (if published study)")
    print("  - References/MANIFEST.md (if published study)")
    answer = input("\nRemove this study? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def load_catalog_rows(table: StudyTable) -> list:
    index_path = STUDIES / "index.html"
    return parse_html_rows(index_path.read_text(encoding="utf-8"), table)


def remove_study(
    slug: str,
    *,
    dry_run: bool,
    assume_yes: bool,
) -> None:
    slug = normalize_slug(slug)
    table = find_study_table(slug)
    paths = study_files(slug)
    existing_paths = [path for path in paths if path.exists()]

    if table is None and not existing_paths:
        known = known_study_slugs()
        hint = f"\nKnown studies: {', '.join(known)}" if known else ""
        raise SystemExit(f"Study not found: {slug}{hint}")

    removed_label = manifest_label(slug)
    is_ongoing = table is not None and any(
        row.slug == slug and row.status.value == "ongoing"
        for row in load_catalog_rows(table)
    )

    if dry_run:
        print(f"Study slug:     {slug}")
        print(f"Catalog table:  {table.value if table else '(files only)'}")
        print(f"MANIFEST label: {removed_label}")
        print("Would delete:")
        for path in existing_paths or paths:
            print(f"  - {path}")
        print("\nDry run — no files changed.")
        return

    if not assume_yes and not confirm_removal(slug, paths):
        print("Cancelled.")
        return

    for path in existing_paths:
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Deleted {path}")
        else:
            path.unlink()
            print(f"Deleted {path}")

    if table is not None:
        rows = load_catalog_rows(table)
        before_count = len(rows)
        rows = remove_study_row(rows, slug)
        if len(rows) == before_count:
            print(f"Warning: {slug} not found in {table.value} catalog.")
        else:
            write_studies_catalog(rows, table)
            print(f"Updated Studies/index.html and Studies/README.md ({table.value} catalog)")

    if not is_ongoing:
        write_references_readme_row(slug, "", remove=True)
        print(f"Updated {REFERENCES / 'README.md'}")

        ref_text = (REFERENCES / "README.md").read_text(encoding="utf-8")
        ref_rows = parse_references_readme_rows(ref_text)
        remaining_labels = sorted(manifest_label(s) for s, _ in ref_rows)

        manifest_path = REFERENCES / "MANIFEST.md"
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest_text = remove_manifest_paper_block(manifest_text, slug)
        manifest_text = update_manifest_tag_section(
            manifest_text,
            removed_label,
            remaining_labels,
        )
        manifest_path.write_text(manifest_text, encoding="utf-8")
        print(f"Updated {manifest_path}")

    print("\nDone. Next steps:")
    print("  1. Search other Studies for cross-links to this paper and remove them.")
    print(f"  2. Review {REFERENCES / 'MANIFEST.md'} summary counts if needed.")
    print("  3. Commit the deletions and catalog updates.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove a study from Studies/ and update catalog files.",
    )
    parser.add_argument(
        "slug",
        help="Study slug (e.g. Why-Humans-Are-Not-Just-Material), with or without .pdf/.md",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing files")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    remove_study(
        normalize_slug(args.slug),
        dry_run=args.dry_run,
        assume_yes=args.yes,
    )


if __name__ == "__main__":
    main()

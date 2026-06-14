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
import re
from pathlib import Path

from _add_study import (
    REFERENCES_README_TABLE_HEADER,
    STUDIES_README_TABLE_HEADER,
    html_row,
    parse_html_rows,
    parse_md_rows,
    parse_references_readme_rows,
    readme_row,
    references_readme_row,
    replace_catalog_block,
)
from _common import REFERENCES, STUDIES

MANIFEST_LABELS: dict[str, str] = {
    "Why-Humans-Are-Not-Just-Material": "Why-Humans",
    "How-To-Form-Self-Sustaining-Organizations": "How-To-Form",
    "Human-Behavior-And-Society-In-Madhyasth-Darshan": "Human-Behavior",
    "The-Coexistence-Template": "Coexistence-Template",
    "Madhyasth-Darshan-Category-Theory-Explained": "Category-Theory",
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
    return [
        STUDIES / f"{slug}.md",
        STUDIES / f"{slug}.pdf",
        STUDIES / f"{slug}.html",
    ]


def remove_manifest_paper_block(content: str, slug: str) -> str:
    pdf_link = f"[{slug}.pdf](../Studies/{slug}.pdf)"
    lines = content.splitlines()
    kept: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if pdf_link in line and line.lstrip().startswith("|"):
            index += 1
            while index < len(lines) and re.match(r"\|\s*\|", lines[index]):
                index += 1
            continue
        kept.append(line)
        index += 1
    trailing = "\n" if content.endswith("\n") else ""
    return "\n".join(kept) + trailing


def strip_cited_in(value: str, removed_label: str, remaining_labels: list[str]) -> str:
    text = value.strip()
    if text == "all Studies papers above":
        if not remaining_labels:
            return "(none — review MANIFEST.md)"
        if len(remaining_labels) == 1:
            return remaining_labels[0]
        return ", ".join(remaining_labels)
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
    print("  - References/README.md")
    print("  - References/MANIFEST.md")
    answer = input("\nRemove this study? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def remove_study(
    slug: str,
    *,
    dry_run: bool,
    assume_yes: bool,
) -> None:
    slug = normalize_slug(slug)
    paths = study_files(slug)
    pdf_path = STUDIES / f"{slug}.pdf"

    if not pdf_path.exists() and not (STUDIES / f"{slug}.md").exists():
        known = sorted(p.stem for p in STUDIES.glob("*.md"))
        hint = f"\nKnown studies: {', '.join(known)}" if known else ""
        raise SystemExit(f"Study not found: {slug}{hint}")

    removed_label = manifest_label(slug)
    existing_paths = [path for path in paths if path.exists()]

    if dry_run:
        print(f"Study slug:        {slug}")
        print(f"MANIFEST label:    {removed_label}")
        print("Would delete:")
        for path in existing_paths or paths:
            print(f"  - {path}")
        print("\nDry run — no files changed.")
        return

    if not assume_yes and not confirm_removal(slug, paths):
        print("Cancelled.")
        return

    for path in existing_paths:
        path.unlink()
        print(f"Deleted {path}")

    index_path = STUDIES / "index.html"
    readme_path = STUDIES / "README.md"
    ref_readme_path = REFERENCES / "README.md"
    manifest_path = REFERENCES / "MANIFEST.md"

    index_text = index_path.read_text(encoding="utf-8")
    html_rows = [row for row in parse_html_rows(index_text) if row[0] != slug]
    if len(html_rows) == len(parse_html_rows(index_text)):
        print(f"Warning: {slug} not found in {index_path} catalog.")
    index_html_block = "\n".join(html_row(s, desc) for s, desc in html_rows)
    index_path.write_text(replace_catalog_block(index_text, index_html_block), encoding="utf-8")
    print(f"Updated {index_path}")

    readme_text = readme_path.read_text(encoding="utf-8")
    md_rows = [row for row in parse_md_rows(readme_text) if row[0] != slug]
    readme_md_block = STUDIES_README_TABLE_HEADER + "\n" + "\n".join(
        readme_row(s, desc) for s, desc in md_rows
    )
    readme_path.write_text(replace_catalog_block(readme_text, readme_md_block), encoding="utf-8")
    print(f"Updated {readme_path}")

    ref_text = ref_readme_path.read_text(encoding="utf-8")
    ref_rows = [row for row in parse_references_readme_rows(ref_text) if row[0] != slug]
    ref_block = REFERENCES_README_TABLE_HEADER + "\n" + "\n".join(
        references_readme_row(s, tags) for s, tags in ref_rows
    )
    ref_readme_path.write_text(replace_catalog_block(ref_text, ref_block), encoding="utf-8")
    print(f"Updated {ref_readme_path}")

    remaining_labels = sorted(manifest_label(s) for s, _ in ref_rows)
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_text = remove_manifest_paper_block(manifest_text, slug)
    manifest_text = update_manifest_tag_section(manifest_text, removed_label, remaining_labels)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    print(f"Updated {manifest_path}")

    print("\nDone. Next steps:")
    print("  1. Search other Studies for cross-links to this paper and remove them.")
    print(f"  2. Review {manifest_path} summary counts if needed.")
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

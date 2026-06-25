"""Add a study to Studies/ and update catalog files.

Usage:
  python Scripts\\_add_study.py path\\to\\Study.md
  python Scripts\\_add_study.py path\\to\\external.pdf
  python Scripts\\_add_study.py Study.md --category Ontology --description "..." --tags "MVD, SB, JV"
  python Scripts\\_add_study.py Study.md --status ongoing --dry-run

Registers the study in Studies/index.html, Studies/README.md, References/README.md,
and References/MANIFEST.md. Markdown input is preferred; sets **Edited on:** and
regenerates the PDF (Draft watermark when status is draft).
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from _common import REFERENCES, STUDIES, study_dir, study_md, study_pdf, study_pdf_ref_path
from _pdf_cache_sync import pdfs_for_tags, sync_pdf_cache
from _study_catalog import (
    StudyRow,
    StudyStatus,
    StudyTable,
    append_manifest_row,
    format_edited_on_md,
    format_status_md,
    now_ist,
    regenerate_pdf,
    set_edited_on,
    set_status_md,
    slug_to_title,
    title_to_slug,
    load_catalog_rows,
    upsert_study_row,
    verify_timestamp_sync,
    write_references_readme_row,
    write_studies_catalog,
)

GITHUB_REPO = "https://github.com/raghavamohan/AnalyticMadhyasthDarshan"
AUTHOR_BLOCK = (
    f"**Author:** [AnalyticMadhyasthDarshan.org]({GITHUB_REPO}) — a group of people "
    f"studying Madhyasth Darshan philosophy. Source repository: "
    f"[raghavamohan/AnalyticMadhyasthDarshan]({GITHUB_REPO})."
)


def prompt_if_missing(value: str | None, label: str, default: str | None = None) -> str:
    if value and value.strip():
        return value.strip()
    suffix = f" [{default}]" if default else ""
    while True:
        answer = input(f"{label}{suffix}: ").strip()
        if answer:
            return answer
        if default:
            return default
        print("  (required)")


def build_stub_markdown(title: str, description: str, edited_at, status: StudyStatus) -> str:
    status_line = format_status_md(status) if status != StudyStatus.ONGOING else ""
    status_block = f"\n{status_line}\n" if status_line else "\n"
    return f"""# {title}

{AUTHOR_BLOCK}

{format_edited_on_md(edited_at)}
{status_block}
{description}

> Expand this markdown source (sections, citations, references) and regenerate the PDF with `Scripts/_convert_to_pdf.py` when ready.

## References

- *(Add references here — link to files under `../References/` where available, or to the original publisher URL.)*
"""


def ensure_author_block(md_text: str) -> str:
    if "**Author:**" in md_text:
        return md_text
    h1_match = re.search(r"^# .+\n+", md_text, re.MULTILINE)
    if not h1_match:
        raise ValueError("Markdown must start with an H1 heading.")
    insert_at = h1_match.end()
    return md_text[:insert_at] + f"\n{AUTHOR_BLOCK}\n\n" + md_text[insert_at:]


def parse_status_arg(value: str) -> StudyStatus:
    normalized = value.strip().lower()
    try:
        return StudyStatus(normalized)
    except ValueError as exc:
        raise SystemExit(
            f"Invalid --status {value!r}; use draft, released, or ongoing."
        ) from exc


def update_manifest(slug: str, tags: str, *, force: bool) -> None:
    manifest_path = REFERENCES / "MANIFEST.md"
    manifest_text = manifest_path.read_text(encoding="utf-8")
    if f"{slug}.pdf" in manifest_text and force:
        manifest_text = re.sub(
            rf"\| \[{re.escape(slug)}\.pdf\]\({re.escape(study_pdf_ref_path(slug))}\) \|[^\n]+\n",
            "",
            manifest_text,
        )
    manifest_path.write_text(
        append_manifest_row(manifest_text, slug, tags),
        encoding="utf-8",
    )
    print(f"Updated {manifest_path}")


def add_study(
    input_path: Path,
    *,
    title: str | None,
    slug: str | None,
    category: str | None,
    description: str | None,
    tags: str | None,
    status: StudyStatus,
    formal: bool,
    dry_run: bool,
    force: bool,
    skip_pdf: bool,
    check_timestamps: bool,
) -> None:
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix not in {".md", ".pdf"}:
        raise SystemExit(f"Expected a .md or .pdf file, got: {input_path}")

    table = StudyTable.FORMAL if formal else StudyTable.TOPICAL
    is_pdf_import = suffix == ".pdf"
    derived_slug = slug or title_to_slug(title or input_path.stem.replace("_", " "))
    study_title = title or slug_to_title(derived_slug)
    dest_dir = study_dir(derived_slug)
    dest_md = study_md(derived_slug)
    dest_pdf = study_pdf(derived_slug)
    edited_at = now_ist()

    study_description = description or ""
    study_tags = tags or ""
    study_category = category or ""

    interactive = not dry_run and sys.stdin.isatty()
    if interactive:
        if not study_category and status != StudyStatus.ONGOING:
            study_category = prompt_if_missing(
                None,
                "Category (catalog column)",
                default="General",
            )
        if not study_description:
            study_description = prompt_if_missing(
                None,
                "Description (one line, shown in the catalog)",
                default=f"Study on {study_title}",
            )
        if not study_tags and status != StudyStatus.ONGOING:
            study_tags = prompt_if_missing(
                None,
                "Primary tags (e.g. MVD, SB, JV)",
                default="MVD, SB, JV",
            )
    else:
        study_description = study_description or f"Study on {study_title}"
        study_tags = study_tags or "MVD, SB, JV"
        if not study_category and status != StudyStatus.ONGOING:
            study_category = "General"

    if status == StudyStatus.ONGOING and formal:
        raise SystemExit("Ongoing placeholders are only supported in the Topical Studies catalog.")

    if dest_md.exists() and not force and not is_pdf_import and input_path.resolve() != dest_md.resolve():
        raise SystemExit(
            f"Study already exists: {dest_md}\nUse --force to refresh catalog entries."
        )
    if dest_pdf.exists() and not force and is_pdf_import:
        raise SystemExit(
            f"Study already exists: {dest_pdf}\nUse --force to overwrite."
        )

    catalog_row = StudyRow(
        slug=derived_slug,
        category=study_category,
        description=study_description,
        status=status,
        edited_at=None if status == StudyStatus.ONGOING else edited_at,
        table=table,
    )

    print(f"Slug:        {derived_slug}")
    print(f"Title:       {study_title}")
    print(f"Table:       {table.value}")
    print(f"Status:      {status.value}")
    print(f"Category:    {study_category}")
    print(f"Description: {study_description}")
    print(f"Tags:        {study_tags}")
    print(f"Input:       {input_path}")
    print(f"Markdown:    {dest_md}")
    if status != StudyStatus.ONGOING:
        print(f"PDF:         {dest_pdf}")

    if dry_run:
        print("\nDry run — no files changed.")
        return

    STUDIES.mkdir(parents=True, exist_ok=True)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if is_pdf_import:
        shutil.copy2(input_path, dest_pdf)
        print(f"Copied PDF to {dest_pdf}")
        if not dest_md.exists() or force:
            dest_md.write_text(
                build_stub_markdown(study_title, study_description, edited_at, status),
                encoding="utf-8",
            )
            print(f"Wrote stub markdown to {dest_md}")
        else:
            md_text = dest_md.read_text(encoding="utf-8")
            md_text = set_edited_on(md_text, edited_at)
            if status != StudyStatus.ONGOING:
                md_text = set_status_md(md_text, status)
            dest_md.write_text(md_text, encoding="utf-8")
            print(f"Updated **Edited on:** in {dest_md}")
        print(
            "\nNote: imported PDFs keep their original content. "
            "A Draft watermark is applied only after you expand the markdown and "
            "regenerate the PDF (re-run this script on the .md file, or use "
            "Scripts/_convert_to_pdf.py)."
        )
    else:
        if input_path.resolve() != dest_md.resolve():
            shutil.copy2(input_path, dest_md)
            print(f"Copied markdown to {dest_md}")
        md_text = dest_md.read_text(encoding="utf-8")
        md_text = ensure_author_block(md_text)
        md_text = set_edited_on(md_text, edited_at)
        if status != StudyStatus.ONGOING:
            md_text = set_status_md(md_text, status)
        dest_md.write_text(md_text, encoding="utf-8")
        print(f"Updated {dest_md}")

        if not skip_pdf and status != StudyStatus.ONGOING:
            regenerate_pdf(dest_md, status)
            print(f"Regenerated PDF at {dest_pdf}")

    rows = load_catalog_rows(table)
    rows = upsert_study_row(rows, catalog_row)
    write_studies_catalog(rows, table)
    print(f"Updated Studies/catalog JSON and Studies/README.md ({table.value} catalog)")

    if status != StudyStatus.ONGOING:
        write_references_readme_row(derived_slug, study_tags)
        print(f"Updated {REFERENCES / 'README.md'}")
        update_manifest(derived_slug, study_tags, force=force)
        tag_names = {tag.strip() for tag in study_tags.split(",") if tag.strip()}
        pdf_paths = pdfs_for_tags(tag_names)
        if pdf_paths:
            print(f"Syncing PDF cache for {len(pdf_paths)} reference(s)...")
            sync_pdf_cache(pdf_paths, prune=False)

    if check_timestamps:
        errors = verify_timestamp_sync(derived_slug)
        if errors:
            print("\nTimestamp verification FAILED:")
            for error in errors:
                print(f"  - {error}")
            raise SystemExit(1)
        print("\nTimestamp verification passed.")

    print("\nDone. Next steps:")
    if is_pdf_import:
        print(f"  1. Edit {dest_md} — expand content and add a References section.")
        print("  2. Re-run on the .md file to regenerate a Draft-watermarked PDF.")
    else:
        print(f"  1. Continue editing {dest_md} as the canonical source.")
    print(f"  2. Update tag details in {REFERENCES / 'MANIFEST.md'} (change TBD rows as needed).")
    print("  3. Commit the study files and catalog updates.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add or register a study and update catalog files.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to study .md (preferred) or external .pdf",
    )
    parser.add_argument("--title", help="Study title (default: derived from filename)")
    parser.add_argument("--slug", help="Filename slug without extension (default: from title)")
    parser.add_argument("--category", help="Catalog category (or Formal Focus when --formal)")
    parser.add_argument("--description", help="One-line catalog description")
    parser.add_argument(
        "--tags",
        help='Primary citation tags for References/README (e.g. "MVD, SB, JV")',
    )
    parser.add_argument(
        "--status",
        default="draft",
        help="Catalog status: draft (default), released, or ongoing",
    )
    parser.add_argument(
        "--formal",
        action="store_true",
        help="Register in Formal Studies table instead of Topical Studies",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing study files")
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Update catalogs only; do not regenerate PDF from markdown",
    )
    parser.add_argument(
        "--check-timestamps",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Verify **Edited on:** matches catalog timestamps after add (default: on)",
    )
    args = parser.parse_args()

    add_study(
        args.input.resolve(),
        title=args.title,
        slug=args.slug,
        category=args.category,
        description=args.description,
        tags=args.tags,
        status=parse_status_arg(args.status),
        formal=args.formal,
        dry_run=args.dry_run,
        force=args.force,
        skip_pdf=args.skip_pdf,
        check_timestamps=args.check_timestamps,
    )


if __name__ == "__main__":
    main()

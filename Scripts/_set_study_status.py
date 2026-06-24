"""Change a study between Draft and Released status.

Usage:
  python Scripts\\_set_study_status.py Study-Slug --status released
  python Scripts\\_set_study_status.py Study-Slug --status draft
  python Scripts\\_set_study_status.py Study-Slug

Updates **Status:** and **Edited on:** in the markdown, the Topical or Formal Studies
catalog row in Studies/index.html and Studies/README.md, and regenerates the PDF
(with or without the Draft watermark).
"""
from __future__ import annotations

import argparse

from _common import STUDIES, known_study_slugs, study_dir, study_md, study_pdf, study_html
from _study_catalog import (
    StudyStatus,
    format_edited_on_md,
    get_study_row,
    load_catalog_rows,
    now_ist,
    regenerate_pdf,
    set_edited_on,
    set_status_md,
    upsert_study_row,
    verify_timestamp_sync,
    write_studies_catalog,
)


def normalize_slug(value: str) -> str:
    slug = value.strip().removesuffix(".md").removesuffix(".pdf").removesuffix(".html")
    if not slug:
        raise ValueError("Study slug must not be empty.")
    return slug


def parse_status_arg(value: str) -> StudyStatus:
    normalized = value.strip().lower()
    if normalized == "ongoing":
        raise SystemExit("Cannot set status to ongoing; use _add_study.py for placeholders.")
    try:
        return StudyStatus(normalized)
    except ValueError as exc:
        raise SystemExit(
            f"Invalid --status {value!r}; use draft or released."
        ) from exc


def set_study_status(
    slug: str,
    *,
    new_status: StudyStatus | None,
    dry_run: bool,
    skip_pdf: bool,
    check_timestamps: bool,
) -> None:
    slug = normalize_slug(slug)
    located = get_study_row(slug)
    if located is None:
        known = known_study_slugs()
        hint = f"\nKnown studies: {', '.join(known)}" if known else ""
        raise SystemExit(f"Study not found in catalog: {slug}{hint}")

    row, table = located
    if row.status == StudyStatus.ONGOING:
        raise SystemExit(
            f"{slug} is an Ongoing placeholder (no PDF). "
            "Register it with _add_study.py before changing Draft/Released status."
        )

    target_status = new_status
    if target_status is None:
        if row.status == StudyStatus.DRAFT:
            target_status = StudyStatus.RELEASED
        elif row.status == StudyStatus.RELEASED:
            target_status = StudyStatus.DRAFT
        else:
            target_status = StudyStatus.DRAFT

    if target_status == row.status:
        print(
            f"Note: {slug} is already {target_status.value} in the catalog; "
            "refreshing **Edited on:** and catalogs."
        )

    md_path = study_md(slug)
    if not md_path.exists():
        raise SystemExit(f"Markdown source not found: {md_path}")

    edited_at = now_ist()

    print(f"Slug:          {slug}")
    print(f"Catalog table: {table.value}")
    if target_status != row.status:
        print(f"Status:        {row.status.value} -> {target_status.value}")
    else:
        print(f"Status:        {target_status.value} (unchanged)")
    print(f"Edited on:     {format_edited_on_md(edited_at).removeprefix('**Edited on:** ')}")
    print(f"Markdown:      {md_path}")
    print(f"PDF:           {study_pdf(slug)}")

    if dry_run:
        print("\nDry run — no files changed.")
        return

    md_text = md_path.read_text(encoding="utf-8")
    md_text = set_edited_on(md_text, edited_at)
    md_text = set_status_md(md_text, target_status)
    md_path.write_text(md_text, encoding="utf-8")
    print(f"Updated {md_path}")

    updated_row = row
    updated_row.status = target_status
    updated_row.edited_at = edited_at
    rows = upsert_study_row(load_catalog_rows(table), updated_row)
    write_studies_catalog(rows, table)
    print(f"Updated Studies/index.html and Studies/README.md ({table.value} catalog)")

    if not skip_pdf:
        regenerate_pdf(md_path, target_status)
        print(f"Regenerated PDF at {study_pdf(slug)}")

    if check_timestamps:
        errors = verify_timestamp_sync(slug)
        if errors:
            print("\nTimestamp verification FAILED:")
            for error in errors:
                print(f"  - {error}")
            raise SystemExit(1)
        print("\nTimestamp and status verification passed.")

    print("\nDone.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Change a study between Draft and Released status.",
    )
    parser.add_argument(
        "slug",
        help="Study slug (e.g. The-Ontology-of-Coexistence), with or without .pdf/.md",
    )
    parser.add_argument(
        "--status",
        choices=["draft", "released"],
        help="Target status (default: toggle draft <-> released)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing files")
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Update markdown and catalogs only; do not regenerate PDF",
    )
    parser.add_argument(
        "--check-timestamps",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Verify sync after update (default: on)",
    )
    args = parser.parse_args()

    new_status = parse_status_arg(args.status) if args.status else None
    set_study_status(
        args.slug,
        new_status=new_status,
        dry_run=args.dry_run,
        skip_pdf=args.skip_pdf,
        check_timestamps=args.check_timestamps,
    )


if __name__ == "__main__":
    main()

"""Regenerate a study PDF from its markdown source.

Reads **Status:** from the study .md and applies the correct watermark.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import STUDIES, iter_study_md_paths, known_study_slugs, study_md, study_pdf
from _study_catalog import StudyStatus, parse_status_md, regenerate_pdf


def normalize_slug(value: str) -> str:
    return value.strip().removesuffix(".md").removesuffix(".pdf").removesuffix(".html")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate Studies/<Slug>/<Slug>.pdf from Studies/<Slug>/<Slug>.md.",
    )
    parser.add_argument(
        "slug",
        help="Study slug (e.g. The-Ontology-of-Coexistence), with or without .md/.pdf",
    )
    args = parser.parse_args()

    slug = normalize_slug(args.slug)
    md_path = study_md(slug)
    if not md_path.exists():
        raise SystemExit(f"Study markdown not found: {md_path}")

    md_text = md_path.read_text(encoding="utf-8")
    status = parse_status_md(md_text)
    if status is None:
        raise SystemExit(f"**Status:** missing in {md_path}")
    if status == StudyStatus.ONGOING:
        raise SystemExit(f"{slug} is Ongoing — no PDF to regenerate.")

    regenerate_pdf(md_path, status)
    print(f"Regenerated PDF at {study_pdf(slug)}")


if __name__ == "__main__":
    main()

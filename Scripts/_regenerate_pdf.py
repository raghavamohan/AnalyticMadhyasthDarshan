"""Regenerate a study or companion note PDF from its markdown source.

Reads **Status:** from a study .md and applies the correct watermark.

Companion notes -- research and technical notes that live beside a study but are
not catalog entries -- carry no **Status:** line, so this script used to reject
them and they had no supported entry point at all. Four of them were found with
their maths typeset in fallback fonts, and rebuilding them took a throwaway
script that reimplemented this pipeline. They are now accepted by path and
rendered without a watermark, matching how they are already committed.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import APPLICATIONS, BASE, STUDIES, study_md, study_pdf
from _study_catalog import StudyStatus, parse_status_md, regenerate_pdf


def normalize_slug(value: str) -> str:
    return value.strip().removesuffix(".md").removesuffix(".pdf").removesuffix(".html")


def _is_companion_note(md_path: Path) -> bool:
    """True for a markdown file beside a study rather than the study itself.

    `Studies/<Slug>/<Slug>.md` is the catalog entry; anything else in that folder
    is a companion. Applications are laid out the same way.
    """
    if md_path.stem == md_path.parent.name:
        return False
    try:
        parent = md_path.parent.parent
    except (ValueError, IndexError):
        return False
    return parent in (STUDIES, APPLICATIONS)


def resolve_target(value: str) -> Path:
    """Accept a study slug or a path to any study-folder markdown file."""
    candidate = Path(value)
    if candidate.suffix.lower() in {".md", ".pdf", ".html"} or any(
        sep in value for sep in ("/", "\\")
    ):
        md_path = (BASE / candidate).resolve() if not candidate.is_absolute() else candidate
        md_path = md_path.with_suffix(".md")
        if md_path.is_file():
            return md_path
        raise SystemExit(f"Markdown not found: {md_path}")

    slug = normalize_slug(value)
    md_path = study_md(slug)
    if md_path.exists():
        return md_path
    raise SystemExit(
        f"Study markdown not found: {md_path}\n"
        "For a companion note, pass its path, e.g.\n"
        "  python Scripts/_regenerate_pdf.py Studies/<Slug>/Research-Note-Example.md"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate a study PDF from Studies/<Slug>/<Slug>.md, or a companion "
            "note PDF from a path to its markdown."
        ),
    )
    parser.add_argument(
        "target",
        help=(
            "Study slug (e.g. The-Ontology-of-Coexistence), or a path to a "
            "companion note's .md inside a study folder"
        ),
    )
    args = parser.parse_args()

    md_path = resolve_target(args.target)
    status = parse_status_md(md_path.read_text(encoding="utf-8"))
    companion = _is_companion_note(md_path)

    if status is None:
        if not companion:
            raise SystemExit(f"**Status:** missing in {md_path}")
        # No Status means no watermark, which is how these notes are committed.
        # RELEASED is the pipeline's way of saying "render unwatermarked"; it
        # writes no catalog row, so nothing here touches the catalogs.
        status = StudyStatus.RELEASED
        print(f"{md_path.name}: companion note, no **Status:** — rendering unwatermarked.")
    elif status == StudyStatus.ONGOING:
        raise SystemExit(f"{md_path.stem} is Ongoing — no PDF to regenerate.")

    regenerate_pdf(md_path, status)
    print(f"Regenerated HTML at {md_path.with_suffix('.html')}")
    pdf_path = md_path.with_suffix(".pdf") if companion else study_pdf(md_path.stem)
    print(f"Regenerated PDF at {pdf_path}")


if __name__ == "__main__":
    main()

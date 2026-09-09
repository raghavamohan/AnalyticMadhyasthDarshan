"""Shared publication eligibility for readers, PDFs, discovery and site packaging."""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import BASE
from _study_pdf_metadata import iter_pdf_study_rows


def is_public_status(status: str) -> bool:
    return status in {"draft", "released"}


def public_studies() -> set[tuple[str, str]]:
    return {(row.collection, row.slug) for row in iter_pdf_study_rows() if is_public_status(row.status)}


def public_markdown(path: Path, *, root: Path | None = None, studies: set[tuple[str, str]] | None = None) -> bool:
    try:
        parts = path.relative_to(root or BASE).parts
    except ValueError:
        return False
    return (len(parts) == 3 and (parts[0], parts[1]) in (public_studies() if studies is None else studies)
            and path.suffix == ".md" and not path.stem.startswith("Research-Template-"))


def planned_reader_paths() -> list[Path]:
    paths = []
    for row in iter_pdf_study_rows():
        if not is_public_status(row.status):
            parent = BASE / row.collection / row.slug
            paths.extend([parent / f"{row.slug}.html", parent / "discussion.html"])
    return paths


def verify_publication_inventory() -> list[str]:
    paths = planned_reader_paths()
    errors = [f"Planned study has a public reader: {p.relative_to(BASE)}" for p in paths if p.exists()]
    index = BASE / "Studies/index.html"
    if index.is_file():
        text = index.read_text(encoding="utf-8")
        for path in paths:
            relative = path.relative_to(BASE / "Studies").as_posix() if path.is_relative_to(BASE / "Studies") else "../" + path.relative_to(BASE).as_posix()
            if f'href="{relative}' in text:
                errors.append(f"Planned study has an index reader link: {relative}")
    return errors


def clean_planned_readers() -> None:
    for path in planned_reader_paths():
        if path.is_symlink() or not path.resolve().is_relative_to(BASE.resolve()):
            raise ValueError(f"Unsafe planned reader path: {path}")
        if path.is_file():
            path.unlink()
            print(f"Removed generated proposal reader: {path.relative_to(BASE)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-planned", action="store_true")
    args = parser.parse_args()
    if args.clean_planned:
        clean_planned_readers()
    errors = verify_publication_inventory()
    if errors:
        raise SystemExit("\n".join(errors))

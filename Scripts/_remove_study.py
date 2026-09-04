"""Remove a study from Studies/ or Applications/ and update catalog files.

Usage:
  python Scripts\\_remove_study.py Study-Slug
  python Scripts\\_remove_study.py Why-Humans-Are-Not-Just-Material --dry-run
  python Scripts\\_remove_study.py Study-Slug --yes

Deletes the complete study directory and updates the catalog, proposal registry,
References/README.md, and References/MANIFEST.md.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from _common import (
    BASE,
    REFERENCES,
    STUDIES,
    known_study_slugs,
    study_dir,
    study_html,
    study_md,
    study_pdf,
    study_pdf_ref_path,
    validate_study_slug,
    write_text_lf,
)
from _study_catalog import (
    StudyTable,
    find_study_table,
    load_catalog_rows,
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
    "The-Epistemology-of-Coexistence": "Knowledge-Knower",
    "Ethics-And-Morals-In-Human-Beings": "Ethics-And-Morals",
}
PROPOSAL_REGISTRY_PATH = STUDIES / "proposal-registry.json"
PRESENTATION_MANIFEST_PATH = BASE / "Scripts" / "presentation-pipeline.json"


def normalize_slug(value: str) -> str:
    slug = value.strip().removesuffix(".md").removesuffix(".pdf").removesuffix(".html")
    if not slug:
        raise SystemExit("Study slug must not be empty.")
    try:
        validate_study_slug(slug)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
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


def manifest_aliases(slug: str) -> set[str]:
    """Names used for one study in MANIFEST.md's historical By-tag column."""
    return {slug, manifest_label(slug)}


def _split_cited_in(value: str) -> list[str]:
    """Split comma/semicolon lists without cutting explanatory parentheses."""
    parts: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(value):
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char in {",", ";"} and depth == 0:
            part = value[start:index].strip()
            if part:
                parts.append(part)
            start = index + 1
    tail = value[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def strip_cited_in(value: str, removed_aliases: set[str]) -> str:
    text = value.strip()
    if text == "all Studies papers above":
        return text
    parts = _split_cited_in(text)

    def is_removed(part: str) -> bool:
        return any(
            part == alias or part.startswith(f"{alias} ") or part.startswith(f"{alias}(")
            for alias in removed_aliases
        )

    kept = [
        part
        for part in parts
        if part and not is_removed(part)
    ]
    if not kept:
        return "(none — review MANIFEST.md)"
    return ", ".join(kept)


def update_manifest_tag_section(
    content: str,
    removed_aliases: set[str],
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
        cells[2] = strip_cited_in(cells[2], removed_aliases)
        updated_lines.append("| " + " | ".join(cells) + " |")

    return before + "\n".join(updated_lines) + "\n" + after


def remove_registry_row(slug: str, *, dry_run: bool) -> bool:
    """Remove proposal metadata that would otherwise recreate a retired study."""
    if not PROPOSAL_REGISTRY_PATH.is_file():
        return False
    data = json.loads(PROPOSAL_REGISTRY_PATH.read_text(encoding="utf-8"))
    proposals = list(data.get("proposals", []))
    filtered = [row for row in proposals if row.get("slug") != slug]
    if len(filtered) == len(proposals):
        return False
    if dry_run:
        return True
    data["proposals"] = filtered
    write_text_lf(PROPOSAL_REGISTRY_PATH, json.dumps(data, indent=2) + "\n")
    return True


def remove_presentation_manifest_entries(
    slug: str,
    *,
    dry_run: bool,
    directory: Path | None = None,
) -> int:
    """Remove every deck whose source lives in the retired study directory."""
    if not PRESENTATION_MANIFEST_PATH.is_file():
        return 0
    study_directory = directory or study_dir(slug)
    try:
        prefix = study_directory.resolve().relative_to(BASE.resolve()).as_posix() + "/"
    except ValueError as exc:
        raise SystemExit(f"Study directory is outside the repository: {study_directory}") from exc
    data = json.loads(PRESENTATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    decks = list(data.get("decks", []))
    prefix_folded = prefix.casefold()
    kept = [
        deck for deck in decks
        if not str(deck.get("source") or "").replace("\\", "/").casefold().startswith(prefix_folded)
    ]
    removed = len(decks) - len(kept)
    if removed and not dry_run:
        data["decks"] = kept
        write_text_lf(PRESENTATION_MANIFEST_PATH, json.dumps(data, indent=2) + "\n")
    return removed


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
        if remove_registry_row(slug, dry_run=True):
            print(f"Would remove {slug} from {PROPOSAL_REGISTRY_PATH}")
        deck_count = remove_presentation_manifest_entries(
            slug,
            dry_run=True,
            directory=study_dir(slug),
        )
        if deck_count:
            print(
                f"Would remove {deck_count} deck entr{'y' if deck_count == 1 else 'ies'} "
                f"from {PRESENTATION_MANIFEST_PATH}"
            )
        print("\nDry run — no files changed.")
        return

    if not assume_yes and not confirm_removal(slug, paths):
        print("Cancelled.")
        return

    deck_count = remove_presentation_manifest_entries(
        slug,
        dry_run=False,
        directory=study_dir(slug),
    )
    if deck_count:
        print(
            f"Updated {PRESENTATION_MANIFEST_PATH}: removed "
            f"{deck_count} deck entr{'y' if deck_count == 1 else 'ies'}"
        )

    for path in existing_paths:
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Deleted {path}")
        else:
            path.unlink()
            print(f"Deleted {path}")

    if remove_registry_row(slug, dry_run=False):
        print(f"Updated {PROPOSAL_REGISTRY_PATH}")

    if table is not None:
        rows = load_catalog_rows(table)
        before_count = len(rows)
        rows = remove_study_row(rows, slug)
        if len(rows) == before_count:
            print(f"Warning: {slug} not found in {table.value} catalog.")
        else:
            write_studies_catalog(
                rows,
                table,
                rebuild_discussion=False,
                rebuild_feedback_template=True,
            )
            print(f"Updated Studies/catalog JSON and Studies/README.md ({table.value} catalog)")

    if not is_ongoing:
        write_references_readme_row(slug, "", remove=True)
        print(f"Updated {REFERENCES / 'README.md'}")

        manifest_path = REFERENCES / "MANIFEST.md"
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest_text = remove_manifest_paper_block(manifest_text, slug)
        manifest_text = update_manifest_tag_section(
            manifest_text,
            manifest_aliases(slug),
        )
        write_text_lf(manifest_path, manifest_text)
        print(f"Updated {manifest_path}")

    print("\nDone. Next steps:")
    print("  1. Remove or retarget cross-study links to this paper; study PR CI rejects stale links.")
    print(f"  2. Review {REFERENCES / 'MANIFEST.md'} summary counts if needed.")
    print("  3. Commit the deletions and catalog updates.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove a study from Studies/ or Applications/ and update catalog files.",
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

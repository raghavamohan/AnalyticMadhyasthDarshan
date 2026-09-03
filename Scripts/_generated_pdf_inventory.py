"""Canonical inventory of generated PDFs under Studies/ and Applications/."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from _common import APPLICATIONS, BASE, STUDIES
from _presentation_pipeline import load_manifest, manifest_errors, repo_relative
from _study_catalog import StudyStatus, parse_status_md


@dataclass(frozen=True)
class GeneratedPdfSpec:
    key: str
    source: Path
    output: Path
    kind: str
    presentation_id: str | None = None


def _publishable_markdown(path: Path) -> bool:
    # Reusable research schemas are source templates, not reader documents.
    if path.stem.startswith("Research-Template-"):
        return False
    # Companion notes are publishable without catalog status. Canonical study
    # stubs are not: Ongoing/Planned rows have no public read/download link and
    # _regenerate_pdf.py intentionally refuses to render them.
    if path.stem != path.parent.name:
        return True
    status = parse_status_md(path.read_text(encoding="utf-8"))
    return status in (StudyStatus.DRAFT, StudyStatus.RELEASED)


def generated_pdf_specs() -> tuple[GeneratedPdfSpec, ...]:
    specs: list[GeneratedPdfSpec] = []
    markdown_sources = sorted(STUDIES.glob("*/*.md")) + sorted(APPLICATIONS.glob("*/*.md"))
    for source in markdown_sources:
        if not _publishable_markdown(source):
            continue
        output = source.with_suffix(".pdf")
        specs.append(GeneratedPdfSpec(repo_relative(output), source, output, "markdown"))

    manifest = load_manifest()
    for deck in manifest.decks:
        specs.append(GeneratedPdfSpec(
            repo_relative(deck.slides_pdf), deck.source, deck.slides_pdf,
            "presentation-slides", deck.id,
        ))
        specs.append(GeneratedPdfSpec(
            repo_relative(deck.notes_pdf), deck.source, deck.notes_pdf,
            "presentation-notes", deck.id,
        ))
    return tuple(sorted(specs, key=lambda item: item.key.casefold()))


def inventory_errors(specs: tuple[GeneratedPdfSpec, ...] | None = None) -> list[str]:
    selected = specs or generated_pdf_specs()
    errors = manifest_errors(load_manifest())
    keys = [spec.key for spec in selected]
    if len(keys) != len(set(keys)):
        errors.append("generated PDF keys are not unique")
    for spec in selected:
        if not spec.source.is_file():
            errors.append(f"generated PDF source is missing: {repo_relative(spec.source)}")
        if spec.output.suffix.lower() != ".pdf":
            errors.append(f"generated output is not a PDF: {spec.key}")
        try:
            spec.output.resolve().relative_to(BASE.resolve())
        except ValueError:
            errors.append(f"generated output escapes the repository: {spec.output}")

    declared = {spec.output.resolve() for spec in selected}
    existing = {
        path.resolve()
        for root in (STUDIES, APPLICATIONS)
        for path in root.glob("*/*.pdf")
    }
    for path in sorted(existing - declared):
        errors.append(f"unclassified generated PDF: {repo_relative(path)}")
    tracked = subprocess.run(
        ["git", "ls-files", "--", "Studies/**/*.pdf", "Applications/**/*.pdf"],
        cwd=BASE,
        check=False,
        text=True,
        capture_output=True,
    )
    if tracked.returncode != 0:
        errors.append("could not inspect Git tracking for generated PDFs")
    else:
        for key in tracked.stdout.splitlines():
            errors.append(f"generated PDF must not be tracked by Git: {key}")
    return errors


def spec_by_key(key: str) -> GeneratedPdfSpec:
    normalized = key.replace("\\", "/").lstrip("/")
    for spec in generated_pdf_specs():
        if spec.key == normalized:
            return spec
    raise ValueError(f"Unknown generated PDF key: {key}")

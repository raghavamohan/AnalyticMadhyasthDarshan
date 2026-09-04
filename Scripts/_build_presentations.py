#!/usr/bin/env python3
"""Build verified companion presentation artifacts from the canonical manifest."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

import pymupdf as fitz

from _build_deck_notes_pdf import build as build_notes_pdf
from _check_deck_layout import check_deck
from _common import BASE, configure_utf8_stdio, write_text_lf
from _pptx_to_pdf import convert_pptx_to_pdf, renderer_profile_for_engine
from _presentation_pipeline import (
    DeckSpec,
    load_manifest,
    manifest_errors,
    repo_relative,
    sha256_file,
)
from _verify_presentations import verify_deck


def mapped_path(root: Path, configured: Path) -> Path:
    return root.resolve() / configured.resolve().relative_to(BASE.resolve())


def artifact_record(spec: DeckSpec, slides_pdf: Path, notes_pdf: Path) -> dict:
    with fitz.open(slides_pdf) as slides, fitz.open(notes_pdf) as notes:
        return {
            "id": spec.id,
            "source": repo_relative(spec.source),
            "sourceSha256": sha256_file(spec.source),
            "slidesPdf": repo_relative(spec.slides_pdf),
            "slidesPdfSha256": sha256_file(slides_pdf),
            "slidePages": len(slides),
            "notesPdf": repo_relative(spec.notes_pdf),
            "notesPdfSha256": sha256_file(notes_pdf),
            "notesPages": len(notes),
        }


def copy_verified_tree(staging: Path, destination: Path, specs: tuple[DeckSpec, ...]) -> None:
    for spec in specs:
        for configured in (spec.slides_pdf, spec.notes_pdf):
            source = mapped_path(staging, configured)
            target = mapped_path(destination, configured)
            target.parent.mkdir(parents=True, exist_ok=True)
            handle, temp_name = tempfile.mkstemp(
                prefix=f".{target.stem}-", suffix=target.suffix, dir=target.parent
            )
            os.close(handle)
            temp_target = Path(temp_name)
            try:
                shutil.copyfile(source, temp_target)
                os.replace(temp_target, target)
            finally:
                temp_target.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Build presentation slides/notes PDFs into a staging tree, verify, then publish locally."
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true", help="Build every manifested deck")
    selection.add_argument("--deck", action="append", metavar="ID", help="Build one deck id; repeatable")
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument(
        "--output-root", type=Path,
        help="Destination root; PDFs retain their repository-relative paths below it",
    )
    destination.add_argument(
        "--in-place", action="store_true",
        help="Replace the configured repository PDFs only after every selected deck passes",
    )
    parser.add_argument(
        "--profile", help="Renderer profile (default: manifest productionProfile)"
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        help=(
            "Provenance JSON path. Defaults to presentation-build-provenance.json "
            "under --output-root; omitted for --in-place unless explicitly requested."
        ),
    )
    args = parser.parse_args(argv)

    manifest = load_manifest()
    errors = manifest_errors(manifest)
    if errors:
        raise SystemExit("Presentation manifest errors:\n  - " + "\n  - ".join(errors))
    specs = manifest.decks if args.all else tuple(manifest.deck(value) for value in args.deck)
    profile = renderer_profile_for_engine(None, args.profile)
    destination_root = BASE if args.in_place else args.output_root.expanduser().resolve()

    layout_errors: list[str] = []
    for spec in specs:
        fatal = [finding for finding in check_deck(spec.source, 95.0) if finding.fatal]
        for finding in fatal:
            layout_errors.append(
                f"{spec.id} slide {finding.slide}: {finding.kind}: {finding.detail}"
            )
    if layout_errors:
        raise SystemExit("Presentation layout checks failed:\n  - " + "\n  - ".join(layout_errors))

    records: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="presentation-build-") as temp:
        staging = Path(temp)
        for spec in specs:
            slides_pdf = mapped_path(staging, spec.slides_pdf)
            notes_pdf = mapped_path(staging, spec.notes_pdf)
            slides_pdf.parent.mkdir(parents=True, exist_ok=True)
            engine, version = convert_pptx_to_pdf(
                spec.source,
                slides_pdf,
                engine=profile.engine,
                expected_version=profile.version,
            )
            build_notes_pdf(spec.source, slides_pdf, notes_pdf)
            deck_errors = verify_deck(spec, staging)
            if deck_errors:
                raise SystemExit(
                    f"Presentation verification failed for {spec.id}:\n  - "
                    + "\n  - ".join(deck_errors)
                )
            records.append(artifact_record(spec, slides_pdf, notes_pdf))
            print(f"Verified {spec.id} ({engine} {version})")

        copy_verified_tree(staging, destination_root, specs)

    provenance = {
        "schemaVersion": 1,
        "rendererProfile": profile.name,
        "rendererEngine": profile.engine,
        "rendererVersion": profile.version,
        "artifacts": records,
    }
    provenance_path = args.provenance
    if provenance_path is None and not args.in_place:
        provenance_path = destination_root / "presentation-build-provenance.json"
    if provenance_path is not None:
        provenance_path = provenance_path.expanduser().resolve()
        write_text_lf(provenance_path, json.dumps(provenance, indent=2) + "\n")
        print(f"Wrote {provenance_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

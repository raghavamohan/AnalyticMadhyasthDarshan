#!/usr/bin/env python3
"""Rank cross-renderer presentation differences and render the worst pages."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageChops, ImageEnhance, ImageStat

from _common import BASE, configure_utf8_stdio, write_text_lf
from _presentation_pipeline import DeckSpec, load_manifest, manifest_errors
from _verify_presentations import token_recall


def mapped_path(root: Path, configured: Path) -> Path:
    return root.resolve() / configured.resolve().relative_to(BASE.resolve())


def render_page(page: fitz.Page) -> Image.Image:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def compare_page(
    reference: Image.Image,
    candidate: Image.Image,
) -> tuple[float, float, Image.Image, bool]:
    adjusted = False
    if reference.size != candidate.size:
        if max(abs(a - b) for a, b in zip(reference.size, candidate.size)) > 2:
            raise ValueError(
                f"rendered page sizes differ materially: {reference.size} != {candidate.size}"
            )
        candidate = candidate.resize(reference.size, Image.Resampling.LANCZOS)
        adjusted = True
    difference = ImageChops.difference(reference, candidate)
    mean_absolute = sum(ImageStat.Stat(difference).mean) / (3 * 255)
    gray = difference.convert("L")
    histogram = gray.histogram()
    changed = sum(histogram[13:]) / (reference.width * reference.height)
    return mean_absolute, changed, difference, adjusted


def comparison_panel(reference: Image.Image, candidate: Image.Image, difference: Image.Image) -> Image.Image:
    enhanced = ImageEnhance.Contrast(difference).enhance(3.0)
    gutter = 12
    panel = Image.new(
        "RGB",
        (reference.width * 3 + gutter * 2, reference.height),
        "white",
    )
    panel.paste(reference, (0, 0))
    panel.paste(candidate, (reference.width + gutter, 0))
    panel.paste(enhanced, ((reference.width + gutter) * 2, 0))
    return panel


def compare_deck(spec: DeckSpec, reference_root: Path, candidate_root: Path) -> list[dict]:
    reference_path = mapped_path(reference_root, spec.slides_pdf)
    candidate_path = mapped_path(candidate_root, spec.slides_pdf)
    if not reference_path.is_file() or not candidate_path.is_file():
        raise FileNotFoundError(f"Missing renderer comparison input for {spec.id}")
    rows: list[dict] = []
    with fitz.open(reference_path) as reference, fitz.open(candidate_path) as candidate:
        if len(reference) != len(candidate):
            raise ValueError(
                f"{spec.id}: page count differs: {len(reference)} != {len(candidate)}"
            )
        for index, (reference_page, candidate_page) in enumerate(zip(reference, candidate), 1):
            reference_image = render_page(reference_page)
            candidate_image = render_page(candidate_page)
            mean_absolute, changed, difference, adjusted = compare_page(
                reference_image, candidate_image
            )
            if adjusted:
                candidate_image = candidate_image.resize(
                    reference_image.size, Image.Resampling.LANCZOS
                )
            rows.append({
                "deck": spec.id,
                "page": index,
                "meanAbsoluteDifference": round(mean_absolute, 6),
                "changedPixelFraction": round(changed, 6),
                "textRecall": round(
                    token_recall(
                        reference_page.get_text("text"),
                        candidate_page.get_text("text"),
                    ),
                    6,
                ),
                "candidateRasterSizeAdjusted": adjusted,
                "_images": (reference_image, candidate_image, difference),
            })
    return rows


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Compare slides PDFs from two renderer output trees."
    )
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--top", type=int, default=3, help="Panels to retain per deck")
    args = parser.parse_args(argv)
    if args.top < 1:
        raise SystemExit("--top must be at least 1")

    manifest = load_manifest()
    errors = manifest_errors(manifest)
    if errors:
        raise SystemExit("Presentation manifest errors:\n  - " + "\n  - ".join(errors))
    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_rows: list[dict] = []

    for spec in manifest.decks:
        rows = compare_deck(spec, args.reference_root, args.candidate_root)
        ranked = sorted(rows, key=lambda row: row["meanAbsoluteDifference"], reverse=True)
        for rank, row in enumerate(ranked[: args.top], 1):
            reference, candidate, difference = row.pop("_images")
            filename = f"{spec.id}-rank-{rank}-page-{row['page']}.png"
            comparison_panel(reference, candidate, difference).save(output / filename)
            row["comparisonPanel"] = filename
        for row in rows:
            row.pop("_images", None)
        report_rows.extend(rows)
        worst = ranked[0]
        print(
            f"{spec.id}: worst page {worst['page']}, "
            f"mean abs diff {worst['meanAbsoluteDifference']:.2%}, "
            f"changed pixels {worst['changedPixelFraction']:.2%}, "
            f"text recall {worst['textRecall']:.2%}"
        )

    report = {
        "schemaVersion": 1,
        "referenceRoot": str(args.reference_root.expanduser().resolve()),
        "candidateRoot": str(args.candidate_root.expanduser().resolve()),
        "pages": report_rows,
    }
    write_text_lf(output / "renderer-comparison.json", json.dumps(report, indent=2) + "\n")
    print(f"Wrote comparison report and panels to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

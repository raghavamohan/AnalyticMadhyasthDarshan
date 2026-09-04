#!/usr/bin/env python3
"""Compare two presentation builds without trusting volatile PDF metadata."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pymupdf as fitz

from _common import BASE, configure_utf8_stdio
from _presentation_pipeline import DeckSpec, load_manifest, manifest_errors, sha256_file


def mapped_path(root: Path, configured: Path) -> Path:
    return root.resolve() / configured.resolve().relative_to(BASE.resolve())


def rendered_content_fingerprint(path: Path) -> str:
    """Hash page geometry, extracted text, and deterministic page rasters."""
    digest = hashlib.sha256()
    with fitz.open(path) as document:
        digest.update(json.dumps({"pages": len(document)}, sort_keys=True).encode())
        for page in document:
            geometry = [round(page.rect.width, 4), round(page.rect.height, 4)]
            digest.update(json.dumps(geometry).encode())
            text = page.get_text("text").replace("\r\n", "\n").replace("\r", "\n")
            digest.update(text.encode("utf-8"))
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            digest.update(f"{pixmap.width}x{pixmap.height}:{pixmap.n}".encode())
            digest.update(pixmap.samples)
    return digest.hexdigest()


def compare_artifact(label: str, left: Path, right: Path) -> list[str]:
    if not left.is_file() or not right.is_file():
        missing = [str(path) for path in (left, right) if not path.is_file()]
        return [f"{label}: missing comparison input: {', '.join(missing)}"]
    left_bytes = sha256_file(left)
    right_bytes = sha256_file(right)
    left_content = rendered_content_fingerprint(left)
    right_content = rendered_content_fingerprint(right)
    print(
        f"{label}: byte-identical={'yes' if left_bytes == right_bytes else 'no'}; "
        f"rendered-content={left_content}"
    )
    if left_content != right_content:
        return [
            f"{label}: rendered/text content differs "
            f"({left_content} != {right_content})"
        ]
    return []


def compare_deck(spec: DeckSpec, left_root: Path, right_root: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(
        compare_artifact(
            f"{spec.id} slides PDF",
            mapped_path(left_root, spec.slides_pdf),
            mapped_path(right_root, spec.slides_pdf),
        )
    )
    errors.extend(
        compare_artifact(
            f"{spec.id} notes PDF",
            mapped_path(left_root, spec.notes_pdf),
            mapped_path(right_root, spec.notes_pdf),
        )
    )
    return errors


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description=(
            "Require stable rendered/text content across two presentation builds; "
            "also report whether each PDF is byte-identical."
        )
    )
    parser.add_argument("--left-root", type=Path, required=True)
    parser.add_argument("--right-root", type=Path, required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true")
    selection.add_argument("--deck", action="append", default=[], metavar="ID")
    args = parser.parse_args(argv)

    manifest = load_manifest()
    errors = manifest_errors(manifest)
    try:
        specs = manifest.decks if args.all else tuple(manifest.deck(item) for item in args.deck)
    except ValueError as exc:
        errors.append(str(exc))
        specs = ()
    for spec in specs:
        errors.extend(compare_deck(spec, args.left_root, args.right_root))

    if errors:
        print("Presentation reproducibility FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Presentation rendered/text content is reproducible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

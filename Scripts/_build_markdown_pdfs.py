#!/usr/bin/env python3
"""Build and verify Markdown-derived generated PDFs into an artifact tree."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from _common import BASE, configure_utf8_stdio
from _generated_pdf_inventory import GeneratedPdfSpec, generated_pdf_specs, inventory_errors
from _presentation_pipeline import repo_relative
from _publish_generated_pdfs import verify_artifacts

SHARED_PIPELINE_PATHS = frozenset({
    "CNAME",
    "requirements.txt",
    "Studies/glossary.json",
    "Scripts/_build_discussion_pages.py",
    "Scripts/_build_markdown_pdfs.py",
    "Scripts/_chrome.js",
    "Scripts/_common.py",
    "Scripts/_convert_to_pdf.py",
    "Scripts/_safe_study_html.py",
    "Scripts/_study_reader.py",
    "Scripts/_study_passages.py",
    "Scripts/_study_search.py",
    "Scripts/_pdf_resource_policy.cjs",
    "Scripts/_generated_pdf_inventory.py",
    "Scripts/_glossary_tooltips.py",
    "Scripts/_html_to_pdf.js",
    "Scripts/_pdf_metadata.py",
    "Scripts/_regenerate_pdf.py",
    "Scripts/_render_katex_math.js",
    "Scripts/_study_catalog.py",
    "Scripts/_verify_pdf_diagrams.py",
    "Scripts/_verify_pdf_fenced_code.py",
    "Scripts/_verify_pdf_math.py",
    "Scripts/_verify_pdf_outline.py",
    "Scripts/_verify_study_svgs.py",
    "Scripts/package.json",
    "Scripts/package-lock.json",
})
SHARED_PIPELINE_PREFIXES = ("Assets/KaTeX/",)
FIGURE_SUFFIXES = (".svg", ".png", ".jpg", ".jpeg", ".webp")


def markdown_specs() -> tuple[GeneratedPdfSpec, ...]:
    return tuple(spec for spec in generated_pdf_specs() if spec.kind == "markdown")


def select_specs(
    changed_paths: tuple[str, ...],
    specs: tuple[GeneratedPdfSpec, ...] | None = None,
) -> tuple[GeneratedPdfSpec, ...]:
    available = specs or markdown_specs()
    changed = {path.replace("\\", "/") for path in changed_paths}
    if any(
        path in SHARED_PIPELINE_PATHS
        or any(path.startswith(prefix) for prefix in SHARED_PIPELINE_PREFIXES)
        for path in changed
    ):
        return available

    selected: list[GeneratedPdfSpec] = []
    for spec in available:
        source = repo_relative(spec.source)
        parent = source.rsplit("/", 1)[0] + "/"
        if source in changed or any(
            path.startswith(parent) and path.lower().endswith(FIGURE_SUFFIXES)
            for path in changed
        ):
            selected.append(spec)
    return tuple(selected)


def changed_paths(base: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        cwd=BASE,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"git diff {base} HEAD failed: {detail}")
    return tuple(line.strip() for line in completed.stdout.splitlines() if line.strip())


def build(specs: tuple[GeneratedPdfSpec, ...], output_root: Path) -> None:
    for spec in specs:
        print(f"Building {spec.key} from {repo_relative(spec.source)}", flush=True)
        subprocess.run(
            [sys.executable, str(BASE / "Scripts" / "_regenerate_pdf.py"), str(spec.source)],
            cwd=BASE,
            check=True,
        )
        target = output_root / Path(spec.key)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spec.output, target)

    verified = verify_artifacts(specs, output_root)
    manifest = {
        "schemaVersion": 1,
        "artifacts": [
            {
                "key": artifact.spec.key,
                "kind": artifact.spec.kind,
                "sha256": artifact.sha256,
                "sourceSha256": artifact.source_sha256,
                "pages": artifact.pages,
            }
            for artifact in verified
        ],
    }
    manifest_path = output_root / "markdown-build-provenance.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Verified {len(verified)} Markdown-derived PDFs")
    print(f"Wrote {manifest_path}")


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true")
    selection.add_argument("--changed-since", metavar="GIT_REF")
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)

    errors = inventory_errors()
    if errors:
        print("Generated PDF inventory errors:\n  - " + "\n  - ".join(errors), file=sys.stderr)
        return 1
    try:
        specs = markdown_specs() if args.all else select_specs(changed_paths(args.changed_since))
        output_root = args.output_root.expanduser().resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        if not specs:
            (output_root / "markdown-build-provenance.json").write_text(
                '{"schemaVersion":1,"artifacts":[]}\n', encoding="utf-8", newline="\n"
            )
            print("No Markdown-derived PDFs selected.")
            return 0
        build(specs, output_root)
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build and verify Markdown-derived generated PDFs into an artifact tree."""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import markdown
from bs4 import BeautifulSoup

from _common import BASE, configure_utf8_stdio
from _generated_pdf_inventory import GeneratedPdfSpec, generated_pdf_specs, inventory_errors
from _presentation_pipeline import repo_relative
from _publish_generated_pdfs import verify_artifacts
from _study_pdf_pipeline import regenerate_pdf, render_status
from _build_inputs import script_dependencies, file_hash
from _study_pdf_metadata import get_pdf_study_row
import hashlib
import platform

SHARED_PIPELINE_PATHS = frozenset({
    "CNAME",
    "requirements.txt",
    "Studies/catalog-applied.json",
    "Studies/catalog-formal.json",
    "Studies/catalog-topical.json",
    "Scripts/_chrome.js",
    "Scripts/_common.py",
    "Scripts/_convert_to_pdf.py",
    "Scripts/_discussion_assets.py",
    "Scripts/_safe_study_html.py",
    "Scripts/_study_reader.py",
    "Scripts/_study_passages.py",
    "Scripts/_study_search.py",
    "Scripts/_build_reader_offline.py",
    "Scripts/_pdf_resource_policy.cjs",
    "Scripts/_generated_pdf_inventory.py",
    "Scripts/_glossary_tooltips.py",
    "Scripts/_html_to_pdf.js",
    "Scripts/_pdf_metadata.py",
    "Scripts/_render_katex_math.js",
    "Scripts/_study_pdf_metadata.py",
    "Scripts/_study_pdf_pipeline.py",
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
FONT_FAMILIES = ("Segoe UI", "Georgia", "Consolas", "system-ui", "sans-serif", "serif", "monospace")


def markdown_specs() -> tuple[GeneratedPdfSpec, ...]:
    return tuple(spec for spec in generated_pdf_specs() if spec.kind == "markdown")


def select_specs(
    changed_paths: tuple[str, ...],
    specs: tuple[GeneratedPdfSpec, ...] | None = None,
    *, base: str | None = None,
) -> tuple[GeneratedPdfSpec, ...]:
    available = specs or markdown_specs()
    changed = {path.replace("\\", "/") for path in changed_paths}
    if any(
        path in SHARED_PIPELINE_PATHS and not path.startswith('Studies/catalog-')
        or any(path.startswith(prefix) for prefix in SHARED_PIPELINE_PREFIXES)
        for path in changed
    ):
        return available

    catalog_slugs = set()
    for name in changed & {p for p in SHARED_PIPELINE_PATHS if p.startswith('Studies/catalog-')}:
        if base is None:
            return available
        before = subprocess.run(['git','show',f'{base}:{name}'],cwd=BASE,capture_output=True,text=True,encoding='utf-8')
        old = {row['slug']:row for row in json.loads(before.stdout or '[]')}
        current = json.loads((BASE/name).read_bytes()) if (BASE/name).is_file() else []
        for row in current:
            if row['status'] in {'draft','released'} and row != old.get(row['slug']):
                catalog_slugs.add(row['slug'])

    selected: list[GeneratedPdfSpec] = []
    for spec in available:
        source = repo_relative(spec.source)
        parent = source.rsplit("/", 1)[0] + "/"
        if spec.source.parent.name in catalog_slugs or source in changed or any(
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


def _catalog_statuses(root: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for path in sorted((root / "Studies").glob("catalog-*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            if row.get("slug") and row.get("status"):
                statuses[str(row["slug"])] = str(row["status"])
    return statuses


def document_link_targets(source: Path, *, root: Path = BASE) -> list[tuple[str, str]]:
    """Describe only local targets referenced by one Markdown document.

    Link rewriting depends on target existence and on whether a catalog study is
    still ongoing.  Tracking every HTML/PDF name in the repository made an
    unrelated new study invalidate every document cache entry.
    """
    md_text = source.read_text(encoding="utf-8")
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code", "smarty"])
    hrefs = {
        unquote(str(anchor["href"]))
        for anchor in BeautifulSoup(html, "html.parser").find_all("a", href=True)
    }
    statuses = _catalog_statuses(root)
    records: dict[str, str] = {}
    collections = (root / "Studies", root / "Applications")
    references = root / "References"
    for href in sorted(hrefs):
        if not href or href.startswith("#"):
            continue
        parsed = urlparse(href)
        if parsed.scheme or parsed.netloc:
            continue
        path_part = unquote(parsed.path)
        if not path_part:
            continue
        candidates = [(source.parent / path_part).resolve()]
        normalized = path_part.replace("\\", "/")
        if normalized.startswith("../References/"):
            candidates.append(
                (source.parent / normalized.replace("../References/", "../../References/", 1)).resolve()
            )
        for candidate in candidates:
            try:
                relative = candidate.relative_to(root).as_posix()
            except ValueError:
                continue
            relevant = candidate.is_relative_to(references) or any(
                candidate.is_relative_to(collection) for collection in collections
            )
            if not relevant:
                continue
            related = {candidate}
            if any(candidate.is_relative_to(collection) for collection in collections):
                related.update(candidate.with_suffix(suffix) for suffix in (".md", ".html", ".pdf"))
                records[f"catalog:{candidate.parent.name}"] = statuses.get(candidate.parent.name, "missing")
            for target in related:
                try:
                    name = target.relative_to(root).as_posix()
                except ValueError:
                    continue
                records[name] = "file" if target.is_file() else "missing"
            records.setdefault(relative, "file" if candidate.is_file() else "missing")
    return sorted(records.items())


@lru_cache(maxsize=1)
def renderer_host_inputs() -> tuple[tuple[str, str], ...]:
    """Fingerprint the actual host fonts used by Chromium, not the runner image."""
    records: list[tuple[str, str]] = []
    executable = shutil.which("fc-match")
    if executable:
        for family in FONT_FAMILIES:
            result = subprocess.run(
                [executable, "--format=%{file}\\n", family],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            for filename in result.stdout.splitlines():
                path = Path(filename.strip())
                if path.is_file():
                    records.append((f"font:{family}:{path.name}", file_hash(path)))
    elif platform.system() == "Windows":
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "georgia.ttf", "consola.ttf", "arial.ttf", "times.ttf", "cour.ttf"):
            path = fonts / name
            if path.is_file():
                records.append((f"font:{name}", file_hash(path)))
    if not records:
        records.extend((
            ("host-image", f'{os.environ.get("ImageOS", os.name)}:{os.environ.get("ImageVersion", "local")}'),
            ("platform-version", platform.version()),
        ))
    return tuple(sorted(set(records)))


def document_fingerprint(spec: GeneratedPdfSpec) -> str:
    dependencies = script_dependencies(BASE, ("_study_pdf_pipeline.py",))
    dependencies.update(SHARED_PIPELINE_PATHS - {name for name in SHARED_PIPELINE_PATHS if name.startswith("Studies/catalog-")})
    dependencies.add(repo_relative(spec.source))
    dependencies.add("References/r2-artifacts.json")
    # Figures in a document's directory are conservative local dependencies.
    dependencies.update(repo_relative(p) for p in spec.source.parent.iterdir() if p.suffix.lower() in FIGURE_SUFFIXES)
    dependencies.update(repo_relative(p) for p in (BASE / "Assets/KaTeX").rglob("*") if p.is_file())
    row = get_pdf_study_row(spec.source.parent.name)
    data = {"files": {name: file_hash(BASE / name) for name in sorted(dependencies) if (BASE / name).is_file()},
            "targets": document_link_targets(spec.source), "status": row.status.value if row else None,
            "description": row.description if row else None,
            "runtime": [sys.version, platform.system(), platform.machine(),
                        subprocess.check_output(["node", "--version"], text=True).strip(), renderer_host_inputs()]}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def build(specs: tuple[GeneratedPdfSpec, ...], output_root: Path, cache_root: Path | None = None) -> None:
    for spec in specs:
        target = output_root / Path(spec.key)
        target.parent.mkdir(parents=True, exist_ok=True)
        fingerprint = document_fingerprint(spec) if cache_root else None
        cached = cache_root / f"{fingerprint}.pdf" if cache_root else None
        seal = cache_root / f"{fingerprint}.json" if cache_root else None
        if cached and cached.is_file() and seal.is_file():
            if json.loads(seal.read_bytes()).get("sha256") != file_hash(cached):
                raise ValueError(f"Corrupt document cache for {spec.key}")
            shutil.copy2(cached, target)
            print(f"Reused verified document inputs: {spec.key}", flush=True)
        else:
            print(f"Building {spec.key} from {repo_relative(spec.source)}", flush=True)
            regenerate_pdf(spec.source, render_status(spec.source))
            shutil.copy2(spec.output, target)
            verify_artifacts((spec,), output_root)
            if cached:
                cache_root.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, cached)
                seal.write_bytes(json.dumps({"sha256": file_hash(cached)}).encode())

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
    parser.add_argument("--cache-root", type=Path, help="Verified document cache restored only from protected-branch builds")
    args = parser.parse_args(argv)

    errors = inventory_errors()
    if errors:
        print("Generated PDF inventory errors:\n  - " + "\n  - ".join(errors), file=sys.stderr)
        return 1
    try:
        specs = markdown_specs() if args.all else select_specs(changed_paths(args.changed_since), base=args.changed_since)
        output_root = args.output_root.expanduser().resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        if not specs:
            (output_root / "markdown-build-provenance.json").write_text(
                '{"schemaVersion":1,"artifacts":[]}\n', encoding="utf-8", newline="\n"
            )
            print("No Markdown-derived PDFs selected.")
            return 0
        build(specs, output_root, args.cache_root)
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

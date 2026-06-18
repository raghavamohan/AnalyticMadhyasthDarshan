"""Build and prune Scripts/_pdf_cache/ for local reference PDFs."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from _common import (
    BASE,
    REFERENCES,
    STUDIES,
    CACHE,
    cache_key_for,
    cache_path_for,
    iter_reference_pdfs,
    load_reference_pages,
    parse_reference_registry,
)
from _quote_verify import extract_quotes_from_markdown


@dataclass
class CacheSyncResult:
    refreshed: list[str] = field(default_factory=list)
    up_to_date: list[str] = field(default_factory=list)
    empty: list[str] = field(default_factory=list)
    missing_source: list[str] = field(default_factory=list)
    pruned: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _study_tag_names(slug: str) -> set[str]:
    tags: set[str] = set()
    md_path = STUDIES / f"{slug}.md"
    if md_path.exists():
        for quote in extract_quotes_from_markdown(md_path):
            tags.update(quote.tags)

    readme = REFERENCES / "README.md"
    if readme.exists():
        pattern = rf"\[{re.escape(slug)}\.pdf\][^|]*\|\s*(.+?)\s*\|"
        match = re.search(pattern, readme.read_text(encoding="utf-8", errors="replace"))
        if match:
            cell = match.group(1)
            for token in re.findall(r"\b([A-Z]{2,3})\b", cell):
                tags.add(token)
            for token in re.findall(r"\b([A-Za-z]+(?:\s+et\s+al\.)?\s+\d{4})\b", cell):
                tags.add(token)
            if "Bhattacharya" in cell:
                tags.add("Bhattacharya")
    return tags


def pdfs_for_study(slug: str) -> list[Path]:
    registry = parse_reference_registry()
    paths: list[Path] = []
    seen: set[Path] = set()
    for tag in sorted(_study_tag_names(slug)):
        path = registry.get(tag)
        if path is None or path.suffix.lower() != ".pdf":
            continue
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            paths.append(resolved)
    return paths


def pdfs_for_tags(tags: set[str]) -> list[Path]:
    registry = parse_reference_registry()
    paths: list[Path] = []
    seen: set[Path] = set()
    for tag in sorted(tags):
        path = registry.get(tag)
        if path is None or path.suffix.lower() != ".pdf":
            continue
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            paths.append(resolved)
    return paths


def sync_pdf_cache(
    paths: list[Path] | None = None,
    *,
    force: bool = False,
    prune: bool = True,
) -> CacheSyncResult:
    """Refresh local PDF text caches and optionally remove stale entries."""
    result = CacheSyncResult()
    targets = paths if paths is not None else iter_reference_pdfs()

    for path in targets:
        rel = path.relative_to(BASE) if path.is_relative_to(BASE) else path
        label = str(rel)
        if not path.exists():
            result.missing_source.append(label)
            continue
        if path.suffix.lower() != ".pdf":
            continue
        try:
            cache_file = cache_path_for(path)
            stale = (
                force
                or not cache_file.exists()
                or cache_file.stat().st_mtime < path.stat().st_mtime
            )
            pages = load_reference_pages(path, force=force)
            if not pages:
                result.empty.append(label)
                continue
            if stale:
                result.refreshed.append(label)
            else:
                result.up_to_date.append(label)
        except (OSError, ValueError) as exc:
            result.errors.append(f"{label}: {exc}")

    if prune:
        valid_keys = {cache_key_for(path) for path in iter_reference_pdfs()}
        CACHE.mkdir(exist_ok=True)
        for cache_file in sorted(CACHE.glob("*.txt")):
            key = cache_file.stem
            if key in valid_keys:
                continue
            cache_file.unlink(missing_ok=True)
            result.pruned.append(key)

    return result


def print_sync_result(result: CacheSyncResult) -> None:
    if result.refreshed:
        print(f"Refreshed ({len(result.refreshed)}):")
        for item in result.refreshed:
            print(f"  {item}")
    if result.up_to_date:
        print(f"Up to date ({len(result.up_to_date)}):")
        for item in result.up_to_date:
            print(f"  {item}")
    if result.empty:
        print(f"No extractable text ({len(result.empty)}):")
        for item in result.empty:
            print(f"  {item}")
    if result.missing_source:
        print(f"Missing source ({len(result.missing_source)}):")
        for item in result.missing_source:
            print(f"  {item}")
    if result.pruned:
        print(f"Pruned orphan caches ({len(result.pruned)}):")
        for item in result.pruned:
            print(f"  {item}")
    if result.errors:
        print(f"Errors ({len(result.errors)}):")
        for item in result.errors:
            print(f"  {item}")


def run_cache_sync(
    *,
    study: str | None = None,
    tags: set[str] | None = None,
    force: bool = False,
    prune: bool = True,
) -> int:
    if study and tags:
        raise SystemExit("Use only one of --study or --tags.")

    paths: list[Path] | None
    if study:
        slug = study.removesuffix(".md")
        paths = pdfs_for_study(slug)
        if not paths:
            print(f"No local PDF references found for study {slug!r}.")
    elif tags:
        paths = pdfs_for_tags(tags)
        if not paths:
            print(f"No local PDF files found for tags: {', '.join(sorted(tags))}")
    else:
        paths = None

    result = sync_pdf_cache(paths, force=force, prune=prune)
    print_sync_result(result)
    if result.errors and not (result.refreshed or result.up_to_date):
        return 1
    return 0

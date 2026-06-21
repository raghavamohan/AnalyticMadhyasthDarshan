"""Blockquote verification against local References/ files."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from _common import (
    AUTHOR_YEAR_PREFIXES,
    REFERENCES,
    STUDIES,
    TAG_ABBREVS,
    cache_key_for,
    find_phrase,
    iter_study_md_paths,
    load_reference_pages,
    parse_reference_registry,
)

QUOTE_LINE = re.compile(r'^>\s*\*\*[“"](.+?)[”"]\*\*\s*$')
ATTR_LINE = re.compile(r'^>\s*[-—]\s*(.+)$')
AUTHOR_YEAR_TAG = re.compile(
    rf"\b({'|'.join(AUTHOR_YEAR_PREFIXES)})\s+(\d{{4}})\b"
)


@dataclass(frozen=True)
class ExtractedQuote:
    study: str
    phrase: str
    attribution: str | None
    tags: tuple[str, ...]


def clean_quote_text(text: str) -> str:
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = text.replace("…", "...")
    return text.strip()


def parse_tags_from_attribution(line: str) -> list[str]:
    text = ATTR_LINE.sub(r"\1", line).strip()
    tags: list[str] = []
    for match in AUTHOR_YEAR_TAG.finditer(text):
        tag = f"{match.group(1)} {match.group(2)}"
        if tag not in tags:
            tags.append(tag)
    for match in re.finditer(r"\b(" + "|".join(TAG_ABBREVS) + r")\b", text):
        tag = match.group(1)
        if tag not in tags:
            tags.append(tag)
    return tags


def extract_quotes_from_markdown(path: Path) -> list[ExtractedQuote]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    quotes: list[ExtractedQuote] = []
    index = 0
    while index < len(lines):
        match = QUOTE_LINE.match(lines[index])
        if match:
            phrase = clean_quote_text(match.group(1))
            attribution: str | None = None
            tags: tuple[str, ...] = ()
            if index + 1 < len(lines) and ATTR_LINE.match(lines[index + 1]):
                attribution = lines[index + 1]
                tags = tuple(parse_tags_from_attribution(attribution))
                index += 1
            quotes.append(
                ExtractedQuote(
                    study=path.stem,
                    phrase=phrase,
                    attribution=attribution,
                    tags=tags,
                )
            )
        index += 1
    return quotes


def load_corpora(
    registry: dict[str, Path],
    tags_needed: set[str],
) -> dict[str, list[tuple[int, str]]]:
    by_path: dict[Path, list[tuple[int, str]]] = {}
    corpora: dict[str, list[tuple[int, str]]] = {}
    for tag in sorted(tags_needed):
        path = registry.get(tag)
        if path is None:
            continue
        if path not in by_path:
            print(f"Loading {path.relative_to(REFERENCES.parent)}...", flush=True)
            by_path[path] = load_reference_pages(path, cache_key_for(path))
            print(f"  {len(by_path[path])} page(s)", flush=True)
        corpora[tag] = by_path[path]
    return corpora


def verify_quote(
    quote: ExtractedQuote,
    registry: dict[str, Path],
    corpora: dict[str, list[tuple[int, str]]],
) -> tuple[str, str | None, list[str]]:
    if not quote.tags:
        return "SKIP_NO_TAG", None, []

    expected = quote.tags[0]
    if expected not in registry:
        return "SKIP_NO_LOCAL_FILE", expected, []

    pages = corpora[expected]
    hit = find_phrase(pages, quote.phrase)
    other_hits: list[str] = []
    if not hit or hit.startswith("PARTIAL"):
        for tag, alt_pages in corpora.items():
            if tag == expected:
                continue
            alt = find_phrase(alt_pages, quote.phrase)
            if alt and not alt.startswith("PARTIAL"):
                other_hits.append(f"{tag}:{alt}")

    if hit and not hit.startswith("PARTIAL"):
        return "OK", f"{expected}:{hit}", other_hits
    if hit and hit.startswith("PARTIAL"):
        return "PARTIAL", f"{expected}:{hit}", other_hits
    if other_hits:
        return "WRONG_SOURCE", None, other_hits
    return "NOT_FOUND", None, other_hits


def collect_quotes(study_filter: str | None) -> list[ExtractedQuote]:
    paths = iter_study_md_paths()
    if study_filter:
        slug = study_filter.removesuffix(".md")
        paths = [path for path in paths if path.parent.name == slug]
        if not paths:
            raise SystemExit(f"No study markdown found for: {study_filter}")
    quotes: list[ExtractedQuote] = []
    for path in paths:
        quotes.extend(extract_quotes_from_markdown(path))
    return quotes


def run_verify(study_filter: str | None = None, tag_filter: set[str] | None = None) -> int:
    registry = parse_reference_registry()
    if tag_filter:
        registry = {tag: path for tag, path in registry.items() if tag in tag_filter}

    quotes = collect_quotes(study_filter)
    if tag_filter:
        quotes = [quote for quote in quotes if quote.tags and quote.tags[0] in tag_filter]

    tags_needed = {quote.tags[0] for quote in quotes if quote.tags and quote.tags[0] in registry}
    if tag_filter:
        tags_needed &= tag_filter

    print(f"Reference tags with local files: {', '.join(sorted(registry))}")
    print(f"Blockquotes to check: {len(quotes)}")
    print(f"Loading sources for tags: {', '.join(sorted(tags_needed)) or '(none)'}\n")

    corpora = load_corpora(registry, tags_needed)

    counts = {
        "OK": 0,
        "PARTIAL": 0,
        "WRONG_SOURCE": 0,
        "NOT_FOUND": 0,
        "SKIP_NO_TAG": 0,
        "SKIP_NO_LOCAL_FILE": 0,
    }

    print("=== VERIFICATION RESULTS ===\n")
    for quote in quotes:
        status, found, other_hits = verify_quote(quote, registry, corpora)
        counts[status] += 1

        if status.startswith("SKIP"):
            print(f"[{status}] ({quote.study}) {quote.phrase[:70]}...")
            if status == "SKIP_NO_LOCAL_FILE":
                print(f"         tag {found} has no local file in References/")
            print()
            continue

        print(f"[{status}] ({quote.study} / exp {quote.tags[0]}) {quote.phrase[:70]}...")
        if found:
            print(f"         found: {found}")
        if other_hits:
            print(f"         alt:   {', '.join(other_hits)}")
        print()

    checked = counts["OK"] + counts["PARTIAL"] + counts["WRONG_SOURCE"] + counts["NOT_FOUND"]
    print(
        "Summary: "
        f"checked={checked} "
        f"OK={counts['OK']} "
        f"PARTIAL={counts['PARTIAL']} "
        f"WRONG_SOURCE={counts['WRONG_SOURCE']} "
        f"NOT_FOUND={counts['NOT_FOUND']} "
        f"skipped_no_tag={counts['SKIP_NO_TAG']} "
        f"skipped_no_local_file={counts['SKIP_NO_LOCAL_FILE']}"
    )
    return 0

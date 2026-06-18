"""Quote verification and PDF text research.

Usage:
    python Scripts/_quote_tool.py verify [--study Slug] [--tags MVD,SB]
    python Scripts/_quote_tool.py search <pdf> "<regex>"
    python Scripts/_quote_tool.py page <pdf> <page> [--keyword kw]
    python Scripts/_quote_tool.py snippet <tag> "<phrase>"
"""
from __future__ import annotations

import argparse
import re
import sys

from pypdf import PdfReader

from _common import (
    chapter_map,
    extract_pdf_page_text,
    find_phrase,
    load_reference_pages,
    norm,
    parse_reference_registry,
)
from _quote_verify import cache_key_for, run_verify


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        print(text.encode(encoding, errors="replace").decode(encoding))


def load_pdf(pdf_path: str) -> PdfReader:
    return PdfReader(pdf_path)


def raw_page_text(reader: PdfReader, index: int) -> str:
    try:
        return reader.pages[index].extract_text() or ""
    except Exception as exc:
        return f"[extract error: {exc}]"


def cmd_search(pdf: str, pattern: str) -> None:
    reader = load_pdf(pdf)
    rx = re.compile(pattern, re.IGNORECASE)
    hits = 0
    for index, _ in enumerate(reader.pages):
        text = extract_pdf_page_text(raw_page_text(reader, index))
        for match in rx.finditer(text):
            start = max(0, match.start() - 120)
            end = min(len(text), match.end() + 120)
            snippet = text[start:end]
            safe_print(f"[p.{index + 1}] ...{snippet}...")
            hits += 1
    safe_print(f"\n{hits} match(es) in {len(reader.pages)} pages.")


def cmd_pages(pdf: str, start: int, end: int | None = None) -> None:
    reader = load_pdf(pdf)
    end = start if end is None else end
    for index in range(start - 1, min(end, len(reader.pages))):
        safe_print(f"\n===== PAGE {index + 1} =====")
        safe_print(extract_pdf_page_text(raw_page_text(reader, index)))


def snippet_around(text: str, keyword: str, before: int = 300, after: int = 300) -> str | None:
    match = re.search(keyword, text, re.IGNORECASE)
    if not match:
        return None
    return text[max(0, match.start() - before) : match.end() + after]


def cmd_page(pdf: str, page: int, keyword: str | None) -> None:
    reader = load_pdf(pdf)
    cleaned = extract_pdf_page_text(raw_page_text(reader, page - 1))
    if keyword:
        snippet = snippet_around(cleaned, keyword)
        safe_print(snippet if snippet else "[not found]")
        safe_print(f"\n--- (cleaned page length: {len(cleaned)} chars) ---")
    else:
        safe_print(cleaned)


def find_snippet(
    pages: list[tuple[int, str]],
    phrase: str,
    width: int = 260,
) -> str:
    nphrase = norm(phrase)
    for page_num, text in pages:
        ntext = norm(text)
        index = ntext.find(nphrase)
        if index != -1:
            ratio = len(text) / max(len(ntext), 1)
            start = max(0, int(index * ratio) - 80)
            end = min(len(text), int((index + len(nphrase)) * ratio) + width)
            snippet = re.sub(r"\s+", " ", text[start:end])
            return f"p{page_num} | {snippet}"
    hit = find_phrase(pages, phrase)
    if hit and not hit.startswith("PARTIAL"):
        return f"{hit} | (spans pages or partial context unavailable)"
    return "NOT FOUND"


def cmd_snippet(tag: str, phrase: str) -> None:
    registry = parse_reference_registry()
    path = registry.get(tag)
    if path is None:
        raise SystemExit(f"Unknown tag or no local file: {tag}")
    pages = load_reference_pages(path, cache_key_for(path))
    result = find_snippet(pages, phrase)
    if tag == "MVD" and result.startswith("p"):
        page_num = int(result.split("|", 1)[0].strip().removeprefix("p"))
        result = f"{result} | {chapter_map(pages).get(page_num, '?')}"
    safe_print(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Quote verification and PDF text research.")
    sub = parser.add_subparsers(dest="command", required=True)

    verify_p = sub.add_parser("verify", help="Verify Studies blockquotes against References/")
    verify_p.add_argument("--study", help="Study slug (markdown stem)")
    verify_p.add_argument("--tags", help="Comma-separated citation tags")

    search_p = sub.add_parser("search", help="Regex search a PDF (cleaned text)")
    search_p.add_argument("pdf", help="Path to PDF")
    search_p.add_argument("pattern", help="Regex pattern")

    page_p = sub.add_parser("page", help="Print one PDF page (cleaned text)")
    page_p.add_argument("pdf", help="Path to PDF")
    page_p.add_argument("page", type=int, help="1-based page number")
    page_p.add_argument("--keyword", help="Print window around keyword instead of full page")

    snippet_p = sub.add_parser("snippet", help="Find phrase in a tagged reference")
    snippet_p.add_argument("tag", help="Citation tag (e.g. MVD, SB)")
    snippet_p.add_argument("phrase", help="Phrase to locate")

    args = parser.parse_args()

    if args.command == "verify":
        tag_filter = {t.strip() for t in args.tags.split(",")} if args.tags else None
        raise SystemExit(run_verify(args.study, tag_filter))
    if args.command == "search":
        cmd_search(args.pdf, args.pattern)
        return
    if args.command == "page":
        cmd_page(args.pdf, args.page, args.keyword)
        return
    if args.command == "snippet":
        cmd_snippet(args.tag, args.phrase)
        return

    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()

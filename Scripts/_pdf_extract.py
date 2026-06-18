"""Extract text from Madhyasth Darshan / Advaita PDFs and search for terms/pages.

Usage:
    python _pdf_extract.py search <pdf> "<regex>"
    python _pdf_extract.py pages <pdf> <start> <end>          # 1-based page numbers
    python _pdf_extract.py pages <pdf> <n>                     # single page
"""
import re
import sys

import pypdf


def load(pdf_path):
    return pypdf.PdfReader(pdf_path)


def page_text(reader, i):  # i is 0-based
    try:
        return reader.pages[i].extract_text() or ""
    except Exception as e:
        return f"[extract error: {e}]"


def norm(s):
    # Normalize whitespace and ligatures for cleaner search/display
    return (
        s.replace("\u00a0", " ")
        .replace("\ufb01", "fi")
        .replace("\ufb02", "fl")
        .replace("\ufb00", "ff")
        .replace("\ufb03", "ffi")
        .replace("\ufb04", "ffl")
    )


def cmd_search(pdf, pattern):
    reader = load(pdf)
    rx = re.compile(pattern, re.IGNORECASE)
    hits = 0
    for i, _ in enumerate(reader.pages):
        text = norm(page_text(reader, i))
        for m in rx.finditer(text):
            start = max(0, m.start() - 120)
            end = min(len(text), m.end() + 120)
            snippet = text[start:end].replace("\n", " ")
            print(f"[p.{i+1}] ...{snippet}...")
            hits += 1
    print(f"\n{hits} match(es) in {len(reader.pages)} pages.")


def cmd_pages(pdf, start, end=None):
    reader = load(pdf)
    end = start if end is None else end
    for i in range(start - 1, min(end, len(reader.pages))):
        print(f"\n===== PAGE {i+1} =====")
        print(norm(page_text(reader, i)))


def main():
    cmd = sys.argv[1]
    if cmd == "search":
        cmd_search(sys.argv[2], sys.argv[3])
    elif cmd == "pages":
        start = int(sys.argv[3])
        end = int(sys.argv[4]) if len(sys.argv) > 4 else None
        cmd_pages(sys.argv[2], start, end)
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()

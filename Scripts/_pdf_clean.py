"""Clean PDF text where each word sits on its own 'line' with large gaps.

Collapses single-word-per-line artifacts into normal prose and prints a
contiguous window around a keyword (case-insensitive), with full page output
as a fallback.
"""
import re
import sys

sys.path.insert(0, "Scripts")
from _pdf_extract import load, page_text, norm


def clean(t):
    # Replace runs of 2+ spaces (the word-per-token artifact) with single space.
    t = re.sub(r"[ \t]{2,}", " ", t)
    # Join lines: collapse newline + spaces into single space, but keep
    # paragraph-ish breaks (blank lines) rare here. Heuristic: treat all
    # newlines as soft wraps.
    t = re.sub(r"\s*\n\s*", " ", t)
    t = re.sub(r" {2,}", " ", t)
    return t.strip()


def around(t, kw, before=300, after=300):
    m = re.search(kw, t, re.IGNORECASE)
    if not m:
        return None
    return t[max(0, m.start() - before) : m.end() + after]


def main():
    pdf = sys.argv[1]
    page = int(sys.argv[2])  # 1-based
    kw = sys.argv[3] if len(sys.argv) > 3 else None
    r = load(pdf)
    raw = norm(page_text(r, page - 1))
    cleaned = clean(raw)
    if kw:
        snip = around(cleaned, kw)
        print(snipped if (snipped := snip) else "[not found]")
        print("\n--- (cleaned page length: %d chars) ---" % len(cleaned))
    else:
        print(cleaned)


if __name__ == "__main__":
    main()

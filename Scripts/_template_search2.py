"""Second pass: targeted passages for the unit-assembly template paper."""
import re

from _common import SCRIPTS, chapter_map, load_pages

QUERIES = {
    "MVD": [
        "hungry",
        "overfull",
        "ten-tier",
        "ten staged",
        "family based",
        "self-governance",
        "exchange",
        "balance",
        "environment",
        "participation in the overall",
        "inherent orderliness",
        "weight",
        "gravitational",
        "tendency to form",
        "multicellular",
        "organism",
    ],
    "JV": [
        "environment",
        "participation",
        "balance",
        "exchange",
        "organism",
        "multicellular",
        "food for food",
        "orbit",
    ],
    "SB": [
        "coexistence",
        "development",
        "atom",
        "value",
        "tradition",
        "environment",
    ],
}

WINDOW = 280
MAX_HITS = 5

out_lines: list[str] = []
for key, terms in QUERIES.items():
    pages = load_pages(key)
    chapters = chapter_map(pages)
    out_lines.append(f"\n{'='*20} SOURCE {key} ({len(pages)} pages) {'='*20}\n")
    for term in terms:
        hits = 0
        out_lines.append(f"\n----- TERM: {term} -----")
        for page_num, text in pages:
            # Keep ASCII and Devanagari only, so the output file stays readable text
            text = re.sub(r"[^\x20-\x7e\u0900-\u097F\s]", " ", text)
            flat = re.sub(r"\s+", " ", text)
            m = re.search(re.escape(term), flat, re.IGNORECASE)
            if m:
                snippet = flat[max(0, m.start() - WINDOW) : m.start() + WINDOW]
                out_lines.append(f"[{key} p{page_num} {chapters[page_num]}] ...{snippet}...")
                hits += 1
            if hits >= MAX_HITS:
                break
        if hits == 0:
            out_lines.append("(no hits)")

(SCRIPTS / "_template_search2.txt").write_text("\n".join(out_lines), encoding="utf-8")
print(f"Wrote {SCRIPTS / '_template_search2.txt'}")

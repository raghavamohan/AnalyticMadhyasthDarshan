"""Extract context windows for unit-assembly template research from JV and MVD caches.

Archived research script — outputs under Scripts/research/.
"""
import re

import _bootstrap
from _bootstrap import RESEARCH
from _common import chapter_map, load_pages

TERMS = [
    "coexistence",
    "saturated",
    "submerged",
    "energised",
    "definite conduct",
    "regulated and conserved",
    "established value",
    "relationship",
    "justice",
    "trust",
    "respect",
    "recognis",
    "fulfil",
    "usefulness",
    "complementarin",
    "developmental progression",
    "constitution",
    "atom",
    "molecule",
    "cell",
    "order",
    "lineage",
    "seed",
    "sanskar",
    "tradition",
    "generation",
    "family",
    "village",
    "world family",
    "undivided society",
    "universal order",
    "evaluation",
    "mutual fulfilment",
]

WINDOW = 260
MAX_HITS_PER_TERM = 6

out_lines: list[str] = []
for key in ["JV", "MVD"]:
    pages = load_pages(key)
    chapters = chapter_map(pages)
    out_lines.append(f"\n{'='*20} SOURCE {key} {'='*20}\n")
    for term in TERMS:
        hits = 0
        out_lines.append(f"\n----- TERM: {term} -----")
        for page_num, text in pages:
            flat = re.sub(r"\s+", " ", text)
            for m in re.finditer(re.escape(term), flat, re.IGNORECASE):
                snippet = flat[max(0, m.start() - WINDOW) : m.start() + WINDOW]
                out_lines.append(f"[{key} p{page_num} {chapters[page_num]}] ...{snippet}...")
                hits += 1
                break  # one hit per page
            if hits >= MAX_HITS_PER_TERM:
                break
        if hits == 0:
            out_lines.append("(no hits)")

(RESEARCH / "_template_search.txt").write_text("\n".join(out_lines), encoding="utf-8")
print(f"Wrote {RESEARCH / '_template_search.txt'}")

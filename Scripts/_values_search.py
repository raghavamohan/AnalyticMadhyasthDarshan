"""Extract the value taxonomy (established/expressed values, justice, trust chain)."""
import re

from _common import SCRIPTS, chapter_map, load_pages

TERMS = [
    "established value",
    "expressed value",
    "sthapit",
    "shisht",
    "Trust ( vishwas",
    "Justice ( nyaya",
    "Respect ( samman",
    "Affection ( sneha",
    "Gratitude",
    "Reverence",
    "Glory ( gaurav",
    "Affinity",
    "mam??",
    "nine values",
    "human values",
    "jeevan values",
    "civic value",
    "value ( mulya",
    "leads to trust",
    "affection leads",
    "trust leads",
    "inherent expectation of values",
    "manifested through relationships",
]

WINDOW = 320
MAX_HITS = 4

out_lines: list[str] = []
for key in ["MVD", "JV"]:
    pages = load_pages(key)
    chapters = chapter_map(pages)
    out_lines.append(f"\n{'='*18} {key} {'='*18}")
    for term in TERMS:
        hits = 0
        out_lines.append(f"\n--- {term} ---")
        for page_num, text in pages:
            text2 = re.sub(r"[^\x20-\x7e\u0900-\u097F\s]", " ", text)
            flat = re.sub(r"\s+", " ", text2)
            m = re.search(re.escape(term), flat, re.IGNORECASE)
            if m:
                snip = flat[max(0, m.start() - WINDOW): m.start() + WINDOW]
                out_lines.append(f"[{key} p{page_num} {chapters[page_num]}] ...{snip}...")
                hits += 1
            if hits >= MAX_HITS:
                break
        if hits == 0:
            out_lines.append("(none)")

(SCRIPTS / "_values_search.txt").write_text("\n".join(out_lines), encoding="utf-8")
print("wrote Scripts/_values_search.txt")

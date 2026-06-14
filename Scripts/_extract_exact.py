"""Extract exact-quote snippets (with page and chapter) from the MVD cache."""
import re

from _common import SCRIPTS, chapter_map, load_pages

pages = load_pages("MVD")
chapters = chapter_map(pages)

patterns = [
    "Trust ( vishwas )",
    "Justice ( nyaya )",
    "Exploitation ( shoshan )",
    "Material prosperity is accomplished",
    "earning for expenditure",
    "Sociality gives rise to needs",
    "Fulfilling the values inherent in relationships",
    "Sociality:",
]

lines: list[str] = []
for pattern in patterns:
    found = False
    for page_num, text in pages:
        idx = text.find(pattern)
        if idx == -1:
            idx = text.lower().find(pattern.lower())
        if idx != -1:
            snippet = re.sub(r"\s+", " ", text[max(0, idx - 40) : idx + 220])
            lines.append(
                f"--- {pattern} | p{page_num} | {chapters[page_num]} ---\n{snippet}\n"
            )
            found = True
            break
    if not found:
        lines.append(f"--- {pattern}: NOT FOUND ---\n")

(SCRIPTS / "_exact_quotes.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {SCRIPTS / '_exact_quotes.txt'}")

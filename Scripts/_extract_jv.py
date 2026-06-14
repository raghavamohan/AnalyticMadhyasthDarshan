"""Extract exact-quote snippets (with page) from the JV cache."""
import re

from _common import SCRIPTS, load_pages

pages = load_pages("JV")

patterns = [
    "religion-based-governance",
    "economics-based-governance",
    "thought about thus far",
    "conflict, revolt, exploitation, and war",
    "revolts, rebellions, exploitations, and wars",
    "The alternative path is",
    "perform study, attain mastery",
    "values and evaluation",
    "fear and temptation",
    "dos and don'ts",
    "labelling non-believers",
    "theocratic",
]

lines: list[str] = []
for pattern in patterns:
    found = False
    for page_num, text in pages:
        if pattern.lower() in text.lower():
            idx = text.lower().find(pattern.lower())
            snippet = re.sub(r"\s+", " ", text[max(0, idx - 60) : idx + 260])
            lines.append(f"--- {pattern} | p{page_num} ---\n{snippet}\n")
            found = True
            break
    if not found:
        lines.append(f"--- {pattern}: NOT FOUND ---\n")

(SCRIPTS / "_jv_exact_quotes.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {SCRIPTS / '_jv_exact_quotes.txt'}")

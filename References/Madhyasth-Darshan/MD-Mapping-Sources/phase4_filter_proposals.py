"""Filter Phase 4 auto-proposals to keep only high-confidence glossary rows."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'\-/]*")

NUMBER_WORDS = {
    "एक",
    "दो",
    "तीन",
    "चार",
    "पाँच",
    "पांच",
    "छह",
    "सात",
    "आठ",
    "नौ",
    "दस",
    "ग्यारह",
    "बारह",
}
BAD_TOKENS = {
    "जब",
    "तब",
    "बात",
    "नागराज",
    "करेंगे।",
    "देना",
    "रहित",
    "संभव",  # too generic; gloss was a full sentence
    "सफल",
    "सुलभ",
    "अध्याय",
    "युद्घ",  # OCR/spelling of युद्ध; gloss wrong
    "सिद्घ",
}
BAD_ENGLISH_PREFIXES = (
    "chapter-",
    "chapter ",
    "may ",
    "according to",
    "buddhi has",
    "the elimination",
    "the activity process",
    "the life of a parent",
    "national life is",
    "human history from",
    "it is evident",
    "every human",
    "when an atom",
    "omnpresence",
    "omnipresence is",
    "knowledge leads",
    "allocating",
)


def word_count(english: str) -> int:
    return len(LATIN_WORD.findall(english))


def keep(row: dict) -> tuple[bool, str]:
    token = row["token"]
    english = row["english"].strip()
    method = row["method"]
    lemma = row["hindi_lemma"]

    if token in NUMBER_WORDS or any(t in NUMBER_WORDS for t in lemma.split(",")):
        return False, "number-word"
    if token in BAD_TOKENS:
        return False, "bad-token"
    if "।" in token or token.endswith("।"):
        return False, "punctuation-token"
    low = english.lower().strip()
    if any(low.startswith(p) for p in BAD_ENGLISH_PREFIXES):
        return False, "bad-english-prefix"
    if low in {"big", "world", "mirage", "kindness", "jeevan", "accessible", "inherent", "the refuge"}:
        return False, "implausible-gloss"
    wc = word_count(english)
    if method == "quoted" and wc <= 5:
        return True, "ok-quoted"
    if method == "definitional" and 1 <= wc <= 6:
        return True, "ok-definitional"
    if method == "title-case" and 1 <= wc <= 4 and english[:1].isupper():
        # Avoid single generic nouns unless multiword technical
        if wc == 1 and low in {"kindness", "allocating", "inherent", "humaneness"}:
            return False, "weak-title"
        return True, "ok-title"
    if method == "short-unit" and 1 <= wc <= 4:
        return True, "ok-short"
    if method == "compact" and 1 <= wc <= 3:
        return True, "ok-compact"
    return False, f"too-noisy:{method}:{wc}"


def main() -> None:
    src = HERE / "phase4_new_rows.json"
    rows = json.loads(src.read_text(encoding="utf-8"))
    kept: list[dict] = []
    dropped: list[dict] = []
    for row in rows:
        ok, reason = keep(row)
        if ok:
            kept.append(row)
        else:
            dropped.append({**row, "filter_reason": reason})
    out = HERE / "phase4_new_rows_filtered.json"
    out.write_text(json.dumps(kept, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    (HERE / "phase4_auto_dropped.json").write_text(
        json.dumps(dropped, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"kept={len(kept)} dropped={len(dropped)} -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()

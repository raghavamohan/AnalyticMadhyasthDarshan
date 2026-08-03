#!/usr/bin/env python3
"""Clean Tier-1 raw ASR sidecars without overwriting decoder dumps.

Writes beside each *-raw-asr.txt:

  <stem>-cleaned.txt
  <stem>-clean-log.json

Fixes (deterministic):

  1. D11 YouTube boilerplate deletion (_transcribe_review.BOILERPLATE)
  2. Consecutive-token collapse (same token ≥ N times → one; logged)
  3. U+FFFD left in place; offsets logged (never auto-guessed)
  4. Context-free ASR normalisations from the 2010 Conventions list

    python Scripts/_clean_tier1_raw_asr.py
    python Scripts/_clean_tier1_raw_asr.py --root E:\\MD-Transcription\\Nagraj-Recorded-Sessions
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _transcribe_review import BOILERPLATE  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
# Unpromoted Tier-1 corpus lives outside the repo (promoted 2010 session stays in References).
DEFAULT_ROOT = Path(r"E:\MD-Transcription\Nagraj-Recorded-Sessions")
REPEAT_N = 5

# Context-free only — same list as the 2010 session Conventions (unambiguous).
NORMALISATIONS = [
    (re.compile(r"साक्षात\s*कार|सक्षात\s*कर|साक्षातकार"), "साक्षात्कार"),
    (re.compile(r"अन्भव|अनुभव़"), "अनुभव"),
    (re.compile(r"अध्येन|अध्यान|अधेन"), "अध्ययन"),
    (re.compile(r"स्विकार"), "स्वीकार"),
    (re.compile(r"सुभाव"), "स्वभाव"),
    (re.compile(r"वस्तो"), "वस्तु"),
    (re.compile(r"दृष्टापत|दर्श्टापद|दर्श्टा"), "दृष्टापद"),
    (re.compile(r"सायम"), "संयम"),
    (re.compile(r"समाधी"), "समाधि"),
    (re.compile(r"जिग्यासा"), "जिज्ञासा"),
    (re.compile(r"अन्संधान|अनुसन्धान"), "अनुसंधान"),
    (re.compile(r"तिब्रता"), "तीव्रता"),
    (re.compile(r"वस्ता"), "अवस्था"),
    (re.compile(r"सहास्तित्व|सहअस्तित्व"), "सह-अस्तित्व"),
    (re.compile(r"इन्द्रियगोचर|इंद्रियगोचर"), "इन्द्रिय-गोचर"),
    (re.compile(r"ज्ञानगोचर|ग्‍यानगोचर"), "ज्ञान-गोचर"),
]


def collapse_repeats(text: str, n: int = REPEAT_N) -> tuple[str, list[dict]]:
    words = text.split()
    out: list[str] = []
    events: list[dict] = []
    i = 0
    while i < len(words):
        j = i + 1
        while j < len(words) and words[j] == words[i]:
            j += 1
        run = j - i
        if run >= n:
            events.append({"token": words[i], "run": run, "at_word": len(out)})
            out.append(words[i])
        else:
            out.extend(words[i:j])
        i = j
    return " ".join(out), events


def clean_text(text: str) -> tuple[str, dict]:
    log: dict = {
        "boilerplate_hits": 0,
        "boilerplate_spans": [],
        "repeat_collapses": [],
        "fffd_offsets": [],
        "normalisations": [],
    }

    for m in BOILERPLATE.finditer(text):
        log["boilerplate_spans"].append({"start": m.start(), "end": m.end(), "text": m.group(0)})
    text2, n_sub = BOILERPLATE.subn(" ", text)
    log["boilerplate_hits"] = n_sub
    text2 = re.sub(r"[ \t]{2,}", " ", text2)
    text2 = re.sub(r" *\n *", "\n", text2)

    text3, events = collapse_repeats(text2)
    log["repeat_collapses"] = events

    for m in re.finditer("\ufffd", text3):
        log["fffd_offsets"].append(m.start())

    text4 = text3
    for pat, repl in NORMALISATIONS:
        text4, c = pat.subn(repl, text4)
        if c:
            log["normalisations"].append({"pattern": pat.pattern, "replacement": repl, "count": c})

    return text4, log


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--repeat-n", type=int, default=REPEAT_N)
    args = ap.parse_args()

    raws = sorted(args.root.rglob("*-raw-asr.txt"))
    # Skip the pre-Tier-1 promoted session's raw file name pattern without --vid
    tier = [p for p in raws if "--" in p.parent.name]
    if not tier:
        sys.exit(f"no Tier-1 *-raw-asr.txt under {args.root}")

    totals = {"files": 0, "boiler": 0, "collapses": 0, "fffd": 0, "norms": 0}
    for raw in tier:
        stem = raw.name[: -len("-raw-asr.txt")]
        text = raw.read_text(encoding="utf-8", errors="replace")
        cleaned, log = clean_text(text)
        # honour --repeat-n if different (re-run collapse only when needed)
        if args.repeat_n != REPEAT_N:
            cleaned, events = collapse_repeats(
                BOILERPLATE.sub(" ", text), args.repeat_n
            )
            log["repeat_collapses"] = events

        out_txt = raw.with_name(f"{stem}-cleaned.txt")
        out_log = raw.with_name(f"{stem}-clean-log.json")
        out_txt.write_text(cleaned, encoding="utf-8", newline="\n")
        out_log.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8", newline="\n")

        totals["files"] += 1
        totals["boiler"] += log["boilerplate_hits"]
        totals["collapses"] += len(log["repeat_collapses"])
        totals["fffd"] += len(log["fffd_offsets"])
        totals["norms"] += sum(x["count"] for x in log["normalisations"])
        print(f"  cleaned {stem}  boiler={log['boilerplate_hits']} "
              f"collapses={len(log['repeat_collapses'])} "
              f"fffd={len(log['fffd_offsets'])}", flush=True)

    print(f"\nDONE {totals['files']} files | boilerplate removals={totals['boiler']} "
          f"| collapse events={totals['collapses']} | FFFD logged={totals['fffd']} "
          f"| normalisation hits={totals['norms']}", flush=True)


if __name__ == "__main__":
    main()

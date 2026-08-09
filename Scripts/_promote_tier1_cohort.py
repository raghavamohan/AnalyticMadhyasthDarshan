#!/usr/bin/env python3
"""Promote a Tier-1 cohort of cleaned ASR files to 2010-shaped bilingual .md.

Uses:
  - *-cleaned.txt (Layer A) as Hindi source — never overwrites *-raw-asr.txt
  - accepted TERMINOLOGY-REGISTRY.json entries + curated phrase overrides for
    English authorities; provisional/disputed entries remain review-only
  - deep-translator (Google) for continuous working English, with technical
    terms protected by placeholders so MT cannot rename dharma→religion etc.

Timestamps are approximate (word-rate × duration); labelled as such.

    python Scripts/_promote_tier1_cohort.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:  # pragma: no cover
    GoogleTranslator = None  # type: ignore

BASE = Path(__file__).resolve().parent.parent
# Unpromoted Tier-1 corpus lives outside the repo.
SESSIONS = Path(r"E:\MD-Transcription\Nagraj-Recorded-Sessions")
TERMINOLOGY = SESSIONS / "TERMINOLOGY.md"
TERMINOLOGY_REGISTRY = SESSIONS / "TERMINOLOGY-REGISTRY.json"

COHORT = {
    "LHmuCc4NveA": {
        "title_hi": "साक्षात्कार – बोध – अनुभव",
        "title_en": "Sakshatkar – Bodh – Anubhav",
        "study": "SPR",
        "dur": "1:30:20",
    },
    "8WNTuXNtawg": {
        "title_hi": "न्याय – धर्म – सत्य",
        "title_en": "Justice – Dharma – Truth",
        "study": "SPR",
        "dur": "56:22",
    },
    "kZ6qdNflDWA": {
        "title_hi": "भाषा – अर्थ – वस्तु",
        "title_en": "Language – Meaning – Vastu",
        "study": "EPI",
        "dur": "36:20",
    },
    "Di8YkI5Olzo": {
        "title_hi": "समाधि-संयम पूर्वक गठनपूर्णता, क्रियापूर्णता, आचरण पूर्णता का अनुसंधान",
        "title_en": "Exploration of constitution-completeness, activity-completeness, and conduct-completeness through samadhi–sanyam",
        "study": "SPR",
        "dur": "44:29",
    },
    "BbfnTJtpQb8": {
        "title_hi": "स्वत्व – स्वतंत्रता – स्वराज्य",
        "title_en": "Selfhood – Freedom – Self-rule",
        "study": "AXI",
        "dur": "1:02:30",
    },
    "QgqtqALvMLw": {
        "title_hi": "अनुसंधान और शोध",
        "title_en": "Exploration and research",
        "study": "SPR",
        "dur": "53:05",
    },
    "QA1WhtS2Gzo": {
        "title_hi": "पुनः अनुसंधान या अध्ययन की आवश्यकता",
        "title_en": "The need for further exploration or study",
        "study": "SPR",
        "dur": "36:12",
    },
    "MeFEslxQ1XU": {
        "title_hi": "साम्य ऊर्जा – कार्य ऊर्जा",
        "title_en": "Saamya energy – activity energy",
        "study": "ONT",
        "dur": "18:14",
    },
}

# Longer / more specific phrases first when protecting.
EXTRA_TERMS = [
    ("सह-अस्तित्व", "coexistence"),
    ("सहअस्तित्व", "coexistence"),
    ("साक्षात्कार", "*sakshatkar*"),
    ("अनुसंधान", "exploration"),
    ("कल्पनाशीलता", "imaginativeness"),
    ("कर्मस्वतंत्रता", "freedom in action"),
    ("विचारशीलता", "thoughtfulness"),
    ("इन्द्रिय-गोचर", "sense-accessible"),
    ("ज्ञान-गोचर", "knowledge-accessible"),
    ("गठनपूर्णता", "constitution-completeness"),
    ("क्रियापूर्णता", "activity-completeness"),
    ("गुणात्मक परिवर्तन", "qualitative transformation"),
    ("तत्सान्निध्य", "absolute-connectedness"),
    ("तदावलोकन", "absolute-observance"),
    ("तादात्म्य", "absolute-oneness"),
    ("तदाकार", "absolute-resonance"),
    ("तद्रूप", "absolute-accordance"),
    ("दृष्टापद", "seat of the Seer"),
    ("पुरुषार्थ", "diligence"),
    ("परमार्थ", "benevolence"),
    ("मानवीयता", "humaneness"),
    ("समृद्धि", "prosperity"),
    ("समाधान", "resolution"),
    ("अस्तित्व", "existence"),
    ("जागृति", "awakening"),
    ("अध्ययन", "study"),
    ("अनुभव", "realisation"),
    ("प्रमाण", "evidence"),
    ("स्वभाव", "essential nature"),
    ("अवस्था", "state"),
    ("संवेदना", "sensation"),
    ("स्वतंत्रता", "freedom"),
    ("स्वराज्य", "self-rule"),
    ("स्वत्व", "selfhood"),
    ("संस्कार", "conditioning"),
    ("प्रारब्ध", "prarabdha"),
    ("समाधि", "*samadhi*"),
    ("संयम", "*sanyam*"),
    ("दृष्टा", "Seer"),
    ("न्याय", "justice"),
    ("धर्म", "dharma"),
    ("सत्य", "truth"),
    ("बोध", "*bodh*"),
    ("जीवन", "*jeevan*"),
    ("इकाई", "unit"),
    ("आचरण", "conduct"),
    ("मूल्य", "value"),
    ("संबंध", "relationship"),
    ("व्यवस्था", "orderliness"),
    ("विकास", "development"),
    ("ऊर्जा", "energy"),
    ("साम्य", "*saamya*"),
    ("भाषा", "language"),
    ("अर्थ", "meaning"),
    ("वस्तु", "*vastu*"),
    ("रूप", "form"),
    ("गुण", "property"),
]


def dur_secs(d: str) -> int:
    p = [int(x) for x in d.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def load_mapping_terms(
    registry_path: Path = TERMINOLOGY_REGISTRY,
) -> list[tuple[str, str]]:
    """Curated phrase overrides plus accepted registry terms for MT protection.

    Dumping all of MD-Mapping into placeholders shreds Hindi and leaves orphan
    ZX codes after MT. The controlled registry is deliberately narrower and
    sense-governed. Provisional/disputed/working-gloss entries are excluded so
    an automatic cohort draft cannot silently turn them into settled English.
    """
    terms = dict(EXTRA_TERMS)
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        for entry in registry.get("entries", []):
            if entry.get("status") != "accepted":
                continue
            english = str(entry.get("canonical_english", "")).strip()
            if not english:
                continue
            for hindi in [entry.get("hindi"), *entry.get("accepted_variants", [])]:
                if hindi:
                    # Curated overrides deliberately win where transliteration
                    # is safer in an automatic continuous-prose draft.
                    terms.setdefault(str(hindi), english)
    return sorted(terms.items(), key=lambda kv: -len(kv[0]))


def find_dir(vid: str) -> Path:
    for p in SESSIONS.iterdir():
        if p.is_dir() and p.name.endswith("--" + vid):
            return p
    raise FileNotFoundError(vid)


def segment_text(text: str, target_words: int = 60) -> list[str]:
    """Split cleaned ASR into ~target_words chunks on danda / sentence ends."""
    text = re.sub(r"\s+", " ", text).strip()
    # Split on Devanagari danda or Latin sentence end, keep delimiter.
    parts = re.split(r"(?<=[।.?!\n])\s+", text)
    segs: list[str] = []
    buf: list[str] = []
    count = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        w = len(part.split())
        if count + w > target_words and buf:
            segs.append(" ".join(buf))
            buf = [part]
            count = w
        else:
            buf.append(part)
            count += w
    if buf:
        segs.append(" ".join(buf))
    return segs


def protect(hi: str, terms: list[tuple[str, str]]) -> tuple[str, dict[str, str]]:
    """Replace technical Hindi with zero-padded placeholders before MT."""
    table: dict[str, str] = {}
    out = hi
    n = 0
    for h, en in terms:
        if h not in out:
            continue
        # ZX…XZ is unlikely in MT output and is length-stable / non-nested
        key = f"ZX{n:03d}XZ"
        n += 1
        table[key] = en
        out = out.replace(h, key)
    return out, table


def restore(en: str, table: dict[str, str]) -> str:
    out = en
    for key, val in sorted(table.items(), key=lambda kv: -len(kv[0])):
        out = re.sub(re.escape(key), val, out, flags=re.IGNORECASE)
        spaced = re.sub(r"(ZX)(\d{3})(XZ)", r"\1 \2 \3", key)
        out = re.sub(re.escape(spaced), val, out, flags=re.IGNORECASE)
        # MT often drops the trailing XZ
        m = re.match(r"ZX(\d{3})XZ", key, re.I)
        if m:
            out = re.sub(rf"ZX\s*{m.group(1)}(?!\d)", val, out, flags=re.IGNORECASE)
    # any leftover placeholders — drop rather than leave codes in prose
    out = re.sub(r"ZX\s*\d{3}\s*XZ", "", out, flags=re.IGNORECASE)
    out = re.sub(r"ZX\s*\d{3}\b", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\s{2,}", " ", out).strip()
    # common MT mistakes → MD English
    fixes = [
        (r"\breligion\b", "dharma"),
        (r"\bReligion\b", "Dharma"),
        (r"\bco-existence\b", "coexistence"),
        (r"\bCo-existence\b", "Coexistence"),
        (r"\bresearch\b(?!\s+and)", "exploration"),  # अनुसंधान often mistranslated
    ]
    for pat, repl in fixes:
        out = re.sub(pat, repl, out)
    return out


def translate_hi(hi: str, terms: list[tuple[str, str]], translator) -> str:
    protected, table = protect(hi, terms)
    # Google has a ~4500 char limit; chunk if needed
    chunks = []
    buf = protected
    while len(buf) > 4200:
        cut = buf.rfind(" ", 0, 4200)
        if cut < 1000:
            cut = 4200
        chunks.append(buf[:cut])
        buf = buf[cut:].lstrip()
    chunks.append(buf)
    translated = []
    for ch in chunks:
        if not ch.strip():
            continue
        try:
            translated.append(translator.translate(ch))
            time.sleep(0.15)
        except Exception as e:  # noqa: BLE001
            translated.append(f"[translation failed: {type(e).__name__}] {ch[:80]}")
    return restore(" ".join(translated), table)


def mark_for(hi: str, log: dict | None) -> str:
    if "\ufffd" in hi or "�" in hi:
        return "U"
    if log:
        # if this segment sits near a collapse, mark U — approximate: token present
        for ev in log.get("repeat_collapses", []):
            tok = ev.get("token", "")
            if tok and hi.count(tok) >= 3:
                return "U"
    # boilerplate residue
    if re.search(r"सब्स्?क्राइब|subscribe", hi, re.I):
        return "U"
    return "P"


def fmt_ts(seconds: float) -> str:
    s = max(0, int(seconds))
    return f"{s // 60:02d}:{s % 60:02d}"


def build_md(vid: str, meta: dict, folder: Path, terms: list[tuple[str, str]],
             translator) -> Path:
    stem = folder.name
    cleaned = folder / f"{stem}-cleaned.txt"
    raw = folder / f"{stem}-raw-asr.txt"
    log_path = folder / f"{stem}-clean-log.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.is_file() else {}

    hi_text = cleaned.read_text(encoding="utf-8", errors="replace")
    segs = segment_text(hi_text)
    total_words = max(1, sum(len(s.split()) for s in segs))
    dur = dur_secs(meta["dur"])

    lines: list[str] = []
    lines += [
        f"# {meta['title_hi']}",
        "",
        f"**{meta['title_en']}** — recorded session with Shri A. Nagraj",
        "",
        f"**Recording:** {meta['dur']}; posted by Rakesh Gupta (translator of MVD, SB, JV), "
        f"<https://youtu.be/{vid}>",
        f"**Audio:** not stored in this repository — **listen at the URL above when checking "
        f"a timestamp below.**",
        f"**Transcript coverage:** approximate 00:00–{fmt_ts(dur)} over {len(segs)} segments "
        f"(timestamps derived from word-rate × duration; GPU `-otxt` has no native stamps)",
        f"**Compiled:** August 2, 2026 · **Status:** Working transcript and translation — "
        f"**not** a published or authenticated text · **Tier-1 cohort 1**",
        "",
        "---",
        "",
        "## What this file is, and what it is not",
        "",
        "This is a **machine-produced transcript of an oral session, with a working English "
        "translation**. It has none of the standing of MVD, SB, JV or KD.",
        "",
        "- **Nobody has authenticated the recording.** Attribution rests on the posting "
        "channel (Rakesh Gupta's).",
        "- **The Hindi below is reconstructed, not heard.** It is Whisper `large-v3` GPU "
        "ASR (ROCm/HIP, **no VAD**, **`--max-context 0`**, beam 5), then Layer-A cleaning "
        "(D11 boilerplate removed, consecutive-token loops collapsed, unambiguous ASR "
        "normalisations). It has **not** been checked against the audio by a Hindi speaker.",
        "- **The English is a working translation** of that reconstruction (MT with "
        "accepted technical terms protected from "
        "[`TERMINOLOGY-REGISTRY.json`](../TERMINOLOGY-REGISTRY.json); curated "
        "transliteration overrides remain in the cohort script). Post-edit against "
        "the printed corpus before quoting in a "
        "released study.",
        "",
        "**Before quoting any line of this file in a released study, listen to the audio "
        "at the cited timestamp.**",
        "",
        f"Raw decoder dump (unmodified): [`{raw.name}`]({raw.name}). "
        f"Cleaned input to this file: [`{cleaned.name}`]({cleaned.name}).",
        "",
        "### Reliability marks",
        "",
        "- **[R] Reliable** — not used in this automated cohort pass except where noted.",
        "- **[P] Probable** — default for cleaned continuous speech.",
        "- **[U] Uncertain** — residual `U+FFFD`, collapsed loop neighbourhood, or "
        "boilerplate residue. **Do not quote.**",
        "",
        "---",
        "",
        "## Conventions",
        "",
        "**Hindi normalisation.** Same context-free list as the 2010 Sakshatkar session "
        "(see Layer-A clean log). Words the ASR did not carry are not supplied.",
        "",
        "**Terminology.** English technical terms follow accepted entries in "
        "[`TERMINOLOGY-REGISTRY.json`](../TERMINOLOGY-REGISTRY.json), which traces "
        "to `MD-Mapping.xlsx` / published MVD·SB·JV·KD English. Provisional entries "
        "are not auto-protected. Continuous prose is working MT with accepted "
        "terms protected.",
        "",
        "**Timestamps** are approximate. They are proportional to cumulative word count "
        f"over {meta['dur']} and are for navigation only.",
        "",
        "---",
        "",
        "## Transcript",
        "",
    ]

    cum = 0
    for i, seg in enumerate(segs, 1):
        mark = mark_for(seg, log)
        t0 = dur * (cum / total_words)
        cum += len(seg.split())
        hi_show = seg.replace("\ufffd", "�")
        # Mark unclear codepoints explicitly in Hindi display
        if "�" in hi_show:
            hi_show = hi_show.replace("�", "[�]")
        en = translate_hi(seg, terms, translator) if translator else "[translation unavailable]"
        # Prefer italic English like 2010
        en_esc = en.replace("*", "")
        lines += [
            f"**[{fmt_ts(t0)}] [{mark}]**",
            "> " + hi_show,
            ">",
            f"> *{en_esc}*",
            "",
        ]
        if i % 20 == 0:
            print(f"    … {vid} segment {i}/{len(segs)}", flush=True)

    lines += [
        "---",
        "",
        "## Passages needing audio verification",
        "",
        "| Stamp | Mark | Reason |",
        "|---|---|---|",
    ]
    cum = 0
    for seg in segs:
        mark = mark_for(seg, log)
        t0 = dur * (cum / total_words)
        cum += len(seg.split())
        if mark == "U":
            reason = []
            if "�" in seg or "\ufffd" in seg:
                reason.append("U+FFFD")
            if log and any(seg.count(ev.get("token", "")) >= 3
                           for ev in log.get("repeat_collapses", [])):
                reason.append("loop neighbourhood")
            if not reason:
                reason.append("uncertain")
            lines.append(f"| {fmt_ts(t0)} | U | {', '.join(reason)} |")

    out = folder / f"{stem}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", default=None,
                    help="subset of video ids")
    args = ap.parse_args()

    if GoogleTranslator is None:
        sys.exit("deep-translator not installed; pip install deep-translator")

    terms = load_mapping_terms()
    print(f"glossary terms: {len(terms)}", flush=True)
    translator = GoogleTranslator(source="hi", target="en")

    ids = args.only or list(COHORT)
    for vid in ids:
        if vid not in COHORT:
            print(f"  skip unknown {vid}", flush=True)
            continue
        folder = find_dir(vid)
        print(f"  promoting {vid} ({folder.name})", flush=True)
        out = build_md(vid, COHORT[vid], folder, terms, translator)
        print(f"    wrote {out.relative_to(BASE)}", flush=True)


if __name__ == "__main__":
    main()

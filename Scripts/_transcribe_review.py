#!/usr/bin/env python3
"""Review a batch of raw ASR transcripts before any of them is promoted.

Cheap, mechanical, and aimed at *systematic* faults rather than individual bad
files. It computes word density against duration, the longest consecutive
repeated token, the most frequent 3-gram, Devanagari share and U+FFFD count,
then prints the distribution and flags outliers.

Read the distribution first. A words-per-minute spread of 31-153 around a
median of 111 is how D10 was found: nobody talks at a third of the median rate,
so the slow files were decodes looping instead of transcribing. A fault that
hits most of the corpus is a configuration fault -- do not start repairing
files one at a time until you have ruled the decoder out.

Two cautions when reading the flags:

  * Consecutive repetition (maxrun) is the sharp signal. A common phrase
    appearing 20 times in 5,000 words is ordinary language, not a defect.
  * U+FFFD is expected at roughly one per 12,000 characters on the GPU path
    (D9). It must be repaired during promotion, not re-run.
  * Every boilerplate hit is a fabrication and must be deleted by hand. No
    decoder setting removes it, and it is fluent enough to read as speech.

    python Scripts/_transcribe_review.py --manifest work/manifest.tsv \
        --transcripts work/transcripts

Exits 1 if anything is flagged, so it can gate a batch.

See References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/TRANSCRIPTION-PROGRAM.md.
"""
from __future__ import annotations

import argparse
import collections
import io
import os
import re
import sys

DEVANAGARI = ("ऀ", "ॿ")

# Whisper was trained on YouTube captions and injects their boilerplate into
# noise and silence. It is NOT in the audio. Unlike a repetition loop this is
# fluent and can sit inside a real sentence -- "कि सब्सक्राइब करना चाहिए कि यह
# जो हम समझा है" -- so it must be searched for, not noticed. Found in 30 of 60
# recordings on both backends, never in the opening 5%, which is what rules out
# a genuine channel intro. See D11.
BOILERPLATE = re.compile(
    r"सब्स्?क्राइब|subscribe|लाइक\s*(और|कर)|चैनल\s*(को|पर)"
    r"|देखने\s*के\s*लिए\s*धन्यवाद|thanks\s*for\s*watching",
    re.IGNORECASE)


def read_manifest(path):
    rows = {}
    for n, line in enumerate(io.open(path, encoding="utf-8")):
        if n == 0 or not line.strip():
            continue
        f = line.rstrip("\n").split("\t")
        if len(f) >= 3:
            rows[f[2]] = (f[0], f[1], f[3] if len(f) > 3 else "")
    return rows


def secs(d):
    try:
        p = [int(x) for x in d.split(":")]
    except ValueError:
        return 0
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def measure(path, duration_s):
    raw = open(path, "rb").read()
    text = raw.decode("utf-8", errors="replace")
    words = text.split()

    # longest run of the same token repeated back to back: a decode loop
    best = run = 1
    for i in range(1, len(words)):
        run = run + 1 if words[i] == words[i - 1] else 1
        best = max(best, run)

    tri = collections.Counter(tuple(words[i:i + 3]) for i in range(len(words) - 2))
    top, top_n = tri.most_common(1)[0] if tri else ((), 0)

    boiler = len(BOILERPLATE.findall(text))
    dev = sum(1 for c in text if DEVANAGARI[0] <= c <= DEVANAGARI[1])
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    minutes = duration_s / 60

    return dict(words=len(words), dur_min=minutes,
                wpm=len(words) / minutes if minutes else 0,
                fffd=text.count("�"), boiler=boiler,
                dev_pct=100 * dev / max(1, dev + latin),
                maxrun=best, top_tri_n=top_n, top_tri=" ".join(top)[:28])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True, help="TSV: study, dur, id, title")
    ap.add_argument("--transcripts", required=True, help="directory of <id>.txt")
    ap.add_argument("--quiet", action="store_true", help="flags and totals only")
    args = ap.parse_args()

    man = read_manifest(args.manifest)
    rows, missing = [], []
    for vid, (study, dur, title) in sorted(man.items()):
        p = os.path.join(args.transcripts, f"{vid}.txt")
        if not os.path.exists(p):
            missing.append(vid)
            continue
        r = measure(p, secs(dur))
        r.update(vid=vid, study=study, title=title)
        rows.append(r)

    if not rows:
        sys.exit(f"no transcripts found in {args.transcripts}")

    wpm = sorted(r["wpm"] for r in rows)
    med = wpm[len(wpm) // 2]
    dev = sorted(r["dev_pct"] for r in rows)

    print(f"{len(rows)}/{len(man)} present"
          + (f"  MISSING: {', '.join(missing)}" if missing else ""))
    print(f"words/min:  median {med:.0f}, range {wpm[0]:.0f}-{wpm[-1]:.0f}")
    print(f"total:      {sum(r['words'] for r in rows):,} words over "
          f"{sum(r['dur_min'] for r in rows) / 60:.2f} h")
    print(f"Devanagari: min {dev[0]:.0f}%, median {dev[len(dev) // 2]:.0f}%")
    print(f"U+FFFD:     {sum(r['fffd'] for r in rows)} across "
          f"{sum(1 for r in rows if r['fffd'])} files  (expected; see D9)")
    print(f"boilerplate:{sum(r['boiler'] for r in rows):4d} across "
          f"{sum(1 for r in rows if r['boiler'])} files  (hallucinated, not spoken; see D11)")

    flagged = []
    for r in rows:
        why = []
        if r["wpm"] < med * 0.55:
            why.append(f"low density {r['wpm']:.0f}wpm")
        if r["maxrun"] >= 5:
            why.append(f"repeat-run x{r['maxrun']}")
        if r["top_tri_n"] >= 12:
            why.append(f"3gram x{r['top_tri_n']} \"{r['top_tri']}\"")
        if r["dev_pct"] < 70:
            why.append(f"only {r['dev_pct']:.0f}% Devanagari")
        if r["words"] < 50:
            why.append("very short")
        if r["boiler"]:
            why.append(f"boilerplate x{r['boiler']}")
        if why:
            flagged.append((r, why))

    print(f"\n=== FLAGGED {len(flagged)}/{len(rows)} ===")
    if not args.quiet:
        for r, why in sorted(flagged, key=lambda x: -len(x[1])):
            print(f"  {r['vid']}  {r['dur_min']:5.1f}min {r['words']:5d}w  "
                  f"{r['title'][:34]:36} | {'; '.join(why)}")
    if not flagged:
        print("  none")

    print("\n=== per study ===")
    for s in sorted({r["study"] for r in rows}):
        g = [r for r in rows if r["study"] == s]
        print(f"  {s}: {len(g):2d} files, {sum(r['words'] for r in g):6,} words, "
              f"{sum(r['dur_min'] for r in g) / 60:.2f} h")

    if len(flagged) > len(rows) / 3:
        print(f"\n{len(flagged)} of {len(rows)} flagged. At that rate this is a decode "
              f"configuration fault, not bad audio. Check --max-context and VAD "
              f"before repairing anything by hand.")
    sys.exit(1 if (flagged or missing) else 0)


if __name__ == "__main__":
    main()

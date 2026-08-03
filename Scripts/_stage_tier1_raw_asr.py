#!/usr/bin/env python3
"""Stage Tier-1 GPU raw ASR into the private work corpus.

Copies decoder output from a work directory into one folder per recording
(<Slug>--<videoId>/) and writes RAW-ASR-TIER1.md with provenance, mechanical
review summary, and a full index. Does not promote (no translation, reliability
marks, or PDF). Default destination is outside the git repo.

    python Scripts/_stage_tier1_raw_asr.py \\
        --manifest E:\\MD-Transcription\\manifest-tier1.tsv \\
        --transcripts E:\\MD-Transcription\\transcripts-gpu-mc0

Default paths match the reference machine's work area. Re-running is safe:
existing identical files are left alone; content changes are overwritten.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# Reuse the mechanical review measures so the index matches _transcribe_review.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _transcribe_review import measure, read_manifest, secs  # noqa: E402

from _common import BASE  # noqa: E402

DEST_ROOT = Path(r"E:\MD-Transcription\Nagraj-Recorded-Sessions")
INDEX_NAME = "RAW-ASR-TIER1.md"

# Already-promoted session; not in Tier-1 manifest today, but never create a
# parallel tree if it appears later.
PROMOTED_IDS = {
    "gIvVme-Sa5s": "Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak",
}

SEVERE_MAXRUN = 15
TITLE_SLUG_MAX = 50

# Compact Devanagari → Latin for filesystem slugs (ITRANS-ish, not scholarly).
_DEV = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ii", "उ": "u", "ऊ": "uu",
    "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
    "ष": "sh", "स": "s", "ह": "h",
    "क्ष": "ksh", "त्र": "tr", "ज्ञ": "gy",
    "ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u",
    "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    "ं": "n", "ः": "h", "्": "", "ँ": "n",
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}


def transliterate_title(title: str) -> str:
    """ASCII-ish slug stem from a Hindi/English title."""
    # Longer conjuncts first.
    s = title.replace("क्ष", "ksh").replace("त्र", "tr").replace("ज्ञ", "gy")
    out = []
    for ch in s:
        if ch in _DEV:
            out.append(_DEV[ch])
        elif ch.isascii() and (ch.isalnum() or ch in "-_"):
            out.append(ch.lower())
        elif ch.isspace() or ch in "–—-/.,;:()[]'\"":
            out.append("-")
        # else drop (punctuation, rare marks)
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug


def make_slug(title: str, vid: str) -> str:
    stem = transliterate_title(title) or "recording"
    if len(stem) > TITLE_SLUG_MAX:
        stem = stem[:TITLE_SLUG_MAX].rstrip("-")
    return f"{stem}--{vid}"


def stage_one(vid: str, title: str, src: Path, dest_root: Path) -> tuple[str, Path]:
    if vid in PROMOTED_IDS:
        # Keep the existing promoted tree; drop a dated mc0 sidecar if absent.
        folder = dest_root / PROMOTED_IDS[vid]
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / f"{PROMOTED_IDS[vid]}-raw-asr-gpu-mc0.txt"
        shutil.copy2(src, dest)
        return PROMOTED_IDS[vid], dest

    slug = make_slug(title, vid)
    folder = dest_root / slug
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{slug}-raw-asr.txt"
    shutil.copy2(src, dest)
    return slug, dest


def write_index(path: Path, rows: list[dict], provenance: dict) -> None:
    severe = [r for r in rows if r["maxrun"] >= SEVERE_MAXRUN]
    wpm = sorted(r["wpm"] for r in rows)
    med = wpm[len(wpm) // 2]
    lines = [
        "# Tier-1 raw ASR — staged corpus",
        "",
        "**Status:** staged as raw ASR only — **not promoted**. Do not cite in a "
        "released study until a session has been normalised, boilerplate-stripped, "
        "reliability-marked, and listened to. See "
        "[README.md](README.md) for evidential standing.",
        "",
        "## Provenance",
        "",
        "| | |",
        "|---|---|",
        f"| Source channel | Rakesh Gupta "
        f"([@RakeshGuptamadhyasth-darshan](https://www.youtube.com/@RakeshGuptamadhyasth-darshan)) |",
        f"| Manifest | `{provenance['manifest']}` (study, duration, video ID, title) |",
        f"| Decoder | whisper.cpp + ROCm/HIP, `ggml-large-v3`, language=hi |",
        f"| Flags | **no VAD**, **`--max-context 0`** (D10), beam 5, workers 1 |",
        f"| Work output | `{provenance['transcripts']}` |",
        f"| Staged | {len(rows)} recordings, "
        f"{sum(r['words'] for r in rows):,} words, "
        f"{sum(r['dur_min'] for r in rows) / 60:.2f} h |",
        "",
        "## Mechanical review (D10 re-run)",
        "",
        "Run: `python Scripts/_transcribe_review.py --manifest … --transcripts …`",
        "",
        "| Metric | Pre-D10 GPU | This corpus (`-mc 0`) |",
        "|---|---|---|",
        f"| Words/min | median 111, range 31–153 | median **{med:.0f}**, "
        f"**{wpm[0]:.0f}–{wpm[-1]:.0f}** |",
        f"| Present | 60/60 | {len(rows)}/60 |",
        f"| `U+FFFD` | ~47 | **{sum(r['fffd'] for r in rows)} across "
        f"{sum(1 for r in rows if r['fffd'])} files** (D9 — repair on promote) |",
        f"| Boilerplate | ~94 / 30 files | **{sum(r['boiler'] for r in rows)} across "
        f"{sum(1 for r in rows if r['boiler'])} files** (D11 — delete by hand) |",
        "",
        "**Density is fixed** — the old 31 wpm loop failure mode is gone. "
        "Files are still **not promotion-ready**: expected D11 boilerplate, "
        "D9 `U+FFFD`, and the severe consecutive-repeat cases below.",
        "",
        f"### Severe consecutive loops (`maxrun` ≥ {SEVERE_MAXRUN})",
        "",
        "These need audio-checked repair before trust:",
        "",
        "| Video ID | maxrun | top 3-gram | Title |",
        "|---|---|---|---|",
    ]
    for r in sorted(severe, key=lambda x: -x["maxrun"]):
        lines.append(
            f"| `{r['vid']}` | ×{r['maxrun']} | {r['top_tri']} | {r['title']} |"
        )
    if not severe:
        lines.append("| *(none)* | | | |")

    lines += [
        "",
        "## Index",
        "",
        "Each directory holds only the decoder dump "
        "`<Slug>--<videoId>-raw-asr.txt`. "
        "URL form: `https://youtu.be/<id>`.",
        "",
        "| Study | Duration | Directory | Title | URL | wpm | FFFD | boiler | maxrun |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    study_order = {"SPR": 0, "EPI": 1, "AXI": 2, "ONT": 3}
    for r in sorted(rows, key=lambda x: (study_order.get(x["study"], 9), -x["dur_min"])):
        url = f"https://youtu.be/{r['vid']}"
        rel = f"{r['slug']}/{r['slug']}-raw-asr.txt"
        lines.append(
            f"| {r['study']} | {r['dur']} | [`{r['slug']}`]({rel}) | "
            f"{r['title']} | [{r['vid']}]({url}) | "
            f"{r['wpm']:.0f} | {r['fffd']} | {r['boiler']} | {r['maxrun']} |"
        )

    lines += [
        "",
        "## Out of scope for this staging",
        "",
        "- Hindi normalisation, English translation, `[R]`/`[P]`/`[U]` marks, PDF",
        "- Bulk deletion of subscribe/boilerplate tokens",
        "- Re-decode of the severe loop files",
        "",
        "Promotion remains per-session work under the "
        "[transcribe-recording](../../../.agents/skills/transcribe-recording/SKILL.md) "
        "skill.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest",
                    default=r"E:\MD-Transcription\manifest-tier1.tsv")
    ap.add_argument("--transcripts",
                    default=r"E:\MD-Transcription\transcripts-gpu-mc0")
    ap.add_argument("--dest", type=Path, default=DEST_ROOT,
                    help="Work-area Nagraj-Recorded-Sessions root (default: E:\\MD-Transcription\\...)")
    args = ap.parse_args()

    man = read_manifest(args.manifest)
    if not man:
        sys.exit(f"empty or missing manifest: {args.manifest}")

    rows = []
    skipped = []
    for vid, (study, dur, title) in man.items():
        src = Path(args.transcripts) / f"{vid}.txt"
        if not src.is_file():
            skipped.append(vid)
            print(f"  MISSING {vid}", flush=True)
            continue
        slug, dest = stage_one(vid, title, src, args.dest)
        m = measure(str(src), secs(dur))
        m.update(vid=vid, study=study, dur=dur, title=title, slug=slug,
                 dest=str(dest))
        rows.append(m)
        print(f"  staged {slug}", flush=True)

    index = args.dest / INDEX_NAME
    write_index(index, rows, {
        "manifest": args.manifest,
        "transcripts": args.transcripts,
    })
    print(f"\n{len(rows)} staged, {len(skipped)} missing", flush=True)
    print(f"index: {index}", flush=True)
    if skipped:
        sys.exit(1)


if __name__ == "__main__":
    main()

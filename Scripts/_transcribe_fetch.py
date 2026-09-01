#!/usr/bin/env python3
"""Fetch audio for a transcription manifest.

Audio only, no re-encoding: PyAV (bundled with faster-whisper) decodes m4a,
webm and opus natively, so ffmpeg is never needed. Resumable — a recording
already present is skipped.

Manifest is TSV with a header and four columns: study, dur, id, title.
Only `id` is required; the rest is provenance carried through to the log.

    python Scripts/_transcribe_fetch.py --manifest work/manifest.tsv --out work/audio

Recordings are not repository content. Point --out somewhere outside the repo.
See References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/TRANSCRIPTION-PROGRAM.md.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time


def read_manifest(path: str) -> list[dict]:
    rows = []
    for n, line in enumerate(io.open(path, encoding="utf-8")):
        if n == 0 or not line.strip():
            continue
        f = line.rstrip("\n").split("\t")
        if len(f) >= 3:
            rows.append(dict(study=f[0], dur=f[1], id=f[2], title=f[3] if len(f) > 3 else ""))
    return rows


def existing(audio_dir: str, vid: str) -> list[str]:
    return [f for f in os.listdir(audio_dir)
            if f.startswith(vid + ".") and not f.endswith(".part")]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True, help="TSV: study, dur, id, title")
    ap.add_argument("--out", required=True, help="audio output directory (outside the repo)")
    ap.add_argument("--sleep", type=float, default=1.5,
                    help="seconds between requests; raise if 403s appear (default 1.5)")
    args = ap.parse_args()

    try:
        import yt_dlp
    except ImportError:
        sys.exit("yt-dlp not installed:  pip install yt-dlp")

    os.makedirs(args.out, exist_ok=True)
    rows = read_manifest(args.manifest)
    print(f"{len(rows)} recordings in manifest", flush=True)

    log = []
    for n, r in enumerate(rows, 1):
        vid = r["id"]
        if existing(args.out, vid):
            log.append(dict(id=vid, status="skip"))
            print(f"[{n}/{len(rows)}] skip {vid}", flush=True)
            continue
        opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": os.path.join(args.out, f"{vid}.%(ext)s"),
            "quiet": True, "no_warnings": True, "noprogress": True,
            "retries": 3, "socket_timeout": 30,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as y:
                y.extract_info(f"https://www.youtube.com/watch?v={vid}", download=True)
            got = existing(args.out, vid)
            mb = round(os.path.getsize(os.path.join(args.out, got[0])) / 1048576, 1) if got else 0
            log.append(dict(id=vid, status="ok", mb=mb, file=got[0] if got else None))
            print(f"[{n}/{len(rows)}] ok   {vid} {mb:6.1f}MB  {r['title'][:46]}", flush=True)
        except Exception as e:                                    # noqa: BLE001
            log.append(dict(id=vid, status="fail", error=f"{type(e).__name__}: {e}"))
            print(f"[{n}/{len(rows)}] FAIL {vid}  {type(e).__name__}: {str(e)[:110]}", flush=True)
        time.sleep(args.sleep)

    io.open(
        os.path.join(args.out, "fetch-log.json"), "w", encoding="utf-8", newline="\n"
    ).write(
        json.dumps(log, ensure_ascii=False, indent=1))

    ok = sum(1 for x in log if x["status"] == "ok")
    fail = [x for x in log if x["status"] == "fail"]
    print(f"\nDONE ok={ok} skipped={sum(1 for x in log if x['status']=='skip')} "
          f"failed={len(fail)}  total={sum(x.get('mb', 0) for x in log):.0f}MB", flush=True)
    for x in fail:
        print(f"  FAILED {x['id']}  {x['error'][:130]}", flush=True)
    if fail:
        print("\nA 403 late in a long run is throttling, not unavailability — "
              "re-run this command and it will retry only the missing ones.", flush=True)


if __name__ == "__main__":
    main()

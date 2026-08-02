#!/usr/bin/env python3
"""Transcribe a fetched manifest, GPU by default.

**Decodes without VAD.** Voice-activity detection drops roughly a fifth of the
words on this material, biased toward the emphasis-flanked statements that carry
doctrine — the speaker pauses for emphasis and VAD cuts at pauses. No-VAD is the
only mode whose output may be promoted to a References artefact. See D7 in
References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/TRANSCRIPTION-PROGRAM.md.

Two backends:

  --backend gpu   whisper.cpp + ROCm/HIP. ~5x realtime, no VAD. Needs the AMD
                  HIP SDK and a whisper.cpp built with -DGGML_HIP=ON; see the
                  skill. Set WHISPER_CPP_CLI to a Vulkan build to use that
                  instead -- it measured marginally faster (D12) and needs no
                  SDK, so it remains a sound fallback.
  --backend cpu   faster-whisper sequential, no VAD. ~0.2x realtime. Correct
                  but 28x slower — a fallback, not a plan.

Resumable: a recording whose .txt already exists is skipped.

    python Scripts/_transcribe_batch.py --manifest work/manifest.tsv \
        --audio work/audio --out work/transcripts --workers 2
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import glob
import io
import os
import re
import subprocess
import sys
import time
import wave

WHISPER_CLI = os.environ.get("WHISPER_CPP_CLI", r"E:\Tools\whisper.cpp\build-hip\bin\whisper-cli.exe")
GGML_MODEL = os.environ.get("WHISPER_CPP_MODEL", r"E:\Tools\whisper.cpp\models\ggml-large-v3.bin")

_gpu_env_cache = None


def rocm_root():
    """Locate the HIP SDK. Returns None if this is not a ROCm build."""
    p = os.environ.get("HIP_PATH")
    if p and os.path.isdir(p):
        return p.rstrip("\\/")
    roots = sorted(glob.glob(r"C:\Program Files\AMD\ROCm\*"), reverse=True)
    return roots[0] if roots else None


def pick_hip_device(env):
    """Choose the discrete GPU when more than one ROCm device is visible.

    Necessary because ggml loads its kernel modules onto *every* visible ROCm
    device, not just the one selected with -dev. On a Ryzen desktop the CPU's
    integrated graphics shows up as a second device with a different
    architecture, and a build targeting only the discrete card dies with
    "device kernel image is invalid" on the first kernel. Hiding the iGPU is
    the fix; -dev is not. See D12.

    Heuristic is largest VRAM, because an iGPU reports a slice of system RAM
    and the discrete card reports its own. Set HIP_VISIBLE_DEVICES yourself if
    that is wrong for your machine.
    """
    try:
        out = subprocess.run([WHISPER_CLI, "--help"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", env=env, timeout=60)
    except Exception:                                             # noqa: BLE001
        return None
    devs = re.findall(r"Device (\d+): (.+?),\s*(gfx\w+).*?VRAM:\s*(\d+)\s*MiB",
                      (out.stdout or "") + (out.stderr or ""))
    if len(devs) < 2:
        return None
    best = max(devs, key=lambda d: int(d[3]))
    print(f"  {len(devs)} ROCm devices visible; using device {best[0]} "
          f"({best[1]}, {best[2]}, {int(best[3])//1024} GB). "
          f"Override with HIP_VISIBLE_DEVICES.", flush=True)
    return best[0]


def gpu_env():
    """Environment for whisper-cli: ROCm on PATH, iGPU hidden. Computed once."""
    global _gpu_env_cache
    if _gpu_env_cache is not None:
        return _gpu_env_cache
    env = dict(os.environ)
    root = rocm_root()
    if root:
        # hipblas.dll and rocBLAS's Tensile libraries live only under the SDK;
        # only amdhip64 is copied to System32. Without this the process dies
        # with 0xC0000135 (DLL not found) before printing anything useful.
        env["PATH"] = os.path.join(root, "bin") + os.pathsep + env.get("PATH", "")
    if "HIP_VISIBLE_DEVICES" not in env:
        dev = pick_hip_device(env)
        if dev is not None:
            env["HIP_VISIBLE_DEVICES"] = dev
    _gpu_env_cache = env
    return env


def read_manifest(path):
    rows = []
    for n, line in enumerate(io.open(path, encoding="utf-8")):
        if n == 0 or not line.strip():
            continue
        f = line.rstrip("\n").split("\t")
        if len(f) >= 3:
            rows.append((f[0], f[1], f[2], f[3] if len(f) > 3 else ""))
    return rows


def secs(d):
    try:
        p = [int(x) for x in d.split(":")]
    except ValueError:
        return 0
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def audio_for(audio_dir, vid):
    c = [f for f in os.listdir(audio_dir)
         if f.startswith(vid + ".") and not f.endswith(".part")]
    return os.path.join(audio_dir, c[0]) if c else None


def to_wav(src, dst):
    """whisper-cli's miniaudio reader cannot open m4a; convert to 16 kHz mono PCM."""
    import numpy as np
    from faster_whisper import decode_audio
    a = decode_audio(src, sampling_rate=16000)
    pcm = (np.clip(a, -1, 1) * 32767).astype("<i2")
    with wave.open(dst, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(16000)
        f.writeframes(pcm.tobytes())


def run_gpu(wav, out_stem, beam):
    # -mc 0 is not optional. whisper.cpp defaults to --max-context -1, feeding
    # unlimited prior text into each window, so a repeated phrase reinforces
    # itself into a degenerate loop. Measured on a 36-minute file: the top
    # 3-gram went from 119 occurrences to 7 and word count rose 22% once the
    # context was cut. It is the equivalent of faster-whisper's
    # condition_on_previous_text=False, which is why the CPU pass never looped.
    r = subprocess.run([WHISPER_CLI, "-m", GGML_MODEL, "-f", wav, "-l", "hi",
                        "-bs", str(beam), "-mc", "0", "-otxt", "-of", out_stem],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=gpu_env())
    return r.returncode == 0, (r.stderr or "")[-200:]


def run_cpu(src, out_stem, beam, threads):
    from faster_whisper import WhisperModel, decode_audio
    a = decode_audio(src, sampling_rate=16000)
    m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=threads)
    segs, _ = m.transcribe(a, language="hi", beam_size=beam, vad_filter=False,
                           condition_on_previous_text=False)
    # Write to .partial and rename only once the generator is exhausted.
    # faster_whisper yields lazily, so streaming into the final .txt would leave
    # a truncated file if the process is killed mid-decode -- and the resume
    # check skips any .txt that exists, so the truncation would be permanent and
    # silent. It would read as a short recording, not a broken one. The GPU path
    # is safe because whisper-cli writes once at the end; this makes the CPU
    # path match. Matters most under _transcribe_autoresume.ps1, where restarts
    # are unattended.
    tmp = out_stem + ".partial"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for s in segs:
            f.write(f"[{int(s.start//60):02d}:{int(s.start%60):02d}] {s.text.strip()}\n")
    os.replace(tmp, out_stem + ".txt")
    return True, ""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wav", default=None, help="WAV scratch dir (default <out>/../wav); disposable")
    ap.add_argument("--backend", choices=("gpu", "cpu"), default="gpu")
    ap.add_argument("--workers", type=int, default=2,
                    help="GPU: 2 takes ~95%% of available throughput; 4 adds ~5%%")
    ap.add_argument("--beam", type=int, default=5,
                    help="5 is faster AND better than greedy here; do not lower without measuring")
    ap.add_argument("--threads", type=int, default=16, help="cpu backend only")
    args = ap.parse_args()

    if args.backend == "gpu":
        for p, what in ((WHISPER_CLI, "whisper-cli.exe"), (GGML_MODEL, "ggml model")):
            if not os.path.exists(p):
                sys.exit(f"{what} not found at {p}\n"
                         f"Set WHISPER_CPP_CLI / WHISPER_CPP_MODEL, or see the "
                         f"transcribe-recording skill for the build steps.")

    wav_dir = args.wav or os.path.join(os.path.dirname(os.path.abspath(args.out)), "wav")
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(wav_dir, exist_ok=True)

    todo = []
    for study, dur, vid, title in read_manifest(args.manifest):
        if os.path.exists(os.path.join(args.out, f"{vid}.txt")):
            continue
        src = audio_for(args.audio, vid)
        if not src:
            print(f"  no audio for {vid} — run _transcribe_fetch.py first", flush=True)
            continue
        todo.append((vid, title, src, secs(dur)))

    if not todo:
        print("nothing to do"); return
    audio_h = sum(t[3] for t in todo) / 3600
    print(f"{len(todo)} to transcribe, {audio_h:.2f} h audio, backend={args.backend}, "
          f"workers={args.workers}, beam={args.beam}, VAD=off", flush=True)

    if args.backend == "gpu":
        for vid, _t, src, _s in todo:
            w = os.path.join(wav_dir, f"{vid}.wav")
            if not os.path.exists(w):
                to_wav(src, w)
        print("WAV conversion done", flush=True)

    todo.sort(key=lambda t: -t[3])          # longest first: no straggler at the end

    def job(t):
        vid, title, src, sec = t
        stem = os.path.join(args.out, vid)
        t0 = time.time()
        try:
            if args.backend == "gpu":
                ok, err = run_gpu(os.path.join(wav_dir, f"{vid}.wav"), stem, args.beam)
            else:
                ok, err = run_cpu(src, stem, args.beam, args.threads)
        except Exception as e:                                    # noqa: BLE001
            ok, err = False, f"{type(e).__name__}: {e}"
        return vid, ok and os.path.exists(stem + ".txt"), time.time() - t0, sec, err

    t0 = time.time(); done = fail = 0
    workers = args.workers if args.backend == "gpu" else 1
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for vid, ok, el, sec, err in ex.map(job, todo):
            if ok:
                done += 1
                print(f"  done {vid}  {sec/60:5.1f}min in {el/60:5.1f}min "
                      f"({sec/el:.2f}x)  [{done}/{len(todo)}]", flush=True)
            else:
                fail += 1
                print(f"  FAIL {vid}  {err[:120]}", flush=True)

    wall = time.time() - t0
    print(f"\nDONE {done} ok, {fail} failed in {wall/3600:.2f} h | "
          f"aggregate {audio_h*3600/wall:.2f}x realtime", flush=True)
    print(f"WAV scratch in {wav_dir} is disposable.", flush=True)


if __name__ == "__main__":
    main()

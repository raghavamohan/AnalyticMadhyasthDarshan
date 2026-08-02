---
name: transcribe-recording
description: >-
  Fetch and transcribe recorded talks (YouTube or local audio) into working
  Hindi transcripts with English translation, using Scripts/_transcribe_fetch.py
  and Scripts/_transcribe_batch.py. Use when adding a recorded session of Shri
  A. Nagraj to References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/, when a
  user asks to transcribe a talk or a channel, or when promoting raw ASR to a
  citable References artefact.
---

# Transcribe a recorded session

Turn a recorded talk into a References artefact a study can cite. Machine ASR is
the cheap first step; most of the work is what comes after it.

Works with **Cursor**, **OpenCode**, and **ZCode** (skills live in
`.agents/skills/`; OpenCode reads them via `.opencode/skills/` junction).

## When to use

- Adding a recorded session under `References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/`
- A user asks to transcribe a talk, a playlist, or a channel
- Promoting an existing raw ASR pass to a citable artefact
- Extending the corpus for a study that needs oral material the printed texts lack

## The rule that governs everything

**Decode without VAD.** Voice-activity detection drops roughly a fifth of the
words on this material, and the loss is *biased toward doctrine* — the speaker
pauses for emphasis and VAD cuts at pauses. Measured on a control slice: 328
words with no VAD, 272 with it, and the missing text included the ladder
statement and the *rup–gun–swabhav* chain.

Both scripts default to no-VAD. Do not "optimise" that away. Full evidence:
[TRANSCRIPTION-PROGRAM.md](../../../References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/TRANSCRIPTION-PROGRAM.md) D7.

## One-time setup

The transcription environment is **not** committed — a 3 GB model and a
GPU-driver-sensitive build cannot honour a reproducibility promise. Set it up
outside the repo.

```powershell
# clean venv — NOT Anaconda: its onnxruntime is broken here and its MKL
# libiomp5md.dll collides with CTranslate2's OpenMP
python -m venv E:\Tools\asr-venv
E:\Tools\asr-venv\Scripts\pip install faster-whisper yt-dlp
```

GPU (strongly preferred — 28x faster than the only correct CPU mode):

```powershell
winget install KhronosGroup.VulkanSDK
winget install Microsoft.VisualStudio.2022.BuildTools --override `
  "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
git clone --depth 1 https://github.com/ggml-org/whisper.cpp E:\Tools\whisper.cpp
cd E:\Tools\whisper.cpp
cmake -B build -G "Visual Studio 17 2022" -A x64 -DGGML_VULKAN=ON
cmake --build build --config Release -j 16
# ggml-large-v3.bin (~2.9 GB) from huggingface.co/ggerganov/whisper.cpp -> models/
```

Point the scripts at it with `WHISPER_CPP_CLI` and `WHISPER_CPP_MODEL`, or accept
the `E:\Tools\whisper.cpp` defaults.

**The Build Tools install needs an approved UAC prompt.** It returns installer
exit **1602** and installs nothing if elevation is declined, and cannot be driven
from an unelevated non-interactive shell.

## Workflow

### 1. Build a manifest

TSV with a header and four columns — `study`, `dur`, `id`, `title`:

```
study	dur	id	title
SPR	45:01	gIvVme-Sa5s	साक्षात्कार - बोध - अनुभव - प्रमाण
```

To enumerate a channel, page YouTube's browse API from the videos tab. **Do not
scroll the page in a headless browser** — lazy-loading needs a composited
viewport and only the first three items ever render.

### 2. Fetch audio

```powershell
python Scripts/_transcribe_fetch.py --manifest work\manifest.tsv --out work\audio
```

Audio only, no re-encoding; PyAV reads m4a/webm/opus so ffmpeg is never needed.
Resumable. A **403 late in a long run is throttling, not unavailability** — just
re-run, or raise `--sleep`.

### 3. Transcribe

```powershell
python Scripts/_transcribe_batch.py --manifest work\manifest.tsv `
    --audio work\audio --out work\transcripts --workers 2
```

Defaults are measured, not guessed: **beam 5** (faster *and* better than greedy
here) and **2 workers** (95% of available GPU throughput; 4 adds ~5%). Add
`--backend cpu` only if no GPU is available — it is correct but ~28x slower.

The GPU path also forces **`--max-context 0`**, which is not optional and is not
a flag. `whisper.cpp` defaults to unbounded context, which turns any repeated
phrase into a self-sustaining loop: 36 of 60 transcripts were affected before
this was found. See [D10](../../../References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/TRANSCRIPTION-PROGRAM.md).

### 4. Review the batch before promoting anything

```powershell
python Scripts/_transcribe_review.py --manifest work\manifest.tsv `
    --transcripts work	ranscripts
```

Mechanical, cheap, and it catches faults that are systematic rather than
per-file. It reports **words per minute against duration**, **longest
consecutive repeated token**, **most frequent 3-gram**, Devanagari share and
`U+FFFD` count, and exits non-zero if anything is flagged. **Read the
distribution, not the individual files.**

A words-per-minute spread of 31–153 around a median of 111 is what exposed D10 —
no one talks at a third of the median rate. Two cautions when reading flags:

- **Consecutive repetition is the sharp signal.** A common phrase appearing 20
  times in 5,000 words is ordinary language, not a defect.
- **A fault that hits most of the corpus is a configuration fault.** Do not
  start repairing files one at a time until you know it is not the decoder.

### 5. Promote to a References artefact

**This is the real work, and raw ASR is not it.** For each recording:

1. Give it a directory: `<Slug>--<videoId>/`. **Include the video ID** — channel
   titles collide (one title covers ten separate uploads).
2. **Repair broken UTF-8 first.** whisper.cpp emits a partial codepoint where a
   multi-byte character splits across tokens — about one per 12,000 characters,
   in both `-otxt` and `-oj`, deterministic and not fixed by re-running.
   Count them with `python -c "import sys;print(open(sys.argv[1],'rb').read().decode('utf-8','replace').count(chr(0xFFFD)))" <file>`,
   **Do not let a `U+FFFD` be silently normalised into a plausible character.**
3. Normalise Devanagari only where the intended word is unambiguous. **Never
   supply words the ASR did not carry**; bracket anything a printed text fixes,
   and say which text fixed it.
4. Translate against `MD-Mapping.xlsx` and the published MVD/SB/JV English.
   Flag terms with no mapping row as working glosses — but **search MVD *and*
   SB space-insensitively before inventing English.** Six of six terms once
   flagged as "no mapping found" were in the corpus all along.
5. Mark every segment **[R]** reliable / **[P]** probable / **[U]** uncertain,
   and tabulate the passages needing audio verification.
6. Cross-reference the printed corpus. A systematic pass recovered seven
   uncertain segments and corrected six terms on the first transcript.
7. Generate the PDF ([AGENTS.md](../../../AGENTS.md) §3 — never pandoc):

```powershell
python Scripts/_convert_to_pdf.py "References/.../<Slug>/<Slug>.md"
node Scripts/_html_to_pdf.js "References/.../<Slug>/<Slug>.html"
```

8. Add rows to the folder `README.md`, `References/MANIFEST.md`, and
   `NOT-DOWNLOADED.md` (recordings stay external; transcripts are local).

**Nothing is promoted from statistics alone.** Every quality judgement above is
made over the text. Deciding which decode configuration to use that way is fine;
signing off a transcript is not. Listen to the flagged passages.

## Citing page numbers — two traps

Recovering a garbled passage means citing the printed text, and the `.md`
extracts will mislead you:

- **MVD's `page-N` is a footer.** Content *after* the marker is on page **N+1**.
  A script attributing a line to "the last marker above it" is off by one, always.
- **JV's extract has no pagination** — eight stray bare numbers in the whole book.
  Reading the nearest as a page number once produced a citation 26 pages out.

Find wording in the extract; **confirm the page in the PDF** before citing.

## Pitfalls

| Symptom | Cause |
|---|---|
| Throughput collapses ~10x | Anaconda's broken `onnxruntime`, or its MKL OpenMP colliding with CTranslate2. Use a clean venv. |
| `UnicodeEncodeError` on Devanagari | Console cp1252. Set `PYTHONIOENCODING=utf-8`. |
| `failed to read audio file` (m4a) | `whisper-cli`'s miniaudio has no AAC. `_transcribe_batch.py` converts to WAV automatically. |
| Devanagari italic looks mangled in PDF | Nirmala UI has no italic face. `_convert_to_pdf.py` sets `font-synthesis-style: none`; keep it. |
| Devanagari renders as tofu | No Devanagari system font. **Check a page of output, not just the exit code.** |
| `vswhere` says nothing installed | Needs `-all` to see BuildTools-only machines. |
| `U+FFFD` in GPU output | whisper.cpp splits a multi-byte char across tokens. ~0.008% of text, both output formats, deterministic. Repair, do not re-run. |
| Phrase repeats for 30s; low words/min | `whisper.cpp` default `--max-context -1` conditions the loop on itself. `-mc 0` is forced in the script; do not remove it. |

## Method warning

Two confident wrong conclusions on this pipeline came from comparisons that
moved two variables at once — blaming batching for a VAD loss, and reporting 2
GPU workers as slower than 1. **Vary one thing; hold the workload identical.**
And validating a change by checking a single phrase is not validation.

A third came from asserting which decoder guards were active without checking:
`whisper.cpp`'s entropy, logprob and temperature-fallback defaults were set all
along, and the real difference was the context window. **Read the defaults.**

## Completion checklist

- [ ] Manifest has video IDs; directory names include them
- [ ] Fetch reports 0 failures (re-run to clear throttling 403s)
- [ ] Transcribed with **VAD off** and `--max-context 0`
- [ ] `python Scripts/_transcribe_review.py` run; flags understood, not just counted
- [ ] `U+FFFD` count is zero, or every occurrence repaired from context/audio (not smoothed away)
- [ ] Raw ASR kept alongside the normalised text so corrections stay auditable
- [ ] Every segment carries [R]/[P]/[U]; verification table present
- [ ] Page citations confirmed against the **PDF**, not the `.md` extract
- [ ] PDF regenerated; `python Scripts/_check_references.py` exits 0
- [ ] Folder `README.md`, `MANIFEST.md`, `NOT-DOWNLOADED.md` rows added
- [ ] [TRANSCRIPTION-PROGRAM.md](../../../References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/TRANSCRIPTION-PROGRAM.md) status table and decision log updated

## Related

- Programme log, decisions D1–D10: [TRANSCRIPTION-PROGRAM.md](../../../References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/TRANSCRIPTION-PROGRAM.md)
- Folder conventions and evidential standing: [Nagraj-Recorded-Sessions/README.md](../../../References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/README.md)
- Reference checks: [check-references](../check-references/SKILL.md)
- PDF pipeline: [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md), [AGENTS.md](../../../AGENTS.md) §3

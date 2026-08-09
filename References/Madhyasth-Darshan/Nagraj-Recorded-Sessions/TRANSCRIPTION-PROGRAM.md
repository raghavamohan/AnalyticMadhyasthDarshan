# Transcription programme — recorded sessions of Shri A. Nagraj

**Started:** August 1, 2026 · **Status:** Phases 1-3 complete; Phase 4's five-video native-timestamp Excel review workspace is prepared (394 segments), but all segments remain unreviewed pending complete listening. Cohort 1 (8/60) remains working-drafted. **References holds only the 2010 Sakshatkar session.** Tier-1 corpus lives outside the repo at `E:\MD-Transcription\Nagraj-Recorded-Sessions\` (`RAW-ASR-TIER1.md`, `TERMINOLOGY-REGISTRY.json`, 60 session dirs).
**Maintainer note:** this is a living document. Update the status table and the decision log as recordings land; record reversals as reversals rather than editing the earlier reasoning away.

Companion: [`README.md`](README.md) sets out the folder conventions and how far machine-transcribed oral material may be relied on. That document governs *use*; this one records *scope, decisions, and progress*.

---

## Why this programme exists

The printed corpus (MVD, SB, JV, KD) states the darshan's positions but is often silent on mechanism. The first transcript — [*Sakshatkar – Bodh – Anubhav – Praman*](Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.md), January 2010 — demonstrated the point: it supplied the four-stage sequence's mechanism, the claim that *anubhav* adds no content beyond *sakshatkar*, and the practical division between *anusandhan* and *adhyayan*, none of which is stated that plainly in the books. It also produced a *negative* result worth having: two of the study's open problems (§6.3, §6.5) got **worse** once the mechanism was clear, which is the kind of finding a corpus is for.

That one recording changed enough of [*Spiritual Practice and Realization*](../../../Studies/Spiritual-Practice-And-Realization/Spiritual-Practice-And-Realization.md) to justify doing this systematically.

---

## The source: Rakesh Gupta's channel

Enumerated 2026-08-01 from `https://www.youtube.com/@RakeshGuptamadhyasth-darshan/videos`, via YouTube's own browse API paged through continuation tokens.

- **480 videos, 176.7 hours** total
- Uploader is Rakesh Gupta, translator of MVD, SB and JV — the same hand behind the published English
- Duration profile: 70 under 5 min · 210 at 5–15 min · 83 at 15–30 min · 69 at 30–60 min · 48 over 60 min

Scrolling the page in a headless pane does **not** work — lazy-loading needs a composited viewport, so only three items ever render. Paging the browse API is the reliable route.

### Notable series discovered

| Series | Parts | Hours | Bears on |
|---|---|---|---|
| सहअस्तित्ववादी विज्ञान (Coexistentialist Science) | 17 | 20.1 | Ontology; SB's systematic physics |
| जीवन विद्या - एक परिचय | 11 | ~11 | JV; general introduction |
| इन्द्रिय-गोचर / ज्ञान-गोचर | 5 (one gap) | ~1 | Epistemology — the two modes of access |
| संस्कार और प्रारब्ध | 5 (one gap) | ~1 | Axiology — *sanskar* |
| सत्संग रायपुर २००५ | 20 | ~8 | General |
| समाधानात्मक भौतिकवाद पर संवाद | 4 | ~1.3 | SB dialogue |

---

## Decision log

### D1 — Title-based routing to studies was tried and rejected

Classifying all 480 titles against the four studies' glossary vocabulary gave: Ontology 78 (35.0 h), **Epistemology 245 (104.1 h)**, Axiology 66 (20.3 h), Spiritual Practice 101 (30.8 h); 321 videos (127 h) matched at least one; 159 (49.7 h) matched none.

**Rejected as a basis for exclusion**, for two reasons. Epistemology's vocabulary (*ज्ञान*, *जीवन*, *अध्ययन*, *समझ*, *प्रमाण*, *बोध*) appears in most titles on the channel, so a filter selecting 104 of 176 hours is not discriminating. And the "unmatched" set contains obvious false negatives — *"The state of the soul in the awakening sequence"*, *"Taste and reception"*, *"Studying using imagination"* — because the term lists are Hindi-heavy and the channel has many English titles.

**Consequence:** titles are the wrong key. Route on *transcripts*, after the fact, by full-text search. A six-minute clip titled `WS_30060` or `d3-01(0)` could hold the clearest statement of a concept on the channel and no keyword list will find it.

### D2 — Phase 1 is a curated Tier-1 across four studies, not the whole channel

60 recordings, 23.43 hours, hand-picked for bearing on named sections of live studies. Selected by exactly the method D1 calls unreliable — accepted knowingly, because the aim of Phase 1 is to prove the pipeline and settle high-value questions, not to be exhaustive. Exhaustiveness is Phase 2's job.

### D3 — Engine: `faster-whisper` large-v3, int8, CPU

Whisper `large-v3` via CTranslate2, `compute_type=int8`, batched VAD pipeline, `beam_size=5`, `language=hi`.

**GPU was investigated and rejected for this phase**, on an AMD Radeon PRO W7900 (48 GB, RDNA3/gfx1100), Windows 11:

| Route | Verdict |
|---|---|
| CTranslate2 (current engine) | **CUDA-only.** Verified on the install: `get_cuda_device_count()` → 0, CPU compute types only. No ROCm/Vulkan/DirectML path exists. |
| whisper.cpp + Vulkan | Vulkan runtime present and the card is visible to it — but **no prebuilt Vulkan binary** is published (v1.9.1 ships CPU, BLAS, and CUDA only). Needs VS Build Tools + Vulkan SDK, several GB, then a compile. |
| torch-directml | `No matching distribution found` for this Python. Dead end. |
| onnxruntime-directml | Available (1.24.4) — the only pip-only route, but needs an ONNX Whisper export via `optimum`, and DirectML's Whisper op coverage is the weak point. |

**Superseded by D8 (2026-08-02): the Vulkan build was done and it works.** The table above stands as the state of play before that, and two of its rows were confirmed the hard way — **DirectML was actually tested and is 3–5× slower than this CPU** (294–359 GFLOP/s flat across matrix sizes, roughly 0.6% of the W7900's fp32 peak; flat scaling rules out transfer overhead as the excuse). The whisper.cpp Vulkan row was the only one worth the toolchain cost, and it was.

### D4 — Four worker processes, not one wide one

Measured on Ryzen 9 7950X (16c/32t), 5-minute slices, real audio:

| Workers × threads | Aggregate | 23.4 h would take |
|---|---|---|
| 1 × 16 | 2.23× | 10.5 h |
| **4 × 4** | **3.25×** | **7.2 h** |
| 8 × 2 | 2.91× | 8.0 h |

CTranslate2's int8 beam search does not scale past roughly 4 threads, and eight copies of large-v3 contend for memory bandwidth. 4 × 4 was chosen on this basis. Caveat noted at the time: the 8 × 2 rung overlapped with the fetch competing for the machine, so its figure is mildly pessimistic.

**Partly superseded by the Phase 1 run — do not treat 4 × 4 as settled.** The real batch achieved **2.98×**, not 3.25×, so slices overstate throughput by roughly 10%. More importantly the 3-file straggler pass, run at 3 × 5 threads, recorded per-worker rates of 1.01–1.27× against 0.69–0.97× throughout the 4 × 4 batch. Five threads per worker looks better than four, which is the opposite of what the slice benchmark indicated. Untested at four workers; see the Phase 1 status section.

### D5 — Batch ordering and resumability

Longest-first, so the 90-minute file does not strand three idle workers at the end. Each `.txt` is written to `.partial` and atomically renamed, so a completed file is never half-written and a restart skips it. The batch can be killed and resumed freely.

### D6 — One directory per recording, video ID in the name

See [`README.md`](README.md). The channel has genuine title collisions, so the ID is the only stable identifier. The first transcript predates the rule and keeps its plain slug.

### D7 — VAD is what drops text; only no-VAD decoding is complete

**Voice-activity detection drops roughly a fifth of the words, and the loss is biased toward doctrine.** Measured 2026-08-02 on the 03:00–06:00 control slice of the 2010 session, same model and beam size throughout:

| Config | VAD | Words | Segments | Speed |
|---|---|---|---|---|
| **A** Sequential | no | **328** (reference) | 19 | 0.20× |
| **B** Batched (Phase 1 config) | yes | 272 (**−17%**) | 6 | 2.07× |
| **C** Sequential | yes | 259 (**−21%**) | 7 | slow |

**The first reading of this was wrong and is corrected here.** A and B differ in *two* variables — decoding mode and VAD — so the initial conclusion blamed the batched pipeline. Adding cell C isolates it: sequential **with** VAD is *worse* than batched with VAD (259 against 272). Batching is therefore essentially innocent; **VAD is the cause**. Word-level similarity A↔B is 0.670.

What the batched pass lost on those three minutes was not filler:

- *…ठीक है जैसा **आँखों से देखने के बाद स्वीकार होना*** — the perception analogy the study quotes at §1.10
- *जो **साक्षात्कार का महिमा** यह है … **बोध होता है, बोध होने पर अनुभव होता है*** — the ladder statement itself
- *जिस वस्तु का हमें ज्ञान हुआ … माने अनुभव हुआ। उसका नाम है ज्ञान।*
- ***रूप के साथ गुण, गुण के साथ स्वभाव*** — the chain §1.1 is built on

The bias has an obvious mechanism: VAD cuts at pauses, and this speaker pauses for emphasis around exactly the statements that carry weight. **Expect the loss to concentrate on what you most want.**

**Consequence — a two-tier corpus, and an awkward one.** Batched output serves search, routing and triage (D1's purpose) and is adequate for deciding what deserves attention. Anything promoted to a References artefact must first be re-decoded **without VAD**.

There is no fast complete mode. The batched pipeline forms its batches *from* VAD segments, so batched-without-VAD does not exist; the only complete configuration is sequential no-VAD at **0.20×**. That is ~117 h single-worker for Tier-1's 23.4 h, or ~29 h at four workers — the reason a working GPU path stops being a convenience and becomes the thing that decides whether Phase 2 is feasible at all.

**Untested and worth trying before accepting 0.20×:** the measurement used aggressive VAD (`threshold=0.25`, `speech_pad_ms=500`). A gentler setting — cutting only on long silences, with generous padding — might retain nearly everything while still skipping the music gaps, recovering most of the speed. Cheap to test; do it before concluding the GPU is mandatory.

**Two method failures produced this, both worth remembering.** The batched pipeline was originally validated by comparing a *single phrase* across two passes, finding it identical, and generalising — one phrase is not a validation. Then the first proper comparison changed two variables at once and produced a confidently-stated wrong cause. The 2010 transcript's doctrinal core survived only because 00:00–18:08 happened to be decoded without VAD before the switch; its 18:08–44:32 tail is VAD output and is being re-run.

### D8 — GPU via whisper.cpp + Vulkan; it makes the complete mode the fast one

D7 concluded there was no fast complete mode. **There is one — it is just not on the CPU.** Built 2026-08-02 and measured on the same 03:00–06:00 control slice:

| Config | VAD | Words | Speed | The four passages VAD drops |
|---|---|---|---|---|
| CPU sequential | no | 328 (reference) | 0.20× | present |
| CPU batched (Phase 1) | yes | 272 | 2.07× | **all four missing** |
| **whisper.cpp Vulkan** | **no** | **337** | **4.28× single / 5.52× at 2 workers** | **all four present** |

**28× faster than the only complete CPU mode, and faster than the lossy one.** It recovers the eye-seeing analogy, the *rup-gun-swabhav* chain, the knowledge identification and the *praman* definition — every passage VAD was eating — and picks up *ऋतम्भरा* as well.

**Settings, both measured rather than assumed.**

*Beam size 5, not greedy.* `-bs 1` came out **slower** (45 s against 42 s) and produced 14 more words; neither output shows repetition (longest same-token run is 2 in both), so the extra words are real rather than a loop. Beam 5 being simultaneously faster and the higher-quality setting leaves greedy with no case.

*Two concurrent workers, not four.* Over a fixed 720 s workload: 1 worker 3.81×, **2 workers 5.52×**, 4 workers 5.82×. The second worker fills the GPU's idle gaps during sequential token generation; by four the device is saturated and jobs merely queue. N=2 takes 95% of the available gain at half the blast radius if a worker dies. (An earlier version of this also cited VRAM; see the hardware section — VRAM was never the constraint.)

**Consequences** (and see D9 for the one defect this path has). Tier-1's 23.4 h re-runs in ~4.2 h against ~117 h on CPU; the full 176.7 h channel becomes ~32 h rather than ~880 h. Phase 2 moves from implausible to an unattended weekend, and the VAD-lossy Phase 1 corpus is superseded rather than patched.

**Method warning — the same mistake twice.** The first concurrency table showed 2 workers *below* 1 worker. That was an artefact: each N processed a different subset of slices, and slices differ in speech density. Fixing the workload removed it. This is the same error as the first VAD comparison, which changed decoding mode and VAD together. **Vary one thing; hold the workload identical.** Both wrong answers were stated confidently before being caught.

---

## Toolchain

Deliberately **not** committed to this repository — it is a throwaway environment, and pinning it here would imply a reproducibility guarantee that a 3 GB model download and a GPU-driver-sensitive stack cannot honour.

| Piece | Choice | Why |
|---|---|---|
| Python | 3.11 in a dedicated venv | Anaconda's `libiomp5md.dll` collides with CTranslate2's OpenMP runtime; a shared interpreter thrashes threads |
| ASR | `faster-whisper` 1.2.1 / CTranslate2 4.8.1 | Batched pipeline gives ~10× over sequential decoding |
| Fetch | `yt-dlp` 2026.07.04, audio-only | `bestaudio[ext=m4a]/bestaudio`, no re-encoding |
| Decode | PyAV, bundled with faster-whisper | Reads m4a/webm/opus natively — **no ffmpeg needed anywhere** |
| **GPU ASR** | **whisper.cpp @ 2ca53bb, `-DGGML_VULKAN=ON`** | The complete (no-VAD) mode at 5.52× — see D8. Built with MSVC 14.44 + Vulkan SDK 1.4.350.0; `KHR_coopmat` matrix cores active on the W7900 |
| GPU model | `ggml-large-v3.bin` (2952 MB) | HuggingFace `ggerganov/whisper.cpp`; not the CTranslate2 model, a separate download |
| Working area | `E:\MD-Transcription\` (outside the repo); toolchain in `E:\Tools\whisper.cpp` | Audio and intermediates are not repository content |

### Pitfalls that cost real time

- **`whisper-cli` cannot read m4a.** Its miniaudio reader handles wav/mp3/flac/ogg but not AAC, so fetched audio must be decoded to 16 kHz mono PCM WAV first (PyAV does it; still no ffmpeg needed). Budget ~2.7 GB of WAV for Tier-1.
- **Build Tools needs an approved UAC prompt.** `winget install` of the VS C++ workload returns installer exit **1602** — "user cancelled" — and installs nothing if elevation is declined. It cannot be driven from an unelevated non-interactive shell.
- **`vswhere` hides BuildTools instances without `-all`.** `vswhere -products *` returns empty for a Build Tools–only machine and reads as "nothing installed" when the toolchain is in fact present.
- **YouTube throttles a long sequential fetch.** Three of 60 returned `HTTP 403 Forbidden` late in the run and all three succeeded on immediate retry with the same format. Budget a retry pass rather than treating a 403 as unavailability.
- **Anaconda's `onnxruntime` is broken here** (`WinMLDeployMainPackage failed … 0x80073d06`). It silently forces VAD off, which costs roughly 10× in throughput. A clean venv has a working one.
- **OpenMP duplication** between Anaconda MKL and CTranslate2 — same fix.
- **Console encoding**: Windows cp1252 crashes on Devanagari output. Set `PYTHONIOENCODING=utf-8`.
- **Page numbers in the `.md` extracts are not what they look like.** MVD marks pages with a `page-N` *footer*, so content following the marker is on page N+1; JV's extract has only eight stray bare numbers and no pagination at all. Recovering a passage means citing the PDF, not the extract. This produced ~20 wrong citations before it was caught.

---

### D9 — whisper.cpp emits occasional broken UTF-8; accept it, but flag it

The GPU path has one defect the CPU path does not. **whisper.cpp emits partial
UTF-8 when a multi-byte Devanagari character's bytes split across token
boundaries**, leaving a truncated codepoint in the output.

Measured across the first 31 GPU transcripts: **39 broken characters in 473,638
— 0.008% of the text**, about one per 12,000 characters. 13 of the 31 files are
entirely clean; the worst has 7.

Three things establish what this is:

- It affects **both `-otxt` and `-oj`**, so it is upstream of the writer, in the
  token→text conversion. `faster-whisper` does not show it because the Python
  tokenizer buffers incomplete sequences before decoding.
- It is **deterministic** — a fresh re-run of an affected file was byte-identical
  to the original, same offset. Not a concurrency artefact, not caused by the
  batch being killed, and **re-running will not fix it**.
- It appears only on longer files. A 3-minute control slice came out clean;
  30-minute recordings do not.

**Accepted, because the alternative is worse and this one is visible.** VAD was
silently deleting ~20% of words with no trace; this leaves a `U+FFFD` at every
affected position, findable with one grep. Against a promotion workflow that
already normalises the Hindi character by character against the printed corpus,
39 flagged positions across 60 recordings is noise.

**But it must be repaired, not normalised away.** Promotion now includes:
`grep -c $'�'` each transcript, and reconstruct each from context or the
audio. A `U+FFFD` silently smoothed into a plausible character is exactly the
kind of error this programme's reliability marking exists to prevent.

**Two false alarms on the way to this, both mine.** A "0% coverage" report came
from a regex expecting timestamps in `-otxt` output, which has none. And the
first reading of the broken bytes blamed the text writer for splitting
characters at line breaks — the JSON output has the same corruption, which
disproves it. Check the second format before blaming the first.

---

### D10 — `--max-context 0` is mandatory on the GPU path; the default produces repetition loops

A quality review of all 60 GPU transcripts flagged **36 of them**. The worst
carried a single 3-gram 214 times; another repeated *बहुत बहुत बहुत* 36 times
consecutively. Words-per-minute ranged from **31 to 153** against a median of
111 — a spread far too wide to be speaking-rate variation.

The cause is `whisper.cpp`'s default **`--max-context -1`**, which feeds
unbounded prior text into each decode window. Once a phrase repeats, it
conditions its own reproduction, and the window fills with the loop instead of
the audio. `-mc 0` cuts that feedback. It is the exact equivalent of
`faster-whisper`'s `condition_on_previous_text=False` — **which the CPU path
already set**, and which is why the CPU output never looped despite being the
weaker configuration in every other respect.

Measured on `kZ6qdNflDWA` (*भाषा - अर्थ - वस्तु*, 36.3 min), which had a verified
tail loop:

| Decode | Words | wpm | Top 3-gram | Longest run |
|---|---|---|---|---|
| GPU default (`-mc -1`) | 2,893 | 80 | **×119** *रूप में क्रियाएं* | 2 |
| **GPU `-mc 0`** | **3,521** | **97** | ×7 *के रूप में* | 4 |
| CPU (VAD, for reference) | 3,248 | 89 | ×9 | 6 |

The loop collapses from 119 occurrences to 7 — normal frequency for a common
Hindi phrase, matching the CPU run's 9 — and **word count rises 22%**, because
the looped span was overwriting real speech. The corrected GPU output now
carries **more** words than the CPU run (3,521 against 3,248), consistent with
recovering both the loop and VAD's losses.

**No throughput cost.** 429 s for 36.3 min of audio is 5.1× realtime, marginally
*better* than the ~4.4× the same file managed with the default, since the model
is no longer re-processing a growing context.

`-mc 0` is now hardcoded in `_transcribe_batch.py` rather than exposed as a flag.
A configuration that silently degrades output should not be reachable by
forgetting an argument.

**Two things this corrects.** First, an earlier claim here that no anti-loop
guards were set was wrong: `-et 2.40`, `-lpt -1.00`, `-tpi 0.20` and temperature
fallback are all `whisper.cpp` defaults and were active throughout. They limit
*intra-window* degeneration and cannot see a loop sustained across windows by the
context itself. Second, the failure recorded below as a one-file curiosity
(`K7KNzk3uX0k` at 01:11) was never file-specific — it was the default
configuration, visible wherever the audio gave it an opening.

**Reading the flags needs care.** Not every flagged file was looping. *के रूप में*
("in the form of") at ×15–29 across a 5,000-word transcript is ordinary Hindi,
not a defect. The sharp detector is **consecutive** repetition (`maxrun`) and
3-gram counts that are wildly out of proportion to length; raw frequency of a
common phrase is not evidence of anything.

---

### D11 — Whisper inserts YouTube caption boilerplate that was never spoken

Found 2026-08-02 while checking D10's first corrected file. The word
**सब्सक्राइब** ("subscribe") appears **94 times across 30 of the 60 recordings**
on the GPU pass, and 85 times across 23 on the CPU pass. Nagraj does not say it.

The model was trained on YouTube captions, which are saturated with
subscribe-and-like requests, and it emits them into noise, silence and unclear
speech. Position settles what these are:

| Position in recording | Hits |
|---|---|
| First 5% | **0** |
| Mid 5–95% | 31 |
| Last 5% | 3 |

A genuine channel intro would cluster at the start and an outro at the end.
There are **none** at the start; the hits land at 54%, 61%, 72%, 87% — the middle
of philosophical exposition.

**This is worse than the repetition loops, and it survives their fix.** A loop is
self-evident on sight. Boilerplate is fluent, and it can sit inside an otherwise
real sentence:

> कि **सब्सक्राइब** करना चाहिए कि यह जो हम समझा है यह हमारा स्वयंत हमारे पर

One fabricated word in a grammatical Hindi clause, in a corpus whose purpose is
to be quoted. Nothing in the decoder configuration removes it — it is present in
both backends and in `-mc 0` output — so it must be **searched for and deleted by
hand during promotion**. `_transcribe_review.py` now counts it and flags any file
containing it.

**The general lesson is the one that matters.** D9 and D10 are defects that
*degrade* text — visible as corruption or as a density anomaly. This one *adds*
plausible text. Reviewing raw ASR by reading it for sense will not catch a
fabrication that reads perfectly well; only a targeted search will. Assume there
are other insertion classes not yet looked for.

---

### D12 — ROCm/HIP builds and works, and is not worth switching to

Built 2026-08-02 to test whether the Vulkan backend was implicated in the
machine's resets. It is not, and HIP is not faster either.

`whisper.cpp` carries a HIP backend (`ggml/src/ggml-hip`, `-DGGML_HIP=ON`) that
needs neither PyTorch nor CTranslate2, so it sidesteps the dead ends in D3 —
those assessed ROCm only through frameworks that still have no Windows GPU path.
AMD's HIP SDK for Windows supports gfx1100 directly.

Measured on an identical 5-minute slice, same model, same flags:

| Backend | Wall | Realtime | Words |
|---|---|---|---|
| Vulkan | 61.0 s | **4.92×** | 439 |
| HIP / ROCm 7.2 | 63.3 s | 4.74× | 457 |

**Neither difference is meaningful at n=1.** 2.3 s out of 61 is noise, and which
of the 18 disputed words are correct is unknown without listening. The usable
conclusion is negative: there is no throughput reason to switch, so Vulkan stays
the default and HIP is kept as a second opinion — useful mainly as an
independent decoder for the two-model disagreement idea, where the point is that
the backends differ.

**Three traps, in the order they cost time.**

*No OpenMP runtime.* ROCm 7.2 for Windows ships no `libomp` and no `omp.h`
anywhere in its tree, but CMake's `FindOpenMP` probe passes regardless, because
clang accepts `-fopenmp=libomp` as a flag whether or not it can link it. The
build then compiles for twenty minutes and fails linking `ggml-base.dll` on
`__kmpc_fork_call`. `-DGGML_OPENMP=OFF` is required, not optional, and costs
nothing here — ggml falls back to its own thread pool and the work is on the GPU.

*The integrated GPU breaks the HIP build, and `-dev` does not save you.* This
machine exposes two ROCm devices: the 7950X's iGPU as gfx1036, and the W7900 as
gfx1100. A build targeting `gfx1100` alone dies with **`ROCm error: device
kernel image is invalid`** on the first kernel. Selecting the right device with
`-dev 1` does *not* fix it — ggml loads modules across all visible devices, and
the gfx1100-only image cannot load on gfx1036. The fix is to hide the iGPU
entirely: **`HIP_VISIBLE_DEVICES=1`**. Vulkan never had this problem, which is
worth knowing before reading any backend comparison as a like-for-like test.

*`AMDGPU_TARGETS` is deprecated* as of ROCm 7; use `GPU_TARGETS`.

Build script, outside the repo with the rest of the toolchain:
`E:\Tools\whisper.cpp\build-hip.ps1`. It leaves the Vulkan build untouched so
the two remain comparable.

**This settles the question it was built to answer.** The resets are not a
Vulkan fault. Both backends drive the same silicon at the same power, and a
reset carrying `BugcheckCode 0` is not something any user-mode API can cause.

**HIP is nevertheless the scripts' default, by decision rather than by
measurement.** Recorded plainly because the numbers above do not support it and
a later reader should not mistake the default for evidence. Reverting is one
environment variable — `WHISPER_CPP_CLI` pointed at the Vulkan build — and the
Vulkan build is deliberately left in place for exactly that.

`_transcribe_batch.py` carries the two runtime requirements so nobody has to
remember them: it prepends the SDK's `bin` to `PATH`, without which the process
dies at `0xC0000135` before printing anything (only `amdhip64` is copied to
System32; `hipblas.dll` and rocBLAS's Tensile libraries are not), and it hides
secondary GPUs by picking the largest-VRAM device into `HIP_VISIBLE_DEVICES`,
announcing the choice and yielding to the variable if already set.

**One caveat that outlives the benchmark.** The two backends do not produce
identical text — 439 words against 457 on the control slice, and on
`a1ARueeihmA` Vulkan resolved *चुम्बकीयता* where HIP split it into *चुम्ब की
अता*. That is fourteen words of one file against an older decode, so it is an
observation and not a finding. But it means **a backend switch is a change to
the corpus, not a free optimisation**, and any transcript's provenance must
record which backend produced it. It also strengthens the two-model
disagreement idea: two decoders that differ are more useful for locating
uncertain passages than either is alone.

---

### D13 — Phase 4 automation prepares evidence; it never awards reliability

The fixed five-video pilot was timestamp-rerun on August 3, 2026: 83:27 of
audio, five successes, zero failures, no VAD, beam 5, `--max-context 0`, and
9.52× aggregate realtime on two HIP workers. Every rerun matched the frozen
canonical text, so the batch published native JSON and the exact decoder JSON
without a timestamp conflict. The Phase-1 baseline still verifies at 181
entries because timestamp evidence is additive and the frozen inputs were not
changed.

The Phase-4 preparation pipeline converted that evidence into **394 native
segments** under `E:\MD-Transcription`:
136 for `KTeH3rM2qK8`, 59 for `OIkSW7QYry4`, 68 for `vuTOjdF6a3k`, 18 for
`a1ARueeihmA`, and 113 for `pk3UxjDkhiE`. The aggregate queue isolates four
segments carrying `U+FFFD`, seventeen containing boilerplate candidates, four
with consecutive repetition runs, 206 containing controlled terminology, and
two containing `चुम्बकीयता`. Deterministic Layer A proposes changes in 78
segments; those proposals are not reviewed Hindi.

On August 9, 2026, the reviewer interface moved from TSV to one
`*-phase4-review.xlsx` workbook beside each session's evidence. The workbooks
use a Devanagari-capable Excel font and contain `Instructions`, `Segments`,
`Corrections`, and `Provenance` sheets. `Scripts/_build_transcription_review_xlsx.ps1`
builds them with the bundled spreadsheet runtime;
`Scripts/_sync_transcription_review_xlsx.py` reads Excel directly, validates the
review gates, and exports UTF-8-with-BOM TSV only when `--sync-tsv` is requested.
The Excel workbook is now the reviewer-facing source of truth; the aggregate
TSV remains migration and audit input rather than the file reviewers edit.

The governing decision is negative: **automation may never turn an unflagged
segment into `[P]` or `[R]`.** Every segment begins `UNREVIEWED`; reviewed Hindi,
English, evidence, reviewer and review date stay blank until a listener fills
them. `--check` fails while any segment remains unreviewed, while a Level-3
target lacks English, or when evidence hashes drift. Packet preparation is an
implemented Phase-4 prerequisite, not completed audio review and not promotion.

---

## Phase 1-3 quality implementation (2026-08-03)

### Immutable Phase-1 baseline

`Scripts/_freeze_transcription_baseline.py` freezes and verifies the manifest,
audio, canonical D10 GPU transcripts, and staged raw-ASR sidecars. The current
baseline at `E:\MD-Transcription\BASELINE-SHA256.tsv` has **181 SHA-256
entries**: one manifest and 60 files in each of the other three classes.
`--check` recomputes the corpus and exits non-zero on any drift without
rewriting the baseline. A normal freeze refuses to replace existing baseline
files; replacement requires the explicit `--force` flag.

All 60 staged raw sidecars equal the canonical D10 text after decoding known
D9 invalid UTF-8 with replacement markers and normalising line endings. None
is byte-identical because whisper.cpp emitted CRLF on Windows while the staged
working copies passed through the repository's LF normalisation. Both byte
forms are preserved and independently hashed; the baseline records that
distinction instead of pretending they are identical.

The pre-D10 `transcripts-gpu\` directory now carries an explicit obsolete
marker. It remains comparison evidence and is never a promotion source.

### Native timestamp output

The GPU path now emits a safe three-file set: `.txt`, valid UTF-8 full `.json`,
and exact decoder `.raw.json`. Full JSON supplies native segment offsets and
token metadata. Because whisper.cpp still writes occasional invalid UTF-8 in
full JSON, the raw bytes are preserved while the valid JSON represents each
bad sequence as `U+FFFD` and records every original byte offset under
`_transcription_pipeline`.

Publishing is atomic. When an older canonical `.txt` exists without JSON, the
rerun text must be byte-identical before timestamp files are accepted. A
difference leaves the old text untouched and preserves all rerun outputs under
`.timestamp-conflict.*`.

Control `hITrFtQsUac` (2:20) passed on the HIP/W7900 path: the timestamp rerun
was byte-identical to the frozen text (SHA-256
`1c2dcc6777a4378f13f6b0928a9a2cca23e56df6843d4d200798a341732c1ee9`),
produced seven native segments through 134.66 s, and logged four invalid raw
JSON byte offsets. The result and all three outputs live under
`E:\MD-Transcription\validation\timestamp-control\`.

### Controlled term-sense registry

`Scripts/_transcription_terminology_registry.py` seeds, validates, queries, and
renders the private work registry. The registry has **60 accepted entries**. It
carries accepted variants, observed ASR
confusions, transliteration, canonical and source-specific English, sense,
authority/locator, decision status, and notes. Candidate ASR confusions are
review prompts, never global replacements.

By user decision on August 3, 2026, `चुम्बकीयता` → “magnetism” and
`चुम्बकीय धारा` → “magnetic current” are accepted for transcript cleanup and
automatic translation protection. Their exact published contexts should still
be checked when a source passage is cited; that citation check does not make
their registry status provisional.
The registry also encodes source-specific distinctions such as MVD's “direct
recognition” and JV's “revelation” for `साक्षात्कार`, and forbids automatic
`धर्म` → “religion” and technical `अनुभव` → “experience”.

These three phases establish provenance, timestamps, and terminology control.
They do **not** make any Tier-1 transcript citable; the five-video audio-checked
pilot is next.

---

## Hardware, and where the bottleneck actually is

The machine this programme runs on, and what each resource was doing mid-GPU-run (2026-08-02, 24 of 60 files in):

| Resource | Spec | In use during the GPU run |
|---|---|---|
| CPU | Ryzen 9 7950X, 16c/32t | **49%** — roughly half idle |
| RAM | 63.2 GB | 17.3 GB used, **45.9 GB free** |
| GPU | Radeon PRO W7900, 45 GB usable | both compute queues saturated |
| VRAM | 45 GB | **3.94 GB per worker, 7.9 GB for the pair**; ~31 GB free |
| Disk | 4 SSDs (3 NVMe, 1 SATA) | **0.1% busy, sub-millisecond latency** |
| Free space | `C:` 422 GB · `E:` 824 GB | corpus + WAV ≈ 4 GB |

**Only the GPU is saturated. Nothing else is close.** For contrast, the CPU pipeline ran at 97% CPU; the GPU run leaves half the machine idle.

**Disk is not and will not be a bottleneck.** Each worker reads its WAV once at startup — a 30-minute recording is ~58 MB, read in a fraction of a second — then computes for 6–10 minutes and writes ~50 KB of text. The only I/O-heavy moment is the one-off WAV conversion at the start of a batch (~2.7 GB for Tier-1), which takes a couple of minutes. The `wav/` directory is disposable and can be deleted after a run.

**This corrects part of D8's reasoning.** N=2 was chosen partly to conserve VRAM. VRAM was never the constraint — two workers use 7.9 GB of 45, and four would fit trivially at ~16 GB. The decision stands, but **on compute saturation alone**: the GPU's queues are already full at two workers, so more workers only queue. The ~31 GB of headroom does mean a larger model or higher-precision inference would fit comfortably, should either ever look worthwhile.

**Phase 2 sizing.** The full 176.7 h channel needs roughly 10 GB of source audio and ~20 GB of intermediate WAV — negligible against 824 GB free on `E:`.

**Temperatures could not be read** until HWiNFO64 was installed mid-programme. `MSAcpi_ThermalZoneTemperature` returns "Not supported" on this board (normal for desktop Ryzen) and AMD exposes no thermal WMI class, so WMI alone will not do it. With HWiNFO64 logging, temperatures under sustained GPU load are unremarkable.

### Unresolved: the machine hard-reboots

**This is an operational risk for Phase 2 and is not understood.** The Windows event log records **8 unexpected restarts in 90 days**, three of them on 2026-08-02 (09:05, 10:31, 12:40). All are Kernel-Power **Event 41 with `BugcheckCode 0`** — meaning Windows was not the thing that stopped. There is no crash dump because there was no crash: power was cut or the board reset. No WHEA errors and no TDR 4101 anywhere in the log.

Three explanations were proposed and each was falsified:

- *Coincidence with the transcription run* — the reboots predate the programme.
- *SMU contention from vendor monitoring software* — reboots continued unchanged after it was removed.
- *GPU load* — an unbroken 8-hour GPU batch completed cleanly, and the 12:40 reboot happened at idle.

The 12:40 event preceded a **grey screen with three green vertical lines**, which is display-output corruption, not a software fault. Together with Event 41 and normal temperatures, that points at hardware: PSU delivery under transient load, GPU seating or auxiliary power connectors, or memory. **No software change will fix this**, and long unattended Phase 2 runs should be assumed to be interruptible until it is diagnosed. The pipeline's resumability (D5) is what has made the interruptions survivable so far.

**HWiNFO64 logging did not capture the moment.** It buffers, and the last 8 minutes before the 12:40 reset — the interesting part — were lost. Enable flush-on-write and auto-start at boot before relying on it as evidence.

**Mitigated, not fixed: `Scripts/_transcribe_autoresume.ps1`.** Registers a Scheduled Task that re-runs the batch three minutes after logon, so a reset costs only the recording in flight instead of the remaining hours. It triggers at *logon* rather than at *startup* deliberately — a task running as SYSTEM in session 0 generally cannot enumerate the GPU, so a Vulkan build fails there. Two guards matter: it looks for a live `whisper-cli` or batch process before starting, since a manually launched run holds no lock and a second batch would double GPU load and race two writers onto the same file; and it treats a lock file from a dead PID as evidence of the reset it exists to recover from, not as a reason to refuse. It writes a journal recording every start, skip and exit alongside the boot time, which accumulates into a record of when the machine died and what it was doing.

**One prerequisite this exposed.** D5 claimed each transcript was written to `.partial` and atomically renamed. That was true of the original working script but not of `_transcribe_batch.py`'s CPU path, which streamed into the final `.txt` as `faster-whisper` yielded segments — so a reset mid-decode would leave a truncated file that the resume check skips as complete, silently, reading as a short recording rather than a broken one. Harmless while runs were attended; not harmless under unattended auto-resume. Now fixed to write-then-rename, matching the GPU path, where `whisper-cli` already wrote once at the end.

**What the reboots are is still unknown.** Four hypotheses have now been falsified: coincidence with the programme, SMU contention from vendor monitoring software, GPU load, and failed resume from sleep — the last ruled out because this machine is configured never to sleep on AC and no sleep or resume event appears near any reset. Two further observations narrow it. **Five of the seven pre-programme resets fall between 05:12 and 06:05**, a 53-minute window across six weeks, with no GPU work and no sleep transition. And in 95 days there is **not one GPU driver event** — no TDR 4101, no adapter reset, no recovery — while every reset carries `BugcheckCode 0`, meaning Windows never ran a crash handler. A driver fault produces a bugcheck or a recovery; this produces neither. The evidence points below the operating system, at power delivery, and the early-morning clustering is consistent with an external mains event rather than anything the computer is doing.

---
## Phase 1 status

**Scope:** 60 recordings, 23.43 h. **Fetch:** complete. **Transcription:** CPU and pre-D10 GPU complete; **D10 GPU re-run complete** (60/60, zero failures, aggregate 5.12× realtime). **Work corpus:** `E:\MD-Transcription\Nagraj-Recorded-Sessions\` (moved out of References 2026-08-03) — see that folder's `RAW-ASR-TIER1.md`. **In References / promoted:** still only the 2010 Sakshatkar session.

**Quality infrastructure:** Phase-1 baseline frozen and verified (181 hashes);
native timestamp JSON control passed; controlled terminology registry valid at
60 entries. These are infrastructure milestones, not promotions.

| Study | Videos | Hours | Fetched | Transcribed | Staged raw ASR | Promoted |
|---|---|---|---|---|---|---|
| Spiritual Practice | 16 | 7.48 | 16 | 16 | 16 | 1 (2010 session; not in Tier-1 manifest) |
| Epistemology | 16 | 6.15 | 16 | 16 | 16 | 0 |
| Axiology | 14 | 5.67 | 14 | 14 | 14 | 0 |
| Ontology | 14 | 4.13 | 14 | 14 | 14 | 0 |
| **Total** | **60** | **23.43** | **60** | **60** | **60** | **1** |

**D10 re-run finished 2026-08-02** into `E:\MD-Transcription\transcripts-gpu-mc0`, then staged by `Scripts/_stage_tier1_raw_asr.py`. Manifest: `E:\MD-Transcription\manifest-tier1.tsv`. The staged tree was later moved to `E:\MD-Transcription\Nagraj-Recorded-Sessions\` (not committed). Pre-D10 GPU output remains in `transcripts-gpu\` for comparison only; do not promote from it.

### Corpus quality review (D10 re-run)

Mechanical review of the `-mc 0` corpus — word density against duration, longest consecutive token run, most frequent 3-gram, Devanagari share, and `U+FFFD` count. Full table: `E:\MD-Transcription\Nagraj-Recorded-Sessions\RAW-ASR-TIER1.md`.

| | Pre-D10 GPU | D10 (`-mc 0`) staged |
|---|---|---|
| Present | 60/60, 136,188 words | 60/60, 154,094 words |
| Words per minute | median 111, **range 31–153** | median **108**, **range 88–137** |
| Devanagari share | 99–100% | 98–100% |
| `U+FFFD` | 47 across 26 files | 131 across 47 files (D9) |
| Boilerplate | ~94 / 30 files | 354 across 54 files (D11) |
| Severe `maxrun` ≥ 15 | (loops were widespread) | **7 files** (listed in the index) |

**Density is fixed.** Staging is triage and search material, not promotion.
Layer A removed all 354 detected D11 boilerplate hits and collapsed 37 repeat
runs, with every event logged. Seven files still carry serious loop
neighbourhoods, every boilerplate-deletion neighbourhood needs audio review,
and all 131 D9 `U+FFFD` positions require repair from context or audio.

`Scripts/_transcribe_review.py` exits non-zero when anything is flagged. Run it after every batch.

**Nobody has listened to the Tier-1 audio for promotion.** Statistics decided the decode configuration; listening decides what may be cited.

### What the run actually cost

| | |
|---|---|
| Wall time | 7.67 h (57 files) + 0.21 h (3 stragglers) |
| Aggregate throughput | **2.98×** realtime |
| Mean `avg_logprob` | **-0.116**, range -0.076 (*अनुसन्धान और शोध*) to -0.179 |
| Failures | 0 |

**The synthetic benchmark overstated throughput by about 10%** — 3.25× on 5-minute slices against 2.98× on real recordings. Slices under-represent model-load amortisation and over-represent dense speech. Quote the real figure when planning Phase 2.

### Two findings from the run

**Fetch 403s are rate-limiting, not unavailability.** Three of 60 failed with `HTTP Error 403: Forbidden` after 57 sequential downloads. All three succeeded on retry **with the identical format**, so a retry pass — or a longer delay between requests — is all that is needed. `retry_failed.py` walks four format/client combinations but never got past the first.

**Five threads per worker may beat four, contradicting D4.** The 3-straggler pass ran 3 × 5 threads and recorded per-worker rates of **1.01×, 1.22×, 1.27×**, against 0.69–0.97× throughout the 4 × 4 main batch. If four workers at five threads sustain even 1.0× each, that is 4.0× aggregate against the 2.98× achieved. **Not yet a conclusion** — those were short files and 15 threads contends less than 16 — but it is a cheap experiment and it points away from the optimum the synthetic benchmark picked. Test before Phase 2.

### Known ASR failure mode

`K7KNzk3uX0k` at 01:11 collapses into a repetition loop (`वो वो वो वो …`)
across roughly 30 seconds — the classic Whisper behaviour on a low-information
stretch. It is visible in the text and in a depressed `avg_logprob`, so it does
not corrupt anything silently. The original D10 GPU corpus was text-only; the
new full timestamp JSON records native offsets and token probabilities for
future pilot and promotion reruns. These signals locate review targets but do
not replace listening.

**Read as file-specific, this was wrong.** The review above found the same collapse in 36 of 60 GPU transcripts, and D10 identifies the cause as the decoder's context setting rather than anything in the audio. Low-information stretches are only where it becomes visible. The advice to check per-segment confidence stands; the diagnosis it was attached to does not.

### Content worth reading first

Three recordings already look consequential for live studies, on a first skim of raw output:

- **`8WNTuXNtawg` न्याय - धर्म - सत्य** (56 min) — at 04:35, that language points at *nyaya, dharma, satya* and at nothing else, everything else remaining in *kalpana*; and that whatever is to be evidenced is these three. Bears on §1.1's evaluation triad and on §1.10's word–meaning–*vastu* analysis.
- **`QgqtqALvMLw` अनुसन्धान और शोध** (53 min, the corpus's most confident transcript at -0.076) — distinguishes *anusandhan* driven by an *apeksha* present in the person but absent from the *parampara*. Bears on §1.8 and §6.2, where the study currently rests on a single oral remark.
- **`K7KNzk3uX0k`** (16 min) — a questioner presses on what was actually seen in *samadhi*, and the answer is that it was **neither *drishti gochar* nor *gyan gochar***. The study records only that *samadhi* was contentless; this is a positive characterisation of what was there and why it does not count as knowing. Bears on §1.2. *(The title is English; the dialogue is Hindi.)*

### What "transcribed" does and does not mean

A raw ASR pass is **not** a References artefact. Promoting one means: normalising the Devanagari without supplying words the ASR did not carry; translating against `MD-Mapping.xlsx` and the published MVD/SB/JV English; marking every segment **[R]/[P]/[U]**; cross-referencing the printed corpus; and tabulating the passages that need the audio checked. The 2010 session took several passes to reach that standard, and a corpus pass over the printed texts later recovered seven of its uncertain segments and corrected six terms. **Expect the same per recording — bulk ASR is the cheap part.** And per D7, promotion starts from a *sequential* re-run, not from the batched Phase 1 output.

---

## Further expansion candidates (not started)

1. **The सहअस्तित्ववादी विज्ञान series** — 17 parts, 20.1 h, the systematic ontology exposition. Largest single coherent block on the channel and the obvious next target for the Ontology study. ~3.6 h on GPU.
2. **Full-channel transcription** — the remaining ~150 h, so that routing by transcript search (D1) becomes possible across the whole corpus rather than a curated slice. **~32 h on GPU at 5.52×**, against ~880 h on CPU. This is what D8 unlocks.
3. ~~GPU revisit~~ — **done, see D8.** DirectML tested and rejected; Vulkan built and adopted.
4. ~~Engine accuracy comparison~~ — **done.** Superseded by D7 and D8: the meaningful variable turned out to be VAD, not the engine, and whisper.cpp Vulkan is both more complete and faster than either CPU configuration.

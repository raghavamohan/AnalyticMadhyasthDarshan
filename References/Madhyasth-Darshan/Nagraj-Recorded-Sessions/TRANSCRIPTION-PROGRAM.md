# Transcription programme — recorded sessions of Shri A. Nagraj

**Started:** August 1, 2026 · **Status:** Phase 1 in progress
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

**Deferred, not dismissed.** Phase 1 is ~7 h on CPU either way; the remaining ~150 hours would be ~46 h, which is where a Vulkan build earns its install cost.

### D4 — Four worker processes, not one wide one

Measured on Ryzen 9 7950X (16c/32t), 5-minute slices, real audio:

| Workers × threads | Aggregate | 23.4 h would take |
|---|---|---|
| 1 × 16 | 2.23× | 10.5 h |
| **4 × 4** | **3.25×** | **7.2 h** |
| 8 × 2 | 2.91× | 8.0 h |

CTranslate2's int8 beam search does not scale past roughly 4 threads, and eight copies of large-v3 contend for memory bandwidth. **4 × 4 is the measured optimum.** Caveat: the 8 × 2 rung overlapped with the fetch competing for the machine, so its figure is mildly pessimistic; the shape of the curve is what the choice rests on.

### D5 — Batch ordering and resumability

Longest-first, so the 90-minute file does not strand three idle workers at the end. Each `.txt` is written to `.partial` and atomically renamed, so a completed file is never half-written and a restart skips it. The batch can be killed and resumed freely.

### D6 — One directory per recording, video ID in the name

See [`README.md`](README.md). The channel has genuine title collisions, so the ID is the only stable identifier. The first transcript predates the rule and keeps its plain slug.

---

## Toolchain

Deliberately **not** committed to this repository — it is a throwaway environment, and pinning it here would imply a reproducibility guarantee that a 3 GB model download and a GPU-driver-sensitive stack cannot honour.

| Piece | Choice | Why |
|---|---|---|
| Python | 3.11 in a dedicated venv | Anaconda's `libiomp5md.dll` collides with CTranslate2's OpenMP runtime; a shared interpreter thrashes threads |
| ASR | `faster-whisper` 1.2.1 / CTranslate2 4.8.1 | Batched pipeline gives ~10× over sequential decoding |
| Fetch | `yt-dlp` 2026.07.04, audio-only | `bestaudio[ext=m4a]/bestaudio`, no re-encoding |
| Decode | PyAV, bundled with faster-whisper | Reads m4a/webm/opus natively — **no ffmpeg needed anywhere** |
| Working area | `E:\MD-Transcription\` (outside the repo) | Audio and intermediates are not repository content |

### Pitfalls that cost real time

- **Anaconda's `onnxruntime` is broken here** (`WinMLDeployMainPackage failed … 0x80073d06`). It silently forces VAD off, which costs roughly 10× in throughput. A clean venv has a working one.
- **OpenMP duplication** between Anaconda MKL and CTranslate2 — same fix.
- **Console encoding**: Windows cp1252 crashes on Devanagari output. Set `PYTHONIOENCODING=utf-8`.
- **Page numbers in the `.md` extracts are not what they look like.** MVD marks pages with a `page-N` *footer*, so content following the marker is on page N+1; JV's extract has only eight stray bare numbers and no pagination at all. Recovering a passage means citing the PDF, not the extract. This produced ~20 wrong citations before it was caught.

---

## Phase 1 status

**Scope:** 60 recordings, 23.43 h. **Fetch:** in progress. **Transcription:** chained to start on fetch completion.

| Study | Videos | Hours | Fetched | Transcribed | In References |
|---|---|---|---|---|---|
| Spiritual Practice | 16 | 7.48 | — | — | 1 (the 2010 session) |
| Epistemology | 16 | 6.15 | — | — | 0 |
| Axiology | 14 | 5.67 | — | — | 0 |
| Ontology | 14 | 4.13 | — | — | 0 |
| **Total** | **60** | **23.43** | **in progress** | **0** | **1** |

Manifest: `E:\MD-Transcription\manifest-tier1.tsv` (study, duration, video ID, title).

### What "transcribed" does and does not mean

A raw ASR pass is **not** a References artefact. Promoting one means: normalising the Devanagari without supplying words the ASR did not carry; translating against `MD-Mapping.xlsx` and the published MVD/SB/JV English; marking every segment **[R]/[P]/[U]**; cross-referencing the printed corpus; and tabulating the passages that need the audio checked. The 2010 session took several passes to reach that standard, and a corpus pass over the printed texts later recovered seven of its uncertain segments and corrected six terms. **Expect the same per recording — bulk ASR is the cheap part.**

---

## Phase 2 candidates (not started)

1. **The सहअस्तित्ववादी विज्ञान series** — 17 parts, 20.1 h, the systematic ontology exposition. Largest single coherent block on the channel and the obvious next target for the Ontology study.
2. **Full-channel transcription** — the remaining ~150 h, so that routing by transcript search (D1) becomes possible across the whole corpus rather than a curated slice.
3. **GPU revisit** — worth the toolchain cost only at Phase 2 scale; see D3.
4. **Engine accuracy comparison** — still outstanding. Both engines should be run on the 03:00–06:00 control slice of the 2010 session, where known-good wording exists to diff against, before any decision to switch. Needs a quiet machine to be meaningful.

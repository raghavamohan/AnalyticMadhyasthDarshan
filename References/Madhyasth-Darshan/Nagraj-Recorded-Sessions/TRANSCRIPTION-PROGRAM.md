# Transcription programme — recorded sessions of Shri A. Nagraj

**Started:** August 1, 2026 · **Status:** Phase 1 raw ASR complete (60/60, 2026-08-02); promotion to References artefacts not started
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

- **YouTube throttles a long sequential fetch.** Three of 60 returned `HTTP 403 Forbidden` late in the run and all three succeeded on immediate retry with the same format. Budget a retry pass rather than treating a 403 as unavailability.
- **Anaconda's `onnxruntime` is broken here** (`WinMLDeployMainPackage failed … 0x80073d06`). It silently forces VAD off, which costs roughly 10× in throughput. A clean venv has a working one.
- **OpenMP duplication** between Anaconda MKL and CTranslate2 — same fix.
- **Console encoding**: Windows cp1252 crashes on Devanagari output. Set `PYTHONIOENCODING=utf-8`.
- **Page numbers in the `.md` extracts are not what they look like.** MVD marks pages with a `page-N` *footer*, so content following the marker is on page N+1; JV's extract has only eight stray bare numbers and no pagination at all. Recovering a passage means citing the PDF, not the extract. This produced ~20 wrong citations before it was caught.

---

## Phase 1 status

**Scope:** 60 recordings, 23.43 h. **Fetch:** in progress. **Transcription:** chained to start on fetch completion.

| Study | Videos | Hours | Fetched | Transcribed | In References |
|---|---|---|---|---|---|
| Spiritual Practice | 16 | 7.48 | 16 | 16 | 1 (the 2010 session) |
| Epistemology | 16 | 6.15 | 16 | 16 | 0 |
| Axiology | 14 | 5.67 | 14 | 14 | 0 |
| Ontology | 14 | 4.13 | 14 | 14 | 0 |
| **Total** | **60** | **23.43** | **60** | **60** | **1** |

**Raw ASR for all 60 completed 2026-08-02, zero failures.** Manifest: `E:\MD-Transcription\manifest-tier1.tsv` (study, duration, video ID, title); transcripts and per-segment JSON in `E:\MD-Transcription\transcripts\`. None has yet been promoted to a References artefact — see the standard below.

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

`K7KNzk3uX0k` at 01:11 collapses into a repetition loop (`वो वो वो वो …`) across roughly 30 seconds — the classic Whisper behaviour on a low-information stretch. It is visible in the text and in a depressed `avg_logprob`, so it does not corrupt anything silently, but **check for it when promoting a transcript**: `no_speech_prob` and `avg_logprob` are recorded per segment in the sibling `.json` precisely so loops and dropouts can be found without re-listening to everything.

### Content worth reading first

Three recordings already look consequential for live studies, on a first skim of raw output:

- **`8WNTuXNtawg` न्याय - धर्म - सत्य** (56 min) — at 04:35, that language points at *nyaya, dharma, satya* and at nothing else, everything else remaining in *kalpana*; and that whatever is to be evidenced is these three. Bears on §1.1's evaluation triad and on §1.10's word–meaning–*vastu* analysis.
- **`QgqtqALvMLw` अनुसन्धान और शोध** (53 min, the corpus's most confident transcript at -0.076) — distinguishes *anusandhan* driven by an *apeksha* present in the person but absent from the *parampara*. Bears on §1.8 and §6.2, where the study currently rests on a single oral remark.
- **`K7KNzk3uX0k`** (16 min) — a questioner presses on what was actually seen in *samadhi*, and the answer is that it was **neither *drishti gochar* nor *gyan gochar***. The study records only that *samadhi* was contentless; this is a positive characterisation of what was there and why it does not count as knowing. Bears on §1.2. *(The title is English; the dialogue is Hindi.)*

### What "transcribed" does and does not mean

A raw ASR pass is **not** a References artefact. Promoting one means: normalising the Devanagari without supplying words the ASR did not carry; translating against `MD-Mapping.xlsx` and the published MVD/SB/JV English; marking every segment **[R]/[P]/[U]**; cross-referencing the printed corpus; and tabulating the passages that need the audio checked. The 2010 session took several passes to reach that standard, and a corpus pass over the printed texts later recovered seven of its uncertain segments and corrected six terms. **Expect the same per recording — bulk ASR is the cheap part.** And per D7, promotion starts from a *sequential* re-run, not from the batched Phase 1 output.

---

## Phase 2 candidates (not started)

1. **The सहअस्तित्ववादी विज्ञान series** — 17 parts, 20.1 h, the systematic ontology exposition. Largest single coherent block on the channel and the obvious next target for the Ontology study.
2. **Full-channel transcription** — the remaining ~150 h, so that routing by transcript search (D1) becomes possible across the whole corpus rather than a curated slice.
3. **GPU revisit** — worth the toolchain cost only at Phase 2 scale; see D3.
4. **Engine accuracy comparison** — still outstanding. Both engines should be run on the 03:00–06:00 control slice of the 2010 session, where known-good wording exists to diff against, before any decision to switch. Needs a quiet machine to be meaningful.

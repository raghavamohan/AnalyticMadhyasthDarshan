# Transcription Quality Plan

**Programme:** Recorded sessions of Shri A. Nagraj from Rakesh Gupta's YouTube channel
**Current phase:** Phase 4 Excel review workbooks prepared; complete audio review pending
**Plan date:** August 9, 2026
**Work area:** `E:\MD-Transcription`
**Repository destination for promoted sessions:** `References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/`

## 1. Objective

Develop a reliable workflow that converts the existing 60-video ASR corpus into:

1. a searchable, mechanically cleaned Hindi corpus;
2. audio-checked Hindi transcripts with Madhyasth Darshan terminology correctly decoded in Devanagari; and
3. selected citable bilingual reference artefacts whose English follows the published terminology of MVD, SB, JV and KD.

The immediate objective is not to promote all 60 recordings. It is to validate the quality workflow on a representative five-video pilot, measure the human effort required, and then promote recordings according to their value for current studies.

## 2. Current baseline

### Implementation status — August 3, 2026

- **Phase 1 complete:** 181 SHA-256 entries freeze the manifest, 60 audio files,
  60 canonical D10 transcripts, and 60 staged raw sidecars. Verification passes
  with `Scripts/_freeze_transcription_baseline.py --check`.
- **Phase 2 complete:** The GPU pipeline now emits byte-protected text, valid
  UTF-8 full JSON with native segment offsets, and exact raw decoder JSON.
  Existing canonical text is never overwritten unless a rerun is byte-identical.
  Control `hITrFtQsUac` produced seven native segments and identical text; four
  invalid raw-JSON byte positions were logged without loss of the raw bytes.
- **Phase 3 complete:** `TERMINOLOGY-REGISTRY.json` contains 60 accepted,
  controlled term-sense entries. It records authority
  order, source-specific English, ASR confusions, forbidden generic renderings,
  and review status. A validator, query CLI and Markdown renderer are available.
- **Phase 4 infrastructure complete:** all five recordings now have native
  timestamp JSON, exact raw decoder JSON, audio/decoder hashes, provenance and
  an Excel review workbook beside the session evidence. Each workbook has
  `Instructions`, `Segments`, `Corrections`, and `Provenance` sheets. The 394
  native segments all remain `UNREVIEWED` until a listener checks the audio.
- **Next phase:** Complete the human listening, Hindi locking, translation and
  second-review gates. Packet preparation alone has promoted no transcript.

### 2.1 Corpus coverage

- Manifest: 60 recordings across Spiritual Practice, Epistemology, Axiology and Ontology.
- Total audio: 23.43 hours.
- Audio downloads: 60/60 complete.
- Corrected GPU transcription: 60/60 complete.
- Canonical Phase-1 decode: `E:\MD-Transcription\transcripts-gpu-mc0`.
- Decoder configuration: whisper.cpp `large-v3`, Hindi, beam 5, no VAD, `--max-context 0`.
- Output: 154,094 words; median 108 words/minute; range 88-137 words/minute.

The realistic density range confirms that the severe pre-D10 decoder-loop failure has been corrected.

### 2.2 Staged working corpus

Every recording has:

- an immutable `*-raw-asr.txt` decoder dump;
- a Layer-A `*-cleaned.txt` sidecar; and
- a `*-clean-log.json` audit log.

Layer A has:

- removed 354 fabricated YouTube boilerplate hits;
- collapsed 37 consecutive-token loops;
- applied 1,162 context-free normalisations; and
- logged 131 `U+FFFD` replacement characters across 47 files without guessing repairs.

Twenty-two recordings contain at least one collapsed-loop neighbourhood. Seven have severe pre-clean loops and require focused audio review:

| Video ID | Pre-clean maximum run | Subject |
|---|---:|---|
| `QA1WhtS2Gzo` | 59 | Further exploration or study |
| `MeFEslxQ1XU` | 57 | Saamya energy and activity energy |
| `NdlSGSwvqVs` | 34 | Sanskar and prarabdha, part 3 |
| `1DAyP7XsEXM` | 24 | Form/property and essential nature/dharma |
| `pk3UxjDkhiE` | 20 | Regulation, control and balance |
| `W6TNMEQIPUA` | 16 | Purposes in relationships |
| `QgqtqALvMLw` | 15 | Exploration and research |

### 2.3 Existing bilingual drafts

Eight recordings have machine-generated bilingual Markdown, HTML and PDF working drafts. Together they contain:

- 506 segments;
- 455 automatically assigned `[P]` segments;
- 51 automatically assigned `[U]` segments;
- zero genuinely reviewed `[R]` segments; and
- five explicit translation failures.

These files are scaffolds, not promotion-ready references. Their timestamps are estimated from cumulative word count rather than produced by the decoder. Their English is Google machine translation with selected technical terms protected. No complete audio review has been performed.

The remaining 52 recordings are Layer-A cleaned Hindi ASR only.

### 2.4 Existing 2010 reference transcript

The 2010 *Sakshatkar-Bodh-Anubhav-Praman* transcript is the editorial and evidential template for future sessions: provenance, raw-ASR preservation, normalisation conventions, bilingual segments, reliability marks, printed-corpus cross-references and a verification table.

It is not yet a complete audio-quality gold standard. Its later portion was produced with VAD-segmented decoding and the document states that the Hindi has not been checked against the audio by a Hindi speaker. It should be re-decoded fully with the current no-VAD configuration and re-reviewed after the pilot workflow is established.

## 3. Governing principles

1. **Never use VAD.** It drops speech at emphasis-flanked pauses and the loss is biased toward doctrinal content.
2. **Always use `--max-context 0`.** Unlimited previous-text conditioning caused self-reinforcing repetition loops.
3. **Raw ASR is immutable.** All repairs occur in sidecars with an audit trail.
4. **Do not supply unheard words silently.** A reconstruction from a printed text must be bracketed and cite the text used.
5. **A statistical review selects the decoder; listening signs off a transcript.**
6. **Lock Hindi before translating.** English must not conceal unresolved Hindi.
7. **Printed texts govern oral material.** A recording never outweighs MVD, SB, JV or KD.
8. **Source-specific English is preserved.** Do not force one global English word where published translations make a meaningful contextual distinction.
9. **Promotion is selective.** Searchability across all 60 is useful; full bilingual promotion of every recording may not justify its human cost.

## 4. Deliverable levels

### Level 1 — Search corpus

All 60 recordings, mechanically cleaned and searchable. This level may retain unresolved ASR errors but must preserve raw input and cleanup logs. It is useful for discovery and routing, not citation.

### Level 2 — Reviewed Hindi

The entire recording has been listened through. Hindi is segmented with native timestamps, doctrinal words are normalised, uncertainty is marked, and all repairs have an audit record. English translation is optional.

### Level 3 — Citable bilingual reference

Reviewed Hindi plus post-edited English, authoritative terminology, printed-corpus cross-references, reliability marks, audio-verification table, Markdown/HTML/PDF artefacts and reference catalog entries.

Only Level 3 sessions are promoted into the repository's `References/` tree.

## 5. Phase A — Preserve and stabilise the baseline

1. Treat `transcripts-gpu-mc0` as the canonical Phase-1 ASR generation.
2. Hash the manifest, audio files and canonical raw transcripts with SHA-256.
3. Mark `transcripts-gpu` as obsolete pre-D10 comparison output; do not promote from it.
4. Retain the CPU transcript/JSON generation only as comparison material where useful.
5. Preserve every Layer-A log permanently.
6. Review and correct status-document drift. For example, the working index still describes bulk boilerplate deletion as out of scope even though Layer A completed it.
7. Pause generation of bilingual drafts for the remaining 52 recordings until the pilot passes.

## 6. Phase B — Produce native timestamps

The current GPU pipeline emits plain text only; the cohort script estimates timestamps from word position. Estimated timestamps cannot support precise listening or citation.

1. Check the exact JSON/SRT output flags supported by the installed whisper.cpp version.
2. Extend `Scripts/_transcribe_batch.py` to emit timestamped JSON or SRT alongside `.txt`.
3. Keep no-VAD, beam 5 and `--max-context 0` unchanged.
4. Run the timestamped form on a fixed control slice and compare its text byte-for-byte or segment-for-segment with the existing configuration.
5. Vary only the output-format variable during this test.
6. Store segment start/end timestamps and available decoder confidence fields.
7. Replace every word-rate-derived timestamp in pilot and promoted files.
8. Preserve timestamped raw decoder output as part of the audit trail.

## 7. Phase C — Build a controlled terminology registry

Create a term-sense registry rather than a flat replacement list. Recommended fields:

| Field | Purpose |
|---|---|
| Canonical Hindi | Preferred Devanagari spelling |
| Accepted variants | Orthographic variants that do not alter meaning |
| ASR confusions | Observed corrupt forms and phonetic neighbours |
| Transliteration | Stable Roman form |
| Canonical English | Default analytical rendering |
| Source-specific English | MVD/SB/JV/KD alternatives by context |
| Sense/context | Distinguishes different uses of the same Hindi word |
| Authority | Book, section and verified PDF page |
| Status | Accepted, provisional, disputed or working gloss |
| Decision note | Reason for the chosen rendering |
| Reviewer/date | Accountability and future revision |

### 7.1 Authority order

1. Exact published English in the same book and doctrinal context.
2. Published English in another MVD, SB, JV or KD source.
3. A reviewed and internally consistent `MD-Mapping.xlsx` entry.
4. A clearly labelled working gloss.

Search MVD and SB space-insensitively before declaring a word unmapped. Confirm page numbers in the PDFs, not only in extracted Markdown.

### 7.2 Initial high-priority terms

| Hindi | Working rendering | Action required |
|---|---|---|
| साक्षात्कार | *sakshatkar*; direct recognition | Preserve JV's “revelation” only where following that published context |
| बोध | *bodh*; enlightenment | Avoid generic “awareness” unless the source uses it |
| अनुभव | realisation | Avoid ordinary “experience” for the technical sense |
| प्रमाण | evidence; *praman* | Distinguish proof/evidence usages where the text does |
| चुम्बकीयता | magnetism | Accepted for transcript cleanup and automatic translation protection; retain the mapping typo in provenance and check the exact source passage when cited |
| चुम्बकीय बल | magnetic force | Add ASR variants such as `चुम्बी की बल` to the review queue, not automatic replacement |
| चुम्बकीय धारा | magnetic current | Accepted for transcript cleanup and automatic translation protection; check KD §3.13 when citing the source passage |
| रूप | form | Check within the रूप-गुण-स्वभाव-धर्म chain |
| गुण | property | Do not translate as generic quality where the technical sense applies |
| स्वभाव | essential nature | Preserve the doctrinal distinction from धर्म |
| धर्म | dharma | Do not allow machine translation to produce “religion” |

### 7.3 Context-dependent terms

Do not flatten contextual distinctions. For example, the mapping notes that `ताप` is “heat” in one MVD context while KD deliberately contrasts it with `ऊष्मा` and uses “temperature” in another. The registry must support term-plus-sense records.

## 8. Phase D — Five-video pilot

Use the following approximately 84 minutes of audio:

| Video ID | Duration | Reason for selection |
|---|---:|---|
| `KTeH3rM2qK8` | 30:13 | Direct target: sakshatkar and becoming evidenced; zero logged `U+FFFD` |
| `OIkSW7QYry4` | 09:04 | Short doctrinal chain: study, bodh, realisation and evidence |
| `vuTOjdF6a3k` | 15:35 | Contains `चुम्बकीयता` and several corrupt magnetic-force forms |
| `a1ARueeihmA` | 04:58 | Short, mechanically clean ontology test: sound, heat and electricity in the atom |
| `pk3UxjDkhiE` | 24:37 | Tests audio repair of a severe repetition-loop neighbourhood |

### 8.1 Pilot workflow for each recording

1. Produce native timestamped no-VAD raw ASR.
2. Verify audio identity and record the file SHA-256.
3. Listen through the complete recording.
4. Segment speech into meaningful units, normally 15-40 seconds.
5. Preserve the spoken Hindi, including incomplete sentences and repetitions that are genuinely spoken.
6. Add only minimal punctuation needed for readability.
7. Repair all `U+FFFD` positions from audio; never infer them silently.
8. Inspect every loop-collapse neighbourhood against the audio.
9. Inspect context around every deleted boilerplate hit; the injected phrase is fabricated, but genuine adjacent speech may remain.
10. Run terminology-candidate detection.
11. Record each correction as original ASR, corrected Hindi, reason, timestamp and supporting evidence.
12. Search MVD, SB, JV and KD for doctrinal phrases and published English.
13. Lock the reviewed Hindi.
14. Produce a protected-term machine-translation draft for ordinary connective speech.
15. Manually post-edit every English segment against the locked Hindi.
16. Assign `[R]`, `[P]` or `[U]` from the review evidence rather than by default.
17. Add a printed-corpus cross-reference table and a passages-needing-verification table.
18. Conduct a second review of all `[P]`, `[U]` and argument-bearing passages.

### 8.2 Reliability definitions

- **[R] Reliable:** Audio checked and clear, or securely corroborated by repeated speech and a printed text. Safe to paraphrase with the timestamp.
- **[P] Probable:** Audio checked, but one limited ambiguity remains. Usable only with the timestamp and stated caveat.
- **[U] Uncertain:** Audio or wording remains unresolved. Do not quote or use as doctrinal evidence.

No segment receives `[P]` merely because an automated process did not detect a problem.

### 8.3 Implementation status — August 3, 2026

The five-video no-VAD timestamp rerun completed with five successes, zero
failures and no byte-identity conflicts. It produced 394 native segments and
preserved the exact decoder JSON beside valid UTF-8 JSON. The Phase-1 baseline
still verifies at 181 entries.

The Phase-4 preparation pipeline created the review workspace and aggregate
migration queue. Candidate detection currently
identifies 4 segments with `U+FFFD`, 17 containing boilerplate, 4 with repeat
runs, 206 containing controlled terminology, and 2 containing
`चुम्बकीयता`. Layer A proposes mechanical Hindi changes in 78 segments.

All 394 segments remain `UNREVIEWED`. This is intentional: automation cannot
establish `[R]` or `[P]`, repair an uncertain codepoint from audio, lock Hindi,
or complete the second review. The completion check is expected to fail until
those human gates are filled in the Excel workbooks.

### 8.4 Excel review source of truth — August 9, 2026

Each pilot session now carries a `*-phase4-review.xlsx` workbook beside its
audio evidence. Reviewers edit only the yellow cells in `Segments` and add
correction rows in `Corrections`; raw ASR and Layer-A candidate Hindi remain
unchanged. The review dropdown permits `UNREVIEWED`, `R`, `P`, or `U` (the
reliability classes usually written `[R]`, `[P]`, and `[U]`).
Hindi is displayed with Nirmala UI, so opening the workbook directly in Excel
does not depend on TSV import or code-page detection.

`Scripts/_sync_transcription_review_xlsx.py` reads the workbooks directly and
validates segment counts, review status, Hindi, required Level-3 English,
reviewer/date fields, evidence, and frozen hashes. Its `--check` mode remains
pending until listening is complete. `--sync-tsv` is an optional legacy export
and writes UTF-8 with BOM so Excel can identify Devanagari correctly.

## 9. Phase E — Layer-B review assistance

Develop a review-queue generator. It should detect and report candidates but should not make context-sensitive replacements automatically.

Flag:

- words close to canonical Madhyasth Darshan terms by edit distance or phonetic similarity;
- known ASR confusions such as forms of `साक्षात्कार`, `चुम्बकीयता` and `चुम्बकीय बल`;
- mixed Latin/Devanagari fragments;
- every `U+FFFD` position;
- repeat-collapse neighbourhoods;
- boilerplate-deletion neighbourhoods;
- doctrinal sequences with a missing or altered member;
- English mistranslations such as `धर्म` to “religion” or technical `अनुभव` to ordinary “experience”; and
- technical Hindi words whose English does not match the registry for that sense.

Each review item should contain:

- video ID and title;
- native start/end timestamp;
- raw context;
- cleaned context;
- candidate correction;
- confidence and reason;
- matching terminology-registry entries; and
- matching MVD/SB/JV/KD passages.

## 10. Phase F — Translation policy

1. Translate only after Hindi is locked.
2. Use machine translation for a first draft of ordinary dialogue, not for doctrinal decisions.
3. Protect approved multiword phrases before shorter terms.
4. Restore terms from the registry after machine translation.
5. Run a forbidden-rendering check, including `धर्म -> religion` and technical `अनुभव -> experience`.
6. Use transliteration plus English at first significant occurrence when the English alone would hide a technical distinction: for example, *sakshatkar* (direct recognition).
7. Preserve source-specific published renderings in quotations and explicit comparisons.
8. Mark any unresolved English as a working gloss.
9. Review English against Hindi segment by segment; do not review English for fluency alone.

## 11. Promotion acceptance gates

A session may enter the repository's `References/` tree only when all applicable checks pass.

### Provenance

- [ ] Video ID, source URL, uploader, date/place when known, duration and local audio hash recorded.
- [ ] Raw ASR and timestamped decoder output preserved unchanged.
- [ ] Every correction has an auditable log.

### Hindi

- [ ] Entire recording listened through.
- [ ] Native timestamps used; no word-rate-derived timestamps.
- [ ] `U+FFFD` count is zero or every residual is explicitly unrecoverable and marked `[U]`.
- [ ] All loop-collapse neighbourhoods checked against audio.
- [ ] All boilerplate-deletion neighbourhoods checked.
- [ ] Doctrinal spellings follow the reviewed registry.
- [ ] Words supplied from printed texts are bracketed and cited.

### English

- [ ] Every segment post-edited against locked Hindi.
- [ ] All doctrinal terms match an accepted source-specific rendering or are labelled working glosses.
- [ ] No translation-failure placeholders remain.
- [ ] Forbidden generic substitutions have been checked.

### Evidence and review

- [ ] Every segment has an evidence-based `[R]`, `[P]` or `[U]` mark.
- [ ] All `[P]`, `[U]` and load-bearing passages receive a second review.
- [ ] Printed-text page citations are confirmed in source PDFs.
- [ ] Differences between the session and printed texts are recorded rather than harmonised silently.

### Artefacts

- [ ] Markdown is the source of truth.
- [ ] HTML/PDF generated with repository scripts.
- [ ] PDF visually checked for Devanagari rendering, clipping and navigation.
- [ ] Session folder README, `References/MANIFEST.md` and `NOT-DOWNLOADED.md` updated.
- [ ] `python Scripts/_check_references.py` passes.
- [ ] Programme status and decision log updated.

## 12. Pilot success criteria

The pilot succeeds when:

1. native timestamp production is reliable and does not degrade text;
2. all five Hindi transcripts pass the Hindi acceptance gates;
3. at least two reach complete Level-3 bilingual promotion quality;
4. the terminology registry covers every technical term encountered in the pilot;
5. the Layer-B queue catches the known sakshatkar and magnetic-term errors without creating unsafe automatic corrections;
6. a second reviewer can reproduce the correction decisions from the audit trail; and
7. actual person-hours are recorded separately for listening/Hindi, terminology research, translation and QA.

## 13. Scaling decision after the pilot

Rank the remaining recordings by:

1. direct relevance to current study sections;
2. uniqueness of oral evidence not present in printed texts;
3. audio/ASR quality;
4. duration and expected review cost;
5. terminology value; and
6. whether related recordings can be reviewed as a thematic series.

Recommended order:

1. promote high-value short recordings;
2. complete the five thematic pilot sessions;
3. review the seven severe-loop files;
4. promote recordings already needed by live studies;
5. review remaining files in thematic cohorts; and
6. consider full-channel Phase 2 only after Tier-1 promotion economics are understood.

## 14. Effort estimate

Expected effort for promotion-quality work:

| Work | Approximate effort per audio hour |
|---|---:|
| Audio-checked Hindi cleanup | 4-6 person-hours |
| Terminology and printed-corpus research | 1-3 person-hours |
| English post-editing | 2-4 person-hours |
| Second review, QA and artefact production | 1-2 person-hours |
| **Total** | **8-15 person-hours** |

The five-video pilot (about 1.4 audio hours) is expected to require roughly 15-25 person-hours plus initial timestamp/registry tooling.

Promoting all 23.43 hours to Level 3 would require approximately 190-350 person-hours. This is why the three deliverable levels and priority-based promotion are essential.

## 15. Immediate next actions

1. Listen through `KTeH3rM2qK8` and `vuTOjdF6a3k` as the first contrasting pair.
2. Fill reviewed Hindi, review status, evidence, reviewer and date in each session's `*-phase4-review.xlsx` workbook.
3. Record every change in the workbook's `Corrections` sheet and actual person-hours by work type.
4. Lock Hindi only after every `U+FFFD`, boilerplate and repeat neighbourhood is resolved or marked `[U]`.
5. Translate and manually post-edit the two Level-3 targets against the locked Hindi and controlled registry.
6. Complete the other three pilot recordings to Level 2.
7. Conduct the independent second review and run `python Scripts/_sync_transcription_review_xlsx.py --work E:\MD-Transcription --check`.
8. Promote the first session only after every applicable acceptance gate passes.
9. Refine Layer-B detection from the reviewed correction log.
10. Reassess scope, staffing and priority for the remaining 55 recordings.

## 16. Related local resources

- `E:\MD-Transcription\manifest-tier1.tsv`
- `E:\MD-Transcription\PHASE-1-BASELINE.md`
- `E:\MD-Transcription\BASELINE-SHA256.tsv`
- `E:\MD-Transcription\BASELINE-SUMMARY.json`
- `E:\MD-Transcription\validation\timestamp-control\CONTROL-RESULT.md`
- `E:\MD-Transcription\Nagraj-Recorded-Sessions\RAW-ASR-TIER1.md`
- `E:\MD-Transcription\Nagraj-Recorded-Sessions\TERMINOLOGY.md`
- `E:\MD-Transcription\Nagraj-Recorded-Sessions\TERMINOLOGY-REGISTRY.json`
- `E:\MD-Transcription\Nagraj-Recorded-Sessions\TERMINOLOGY-REGISTRY.md`
- `E:\Madhyasth Darshan\Scripts\_transcribe_batch.py`
- `E:\Madhyasth Darshan\Scripts\_transcribe_review.py`
- `E:\Madhyasth Darshan\Scripts\_clean_tier1_raw_asr.py`
- `E:\Madhyasth Darshan\References\Madhyasth-Darshan\MD-Mapping.xlsx`
- `E:\Madhyasth Darshan\References\Madhyasth-Darshan\MVD-Madhyasth-Darshan-Coexistentialism.md`
- `E:\Madhyasth Darshan\References\Madhyasth-Darshan\SB-Samadhanatmak-Bhautikvad.md`
- `E:\Madhyasth Darshan\References\Madhyasth-Darshan\JV-Jeevan-Vidya-An-Introduction.md`
- `E:\Madhyasth Darshan\References\Madhyasth-Darshan\KD-karm darshan v5.pdf`
- `E:\Madhyasth Darshan\References\Madhyasth-Darshan\Nagraj-Recorded-Sessions\TRANSCRIPTION-PROGRAM.md`

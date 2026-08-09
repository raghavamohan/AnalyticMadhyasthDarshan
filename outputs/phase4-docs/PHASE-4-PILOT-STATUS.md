# Phase 4 — Five-video audio-review pilot

**Status:** Excel review workbooks prepared from native no-VAD timestamp JSON. Human audio review is not yet complete; nothing here is citable or promoted.

Automation intentionally leaves every segment `UNREVIEWED`. `[R]`, `[P]`, or `[U]` must be assigned only after listening to the full recording.

| Video | Target | Native segments | Unreviewed | Gate |
|---|---:|---:|---:|---|
| `KTeH3rM2qK8` | Level 3 | 136 | 136 | PENDING |
| `OIkSW7QYry4` | Level 2 | 59 | 59 | PENDING |
| `vuTOjdF6a3k` | Level 3 | 68 | 68 | PENDING |
| `a1ARueeihmA` | Level 2 | 18 | 18 | PENDING |
| `pk3UxjDkhiE` | Level 2 | 113 | 113 | PENDING |

## Remaining human gates

1. Listen through all five recordings and fill reviewed Hindi segment by segment.
2. Repair every `U+FFFD`, loop and boilerplate neighbourhood from audio.
3. Record every correction and supporting audio/printed-text evidence.
4. Lock all five Hindi transcripts; translate and post-edit the two Level-3 targets.
5. Conduct the independent second review before repository promotion.

## Review files

Open the `*-phase4-review.xlsx` file inside each pilot session directory. Edit
only the yellow cells in `Segments` and add change records in `Corrections`.
The workbooks use Nirmala UI for Devanagari and are the reviewer-facing source
of truth. `PHASE-4-REVIEW-QUEUE.tsv` remains migration and audit input.

Run the completion gate from the repository root:

```powershell
python Scripts/_sync_transcription_review_xlsx.py --work E:\MD-Transcription --check
```

The command is expected to report `PENDING` until every human gate is complete.

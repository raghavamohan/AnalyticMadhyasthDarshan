# Study audio introductions

Reviewable scripts for short audio introductions to the studies in this
repository. The first five follow the Start here path. The directory is organised
by study, so any topical, formal, or applied study can be added later.

## Review the first five drafts

These are English drafts for a single narrator, prepared for author review.
Each targets **4–5 minutes**. Read the transcript aloud at a measured pace,
allowing short pauses between paragraphs; actual recording time decides the
final length. Titles and review notes are not spoken.

| Order | Stage | Transcript | Spoken words | Review notes |
| --- | --- | --- | ---: | --- |
| 1 | Human | [Why Humans Are Not Just Material](Why-Humans-Are-Not-Just-Material/en/transcript.md) | 649 | [Sources and review](Why-Humans-Are-Not-Just-Material/en/review-notes.md) |
| 2 | Existence | [The Ontology of Coexistence](The-Ontology-of-Coexistence/en/transcript.md) | 644 | [Sources and review](The-Ontology-of-Coexistence/en/review-notes.md) |
| 3 | Knowledge | [The Epistemology of Coexistence](The-Epistemology-of-Coexistence/en/transcript.md) | 646 | [Sources and review](The-Epistemology-of-Coexistence/en/review-notes.md) |
| 4 | Value | [Axiology: Value Theory](Axiology-Value-Theory/en/transcript.md) | 645 | [Sources and review](Axiology-Value-Theory/en/review-notes.md) |
| 5 | Living | [How Undivided Society Is Established](How-Undivided-Society-Is-Established/en/transcript.md) | 649 | [Sources and review](How-Undivided-Society-Is-Established/en/review-notes.md) |

The scripts have had one editorial revision (Revision 2, September 18, 2026) for
fidelity to each study's central question and for the weight of the examples
chosen; each review file records what was added, what was cut, and the revised
transcript hash. Status remains `Draft — awaiting author review`.

## Organisation

```text
Audio/
  README.md
  <study-slug>/
    en/
      transcript.md
      review-notes.md
    hi/                    # Optional future language edition
      transcript.md
      review-notes.md
```

Use the canonical study slug as the folder name. Keep sequence numbers in this
index, rather than in filenames: a study can appear in several listening paths
without duplicating its script. Each review file links to the actual source
under `Studies/` or `Applications/`, so the structure accommodates all three
study collections. Add another language beside `en/` when needed, with its own
review and timing.

- **`transcript.md`** contains a title followed by only the words intended to be
  spoken. Edit this file directly to review and finalise the introduction. It is
  a recording script now; after recording, reconcile any spoken changes so it
  becomes an accurate transcript of the released audio.
- **`review-notes.md`** contains the draft state, source version, section map,
  editorial choices, and checklist. It is the place for review comments,
  pronunciation decisions, and eventual recording details. Nothing in it is
  part of the narration.
- **`README.md`** provides the listening/review order and links. Additional paths
  can be added here, or split into separate index files when the collection
  grows. Keep one canonical introduction per study and language.

This layout supersedes the earlier proposal to keep audio scripts inside each
study directory. The wider [implementation plan](../docs/start-here-audio-plan.md)
has been updated to use this directory.

## Editorial and recording workflow

1. Review each draft for meaning, spoken clarity, and its balance of exposition,
   comparison, and open questions. The section map identifies the source of
   each main claim. These drafts paraphrase the canonical studies; they are not
   a new independent verification of every primary reference those studies cite.
2. Revise the transcript directly and record consequential choices in its review
   file. Keep it near 550–650 words, then use a timed read to reach 4–5 minutes.
3. Mark the transcript `Ready to record` in the review file when its wording is
   accepted. Language and human versus AI narration can be settled before the
   pilot recording; English was used for these first drafts.
4. Record the Human episode first to settle voice, pacing, and pronunciation.
   Then use the accepted approach for the other four.
5. Listen through the recording, reconcile the transcript, and record the measured
   duration, audio checksum, and review outcome. Mark it `Recorded` after this
   check; use `Published` only after verified site publication.

The lifecycle above is for audio authoring and does not change a study's
Draft/Released status. A later substantive study revision calls for audio review;
mark the affected entry `Needs review` until its claims have been reconciled.
The source and transcript hashes in each review file identify the initial draft
baseline. They are provenance, not automatic freshness checks. Update the baseline
when a reviewed version replaces it, and recalculate the word-count summary when
wording changes.

For the first voice sample, check **Madhyasth Darshan**, **Shri A. Nagraj**,
**jeevan**, **satta**, **dharma**, **Advaita Vedanta**, **Brahman**, and
**Brahma** (in the Existence episode's spoken slogan "Brahma is truth, the world
is perpetual"; distinct from Brahman) with the narrator. Use the same
pronunciation throughout the series. The transcripts
explain technical terms in context and avoid long lists of untranslated terms.

The recordings and archival masters will need durable storage outside this text
directory, with verified R2 delivery and metadata added during the implementation
phase. No audio files, published transcript readers, players, or publication
manifest entries have been created yet. The source studies, their timestamps,
and their generated PDFs are unchanged.

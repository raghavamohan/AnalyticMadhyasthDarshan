# Start here audio introductions: implementation plan

Status: Five English draft scripts prepared for author review in
[Audio/README.md](../Audio/README.md); one editorial revision applied (September 18,
2026) for fidelity to each study's central question and the weight of its examples.
Recording, site integration, and publication remain planned. Open items:
[PENDING.md](../PENDING.md#audio).

## Objective and agreed scope

Add a 4–5 minute audio introduction to each of the five core studies in the
Start here path. Help a newcomer understand the question, the study's approach,
and why the next stage follows. The user has confirmed the duration and asked
for this plan, then requested drafts of all five transcripts. English drafts are
available for review; the final recording language and narration method remain
to be selected.

| Stage | Study | Repository slug |
| --- | --- | --- |
| Human | Why Humans Are Not Just Material | `Why-Humans-Are-Not-Just-Material` |
| Existence | The Ontology of Coexistence | `The-Ontology-of-Coexistence` |
| Knowledge | The Epistemology of Coexistence | `The-Epistemology-of-Coexistence` |
| Value | Axiology: Value Theory | `Axiology-Value-Theory` |
| Living | How Undivided Society Is Established | `How-Undivided-Society-Is-Established` |

All five core studies were Released when this plan was prepared. Recheck their
current content and status when work resumes. Related studies, a podcast RSS
feed, podcast-platform distribution, translations, and full-paper narration are
possible later additions outside this initial scope.

## Recommended format

Use one consistent narrator and a conversational, welcoming delivery. Start
with the first study as a pilot. Target roughly 550–650 words, then adjust by
timing the actual recording: the acceptance criterion is 4–5 minutes including
pauses, not a fixed word count.

| Approximate position | Content |
| --- | --- |
| 0:00–0:30 | The central question and one reason it matters. |
| 0:30–1:00 | An everyday example that makes the question concrete. |
| 1:00–3:15 | Two or three central ideas and the comparisons actually developed in the study. |
| 3:15–4:10 | A limitation, objection, or open question and what the reader can examine further. |
| 4:10–4:40 | Invitation to read/discuss and the connection to the next stage. |

The final episode closes the five-stage journey and invites further study and
discussion. It should not imply an additional sixth stage.

Editorial requirements:

- Base each script on the current canonical study; inspect its primary-source
  support where a condensed explanation could alter its meaning.
- Distinguish Madhyasth Darshan's claims, the project's analysis, comparison
  positions, and open questions. Preserve qualifications about evidence.
- Explain unfamiliar terms when first introduced. Maintain a shared
  pronunciation guide for terms such as jeevan, satta, and anubhav.
- Use the project's established voice and avoid unsupported analogies,
  promotional claims, or an invented conversation presented as real speakers.
- Keep citations and section pointers in editorial metadata rather than
  reading long references aloud. Publish a transcript matching the final audio.
- Prefer clean speech without background music for the initial series.

## Phase 1: select delivery and prepare the pilot

1. Confirm the recording language and whether the user will record the narration
   or prefers AI narration. Recommended starting language: English, matching
   the current study readers. These are pending choices, not settled decisions.
2. Review the five existing drafts with the user, beginning with the Human
   episode. Use their source maps and the repository's substantive study-review
   guidance for fidelity and terminology.
3. Review the script and a short voice/pronunciation sample with the user before
   producing all five episodes. If using AI, choose the provider at that time
   using current quality, cost, usage terms, and voice availability.
4. Record or generate the full pilot. Listen through and correct mispronunciation,
   missing words, unnatural pauses, distortion, and changes in meaning.
5. Time the final recording and align its transcript. Ask a few newcomers whether
   they can state the central question and understand what reading adds.

Deliverable: one reviewed script/transcript, pronunciation notes, and an accepted
4–5 minute pilot recording. Revise this format before recording the other four.

## Phase 2: establish audio ownership and publishing

Inspect the existing artifact inventory and publication contracts before
choosing final filenames. The following names are proposals, not implemented APIs:

- `Audio/<Slug>/<language>/transcript.md`: canonical spoken script; the initial
  five English drafts already use this path.
- `Audio/<Slug>/<language>/review-notes.md`: separate source map, draft provenance,
  and author-review notes; already present for the five English drafts.
- `Audio/<Slug>/<language>/transcript.html`: proposed generated public transcript,
  using existing reader infrastructure where appropriate. This output does not
  exist yet.
- `Scripts/audio-pipeline.json`: registry mapping study slug and language to
  script, transcript, recording, duration, provenance, and publication state.
- `/Audio/<Slug>/<language>/introduction.mp3`: proposed stable public audio URL,
  backed by a verified immutable object in R2.

Store scripts and metadata in Git. Preserve the accepted recording and its
checksum in durable storage: a human recording is an authoring input, and an
AI recording must also be retained rather than assumed reproducible. Preserve
an archival master when available and publish a compact MP3 derivative.

Extend the existing coherent-site publication flow to inventory, verify, stage,
and promote audio alongside the corresponding transcript and page controls.
Do not route audio through PDF-specific conversion code. Inspect these starting
points during implementation:

- `.github/CI.md` and `.github/workflows/publish-site.yml`
- `Scripts/_artifact_graph.py` and `Scripts/_publication_plan.py`
- `infra/site-worker/README.md` and `infra/site-worker/src/index.js`
- Existing companion inventory, rename/removal, and generated-file checks

The site worker already contains byte-range handling; verify that the selected
audio storage route actually uses it. Test MP3 content type, seeking, download,
cache headers, and missing-file behavior. Use content hashes for asset versions.
Do not generate paid AI audio during ordinary CI builds or on page requests.

Record the canonical study revision/hash, script hash, recording checksum,
measured duration, language, narrator, and review state for each episode.
Invalidate the review state when the study or script changes. Before publishing
that study revision, require re-review or omit its stale Listen control until
the audio is corrected; do not block unrelated site updates. Avoid needless
re-recording for changes that reviewers confirm do not affect the introduction.

## Phase 3: integrate the pilot into Start here

Use `.agents/skills/refine-studies-index/SKILL.md` when implementing the UI.
Edit `INDEX_TEMPLATE` in `Scripts/_build_studies_index.py`, then regenerate
`Studies/index.html`; do not hand-edit the generated landing page.

- Add a compact `Listen · 4:xx` action beside the existing study actions. Populate
  availability and duration from the audio registry, not duplicated markup.
- Open an inline audio player with play/pause, seeking, volume, and an accessible
  playback-speed control. Prefer native controls with a small speed selector.
- Show Transcript and Download links. Identify AI narration if that option is
  selected, and credit human narration where appropriate.
- Do not autoplay or download all five recordings on initial page load. Load
  audio when requested and allow only one episode to play at a time.
- Pause the current episode when its stage is hidden, preserving its position
  for return. Do not leave a hidden player producing sound.
- Keep controls usable with keyboard, screen readers, mobile layouts, and both
  themes. Use descriptive labels and a clear error/retry state.
- Keep a normal transcript link available without JavaScript. Add matching
  audio/transcript access to the README representation through its generator.
- Keep large audio files out of automatic service-worker precaching. Initial
  offline behavior may explain that playback requires a connection; explicit
  offline audio downloads can be considered separately.

Only expose episodes whose audio and transcript are ready. The remaining stages
can retain their existing controls during the pilot rollout.

## Phase 4: produce the remaining episodes

Draft scripts for Existence, Knowledge, Value, and Living are already available
for review. After accepting the pilot's editorial style and voice, revise those
scripts as needed and record them. Review all five together for shared
terminology, consistent volume, repetition, and accurate stage transitions.

The authoring loop is: current study → reviewed script → accepted recording →
matching transcript and metadata → verified publication. Audio-only work does
not change canonical study dates or require study PDF regeneration. If canonical
study text is revised, follow the normal timestamp/catalog/PDF workflow.

## Verification and completion

Before opening implementation PRs, create an appropriate feature branch and
follow the current repository rules. Study-directory additions require the
applicable study-update PR metadata; audio-only companion changes mark canonical
study timestamp/PDF items not applicable. Document the new supported companion
type and synchronize agent rules if any canonical skill or AGENTS.md is edited.

Acceptance criteria:

- Each of the five recordings lasts 4–5 minutes and has been listened to in full.
- Each transcript matches the published speech; pronunciation and doctrinal
  attribution have been checked against the study.
- Registry entries resolve to the correct studies and verified assets. Invalid
  duration, missing transcript, or stale review state cannot expose a Listen link.
- Mobile and desktop playback, keyboard operation, stage switching, speed,
  seeking, downloads, failed requests, and no-autoplay behavior work as intended.
- Publication verifies the audio, transcript, and page as one revision; rollback
  restores a matching set. Unchanged accepted recordings are reused.
- Existing reading, slides, discussion, catalogs, and offline-reader behavior
  remain functional.

Run the repository's relevant index, reader, lifecycle, publication, and worker
checks for the files actually changed. Include `_verify_studies_index.py` and
`git diff --check`; add focused tests for audio registry validation, playback
coordination, and publication integrity. Check that unchanged regeneration
produces no tracked diff. Avoid unrelated document/PDF rebuilds.

## Resume here

Open audio items live in [PENDING.md](../PENDING.md#audio). Start with author
review of the draft transcripts linked from [Audio/README.md](../Audio/README.md)
(`AUD-01`), then confirm recording language and human versus AI narration
(`AUD-02`) before recording the Human episode (`AUD-03`). Keep this file for
format, phases, and verification how-to. Do not add a second remaining-work
list here.

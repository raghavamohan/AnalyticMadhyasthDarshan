---
name: update-presenters-companion
description: >-
  Update a study Presenter's Companion (slide-by-slide delivery notes) under
  Studies/ or Applications/: keep the companion markdown as source of truth,
  rebuild DOCX/PDF, and sync PowerPoint speaker notes from a JSON map. Use when
  the teaching deck gains/loses slides, companion notes drift from the deck, or
  regenerating Presenters-Companion-*.docx/.pdf/.notes.json.
---

# Update a Presenter's Companion

## Source and authoring model

- Companion markdown is the **source of truth** for delivery notes, primary-text
  background, and Q&A:
  `Studies/<Slug>/Presenters-Companion-<Name>.md` (or under `Applications/`).
- PowerPoint notes-pane text lives beside it as JSON:
  `Presenters-Companion-<Name>.notes.json` — object keys are **1-based slide
  numbers** (strings or ints), values are **complete read-aloud scripts** (same
  wording as “Delivering the slide”), suitable for live or video-conference
  presenter view. Do not store coaching cues (“walk the table”, “land the
  line”) in the notes pane.
- Generated artifacts (do not hand-edit as source):
  - `Presenters-Companion-<Name>.docx`
  - `Presenters-Companion-<Name>.pdf`
- The teaching deck (`.pptx`) remains the source of truth for **visible slides**.
  Companion and notes must track its slide count and order. Deck visual edits
  still follow [update-study-presentation](../update-study-presentation/SKILL.md).

## Heading conventions

```markdown
# PRESENTER'S COMPANION
## <Deck title>

Intro paragraphs (audience, how to use, house conventions).

# Slide N
# <Slide title matching the deck>
## Delivering the slide
## Primary-text background
## Likely questions from the audience
```

Keep one `# Slide N` block per deck slide. Cross-references inside the companion
must use the **current** deck numbering.

## Scripts

| Script | Role |
|--------|------|
| `Scripts/_build_presenters_companion.py` | Markdown → DOCX; optional PDF; optional PPTX notes sync |
| `Scripts/_study_pdf_pipeline.py` | Canonical Markdown → HTML/PDF owner, including companion PDFs |
| `Scripts/_verify_companion_outputs.py` | Check declared Markdown/DOCX/JSON/PPTX freshness |
| `Scripts/_sync_pptx_speaker_notes.py` | Write notes JSON into a `.pptx` notes pane |
| `Scripts/_build_deck_notes_pdf.py` | Deck → `<Deck>-notes.pdf`: slide image plus that slide's read-aloud script, with continuation pages when needed |

Dependencies: the repository Python requirements and pinned Chrome/Node toolchain. The published companion PDF is rendered from Markdown through the same pipeline locally and in CI; Word COM is not its producer.

Three PDFs serve different purposes; do not conflate them:

| PDF | Contains | Audience |
|-----|----------|----------|
| `<Deck>.pdf` | Slides only | Projecting; linked from `Studies/index.html` |
| `<Deck>-notes.pdf` | Slide plus read-aloud script, with continuation pages when needed | The presenter, while delivering |
| `Presenters-Companion-<Name>.pdf` | Script **plus** primary-text background and Q&A | Pre-session study |

The staged `_build_presentations.py` is the normal entry point: it generates
the slides PDF before composing notes from the same PPTX and those slide images,
then verifies/replaces the pair. Local mtimes or missing ignored PDFs do not
determine CI selection. Long scripts continue onto a `CONTINUED` page instead
of being truncated. Use the lower-level notes builder only for diagnostics.

## Workflow

1. Confirm work is on a **feature branch**. Any change under `Studies/` or
   `Applications/` needs a `study-update` PR per [AGENTS.md](../../../AGENTS.md) §7.
2. Diff the current deck against the companion: extract slide titles/order from
   the `.pptx`, compare to `# Slide N` headings. Remap, add, or remove sections
   until counts match.
3. Update the companion `.md`. Under **Delivering the slide**, write a complete
   spoken script the presenter can read aloud nearly verbatim (first person or
   direct address to the audience; cover the slide’s visible claims in order).
   Keep coaching / stage directions out of that section — put prep material under
   Primary-text background and Likely questions. The builder extracts each delivery
   section into `.notes.json` when `--pptx` is supplied. Register the companion and
   deck mapping in `Scripts/companion-pipeline.json`. New sources must be declared
   once, with a registered deck under the same parent study; missing, duplicate,
   unsafe and cross-study mappings fail verification.
4. For a new companion source, stage its intended Markdown/resources before
   rendering, as described in
   [manage-studies: shared finish](../manage-studies/SKILL.md#shared-finish-before-review).
   Rebuild artifacts from repo root:

   ```powershell
   python Scripts/_build_presenters_companion.py Studies/<Slug>/Presenters-Companion-<Name>.md --pdf --pptx Studies/<Slug>/<Deck>.pptx
   ```

   DOCX/PDF only:

   ```powershell
   python Scripts/_build_presenters_companion.py Studies/<Slug>/Presenters-Companion-<Name>.md --pdf
   ```

   Diagnostic notes sync from an already regenerated JSON (do not hand-edit JSON):

   ```powershell
   python Scripts/_sync_pptx_speaker_notes.py Studies/<Slug>/<Deck>.pptx Studies/<Slug>/Presenters-Companion-<Name>.notes.json
   ```

5. If the `.pptx` changed (including notes-only), regenerate the deck PDF and the
   read-aloud notes PDF:

   ```powershell
   python Scripts/_build_presentations.py --deck <Presentation-ID> --in-place
   python Scripts/_verify_companion_outputs.py
   ```

   The staged builder generates both outputs with the pinned production renderer
   and verifies slide count, complete scripts, layout and fonts before replacement.

   All three PDFs are generated artifacts ignored by Git and published through
   protected coherent-site publication after merge. The companion markdown, DOCX, notes JSON, and PPTX remain tracked.

6. Companion-only edits do **not** refresh the study's `**Edited on:**` or catalog
   timestamps. Mark Edited-on checklist items N/A in the PR when the study `.md`
   was not changed.

## Content rules

- Align terminology with the study (e.g. Omnipresence in prose vs Omnipotence in
  translation/quotes when that is the study's Editorial Notes convention).
- Prefer primary-text page citations already used in the study.
- Be candid on open problems and instrument-measurement limits; do not overclaim.
- When the deck retires a framing (taxonomy, slide), remove it from companion and
  notes rather than leaving stale mid-deck payoffs.

## Completion check

- [ ] Companion `# Slide N` count equals PPTX slide count
- [ ] `.notes.json` has an entry for every slide `1..N` and no extras
- [ ] Delivering / notes scripts are complete read-aloud prose (not coaching cues)
- [ ] DOCX and PDF regenerated from the markdown
- [ ] PPTX speaker notes synced when `--pptx` / notes sync was in scope
- [ ] Deck PDF regenerated if the PPTX changed; page count matches
- [ ] `<Deck>-notes.pdf` regenerated after the deck PDF; every slide's script
      present in full (no clipped tail)
- [ ] Generated PDFs were not added to Git
- [ ] `study-update` PR uses `Study slug: <Slug>` (bare slug); Edited-on N/A when
      the study markdown was not changed

## Finish with the shared CI workflow

Complete [manage-studies: shared finish](../manage-studies/SKILL.md#shared-finish-before-review)
after this skill's targeted renders. Use `_finalize_study_artifacts.py --study
<Slug>` for changed canonical metadata, or omit `--study` for companion-only
changes and retirement. Commit the tracked outputs, validate the committed
HEAD with `_validate_study_change.py` and the same PR body, and let protected
coherent-site publication handle changed artifacts after merge.

## Companion-only deletion

To remove one or more notes/decks while keeping their parent study, use
[remove-study-companions](../remove-study-companions/SKILL.md).
The whole-study `_remove_study.py` command is exclusively for retirement of the
study and all its companions; it is not a companion-removal command.

For filename changes or moves between studies use [relocate-study-companion](../relocate-study-companion/SKILL.md). For restoration from merged history use [restore-study](../restore-study/SKILL.md).

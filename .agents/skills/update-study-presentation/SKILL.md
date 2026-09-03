---
name: update-study-presentation
description: >-
  Update an existing study companion PowerPoint deck under Studies/ or
  Applications/, preserve its established design, regenerate its slides PDF and
  read-aloud notes PDF, and verify every format. Use for PPTX content edits,
  figure replacements, slide additions or removals, slide reordering,
  presentation reviews that require fixes, and PPTX-to-PDF refreshes. The PPTX is
  the source of truth; this repository does not use a slides-YAML generation
  workflow.
---

# Update a study presentation

## Source and authoring model

- Treat the existing `.pptx` as the source of truth and update it in place.
- Do not create presentation YAML or derive slides mechanically from study markdown.
- Use the installed Presentations skill and its artifact-tool template-following workflow.
- Preserve the deck's typography, palette, spacing, layouts, footers, notes, and visual language unless the user asks for a redesign.
- Base substantive changes on the companion study and cited sources. Keep visible copy concise and suitable for teaching; avoid editorial or production commentary unless it serves the audience.

## Workflow

1. Confirm the work is on a feature branch. Any change under `Studies/` or `Applications/` requires a `study-update` pull request under [AGENTS.md](../../../AGENTS.md) §7.
2. Inspect and render the complete source deck before editing.
3. Map requested changes to inherited slides and objects; edit with artifact-tool rather than `python-pptx` or direct OOXML mutation.
4. Render every final slide and run the Presentations skill's overflow check. Inspect changed slides at full size and review the complete deck for flow and consistency.
5. Replace the canonical `.pptx` only after the edited copy passes QA.
6. Find the deck's ID in `Scripts/presentation-pipeline.json`, then run the staged
   production build:

   ```powershell
   python Scripts/_build_presentations.py --deck <Presentation-ID> --in-place
   ```

   This checks fatal source layout first, asserts the exact production renderer,
   generates both PDFs in a temporary tree, verifies them, and replaces the configured
   outputs only after all gates pass. For a non-publishing diagnostic build, retain the
   repository-relative output tree elsewhere:

   ```powershell
   python Scripts/_build_presentations.py --deck <Presentation-ID> --profile libreoffice-production --output-root tmp/presentation-check
   ```

7. Use the low-level commands only to isolate a converter or notes-composer failure:

   ```powershell
   python Scripts/_pptx_to_pdf.py Studies/<Slug>/<Deck>.pptx --profile powerpoint-baseline
   python Scripts/_build_deck_notes_pdf.py Studies/<Slug>/<Deck>.pptx
   ```

   The notes command must follow the slides command because it takes its slide images
   from the slides PDF. Repository decks absent from the manifest fail closed.

8. The builder verifies all machine-checkable invariants. Visually
   inspect changed pages in both PDFs.

## Layout rules

Run this before regenerating anything, and again before you call the deck done:

```powershell
python Scripts/_check_deck_layout.py Studies/<Slug>/<Deck>.pptx
python Scripts/_check_deck_layout.py --all
```

It fails on rendered text colliding with other rendered text, text spilling off
the canvas, wrong `N / M` footer numbering, and out-of-range slide
cross-references. Everything it is less sure about — hairline overlaps, boxes
holding more lines than they were sized for, single lines at ≥95% of box
width — it prints as a note for you to eyeball. Notes are not noise to be
ignored; they are the cases where the model defers to your eyes.

### A too-long title reads as *overlap*, not as overflow

PowerPoint never clips overflowing text, so a box's declared height does not
constrain what renders. On these decks the title box is one line tall and
**centre-anchored**, so a title that wraps to two lines grows in *both*
directions and its first line rides up through the eyebrow above it. The
symptom on screen is a struck-through eyebrow; the cause is a title four words
too long. Fix the length, not the eyebrow.

The same mechanic makes a wrapped one-line footer orphan its page number below
the footer band.

### Keep single-line boxes to one line

Measure, do not eyeball: the string in its own font and size against the box
width, minus insets. `_check_deck_layout.py` does this. Targets:

| Fill of box width | Verdict |
|---|---|
| ≤ 90% | Safe. Aim here. |
| 90–95% | Fine, no headroom for later edits. |
| 95–100% | Renderer-dependent — PIL and PowerPoint disagree by up to ~1%. A title measured at 100.2% still rendered on one line. |
| > 100% | Wraps. On a one-line box, that is a collision. |

### The 10 × 5.625in grid

Four decks share it: both Epistemology decks and both Ontology decks. Match
these exactly rather than inventing a variant — an outlier box is the likelier
bug, and correcting it to the grid beats rewriting copy to fit a wrong box.

| Band | L | T | W | H | Type |
|---|---|---|---|---|---|
| Eyebrow | 1.05 | 0.28 | 8.40 | 0.26 | Calibri 10.5 bold |
| Title | 1.05 | 0.50 | 8.45 | 0.62 | Cambria 30 bold, anchor `ctr` |
| Footer | 0.55 | 5.28 | 8.90 | 0.28 | Calibri 9.5 |
| Section title | 0.70 | 1.72 | 6.10 | 1.50 | Cambria 44 bold — two lines by design |
| Section footer (two boxes) | 0.70 | 4.55 / 4.85 | 5.80 | 0.30 | Calibri 11.5 |

At Cambria 30 bold in the 8.45in title box, one line holds roughly 40
characters. Past that, check the measurement rather than guessing.

The two 13.33 × 7.5in decks — `How-Undivided-Society-Is-Established` and
`Why-Humans-Are-Not-Just-Material` —
each carry their own geometry. Read the deck you are editing; do not port
numbers from the table above into one of them.

### Adding, removing, or reordering a slide

Renumbering is not optional and not confined to the slides you touched:

- Every slide in a numbered deck carries an `N / M` footer. Removing one slide
  invalidates all of them. Only the Epistemology decks number their slides
  today; check before assuming.
- Hard-coded `slide N` references live in **shape text and speaker notes
  alike** — a phrase like "the failure modes return at slide 32" silently
  repoints at the wrong slide. Re-confirm each target by its title, not by
  arithmetic.
- A removed slide can leave a speaker note referring to it ("the drish term
  from the earlier triad"). Read the notes on the neighbours.

### Where the deck's speaker notes come from

Notes flow one way *only where a Presenter's Companion exists*:
`Presenters-Companion-<Name>.md` → `.notes.json` →
`Scripts/_sync_pptx_speaker_notes.py` → the `.pptx` notes pane. Today only
`The-Ontology-of-Coexistence` has one, so for every other deck the notes pane
in the `.pptx` is itself the source of truth and is edited directly. Check
which case you are in before editing a note — see [AGENTS.md](../../../AGENTS.md) §3.

## The three deck PDFs

A deck with a Presenter's Companion produces three PDFs. They are not
interchangeable; never regenerate one over another's path.

| PDF | Contains | Audience |
|-----|----------|----------|
| `<Deck>.pdf` | Slides only | Projecting; this is what `Studies/index.html` links as the presentation PDF |
| `<Deck>-notes.pdf` | Slide plus that slide's read-aloud script, one page per slide | The presenter, while delivering |
| `Presenters-Companion-<Name>.pdf` | Script **plus** primary-text background and Q&A | Pre-session study |

`<Deck>.pdf` must stay slides-only. Its filename is referenced from
`Scripts/_build_studies_index.py` and the generated `Studies/index.html`
(`data-presentation-pdf`, `data-study-link`), so renaming it means editing the
generator and the generated index together.

## Notes on the PDF tooling

- **A study folder may hold more than one deck.** `--study <Slug>` on its own only
  resolves when exactly one `.pptx` is present; otherwise pass `--deck <file>` or a
  full path. `The-Ontology-of-Coexistence` holds two decks, so the bare `--study`
  form fails there by design.
- `presentation-pipeline.json` is the canonical mapping from each PPTX to its slides
  and notes PDFs. This is essential where a deck stem matches the study slug: the
  slides output uses `-presentation.pdf` rather than overwriting the study PDF.
- `_build_deck_notes_pdf.py` reads speaker notes from the `.pptx`, so it always
  reflects the deck rather than a side file, and uses the manifest's slides PDF when
  no explicit path is supplied.
- It composes pages rather than using PowerPoint's notes-pages export, for two
  reasons: native notes pages can clip text overflowing the notes placeholder, and
  the repository needs a deterministic layout independent of authoring-time notes
  page geometry. Long scripts continue onto a `CONTINUED` page instead.
- Renderer selection never falls back based on the host. The exact LibreOffice
  production renderer and PowerPoint fidelity baseline are declared in the manifest;
  a version mismatch fails before any final output is replaced.
- After regenerating, confirm no script was truncated — compare the notes PDF text
  against the deck's notes rather than eyeballing the first page or two.

[AGENTS.md](../../../AGENTS.md) §3 governs **study markdown → PDF** only. Deck PDFs
are a separate pipeline and are not produced by `_regenerate_pdf.py`.

## Figures

- Reuse existing study figures when they support the slide.
- Keep study SVG files valid UTF-8 and follow [AGENTS.md](../../../AGENTS.md) §3 for special characters.
- Use `Scripts/_svg_to_png.js <input.svg> <output.png>` when a raster copy is needed for embedding.
- Run `python Scripts/_verify_study_svgs.py Studies/<Slug>/<Slug>.md` after changing an SVG referenced by the study markdown.

## Metadata and completion

Companion-only presentation edits do not update the study's `**Edited on:**` field or catalog timestamp. Update them only when the study markdown itself changes.

Before finishing, confirm:

- [ ] Canonical PPTX updated and all slides visually reviewed
- [ ] `python Scripts/_check_deck_layout.py <deck>` reports no failures, and each
      note was looked at rather than assumed harmless
- [ ] Footer numbering and every `slide N` cross-reference still correct after any
      add, removal, or reorder
- [ ] No unintended clipping, overlap, or unresolved placeholders
- [ ] Speaker notes and source footers preserved where intended
- [ ] Staged manifest build completed and changed pages visually verified
- [ ] PPTX slide count equals slides-PDF page count
- [ ] `<Deck>-notes.pdf` regenerated after the slides PDF, with every slide's script
      present in full (no clipped tail) and slide numbering matching the deck
- [ ] `<Deck>.pdf` is still slides-only — the notes PDF was not written over it
- [ ] `study-update` PR uses `Study slug: <Slug>` with the bare slug; Edited-on items are marked N/A for companion-only changes

When the Presenter's Companion markdown or notes JSON also needs to track the
deck, use [update-presenters-companion](../update-presenters-companion/SKILL.md).

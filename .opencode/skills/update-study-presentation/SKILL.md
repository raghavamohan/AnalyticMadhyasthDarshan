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
6. Regenerate the slides PDF:

   ```powershell
   python Scripts/_pptx_to_pdf.py Studies/<Slug>/<Deck>.pptx
   ```

   Force an engine only when necessary:

   ```powershell
   python Scripts/_pptx_to_pdf.py Studies/<Slug>/<Deck>.pptx --engine powerpoint
   python Scripts/_pptx_to_pdf.py Studies/<Slug>/<Deck>.pptx --engine libreoffice
   ```

7. Regenerate the read-aloud notes PDF — **after** step 6, since it takes its slide
   images from the slides PDF:

   ```powershell
   python Scripts/_build_deck_notes_pdf.py Studies/<Slug>/<Deck>.pptx
   ```

   Do this whenever the deck changes at all, including notes-only and
   reorder-only edits: slide images, slide numbering and the scripts all live in
   this artifact.

8. Verify that the slides-PDF page count matches the PPTX slide count and visually
   inspect changed pages in both PDFs.

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
- `_build_deck_notes_pdf.py` reads speaker notes from the `.pptx`, so it always
  reflects the deck rather than a side file, and regenerates `<Deck>.pdf` itself if
  that file is missing or older than the deck.
- It composes pages rather than using PowerPoint's notes-pages export, for two
  reasons worth knowing before anyone tries to "simplify" it. PowerPoint's
  `ExportAsFixedFormat` — the only API that accepts an `OutputType` of
  `ppPrintOutputNotesPages` — raises "The Python instance can not be converted to a
  COM object" at every arity in this environment, including the two-argument call
  `_pptx_to_pdf.py` makes; that script has always been falling back silently to
  `SaveAs`, which has no `OutputType` parameter. And native notes pages *clip* text
  overflowing the notes placeholder, which for multi-paragraph scripts would
  silently drop the tail. Long scripts continue onto a `CONTINUED` page instead.
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
- [ ] No unintended clipping, overlap, or unresolved placeholders
- [ ] Speaker notes and source footers preserved where intended
- [ ] Slides PDF regenerated and changed pages visually verified
- [ ] PPTX slide count equals slides-PDF page count
- [ ] `<Deck>-notes.pdf` regenerated after the slides PDF, with every slide's script
      present in full (no clipped tail) and slide numbering matching the deck
- [ ] `<Deck>.pdf` is still slides-only — the notes PDF was not written over it
- [ ] `study-update` PR uses `Study slug: <Slug>` with the bare slug; Edited-on items are marked N/A for companion-only changes

When the Presenter's Companion markdown or notes JSON also needs to track the
deck, use [update-presenters-companion](../update-presenters-companion/SKILL.md).

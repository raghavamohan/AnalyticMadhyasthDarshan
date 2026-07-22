---
name: update-study-presentation
description: >-
  Update an existing study companion PowerPoint deck under Studies/ or
  Applications/, preserve its established design, regenerate its companion PDF,
  and verify both formats. Use for PPTX content edits, figure replacements,
  slide additions or removals, presentation reviews that require fixes, and
  PPTX-to-PDF refreshes. The PPTX is the source of truth; this repository does
  not use a slides-YAML generation workflow.
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
6. Regenerate the matching companion PDF:

   ```powershell
   python Scripts/_pptx_to_pdf.py Studies/<Slug>/<Deck>.pptx
   ```

   Force an engine only when necessary:

   ```powershell
   python Scripts/_pptx_to_pdf.py Studies/<Slug>/<Deck>.pptx --engine powerpoint
   python Scripts/_pptx_to_pdf.py Studies/<Slug>/<Deck>.pptx --engine libreoffice
   ```

7. Verify that the PDF page count matches the PPTX slide count and visually inspect changed pages.

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
- [ ] Companion PDF regenerated and changed pages visually verified
- [ ] PPTX slide count equals PDF page count
- [ ] `study-update` PR uses `Study slug: <Slug>` with the bare slug; Edited-on items are marked N/A for companion-only changes

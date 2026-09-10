---
name: add-study-presentation
description: >-
  Add and register a new companion PowerPoint deck under Studies/ or
  Applications/, declare its slides/notes PDF outputs, optionally register a
  Presenter's Companion, and use the same staged renderer and checks as CI.
  Use when adding a first or additional teaching deck to an existing study.
---

# Add a study presentation

1. Use a feature branch and an existing Draft/Released parent study. Ongoing
   proposals have no public companion artifacts; prepare the first draft through
   [add-study](../add-study/SKILL.md) before adding public companions.
2. Author `Studies/<Slug>/<Deck>.pptx` (or `Applications/<Slug>/`) with the
   available presentation authoring skill. The PPTX is the visible-slide source.
   Follow [update-study-presentation](../update-study-presentation/SKILL.md) for
   typography, source support, notes ownership, slide order and visual QA.
3. Add one entry to the authored `decks` array in
   `Scripts/presentation-pipeline.json`. Keep its renderer profiles and production
   profile unchanged. Use a unique ID and noncolliding sibling output paths:

   ```json
   {
     "id": "example-study-deck",
     "source": "Studies/<Slug>/<Deck>.pptx",
     "slidesPdf": "Studies/<Slug>/<Deck>-presentation.pdf",
     "notesPdf": "Studies/<Slug>/<Deck>-presentation-notes.pdf",
     "requiredFonts": ["Cambria", "Calibri"]
   }
   ```

   Replace placeholders and list the fonts actually required by the deck. Both
   output paths must be unique and beside the PPTX. In particular, a deck named
   `<Slug>.pptx` must not overwrite `<Slug>.pdf`. Every repository PPTX must be
   declared; the builder and publication inventory reject missing registrations.

4. If the deck has a Presenter's Companion, author
   `Presenters-Companion-<Name>.md` beside it and add the ownership row to the
   `companions` array in `Scripts/companion-pipeline.json`:

   ```json
   {"markdown": "Studies/<Slug>/Presenters-Companion-<Name>.md", "deck": "example-study-deck"}
   ```

   One companion owns one registered deck under the same study. Follow
   [update-presenters-companion](../update-presenters-companion/SKILL.md) for
   contiguous `# Slide N` sections, delivery scripts and generation:

   ```powershell
   python Scripts/_build_presenters_companion.py Studies/<Slug>/Presenters-Companion-<Name>.md --pdf --pptx Studies/<Slug>/<Deck>.pptx
   ```

   Without a declared companion, speaker notes are authored in the PPTX. With
   one, its Markdown owns delivery text; notes JSON and PPTX notes are outputs.

5. Ensure Python requirements and pinned renderer/fonts are installed. On
   Windows, `Scripts/_install_presentation_renderer.ps1` installs the production
   LibreOffice version pinned by the manifest. Build the pair through:

   ```powershell
   python Scripts/_build_presentations.py --deck example-study-deck --in-place
   ```

   The builder checks manifest coverage, fatal source layout, renderer version,
   slide geometry/count/text, font coverage, blank pages and complete notes. It
   replaces both PDFs only after the selected build passes. Inspect the slides
   and notes visually as well. Do not substitute authoring-tool PDF exports for
   these published outputs or claim byte reproducibility beyond verified results.

6. Complete [manage-studies: shared finish](../manage-studies/SKILL.md#shared-finish-before-review).
   Finalization refreshes the index's presentation links, My Submissions companion
   registry, PDF keys and dependent web artifacts from the manifests. Do not
   hand-edit generated catalog JSON, HTML or PDF-key lists. Commit the PPTX,
   manifests, optional companion MD/DOCX/notes JSON and generated web outputs;
   PDFs stay ignored. Use `study-update` and `Study slug: <Slug>`.

Adding a deck alone leaves the parent's Edited-on/catalog timestamp unchanged.
If adding a link to it also changes canonical study Markdown, refresh that
study's timestamp and render its HTML/PDF too. Embed source SVG/raster figures
inside the PPTX; loose image edits do not update the deck automatically.

For filename changes or moves between studies use [relocate-study-companion](../relocate-study-companion/SKILL.md). For restoration from merged history use [restore-study](../restore-study/SKILL.md).

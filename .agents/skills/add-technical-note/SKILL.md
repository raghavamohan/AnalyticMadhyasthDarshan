---
name: add-technical-note
description: >-
  Add a technical or research note beside an existing study, including SVG,
  raster, Mermaid and math dependencies; generate its HTML/PDF and refresh the
  companion/publication inventory using the same scripts and checks as CI.
  Use for new Technical-Note-* or Research-Note-* companion Markdown documents.
---

# Add a technical or research note

1. Work on a feature branch under an existing Draft/Released study. Use a direct
   child of its directory, for example:

   ```text
   Studies/<Slug>/Technical-Note-<Name>.md
   Studies/<Slug>/Research-Note-<Name>.md
   ```

   The same layout works under `Applications/`. Choose a unique alphanumeric /
   hyphen name. These prefixes and a nonempty name make the note discoverable in
   My Submissions through `_companion_artifacts.py`. Planned parents have no
   public note/PDF inventory; complete first-draft registration first.

2. Author the note and its cited sources. It is a companion, with no independent
   catalog row and no `**Status:**` line, so its PDF is unwatermarked. Follow the
   applicable study prose/reference rules. Do not change the parent's Edited-on
   date unless its own Markdown changes, including adding a link to the note.
3. Keep figures and local embedded resources within the repository and reference
   them with relative paths. SVGs must be valid UTF-8 XML; use numeric XML entities
   for special characters as required by AGENTS §3. Include resources referenced
   inside SVGs in the same PR. The dependency graph follows these recursively.
   Mermaid/math use the pinned repository Node/Chrome pipeline.
4. Generate and verify the note with its **path**, not the parent study slug:

   ```powershell
   python Scripts/_regenerate_pdf.py Studies/<Slug>/Technical-Note-<Name>.md
   ```

   This uses the same `_study_pdf_pipeline.py` producer as CI, producing tracked
   sibling HTML and an ignored PDF. It checks SVG validity, rendered Mermaid,
   fenced-code completeness, embedded KaTeX fonts and PDF outline. Inspect new
   figures, math and page layout in the generated output.
5. Complete [manage-studies: shared finish](../manage-studies/SKILL.md#shared-finish-before-review)
   without `--study` for a note-only change. The automatic Markdown inventory,
   My Submissions registry, generated-PDF keys and search/offline data pick up
   the new note. Ordinary technical notes do not go in `companion-pipeline.json`;
   that manifest is for presenter MD/DOCX/JSON/PPTX ownership.
6. Commit the note, figures/resources, sibling HTML and finalization outputs in
   a `study-update` PR with `Study slug: <Slug>`. PDFs remain ignored. The coherent
   publication workflow builds/uploads the changed note and reuses unchanged
   study/deck PDFs. A figure shared with another Markdown document requires
   rendering that other consumer too.

For later edits use [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md).
For slide delivery scripts use
[update-presenters-companion](../update-presenters-companion/SKILL.md) instead.

## Companion-only deletion

To remove one or more notes/decks while keeping their parent study, use
[remove-study-companions](../remove-study-companions/SKILL.md).
The whole-study `_remove_study.py` command is exclusively for retirement of the
study and all its companions; it is not a companion-removal command.

For filename changes or moves between studies use [relocate-study-companion](../relocate-study-companion/SKILL.md). For restoration from merged history use [restore-study](../restore-study/SKILL.md).

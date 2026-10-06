---
name: relocate-study-companion
description: Rename a technical/research note, deck or Presenter’s Companion, or move a note/deck to another existing study. Uses Scripts/_relocate_study_companion.py to update owned paths and relative Markdown links while preserving parent studies and shared figures.
---

# Rename or move a companion

Use a feature branch. Both source and destination must have surviving canonical
studies. For a whole-study slug/title rename use `rename-study` instead.

```powershell
python Scripts/_relocate_study_companion.py Source-Study Technical-Note-Old.md --to-name Technical-Note-New.md --dry-run
python Scripts/_relocate_study_companion.py Source-Study Deck.pptx --to-study Target-Study --to-name Teaching.pptx --dry-run
```

Review the complete plan, then repeat the chosen command with `--yes` instead
of `--dry-run`. Omit `--to-study` for a same-study rename, or `--to-name` to keep
the filename. Occupied/unsafe targets fail before writes. Stable deck IDs are
retained. A deck move includes its declared slides/notes paths and linked
Presenter’s Companion chain. Move the owning deck to move presenter Markdown
between studies; a presenter-only rename stays beside its deck.

Shared figures stay in their original location. The script rebases relative
Markdown image/document links and repairs inbound Markdown links to moved paths.
Review reference-style links and authored HTML too. Canonical Markdown changed
by those repairs gets a real current Edited-on timestamp. Parent content and
catalog status otherwise remain untouched. Deck images embedded in PPTX need
no external image move.

Render every path printed by the command: notes through `_regenerate_pdf.py
<path>`, changed canonical sources by slug, presenter documents through
`_build_presenters_companion.py <path> --pdf --pptx <deck>`, and each affected
deck pair through `_build_presentations.py --deck <ID> --in-place`.
Guided-path slides follow the presentation manifest during finalization.

Complete [manage-studies: shared finish](../manage-studies/SKILL.md#shared-finish-before-review).
Pass `--study` for canonical sources changed by link repairs. Review both parent
inventories and all moved/retired URLs, then validate committed HEAD with the PR
body. Use `study-update`; CI recognizes relocated ownership and does not cascade
old-path cleanup into deletion of the moved chain. Publication remains coherent
and historical R2 retention is unchanged.

---
name: remove-study-companions
description: >-
  Remove one or more technical/research notes, presentation decks or presenter
  companions while preserving the parent study, catalog and proposal metadata.
  Use for companion-only deletion; runs Scripts/_remove_study_companions.py and
  the shared finalizer, including cleanup of each selected companion's owned outputs.
---

# Remove selected study companions

Use this skill for individual companion removal. `remove-study` retires the
entire study and every file below it; never use that command for a companion.

## Deletion scope

| Selected source | Removed with it | Preserved |
|-----------------|-----------------|-----------|
| Technical/research note `.md` | Its sibling `.html` and ignored `.pdf` | Parent study, other notes and decks |
| Deck `.pptx` | Its two manifest-declared PDFs; any linked Presenter's Companion MD/HTML/PDF/DOCX/notes JSON and ownership row | Parent study and other companions |
| Presenter's Companion `.md` alone | Its HTML/PDF/DOCX/notes JSON and ownership row | Deck and its existing speaker notes; those notes become authored in the PPTX |

The script preserves the parent canonical MD/HTML/PDF, Edited-on/Status,
catalog and proposal metadata. It removes no directories or shared figures.
Repair inbound links in the same PR; if this changes canonical study Markdown,
refresh that study's timestamp and regenerate its HTML/PDF through the usual skill.
Delete loose figures only when separately requested and proven unused by all
surviving documents/decks; directory proximity alone does not establish ownership.

## Commands

Work on a feature branch, from the repository root. Use bare companion filenames,
and pass multiple names to remove several companions in one study-update PR:

```powershell
python Scripts/_remove_study_companions.py <Slug> Technical-Note-Example.md Deck.pptx --dry-run
python Scripts/_remove_study_companions.py <Slug> Technical-Note-Example.md Deck.pptx --yes
python Scripts/_finalize_study_artifacts.py
```

Review the listed owned files, particularly a deck's linked presenter text.
The command requires a surviving canonical study source, rejects the canonical
MD/HTML/PDF and paths outside the selected study, validates the complete plan
before writing, and updates the deck/companion manifests by exact source identity.
For a partial deletion whose manifest entry has already gone, add
`--base-ref origin/master` to recover that entry from the last known source commit.

Complete [manage-studies: shared finish](../manage-studies/SKILL.md#shared-finish-before-review):
commit deletions, manifest and generated inventory/web updates together, then
validate committed HEAD with the PR body. Use `study-update` and the surviving
`Study slug: <Slug>`. Do not use `Operation: delete-study` for companion removal.
Leave Edited-on items N/A unless the canonical study Markdown also changes.

My Submissions supports individual deletion and selecting several companions in
one request. `delete-note`, `delete-presentation`, `delete-presenter`, and
`delete-companions` use the same scoped CI cleanup from deleted sources and base
manifests. Every selected source is version-checked before branch creation.
Whole-study deletion alone uses `delete-study`; companion deletion never retires
the parent. An empty global deck inventory is valid and selects no deck render.

To undo a retirement from merged history use
[restore-study](../restore-study/SKILL.md). To change a companion filename or
parent use [relocate-study-companion](../relocate-study-companion/SKILL.md).

After merge, coherent publication removes the retired outputs from the active
site inventory and keeps the parent study. Historical R2 object retention is a
separate policy; this command does not upload or purge remote objects.

---
name: restore-study
description: Restore a retired study or selected companion sources from a full commit SHA already in master history, using Scripts/_restore_study.py. Preserves historical canonical content and catalog metadata, rejects active-file/ownership conflicts, and rebuilds through the current shared pipelines.
---

# Restore retired study content

Use a feature branch and refresh the remote base. Select a full 40-character
commit SHA from merged master history where the study was Draft or Released.
This operation restores authoring sources; it does not roll back production or
activate an old deployment. A new or never-approved study still uses `add-study`
and the proposal approval workflow.

```powershell
python Scripts/_restore_study.py Study-Slug --from-ref <Merged-SHA> --dry-run
python Scripts/_restore_study.py Study-Slug --from-ref <Merged-SHA> --companion Technical-Note-Example.md --companion Deck.pptx --dry-run
```

Inspect the paths and ownership, then repeat with `--yes`. Whole-study restoration
requires an absent study directory and catalog entry. Companion-only restoration
requires the original parent to survive. Existing sources, conflicting deck IDs,
proposal ownership and changed shared figures fail before any replacement.
Deck restoration includes its presenter chain. Local note image dependencies
are restored when absent and reused only when their bytes still match.

The historical canonical Markdown, status and catalog date remain exact. Revise
content or change status in a subsequent PR. Generated PDFs are excluded from
recovery; render the restored Markdown/decks through current pinned producers.
Rebuild presenter DOCX/notes/PPTX from its Markdown and visually inspect affected
outputs. Complete [manage-studies: shared finish](../manage-studies/SKILL.md#shared-finish-before-review).
Run full reference checks for whole-study restoration because its reference
inventory rows are restored. Review links and discovery output.

For a whole-study restoration, use `study-update` and these bare PR-body fields:

```text
Study slug: Study-Slug
Operation: restore-study
Restore from: <Merged-SHA>
```

Required verification proves ancestry against the actual PR base, prior public
registration, and exact historical canonical/catalog content. This scoped proof
replaces a new first-draft approval only for genuine restoration. Companion-only
recovery uses an ordinary `study-update` PR and does not change parent metadata.
Coherent publication publishes the verified new revision after merge; historical
R2 objects and retained deployments are never purged by this command.

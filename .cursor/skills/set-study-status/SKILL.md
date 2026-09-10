---
name: set-study-status
description: >-
  Change a study between Draft and Released using Scripts/_set_study_status.py
  or _set_study_status.ps1 — syncs markdown Status, Edited on, catalogs, and PDF
  watermark. Use when releasing a study, reverting to draft, finalizing a paper,
  or updating draft/released status.
---

# Set study status (Draft ↔ Released)

Only for catalog studies whose current status is **Draft or Released**. A missing ignored local PDF does not make a study unpublished. Ongoing/Planned
entries cannot use this script — register the first draft with
[add-study](../add-study/SKILL.md) first.

## Commands

Set explicitly:

```powershell
python Scripts/_set_study_status.py <Slug> --status released
python Scripts/_set_study_status.py <Slug> --status draft
```

Toggle only when the user explicitly requests a toggle:

```powershell
python Scripts/_set_study_status.py <Slug>
```

Windows wrapper:

```powershell
.\Scripts\_set_study_status.ps1 <Slug> -Status released
```

Preview: `--dry-run`
Catalog/metadata only (no PDF): `--skip-pdf`
Skip sync check: `--no-check-timestamps`

The last two flags are for intermediate/diagnostic work. Complete the targeted
render and normal checks before review. Do not rerun the status setter merely
to finalize other artifacts: it refreshes the timestamp even for the same status.

## What the script does

1. Updates `**Status:**` and `**Edited on:**` in the canonical
   `Studies/<Slug>/<Slug>.md` or `Applications/<Slug>/<Slug>.md` — always set to
   the current IST time, even when status is unchanged
2. Updates the matching catalog JSON and `Studies/README.md` row, then rebuilds `Studies/index.html`
3. Regenerates the canonical markdown's tracked sibling `<Slug>.html` and ignored
   `<Slug>.pdf` verification artifact:
   - **Draft** → `--watermark Draft` via conversion pipeline
   - **Released** → no watermark

`**Status:**` is stripped from the PDF body by `_convert_to_pdf.py` — readers see watermark (draft) or clean pages (released).

## When to use

| Situation | Action |
|-----------|--------|
| Study finalized, ready for readers | `--status released` |
| Reopen for major revision | `--status draft` |
| Unsure of current state | Read canonical Status/catalog metadata; choose the requested explicit target |

## Manual PDF regen (if `--skip-pdf` was used)

See [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md) (`python Scripts/_regenerate_pdf.py <Slug>`).

## Completion checklist

- [ ] `**Status:**` in `.md` matches catalog (Draft or Released)
- [ ] `**Edited on:**` matches catalog **Last updated on**
- [ ] PDF watermark matches status
- [ ] Generated PDF was not added to Git; protected-branch CI publishes it to R2
- [ ] `verify_timestamp_sync` passed (default)

## Related

- Overview: [manage-studies](../manage-studies/SKILL.md)
- Add new study: [add-study](../add-study/SKILL.md)
- Regenerate PDF: [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md)
- Rules: [AGENTS.md](../../../AGENTS.md) §1 (Edited on), §2 (catalog sync), §3 (PDF pipeline)

## Finish with the shared CI workflow

Complete [manage-studies: shared finish](../manage-studies/SKILL.md#shared-finish-before-review)
after this skill's targeted renders. Use `_finalize_study_artifacts.py --study
<Slug>` for changed canonical metadata, or omit `--study` for companion-only
changes and retirement. Commit the tracked outputs, validate the committed
HEAD with `_validate_study_change.py` and the same PR body, and let protected
coherent-site publication handle changed artifacts after merge.

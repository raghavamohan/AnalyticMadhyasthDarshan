---
name: set-study-status
description: >-
  Change a study between Draft and Released using Scripts/_set_study_status.py
  or _set_study_status.ps1 — syncs markdown Status, Edited on, catalogs, and PDF
  watermark. Use when releasing a study, reverting to draft, finalizing a paper,
  or updating draft/released status.
---

# Set study status (Draft ↔ Released)

Only for **published** studies (linked in catalog with a PDF). Ongoing placeholders cannot use this script — register them with [add-study](../add-study/SKILL.md) first.

## Commands

Set explicitly:

```powershell
python Scripts/_set_study_status.py <Slug> --status released
python Scripts/_set_study_status.py <Slug> --status draft
```

Toggle current status:

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

## What the script does

1. Updates `**Status:**` and `**Edited on:**` in `Studies/<Slug>.md` — always set to the current IST time, even when status is unchanged
2. Updates matching row in `Studies/index.html` and `Studies/README.md`
3. Regenerates `Studies/<Slug>.pdf`:
   - **Draft** → `--watermark Draft` via conversion pipeline
   - **Released** → no watermark

`**Status:**` is stripped from the PDF body by `_convert_to_pdf.py` — readers see watermark (draft) or clean pages (released).

## When to use

| Situation | Action |
|-----------|--------|
| Study finalized, ready for readers | `--status released` |
| Reopen for major revision | `--status draft` |
| Unsure of current state | run without `--status` to toggle |

## Manual PDF regen (if `--skip-pdf` was used)

```powershell
python Scripts/_convert_to_pdf.py "Studies/<Slug>.md" --watermark Draft
node Scripts/_html_to_pdf.js "Studies/<Slug>.html"
Remove-Item "Studies/<Slug>.html"
```

Omit `--watermark Draft` for released studies.

## Completion checklist

- [ ] `**Status:**` in `.md` matches catalog (Draft or Released)
- [ ] `**Edited on:**` matches catalog **Last updated on**
- [ ] PDF watermark matches status
- [ ] `verify_timestamp_sync` passed (default)

## Related

- Overview: [manage-studies](../manage-studies/SKILL.md)
- Add new study: [add-study](../add-study/SKILL.md)
- Rules: `.cursor/rules/study-edited-on.mdc`, `.cursor/rules/md-to-pdf.mdc`

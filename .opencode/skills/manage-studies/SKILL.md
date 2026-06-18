---
name: manage-studies
description: >-
  Add, remove, or change Draft/Released status of studies in this repo using
  Scripts/_add_study.py, _remove_study.py, and _set_study_status.py. Use when
  registering a new study, retiring a study, releasing or reverting draft status,
  updating study catalogs, or when the user asks to manage studies in
  Studies/.
---

# Manage studies

Orchestration skill for the study lifecycle. Read the focused skill for your task:

| Task | Skill |
|------|-------|
| Register or add a study | [add-study](../add-study/SKILL.md) |
| Remove a study | [remove-study](../remove-study/SKILL.md) |
| Draft ↔ Released | [set-study-status](../set-study-status/SKILL.md) |

## Repository model

- **Source of truth:** `Studies/<Slug>.md`
- **Published output:** `Studies/<Slug>.pdf` (generated; never edit by hand)
- **Catalogs:** `Studies/index.html`, `Studies/README.md` (updated by scripts)
- **Citations:** `References/README.md`, `References/MANIFEST.md` (add/remove only)

## Study states

| State | Catalog | PDF |
|-------|---------|-----|
| Ongoing | Italic, no link | None |
| Draft | Linked + Draft status | Draft watermark |
| Released | Linked + Released status | No watermark |

## Prerequisites

From repo root (PowerShell):

```powershell
pip install pypdf markdown
Set-Location Scripts; npm install; Set-Location ..
```

## Which script?

```
New study or catalog entry?     → _add_study.py
Delete study entirely?          → _remove_study.py
Finalize or revert draft?       → _set_study_status.py
Edit body text only?            → edit .md, then `python Scripts/_regenerate_pdf.py <Slug>`
Quote check before PR?          → `python Scripts/_quote_tool.py verify --study <Slug>`
```

Always run scripts from the **repository root**. Append `--dry-run` to preview.

## After any study change

Confirm before finishing:

- [ ] `**Edited on:**` in `.md` matches catalog **Last updated on** (abbreviated month in catalog)
- [ ] `**Status:**` in `.md` matches catalog Draft/Released (if published)
- [ ] PDF regenerated when content or status changed
- [ ] `Studies/index.html` and `Studies/README.md` catalog rows stay in sync

**Agent rules:** [AGENTS.md](../../AGENTS.md) — §1 (Edited on), §2 (catalog sync), §3 (PDF pipeline).

## Study writing standards

When editing study **body text**, follow [AGENTS.md](../../AGENTS.md):

- §4 — prose style (no `[Text]` tags, `**Step N —**`, `**Verdict:**`, or honesty qualifiers)
- §5 — `## Standpoint and scope` on every topical study

Reference implementations: `Studies/What-Is-Existence.md`, `Studies/Why-Humans-Are-Not-Just-Material.md`.

Contributor overview: [Studies/README.md](../../Studies/README.md), [CONTRIBUTING.md](../../CONTRIBUTING.md)

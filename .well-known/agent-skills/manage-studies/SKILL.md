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
| Rename slug / sync proposal metadata | [rename-study](../rename-study/SKILL.md) |
| Regenerate PDF / fix diagrams | [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md) |
| Update teaching deck (PPTX) | [update-study-presentation](../update-study-presentation/SKILL.md) |
| Update Presenter's Companion notes | [update-presenters-companion](../update-presenters-companion/SKILL.md) |
| Audit / download references | [download-references](../download-references/SKILL.md) |

## Repository model

- **Source of truth:** `Studies/<Slug>/<Slug>.md`
- **Published output:** `Studies/<Slug>/<Slug>.html` and `.pdf` (generated; never edit by hand)
- **Companion deck artifacts** (generated; a study folder may hold more than one deck): `<Deck>.pptx` is the source of truth, and it produces `<Deck>.pdf` (slides only — what the index links), `<Deck>-notes.pdf` (slide plus read-aloud script per page, for the presenter), and alongside them `Presenters-Companion-<Name>.md` → `.notes.json` / `.docx` / `.pdf` (script plus background and Q&A). Deck-only changes never touch `**Edited on:**` or catalog timestamps.
- **Catalogs:** `Studies/index.html` (JSON + card UI shell), `Studies/README.md` (markdown tables; updated by scripts)
- **Index shell source:** `Scripts/_build_studies_index.py` (`INDEX_TEMPLATE`) — edit template, run `python Scripts/_build_studies_index.py`, verify with `python Scripts/_verify_studies_index.py`
- **Citations:** `References/README.md`, `References/MANIFEST.md` (add/remove only)

## Study states

| State | Catalog | PDF |
|-------|---------|-----|
| Ongoing | Italic, no link | None |
| Draft | Linked + Draft status | Draft watermark |
| Released | Linked + Released status | No watermark |

## Before you start

Create a feature branch before touching anything under `Studies/` — never commit study
changes directly to the default branch. See [AGENTS.md](../../../AGENTS.md) §7 for the full
branch/PR-label/template workflow; this skill covers file-level correctness only.

## Prerequisites

From repo root (PowerShell):

```powershell
pip install -r requirements.txt
Set-Location Scripts
npm ci
npx puppeteer browsers install chrome
Set-Location ..
```

## Which script?

```
New study or catalog entry?     → _add_study.py
Delete study entirely?          → _remove_study.py
Finalize or revert draft?       → _set_study_status.py
Rename slug (directory move)?   → [rename-study](../rename-study/SKILL.md) (`_rename_study.py`; study-update PR)
Edit body text only?            → edit .md, then [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md)
Edit slides or slide order?     → [update-study-presentation](../update-study-presentation/SKILL.md); regenerate `<Deck>.pdf` then `<Deck>-notes.pdf`
Edit read-aloud scripts only?   → [update-presenters-companion](../update-presenters-companion/SKILL.md); re-sync notes, then rebuild `<Deck>-notes.pdf`
Quote check before PR?          → `python Scripts/_quote_tool.py verify --study <Slug>`
```

Always run scripts from the **repository root**. The lifecycle entry points
`_add_study.py`, `_remove_study.py`, and `_set_study_status.py` support
`--dry-run`; check `--help` rather than assuming unrelated commands do.

## After any study change

Confirm before finishing:

- [ ] `**Edited on:**` in `.md` matches catalog **Last updated on** (abbreviated month in catalog)
- [ ] `**Status:**` in `.md` matches catalog Draft/Released (if published)
- [ ] PDF regenerated when content or status changed (pinned Node dependencies and Chrome installed under `Scripts/`)
- [ ] `Studies/catalog-*.json` and `Studies/README.md` table rows stay in sync (use `write_studies_catalog` via scripts — never hand-edit JSON)
- [ ] After landing-page UI changes: `INDEX_TEMPLATE` updated in `_build_studies_index.py`, shell rebuilt, `python Scripts/_verify_studies_index.py` passes
- [ ] Change is on a feature branch (not the default branch); the PR to open carries exactly one
  of `new-study` / `study-update` / `status-change` and the body field that label requires —
  [AGENTS.md](../../../AGENTS.md) §7

**Agent rules:** [AGENTS.md](../../../AGENTS.md) — §1 (Edited on), §2 (catalog sync), §3 (PDF pipeline), §7 (submission process: branches, PR labels, templates).

## Study writing standards

When editing study **body text**, follow [AGENTS.md](../../../AGENTS.md):

- §4 — prose style (no `[Text]` tags, `**Step N —**`, `**Verdict:**`, or honesty qualifiers)
- §5 — `## Standpoint and scope` on every topical study

Reference implementations: `Studies/The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.md`, `Studies/Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.md`.

Contributor overview: [Studies/README.md](../../../Studies/README.md), [CONTRIBUTING.md](../../../CONTRIBUTING.md)

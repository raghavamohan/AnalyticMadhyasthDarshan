---
name: rename-study
description: >-
  Rename a study slug and/or display title using Scripts/_rename_study.py —
  moves the study directory, syncs catalogs, proposal-registry, GitHub proposal
  issue, References paths, Start here links, and regenerated PDF/HTML. Use when
  renaming a study, changing a catalog slug, fixing a too-long slug, or updating
  My Submissions after a rename.
---

# Rename a study

Renames `Studies/<Old-Slug>/` (or `Applications/<Old-Slug>/`) to a new slug and
keeps portal, catalog, and My Submissions metadata in sync. This is a
**`study-update`** change — never commit the rename on `master`/`main`.

## Before you start

1. Create a **feature branch** from an up-to-date default branch.
2. Confirm the new slug:
   - Characters: letters, digits, hyphens only (`[A-Za-z0-9-]+`)
   - Length: **≤ 60** characters (portal rejects longer slugs)
   - Path: `Studies/<Slug>/<Slug>.md` must stay ≤ 200 characters
3. Decide the new **display title** (H1 / catalog / proposal issue title).
4. Note the proposal issue number if known (also in
   `Studies/<Old-Slug>/.proposal-meta.json` or `Studies/proposal-registry.json`).

## Core command

Preview first:

```powershell
python Scripts/_rename_study.py --from Old-Slug --to New-Slug --title "New display title" --dry-run
```

Then run (from repo root):

```powershell
python Scripts/_rename_study.py --from Old-Slug --to New-Slug --title "New display title"
```

Windows wrapper: `.\Scripts\_rename_study.ps1` (same flags).

### Flags

| Flag | Purpose |
|------|---------|
| `--from` / `--to` | Required old and new catalog slugs |
| `--title` | New display title (catalog, registry, proposal issue) |
| `--issue N` | Proposal issue number (optional; auto-resolved from meta/registry) |
| `--dry-run` | Preview without writing |
| `--metadata-only` | Skip filesystem rename; sync registry/issue/references only (directory already moved) |
| `--skip-issue` | Do **not** patch the GitHub proposal issue (avoid unless blocked; see My Submissions below) |
| `--skip-pdf` | Skip PDF/discussion regeneration (finish with `_regenerate_pdf.py` later) |

### What the script updates

- Directory and stem-matched files: `<Old>.md` / `.html` / `.pdf` → `<New>.*`
  (companion decks with other basenames move with the folder unchanged)
- Topical/formal/applied catalog row (slug + title)
- `Studies/proposal-registry.json` and `Studies/<New-Slug>/.proposal-meta.json`
- `References/README.md` and `References/MANIFEST.md` study PDF/HTML paths
- GitHub proposal issue: `### Slug`, `### Proposed title`, and
  `Study proposal: <title>` issue title (unless `--skip-issue`)
- Regenerated study PDF, HTML, and discussion page (unless `--skip-pdf`)

## Manual steps the script does **not** cover

Complete these on the same feature branch before opening the PR:

1. **Study H1** — `_rename_study.py` does not rewrite `# Title` in the `.md`.
   Set it to the new display title when the title changes.
2. **`**Edited on:**`** — refresh with real IST time
   (`Get-Date -Format "MMMM d, yyyy, h:mm tt"` + ` IST`), then sync catalog
   **Last updated on** (abbreviated month). See [AGENTS.md](../../AGENTS.md) §1.
3. **Display order** — if the slug appears in
   `TOPICAL_DISPLAY_ORDER` in `Scripts/_study_catalog.py`, replace the old slug.
4. **Start here path** — if the study is a core stage in
   `Scripts/_build_studies_index.py` (`INDEX_TEMPLATE`), update
   `data-study-slug`, presentation PDF hrefs, discuss link, and visible title;
   then `python Scripts/_build_studies_index.py` and
   `python Scripts/_verify_studies_index.py`.
5. **Agent docs** — update path mentions in `AGENTS.md` (and any skill text)
   that cite `Studies/<Old-Slug>/…`; run
   `python Scripts/_sync_agent_rules.py` and `--check` when `AGENTS.md` or
   `.agents/skills/**` change.
6. **References link text** — script rewrites paths; if the markdown link label
   still shows `<Old-Slug>.pdf`, rename the label to match.
7. **Cross-study links** — other studies’ `.md` files that point at the old
   slug are **out of scope for this PR**. [AGENTS.md](../../AGENTS.md) §7:
   one study slug per `study-update` PR. Open follow-up PRs per linked study.

## My Submissions (portal)

My Submissions (`Studies/submit.html` → `GET /api/me/submissions`) joins:

| Source | Role after rename |
|--------|-------------------|
| `Studies/proposal-registry.json` | Canonical slug for the proposal `issueNumber` |
| GitHub proposal issue | Card **title** (`Study proposal: …`) and body `### Slug` / `### Proposed title` |
| `Studies/catalog-*.json` | Catalog status (draft / released / ongoing) |

**Do not skip the proposal-issue patch** unless GitHub auth is unavailable.
If you used `--skip-issue`, finish with either:

```powershell
# Preferred: metadata-only rename sync (needs GITHUB_TOKEN + GITHUB_REPOSITORY)
$env:GITHUB_TOKEN = (gh auth token)
$env:GITHUB_REPOSITORY = "raghavamohan/AnalyticMadhyasthDarshan"
python Scripts/_rename_study.py --from Old-Slug --to New-Slug --title "New display title" --metadata-only --skip-pdf
```

or patch the issue with `gh issue edit` so `### Slug`, `### Proposed title`, and
the issue title all use the new values.

Registry without issue sync → wrong title or (if registry missing) wrong slug on
the dashboard. Historical merged PRs may still say `Study slug: Old-Slug`; the
submissions worker drops merged orphan PRs whose slug is no longer in the
catalog or registry so they do not create a second ghost row.

## Pull request

1. Local checks (as applicable):

```powershell
python Scripts/_check_references.py --study <New-Slug>
python Scripts/_regenerate_pdf.py <New-Slug>
python Scripts/_verify_studies_index.py
```

2. Open a **`study-update`** PR (template
   [.github/PULL_REQUEST_TEMPLATE/study-update.md](../../.github/PULL_REQUEST_TEMPLATE/study-update.md)):

```text
Study slug: New-Slug
```

Bare slug only — no notes on that line. Apply label **`study-update`** (exactly
one study label). CI (`Scripts/_ci_study_pr.py`) detects one slug removed + one
added and can run `_rename_study.py --metadata-only` on the branch.

## Completion checklist

- [ ] Feature branch (not default branch)
- [ ] `_rename_study.py` run (dry-run first); new directory
      `Studies/<New-Slug>/<New-Slug>.md` exists
- [ ] H1 / display title updated in the study `.md` when the title changed
- [ ] `**Edited on:**` and catalog **Last updated on** match
- [ ] `proposal-registry.json` and `.proposal-meta.json` use **New-Slug**
- [ ] GitHub proposal issue slug + title updated (verify with `gh issue view`)
- [ ] Start here / `TOPICAL_DISPLAY_ORDER` updated if they referenced the old slug
- [ ] PDF/HTML/discussion regenerated for **New-Slug**
- [ ] PR labeled `study-update` with `Study slug: New-Slug`
- [ ] Cross-study link updates left for separate one-slug PRs
- [ ] Agent rules/skills synced if `AGENTS.md` or `.agents/skills/**` changed

## Related

- Overview: [manage-studies](../manage-studies/SKILL.md)
- PDF regen: [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md)
- Index / Start here: [refine-studies-index](../refine-studies-index/SKILL.md)
- Rules: [AGENTS.md](../../AGENTS.md) §1, §2, §3, §7; [CONTRIBUTING.md](../../CONTRIBUTING.md) (slug rename)

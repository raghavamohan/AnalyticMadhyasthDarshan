---
name: remove-study
description: >-
  Remove a study from Studies/ or Applications/ using Scripts/_remove_study.py
  or _remove_study.ps1 — deletes the complete directory and updates catalogs,
  proposal metadata, and References. Use when retiring a study, deleting a
  paper, removing an Ongoing placeholder, or cleaning up a study slug.
---

# Remove a study

## Command

From repo root:

```powershell
python Scripts/_remove_study.py <Slug>
```

Skip confirmation:

```powershell
python Scripts/_remove_study.py <Slug> --yes
```

Preview:

```powershell
python Scripts/_remove_study.py <Slug> --dry-run
```

Windows wrapper: `.\Scripts\_remove_study.ps1 <Slug> [-Yes] [-DryRun]`

Use the slug without extension (e.g. `The-Ontology-of-Coexistence`).

## What the script does

1. Deletes the complete `Studies/<Slug>/` (or `Applications/<Slug>/`) directory,
   including companion files
2. Removes the Topical, Formal, or Applied catalog entry from catalog JSON,
   `Studies/README.md`, and the rebuilt `Studies/index.html`
3. Removes the slug from `Studies/proposal-registry.json`, so proposal sync cannot recreate it
4. For published studies (not Ongoing): removes the row from `References/README.md`,
   the paper block from `References/MANIFEST.md`, and its By-tag citations while
   preserving citations to other studies
5. Removes every deck sourced from the retired study from
   `Scripts/presentation-pipeline.json`

Ongoing placeholders (italic, no public PDF) are supported — their directory,
catalog row, and proposal-registry row are removed.

## After removal

1. **Remove or retarget cross-links in the same PR** — CI rejects any remaining
   Markdown link to the retired slug. When linked study markdown changes, refresh
   its timestamp/catalog row and regenerate its PDF.
2. **Update Start here** if `INDEX_TEMPLATE` names the slug; rebuild the index.
   CI rejects unknown Start here slugs.
3. **Verify** catalogs and references with `python Scripts/_verify_studies_index.py`
   and `python Scripts/_check_references.py`
4. **Commit** deletions and catalog updates on a feature branch
5. **Open a ready-for-review pull request** with the `study-update` template and
   label. Keep the retired directory name as the bare `Study slug: <Slug>` value;
   mark Edited-on and quote-verification checklist items N/A.

A single `study-update` PR may remove multiple studies. Name one retired slug in
the PR body; CI derives and validates every deleted study directory from the diff.

## Do not

- Delete catalog entries by hand — use this script (`write_studies_catalog` updates JSON and README together)
- Remove files without updating catalogs — leaves broken links on the site

## Related

- Overview: [manage-studies](../manage-studies/SKILL.md)
- Add: [add-study](../add-study/SKILL.md)
- Rules: [AGENTS.md](../../../AGENTS.md) §2 (catalog sync when removing published studies)

---
name: remove-study
description: >-
  Remove a study from Studies/ using Scripts/_remove_study.py or
  _remove_study.ps1 — deletes files and updates catalogs and References. Use when
  retiring a study, deleting a paper, removing an Ongoing placeholder, or
  cleaning up a study slug.
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

1. Deletes `Studies/<Slug>/<Slug>.md`, `.pdf`, and `.html` (if present)
2. Removes catalog entry from **Topical** or **Formal** catalog in `Studies/index.html` (JSON) and `Studies/README.md` (markdown table)
3. For published studies (not Ongoing): removes row from `References/README.md` and paper block from `References/MANIFEST.md`

Ongoing placeholders (italic, no PDF) are supported — only the catalog row is removed.

## After removal

1. **Search cross-links** — grep other `Studies/*/*.md` for links to the removed slug
2. **Review** `References/MANIFEST.md` summary counts if needed
3. **Commit** deletions and catalog updates

## Do not

- Delete catalog entries by hand — use this script (`write_studies_catalog` updates JSON and README together)
- Remove files without updating catalogs — leaves broken links on the site

## Related

- Overview: [manage-studies](../manage-studies/SKILL.md)
- Add: [add-study](../add-study/SKILL.md)
- Rules: [AGENTS.md](../../AGENTS.md) §2 (catalog sync when removing published studies)

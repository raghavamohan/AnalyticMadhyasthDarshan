---
name: refine-studies-index
description: >-
  Review and refine the Studies landing page, including the guided Start here
  path, hero and methodology copy, navigation, status language, catalog
  descriptions, contribution flow, and About section. Use when auditing or
  updating Studies/index.html through Scripts/_build_studies_index.py while
  keeping Studies/README.md, catalog JSON, proposal metadata, and generated
  artifacts synchronized.
---

# Refine the Studies index

Treat the landing page as a reader journey, not only a catalog. Preserve the
personal study path while keeping the surrounding project comparative, open,
and collaborative.

## Decide the task mode

- For a **review**, inspect the complete page and report prioritized,
  implementable comments. Do not edit files.
- For an **update**, create a feature branch before changing any file under
  `Studies/`. Never make Studies changes directly on `master` or `main`.
- For a **PR follow-up**, check whether the existing PR is open or merged before
  deciding whether to push to it or create a new branch and PR.

## Review the copy

Read the page in this order:

1. Hero, metadata, and comparison partners
2. Sticky navigation
3. Start here path and its parallel track
4. Transition into the complete catalog
5. Status and collection filters
6. How we work
7. How to contribute
8. About and independence statement
9. Catalog titles and descriptions

Use these editorial checks:

- Use **we/the project** throughout, including for the Start here path, and
  **Madhyasth Darshan holds** for claims of the philosophy. The site speaks
  with one voice; do not reintroduce first-person singular for the study path.
  Where a sentence needs the universal "we" meaning people, rephrase it
  (*how a human should live*) so the referent cannot be read as the project.
- Present comparisons as inquiry rather than predetermined conclusions.
- Make the reader journey explicit: human, existence, knowledge, value, lived
  participation, with formal/scientific synthesis as a parallel track.
- Distinguish public statuses clearly: **Released**, **Draft**, and **In
  progress**. The stored lifecycle value may remain `ongoing`.
- Explain how readers can discuss a claim, correct a concrete error, review a
  draft, or help develop an in-progress study.
- Avoid self-evaluative copy such as “carefully argued,” exaggerated fidelity
  claims, forced mathematical formalization, and vague phrases such as “fit
  with public knowledge.”
- Keep source doctrine, project analysis, and open questions visibly separate.
- Hide or identify empty collections rather than leading readers to dead ends.

## Edit the sources of truth

Do not edit `Studies/index.html` as the source.

- Edit the HTML/CSS/JavaScript shell in
  `Scripts/_build_studies_index.py` (`INDEX_TEMPLATE`).
- Keep shared lead, How we work, How to contribute, and About prose aligned in
  `Studies/README.md`.
- Edit ongoing/pre-catalog study descriptions in
  `Studies/proposal-registry.json`.
- Do not hand-edit `Studies/catalog-*.json`. For a Draft or Released catalog
  description, load its `StudyRow` with `Scripts/_study_catalog.py`, update the
  row, and call `write_studies_catalog`.

Example catalog-description update from the repository root:

```powershell
@'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("Scripts").resolve()))
from _study_catalog import StudyTable, load_catalog_rows, write_studies_catalog

rows = load_catalog_rows(StudyTable.TOPICAL)
for row in rows:
    if row.slug == "Study-Slug":
        row.description = "Revised catalog description"
write_studies_catalog(
    rows,
    StudyTable.TOPICAL,
    rebuild_discussion=False,
    rebuild_feedback_template=False,
)
'@ | python
```

Do not refresh a study's `Edited on` timestamp or regenerate its PDF when only
landing-page prose or catalog-card wording changes. Follow the normal study
workflow if the study markdown itself changes.

## Rebuild and verify

Run from the repository root:

```powershell
python Scripts/_build_studies_index.py
python Scripts/_verify_studies_index.py
python -m py_compile Scripts/_build_studies_index.py
git diff --check
git status --short
```

After rebuilding:

- Confirm the generated `Studies/index.html` matches the template.
- Confirm README tables and catalog JSON agree.
- Confirm navigation targets exist and follow the intended order.
- Confirm visible UI text says **In progress**, not **Planned**, when that is
  the chosen public label.
- Confirm every Start here slug exists in the catalog and its status/date are
  populated from catalog data rather than duplicated manually.
- Confirm empty collection controls and groups do not appear as dead ends.
- Parse or exercise generated JavaScript when JavaScript changed.
- Inspect desktop and narrow layouts when browser preview is available.
- Preserve LF line endings in every touched text file.
- Review the final diff for unrelated generator output.

## Pull request

Landing-page and root-catalog changes use a normal feature PR. Do not apply a
study-specific label unless files under `Studies/<Slug>/` or
`Applications/<Slug>/` also change. Include the rebuild and verification
commands in the PR body.

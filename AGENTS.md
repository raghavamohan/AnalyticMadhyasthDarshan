# AGENTS.md

This file carries the standing instructions for AI agents working in this repo.
It replaces the earlier `.cursor/rules/*.mdc` files; those still exist for
Cursor, but this is the source of truth for ZCode/opencode.

There are three rule sections below. The first applies to **every** study edit;
the other two apply when their stated condition is met.

---

## 1. Keep "Edited on" current in Studies *(always applies)*

Every study under `Studies/` carries an `**Edited on:**` field directly below
the `**Author:**` line. **Any change to study content** — including edits made
during review, restructuring, typo fixes in body text, citation updates, or PDF
regeneration after content changes — **must** refresh that timestamp before you
finish the task.

### Mandatory workflow (do not skip steps)

When you edit a study markdown file (`Studies/<Name>.md`):

1. **Get the real current time** — run in PowerShell from the repo root:
   `Get-Date -Format "MMMM d, yyyy, h:mm tt"`
   Append ` IST` to the result. **Never** guess, round, or copy a timestamp from
   another file or an earlier message.
2. **Update `**Edited on:**`** in the study `.md` — format:
   `**Edited on:** Month D, YYYY, h:mm AM/PM IST`
   (e.g. `June 16, 2026, 3:45 PM IST`).
3. **Update the catalog `Status` date** in **both** `Studies/README.md` and
   `Studies/index.html` for that study's row. Use the same date and time as
   step 2, with abbreviated month in the catalog (`Jun` not `June`):
   `Draft<br>Last updated on: Jun 16, 2026, 3:45 PM IST`
4. **Regenerate the PDF** using the pipeline in
   [§3 Markdown to PDF](#3-markdown-to-pdf--use-internal-scripts-only-applies-when-generating-a-study-pdf)
   (never ad-hoc converters). The PDF embeds the `**Edited on:**` line from the
   markdown — an old timestamp in the `.md` means an old timestamp in the PDF.

If the field is missing, add it on its own line immediately after the
`**Author:**` line, separated by a blank line.

### Status values in catalogs

- `Ongoing` — no document uploaded yet (italic title, no PDF).
- `Draft<br>Last updated on: <date>, <time> IST` — a document/PDF exists but is
  not finalized (date/time **must match** the study's `**Edited on:**` field).
- `Released<br>Last updated on: <date>, <time> IST` — only once a study is
  explicitly finalized/released.

### When to update

Update the timestamp whenever **any** of these change in the study `.md`:

- Body text, headings, tables, blockquotes, or references
- Structure (sections added, removed, or reordered)
- Metadata other than `**Edited on:**` itself

The **only** exception: editing this rule file's own example timestamps.

### Completion check

Before marking a study edit done, confirm all three are in sync:

- [ ] `Studies/<Name>.md` → `**Edited on:**`
- [ ] `Studies/README.md` → that study's `Last updated on`
- [ ] `Studies/index.html` → that study's `Last updated on`
- [ ] `Studies/<Name>.pdf` regenerated after the timestamp change

---

## 2. Keep Studies/index.html and Studies/README.md in sync *(applies when editing the study catalogs)*

`Studies/index.html` (the published site page) and `Studies/README.md` (the
GitHub-rendered page) present the same catalog to two audiences. Whenever you
change one, make the matching change in the other in the same edit so they never
drift apart.

### What must always match

- **Topical Studies catalog** — the rows between the `<!-- studies-catalog -->`
  and `<!-- /studies-catalog -->` markers (present in both files): same studies,
  same order, same titles, categories, descriptions, and `Status` values.
  Status is `Ongoing` when no document is uploaded yet (no PDF),
  `Draft<br>Last updated on: <date>, <time> IST` once a PDF exists but is not
  finalized, and `Released<br>Last updated on: <date>, <time> IST` only when a
  study is explicitly released.
  **When a study is edited**, the `Last updated on` date/time in both catalogs
  must match that study's `**Edited on:**` field in its `.md` file exactly
  (abbreviated month in catalogs: `Jun`; full month in `.md`: `June`). See
  [§1 Keep "Edited on" current](#1-keep-edited-on-current-in-studies-always-applies)
  for the mandatory workflow.
- **In-progress studies** — shown in italics (`<em>...</em>` in HTML,
  `*...*` in markdown) with no link; published studies link to `<Name>.pdf`.
- **Formal Studies table** — same documents, focus, and descriptions.
- **Shared prose** — the lead intro, Study Objectives, **About us**, and
  License sections should carry the same wording.

### Intentional differences (do NOT force these to match)

- `Studies/index.html` has a **"From Study to Understanding"** section (site-only).
- `Studies/index.html` and `Studies/README.md` both end with **How to contribute**
  and **About us** after the study catalogs; wording should stay aligned.

### How to verify

After editing, re-read both catalogs and confirm the study list is identical
(count, order, titles, categories, descriptions, and which entries are linked vs.
italicised). If you add or remove a study, update both files plus
`References/README.md` and `References/MANIFEST.md`.

---

## 3. Markdown to PDF — use internal scripts only *(applies when generating a study PDF)*

When a study markdown file under `Studies/` needs a PDF, **always** use the
repository pipeline. Do not substitute pandoc, `markdown-pdf`, VS Code export,
hand-written Puppeteer scripts, or other one-off converters.

### Required two-step pipeline

1. **`Scripts/_convert_to_pdf.py`** — markdown → styled HTML (same basename, `.html`).
2. **`Scripts/_html_to_pdf.js`** — HTML → PDF via Puppeteer (footer, A4 margins).

Run from the repository root in PowerShell:

```powershell
python Scripts/_convert_to_pdf.py Studies/<Name>.md --watermark Draft
node Scripts/_html_to_pdf.js Studies/<Name>.html
Remove-Item Studies/<Name>.html
```

- **`--watermark Draft`** — required for studies in **Draft** status (diagonal
  watermark on every page). Omit only when regenerating a **Released** study.
- **Delete the intermediate `.html`** after PDF generation; it is a build
  artifact, not a published file.

### What the scripts provide (do not reimplement)

- Study typography, tables, blockquotes, and print CSS — `_convert_to_pdf.py`
- **`**Status:**` omitted from the PDF body** — draft/released is shown via watermark
  (Draft) or its absence (Released); the flag remains in the `.md` source only
- Footer on every page: `AnalyticMadhyasthDarshan.org` and `Page X of Y` —
  `_html_to_pdf.js`
- Optional page watermark — `--watermark` on `_convert_to_pdf.py`

### Regenerate one or all studies

Single study — replace `<Name>` with the file stem (e.g. `Aesthetics`).

All studies (exclude `README.md`):

```powershell
$studies = Get-ChildItem Studies/*.md | Where-Object { $_.Name -ne 'README.md' }
foreach ($s in $studies) {
  python Scripts/_convert_to_pdf.py $s.FullName --watermark Draft
  $html = $s.FullName -replace '\.md$', '.html'
  node Scripts/_html_to_pdf.js $html
  Remove-Item $html
}
```

### After conversion

- Confirm the output PDF path is `Studies/<Name>.pdf` (same stem as the `.md`).
- **Before** running the pipeline, ensure `**Edited on:**` in the `.md` reflects
  the current time (see
  [§1 Keep "Edited on" current](#1-keep-edited-on-current-in-studies-always-applies)
  — run `Get-Date`, never guess). Regenerating a PDF without updating the
  timestamp leaves a stale date on every page of the document header.
- After conversion, if the study's `**Edited on:**` or catalog **Status**
  changed, confirm both catalogs match per
  [§2 catalog sync](#2-keep-studiesindexhtml-and-studiesreadmemd-in-sync-applies-when-editing-the-study-catalogs).

### Do not

- Edit PDFs directly or commit hand-built HTML as the source of truth.
- Change conversion behavior inline in chat without updating these scripts when
  the change should apply to all future PDFs (footer, watermark, styling).

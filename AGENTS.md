# AGENTS.md

This file carries the standing instructions for AI agents working in this repo.
It is the **source of truth** for ZCode, OpenCode, and other agents that read
`AGENTS.md` at the repository root.

**Cursor** loads the same content through `.cursor/rules/*.mdc` mirrors (one file
per section below). **OpenCode / ZCode** loads `AGENTS.md` automatically and also reads
`.cursor/rules/*.mdc` via `opencode.json` → `instructions`.

**After editing `AGENTS.md` (§1–§6) or any `.agents/skills/**/SKILL.md`**, run sync before
you finish the task or commit:

```powershell
python Scripts/_sync_agent_rules.py
python Scripts/_sync_agent_rules.py --check
```

This updates `.cursor/rules/*.mdc` and `.cursor/skills/` from the canonical sources.
Commit sync output in the **same commit** as the canonical edit. Full workflow:
`.cursor/rules/agent-rules-sync.mdc` (always applies).

**Skills** (study lifecycle scripts) live in `.agents/skills/` (canonical). **OpenCode /
ZCode** loads them through `.opencode/skills/`, a junction to `.agents/skills/`.
**Cursor** also reads `.agents/skills/`; an identical copy is kept in `.cursor/skills/`.
Skills orchestrate `Scripts/_*.py`; they defer content and style rules to the sections below.

Available skills: `manage-studies`, `add-study`, `remove-study`, `set-study-status`,
`download-references`, `check-references`, `regenerate-study-pdf`.

| Section | Topic | Cursor mirror |
|---------|--------|---------------|
| *(meta)* | Agent rules & skills sync | `agent-rules-sync.mdc` |
| §1 | Edited on, catalogs, PDF timestamps | `study-edited-on.mdc` |
| §2 | `Studies/index.html` ↔ `README.md` sync | `studies-index-readme-sync.mdc` |
| §3 | Markdown → PDF pipeline | `md-to-pdf.mdc` |
| §4 | Study prose style | `study-prose-style.mdc` |
| §5 | Standpoint and scope | `study-standpoint-scope.mdc` |
| §6 | Reference checks when citations change | `study-references-check.mdc` |

There are six rule sections below. The first, fourth, fifth, and sixth apply when
their stated conditions are met; §1 also applies to every topical study edit.

---

## 1. Keep "Edited on" current in Studies *(always applies)*

Every study under `Studies/` lives in its own directory: `Studies/<Slug>/<Slug>.md`,
companion PDF, and any figures. Catalog files `Studies/README.md` and
`Studies/index.html` stay at the `Studies/` root.

Every study carries an `**Edited on:**` field directly below
the `**Author:**` line. **Any change to study content** — including edits made
during review, restructuring, typo fixes in body text, citation updates, or PDF
regeneration after content changes — **must** refresh that timestamp before you
finish the task.

### Mandatory workflow (do not skip steps)

When you edit a study markdown file (`Studies/<Slug>/<Slug>.md`):

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

- [ ] `Studies/<Slug>/<Slug>.md` → `**Edited on:**`
- [ ] `Studies/README.md` → that study's `Last updated on`
- [ ] `Studies/index.html` → that study's `Last updated on`
- [ ] `Studies/<Slug>/<Slug>.pdf` regenerated after the timestamp change

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
  `*...*` in markdown) with no link; published studies link to `<Slug>/<Slug>.pdf`.
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

### One-time setup (required for PDF generation)

```powershell
pip install -r requirements.txt
cd Scripts
npm install
cd ..
```

`npm install` in `Scripts/` installs **Puppeteer**, **pdf-lib**, and **mermaid** (for
` ```mermaid ` diagrams in studies). CI runs `npm ci` in `Scripts/` automatically.

### Regenerate one study

```powershell
python Scripts/_regenerate_pdf.py <Name>
```

Reads **Status:** from the markdown and applies the Draft watermark when appropriate.

### Internal pipeline (batch or debugging)

`_regenerate_pdf.py` runs this pipeline:

1. **`Scripts/_convert_to_pdf.py`** — markdown → styled HTML (same basename, `.html`).
   Converts ` ```mermaid ` fenced blocks to `<div class="mermaid">` for rendering.
2. **`Scripts/_html_to_pdf.js`** — loads Mermaid from `Scripts/node_modules`, renders
   `.mermaid` divs to SVG, then HTML → PDF via Puppeteer (footer, A4 margins).
3. **`Scripts/_verify_pdf_diagrams.py`** — after PDF generation, fails if markdown
   contains Mermaid but raw diagram syntax (e.g. `flowchart TD`) still appears in the PDF.
4. **`Scripts/_verify_pdf_fenced_code.py`** — fails if fenced ` ```text ` / code-block
   content is clipped in the PDF (e.g. `[compound]` truncated to `[c`).

Regenerate all studies:

```powershell
$studies = Get-ChildItem Studies -Directory
foreach ($s in $studies) {
  python Scripts/_regenerate_pdf.py $s.Name
}
```

Manual single-study steps (only if needed):

```powershell
python Scripts/_convert_to_pdf.py Studies/<Slug>/<Slug>.md
node Scripts/_html_to_pdf.js Studies/<Slug>/<Slug>.html Draft
python Scripts/_verify_pdf_diagrams.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf
python Scripts/_verify_pdf_fenced_code.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf
Remove-Item Studies/<Slug>/<Slug>.html
```

- **`Draft`** argument to `_html_to_pdf.js` — required for **Draft** studies. Omit for **Released**.
- **Delete the intermediate `.html`** after PDF generation; it is a build artifact.

### What the scripts provide (do not reimplement)

- Study typography, tables, blockquotes, and print CSS — `_convert_to_pdf.py`
- **Fully justified body paragraphs** — all `<p>` elements use `text-align: justify`
  (with `text-justify: inter-word` and `hyphens: auto`) in screen and print CSS;
  list items and table cells remain left-aligned — `_convert_to_pdf.py`
- **Embedded study figures** — PNG (or other raster) images referenced from the
  study `.md` (same directory) render in HTML/PDF with responsive width — `_convert_to_pdf.py`
- **Mermaid flowcharts and diagrams** — fenced ` ```mermaid ` blocks become rendered SVG
  in the PDF via `_convert_to_pdf.py` + `_html_to_pdf.js`; verified by
  `_verify_pdf_diagrams.py` after each regeneration
- **Fenced code and spec blocks** — ` ```text ` and other fenced code use `white-space:
  pre-wrap` so long lines wrap inside the page; verified by `_verify_pdf_fenced_code.py`.
  Prefer a **table** for multi-column formal specs (Petri transitions, type signatures)
  when lines would exceed ~80 characters — tables do not clip in PDF.
- **`**Status:**` omitted from the PDF body** — draft/released is shown via watermark
  (Draft) or its absence (Released); the flag remains in the `.md` source only
- **Clickable local bibliography and cross-study links** — relative `../References/…`
  and cross-study `.pdf` hrefs in the HTML intermediate are rewritten to
  `https://<CNAME>/References/…` and `https://<CNAME>/Studies/…` (from `CNAME`
  at repo root) so PDF links opened from the published site download repository
  files; external `http(s)` links are unchanged — `_convert_to_pdf.py`
- Footer on every page: `AnalyticMadhyasthDarshan.org` and `Page X of Y` —
  `_html_to_pdf.js`
- Optional page watermark — `--watermark` on `_convert_to_pdf.py`

### Regenerate one or all studies

Single study — replace `<Name>` with the file stem (e.g. `Aesthetics`):

```powershell
python Scripts/_regenerate_pdf.py <Name>
```

All studies:

```powershell
$studies = Get-ChildItem Studies -Directory
foreach ($s in $studies) {
  python Scripts/_regenerate_pdf.py $s.Name
}
```

### After conversion

- Confirm the output PDF path is `Studies/<Slug>/<Slug>.pdf` (same stem as the `.md`).
- If the study uses ` ```mermaid ` blocks, confirm the PDF shows diagrams (not raw
  `flowchart TD` source). Regeneration runs `_verify_pdf_diagrams.py` automatically;
  manual check: `python Scripts/_verify_pdf_diagrams.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf`
- If the study uses long ` ```text ` spec blocks, confirm bracket tags and line tails
  are intact. Regeneration runs `_verify_pdf_fenced_code.py` automatically;
  manual check: `python Scripts/_verify_pdf_fenced_code.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf`
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

---

## 4. Study prose style — scholarly essay, not AI scaffold *(always applies)*

Applies to every topical study under `Studies/` except `Studies/README.md`.
References: [The-Ontology-of-Coexistence.md](Studies/The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.md) (ontology
exposition, open problems); [Why-Humans-Are-Not-Just-Material.md](Studies/Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.md)
(comparative anthropology, critique closings);
[Knowledge-Knower-And-Known.md](Studies/Knowledge-Knower-And-Known/Knowledge-Knower-And-Known.md) (epistemology,
tradition comparison); [Human-Behavior-And-Society.md](Studies/Human-Behavior-And-Society/Human-Behavior-And-Society.md)
(social philosophy, critique closings). Cursor mirror:
`.cursor/rules/study-prose-style.mdc`.

### Voice

Write exposition (typically §1–§4) as **continuous scholarly essay**. Tradition
sections open with multi-sentence prose that states the position (*Madhyasth
Darshan holds…*, *Advaita Vedanta holds…*, *Mainstream science answers…*) —
not `**The claim in one sentence:**`. Use `### N.M Descriptive title`
subsections for argument steps — not `**Step N —**`, `**N. Bold title.**`, or
`#### Argument N:` roadmaps. Comparison may use tables in a dedicated section
(typically §4–§5); do not label the table `### Comparative Matrix`. Critical
review (typically §5–§6) uses `### N.1 Tradition — descriptive subtitle` with
`**Strengths.**` and `**Weaknesses.**` bullet lists; end each tradition's
review with a plain closing sentence naming the tradition, not `**Verdict:**`
or `### Critical assessment`. Cross-reference with `§2.3`, not `Section 2`. Do
not use `---` horizontal rules between sections within the study body.

### Avoid

- Reader guides: `## How to read this study` and tag-legend blocks
- Bracket meta-tags: `[Open]`, `[Interpretation]`, `[Text]`
- Outline scaffolding: `**The claim in one sentence:**`, `**Step N —**` or
  `**N. Bold title.**` numbered roadmaps, `#### Argument N:` labels, logical-
  structure / step-recap tables in exposition, `In short:` recap labels
- Conclusion labels: `**Verdict:**`, `## Critical conclusion`, `###
  Critical assessment` — state the conclusion as plain prose
- Epistemic qualifiers and hedges: `honestly`, `honest caveat`, `The honest
  bottom line`, `On a charitable reading`, `A charitable reading` — state the
  point directly (*What science leaves open*; *Gyan here names…*)
- Distancing fillers: `According to this darshan` (when stating the darshan's
  own position), `Therefore, the most balanced reading is:` before a closing
  blockquote — name the tradition or state the conclusion directly
- Elimination filters: bold `**Not constitution.**` / `**Proposed reading:**`
  headers — weave rejections into prose
- Document signposting: `primary reference`, `prepares its rows`, `not
  decoration`, `keep in view`, `one-sentence preview`, subtitle lines under
  the `#` title (e.g. `## A critical writeup based on…`)
- References boilerplate: section preamble explaining how citations work;
  numbered `## N. References` — use `## References`; per-entry `Linked
  externally; not stored locally` (the link shows this)
- Formulaic bridges: `Having examined…`, `To map these divergent models…`

### Use instead

- Plain commitments: *Madhyasth Darshan holds…*, *This paper adopts…*,
  *Advaita Vedanta holds…* — for a contested interpretive fork only, *One
  reading is…* / *The texts take…* (not `On a charitable reading`)
- Unsettled points in prose where they arise, collected in an **Open problems**
  section without bracket labels
- Caveats stated directly, without labeling them `honest` or `frank`
- Content-first transitions: *Sentience is the next threshold…*
- Cross-refs only for argument (`§6.2`, `§3.3`), not for cataloguing the outline
- One running English term per source concept in analytical prose (glossary +
  Editorial Notes); block quotes keep translation wording
- **References:** `## References` then tradition subsections — no preamble;
  optional `### Related studies in this collection`; `**TAG** —` author, linked
  title, `Cited:`; local `../References/...` or external URL in the link; no
  `Linked externally; not stored locally`

### Check before finishing

- [ ] No `## How to read this study` or tag legend
- [ ] No `[Open]` / `[Interpretation]` / `[Text]` in the study `.md`
- [ ] No `**The claim in one sentence:**`, `**Step N —**`, `**N. Bold title.**`,
  `#### Argument N:`, or `**Verdict:**`
- [ ] No `honestly` / `honest caveat` / `The honest bottom line` / `On a
  charitable reading` / `A charitable reading` qualifiers
- [ ] No `**Not …**` rejection headers in exposition
- [ ] No `### Critical assessment`, `## Critical conclusion`, or `---` section
  dividers in the body
- [ ] No navigation-only meta-sentences or `### Comparative Matrix` labels
- [ ] Comparison recaps not duplicated outside the comparison section
- [ ] Cross-refs use `§`, not `Section`
- [ ] References: `## References` (unnumbered), no section preamble, no
  external-storage notes on entries

---

## 5. Standpoint and scope — topical studies *(always applies)*

Every **topical** study (`Studies/<Slug>/<Slug>.md`, not `README.md`, not Formal
Studies) includes `## Standpoint and scope` after the opening intro and before
the glossary or first major section.

Canonical text: [The-Ontology-of-Coexistence.md](Studies/The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.md). Cursor
mirror: `.cursor/rules/study-standpoint-scope.mdc`.

### Must establish

1. Author standpoint: scientist/technologist with graduate physics and mathematics.
2. Honest starting point: matter-first science acknowledged; hard problem, self,
   and value not treated as settled for materialism.
3. Method: read primary MD texts; state the darshan; compare in parallel with
   **physics and natural sciences**, **Advaita Vedanta**, and **modern Western
   philosophy** (tailor parenthetical to topic).
4. Physics/math are **one leg** of comparison, not the only one.
5. Aim: rigorous comparative understanding — not persuasion or devotional
   endorsement.
6. Series note: clear checkable prose first; formal math may follow later; this
   study does not require it.

### Form

Four short essay paragraphs (see §4). The intro above names this study's
particular questions and partners; Standpoint and scope states the **shared**
epistemic frame. Do not repeat the main question or preview the outline.

### Check before finishing

- [ ] Section present in the correct place
- [ ] All six points covered
- [ ] No missionary tone; materialism not treated as proven

---

## 6. Reference checks when citations change *(applies when adding or editing study references or References/ files)*

Whenever a study **bibliography** or any **`../References/...` link** changes, or any
file under `References/` is added, replaced, or removed, run the full reference check
suite before you finish the task or open a PR.

### Mandatory workflow

From repo root:

```powershell
python Scripts/_check_references.py
```

While editing a single study, you may scope checks until the full repo is ready:

```powershell
python Scripts/_check_references.py --study <Slug>
```

Use `--skip-pdf` only while drafting before PDF regeneration; **remove `--skip-pdf`
before finishing** if bibliography links changed.

The check suite (`Scripts/_check_references.py`) verifies:

1. **`## References` entries** — local paths exist and are usable PDF/HTML (not empty,
   not HTML saved as `.pdf`)
2. **All `../References/` links** in the study markdown (body and bibliography)
3. **All mirror files under `References/`** — valid on a full-repo run
4. **Study PDF embedded links** — no `file://` links; published-site links target
   usable local files

Supporting scripts: `_audit_references.py` (bibliography-only), `_download_references.py`
(mirrors), `_quote_tool.py verify` (blockquotes against local PDFs).

Agent skill: [check-references](.agents/skills/check-references/SKILL.md). Download
workflow: [download-references](.agents/skills/download-references/SKILL.md).

### When adding a new local mirror

1. Confirm redistribution rights; add entry to `Scripts/_reference_downloads.py`
2. `python Scripts/_download_references.py --tag "<Tag>"`
3. Point the study entry at `../References/...`; update `References/README.md`,
   `MANIFEST.md`, and `NOT-DOWNLOADED.md` as appropriate
4. Run `python Scripts/_check_references.py` (must exit 0)
5. Regenerate affected study PDFs; re-run checks **without** `--skip-pdf`
6. Refresh `**Edited on:**` and catalogs if study `.md` references changed (§1)

### When a local mirror cannot be stored

Link the external DOI or publisher URL in the study; add or keep a row in
`References/NOT-DOWNLOADED.md`. **Do not** commit empty files or HTML-as-PDF placeholders
under `References/`.

### Completion check

- [ ] `python Scripts/_check_references.py` exits 0
- [ ] No `file://` reference links in regenerated study PDFs
- [ ] `References/README.md`, `MANIFEST.md`, and `NOT-DOWNLOADED.md` agree on local vs external
- [ ] Study PDFs regenerated when bibliography links changed

# AGENTS.md

This file carries the standing instructions for AI agents working in this repo.
It is the **source of truth** for ZCode, OpenCode, and other agents that read
`AGENTS.md` at the repository root.

**Cursor** loads the same content through `.cursor/rules/*.mdc` mirrors (one file
per section below). **OpenCode / ZCode** loads `AGENTS.md` automatically and also reads
`.cursor/rules/*.mdc` via `opencode.json` → `instructions`.

**After editing `AGENTS.md` (§1–§9) or any `.agents/skills/**/SKILL.md`**, run sync before
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

Available skills: `manage-studies`, `add-study`, `remove-study`, `rename-study`,
`set-study-status`, `download-references`, `check-references`, `regenerate-study-pdf`,
`update-study-presentation`, `update-presenters-companion`, `refine-studies-index`.

| Section | Topic | Cursor mirror |
|---------|--------|---------------|
| *(meta)* | Agent rules & skills sync | `agent-rules-sync.mdc` |
| §1 | Edited on, catalogs, PDF timestamps | `study-edited-on.mdc` |
| §2 | `Studies/index.html` ↔ `README.md` sync | `studies-index-readme-sync.mdc` |
| §3 | Markdown → PDF pipeline | `md-to-pdf.mdc` |
| §4 | Study prose style | `study-prose-style.mdc` |
| §5 | Standpoint and scope | `study-standpoint-scope.mdc` |
| §6 | Reference checks when citations change | `study-references-check.mdc` |
| §7 | Study submission process: branches, PR labels, templates | `study-submission-process.mdc` |
| §8 | Line endings: LF everywhere | `line-endings.mdc` |
| §9 | Windows shell: PowerShell conventions | `powershell-terminal.mdc` |

There are nine rule sections below. The first, fourth, fifth, and sixth apply when
their stated conditions are met; §1 also applies to every topical study edit; §7 always
applies to any change under `Studies/`; §8 and §9 always apply (line endings and the
Windows/PowerShell shell).

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

- **Topical Studies catalog** — the data between the `<!-- studies-catalog -->`
  and `<!-- /studies-catalog -->` markers in `Studies/README.md`, and the matching
  `Studies/catalog-topical.json` file: same studies, same order, same titles,
  categories, descriptions, and status values.
  - **`Studies/catalog-topical.json`** (and `catalog-formal.json`, `catalog-applied.json`)
    — minified JSON arrays written by `Scripts/_study_catalog.py`; do not hand-edit.
    The studies landing page fetches these files at runtime.
  - **`Studies/README.md`** — markdown table rows (same marker names).
  Status is `ongoing` / `Ongoing` when no document is uploaded yet (no PDF),
  `draft` / `Draft<br>Last updated on: <date>, <time> IST` once a PDF exists but is
  not finalized, and `released` / `Released<br>Last updated on: <date>, <time> IST`
  only when a study is explicitly released.
  **When a study is edited**, the `Last updated on` date/time in both catalogs
  must match that study's `**Edited on:**` field in its `.md` file exactly
  (abbreviated month in catalogs: `Jun`; full month in `.md`: `June`). See
  [§1 Keep "Edited on" current](#1-keep-edited-on-current-in-studies-always-applies)
  for the mandatory workflow.
- **In-progress studies** — `status: "ongoing"` in catalog JSON; italic `*title*`
  with `<!-- slug: ... -->` in README; no PDF link.
- **Formal Studies catalog** — same documents, focus, and descriptions; JSON in
  `Studies/catalog-formal.json`, markdown table in README.
- **Applied Studies catalog** — papers under `Applications/` that instantiate the
  formal template in concrete domains; JSON in `Studies/catalog-applied.json`,
  markdown table in README. PDF links use
  `../Applications/<Slug>/<Slug>.pdf` from the studies page.
- **Shared prose** — the lead intro, **How we work**, **Contribute**,
  and **About us** (including license) should carry the same wording.

### Intentional differences (do NOT force these to match)

- **`Studies/index.html`** — card-grid catalog with search, filters, and sort
  (client-side JavaScript); hero stats and layout are site-only.
- **`Studies/README.md`** — markdown tables for GitHub rendering; no card UI or
  filters.

Both files end with **Contribute** and **About us** after the study catalogs;
wording should stay aligned.

### Building the index.html landing page shell

Catalog **data** (JSON + README tables) is updated by `Scripts/_study_catalog.py`
via `write_studies_catalog` and study lifecycle scripts (`_add_study.py`,
`_remove_study.py`, `_set_study_status.py`).

The **HTML/CSS/JS shell** — hero, card catalog UI, filters, sections, scroll-spy —
lives in `Scripts/_build_studies_index.py` as `INDEX_TEMPLATE`. Do not edit
`Studies/index.html` layout or styles in isolation.

Agent skill: [refine-studies-index](.agents/skills/refine-studies-index/SKILL.md).

When changing the landing page UI:

1. Edit `INDEX_TEMPLATE` in `Scripts/_build_studies_index.py`.
2. Regenerate (preserves existing catalog JSON):

   ```powershell
   python Scripts/_build_studies_index.py
   ```

3. Verify catalog data and shell match:

   ```powershell
   python Scripts/_verify_studies_index.py
   ```

CI runs `_verify_studies_index.py` on pull requests that touch the catalog or
index build scripts (`.github/workflows/studies-index-check.yml`). Labeled study
PRs also verify after regenerating artifacts (`Scripts/_ci_study_pr.py`).

### How to verify

After editing catalog **data** or the index **shell**, from repo root:

```powershell
python Scripts/_verify_studies_index.py
```

This checks JSON ↔ README sync; that `Studies/index.html` matches
`INDEX_TEMPLATE` (catalog blocks excluded); that the inlined catalog bootstrap in
`Studies/index.html` matches the `catalog-*.json` fetched at runtime, so first
paint and rehydration cannot disagree; and that no `ongoing` row carries a `pdf`
or `html` link. Study lifecycle scripts call `write_studies_catalog`, which
updates both catalog files together. If you add or remove a study, also update
`References/README.md` and `References/MANIFEST.md`.

Regenerating with no content change must produce no diff. If
`python Scripts/_build_studies_index.py` rewrites files on a clean tree, that is
a generator bug, not something to commit.

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

`npm install` in `Scripts/` installs **Puppeteer**, **pdf-lib**, **mermaid** (for
` ```mermaid ` diagrams in studies), and **katex** (for `$...$` / `$$...$$` math). CI runs
`npm ci` in `Scripts/` automatically.

### Regenerate one study

```powershell
python Scripts/_regenerate_pdf.py <Name>
```

Reads **Status:** from the markdown and applies the Draft watermark when appropriate.

### Internal pipeline (batch or debugging)

`_regenerate_pdf.py` runs this pipeline:

0. **`Scripts/_verify_study_svgs.py`** — before conversion, fails if any `![…](*.svg)`
   referenced from the study is missing, not valid UTF-8, or malformed XML.
1. **`Scripts/_convert_to_pdf.py`** — markdown → styled HTML (same basename, `.html`),
   with web navigation chrome and in-browser Mermaid when applicable.
2. **`Scripts/_html_to_pdf.js`** — loads Mermaid from `Scripts/node_modules`, renders
   `.mermaid` divs to SVG, then HTML → PDF via Puppeteer (footer, A4 margins).
3. **`Scripts/_pdf_metadata.py`** — pins `/CreationDate` and `/ModDate` from the study's
   `**Edited on:**` line so the output is reproducible.
4. **`Scripts/_verify_pdf_diagrams.py`** — after PDF generation, fails if markdown
   contains Mermaid but raw diagram syntax (e.g. `flowchart TD`) still appears in the PDF.
5. **`Scripts/_verify_pdf_fenced_code.py`** — fails if fenced ` ```text ` / code-block
   content is clipped in the PDF (e.g. `[compound]` truncated to `[c`).
6. **`Scripts/_verify_pdf_outline.py`** — fails if the PDF has no document outline
   (sidebar bookmarks) when the markdown has two or more `##` headings.

### Reproducible output, and when CI rebuilds

Re-running the pipeline on unchanged markdown produces a **byte-identical** PDF.
Chrome and pdf-lib both stamp wall-clock `/CreationDate` and `/ModDate`, so before
this was pinned every run emitted a different file and CI pushed a fresh
multi-megabyte blob on every commit to every study PR. Never reintroduce a
wall-clock timestamp into a generated artifact.

Reproducibility is scoped to a fixed Chrome and Node toolchain: a Chrome upgrade
legitimately changes glyph rendering, so the first regeneration after one will
show a real diff.

On a `study-update` PR, CI rebuilds the study PDF only when something that affects
it changed — the study markdown, a figure inside that study's own directory, the
PDF pipeline itself, or a missing PDF. A PR that touches only companion files (a
deck, research notes, figures the study does not embed) **skips** regeneration and
logs why. `Scripts/_ci_study_pr.py` holds that rule as `pdf_regeneration_reason()`;
`Scripts/_test_ci_study_pr.py` covers every branch of it.

Regenerate all studies:

```powershell
$studies = Get-ChildItem Studies -Directory
foreach ($s in $studies) {
  python Scripts/_regenerate_pdf.py $s.Name
}
```

Manual single-study steps (only if needed):

```powershell
python Scripts/_verify_study_svgs.py Studies/<Slug>/<Slug>.md
python Scripts/_convert_to_pdf.py Studies/<Slug>/<Slug>.md
node Scripts/_html_to_pdf.js Studies/<Slug>/<Slug>.html Draft
python Scripts/_verify_pdf_diagrams.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf
python Scripts/_verify_pdf_fenced_code.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf
python Scripts/_verify_pdf_outline.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf
```

### Study SVG figures

Static diagrams live as `Studies/<Slug>/*.svg` and are referenced from the study
markdown with `![alt text](figure.svg)`. They are embedded in HTML/PDF through
Chromium; the file must parse as valid XML.

**Encoding and characters**

- Save every study SVG as **UTF-8** (matching `<?xml encoding="UTF-8"?>`).
- In SVG `<text>` nodes, use **numeric XML entities** for special characters —
  do not rely on editor defaults that may write Windows-1252 bytes:
  - § → `&#167;`
  - · → `&#183;`
  - — → `&#8212;`
  - → → `&#8594;`
- A UTF-8-declared file that contains raw `0xA7` / `0xB7` bytes (Latin-1 § or ·)
  is **invalid**, breaks XML parsing, and produces a broken or blank figure in the PDF.
  This has recurred when section references (e.g. `§1.7 · §1.10.1`) were pasted into
  diagram footers.

**Verification**

- `_verify_study_svgs.py` runs automatically at the start of `_regenerate_pdf.py`.
- Run manually after editing any study SVG:

```powershell
python Scripts/_verify_study_svgs.py Studies/<Slug>/<Slug>.md
python Scripts/_verify_study_svgs.py
```

The second form validates SVG figures for all studies.

- **`Draft`** argument to `_html_to_pdf.js` — required for **Draft** studies. Omit for **Released**.
- **Keep the published `.html`** beside each study `.pdf` — the Studies index **Read**
  links open HTML; the download control fetches the PDF. Toolbar chrome is hidden in
  print/PDF output via `@media print` CSS.

### What the scripts provide (do not reimplement)

- Study typography, tables, blockquotes, and print CSS — `_convert_to_pdf.py`
- **Fully justified body paragraphs** — all `<p>` elements use `text-align: justify`
  (with `text-justify: inter-word` and `hyphens: auto`) in screen and print CSS;
  list items and table cells remain left-aligned — `_convert_to_pdf.py`
- **Embedded study figures** — PNG (or other raster) images and local **SVG** figures
  referenced from the study `.md` render in HTML/PDF with responsive width —
  `_convert_to_pdf.py`; SVG sources validated by `_verify_study_svgs.py` before conversion
- **Mermaid flowcharts and diagrams** — fenced ` ```mermaid ` blocks become rendered SVG
  in the PDF via `_convert_to_pdf.py` + `_html_to_pdf.js`; verified by
  `_verify_pdf_diagrams.py` after each regeneration
- **Inline and display LaTeX math** — `$...$` and `$$...$$` in study markdown are rendered
  with KaTeX in `_convert_to_pdf.py` (`_render_katex_math.js`) before glossary tooltips run;
  KaTeX CSS (with absolute font paths) is embedded in the HTML for PDF output
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
- **PDF sidebar bookmarks** — document outline from `h1`–`h3` via `outline: true` in
  `_html_to_pdf.js`; verified by `_verify_pdf_outline.py`
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
- Confirm the companion HTML path is `Studies/<Slug>/<Slug>.html` (or
  `Applications/<Slug>/<Slug>.html` for applied studies).
- If the study uses ` ```mermaid ` blocks, confirm the PDF shows diagrams (not raw
  `flowchart TD` source). Regeneration runs `_verify_pdf_diagrams.py` automatically;
  manual check: `python Scripts/_verify_pdf_diagrams.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf`
- If the study uses long ` ```text ` spec blocks, confirm bracket tags and line tails
  are intact. Regeneration runs `_verify_pdf_fenced_code.py` automatically;
  manual check: `python Scripts/_verify_pdf_fenced_code.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf`
- Confirm the PDF has sidebar bookmarks when the study has multiple sections.
  Regeneration runs `_verify_pdf_outline.py` automatically;
  manual check: `python Scripts/_verify_pdf_outline.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf`
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
- Insert `---` (horizontal rule) lines between sections or headings in study markdown — `---` translates to HTML `<hr>` elements which render as unwanted full-width separator lines across the page in generated PDFs.

### PDF → markdown (maintainers only)

Contributors submit markdown; PDF is always a **generated** artifact in CI. When a
contributor provides only a PDF, maintainers run `Scripts/_pdf_to_study_md.py` or
`Scripts/_add_study.py … --convert` on a feature branch, **review and fix** the
converted `.md` (headings, tables, citations, Standpoint and scope, References), then
regenerate the PDF with `_regenerate_pdf.py` before opening a study PR. Diagrams,
math, and glossary tooltips are not recovered from PDF — re-add them in markdown.
Scanned or image-only PDFs fail fast; do not commit placeholder extractions.

### Companion deck PDFs — a separate pipeline

`_regenerate_pdf.py` does **not** produce deck PDFs. A study folder may hold one or
more teaching decks; each `<Deck>.pptx` is hand-built and is the source of truth
(there is no slides-YAML generation workflow). A deck with a Presenter's Companion
yields three PDFs, which are **not interchangeable**:

| PDF | Contains | Audience |
|-----|----------|----------|
| `<Deck>.pdf` | Slides only | Projecting; the filename `Studies/index.html` links as the presentation PDF |
| `<Deck>-notes.pdf` | Slide plus that slide's read-aloud script, one page per slide | The presenter, while delivering |
| `Presenters-Companion-<Name>.pdf` | Script **plus** primary-text background and Q&A | Pre-session study |

Regenerate in this order whenever the deck changes at all — including notes-only and
reorder-only edits, since slide images, numbering and scripts all live in the notes PDF:

```powershell
python Scripts/_pptx_to_pdf.py Studies/<Slug>/<Deck>.pptx
python Scripts/_build_deck_notes_pdf.py Studies/<Slug>/<Deck>.pptx
```

The second command takes its slide images from `<Deck>.pdf`, so it must run after the
first. Both accept `--study <Slug>`, but that form resolves only when the folder holds
exactly one `.pptx`; otherwise pass `--deck <file>` or a full path.

Read-aloud scripts flow one way: `Presenters-Companion-<Name>.md` (source of truth) →
`.notes.json` → `Scripts/_sync_pptx_speaker_notes.py` → the `.pptx` notes pane →
`<Deck>-notes.pdf`. Edit the markdown, never the notes pane directly. Rebuild the
companion DOCX/PDF with `Scripts/_build_presenters_companion.py`.

Keep `<Deck>.pdf` slides-only. Its filename is referenced from
`Scripts/_build_studies_index.py` and the generated `Studies/index.html`
(`data-presentation-pdf`, `data-study-link`), so renaming it means editing the
generator and the generated index together. Never write the notes PDF over that path.

Deck and companion edits are companion-only changes: they use the `study-update` label
but do **not** refresh the study's `**Edited on:**` or catalog timestamps (§1, §7).

---

## 4. Study prose style — scholarly essay, not AI scaffold *(always applies)*

Applies to every topical study under `Studies/` except `Studies/README.md`.
References: [The-Ontology-of-Coexistence.md](Studies/The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.md) (ontology
exposition, open problems); [Why-Humans-Are-Not-Just-Material.md](Studies/Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.md)
(comparative anthropology, critique closings);
[The-Epistemology-of-Coexistence.md](Studies/The-Epistemology-of-Coexistence/The-Epistemology-of-Coexistence.md) (epistemology,
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

### Source attribution in exposition

Exposition states the darshan's own positions in continuous prose. Do **not** make
a source sigil the grammatical subject of an expository sentence — `MVD
describes…`, `KD says…`, `SB extends…`, `JV defines…`, `*Manav Karm Darshan*
gives the most direct account…` — and do not use source possessives for doctrine
(`MVD's account`, `in KD's view`, `KD's linked triads`). The reader should meet
the philosophy, not the study's familiarity with the books.

Attribution stays in the parenthetical citation and in the `## References` entry.
Parentheticals are kept — they are ordinary scholarly apparatus, not
text-as-speaker — and each cited page in a References entry carries the section
that uses it: `the sequence from knowledge through law, regulation, and balance
(p. 174; §1.4)`. Naming **Shri A. Nagraj** as author is correct where the point
is his (`Nagraj's founding questions ask…`); naming a book as a speaker is not.

### Textual variants and interpretive choices

Exposition presents what the texts establish, not the study's reading of them.
Keep the following out of the exposition sections:

- Enumeration reconciliation: `the three-content formulation… the four-content
  formulation`, `the two enumerations answer different questions`, `these
  formulations are not one mechanical ladder`
- Cross-text variant notes: `KD sometimes renders…`, `Elsewhere MVD says…`,
  `describes the same ten a second way`, `The common point is…`
- Meta-commentary on the sources: `the source therefore supports…`, `a
  source-faithful exposition can…`, `performs argumentative work in the darshan`
- Defensive clarification of what a term is *not* (`not a fourth *eshana*`, `not
  nine independent activities`, `more precise than "five *samvedanas*"`)

State the chosen content positively in the exposition and record the choice in
`## Editorial Notes` (`### <topic>` subsections, placed after the glossary and
before `## References`). **Never assert a harmonisation the sources do not
state** — if one passage lists four constituents and another three, present the
content and let the Editorial Note carry the enumeration; do not write that one
of them is "not a separate fourth content."

Comparison with other traditions belongs in the comparison sections (typically
§§2–5). Criticism, contestable inferences, testability, and open problems belong
in critical review and open problems (typically §§6–7), cross-referenced from the
exposition with `§6.1` or `§7.4` rather than argued in place.

### Block quotes

Quote the primary text for a section's **most important point**, not for each
claim it supports — a block quote per paragraph breaks the argument's flow, and
a point already stated in the sentence before it does not need quoting. Ordinary
support is carried by prose plus a parenthetical citation. Verify what remains:
`python Scripts/_quote_tool.py verify --study <Slug>`.

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
- Source-as-speaker attribution: `MVD says`, `KD describes`, `SB extends`,
  `MVD's account`, `in KD's view` — state the position, cite in parentheses
- Enumeration reconciliation, cross-text variant notes, and meta-commentary on
  the sources inside exposition — move them to `## Editorial Notes`
- Elimination filters: bold `**Not constitution.**` / `**Proposed reading:**`
  headers — weave rejections into prose
- Document signposting: `primary reference`, `prepares its rows`, `not
  decoration`, `keep in view`, `one-sentence preview`, subtitle lines under
  the `#` title (e.g. `## A critical writeup based on…`)
- References boilerplate: section preamble explaining how citations work;
  numbered `## N. References` — use `## References`; per-entry `Linked
  externally; not stored locally` (the link shows this)
- Formulaic bridges: `Having examined…`, `To map these divergent models…`
- Horizontal divider lines (`---`): Do not insert `---` lines between sections, pillars, or headings in study markdown — `---` translates to HTML `<hr>` elements which render as unwanted full-width separator lines across pages in the generated PDF.

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
- Doctrine stated in the darshan's voice with the page in parentheses: *Complete
  knowledge comprises… (KD §3.5, p. 69)* — not *KD lists four contents of
  complete knowledge*
- **References:** `## References` then tradition subsections — no preamble;
  optional `### Related studies in this collection`; `**TAG** —` author, linked
  title, `Cited:` with a `§`-tag on each cited page or range so every section's
  sources are recoverable from the entry; local `../References/...` or external
  URL in the link; no `Linked externally; not stored locally`

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
- [ ] No source sigil as the subject of an expository sentence (`MVD says`, `KD
  describes`, `SB extends`) and no source possessives for doctrine (`MVD's
  account`, `in KD's view`)
- [ ] No enumeration reconciliation, cross-text variant notes, or
  meta-commentary on the sources in exposition — recorded in
  `## Editorial Notes` instead
- [ ] No harmonisation asserted that the sources do not state
- [ ] Comparison confined to the comparison sections and criticism to critical
  review / open problems, not argued inside the exposition
- [ ] Block quotes reserved for a section's most important point;
  `python Scripts/_quote_tool.py verify --study <Slug>` passes
- [ ] References: `## References` (unnumbered), no section preamble, no
  external-storage notes on entries, `§`-tag on each cited page or range

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

---

## 7. Study submission process — branches, PR labels, and templates *(always applies)*

Applies to any change under `Studies/` (adding, editing, or changing the status of a study).
Human contributors follow the Web Submission Portal flow in [CONTRIBUTING.md](CONTRIBUTING.md).
Agents and other direct-repo contributors must follow the same underlying shape as a plain git
workflow: **never commit a `Studies/` change directly to the default branch.** Every study
addition, edit, or status change lands through a pull request that CI
(`.github/workflows/study-pr.yml` → `Scripts/_ci_study_pr.py`) can process.

### Mandatory workflow

1. **Create a feature branch** before touching any file under `Studies/`. Do not commit study
   changes on `master`/`main`.
2. **Single or multi-study pull requests supported** — `Scripts/_ci_study_pr.py` automatically resolves and processes all changed study slugs in the PR diff (or reads the primary `Study slug:` field from the PR body). When a PR touches multiple studies (e.g. cross-study terminology updates, shared reference updates, or multi-study reviews), CI validates timestamp sync, rebuilds PDFs, and runs reference checks for every changed study.
3. **Run local verification before pushing** — the same checks CI runs, so the PR is expected to
   pass on first push:
   - `python Scripts/_quote_tool.py verify --study <Slug>` if you quoted a local source
   - `python Scripts/_check_references.py --study <Slug>` (drop `--study` if `References/` itself
     changed)
   - `python Scripts/_regenerate_pdf.py <Slug>` (regenerates PDF/HTML and runs the SVG/diagram/
     fenced-code/outline verifiers)
   - `python Scripts/_verify_studies_index.py` if a catalog or the index shell changed
4. **Push the branch and open a pull request** using the matching template in
   [.github/PULL_REQUEST_TEMPLATE/](.github/PULL_REQUEST_TEMPLATE/) (or the chooser
   [.github/pull_request_template.md](.github/pull_request_template.md)) and apply
   **exactly one** label:

   | Change | Template | Label | Required PR body field |
   |--------|----------|-------|-------------------------|
   | Add a new study (after `proposal-approved`) | `new-study.md` | `new-study` | `Proposal issue: #N` and `Slug: <Slug>` |
   | Edit an existing study's content **or companion files** under that study folder (`.pptx`, research notes, SVGs, etc.) | `study-update.md` | `study-update` | `Study slug: <Slug>` |
   | Rename slug (directory + metadata) | `study-update.md` | `study-update` | `Study slug: <New-Slug>` (CI runs `_rename_study.py` when one slug is removed and another added) |
   | Change Draft ↔ Released | `status-change.md` | `status-change` | `Study slug: <Slug>` and `Target status: draft`/`released` |

   **Bare slug only.** Put `Study slug:`, `Slug:`, and `Target status:` each on its **own
   line**. The value must be the catalog directory name alone — e.g.
   `Study slug: The-Ontology-of-Coexistence`. Do **not** append parentheticals, em dashes,
   or other notes on that line (`Study slug: Foo (pptx only)` fails catalog lookup; put
   notes under Summary instead). CI strips common trailing notes as a backstop, but
   templates and agents must still write a bare slug.

   **When a study label is required.** Any change under `Studies/<Slug>/` or
   `Applications/<Slug>/` — including companion-only edits that do not touch the study
   `.md` — needs a study-labeled PR and the matching template. Companion-only PRs still
   set `Study slug: <Slug>`; mark Edited-on checklist items N/A in the PR body when the
   study markdown was not changed.

   A change that only touches non-study files (`Scripts/`, `AGENTS.md`, `.agents/skills/`,
   infra, etc.) is **not** a study PR — do not apply a study label to it, and it does not
   need a `Study slug:` field.
5. **Tick the template checklist** in the PR body before requesting review or merge (Edited on
   refreshed when the study `.md` changed, `References/MANIFEST.md` updated if citations
   changed, quote verification run when applicable). Prefer opening the specific template
   link rather than leaving the default chooser body as the PR description.

### Contributor PDFs (maintainers only)

The Web Submission Portal and CI expect `Studies/<Slug>/<Slug>.md` as source. When a
contributor hands off a PDF instead, maintainers convert on a feature branch with
`python Scripts/_pdf_to_study_md.py …` or `python Scripts/_add_study.py … --convert`,
manually review the output against AGENTS.md §4–§5, regenerate the PDF, then open the
normal labeled PR. PDF is never accepted as the canonical study source in the repository.

### Renaming a study slug

Renaming is a **`study-update`** PR, not a silent directory move. When the diff removes one
`Studies/<Old>/` (or `Applications/<Old>/`) tree and adds one new slug, `_ci_study_pr.py`
invokes `Scripts/_rename_study.py --metadata-only` to sync `proposal-registry.json`,
`.proposal-meta.json`, and the linked GitHub proposal issue. The PR must set `Study slug: <New-Slug>`
and include registry/meta updates (or let CI write them on the branch).

Agent skill (full checklist, Start here, My Submissions):
[rename-study](.agents/skills/rename-study/SKILL.md).

For local/maintainer runs before opening the PR:

```powershell
python Scripts/_rename_study.py --from Old-Slug --to New-Slug --title "New display title"
```

Keep slugs at or under **60 characters**. The portal rejects longer slugs at proposal time.

### Why this matters

`Scripts/_ci_study_pr.py` re-derives the slug, re-syncs the catalog timestamp from the study's
`**Edited on:**`, regenerates the PDF, runs reference checks when the bibliography changed, and
verifies timestamp/catalog sync — all keyed to the PR's label and body field. Committing directly
to the default branch skips every one of those checks and is how catalogs, timestamps, and PDFs
drift out of sync with the source `.md`.

### Completion check

- [ ] Change is on a feature branch, not the default branch
- [ ] Exactly one of `new-study` / `study-update` / `status-change` will be applied to the PR
- [ ] PR body includes the field that label requires (`Study slug:`, `Proposal issue: #N`, or
  `Target status:`) — bare slug / status value only, no notes on that line
- [ ] One study slug per PR for `study-update` / `status-change` (open a second PR for a second
  slug)
- [ ] Local verification (`_quote_tool.py verify`, `_check_references.py`, `_regenerate_pdf.py`,
  `_verify_studies_index.py` as applicable) run and passing before push
- [ ] Non-study changes (Scripts/, rules, skills, infra) are not carrying a study label

---

## 8. Line endings — LF everywhere *(always applies)*

Every file in this repository uses **LF** (`\n`) line endings. `.gitattributes` at
the repo root (`* text=auto eol=lf`) normalizes all tracked text files to LF in git
and on checkout across platforms; binary types (`*.pdf`, `*.png`, fonts, Office
documents, archives) are marked `binary` and left untouched. `.vscode/settings.json`
sets `"files.eol": "\n"` so the editor writes LF at the source on every OS.

This exists because the repo previously had mixed endings and no `.gitattributes`,
so generated artifacts (study `*.html`, `catalog-*.json`, `Studies/index.html`,
companion HTML from PDF regeneration) churned between CRLF and LF depending on which
tool or OS last wrote them, producing large line-ending-only diffs.

### Rules

- Never introduce CRLF (`\r\n`) into tracked text files. Create and edit files with LF.
- Keep `.gitattributes` as the single source of EOL policy; do not add per-path
  overrides that reintroduce CRLF, and do not delete the `eol=lf` normalization.
- Scripts that write files (PDF/HTML pipeline, `_build_studies_index.py`, catalog
  writers) must emit LF; `.gitattributes` also normalizes on commit as a backstop.
- Do not hand-convert generated artifacts to CRLF to "fix" a diff — regenerate them
  with the repo scripts instead.

### Check

- `git add --renormalize .` produces no changes on an otherwise clean tree.
- `git diff --ignore-cr-at-eol` shows no files that differ only by line ending.
- New text files report `i/lf` under `git ls-files --eol`.

---

## 9. Windows shell — PowerShell conventions *(always applies)*

The development environment is **Windows with PowerShell**. All terminal commands must
use PowerShell syntax, never bash. The repo root path contains a space
(`e:\Madhyasth Darshan`), which makes quoting mandatory.

### Rules

- **Sequencing:** chain commands with `;`, or run them as separate calls. Do **not** use
  bash `&&` or `||` — the PowerShell here rejects `&&` as an invalid statement separator.
- **No bash heredocs.** For multi-line input (PR bodies, commit bodies), write a temp file
  and pass it (e.g. `gh pr create --body-file <file>`) or use a PowerShell here-string
  (`@" ... "@`); never `cat <<'EOF'`.
- **Quote paths that contain spaces** with double quotes:
  `python "Scripts/_regenerate_pdf.py"`, `cd "e:\Madhyasth Darshan"`.
- **Use PowerShell cmdlets and idioms**, not unix-only assumptions: `Get-ChildItem`,
  `Get-Content`, `Select-String`, `Measure-Object`, `$env:VAR`, `$LASTEXITCODE`.
  Prefer the editor's dedicated file and search tools over shelling out to read, edit, or
  search files.
- **Line endings:** author files as **LF** (§8). On Windows some generators still write
  CRLF into the working tree; `.gitattributes` (`* text=auto eol=lf`) normalizes on commit,
  so CRLF churn in `git status` is expected — stage only real content changes and let
  normalization handle EOL, rather than hand-converting files.

### Check

- No `&&`, `||`, or bash heredocs in commands issued this session.
- Paths containing spaces are wrapped in double quotes.

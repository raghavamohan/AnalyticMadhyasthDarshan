# Manav Sanchetnavadi Manovigyan - English translation workspace

This directory prepares a page-aligned working English translation of A. Nagraj's
*Manav Sanchetnavadi Manovigyan* (*मानव संचेतनावादी मनोविज्ञान*). It follows the
working method established in `../KD-Karm-Darshan-English/`, with the lessons from
KD made explicit before translation begins.

**Current status:** setup only. No English translation has been drafted or implied
by the files in this directory.

## Source and page map

The canonical Hindi source is
[`../MSM-manav-sanchetnavaadi-manovigyan.pdf`](../MSM-manav-sanchetnavaadi-manovigyan.pdf),
the official 2008 OCR edition registered under the `MSM` reference tag.

- Source SHA-256: `d71ff870a3fdaffd99cc0e3e4a3c52444c817b7f02c41f8b09ecd904a45cff87`
- PDF pages: 268
- PDF pp. 1-12: front matter; filenames use logical print keys 1-12
- PDF pp. 13-266: book body; printed pp. 1-254 (`printed = PDF - 12`)
- PDF p. 267: publisher back matter; logical print key 255
- PDF p. 268: blank/footer page; logical print key 256

The `print` field on the final two filenames is an alignment key, not a claim that
those pages display a printed number.

[`_page-images/`](_page-images/) contains one 150 dpi grayscale PNG for every PDF
page. The grayscale render retains the monochrome source detail without storing
redundant RGB channels. The name `p{pdf:03d}_print{logical:03d}.png` makes the source
location unambiguous even where front-matter numbering and body numbering overlap.
Images, not the OCR text layer, are authoritative for translation and review. The
OCR layer contains useful search hints but also visible recognition errors and
scanner artefacts.

## Workspace files

| File | Purpose |
| :--- | :--- |
| [`README.md`](README.md) | Translation method, gates, page map, and commands |
| [`MSM-Glossary-Additions.md`](MSM-Glossary-Additions.md) | MSM-specific terminology decisions and unresolved terms |
| [`MSM-Source-Image-Review-Ledger.md`](MSM-Source-Image-Review-Ledger.md) | Direct source-image review coverage and corrections |
| [`_page-images/`](_page-images/) | Page-by-page Hindi source renders |

The canonical `MSM-Manav-Sanchetnavadi-Manovigyan-English.md` and its generated
HTML/PDF do not exist yet. Create them only when the first reviewed translation
batch is ready; this avoids presenting an empty scaffold as a translation.

## Translation authority

Use this order when making a translation decision:

1. The Hindi visible in the corresponding `_page-images/` file controls the
   meaning, syntax, negation, sequence, agency, and enumerations.
2. `../MD-Mapping.xlsx` and Rakesh Gupta's published MVD, SB, and JV translations
   control established English terminology and recurring sentence patterns.
3. The KD working translation and `../KD-Karm-Darshan-English/KD-Glossary-Additions.md`
   are precedents only when the same Hindi expression is used in the same sense.
   A KD-specific contextual exception is not automatically an MSM standard.
4. Record every MSM-specific departure, ambiguity, or contextual distinction in
   `MSM-Glossary-Additions.md`. A proposed departure becomes settled only after
   explicit review; it must not silently rewrite the shared glossary.

Never translate from OCR output alone. It may be used to locate a page or generate
a search candidate, but every sentence and technical term must be checked against
the rendered source image.

## Page-aligned source format

When the translation source is created, keep source boundaries visible:

- Use `[PDF p. N - front matter]` for each front-matter page.
- Use `[p. N]` for each numbered body page.
- Use `[blank p. N]` when a source page is blank.
- Immediately follow each marker with an invisible source pointer such as
  `<!-- source: _page-images/p013_print001.png -->`.
- Do not combine or split page markers merely to improve English flow. Page
  alignment is part of the verification contract.
- Preserve headings, lists, tables, formulae, quotations, names, and closing
  formulae before doing a readability pass.

## Work plan

### Phase 0 - source preparation (complete)

- Pin the exact source edition and checksum.
- Establish PDF-to-printed-page mapping.
- Render and validate one source image per PDF page.
- Create terminology and source-review ledgers.

### Phase 1 - structural inventory

- Read the table of contents and all section-opening pages from images.
- Record the complete Hindi heading hierarchy and page ranges without translating
  the prose.
- Identify tables, diagrams, formulae, unusually dense pages, and apparent OCR or
  print defects that will require special handling.
- Select a representative pilot of 8-12 pages across front matter, ordinary prose,
  technical vocabulary, lists/tables, and the closing sections.

### Phase 2 - terminology pilot

- Translate only the approved pilot pages.
- Extract recurring technical terms and compare them with MD-Mapping, MVD, SB, JV,
  and same-sense KD usage.
- Record proposed MSM-specific choices and conflicts in the glossary additions.
- Review fidelity first; perform the English readability pass only after the Hindi
  meaning is settled.
- Obtain approval for terminology departures before scaling to the full book.

### Phase 3 - page batches

- Work in small, reviewable batches with explicit PDF and printed-page ranges.
- For each batch, check every sentence against its source image and update the
  source-image review ledger.
- Preserve logical sequence, negation, exclusivity, referents, and technical
  distinctions. Do not add explanatory claims to the translated body.
- Put necessary translator clarifications in notes, clearly distinguished from the
  author's text.
- Re-run the terminology guardrail after each accepted batch once that guardrail
  has been created from settled MSM decisions.

### Phase 4 - cross-corpus alignment

- Compare recurring terms and formulae against the published MVD/SB/JV English,
  not only against row-level glossary matches.
- Recheck every borrowed KD exception in its MSM context.
- Audit headings, page markers, omissions, duplicated passages, tables, names, and
  number sequences across the complete draft.

### Phase 5 - editorial pass

- Replace mechanical Hindi-to-English syntax only where the underlying logical
  relationships remain unchanged.
- Keep technical classifications precise even when their English is repetitive.
- Directly re-review representative high-density pages from every major section and
  record that coverage; do not imply a page received a second review when it did not.

### Phase 6 - generated outputs

- Generate HTML and English PDF from the canonical markdown with the repository's
  `_convert_to_pdf.py` and `_html_to_pdf.js` pipeline.
- Verify that the English PDF retains one output page per source page before making
  a bilingual interleaved edition. Do not force alignment by deleting or silently
  merging content.
- Build any Hindi-English interleaved PDF only after both inputs have the same page
  count and spot-check the first, transition, dense, and final pages.
- Continue to label all outputs as machine-assisted working translations, not
  published translations.

## Commands

Run from the repository root:

```powershell
# Re-render only missing MSM source images at 150 dpi
python Scripts/_msm_render_page_images.py

# Confirm source identity and the complete 268-image set
python Scripts/_msm_render_page_images.py --check

# Once a real translation source exists, generate its HTML and PDF
python Scripts/_convert_to_pdf.py "References/Madhyasth-Darshan/MSM-Manav-Sanchetnavadi-Manovigyan-English/MSM-Manav-Sanchetnavadi-Manovigyan-English.md"
node Scripts/_html_to_pdf.js "References/Madhyasth-Darshan/MSM-Manav-Sanchetnavadi-Manovigyan-English/MSM-Manav-Sanchetnavadi-Manovigyan-English.html"
```

If the Hindi source file changes, stop before rendering. Confirm the new edition,
page count, body offset, and checksum; then update the renderer and this document
together. Never use `--allow-source-mismatch` for committed page images.

## Completion gates for each future translation batch

- [ ] Every translated page has a page marker and matching source-image pointer.
- [ ] Hindi was checked from the image, not accepted from OCR alone.
- [ ] Logical sequence, negation, enumerations, and agency were verified.
- [ ] Established terminology follows MD-Mapping and published MVD/SB/JV usage.
- [ ] Same-sense KD precedents were checked contextually, not copied mechanically.
- [ ] New or disputed choices are recorded in `MSM-Glossary-Additions.md`.
- [ ] Directly reviewed pages and accepted corrections are recorded in the ledger.
- [ ] Readability edits occurred only after the fidelity pass.
- [ ] Generated files, once they exist, were rebuilt and visually spot-checked.

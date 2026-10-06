# Avartansheel Arthshastra - English translation workspace

This directory prepares a page-aligned working English translation of A. Nagraj's
*Avartansheel Arthshastra* (*आवर्तनशील अर्थशास्त्र*, cyclical economics). It
follows the working method established in `../KD-Karm-Darshan-English/` and the
setup already made for `../MSM-Manav-Sanchetnavadi-Manovigyan-English/`.

**Current status:** setup and chapter-level inventory only. No English translation
has been drafted or implied by the files in this directory. Any translation made
here will be a machine-assisted working translation, not a published translation;
verify against the Hindi original before quoting it in a publication.

Phase status and the next batch are tracked only in
[PENDING.md](../../../PENDING.md#references), under `REF-AA-TR`. The
[Prosperity Economics study plan](../../../docs/prosperity-economics-study-plan.md#8-sources)
explains why the study needs this translation and gates its first draft on a
complete first pass.

## Source and page map

The canonical Hindi source is
[`../AA-avartanshil-arthashastra.pdf`](../AA-avartanshil-arthashastra.pdf), the
official published-book download registered under the `AA` reference tag.

- Publisher: Jeevan Vidya Prakashan, Divyapath Sansthan, Amarkantak
- Printing: 14 January 2024; earlier editions 2001 and 2009
- ISBN: 978-81-956883-8-8
- Source SHA-256: `c80b2b6ef1223046d8191bafccda5ad3144f2bd362fb65e44957c0f424c7ca40`
- PDF pages: 164
- PDF pp. 1-10: front matter; filenames use logical print keys 1-10
- PDF pp. 11-159: book body; printed pp. 1-149 (`printed = PDF - 10`)
- PDF pp. 160-164: blank and publisher back matter; logical print keys 150-154

The `print` field on the five trailing filenames is an alignment key, not a claim
that those pages display a printed number.

[`_page-images/`](_page-images/) contains one 150 dpi grayscale PNG for every PDF
page, named `p{pdf:03d}_print{logical:03d}.png`. The name keeps the source location
unambiguous even where front-matter keys and body numbering overlap.

### Never translate or verify from the PDF's text layer

The upstream filename says "unicode", but every page is a scanned image with an OCR
text layer. That layer is useful for locating a passage and unreliable for wording.
Checked 6 October 2026 with PyMuPDF: the even-page running header reads
`केन्द्रित चिंतन` in the image but extracts as `केन्द्रित चितन` on all 74 even
body pages; the table of contents extracts printed pages 104, 110 and 122 as
`404`, `40` and `422`; and the imprint's ISBN and web addresses come out garbled.
The images, not the OCR text, are authoritative for translation and review.

## Workspace files

| File | Purpose |
| :--- | :--- |
| [`README.md`](README.md) | Translation method, page map, structural inventory, and commands |
| [`AA-Glossary-Additions.md`](AA-Glossary-Additions.md) | AA-specific terminology decisions, candidate economic terms, and unresolved terms |
| [`AA-Source-Image-Review-Ledger.md`](AA-Source-Image-Review-Ledger.md) | Direct source-image review coverage and corrections |
| [`_page-images/`](_page-images/) | Page-by-page Hindi source renders |

The canonical `AA-Avartansheel-Arthshastra-English.md` and its generated HTML/PDF
do not exist yet. Create them only when the first reviewed translation batch is
ready; this avoids presenting an empty scaffold as a translation.

## Structural inventory

Read from the page images on 6 October 2026. Every chapter opens at the top of its
page, and the printed table of contents (PDF p. 9) agrees with the chapter
openings.

| Part | Hindi heading | PDF pages | Printed pages |
| :--- | :--- | :--- | :--- |
| Title page | आवर्तनशील अर्थशास्त्र | 1 | - |
| Imprint and right-use policy (सदुपयोग नीति) | - | 2 | - |
| Preface | विकल्प | 3-7 | (i)-(v) |
| Blank | - | 8 | - |
| Table of contents | अनुक्रमणिका | 9 | - |
| Blank | - | 10 | - |
| Chapter 1 | अर्थ को पहचानने की शुरूआत क्रम से अर्थ की परिभाषा/मान्यता | 11-18 | 1-8 |
| Chapter 2 | आर्वतनशील अर्थशास्त्र : दार्शनिक आधार | 19-34 | 9-24 |
| Chapter 3 | आर्वतनशील अर्थशास्त्र : अवधारणा | 35-53 | 25-43 |
| Chapter 4 | आवर्तनशीलता - अनिवार्यता और उसका स्वरूप | 54-77 | 44-67 |
| Chapter 5 | उत्पादन और मूल्य | 78-105 | 68-95 |
| Chapter 6 | प्रमाण का आधार : मानव | 106-113 | 96-103 |
| Chapter 7 | जागृति और स्वतंत्रता | 114-119 | 104-109 |
| Chapter 8 | परिवार मूलक ग्राम स्वराज्य व्यवस्था का स्वरूप | 120-131 | 110-121 |
| Chapter 9 | परिवार मूलक स्वराज्य व्यवस्था योजना | 132-159 | 122-149 |
| Blank | - | 160 | 150 |
| Publisher's list of works (मूल ग्रंथ) | - | 161 | 151 |
| Publisher's list of compilations and contacts | - | 162 | 152 |
| Blank | - | 163-164 | 153-154 |

Printed p. 149 ends the book with the closing benediction
(*bhūmiḥ svargatām yātu ... nityam yātu śubhodayam*). Odd body pages carry the
running header `आवर्तनशील अर्थशास्त्र (अध्याय - N)`; even pages carry
`मध्यस्थ दर्शन सहअस्तित्ववाद (अस्तित्व मूलक मानव केन्द्रित चिंतन)`.

**Print defect.** The table of contents, the chapter 2 and chapter 3 headings, and
the prose of printed pp. 1 and 6 spell the title `आर्वतनशील` (confirmed in the
images; OCR search finds no other body page). The title page, running headers,
chapter 4 heading and the rest of the prose read `आवर्तनशील`. Translate both
spellings as the same title and note the misprint once rather than reproducing it.

**Pages needing special layout.** Found by a ruled-line scan of every page and
confirmed visually; prose pages carrying a short table may still be missed, so
record any further cases here when found.

| Printed page | PDF page | Content |
| :--- | :--- | :--- |
| 101 | 111 | Five-column table: ज्ञानावस्था के पाँच मानव (the five kinds of human in the knowledge order) |
| 109 | 119 | Stacked tier diagram: मानवीय संविधान का प्रारूप (draft of the humane constitution) |
| 112 | 122 | Circular diagram of the five dimensions of orderliness (शिक्षा-संस्कार, स्वास्थ्य-संयम, न्याय-सुरक्षा, उत्पादन-कार्य, विनिमय-कोष) around an inner pentagon, and a bracketed chart contrasting common aspirations (सामान्य आकांक्षा) with special aspirations (महत्वाकांक्षा) |
| 141 | 151 | Two-column table pairing established values (स्थापित मूल्य) with civic values (शिष्ट मूल्य) |

Chapters 8 and 9 are largely numbered schemes (committees, village services,
evaluation criteria). Keep their enumeration and nesting exactly as printed.

**Still to inventory.** The sub-heading hierarchy inside each chapter, which is
needed before the pilot is approved; see `REF-AA-TR` in PENDING.md.

## Translation authority

Use this order when making a translation decision:

1. The Hindi visible in the corresponding `_page-images/` file controls the
   meaning, syntax, negation, sequence, agency, and enumerations.
2. `../MD-Mapping.xlsx` and Rakesh Gupta's published MVD, SB, and JV translations
   control established English terminology and recurring sentence patterns. SB and
   JV discuss exchange, currency and cyclical economics directly and are the
   closest published precedents for AA's vocabulary.
3. The KD working translation and `../KD-Karm-Darshan-English/KD-Glossary-Additions.md`
   are precedents only when the same Hindi expression is used in the same sense.
   A KD-specific contextual exception is not automatically an AA standard.
4. Record every AA-specific departure, ambiguity, or contextual distinction in
   `AA-Glossary-Additions.md`. A proposed departure becomes settled only after
   explicit review by the author; it must not silently rewrite the shared glossary.

Two economic rules already follow from this hierarchy. श्रम is **effort** in
effort-motion-result, but **labour** in economic compounds (श्रम मूल्य =
**evaluation of labour**, श्रम विनिमय = **exchange of labour**), per MD-Mapping
and the KD glossary. And a bare MD-Mapping row is not enough where the economic
sense differs from the row's sense: मुद्रा is "gesture" in MD-Mapping but
"currency" in SB's economic passages. The glossary-additions file lists these
candidates for the pilot.

## Page-aligned source format

When the translation source is created, keep source boundaries visible:

- Use `[PDF p. N - front matter]` for each front-matter page.
- Use `[p. N]` for each numbered body page.
- Use `[blank p. N]` when a source page is blank.
- Immediately follow each marker with an invisible source pointer such as
  `<!-- source: _page-images/p011_print001.png -->`.
- Do not combine or split page markers merely to improve English flow. Page
  alignment is part of the verification contract.
- Preserve headings, lists, tables, diagrams, quotations, names, and closing
  formulae before doing a readability pass. Render diagram labels as a table or
  list that keeps their structure, with a translator's note naming the original
  layout.

## Work plan

The method follows KD's. Status for each phase lives in PENDING.md.

### Phase 0 - source preparation (complete)

- Pin the exact source edition and checksum.
- Establish the PDF-to-printed-page mapping.
- Render and validate one source image per PDF page.
- Create terminology and source-review ledgers.

### Phase 1 - structural inventory (chapter level recorded above)

- Read the table of contents and all section-opening pages from images.
- Record the complete Hindi heading hierarchy and page ranges without translating
  the prose.
- Identify tables, diagrams, unusually dense pages, and apparent OCR or print
  defects that will require special handling.
- Select a representative pilot of 8-12 pages across front matter, ordinary prose,
  technical vocabulary, lists/tables, and the closing sections.

Proposed pilot, for approval: PDF p. 3 (*vikalp* (i)) and printed pp. 1, 9, 25,
27, 44, 68, 91, 101, 109, 122 and 149. The set covers every chapter opening that
introduces a new topic, the core definitions of chapter 3, pages where OCR search
locates *vinimay-kosh*, *shram mulya*, currency and *labhonmad*, two
table/diagram pages, the opening of the chapter 9 scheme, and the closing page.
OCR was used only to find candidate pages; each must be read from its image.

### Phase 2 - terminology pilot

- Translate only the approved pilot pages.
- Extract recurring technical terms and compare them with MD-Mapping, MVD, SB, JV,
  and same-sense KD usage.
- Record proposed AA-specific choices and conflicts in the glossary additions.
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

### Phase 4 - cross-corpus alignment

- Compare recurring terms and formulae against the published MVD/SB/JV English,
  not only against row-level glossary matches.
- Recheck every borrowed KD exception in its AA context.
- Audit headings, page markers, omissions, duplicated passages, tables, names, and
  number sequences across the complete draft.

### Phase 5 - editorial pass

- Replace mechanical Hindi-to-English syntax only where the underlying logical
  relationships remain unchanged.
- Keep technical classifications precise even when their English is repetitive.
- Directly re-review representative high-density pages from every chapter and
  record that coverage; do not imply a page received a second review when it did
  not.

### Phase 6 - generated outputs

- Generate HTML and English PDF from the canonical markdown with the repository's
  `_convert_to_pdf.py` and `_html_to_pdf.js` pipeline.
- Verify that the English PDF retains one output page per source page before making
  a bilingual interleaved edition. Do not force alignment by deleting or silently
  merging content.
- Continue to label all outputs as machine-assisted working translations, not
  published translations.

## Commands

Run from the repository root:

```powershell
# Re-render only missing AA source images at 150 dpi
python Scripts/_aa_render_page_images.py

# Confirm source identity and the complete 164-image set
python Scripts/_aa_render_page_images.py --check

# Once a real translation source exists, generate its HTML and PDF
python Scripts/_convert_to_pdf.py "References/Madhyasth-Darshan/AA-Avartansheel-Arthshastra-English/AA-Avartansheel-Arthshastra-English.md"
node Scripts/_html_to_pdf.js "References/Madhyasth-Darshan/AA-Avartansheel-Arthshastra-English/AA-Avartansheel-Arthshastra-English.html"
```

If the Hindi source file changes, stop before rendering. Confirm the new edition,
page count, body offset, and checksum; then update the renderer and this document
together. Never use `--allow-source-mismatch` for committed page images.

## Rights

The imprint reserves all rights to Divyapath Sansthan. Its right-use policy
(सदुपयोग नीति) states that the book is published for universal good, without
commercial purpose, that copying for personal study is permitted, and that any
other use needs the Sansthan's written permission. The source is retained in Git
as an active-translation exception, like the KD and MSM sources, with rights status
`review-required` in `References/r2-artifacts.json`; see `REF-AA` in PENDING.md.

## Completion gates for each translation batch

- [ ] Every translated page has a page marker and matching source-image pointer.
- [ ] Hindi was checked from the image, not accepted from OCR alone.
- [ ] Logical sequence, negation, enumerations, and agency were verified.
- [ ] Established terminology follows MD-Mapping and published MVD/SB/JV usage.
- [ ] Same-sense KD precedents were checked contextually, not copied mechanically.
- [ ] New or disputed choices are recorded in `AA-Glossary-Additions.md`.
- [ ] Directly reviewed pages and accepted corrections are recorded in the ledger.
- [ ] Readability edits occurred only after the fidelity pass.
- [ ] Generated files, once they exist, were rebuilt and visually spot-checked.

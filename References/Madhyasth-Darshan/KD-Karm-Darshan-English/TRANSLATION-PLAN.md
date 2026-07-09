# Karm Darshan English Translation — Plan

Goal: a page-aligned Hindi–English PDF pair for side-by-side verification of *Manav Karm Darshan* (v5). All content lives in [`KD-Karm-Darshan-English.md`](KD-Karm-Darshan-English.md).

## Page-number convention

- **Printed page** = PDF page − 25 for body content (printed pp. 1–153 → PDF pp. 26–178).
- Front matter uses printed = PDF for PDF pages 1–25.
- Page images: `_page-images/p{pdf:03d}_print{printed:03d}.png` (render with `python Scripts/_kd_render_page_images.py`).

## Transition layout (printed pp. 50–54)

| Printed | PDF | Content |
|---|---|---|
| 50 | 75 | Blank |
| 51 | 76 | Chapter 3 title + five-theme outline |
| 52 | 77 | Sub-TOC sections 1–16 |
| 53 | 78 | Sub-TOC sections 17–18 |
| 54 | 79 | Section 3.1 begins |

Previously, printed pp. 51–52 were `[blank p. NN]` placeholders and section 3.1 started at printed p. 53, which misaligned every interleaved pair from chapter 3 onward.

## Remaining work

### Done (2026-07-09)

- [x] Translate printed pp. 51–53 (chapter 3 title page + detailed sub-TOC)
- [x] Renumber chapter 3 body markers (+1 after sub-TOC; final page stays p. 153)
- [x] Regenerate `KD-Karm-Darshan-English.pdf` (182 pages) and `KD-Karm-Darshan-Hindi-English.pdf` (364 pages)
- [x] Add helper scripts: `_kd_shift_page_markers.py`, `_kd_verify_page_markers.py`

### Ongoing — fine page alignment (chapter 3 body)

English prose length differs from Hindi, so section headings may sit ±1–2 printed pages from the sub-TOC start pages. Use `_page-images/` vs the regenerated English PDF to adjust paragraph splits at `[p. NN]` markers.

Priority checkpoints (sub-TOC start pages):

| Section | Hindi start | Verify marker / heading |
|---|---|---|
| 3.1 | 54 | PDF p. 79 |
| 3.2 | 57 | |
| 3.3 | 59 | |
| 3.8 | 83 | sanity check (content was aligned pre-shift) |
| 3.18 | 150–153 | closing benediction on p. 153 |

Run `python Scripts/_kd_verify_page_markers.py` for a section-boundary report.

### Optional

- Isolate printed p. 50 as a fully blank English PDF page (currently the title outline may share the break with `[blank p. 50]`); requires removing one page break elsewhere to keep 182 pages.

## Methodology

1. Render Hindi page images — `python Scripts/_kd_render_page_images.py`
2. Translate from images into `KD-Karm-Darshan-English.md` with `[p. NN]` / `[blank p. NN]` markers
3. Apply glossary conventions — see `KD-Glossary-Additions.md`
4. Rebuild glossary spreadsheet — `python Scripts/_kd_build_glossary_xlsx.py`
5. Regenerate PDFs (below)

## Regenerate PDFs

```powershell
python Scripts/_convert_to_pdf.py "References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Karm-Darshan-English.md"
node Scripts/_html_to_pdf.js "References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Karm-Darshan-English.html"
python Scripts/_kd_build_hindi_english_pdf.py
```

Shift page markers (if needed): `python Scripts/_kd_shift_page_markers.py --from 54 --delta 1 --cap-final 153`

## Glossary

Settled terminology and judgment calls: [`KD-Glossary-Additions.md`](KD-Glossary-Additions.md), [`KD-Translation-Glossary.xlsx`](KD-Translation-Glossary.xlsx), [`../MD-Mapping.xlsx`](../MD-Mapping.xlsx).

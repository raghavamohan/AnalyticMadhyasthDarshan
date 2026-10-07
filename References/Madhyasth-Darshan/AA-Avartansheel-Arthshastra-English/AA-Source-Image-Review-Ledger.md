# AA source-image review ledger

This ledger records direct comparison of English translation batches with the
rendered Hindi pages in `_page-images/`. It distinguishes an initial translation,
a fidelity review, and an independent second review; completing one does not imply
the others.

## Coverage

- Source images prepared: **164 / 164**
- Front-matter pages translated: **10 / 10** (first pass)
- Body pages translated: **24 / 149** (first pass)
- Body pages fidelity-reviewed against images: **0 / 149**
- Body pages independently second-reviewed: **0 / 149**

The first three batches were translated directly from the page images on 7 October
2026, page by page, with a targeted re-read of the densest sentences against the
images; the corrections to batches already committed are logged below. That is not a full
fidelity review: every sentence still needs its clause-by-clause comparison. The
structural inventory in the [README](README.md#structural-inventory) is not
translation or review coverage.

## Batch ledger

| Batch | PDF pages | Printed pages | Translation | Fidelity review | Second review | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 1-10 | front matter | first pass, 7 Oct 2026 | pending | pending | Title page, imprint, *vikalp* (i)-(v), contents; PDF pp. 8 and 10 blank. The *vikalp* is close to KD's; KD wording was reused only where the Hindi matches, and AA's differences (the fourth question, the सत्यापन heading, the item 3 list) were translated afresh. |
| 2 | 11-18 | 1-8 | first pass, 7 Oct 2026 | pending | pending | Chapter 1. Bold passages on pp. 4-7 kept as bold. |
| 3 | 19-34 | 9-24 | first pass, 7 Oct 2026 | pending | pending | Chapter 2. Bold passages kept as bold, including those that run across page breaks (pp. 18-19, 23-24). Even-page running heads (मध्यस्थ दर्शन सहअस्तित्ववाद ...) are not translated. Closing formula and ornament on p. 24. |

## Correction log

| Date | PDF / printed page | Issue | Source-supported correction | Reviewer |
| :--- | :--- | :--- | :--- | :--- |
| 7 Oct 2026 | PDF 13 / p. 3 | First draft had people surrendering their acquisitions to the seat of state | The Hindi makes सुरक्षा govern the acquisitions, body and family: people surrendered to the seat of state on assurances of the security of these | Claude (translator's re-read) |
| 7 Oct 2026 | PDF 12 / p. 2 | महिमावश was rendered "inspired by the glory of" | MD: महिमा = magnificence; changed to "inspired by the magnificence of" so that महिमा stays distinct from वैभव (grandeur), as chapter 2 requires | Claude (terminology consistency) |

## Review method

- Read the Hindi from the named rendered source image, or use
  [`AA-Avartansheel-Arthshastra-Hindi-English.pdf`](AA-Avartansheel-Arthshastra-Hindi-English.pdf),
  which pairs each Hindi page with its English on one sheet. Rebuild it first with
  `python Scripts/_aa_build_hindi_english_pdf.py` if the manuscript has changed.
- Compare sentence order, negation, enumeration, agency, referents, headings,
  tables, diagrams, and technical terms with the English page.
- Confirm terminology against MD-Mapping and published MVD/SB/JV usage; use KD only
  as a same-sense contextual precedent.
- Revise only where the source image supports the change.
- Record glossary changes separately in `AA-Glossary-Additions.md`.
- Never expand the coverage totals beyond the pages actually reviewed at that level.

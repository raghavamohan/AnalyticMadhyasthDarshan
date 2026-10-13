# AA source-image review ledger

This ledger records direct comparison of English translation batches with the
rendered Hindi pages in `_page-images/`. It distinguishes an initial translation,
a fidelity review, and an independent second review; completing one does not imply
the others.

## Coverage

- Source images prepared: **164 / 164**
- Front-matter pages translated: **10 / 10** (first pass)
- Body pages translated: **149 / 149** (first pass)
- Trailing pages translated: **5 / 5** (first pass; PDF 160–164, logical pp. 150–154)
- Body pages fidelity-reviewed against images: **0 / 149**
- Body pages independently second-reviewed: **0 / 149**

Batches 1–3 were translated directly from the page images on 7 October 2026, and
batches 4–9 on 13 October 2026 by parallel translators working from a common brief and
term sheet, then merged and harmonised (see
[`AA-Translation-Term-Log.md`](AA-Translation-Term-Log.md)). Every batch was translated
page by page from the images, with a targeted re-read of the densest sentences; the
corrections to batches already committed are logged below. That is not a full
fidelity review: every sentence still needs its clause-by-clause comparison. The
structural inventory in the [README](README.md#structural-inventory) is not
translation or review coverage.

## Batch ledger

| Batch | PDF pages | Printed pages | Translation | Fidelity review | Second review | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 1-10 | front matter | first pass, 7 Oct 2026 | pending | pending | Title page, imprint, *vikalp* (i)-(v), contents; PDF pp. 8 and 10 blank. The *vikalp* is close to KD's; KD wording was reused only where the Hindi matches, and AA's differences (the fourth question, the सत्यापन heading, the item 3 list) were translated afresh. |
| 2 | 11-18 | 1-8 | first pass, 7 Oct 2026 | pending | pending | Chapter 1. Bold passages on pp. 4-7 kept as bold. |
| 3 | 19-34 | 9-24 | first pass, 7 Oct 2026 | pending | pending | Chapter 2. Bold passages kept as bold, including those that run across page breaks (pp. 18-19, 23-24). Even-page running heads (मध्यस्थ दर्शन सहअस्तित्ववाद ...) are not translated. Closing formula and ornament on p. 24. |
| 4 | 35-53 | 25-43 | first pass, 13 Oct 2026 | pending | pending | Chapter 3. Key definitions on pp. 25–26; sub-headings on pp. 30 and 34; atom and energy vocabulary on pp. 30–41. 21 unclear passages. |
| 5 | 54-77 | 44-67 | first pass, 13 Oct 2026 | pending | pending | Chapter 4. Four bold passages cross page breaks. 30 unclear passages. |
| 6 | 78-105 | 68-95 | first pass, 13 Oct 2026 | pending | pending | Chapter 5. Sub-heading and definitions of usefulness, right-use and purposeful use on p. 94. 30 unclear passages. |
| 7 | 106-119 | 96-109 | first pass, 13 Oct 2026 | pending | pending | Chapters 6–7. Five-column table on p. 101; two-block depiction on p. 102; the humane-constitution diagram on p. 109 as a translator's note and table. 16 unclear passages. |
| 8 | 120-131, 160-164 | 110-121, trailing | first pass, 13 Oct 2026 | pending | pending | Chapter 8 and the trailing pages. The five-dimensions diagram and the aspirations chart on p. 112 as translator's notes and tables. The running heads on pp. 111–121 misprint "(अध्याय – 9)". Publisher's list of works (PDF 161) with transliterated and English titles. 15 unclear passages. |
| 9 | 132-159 | 122-149 | first pass, 13 Oct 2026 | pending | pending | Chapter 9. Numbered schemes kept as printed; values table on p. 141; closing verse on p. 149. 17 unclear passages. |

## Correction log

| Date | PDF / printed page | Issue | Source-supported correction | Reviewer |
| :--- | :--- | :--- | :--- | :--- |
| 7 Oct 2026 | PDF 13 / p. 3 | First draft had people surrendering their acquisitions to the seat of state | The Hindi makes सुरक्षा govern the acquisitions, body and family: people surrendered to the seat of state on assurances of the security of these | Claude (translator's re-read) |
| 7 Oct 2026 | PDF 12 / p. 2 | महिमावश was rendered "inspired by the glory of" | MD: महिमा = magnificence; changed to "inspired by the magnificence of" so that महिमा stays distinct from वैभव (grandeur), as chapter 2 requires | Claude (terminology consistency) |
| 13 Oct 2026 | PDF 21 / p. 11 | Item 3 opening: the relation between the source of awareness, the joint system of body and jeevan, and their goal and study was unclear | Revised wording supplied by the author: "The fact that the fundamental source of awareness is the formation and functioning of the body and jeevan as a joint system, the goals and the method of study of awareness, have not become studiable …"; मीमांसा rendered "hermeneutics" here | Raghava (author review) |
| 13 Oct 2026 | PDF 22 / p. 12 | The bold definitions of science-wisdom, knowledge, wisdom and analysis (*vivechana*) did not read clearly | Revised wording supplied by the author ("Science-wisdom are meant to bring about consistency between all analyses and knowledge. …"); bold kept as in the source | Raghava (author review) |
| 13 Oct 2026 | PDF 6 / *vikalp* item 13 | The draft made "a physical structure" the subject of the sentence | The Hindi (भौतिक रचना रुपी धरती पर ही) describes the earth as a physical formation; the sentence now reads "on this very earth, which is a physical formation, it was understood that formations composed of biological cells … flourished" | Claude (re-read for the unclear-passage index) |
| 13 Oct 2026 | PDF 24, 31 / pp. 14, 21 | आवर्तनशील अर्थव्यवस्था was rendered "cyclical economic system" | Key term 1 (approved) is "cyclical economy"; both places corrected while harmonising chapters 3–9 | Claude (terminology consistency) |
| 13 Oct 2026 | PDF 19 / p. 9 | अनुसंधान was rendered "investigation" | MD: अनुसंधान = exploration; "research and exploration" (twice), matching chapters 3–9 | Claude (terminology consistency) |

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

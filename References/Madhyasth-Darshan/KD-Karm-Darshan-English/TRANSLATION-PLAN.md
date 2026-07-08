# Karm Darshan English Translation — Plan for Remaining Work

Goal: a complete working English translation of *Manav Karm Darshan* (v5) by Shri A. Nagaraj,
covering front matter and all three chapters. This plan supersedes the "Not yet translated" list
in `README.md` with an exact, page-verified breakdown and a proposed order of work.

## Status as of 2026-07-08

**Book structure** (confirmed against the Hindi original's own table of contents and the
detailed chapter-3 sub-TOC, PDF pp. 24 and 76–78): the book has front matter, then exactly three
chapters. Printed page = PDF page − 25. Actual book content ends at printed p.153 (PDF p.178,
closing benediction); printed pp.154–155 are publisher back matter, not book content — excluded
throughout.

| Chapter | Hindi | Printed pp. | Status |
|---|---|---|---|
| — | Front matter (title page, author's declaration, "मध्यस्थ दर्शन के मूल तत्व" outline, प्राक्कथन preface, अनुक्रमणिका TOC) | pdf 1–25 (~21 content pages) | Not translated |
| 1 | कर्म (Karma) | 1–29 | **Done** — `KD-Ch1-Karma.md` |
| 2 | उपासना (Upasana / Worship) | 30–49 | **Done** — `KD-Ch2-Upasana.md` (corrected range: pp.50–52 are not chapter 2 — p.50 is blank, pp.51–52 are chapter 3's title page and detailed sub-TOC) |
| 3.1–3.3 | Atomic Structure & Molecular Composition; Development Progression; Development in the Atom | 53–63 | **Done** — `KD-3.1-3.3-Atomic-Structure-and-Development.md` |
| 3.4–3.6 | मनःस्वस्थता का स्वरूप (Nature of mental well-being); सहअस्तित्व स्थिर है, विकास और जागृति निश्चित है; अनुभव और जागृति की स्थिरता और निश्चयता | 64–72 | **Done** — `KD-3.4-3.6-Mental-Wellbeing-Coexistence-Stability.md` |
| 3.7–3.8 | Heat and the Earth's Balance; State–Motion | 73–87 | **Done** — `KD-3.7-3.8-Heat-Earth-Balance-State-Motion.md` |
| 3.9–3.10 | मात्रा (Quantity); गुण, स्वभाव, धर्म (Property, Disposition, Dharma) | 88–102 | **Done** — `KD-3.9-3.10-Quantity-Property.md` |
| 3.11–3.12 | Force–Power; Projection–Reflection | 102–118 | **Done** — `KD-3.11-3.12-Force-Power-Projection-Reflection.md` |
| 3.13–3.15 | Pressure/Flow/Wave/EM Force; Place/Direction/Distance/Area/Angle; Time | 118–135 | **Done** — `KD-3.13-3.15-Pressure-Wave-Electromagnetic-Space-Time.md` |
| 3.16–3.18 | प्राणावस्था, मानव शरीर और जीवन के संयुक्त रूप में मानव; ज्ञान, ज्ञाता, ज्ञेय (Knowledge, Knower, Known); दृष्टा, कर्त्ता, भोक्ता (Seer, Doer, Enjoyer) | 135–153 | **Done** — `KD-3.16-3.18-Life-State-Knower-Seer-Doer.md` |

**Chapter 3 (pp. 53–153) is fully translated across 7 files, chapter 1 (pp. 1–29) is done as its
own file, and chapter 2 (pp. 30–49) is done as its own file.** Done: ~148 printed pages (9
files). Remaining: front matter only (~21pp).

Note: chapter 2's actual content ends at printed p.49, not p.52 as originally estimated below —
p.50 is blank and pp.51–52 are chapter 3's own title page and detailed sub-table-of-contents
(printed page = PDF page − 25 still holds; the sub-TOC there lists chapter 3's 16 sections with
their own page numbers, corroborating the PDF pp. 76–78 sub-TOC location noted above).

## Proposed batches and order

Same granularity as the existing files (topic-coherent chunks, each its own `.md`). Suggested
order, front-loading the highest-value/lowest-risk work:

1. ~~Chapter 2 — उपासना (pp.30–52, ~23pp) as its own file.~~ **Done** — `KD-Ch2-Upasana.md`
   (actual range pp.30–49, ~20pp). Chapter 1's foundational glossary entries (कर्म, इच्छा,
   आवश्यकता, वेदना, संस्कार, काम, अर्थ, अभीष्ट) were reused rather than re-decided; see
   `KD-Glossary-Additions.md` for chapter 2's own new terms (उपासना, विवेक, नश्वरत्व,
   कूटस्थ/रूपस्थ/आत्मस्थ, देवात्मा/भूतात्मा/दिव्यात्मा, and others).
2. **Front matter** last (~21pp) — paratext rather than argument, lowest priority for a working
   translation, but needed for completeness. Note: `MVD-Madhyasth-Darshan-Coexistentialism.pdf`
   already contains a published English rendering of the "मध्यस्थ दर्शन के मूल तत्व" section
   (it's reproduced verbatim there, item-numbered, starting MVD p.11) — reuse/cross-check against
   that instead of translating it cold.

## Methodology (unchanged from the existing 8 files)

The source PDF's embedded text layer is corrupted (confirmed: extracted text shows systematic
glyph-substitution garbling, e.g. "कास्यक" for "कायिक") — text extraction/OCR-by-copy-paste does
not work. For each batch:

1. Render the printed-page range to images (PyMuPDF, ~150 dpi) from `../KD-karm darshan v5.pdf`
   (PDF page = printed page + 25).
2. Translate page-by-page from the images, carrying `[p. NN]` markers at each page break, italic
   transliteration on first occurrence per chapter for untranslatable technical terms.
3. Apply glossary conventions (below) for consistency with the 8 completed files and with the
   wider Madhyasth Darshan corpus.
4. Update `README.md`'s status table and this plan's status table as each batch lands.

## Glossary resources (substantially stronger now than when the first 4 files were translated)

- **`../MD-Mapping.xlsx`** — now ~2147 rows, reconciled against Rakesh Gupta's MVD and SB
  translations (2026-07-08 update): 59 terms corrected where MD-Mapping's old value conflicted
  with MVD/SB usage, 53 new rows added for previously-uncovered terms. Check it first for any
  unfamiliar term.
- **`../MD-Mapping-Sources/`** — the underlying parallel Hindi–English corpora
  (`mvd_pairs.json`, `sb_pairs.json`) extracted from MVD and SB. **SB in particular directly
  overlaps with KD's उपासना content** — before translating chapter 2, it's worth grepping
  these files for उपासना-specific vocabulary — SB may already have a Rakesh Gupta–quality rendering of the same concept
  to check against, the same way MVD already covers the front matter's "मूल तत्व" section.
- **`KD-Glossary-Additions.md`** — KD-specific term decisions and settled conventions. Known
  contextual exceptions to apply (don't blindly follow MD-Mapping's single global rendering
  where these apply):
  - **आवेश/आवेशित** — "charge/charged" for the positive–negative (sam–visham) atomic-imbalance
    sense; "excitation/excited" where it contrasts a neutral/natural state with a disturbed one.
  - **श्रम = effort**; "labour" only in the economic compounds (श्रम मूल्य, श्रम विनिमय, श्रम
    नियोजन — not yet encountered in translated KD text, so this hasn't been tested yet).
  - **ताप = "temperature"**, distinct from ऊष्मा = "heat" — the two are used contrastively in
    KD 3.7 itself; don't collapse both to "heat" even though MD-Mapping's plain row now says
    ताप=heat.
  - **वास्तविकता = "actuality"**, distinct from यथार्थता = "reality" — both appear together in a
    "reality, actuality, truth" list; don't collapse to the same English word.
  - **परावर्तन = projection, प्रत्यावर्तन = reflection** (re-settled 2026-07-08, aligned with
    MD-Mapping/MVD) — watch for this pair in the still-untranslated chapters too, since it's a
    recurring epistemological duality in this corpus, not confined to chapter 3.12.
  - **संसार compounds** (पशु-संसार, वनस्पति-संसार, etc.) render as "order" (animal order, plant
    order), not literal "world".
  - **गुण = "property"**, NOT "quality" (per Raghava, 2026-07-08) — applies to the noun गुण as it
    recurs in the रूप/गुण/स्वभाव/धर्म (form/property/disposition/dharma) list of the four orders'
    predominant traits. Exception: गुणात्मक परिवर्तन (adjectival compound) keeps "qualitative
    change/transformation" per MD-Mapping's own separate row for that compound.
  - **दृष्टा/ज्ञाता/साध्य/साधक/साधन** keep MD-Mapping's existing renderings (Seer, knower, aim,
    the seeker, the means); **कर्त्ता/भोक्ता, दृश/दृश्य/दर्शन, ध्यान/ध्याता/ध्येय** are not in
    MD-Mapping and use compositional judgment-call renderings (doer/enjoyer; the
    seeing/the seen/seeing; attention/attender/object of attention) — see
    `KD-Glossary-Additions.md` for the full triads and reasoning, introduced in KD 3.16–3.18.
  - **KD 1 (Karma) settles several more terminology decisions**, watch for these in chapter 2
    too: **संस्कार** = left transliterated "*sanskar*", distinct from **संस्कृति** = "culture"
    (they appear together constantly); **अभीष्ट** = "desire" (per Raghava, 2026-07-08 — note
    this now overlaps in English with इच्छा, the general term for desire; distinguish by
    context), kept distinct from **साध्य** = "aim" (the source glosses them together as
    "साध्य (अभीष्ट)" → "the aim (the desire)"); **अनुभूति** = "experiencing", distinct from
    **अनुभव** = "realisation"; **काम** = "*kama*" (desire), kept transliterated rather than
    MD-Mapping's "lust" (used only in the classical मोक्ष/धर्म/काम/अर्थ list); **कायिक** =
    "physical" (per Raghava, 2026-07-08, matching MD-Mapping — note this now overlaps in
    English with भौतिक, also "physical"; distinguish by context); and **कृत, कारित, अनुमोदित**
    = "done, caused, intended" (per Raghava, 2026-07-08).
- When a new technical term comes up with no existing MD-Mapping row and no MVD/SB evidence,
  add it to `KD-Glossary-Additions.md` following the existing table format, and flag it as a
  judgment call (as the existing entries do) rather than silently deciding.

## Definition of done for each batch

- New `.md` file matches the existing format: title line, one-line disclaimer/epigraph, `##`
  chapter headers with Hindi title in parentheses, `[p. NN]` markers, italic transliterations.
- `README.md`'s "Translated so far" / "Not yet translated" tables and this plan's status table
  both updated.
- Any new judgment-call terms added to `KD-Glossary-Additions.md`.
- Spot-check a handful of technical terms against `MD-Mapping.xlsx` before considering the batch
  finished.

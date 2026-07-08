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
| 1 | कर्म (Karma) | 1–29 | Not translated |
| 2 | उपासना (Upasana / Worship) | 30–52 | Not translated |
| 3.1–3.3 | Atomic Structure & Molecular Composition; Development Progression; Development in the Atom | 53–63 | **Done** — `KD-3.1-3.3-Atomic-Structure-and-Development.md` |
| 3.4 | मनःस्वस्थता का स्वरूप (Nature of mental well-being) | 63–67 | Not translated |
| 3.5 | सहअस्तित्व स्थिर है, विकास और जागृति निश्चित है | 68 | Not translated |
| 3.6 | अनुभव और जागृति की स्थिरता और निश्चयता | 69–72 | Not translated |
| 3.7–3.8 | Heat and the Earth's Balance; State–Motion | 73–87 | **Done** — `KD-3.7-3.8-Heat-Earth-Balance-State-Motion.md` |
| 3.9 | मात्रा (Quantity) | 87–98 | Not translated |
| 3.10 | गुण (Quality) | 99–101 | Not translated |
| 3.11–3.12 | Force–Power; Projection–Reflection | 102–118 | **Done** — `KD-3.11-3.12-Force-Power-Projection-Reflection.md` |
| 3.13–3.15 | Pressure/Flow/Wave/EM Force; Place/Direction/Distance/Area/Angle; Time | 118–135 | **Done** — `KD-3.13-3.15-Pressure-Wave-Electromagnetic-Space-Time.md` |
| 3.16 | प्राणावस्था, मानव शरीर और जीवन के संयुक्त रूप में मानव | 135–144 | Not translated |
| 3.17 | ज्ञान, ज्ञाता, ज्ञेय (Knowledge, Knower, Known) | 145–149 | Not translated |
| 3.18 | दृष्टा, कर्त्ता, भोक्ता (Seer, Doer, Enjoyer) | 150–153 | Not translated |

Done: ~57 printed pages (4 files). Remaining: ~117 pages across front matter + 2 chapters + 6
chapter-3 gaps.

## Proposed batches and order

Same granularity as the existing files (topic-coherent chunks, each its own `.md`). Suggested
order, front-loading the highest-value/lowest-risk work:

1. **Close the chapter 3 gaps first** — keeps the physics core (chapter 3) complete and
   self-contained, and stays in the vocabulary already built up across 4 files and the glossary:
   - `KD-3.4-3.6-Mental-Wellbeing-Coexistence-Stability.md` (pp.63–72, ~10pp)
   - `KD-3.9-3.10-Quantity-Quality.md` (pp.87–101, ~15pp)
   - `KD-3.16-3.18-Life-State-Knower-Seer-Doer.md` (pp.135–153, ~19pp) — the philosophical
     capstone of chapter 3; likely the densest of the three remaining gaps.
2. **Chapter 1 — कर्म** (pp.1–29, ~29pp) as its own file. Foundational terms here (कर्म, इच्छा,
   आवश्यकता, वेदना) will seed glossary entries the rest of the book leans on — translate before
   chapter 2.
3. **Chapter 2 — उपासना** (pp.30–52, ~23pp) as its own file.
4. **Front matter** last (~21pp) — paratext rather than argument, lowest priority for a working
   translation, but needed for completeness. Note: `MVD-Madhyasth-Darshan-Coexistentialism.pdf`
   already contains a published English rendering of the "मध्यस्थ दर्शन के मूल तत्व" section
   (it's reproduced verbatim there, item-numbered, starting MVD p.11) — reuse/cross-check against
   that instead of translating it cold.

## Methodology (unchanged from the existing 4 files)

The source PDF's embedded text layer is corrupted (confirmed: extracted text shows systematic
glyph-substitution garbling, e.g. "कास्यक" for "कायिक") — text extraction/OCR-by-copy-paste does
not work. For each batch:

1. Render the printed-page range to images (PyMuPDF, ~150 dpi) from `../KD-karm darshan v5.pdf`
   (PDF page = printed page + 25).
2. Translate page-by-page from the images, carrying `[p. NN]` markers at each page break, italic
   transliteration on first occurrence per chapter for untranslatable technical terms.
3. Apply glossary conventions (below) for consistency with the 4 completed files and with the
   wider Madhyasth Darshan corpus.
4. Update `README.md`'s status table and this plan's status table as each batch lands.

## Glossary resources (substantially stronger now than when the first 4 files were translated)

- **`../MD-Mapping.xlsx`** — now ~2147 rows, reconciled against Rakesh Gupta's MVD and SB
  translations (2026-07-08 update): 59 terms corrected where MD-Mapping's old value conflicted
  with MVD/SB usage, 53 new rows added for previously-uncovered terms. Check it first for any
  unfamiliar term.
- **`../MD-Mapping-Sources/`** — the underlying parallel Hindi–English corpora
  (`mvd_pairs.json`, `sb_pairs.json`) extracted from MVD and SB. **SB in particular directly
  overlaps with KD's remaining physics content** — e.g. SB has passages specifically about
  प्राणावस्था/biological cells that map onto KD 3.16. Before translating a chapter-3 gap, it's
  worth grepping these files for the chapter's key terms — SB may already have a Rakesh
  Gupta–quality rendering of the same concept to check against, the same way MVD already covers
  the front matter's "मूल तत्व" section.
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

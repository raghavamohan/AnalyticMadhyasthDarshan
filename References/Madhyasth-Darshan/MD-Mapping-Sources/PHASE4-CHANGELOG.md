# Phase 4 — Exhaustive MVD/SB glossary expansion + KD verification (2026-07-10)

Goal: expand `../MD-Mapping.xlsx` with remaining Hindi tokens attested at **frequency ≥ 2**
in MVD/SB bilingual pairs, then verify the KD working translation against the glossary.

## Pipeline

```powershell
cd "References/Madhyasth-Darshan/MD-Mapping-Sources"
python extract_pairs.py "..\MVD-Madhyasth-Darshan-Coexistentialism.pdf" MVD mvd_pairs.json
python extract_pairs.py "..\SB-Samadhanatmak-Bhautikvad.pdf" SB sb_pairs.json
python build_candidates.py
python gather_new_term_evidence.py candidates_freq2.json mvd_pairs.json sb_pairs.json phase4_evidence.json
# curated proposals → phase4_new_rows.json (see below)
python phase4_apply_rows.py
python kd_verify_against_mapping.py
python ..\..\..\Scripts\_kd_build_glossary_xlsx.py
```

## Counts

| Stage | Count |
|-------|------:|
| MVD pairs (with English) | 597 |
| SB pairs (with English) | 137 usable / 147 total |
| Uncovered tokens freq ≥ 2 (after stopwords + known lemmas) | **818** |
| Evidence packs (`phase4_evidence.json`) | 818 |
| Technical review cards remaining (`phase4_review_cards.*`) | 293 (freq ≥ 3, len ≥ 4, not yet applied) |
| **New MD-Mapping rows applied (2148–2207)** | **60** |
| MD-Mapping nonempty Hindi rows after Phase 4 | **1649** |

## What was applied

Sixty high-confidence rows were **hand-curated from paired MVD/SB evidence** (not invented).
Automated short-unit / co-occurrence / positional-alignment proposers were tried first; paragraph
misalignment in the bilingual PDFs produced too many false glosses, so only evidence-checked
curated rows were written into the xlsx (columns A/B/C/F/I; D/E/G/H left empty, same as Phase 3).

Notable additions: अखण्ड (undivided), पूरक (complementary), जंगल युग / धातु युग (Jungle/Iron Age),
अमानवीय दृष्टि (inhumane perspective), शाकाहारी/मांसाहारी, सम्पर्क, नियंत्रित/संरक्षित, वर्ग विहीन, etc.

## What remains (honest gap)

Of the **818** freq≥2 candidates, most are:

- function/discourse words (expanded stop list still incomplete),
- inflections of lemmas already in MD-Mapping,
- or terms whose English cannot be read safely from long misaligned paragraph pairs.

`phase4_review_cards.json` / `.txt` list **293** remaining technical-looking candidates (freq≥3)
with evidence snippets for continued manual curation. Re-run `phase4_write_review_cards.py`
after further applies.

## JV

JV still has no usable Hindi text layer for hi→en pairs. Optional JV page citations were not
added to Phase 4 rows (English-phrasing cross-check only). Analysis `.md` extracts remain
non-authoritative for Studies citations.

## KD verification

See [`KD-vs-MD-Mapping-report.md`](KD-vs-MD-Mapping-report.md) (machine JSON alongside).

Snapshot after Phase 4:

- KD-Glossary-Additions vs MD-Mapping: **52 aligned**, **65 overrides**, **35 md_missing**, **1 md_missing_english**
- Known deliberate exceptions recorded in the report (ताप, वास्तविकता, संस्कार, काम, …)
- `KD-Translation-Glossary.xlsx` regenerated so Overrides reflect the expanded MD-Mapping

No KD body text was changed in this phase (report only).

# MD-Mapping Sources — Extracted Hindi–English Pairs

Phase 1 extraction artifacts supporting an update to `../MD-Mapping.xlsx` from Rakesh Gupta's
published/working translations (JV, MVD, SB), so KD-Karm-Darshan-English stays consistent with
his established terminology.

## Files

- `extract_pairs.py` — extraction script. Walks PDF text blocks per page, classifies each as
  Hindi (`hi`), English (`en`), or `mixed`, merges consecutive same-class blocks into paragraph/item
  units, and pairs each Hindi unit with the English unit that immediately follows it.
- `mvd_pairs.json` — 597 pairs from `MVD-Madhyasth-Darshan-Coexistentialism.pdf` (item/bullet granularity).
- `sb_pairs.json` — 147 pairs from `SB-Samadhanatmak-Bhautikvad.pdf` (paragraph granularity).
- `build_candidates.py` — Phase 4: uncovered tokens at freq ≥ 2 vs live `MD-Mapping.xlsx`.
- `gather_new_term_evidence.py` — evidence packs for candidate tokens.
- `phase4_apply_rows.py` / `phase4_new_rows.json` — apply curated Phase 4 rows.
- `kd_verify_against_mapping.py` — KD glossary/body vs MD-Mapping report.
- `phase4_review_cards.*` — remaining technical candidates for continued curation.

Each pair entry: `{book, hi, en, hi_page, en_page}` — page numbers are PDF page numbers (1-indexed), not printed page numbers.

## Known limitations

- **JV excluded.** `JV-Jeevan-Vidya-An-Introduction.pdf` is English-only in this copy (no
  Devanagari text layer despite the translator's note describing a bilingual edition). It's
  useful for cross-checking Rakesh Gupta's English phrasing/transliteration conventions, but
  contributes no Hindi→English term pairs.
- **SB has no English past ~printed p.272.** Pages ~273–298 (closing chapters, e.g. "9)
  संकरीकरण और परंपरा") are Hindi-only in this file — confirmed by reading the raw page text, not
  an extraction artifact. `sb_pairs.json` has 10 entries with `en: null` marking this tail.
- **MVD has occasional block-order noise** on pages with non-standard sub-layout (e.g. item 7
  "प्रमाण/The Evidence" merges oddly because that page's Hindi/English blocks aren't laid out in
  the usual stacked order). A handful of pairs like this exist; most are clean.
- Page-level merging only — a block that straddles pages is joined to its continuation, but the
  hi→en pairing itself is positional, not semantic. Some pairs will be noisy; Phase 2 (semantic
  alignment against MD-Mapping.xlsx) needs to tolerate this rather than assume 1:1 clean alignment.

## Phase 2 — done (2026-07-08)

See [`PHASE2-CHANGELOG.md`](PHASE2-CHANGELOG.md) for the full writeup. Summary: 927 of ~1536
glossary rows had MVD/SB evidence; 695 confirmed (citation added only), 59 updated in place
(English term changed per the MVD > SB > existing priority rule — old value preserved in a
column F note), 173 flagged as ambiguous (evidence found but term-level rendering unclear —
left untouched). One special case — परावर्तन/प्रत्यावर्तन — was left as-is but flagged for a
manual decision since it contradicts an explicit KD-specific ruling on record.

## Phase 3 — done (2026-07-08)

See [`PHASE3-CHANGELOG.md`](PHASE3-CHANGELOG.md). Summary: checked all 4 translated KD chapters
against the Phase 2 conflict list (no body-text changes needed — the two terms that actually
appear, ताप and वास्तविकता, are correctly kept as contextual exceptions rather than updated to
the new global value; two stale documentation citations were fixed instead). Added 53 new
`MD-Mapping.xlsx` rows (2095–2147) for terms frequent in MVD/SB but previously missing from the
glossary entirely, including स्वभावगति, सहअस्तित्ववाद, and the six paired dṛṣṭi terms.

## Phase 4 — done (2026-07-10)

See [`PHASE4-CHANGELOG.md`](PHASE4-CHANGELOG.md). Summary: regenerated MVD/SB pairs; built **818**
freq≥2 uncovered candidates with evidence; applied **60** curated high-confidence rows
(2148–2207) after automated proposers proved too noisy on paragraph-aligned pairs; left **293**
technical review cards for continued curation. KD verification report:
[`KD-vs-MD-Mapping-report.md`](KD-vs-MD-Mapping-report.md).

```powershell
python build_candidates.py
python gather_new_term_evidence.py candidates_freq2.json mvd_pairs.json sb_pairs.json phase4_evidence.json
python phase4_apply_rows.py
python kd_verify_against_mapping.py
```

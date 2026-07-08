# Phase 3 — KD revision check + new MD-Mapping rows (2026-07-08)

Two tasks: (1) check whether the Phase 2 conflict-updates require revising the already-translated
KD chapters, (2) propose brand-new `MD-Mapping.xlsx` rows for terms that appear frequently in
MVD/SB but aren't in the glossary at all.

## 1. KD translation revision check

Searched all 4 translated KD files (`KD-3.1-3.3`, `KD-3.7-3.8`, `KD-3.11-3.12`, `KD-3.13-3.15`)
and the glossary/README docs for every one of Phase 2's 59 changed terms.

**Result: no body-text revisions were needed.** Most of the 59 changed terms simply haven't come
up yet in the ~57 pages translated so far. Of the few that are physics-relevant:

- **प्राण (Prana)** — KD already consistently uses "Prana" (as `prana cells`, `prana air`,
  `prana sutras`), matching the Phase 2 update. Nothing to change.
- **ताप (temperature) and वास्तविकता (actuality)** — these are the two cases that actually
  appear in KD text, and in both cases **the existing KD wording is correct and should NOT be
  changed to the new global MD-Mapping value.** KD 3.7 (pp.74–76) uses ताप="temperature"
  contrastively against ऊष्मा="heat" in the same passage; KD 3.1/3.7 uses वास्तविकता="actuality"
  distinct from यथार्थता="reality" in the same list ("reality, actuality, truth"). Applying the
  new global renderings ("heat", "reality") would collapse distinctions the source text is
  actively drawing. Documented as contextual exceptions in `MD-Mapping.xlsx` (column F, rows 1359
  and 621) and in `../KD-Karm-Darshan-English/README.md`'s Conventions section, alongside the
  existing āvesh/āveshit and śram exceptions.
- **सारक/मारक, मध्यस्थ बल, सूत्र व्याख्या, निर्विरोध, आप्लावन** — not present in translated KD
  text at all; no action needed (will matter only once later chapters are translated).

**Documentation fixes applied** (stale citations, not translation changes):
- `KD-Glossary-Additions.md`'s श्रम row cited the old श्रम मूल्य/श्रम विनिमय values — updated to
  the Phase 2 values, with a note that these compounds haven't appeared in KD text yet.
- The परावर्तन/प्रत्यावर्तन notes (both files) previously said "MD-Mapping should be revisited."
  Updated to reflect that **MVD independently confirms MD-Mapping's original (opposite) pairing**
  — this is no longer just MD-Mapping's own unverified guess. **Resolved 2026-07-08**: per
  Raghava, the KD chapters were realigned to MD-Mapping/MVD (परावर्तन=projection,
  प्रत्यावर्तन=reflection), superseding the July 2026 KD-specific choice. See Section 3 below.

## 3. परावर्तन/प्रत्यावर्तन realignment (2026-07-08, after the above was flagged)

Swapped throughout `KD-3.11-3.12` (68 instances — the file itself is entirely about this
duality, chapter retitled "Projection–Reflection", file renamed to
`KD-3.11-3.12-Force-Power-Projection-Reflection.md`) and the confirmed-parāvartan instances in
`KD-3.7-3.8` (10 of 11 "reflect*" hits — heat/light physical-reflection passages, e.g. "the
sun's heat is being projected equally in all directions").

**Not swapped**, deliberately: KD-3.1-3.3's 3 "reflect*" hits and KD-3.13-3.15's 12 hits, and
one specific KD-3.7-3.8 hit (p.83, "celestial light is reflected (imaged)") — all verified
against the Hindi source to translate a *different* word, प्रतिबिंब/प्रतिबिंबित ("image/mirror
image"), not परावर्तन. Blind text-based swapping would have silently corrupted these — the same
English word "reflection" renders two unrelated Hindi technical terms in this corpus.

## 2. New MD-Mapping rows: 53 added (rows 2095–2147)

Pipeline: tokenized all Hindi text across `mvd_pairs.json`+`sb_pairs.json`, subtracted anything
already covered by an existing glossary row (~1424 known tokens), dropped ~200 function
words/pronouns via a stopword list (`stopwords.py`), leaving 315 candidate tokens (freq ≥ 4).
Each was sent with evidence to an agent that could (a) reject it as a grammatical form or
inflection of an already-covered concept — importantly, agents cross-checked candidates directly
against the live `MD-Mapping.xlsx`, catching several near-misses my token-matching missed (e.g.
गठनपूर्ण already existing as "गठन पूर्णता", बन्धन as "बंधन") — or (b) propose a new row with an
English rendering read off the paired evidence, not guessed from the transliteration.

**56 proposed → 53 unique rows after dedup** (two अंश duplicates merged; मानवेतर/मनुष्येत्तर/
KD's own मानवेत्तर spelling merged into one row with all three variants).

Notable finds:
- **स्वभावगति ("natural state")** — a core recurring term already used in KD's own translation
  (as *svabhav gati*, contrasted with आवेशित गति) but never captured in MD-Mapping itself.
- **सहअस्तित्ववाद (Coexistentialism)** — the name of the "-ism" itself, distinct from
  सहअस्तित्व (coexistence, the state), previously missing.
- Six paired "dṛṣṭi" behavioural-perspective terms as a complete set: प्रियाप्रिय, हिताहित,
  लाभालाभ, न्यायान्याय, धर्माधर्म, सत्यासत्य.
- Named historical periodization terms from SB: युग (Age/Era) plus दास युग (Submission Age),
  शिलायुग (Stone Age).
- परम्परा (tradition), शांति (peace), आनन्द (bliss) — surprisingly high-frequency core terms
  that had no existing row despite constant use.

New rows carry only Hindi/English/transliteration/citation/note (column F) — no formal
definitions were fabricated; add those by hand if/when needed.

## Files

- `phase3_new_rows.json` — the 53 rows as applied (machine-readable).
- `all_newterm_decisions.json`-equivalent data is in the batch outputs under
  `newterm_batches/` in the working scratch dir (not copied into the repo — only the final
  applied rows are kept here to avoid clutter).
- `gather_new_term_evidence.py`, `stopwords.py` — scripts, for re-running if more source books
  are added later.

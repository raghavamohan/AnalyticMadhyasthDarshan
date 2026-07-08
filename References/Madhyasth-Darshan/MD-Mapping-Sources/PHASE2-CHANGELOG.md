# Phase 2 — MD-Mapping.xlsx reconciled against MVD/SB (2026-07-08)

Cross-checked `../MD-Mapping.xlsx`'s ~1536 real term rows against the Hindi→English pairs
extracted in Phase 1 (`mvd_pairs.json`, `sb_pairs.json`). **Priority rule applied throughout:
MVD's rendering wins over SB's, and SB's wins over whatever was already in MD-Mapping.**

## Pipeline

1. `match_terms.py` — deterministic token-level search: for every glossary Hindi term (and its
   comma-separated spelling variants), find every paragraph/item in MVD and SB that contains it.
   927 of ~1536 rows had at least one hit (784 in MVD, 143 SB-only).
2. `trim_candidates.py` — capped to the 3 shortest/most-focused evidence snippets per row per
   source, to keep the semantic-judgment step tractable.
3. 927 rows were split into batches and each batch read by an agent that (a) located the term
   inside the Hindi excerpt, (b) read the paired English excerpt and pinpointed the term-level
   rendering (not just paraphrased the paragraph), and (c) compared it against the existing
   MD-Mapping English, applying the priority rule.
4. Results applied directly to `MD-Mapping.xlsx` (column B = English term, column I = citation,
   column F = change note / review flag). Full machine-readable output: `phase2_applied_report.json`.

## Results: 927 rows reconciled

| Outcome | Count | Action taken |
|---|---:|---|
| **Confirmed** | 695 | MVD/SB agrees with existing English — citation added to column I, no wording changed. |
| **Conflict → updated** | 59 | MVD/SB renders it differently — column B updated, old value preserved in a column F note, citation added. |
| **Ambiguous → flagged, not changed** | 173 | Evidence found but the term-level rendering couldn't be pinned down cleanly — column B left untouched, a review flag added to column F. |

**Caveat on the ambiguous bucket:** a meaningful chunk of these are extraction noise, not real
translation ambiguity — the sub-agents repeatedly reported cases of truncated excerpts cutting
off right before the term's rendering, SB paragraph-pairing picking up publisher/website
boilerplate instead of a real translation, or a false-positive term match. These are worth a
second pass with wider excerpts before concluding the term is genuinely contested. Don't read
"173 ambiguous" as "173 unresolved philosophical disputes."

## The 59 conflicts (all applied)

| Row | Hindi | Old | New | Source |
|---:|---|---|---|---|
| 76 | श्रम मूल्य | labour value | evaluation of labour | MVD p.269 |
| 77 | श्रम नियोजन | deployment of labour | utilisation of labour | MVD p.265 |
| 78 | श्रम विनिमय | exchange based on labour value | exchange of labour | MVD p.269 |
| 110 | देव मानव | godly human | deific human | MVD p.303 |
| 131 | देव पद | Godly plane | Deific plane | MVD p.9 |
| 140 | नैसर्गिकता | Rest of nature, natural habitat | Naturalness | SB p.15 |
| 150 | प्रजाति | Kind | Species | SB p.17 |
| 160 | सारक | Nourishing | Vitalising | MVD p.52 |
| 161 | मारक | Harming | Devitalising | MVD p.52 |
| 193 | मध्यस्थ बल | mediative strength | Mediative Force | SB p.85 |
| 212 | परिकल्पना | hypothesis | Conception | SB p.26 |
| 255 | प्राण | life | Prana | MVD p.208 |
| 263 | रस | rasa | Taste | MVD p.343 |
| 285 | अध्यास | adhyas | Inertial-impression | MVD p.121 |
| 292 | हृदयंगम | assimilation | Internalise | MVD p.23 |
| 475 | सार्वभौम व्यवस्था | Universal System | Universal Orderliness | MVD p.259 |
| 530 | अधिदैवीवाद | adhi-daivivad | Adhidaivika-vada | SB p.24 |
| 568 | शास्त्र | Treatise | Scripture | MVD p.191 |
| 614 | धारक | bearer | carrier | MVD p.6 |
| 615 | वाहक | carrier | bearer | MVD p.29 |
| 621 | वास्तविकता | actuality | reality | SB p.46 |
| 625 | स्वयं स्फूर्त | self-driven | spontaneity/spontaneous | SB p.54 |
| 667 | अलंकार | clothing | adornment | MVD p.268 |
| 682 | चेष्टा | impulsion | initiative | MVD p.152 |
| 694 | स्पर्धा | striving | contest | MVD p.176 |
| 717 | रस | rasa | taste | MVD p.343 |
| 730 | उत्पन्न | arise | generate / build / cultivate (produce) | MVD p.223-224 |
| 840 | त्रस्त | oppressed | plagued / afflicted | MVD p.143 |
| 844 | संकट | crisis | trouble / problem | MVD p.186 |
| 867 | सूत्र व्याख्या | formula and elaboration | essence and elaboration | MVD p.21 |
| 875 | विरक्ति | detachment | renunciation | SB p.5 |
| 878 | त्व सहित व्यवस्था | orderliness with '-ness' | inherent orderliness | MVD p.11 |
| 920 | निर्विरोध/निर्विरोधता | nonresistance, absence of resistance | harmony | MVD p.215 |
| 975 | वांछा | righteous need | need | MVD p.225 |
| 1005 | आप्लावन | inundation | immersion | MVD p.156 |
| 1019 | प्रदान | give | provide | MVD p.71 |
| 1038 | अभ्युदय | abhyudaya | comprehensive resolution (Abhyudaya) | MVD p.23 |
| 1057 | विवेचना | reasoning | analysis | MVD p.239 |
| 1090 | दरिद्र | destitute | poor | MVD p.23 |
| 1120 | अज्ञानी | commoner | ignorant | SB p.31 |
| 1128 | विहित | lawful | prescribed | MVD p.135 |
| 1133 | अकर्त्तव्य/अकर्तव्य | Undutiful | non-duty | MVD p.309 |
| 1141 | एकसूत्रता | cohesiveness | Integrality | MVD p.103 |
| 1160 | याचक | Pleader | seeker (of justice) | SB p.15 |
| 1165 | अनिवार्य | imperative | mandatory | MVD p.134 |
| 1167 | अपरिहार्य | indispensable | inevitable | SB p.51 |
| 1170 | निवारण | eradication | overcome | MVD p.233 |
| 1192 | सहायक | assistant | helpful | MVD p.103 |
| 1199 | प्रजा | public | citizens | MVD p.257 |
| 1222 | विद्वान | learned | scholar | MVD p.5 |
| 1224 | निश्चय | determination | certitude | SB p.8 |
| 1233 | पुष्टि | confirmation | growth | MVD p.112 |
| 1237 | हास/ह्रास | merriness | decline | MVD p.137 |
| 1314 | दीक्षा | ordination | initiation | MVD p.3 |
| 1322 | परिवार मूलक स्वराज्य व्यवस्था | family based self-governing system | family-based self-governance orderliness | MVD p.19 |
| 1359 | ताप | temperature | heat | MVD p.45 |
| 1374 | पूजा | veneration | worship | SB p.23 |
| 1403 | उपाय | solution, to take steps | path, means | MVD p.20 |
| 1491 | तपस्वी (in योगी/यति/सती/संत/तपस्वी/भक्त) | ascetic | seeker | MVD p.256 |

Two worth double-checking by hand: **row 1237 (हास/ह्रास)** — the agent found the glossary
appears to have conflated two distinct Hindi words (हास "mirth" vs ह्रास "decline") under one
entry; and **row 614/615 (धारक/वाहक)** — MVD suggests these were simply swapped in MD-Mapping.

## Special case NOT changed — needs your call

**परावर्तन / प्रत्यावर्तन (rows 607–608).** MD-Mapping currently has परावर्तन → "projection",
प्रत्यावर्तन → "reflection" — and MVD *confirms* that exact pairing (p.328, p.286), so no
conflict was flagged and nothing changed here.

But `KD-Karm-Darshan-English/README.md` records that you explicitly **settled the opposite**
for the KD working translation in July 2026: *paravartan = reflection, pratyavartan =
projection*, noting at the time that it differed from MD-Mapping. Now that MVD's usage is
confirmed (not just MD-Mapping's own guess), you may want to revisit that KD decision — or keep
it as an intentional KD-specific deviation. I didn't touch either file for this; flagging it for
your judgment call.

## Files

- `phase2_applied_report.json` — full machine-readable output (all 927 rows, all fields).
- `mvd_pairs.json` / `sb_pairs.json` — Phase 1 source pairs (unchanged).
- `match_terms.py`, `trim_candidates.py` — Phase 2 scripts, for re-running if MVD/SB text
  extraction improves or more source books are added.

# Karma Darshan Hindi Root Words & Terminology Mapping Audit

This audit extracts all Hindi root words, technical terms, and core concepts from *Karma Darshan* (source text & working translation), maps them against current translation glossaries (`MD-Mapping.xlsx` and `KD-Glossary-Additions.md`), and identifies terminology coverage and gaps.

## 1. Summary Statistics

- **Total Unique Terms Extracted:** `4260`
- **Mapped Terms:** `535` (`12.6%` coverage)
- **Unmapped Gaps:** `3725` (`87.4%` missing entries)

### Mapping Source Breakdown

| Source | Term Count | Percentage |
| :--- | :--- | :--- |
| `UNMAPPED_GAP` | 3725 | 87.4% |
| `MD-Mapping.xlsx` | 271 | 6.4% |
| `KD-Glossary-Additions.md` | 219 | 5.1% |
| `MD-Mapping.xlsx (Stemmed)` | 34 | 0.8% |
| `KD-MD-Contextual` | 5 | 0.1% |
| `KD-Glossary-Additions.md (Stemmed)` | 5 | 0.1% |
| `Compound-Derived` | 1 | 0.0% |

## 2. Key Mapped Terms (Sample)

| Hindi Term | Root Stem | English Translation Used | Source | Occurrences | Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| जीवन | जीवन | jeevan | MD-Mapping.xlsx | 237 | [Unconfirmed MVD/SB evidence found (MVD ~p.257) — needs human review; see MD-Mapping-Sources. All three MVD samples render जीवन in an ordinary/colloquial sense as plain 'life' (e.g. 'माता-पिता का जीवन' -> 'the life of a parent'), not as the technical transliterated 'jeevan' used elsewhere in the same translation; unclear whether this confirms the existing 'jeevan' gloss.] |
| आकार | आकार | shape | MD-Mapping.xlsx | 219 |  |
| परमाणु | परमाणु | Atom | MD-Mapping.xlsx | 175 | starved atom, hungry atom |
| प्रमाण | प्रमाण | evidence | MD-Mapping.xlsx | 170 | evidence, standard |
| ज्ञान | ज्ञान | Knowledge | MD-Mapping.xlsx | 157 | epistemological knowledge |
| अर्थ | अर्थ | wealth (contextual) | KD-Glossary-Additions.md | 134 | Per MD-Mapping ("resources"), rendered "wealth" for readability in the चतुर्वर्ग list and wealth/resource contexts ("अर्थ तन, मन, धन है"). CONTEXTUAL EXCEPTION: where अर्थ is used epistemically (e.g. "सम्पूर्ण अर्थ का पूर्ण अर्थ अनुभव ही है"), it means "meaning," not "wealth" — judge from context |
| अध्ययन | अध्ययन | study | MD-Mapping.xlsx | 133 | study |
| अनुभव | अनुभव | realisation | MD-Mapping.xlsx | 132 | realization |
| विकास | विकास | development | MD-Mapping.xlsx | 116 | configuration complete atom |
| आवश्यकता | आवश्यकता | need | MD-Mapping.xlsx | 114 | need |
| व्यवहार | व्यवहार | Behaviour | MD-Mapping.xlsx | 113 | worldly, local, localized |
| विज्ञान | विज्ञान | Science | MD-Mapping.xlsx | 104 | It is to know that time is but duration of activity.  Time has no independent existence from activity. |
| सहज | सहज | Natural | MD-Mapping.xlsx | 98 | [Unconfirmed MVD/SB evidence found (MVD ~p.55) — needs human review; see MD-Mapping-Sources. सहज is extremely high-frequency and context-dependent; samples show it absorbed into phrases (e.g. 'सहज उपासना' -> 'upasana', 'मानव सहज प्रयोजन' -> 'The Human Purpose') rather than rendered as one distinct word, so no clean term-level rendering could be pinned down.] |
| समाधान | समाधान | resolution | MD-Mapping.xlsx | 94 | within self |
| इकाई | इकाई | Unit | MD-Mapping.xlsx | 82 |  |
| क्षमता | क्षमता | capacity | MD-Mapping.xlsx | 81 |  |
| पूर्ण | पूर्ण | Complete | MD-Mapping.xlsx | 78 | The word refers to vyapak.  Use of ‘perfect’ is better than use of ‘complete’ – as perfect gives a qualitative sense, while complete gives a quantitative sense.  Suggestions:  Ideal, absolute, complete, perfect, prime, Omni-perfection |
| धर्म | धर्म | dharma | MD-Mapping.xlsx | 77 |  |
| विचार | विचार | thought | MD-Mapping.xlsx | 76 | thought |
| सार्थक | सार्थक | meaningful | MD-Mapping.xlsx | 76 |  |
| विवेक | विवेक | wisdom | KD-Glossary-Additions.md | 73 | Per MD-Mapping ("wisdom"); KD 2 chapter subtitle ("उपासना – विवेक" → "Upasana – Wisdom") |
| वैभव | वैभव | grandeur | MD-Mapping.xlsx | 72 | expanse, greatness, grandeur,  magnificence |
| परम्परा | परम्परा | tradition | MD-Mapping.xlsx | 71 | [New row added 2026-07-08 from MVD/SB reconciliation.] Recurring key term for social/human continuity of practice, e.g. 'जागृत मानव परम्परा' rendered 'the awakened human tradition' (MVD p.300). |
| प्रयोग | प्रयोग | experimentation | MD-Mapping.xlsx | 68 |  |
| पद | पद | Plane | MD-Mapping.xlsx | 67 | hindi defin: astitva mein pran pad, bhranti pad, dev pad, divya pad chakr ke roop me nitya prakashan.  State of existence, development. |
| लक्ष्य | लक्ष्य | goal | MD-Mapping.xlsx | 67 |  |
| दर्शन | दर्शन | the seeing, the seen, seeing/philosophy | KD-Glossary-Additions.md | 65 | KD 3.17: the seer-triad parallel to ज्ञान/ज्ञाता/ज्ञेय; left transliterated with bracketed gloss on first use, not in MD-Mapping under these exact senses |
| बल | बल | Strength, Force | MD-Mapping.xlsx | 65 | Society |
| सम्पूर्ण | सम्पूर्ण | whole, all | MD-Mapping.xlsx | 63 |  |
| जीव | जीव | living beings, jeeva, animal | MD-Mapping.xlsx | 61 |  |
| प्रवाह | प्रवाह | flow | MD-Mapping.xlsx | 60 |  |
| सूत्र | सूत्र | sutra, essence, maxim | MD-Mapping.xlsx | 59 | Maxim : Sentences which communicate the maximum (complete) meaning using minimum words |
| समाज | समाज | Society | MD-Mapping.xlsx | 59 |  |
| आवश्यक | आवश्यक | necessary | MD-Mapping.xlsx | 59 | आवश्यकता = need (already done) |
| बोध | बोध | enlightenment | MD-Mapping.xlsx | 59 | awareness |
| रहना | रहना | abiding | MD-Mapping.xlsx | 58 | becoming |
| सत्य | सत्य | truth | MD-Mapping.xlsx | 57 |  |
| परिणाम | परिणाम | result | KD-Glossary-Additions.md | 52 | REALIGNED 2026-07-08 with MVD/SB: श्रम-गति-परिणाम → "Effort – Motion – Result" (MVD/SB title-page Principle; MVD p.11). Both फल and bare परिणाम render as "result" in English — acceptable overlap where Hindi also overlaps (फल-परिणाम compounds collapse to "result" rather than "result-consequence"). Idiomatic connectors ("as a result of X") unchanged. Retrofitted corpus-wide across all 9 translation files on 2026-07-08 remediation pass |
| सुख | सुख | happiness | MD-Mapping.xlsx | 52 | happiness |
| उपासना | उपासना | Upasana (worship) | KD-Glossary-Additions.md | 51 | KD 2 chapter title. Per MD-Mapping ("worship, upasana") and SB's own English rendering (SB p.23: "worship, archana, yoga, sadhana, and upasana" — SB itself leaves उपासना transliterated rather than translating it). Kept transliterated as "upasana" throughout, glossed "(worship)" on first use, per this project's practice for the book's central chapter-2 term |
| व्यापक | व्यापक | Omnipresent, Omnipresence | MD-Mapping.xlsx | 46 | Omni-pervasive, omni-present;  “All” indicates units.  How about “Omni” alone for vyapak vastu?  Hindi defn: “sarvatr vidyman satta”.  English defn:  that which is present everywhere.  Omnipresent. |
| उपयोग | उपयोग | use | MD-Mapping.xlsx | 42 | Usefulness, utility, utilization |
| प्रयोजन | प्रयोजन | Purpose | MD-Mapping.xlsx | 42 |  |
| योग्य | योग्य | fit / worthy / suitable | MD-Mapping.xlsx | 41 | Phase 4 curated: योगानुभूति योग्य विकास = development fit for realisation of yog; distinct from योग्यता (ability). |
| गुण | गुण | property | KD-Glossary-Additions.md | 41 | Settled per Raghava (2026-07-08): "property," NOT "quality." MD-Mapping carries both readings (गुण = "properties" as a noun; गुण = "qualitative" as an adjective) — for KD's recurring रूप/गुण/स्वभाव/धर्म (form/property/essential nature/dharma) list of the four orders' predominant traits, and for chapter 3.10's title, गुण is a noun and takes "property." Retroactively corrected in KD-Karm-Darshan-English.md §3.4–3.6, KD-Karm-Darshan-English.md §3.11–3.12, and KD-Karm-Darshan-English.md §3.13–3.15 (previously translated "quality") on 2026-07-08. Exception: the adjectival compound गुणात्मक परिवर्तन keeps MD-Mapping's own established "qualitative change/transformation" (KD 3.9) — "property-al" does not read in English, and MD-Mapping treats this compound as a separate row from bare गुण |
| विश्वास | विश्वास | Trust, Confidence | MD-Mapping.xlsx | 41 | courteousness: working together, sharing together, supporting one another |
| फल | फल | result | KD-Glossary-Additions.md | 40 | Settled per Raghava (2026-07-08), superseding this project's earlier "fruit" — "phal means result of the action (karma)." Retrofitted in KD-Karm-Darshan-English.md on 2026-07-08 wherever फल stood alone (not फलन=fruition, not a फल-परिणाम compound, not literal fruit as food). See परिणाम for the resolved collision and the फल-परिणाम compound convention |
| ध्यान | ध्यान | attention, attender, object of attention | KD-Glossary-Additions.md | 39 | KD 3.17: not in MD-Mapping under this triad; compositional, parallel structure to ज्ञान/ज्ञाता/ज्ञेय |
| मूल्य | मूल्य | Values | MD-Mapping.xlsx | 39 | [Unconfirmed MVD/SB evidence found (MVD ~p.269 (unclear)) — needs human review; see MD-Mapping-Sources. MVD samples render मूल्य inconsistently (once as 'evaluation' in a labour-value context, headings truncated elsewhere); no clean single-word anchor found.] |
| इच्छा | इच्छा | desire | MD-Mapping.xlsx | 39 | desire, intent, will, wish |

## 3. High-Priority Gaps & Unmapped Terms

The following terms occur in Karma Darshan texts but are currently missing explicit entries in `KD-Glossary-Additions.md` or `MD-Mapping.xlsx`:

| Hindi Term | Root Stem | Occurrences in Text | Status / Recommendation |
| :--- | :--- | :--- | :--- |
| वितत | वितत | 295 | Needs evaluation & glossary entry |
| व्यवथिा | व्यवथिा | 243 | Needs evaluation & glossary entry |
| प्रमाणिि | प्रमाणिि | 238 | Needs evaluation & glossary entry |
| परष्ट | परष्ट | 215 | Needs evaluation & glossary entry |
| क्रम | क्रम | 186 | Needs evaluation & glossary entry |
| हत | हत | 186 | Needs evaluation & glossary entry |
| कि्रया | कि्रया | 180 | Needs evaluation & glossary entry |
| जागृस्ि | जागृस्ि | 166 | Needs evaluation & glossary entry |
| र्िीि | र्िीि | 166 | Needs evaluation & glossary entry |
| दर्मन | दर्मन | 162 | Needs evaluation & glossary entry |
| सहअतिित्व | सहअतिित्व | 161 | Needs evaluation & glossary entry |
| कर्म | कर्म | 158 | Needs evaluation & glossary entry |
| रुप | रुप | 157 | Needs evaluation & glossary entry |
| तिथतत | तिथतत | 148 | Needs evaluation & glossary entry |
| वतिु | वतिु | 144 | Needs evaluation & glossary entry |
| िण | िण | 140 | Needs evaluation & glossary entry |
| हम | हम | 134 | Needs evaluation & glossary entry |
| गतत | गतत | 132 | Needs evaluation & glossary entry |
| पूर्वक | पूर्वक | 121 | Needs evaluation & glossary entry |
| िक | िक | 113 | Needs evaluation & glossary entry |
| समझ | समझ | 110 | Needs evaluation & glossary entry |
| मूल | मूल | 104 | Needs evaluation & glossary entry |
| कायश | कायश | 100 | Needs evaluation & glossary entry |
| अर्थात् | अर्थात् | 90 | Needs evaluation & glossary entry |
| सहिि | सहिि | 78 | Needs evaluation & glossary entry |
| कमश | कमश | 78 | Needs evaluation & glossary entry |
| निशि्चत | निशि्चत | 78 | Needs evaluation & glossary entry |
| प्रत्यत | प्रत्यत | 78 | Needs evaluation & glossary entry |
| जानने | जानने | 78 | Needs evaluation & glossary entry |
| संपन्न | संपन्न | 77 | Needs evaluation & glossary entry |
| वियं | वियं | 76 | Needs evaluation & glossary entry |
| अतिित्व | अतिित्व | 74 | Needs evaluation & glossary entry |
| अधिक | अधिक | 74 | Needs evaluation & glossary entry |
| जागृत | जागृत | 71 | Needs evaluation & glossary entry |
| सिंसात | सिंसात | 68 | Needs evaluation & glossary entry |
| विभाव | विभाव | 67 | Needs evaluation & glossary entry |
| प्रत्येक | प्रत्येक | 66 | Needs evaluation & glossary entry |
| सकिा | सकिा | 66 | Needs evaluation & glossary entry |
| परिंपरा | परिंपरा | 65 | Needs evaluation & glossary entry |
| तात्पर्य | तात्पर्य | 65 | Needs evaluation & glossary entry |
| भौतिक | भौतिक | 64 | Needs evaluation & glossary entry |
| अणु | अणु | 64 | Needs evaluation & glossary entry |
| भागीदािी | भागीदािी | 64 | Needs evaluation & glossary entry |
| स् | स् | 62 | Needs evaluation & glossary entry |
| ओि | ओि | 61 | Needs evaluation & glossary entry |
| िहिे | िहिे | 61 | Needs evaluation & glossary entry |
| वाले | वाले | 60 | Needs evaluation & glossary entry |
| दूसिे | दूसिे | 60 | Needs evaluation & glossary entry |
| प्रकि्रया | प्रकि्रया | 58 | Needs evaluation & glossary entry |
| आिा | आिा | 58 | Needs evaluation & glossary entry |
| अिंर् | अिंर् | 58 | Needs evaluation & glossary entry |
| िासायनिक | िासायनिक | 57 | Needs evaluation & glossary entry |
| बात | बात | 57 | Needs evaluation & glossary entry |
| क्योंकत | क्योंकत | 57 | Needs evaluation & glossary entry |
| इसमें | इसमें | 57 | Needs evaluation & glossary entry |
| प्रवृस्ि | प्रवृस्ि | 56 | Needs evaluation & glossary entry |
| रि्िा | रि्िा | 55 | Needs evaluation & glossary entry |
| सिंपूर्ण | सिंपूर्ण | 54 | Needs evaluation & glossary entry |
| वाली | वाली | 54 | Needs evaluation & glossary entry |
| विद्युि | विद्युि | 54 | Needs evaluation & glossary entry |

---
*Report auto-generated by `Scripts/_extract_kd_hindi_terms.py`.*
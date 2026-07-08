# Karm Darshan — Working English Translation (KD-Karm-Darshan-English)

Working English translation of *Manav Karm Darshan* (v5) by Shri A. Nagaraj, produced from page images because the source PDF's embedded text layer is corrupted. **These are machine-assisted working translations, not published translations** — verify against the Hindi original (`../KD-karm darshan v5.pdf`) before quoting in publications. Technical terms follow the conventions in `../MD-Mapping.xlsx`; new KD-specific terms and judgment calls are catalogued in `KD-Glossary-Additions.md` and in `KD-Translation-Glossary.xlsx`.

## Canonical source

| File | Content | Printed / PDF pages |
| :---- | :---- | :---- |
| [`KD-Karm-Darshan-English.md`](KD-Karm-Darshan-English.md) | Full working translation (front matter + chapters 1–3) | PDF pp. 1–25 (front matter); printed pp. 1–153 (body); blank placeholders at printed pp. 51–52 (p. 50 via natural pagination) |
| [`KD-Karm-Darshan-English.pdf`](KD-Karm-Darshan-English.pdf) | Generated PDF (182 pages — aligned with Hindi PDF page count) | Same markers as markdown |
| [`_page-images/`](_page-images/) | Hindi source page renders for side-by-side verification | 182 PNGs (`p{pdf}_print{printed}.png`) |

## Section index (in `KD-Karm-Darshan-English.md`)

| Section | Printed pages |
| :---- | :---- |
| Front matter (*vikalp*, मूल तत्व outline, author's declaration, gratitude, foreword, TOC) | PDF pp. 1–25 |
| Chapter 1 — कर्म (Karma) | 1–29 |
| Chapter 2 — उपासना (Upasana / Worship) | 30–49 |
| *(blank placeholders — not translated)* | 50–52 |
| Chapter 3 — Coexistence-ist Science | 53–153 |
| 3.1–3.3 Atomic structure and development | 53–63 |
| 3.4–3.6 Mental well-being, coexistence stability | 64–72 |
| 3.7–3.8 Heat, earth balance, state–motion | 73–87 |
| 3.9–3.10 Quantity; property, essential nature, dharma | 88–102 |
| 3.11–3.12 Force–power; projection–reflection | 102–118 |
| 3.13–3.15 Pressure, wave, EM force; place/direction/distance; time | 118–135 |
| 3.16–3.18 Life-state, knower, seer–doer | 135–153 |

Printed p.153 ends with the book's closing benediction (*nityam yātu śubhodayam*). Printed pp.154–155 are publisher back matter (not book content). The "मध्यस्थ दर्शन के मूल तत्व" outline reuses Rakesh Gupta's published MVD English (MVD pp. 11–19).

## Maintenance scripts

From the repo root:

```powershell
# Render Hindi PDF pages to _page-images/ (150 dpi; skip existing unless --force)
python Scripts/_kd_render_page_images.py

# Rebuild KD-Translation-Glossary.xlsx from MD-Mapping + KD-Glossary-Additions.md
python Scripts/_kd_build_glossary_xlsx.py

# Regenerate English PDF
python Scripts/_convert_to_pdf.py "References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Karm-Darshan-English.md"
node Scripts/_html_to_pdf.js "References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Karm-Darshan-English.html"
```

**Page-image naming:** `p{pdf:03d}_print{printed:03d}.png` where `printed = pdf page` for PDF pages 1–25 (front matter), and `printed = pdf page − 25` for PDF pages 26+ (body).

**Blank PDF pages:** Printed pp. 51–52 are marked `[blank p. NN]` in the markdown so the English PDF stays page-aligned with the Hindi original for side-by-side verification (ch. 3 title / sub-TOC in Hindi). Printed p. 50 is blank in the Hindi original; the English PDF leaves it empty via natural pagination after the ch. 2 closing benediction (`[p. 50]` marker only).

## Conventions

Printed page numbers appear as `[p. NN]` markers (printed = PDF page − 25 for body content). Untranslatable technical terms carry italic transliteration on first occurrence per chapter. Two fixed conventions: ***āvesh/āveshit* is translated contextually** — "charge/charged" where the text concerns the positive–negative (धन-ऋणात्मक / sam–visham) imbalance of atoms, "excitation/excited" where it contrasts a unit's neutral/natural state with a disturbed one (aveshit gati vs swabhav gati, overfull atoms, heated bodies). SB's published English uses "charge" for both senses but glosses the state sense itself at p. 257 ("excited (charged) state"); MD-Mapping carries both readings (आवेश = "agitation, charge, excitement"; आवेशित गति = "agitated state, excited state"). And ***śram* = effort** (MD-Mapping notes: "We are using 'effort' for shram in the sense of shram-gati-parinam"; "labour" only in economic compounds like श्रम मूल्य = evaluation of labour — updated 2026-07-08 per MVD, not yet encountered in translated KD text). Re-settled (per Raghava, 2026-07-08, superseding the July 2026 KD-specific choice): ***paravartan* = projection, *pratyavartan* = reflection** — aligned with MD-Mapping's row, which MVD independently confirms (paravartan=projection, MVD p.328; pratyavartan=reflection, MVD p.286). Chapter 3.12 (now titled "Projection–Reflection") and all matching instances in 3.7's heat-reflection passages were swapped accordingly on 2026-07-08; the one exception is the "celestial light is reflected (imaged)" line in 3.7 (p.83), which translates a different word (*pratibimbit*, "imaged"), not paravartan, and was left untouched.

Two more contextual exceptions found while reconciling against MVD/SB (2026-07-08), both kept as the KD chapters already have them, in preference to the flatter global MD-Mapping rendering: ***tāp* = "temperature", distinct from *ūshmā* = "heat"** — KD 3.7 (pp. 74–76) uses both words contrastively in the same passage (heat as the causal effect of burning; temperature as the measured degree recognised only by humans), so collapsing both to "heat" (MD-Mapping's current global row for tāp) would erase a distinction the source text is actively drawing. And ***vāstavikatā* = "actuality", distinct from *yathārthatā* = "reality"** — KD 3.1 and 3.7 both list "reality, actuality, and truth/verity" as three distinct terms in one breath; MD-Mapping's global row now says vāstavikatā = "reality", which would collide with yathārthatā's existing "reality" in the same list.

Settled per Raghava (2026-07-08): ***guṇa* = "property", NOT "quality"** — the noun गुण, as it recurs in KD's रूप/गुण/स्वभाव/धर्म (form/property/essential nature/dharma) list of the four orders' predominant traits and as chapter 3.10's title, takes "property," aligning with one of MD-Mapping's two existing रूप rows (the other, "qualitative," is the adjectival reading and does not apply to this noun usage). The compound गुणात्मक परिवर्तन (KD 3.9) is a documented exception, kept as "qualitative change/transformation" per MD-Mapping's own separate row for that adjectival compound.

Settled per Raghava (2026-07-08 remediation): ***parināma* / bare *parinām* = "result"**, aligned with MVD/SB **Effort – Motion – Result** for श्रम-गति-परिणाम — both फल and bare परिणाम render as "result" in English (acceptable overlap where Hindi overlaps; फल-परिणाम compounds collapse to "result"). Idiomatic "as a result of" unchanged. Retrofitted corpus-wide on 2026-07-08.

Settled per Raghava (2026-07-08): ***sañcetanā* = "awareness"**

Settled per Raghava (2026-07-08 remediation): ***svabhāv* = "essential nature"**, matching MVD and Studies (supersedes the earlier project-specific "disposition")

Settled per Raghava (2026-07-08 remediation): ***abhyudaya* = "comprehensive resolution"**, aligned with MVD p.23 (supersedes "well-being" / "rise")

Settled per Raghava (2026-07-08 remediation): ***sammat* = "aligned"**, aligned with logic/justice mappings (supersedes "approved") — overrides MD-Mapping/SB's "Humane Consciousness" for this project; keep चेतना/जीव चेतना as "consciousness." Audit: replace "human consciousness" with "awareness" only where Hindi is संचेतना (KD 3.4 p.69); keep "human consciousness" for मानव चेतना (KD 2, 3.9).

Chapter 3's closing triads (3.16–3.18) introduce several three- and five-term Sanskrit sets that are largely left transliterated with bracketed glosses on first use, following MD-Mapping where it has an entry (दृष्टा=Seer, ज्ञाता=knower, साध्य=aim, साधक=the seeker, साधन=the means) and compositional/judgment-call renderings where it doesn't (कर्त्ता=doer, भोक्ता=enjoyer, दृश/दृश्य/दर्शन=the seeing/the seen/seeing, ध्यान/ध्याता/ध्येय=attention/attender/object of attention). See `KD-Glossary-Additions.md` for the full set and reasoning.

Chapter 1 (Karma) settles several more terminology decisions, all judgment calls, some of them overriding MD-Mapping: ***संस्कार* = left transliterated as "*sanskar*"**, distinct from ***संस्कृति* = "culture"*** (the two appear together constantly, e.g. "संस्कार, संस्कृति व सभ्यता"); ***अभीष्ट* = "desire"** (per Raghava, 2026-07-08, superseding this project's earlier "desideratum") — note this now overlaps in English with इच्छा (the general term for desire), distinguish by context; ***साध्य* = "aim"** kept distinct from अभीष्ट (the source glosses them together as "साध्य (अभीष्ट)," rendered "the aim (the desire)"); ***अनुभूति* = "experiencing"**, distinct from ***अनुभव* = "realisation"*** (both are "realisation" per MD-Mapping, but अनुभव is entrenched across chapter 3 and the two words appear near each other throughout chapter 1); ***काम* = "*kama*" (desire)**, kept transliterated rather than MD-Mapping's "lust," since chapter 1 uses it only in the classical मोक्ष/धर्म/काम/अर्थ (moksha/dharma/kama/wealth) list; ***कायिक* = "physical"** (per Raghava, 2026-07-08, matching MD-Mapping, superseding this project's earlier "bodily") — now overlaps in English with भौतिक (also "physical," the material/physical-world sense), distinguish by context; and ***कृत, कारित, अनुमोदित* = "done, caused, intended"** (per Raghava, 2026-07-08, superseding "done, caused-to-be-done, and approved"). See `KD-Glossary-Additions.md` for the full reasoning on each.

Three systematic errors were found and corrected across the translation on 2026-07-08, after checking KD phrases against MVD's actual sentence-level translations (not just MD-Mapping's row-level gloss): ***दर्शन* (bare, or in "X दर्शन (ज्ञान)" / "दर्शन-क्षमता" compounds) = "the holistic view (of X)"**, not transliterated "darshan" — MD-Mapping has a direct row (दर्शन = "Holistic view, Worldview, Philosophy") and MVD confirms it verbatim; excluded from this fix are the proper noun "Madhyasth Darshan," the दृश/दृश्य/दर्शन seer-triad sense (KD 3.17), and the verb "X का दर्शन करना" = "to behold X." ***मानवीयतापूर्ण* (X) / *अतिमानवीयतापूर्ण* (X) = "humane (X)" / "higher-humane (X)"**, a plain adjective, not "X filled/replete with humaneness" — confirmed by MD-Mapping's मानवीयता पूर्ण आचरण = "Humane Conduct" and by MVD's own running prose and glossary ("मानवीयतापूर्ण व्यवहार" → "Humane Behaviour," MVD p.34); not extended to other "-पूर्ण" compounds on different roots. ***जीवन ज्ञान* = "knowledge of jeevan"**, not "jeevan knowledge" — keeps the "knowledge of X" pattern parallel with the other two terms of the recurring three-part formula ("अस्तित्व दर्शन ज्ञान, जीवन ज्ञान, मानवीयतापूर्ण आचरण ज्ञान" → "knowledge of the holistic view of existence, knowledge of jeevan, knowledge of humane conduct"), confirmed twice in MVD (p.3, p.259). See `TRANSLATION-PLAN.md`'s "Systematic errors found and corrected" section and the matching `KD-Glossary-Additions.md` rows.

# Karm Darshan — Working English Translation (KD-Karm-Darshan-English)

Working English translation of *Manav Karm Darshan* (v5) by Shri A. Nagaraj, produced from page images because the source PDF's embedded text layer is corrupted. **These are machine-assisted working translations, not published translations** — verify against the Hindi original (`../KD-karm darshan v5.pdf`) before quoting in publications. Technical terms follow the conventions in `../MD-Mapping.xlsx`; new KD-specific terms and judgment calls are catalogued in `KD-Glossary-Additions.md` and in `KD-Translation-Glossary.xlsx`.

## Canonical source

| File | Content | Printed / PDF pages |
| :---- | :---- | :---- |
| [`KD-Karm-Darshan-English.md`](KD-Karm-Darshan-English.md) | Full working translation (front matter + chapters 1–3) | PDF pp. 1–25 (front matter); printed pp. 1–153 (body) |
| [`KD-Karm-Darshan-English.pdf`](KD-Karm-Darshan-English.pdf) | Generated PDF (182 pages — aligned with Hindi PDF page count) | Same markers as markdown |
| [`KD-Karm-Darshan-Hindi-English.pdf`](KD-Karm-Darshan-Hindi-English.pdf) | Interleaved Hindi-then-English PDF for side-by-side reading | 364 pages (182 × 2) |
| [`_page-images/`](_page-images/) | Hindi source page renders for side-by-side verification | 182 PNGs (`p{pdf}_print{printed}.png`) |

### Never translate or verify from the PDF's text layer

Translate and quote-check from `_page-images/` (or a fresh PyMuPDF render), never from
text extracted out of `../KD-karm darshan v5.pdf`. Its embedded text layer is
systematically corrupt, and the corruption is silent — the output looks like ordinary
Hindi rather than mojibake, so a bad excerpt will pass unnoticed into a translation or
a quotation.

Re-verified 2026-07-27 with PyMuPDF: 24 of the first 120 pages carry the malformed
`पिमाणु` where the source reads `परमाणु`, against only 3 pages with the correct form.
Page 6 extracts as `सहअस्तित्व में ही :- पिमाणु में स्वकासक्रम…`.

This matters most for the repo's **`pdf-mcp`** server (configured in both
`.cursor/mcp.json` and `opencode.json` as `python -m pdf_mcp.server`), because it is
present, it works, and it looks authoritative:

| Tool | Use for KD? | Why |
|---|---|---|
| `pdf_read_pages`, `pdf_search`, `pdf_read_all` | **No** | Faithfully return the corrupt text layer. Headings are sometimes clean; body paragraphs are not. |
| `pdf_read_pages` with `ocr=true` | **No** | OCR is not installed on this server (`server_info` reports `ocr.available: false`), and the pages already carry a native text layer, so OCR would not auto-trigger anyway. |
| `pdf_search` | Page numbers only | Useful to locate a section, but treat the returned excerpts as unusable wording. |
| `pdf_render_pages` | Spot checks only | Correct visual Hindi, but capped at 5 pages per call and returns large inline PNGs. Prefer `_page-images/`. |

Its `pages` argument must be a comma-separated **string** (`"88,89"`), not a JSON array.

## Section index (in `KD-Karm-Darshan-English.md`)

| Section | Printed pages |
| :---- | :---- |
| Front matter (*vikalp*, मूल तत्व outline, author's declaration, gratitude, foreword, TOC) | PDF pp. 1–25 |
| Chapter 1 — कर्म (Karma) | 1–29 |
| Chapter 2 — उपासना (Upasana / Worship) | 30–49 |
| Chapter 3 transition (blank p. 50; title + sub-TOC pp. 51–53) | 50–53 |
| Chapter 3 — Coexistence-ist Science | 54–153 |
| 3.1–3.3 Atomic structure and development | 54–63 |
| 3.4–3.6 Mental well-being, coexistence stability | 64–72 |
| 3.7–3.8 Heat, earth balance, state–motion | 73–87 |
| 3.9–3.10 Quantity; property, essential nature, dharma | 88–102 |
| 3.11–3.12 Strength–power; projection–reflection | 102–118 |
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

# Legacy PDF-text-layer extractor is intentionally disabled: the Hindi PDF's
# embedded text is corrupt. Use rendered source-page images for Hindi checks.

# Audit mapped terms against Rakesh Gupta's MVD / SB / JV translations
python Scripts/_review_rakesh_translations.py

# Regenerate English PDF
python Scripts/_convert_to_pdf.py "References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Karm-Darshan-English.md"
node Scripts/_html_to_pdf.js "References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Karm-Darshan-English.html"

# Build interleaved Hindi–English PDF (requires both PDFs at 182 pages)
python Scripts/_kd_build_hindi_english_pdf.py
```

**Page-image naming:** `p{pdf:03d}_print{printed:03d}.png` where `printed = pdf page` for PDF pages 1–25 (front matter), and `printed = pdf page − 25` for PDF pages 26+ (body).

**Chapter 3 transition (printed pp. 50–53):** Printed p. 50 is `[blank p. 50]`; pp. 51–53 carry the chapter 3 title outline and detailed sub-TOC (with Hindi printed page numbers preserved in the table). Section 3.1 prose begins at printed p. 54 (PDF p. 79).

## Conventions

**Editorial readability pass (2026-08-23).** A ten-page pilot on printed pp. 8, 15, 31, 39, 43, 70, 102, 119, 133, and 147 established the editorial method, which was then applied chapter by chapter across the complete translated body. The pass preserves settled MVD/JV/SB terminology while replacing mechanical Hindi-to-English syntax such as repeated "this itself is," "is found," and "comes to be," visible grammatical insertions in square brackets, and ad hoc hyphenated compounds. Technical "in the form of" constructions are retained where they express an actual classification or equivalence rather than translation scaffolding. Logical sequence, negation, exclusivity, enumerations, and technical distinctions remain source-controlled. Representative high-density revisions in every chapter were checked directly against rendered Hindi source pages. Two fidelity corrections identified during the pilot remain recorded: KD 2 p.43's निर्भरतापूर्ण क्षमता is **a capacity dependent upon nature**, not the former "free-from-delusion capacity"; and KD 3.11 p.102 uses **strength–power** for bare बल–शक्ति while retaining **force** in the physical claim that science treats pressure as force.

**Translation-policy hierarchy.** Rakesh Gupta's published MVD, SB, and JV translations, together with `MD-Mapping.xlsx`, remain the default authority for English terminology. Departures are made only as explicit, documented project decisions approved by Raghava; they are not precedents for changing unrelated terms. The approved exceptions are recorded term by term in `KD-Glossary-Additions.md` and `KD-Translation-Glossary.xlsx`. They currently include bare/general/ontological ***bal* (बल) = "strength"** — the standing capacity present in a unit or *jeevan* faculty — rather than Rakesh's more general "force"; ***poshan* (पोषण) = "nourishment"** where MD-Mapping's bare row has "nurturing"; ***prayog* (प्रयोग) = "application / apply"** where Rakesh frequently uses "experiment / experimentation"; and bare ***bhog* (भोग) = "enjoyment"** where MVD often uses "indulgence / sensory enjoyments." Named physical or interaction terms such as magnetic force, electromagnetic force, attraction force, and flow force retain **"force"**; ***bal sampanna / bal sampannatā* (बल सम्पन्न / बल सम्पन्नता)** retain **"forceful / forcefulness."** Contextual distinctions under each approved term remain in force.

**Rakesh-alignment sweep (2026-08-23).** Confirmed terminology drift was corrected corpus-wide: ***sadupyog* (सदुपयोग) = "right-use"**; the four ontological *avasthā* terms are **material / biological / animal / knowledge order**; ***prāṇakośa* (प्राणकोष) = "biological cell"**; ***vivek* (विवेक) = "wisdom"**; ***vyavasāy* (व्यवसाय) = "vocation"**; ***dayā / kṛpā / karuṇā* (दया / कृपा / करुणा) = "kindness / grace / compassion"**; ***vyāpak / vyāpak vastu* (व्यापक / व्यापक वस्तु) = "Omnipresence / omnipresent reality"**; and ***dev mānav* (देव मानव) = "deific human"**. X-त्रय compounds also retain Rakesh's fixed **X-trio** pattern. These are alignment corrections, not exceptions to the hierarchy.

**Follow-up terminology decisions (2026-08-23).** पोषण is **nourishment**; अनुकूल is **aligned** when one faculty, activity, or result functions in relation to another (while environmental अनुकूल remains **favourable**); प्रयास / प्रयत्न is **endeavour**, reserving **effort** for श्रम in Effort–Motion–Result; प्रयोग is **application / apply**; and द्वेष is **malice**, following MVD's direct definition and remaining distinct from घृणा = **hatred**. Bare भोग remains **enjoyment** by explicit project decision; फल भोगना is **experience consequences/results**, भोक्ता is **enjoyer**, and उपभोग is **consumption**. KD 1 p.18 uses **study of yoga** for both योगाभ्यास and योग्याभ्यास by explicit project decision, keeping **yoga** transliterated rather than translating the technical term as "union." Source-image review of KD 1 pp.4–6 also replaced truth-/desire-/object-investigation with **truth-oriented / motive-oriented / instincts-oriented exploration**, and **investigation-trio** with **exploration-trio**. The exact compounds are absent from MVD/JV, so this is a compositional alignment to their established सत्य / ऐषणा / विषय vocabulary; the related ऐषणा-त्रय is now aligned to Rakesh's **motive-trio**. KD 2 pp.40–41 now aligns तदाकार with MVD and MD-Mapping as **absolute-resonance**, using the relational grammar "brought into / attaining absolute-resonance with"; this supersedes **take-/taking-the-form-of**.

**Further Rakesh-alignment corrections (2026-08-23).** The text now uses **brain** for मेधस; **magnetism** for चुम्बकीयता; **field** for प्रभाव क्षेत्र; **irreversible transition / irreversibility** for संक्रमण / संक्रमणीयता; **expanse** for विस्तार; **outcome** for फलन; **existent state** for यथास्थिति; **satisfaction** for तृप्ति; **vitalising / devitalising** for सारक / मारक; **object of knowledge** for ज्ञेय; **seer / scene / worldview** for दृश / दृश्य / दर्शन; **concentration / one who concentrates / object of concentration** for ध्यान / ध्याता / ध्येय; transliterated ***Adhyatma-vada / Adhidaivika-vada / Adhibhautika-vada***; **mortality** for नश्वरत्व; **deific / elemental / divine self** for देवात्मा / भूतात्मा / दिव्यात्मा; **supreme order** for प्रभुसत्ता; and **dispassion / detachment / supreme-detachment** for विराग / वैराग्य / पर-वैराग्य. KD 3.13's molecule-to-molecule wave context uses **propagated** for अनुप्राणित by explicit project decision, since MVD's “invigorated/inspired” does not fit that physical context. The technical क्षमता / योग्यता / पात्रता trio remains **capacity / ability / receptivity**, because these qualities underlie recognition of relationships and evaluation; **worthiness** for पात्रता is confined to KD 3.10's reciprocal kindness/grace/compassion definition.

**Deferred terminology review (marked 2026-08-23).** The current contextual renderings of आवेश, विन्यास, अनुभूति, काम, अर्थ, and the कासा / आकूति / मेधा triad are retained but explicitly marked for reconsideration in the glossary and alignment audit. मात्रा remains on the existing manual-review list. No further change to these terms has been inferred in this pass.

**KD 2 p.31 source-image review (2026-08-23).** जीवन-पुंज is **jeevan-cloud**, aligning with MVD's explicit **Jeevan-cloud (*punj*)** and superseding the former **jeevan-cluster**. प्राण वायु is retained as the single transliterated technical term ***pranavayu*** by explicit project decision, rather than translated as **life-breath** or separated as *pran vayu*. The surrounding deity passage was also revised directly against the Hindi page image for clearer classification, agency, and signal language without changing its doctrinal content.

Printed page numbers appear as `[p. NN]` markers (printed = PDF page − 25 for body content). Untranslatable technical terms carry italic transliteration on first occurrence per chapter. Two fixed conventions: ***āvesh/āveshit* is translated contextually** — "charge/charged" where the text concerns the positive–negative (धन-ऋणात्मक / sam–visham) imbalance of atoms, "excitation/excited" where it contrasts a unit's neutral/natural state with a disturbed one (aveshit gati vs swabhav gati, overfull atoms, heated bodies). SB's published English uses "charge" for both senses but glosses the state sense itself at p. 257 ("excited (charged) state"); MD-Mapping carries both readings (आवेश = "agitation, charge, excitement"; आवेशित गति = "agitated state, excited state"). And ***śram* = effort** (MD-Mapping notes: "We are using 'effort' for shram in the sense of shram-gati-parinam"; "labour" only in economic compounds like श्रम मूल्य = evaluation of labour — updated 2026-07-08 per MVD, not yet encountered in translated KD text). Re-settled (per Raghava, 2026-07-08, superseding the July 2026 KD-specific choice): ***paravartan* = projection, *pratyavartan* = reflection** — aligned with MD-Mapping's row, which MVD independently confirms (paravartan=projection, MVD p.328; pratyavartan=reflection, MVD p.286). Chapter 3.12 (now titled "Projection–Reflection") and all matching instances in 3.7's heat-reflection passages were swapped accordingly on 2026-07-08; the one exception is the "celestial light is reflected (imaged)" line in 3.7 (p.83), which translates a different word (*pratibimbit*, "imaged"), not paravartan, and was left untouched.

Two more contextual exceptions found while reconciling against MVD/SB (2026-07-08), both kept as the KD chapters already have them, in preference to the flatter global MD-Mapping rendering: ***tāp* = "temperature", distinct from *ūshmā* = "heat"** — KD 3.7 (pp. 74–76) uses both words contrastively in the same passage (heat as the causal effect of burning; temperature as the measured degree recognised only by humans), so collapsing both to "heat" (MD-Mapping's current global row for tāp) would erase a distinction the source text is actively drawing. And ***vāstavikatā* = "actuality", distinct from *yathārthatā* = "reality"** — KD 3.1 and 3.7 both list "reality, actuality, and truth/verity" as three distinct terms in one breath; MD-Mapping's global row now says vāstavikatā = "reality", which would collide with yathārthatā's existing "reality" in the same list.

Settled per Raghava (2026-07-08): ***guṇa* = "property", NOT "quality"** — the noun गुण, as it recurs in KD's रूप/गुण/स्वभाव/धर्म (form/property/essential nature/dharma) list of the four orders' predominant traits and as chapter 3.10's title, takes "property," aligning with one of MD-Mapping's two existing रूप rows (the other, "qualitative," is the adjectival reading and does not apply to this noun usage). The compound गुणात्मक परिवर्तन (KD 3.9) is a documented exception, kept as "qualitative change/transformation" per MD-Mapping's own separate row for that adjectival compound.

Settled per Raghava (2026-07-08 remediation): ***parināma* / bare *parinām* = "result"**, aligned with MVD/SB **Effort – Motion – Result** for श्रम-गति-परिणाम — both फल and bare परिणाम render as "result" in English (acceptable overlap where Hindi overlaps; फल-परिणाम compounds collapse to "result"). Idiomatic "as a result of" unchanged. Retrofitted corpus-wide on 2026-07-08.

Settled per Raghava (2026-07-08): ***sañcetanā* = "awareness"**

Settled per Raghava (2026-07-08 remediation): ***svabhāv* = "essential nature"**, matching MVD and Studies (supersedes the earlier project-specific "disposition")

Settled per Raghava (2026-07-08 remediation): ***abhyudaya* = "comprehensive resolution"**, aligned with MVD p.23 (supersedes "well-being" / "rise")

Settled per Raghava (2026-07-08 remediation): ***sammat* = "aligned"**, aligned with logic/justice mappings (supersedes "approved") — overrides MD-Mapping/SB's "Humane Consciousness" for this project; keep चेतना/जीव चेतना as "consciousness." Audit: replace "human consciousness" with "awareness" only where Hindi is संचेतना (KD 3.4 p.69); keep "human consciousness" for मानव चेतना (KD 2, 3.9).

Chapter 3's closing triads (3.16–3.18) introduce several three- and five-term Sanskrit sets, with transliteration and concise glosses on first use where useful. Their aligned renderings include दृष्टा / ज्ञाता / ज्ञेय = **seer / knower / object of knowledge**, दृश / दृश्य / दर्शन = **seer / scene / worldview**, ध्यान / ध्याता / ध्येय = **concentration / one who concentrates / object of concentration**, and साध्य / साधक / साधन = **aim / seeker / means**. See `KD-Glossary-Additions.md` for the full set and reasoning.

Chapter 1 (Karma) carries several additional contextual decisions. ***संस्कार* remains transliterated as "*sanskar*"**, distinct from ***संस्कृति* = "culture"***; ***अभीष्ट* = "desire"**; ***साध्य* = "aim"**; ***कायिक* = "physical"**; and ***कृत, कारित, अनुमोदित* = "done, caused, intended"**. The current ***अनुभूति* = "experiencing"**, ***काम* = "*kama*" (desire)**, contextual ***अर्थ* = "wealth/resources/meaning"**, and कासा / आकूति / मेधा renderings are retained but marked for deferred review rather than treated as final precedents. See `KD-Glossary-Additions.md` for the full reasoning on each.

Three systematic errors were found and corrected across the translation on 2026-07-08, after checking KD phrases against MVD's actual sentence-level translations (not just MD-Mapping's row-level gloss): ***दर्शन* (bare, or in "X दर्शन (ज्ञान)" / "दर्शन-क्षमता" compounds) = "the holistic view (of X)"**, not transliterated "darshan" — MD-Mapping has a direct row (दर्शन = "Holistic view, Worldview, Philosophy") and MVD confirms it verbatim; excluded from this fix are the proper noun "Madhyasth Darshan," the दृश/दृश्य/दर्शन seer-triad sense (KD 3.17), and the verb "X का दर्शन करना" = "to behold X." ***मानवीयतापूर्ण* (X) / *अतिमानवीयतापूर्ण* (X) = "humane (X)" / "higher-humane (X)"**, a plain adjective, not "X filled/replete with humaneness" — confirmed by MD-Mapping's मानवीयता पूर्ण आचरण = "Humane Conduct" and by MVD's own running prose and glossary ("मानवीयतापूर्ण व्यवहार" → "Humane Behaviour," MVD p.34); not extended to other "-पूर्ण" compounds on different roots. ***जीवन ज्ञान* = "knowledge of jeevan"**, not "jeevan knowledge" — keeps the "knowledge of X" pattern parallel with the other two terms of the recurring three-part formula ("अस्तित्व दर्शन ज्ञान, जीवन ज्ञान, मानवीयतापूर्ण आचरण ज्ञान" → "knowledge of the holistic view of existence, knowledge of jeevan, knowledge of humane conduct"), confirmed twice in MVD (p.3, p.259). See `TRANSLATION-PLAN.md`'s "Systematic errors found and corrected" section and the matching `KD-Glossary-Additions.md` rows.

Settled per Raghava (2026-07-09): ***अवकाश* = "opportunity"**, not "leisure" — KD 1 p.14 (PDF p.39) glosses अवकाश (सम्भावना) as "opportunity (possibility)"; the three former "leisure" instances on that page were corrected. Distinct from MD-Mapping's space-sense row (आकाश, अवकाश = void). See `KD-Glossary-Additions.md`.

Settled per Raghava (2026-07-10): ***सम / विषम* = "generative" / "degenerative"** — match MD-Mapping and MVD running prose (not left transliterated as *sam*/*visham* in analytical prose). Corrected remaining KD 1 instances (pp. 15–16, 25). Optional (*sam-visham*) gloss kept only where helpful on compounds. Spelling is "degenerative" (MVD/MD-Mapping), not "de-generative".

Settled per Raghava (2026-07-10): ***ऊर्जा सम्पन्न* = "energised"** (***पूर्णतया ऊर्जा सम्पन्न* = "fully energised"**) — match MVD p.26 Main points ("fully energised") and MD-Mapping ऊर्जित = Energised; noun ***ऊर्जा सम्पन्नता* = "energy-fullness"** (MD-Mapping). Parallel: ***बल सम्पन्न / बल सम्पन्नता* = "forceful" / "forcefulness"**; ***चुंबकीय बल सम्पन्न(ता)* = "magnetic-force-full" / "magnetic force-fullness"**. Supersedes earlier "energy-endowed" / "energy-endowment" / "force-endowment" renderings; corrected corpus-wide.

Settled per Raghava (2026-07-10): ***जागृति क्रम* = "awakening progression"** (not "awakening sequence"); ***विकास क्रम* = "development progression"** (not "developmental sequence") — match MD-Mapping and MVD. Corrected corpus-wide.

A further comparison pass against MVD/SB/JV running prose on 2026-07-09 found and corrected four more systematic issues across chapters 1–3, verified where uncertain against the KD 1 source page images directly (not inferred from corpus comparison alone): ***जड़-चैतन्य* (bare, or in जड़-चैतन्यात्मक प्रकृति) = "insentient and sentient (nature)"**, not "material-conscious" (7 instances, KD 1 and KD 3.7/3.10; KD 2's existing "insentient-sentient" also normalized to match MVD's exact "insentient and sentient" conjunction); ***विश्राम* = "restfulness"**, not "repose" (3 instances, KD 1 and KD 3.18); **X-त्रय compounds = "X-trio"** (rule-trio, behaviour-trio, investigation-trio, awakening-trio, *-tā*-trio, powers-trio, desires-trio), not "triad of X" (16 instances, KD 1–2; leftover *"triad of desires"* → *"desires-trio"* fixed 2026-07-10) — MVD/SB's fixed pattern is "[noun]-trio," never the reversed "triad of X" construction; and ***पाण्डित्य*, in the "skill, proficiency, X" triad, = "scholarliness"** in KD 1 (2 instances), correcting "erudition" to match this project's own KD 2 decision and MVD's repeated "skill, proficiency, and scholarliness." Several other suspected issues from that same pass — a सुकाम/पुण्य collision, a cluster of "freedom-from-delusion" instances suspected of substituting for मोक्ष, a KD 1 table/prose mismatch, and an इच्छा-triad "causal" collision — were checked against source page images and found to already be correct; see the retraction note in `KD-Glossary-Additions.md` for the reasoning on each, kept so the same false leads aren't re-investigated.

Consistency pass 2026-07-10: ***क्षमता / योग्यता / पात्रता* trio = "capacity, ability, and receptivity"** (MD-Mapping/MVD), replacing mixed "fitness/competence/merit" and "worthiness" in the general trio (foreword + KD 1–2). ***पात्रता* = "worthiness"** is kept only for the KD 3.10 kindness/grace/compassion technical contrast.

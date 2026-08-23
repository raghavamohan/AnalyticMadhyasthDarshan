# Rakesh Gupta (MVD / SB / JV) Alignment Status for Karma Darshan

**Updated:** August 23, 2026

This is a deterministic body-level terminology guardrail for the working English translation. It checks known deprecated English variants against the standards established from Rakesh Gupta's MVD, SB, JV, and `MD-Mapping.xlsx`. It does **not** certify every lexical choice. The Hindi source PDF's embedded text layer is corrupt, so contextual Hindi verification must use rendered source-page images.

## Confirmed alignment checks

| Hindi concept | Current KD / Rakesh standard | Deprecated variants checked | Remaining hits | Status |
| :--- | :--- | :--- | ---: | :--- |
| सत्यता | truthfulness | `verity` | 0 | **PASS** |
| स्वभाव | essential nature | `intrinsic-nature`, `disposition` | 0 | **PASS** |
| सभ्यता | civilisation | `civilization` | 0 | **PASS** |
| संचेतना | awareness | `humane consciousness` | 0 | **PASS** |
| श्रम-गति-परिणाम | Effort – Motion – Result | `effort-motion-consequence` | 0 | **PASS** |
| जागृति क्रम | awakening progression | `awakening sequence` | 0 | **PASS** |
| विकास क्रम | development progression | `developmental sequence` | 0 | **PASS** |
| सत्ता में संपृक्त | saturated in Omnipotence | `endowed with omnipotence`, `soaked in omnipotence` | 0 | **PASS** |
| पाण्डित्य | scholarliness | `erudition` | 0 | **PASS** |
| प्रसन्नता | happiness | `gladness` | 0 | **PASS** |
| सदुपयोग | right-use | `proper use`, `good-use`, `good use`, `right use` | 0 | **PASS** |
| पदार्थावस्था / प्राणावस्था / जीवावस्था / ज्ञानावस्था | material / biological / animal / knowledge order | `material state`, `prana state`, `prana-state`, `prana order`, `jeevan state`, `knowledge state`, `knowledge-state`, `four states` | 0 | **PASS** |
| प्राणकोष | biological cell | `prana cell`, `prana-cell` | 0 | **PASS** |
| विवेक | wisdom | `discretion` | 0 | **PASS** |
| व्यवसाय | vocation | `occupation` | 0 | **PASS** |
| दया / कृपा / करुणा | kindness / grace / compassion | `compassion, grace, and mercy`, `compassion/grace/mercy`, `mercy`, `compassionate work-behaviour` | 0 | **PASS** |
| व्यापक / व्यापक वस्तु | Omnipresence / omnipresent reality | `all-pervasive`, `pervasive substance`, `pervasive entity`, `pervasive reality`, `pervasiveness`, `omnipresent space`, `omnipresent substance`, `situated in the omnipresent` | 0 | **PASS** |
| देव मानव | deific human | `god-human`, `godly human`, `godly-human` | 0 | **PASS** |
| पोषण | nourishment | `nurture`, `nurtures`, `nurtured`, `nurturing`, `nourishes` | 0 | **PASS** |
| अनुकूल (relational chain) | aligned | `consonant with` | 0 | **PASS** |
| प्रयास / प्रयत्न | endeavour (effort reserved for श्रम) | `endevour`, `engaged in effort`, `make effort`, `bound to effort`, `human effort`, `tireless effort`, `effort toward`, `efforts have been made`, `propensity, effort`, `conception and effort`, `effort at practice` | 0 | **PASS** |
| प्रयोग | application / apply | `experiment`, `experiments`, `experimental`, `experimentation`, `experimenting` | 0 | **PASS** |
| द्वेष | malice | `accumulation, hatred`, `attachment, hatred`, `envy, hatred, conceit`, `attachment and aversion`, `envy, aversion, hatred`, `hatred by affection` | 0 | **PASS** |
| भोग | enjoyment (contextual) | `indulgence`, `over-indulgence` | 0 | **PASS** |
| सत्यान्वेषण / ऐषणान्वेषण / विषयान्वेषण | truth- / motive- / instincts-oriented exploration | `truth-investigation`, `desire-investigation`, `object-investigation`, `truth-investigative`, `desire-investigative`, `object-investigative`, `investigation-trio` | 0 | **PASS** |
| ऐषणा-त्रय | motive-trio | `desires-trio`, `desire-trio` | 0 | **PASS** |
| सम्मत | aligned | `endorsed by`, `truth-connected`, `in accordance with dharma and justice`, `in accordance with wisdom` | 0 | **PASS** |
| X-त्रय | X-trio | `triad of` | 0 | **PASS** |

**Configured deprecated variants remaining:** 0

## Approved deviations from Rakesh / MD-Mapping

The default remains Rakesh Gupta's MVD/SB/JV terminology and `MD-Mapping.xlsx`. Raghava has explicitly approved these limited KD choices:

- Bare/general/ontological **बल** is **strength**, instead of Rakesh's usual **force**. Named physical/interaction categories remain **force**; बल सम्पन्न / बल सम्पन्नता remain **forceful / forcefulness**.
- **पोषण** is **nourishment**, where MD-Mapping's bare row has **nurturing**.
- **प्रयोग** is **application / apply**, where Rakesh frequently uses **experiment / experimentation**.
- Bare **भोग** is **enjoyment**, where MVD often uses **indulgence / sensory enjoyments**. Contextual फल भोगना remains **experience consequences/results**, भोक्ता is **enjoyer**, and उपभोग is **consumption**.

## Follow-up decisions now resolved

The August 23 follow-up also settled **अनुकूल = aligned** in relational faculty/activity chains (while environmental अनुकूल remains **favourable**), **प्रयास / प्रयत्न = endeavour** with **effort** reserved for श्रम, **द्वेष = malice** following MVD's direct definition, and the three अन्वेषण compounds as **truth- / motive- / instincts-oriented exploration**. The exact compounds are absent from MVD/JV; the last choice is compositional from their established base vocabulary. ऐषणा-त्रय is now **motive-trio**.

## Items still requiring contextual alignment review

These are review candidates, not confirmed errors:

| Hindi term | Current candidate range | What remains to verify |
| :--- | :--- | :--- |
| मात्रा | quantity / measure | Confirm quantitative amount versus existential measure. |

## Reproduce

```powershell
python Scripts/_verify_kd_translation_alignment.py
python Scripts/_review_rakesh_translations.py
```

The review corpus is `MVD-Madhyasth-Darshan-Coexistentialism.md`, `SB-Samadhanatmak-Bhautikvad.md`, `JV-Jeevan-Vidya-An-Introduction.md`, and `MD-Mapping.xlsx` under `References/Madhyasth-Darshan/`.

*Report generated by `Scripts/_review_rakesh_translations.py`.*

# References

Reference catalog for sources cited across `Studies/`. Approved large payloads are
served at their stable `/References/...` URLs from Cloudflare R2; unresolved-rights
PDFs and the two active translation sources remain in Git. See
[MANIFEST.md](MANIFEST.md) for the citation audit,
[r2-artifacts.json](r2-artifacts.json) for the storage/checksum source of truth, and
[NOT-DOWNLOADED.md](NOT-DOWNLOADED.md) for works linked externally only.

**What remains in Git**

- Small, reviewable Markdown, metadata, manifests, mappings, and translation workspaces.
- The KD and MSM Hindi source PDFs while those translations are active.
- PDFs whose redistribution status is still under review; the R2 Worker passes their
  existing public paths through to GitHub Pages.
- Cleaned Markdown for the nine retained webpage snapshots. Their original HTML bytes are
  private in R2; generated PDFs are build-only unless the manifest records a public right.

**What is stored outside Git**

- Twenty-five approved PDFs are served from the private `amd-reference-archive` R2 bucket
  through the allowlisted `amd-generated-pdfs` Worker.
- Nine original webpage snapshots are retained under the non-public
  `archive/original-html/` prefix.
- SEP entries and unresolved Poorvam/Carroll derivatives link to their canonical
  publisher pages rather than being electronically redistributed.

**What we do not mirror**

Commercial science books, **ATR**, and other restricted material are **not** copied here. Link to the original publisher or author URL instead — see [NOT-DOWNLOADED.md](NOT-DOWNLOADED.md). **Contributors: do not upload restricted material** to this folder; only add files you may redistribute.

Run `python Scripts/_hydrate_references.py --all-public` to populate the ignored,
hash-verified cache without Cloudflare credentials. Run `Scripts/_quote_tool.py verify`
to check blockquotes; external-only works are skipped.

## Directory layout

```
References/
├── README.md
├── MANIFEST.md                 Citation audit: Studies tags → files or external
├── NOT-DOWNLOADED.md           External works with original URLs
├── r2-artifacts.json           Storage, provenance, rights, size, and SHA-256 manifest
├── Madhyasth-Darshan/          Markdown/mappings, active translation sources, workspaces
├── Advaita-Vedanta/            R2 links for approved source PDFs
├── Comparative-Philosophy/     Cleaned Markdown plus rights-review PDFs
├── Science/                    R2 links and rights-review PDFs
├── Modern-Philosophy/          Cleaned Markdown, R2 links, and rights-review PDFs
└── Applied-Studies/            R2 links for openly licensed formal studies
```

To hydrate R2-published references into the ignored local cache:

```powershell
python Scripts/_hydrate_references.py --all-public
```

Audit Studies bibliographies first: `python Scripts/_audit_references.py`. Agent skill:
[.agents/skills/download-references](../.agents/skills/download-references/SKILL.md).

## Studies coverage

<!-- studies-catalog -->
| Paper | Primary tags |
|-------|----------------|
| [Aesthetics.pdf](../Studies/Aesthetics/Aesthetics.pdf) | MVD, JV, SB; Advaita (TU, BU, BG, VC); modern aesthetics (SEP Concept of the Aesthetic, SEP Kant Aesthetics, SEP Definition of Art, SEP Environmental Aesthetics, SEP Aesthetics of the Everyday external); Indian aesthetics (Poorvam Rasa external; Keating 2008, Mind and Creativity Rasa external) |
| [Ethics-And-Morals-In-Human-Beings.pdf](../Studies/Ethics-And-Morals-In-Human-Beings/Ethics-And-Morals-In-Human-Beings.pdf) | MVD, SB, JV; traditional religious ethics (SEP Theological Voluntarism, SEP Natural Law Ethics external; Matthew 22, Quran 16 external); Advaita (BG, VC); modern moral science/philosophy (Crockett 2013 R2, SEP Moral Psychology external; Curry et al. 2019, Graham et al. 2013, Greene et al. 2001, Haidt 2001, Tomasello and Vaish 2013 external) |
| [How-To-Form-Self-Sustaining-Organizations.pdf](../Studies/How-To-Form-Self-Sustaining-Organizations/How-To-Form-Self-Sustaining-Organizations.pdf) | MVD, SB, JV; AV, SV; ATR (external) |
| [Human-Behavior-And-Society.pdf](../Studies/Human-Behavior-And-Society/Human-Behavior-And-Society.pdf) | MVD, SB, JV |
| [The-Epistemology-of-Coexistence.pdf](../Studies/The-Epistemology-of-Coexistence/The-Epistemology-of-Coexistence.pdf) | MVD, SB, JV; Advaita (BG, BU, BSB, CU, DDV, MU, TU, VC in R2; VP external); modern science/philosophy (27 works, 8 local / 19 external) |
| [Nature-Of-Time.pdf](../Studies/Nature-Of-Time/Nature-Of-Time.pdf) | MVD, SB, JVD; Advaita (MU, BG, VC); Carroll 2010, Ashtekar-Singh 2011, McTaggart 1908; external (Rovelli 2018) |
| [The-Ontology-of-Coexistence.pdf](../Studies/The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.pdf) | MVD, SB, JV; Advaita (CU, TU, VC); modern science/philosophy (Chalmers 1995, Nagel 1974, Strawson 2006, Frankish 2016, Limanowski and Blankenburg 2013, Whitehead 1929, Russell 1921, Mach 1914, Friston 2010, Carroll 2010, Guth 2007, Ashtekar and Singh 2011); external (Metzinger 2003, Penrose 2010, Ishvarakrishna, Nagarjuna, Weinberg 1995) |
| [Why-Humans-Are-Not-Just-Material.pdf](../Studies/Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.pdf) | MVD, SB, JV; Advaita (BU, TU, MU, CU, KU, BG, BSB, VC, DDV); Science (12 works, 3 local / 9 external) |
| [How-Undivided-Society-Is-Established.pdf](../Studies/How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established.pdf) | MVD, SB, JV, JVD, AVD |
| [Axiology-Value-Theory.pdf](../Studies/Axiology-Value-Theory/Axiology-Value-Theory.pdf) | MVD, SB, JV, AVD, KD; Advaita (BU, TU, BG, BSB, VC); Western value theory and scientific valuation research, including Killingsworth 2021 and Killingsworth, Kahneman, and Mellers 2023 (external) |
| [Family-Relationships-And-Values.pdf](../Studies/Family-Relationships-And-Values/Family-Relationships-And-Values.pdf) | MVD, JV, SB, KD |
| [Spiritual-Practice-And-Realization.pdf](../Studies/Spiritual-Practice-And-Realization/Spiritual-Practice-And-Realization.pdf) | MVD, JV, KD |
| [A-State-Dynamic-Model-Of-Coexistence.pdf](../Studies/A-State-Dynamic-Model-Of-Coexistence/A-State-Dynamic-Model-Of-Coexistence.pdf) | MVD, SB, JV, AVD, KD |
<!-- /studies-catalog -->

## Madhyasth-Darshan/

For **MVD**, **SB**, and **JV**, Studies bibliographies and quote verification must link the **PDF**. The companion `.md` files are machine extracts of the PDF text layer for search and analysis only — do not edit them by hand, and do not cite or link them from Studies.

| Tag | File | Notes |
|-----|------|-------|
| **MVD** | [MVD-Madhyasth-Darshan-Coexistentialism.pdf](https://analyticmadhyasthdarshan.org/References/Madhyasth-Darshan/MVD-Madhyasth-Darshan-Coexistentialism.pdf) · [`.md`](Madhyasth-Darshan/MVD-Madhyasth-Darshan-Coexistentialism.md) | *Madhyasth Darshan — Co-existentialism*; English translation by Rakesh Gupta. Cite the PDF in Studies; `.md` is analysis-only (do not edit by hand). |
| **SB** | [SB-Samadhanatmak-Bhautikvad.pdf](https://analyticmadhyasthdarshan.org/References/Madhyasth-Darshan/SB-Samadhanatmak-Bhautikvad.pdf) · [`.md`](Madhyasth-Darshan/SB-Samadhanatmak-Bhautikvad.md) | *Samadhanatmak Bhautikvad*; English translation by Rakesh Gupta; [bilingual Hindi and English playlist on YouTube](https://www.youtube.com/playlist?list=PL69PCoz1OQW0dhshZ0Xv3KtZ7ajJOIpgv). Cite the PDF in Studies; `.md` is analysis-only (do not edit by hand). |
| **JV** | [JV-Jeevan-Vidya-An-Introduction.pdf](https://analyticmadhyasthdarshan.org/References/Madhyasth-Darshan/JV-Jeevan-Vidya-An-Introduction.pdf) · [`.md`](Madhyasth-Darshan/JV-Jeevan-Vidya-An-Introduction.md) | *Jeevan Vidya: An Introduction*; English translation by Rakesh Gupta. Cite the PDF in Studies; `.md` is analysis-only (do not edit by hand). |
| **AVD** | [AVD-Adhyatmvad.docx.pdf](https://analyticmadhyasthdarshan.org/References/Madhyasth-Darshan/AVD-Adhyatmvad.docx.pdf) | *Realisation Centred Spiritualism* (Adhyatmvad); English WIP translation by Sanjeev Chopra |
| **JVD** | [JVD-Janvad.pdf](https://analyticmadhyasthdarshan.org/References/Madhyasth-Darshan/JVD-Janvad.pdf) | *Behaviour Centred Public Discourse* (Janvad); English WIP translation by Sanjeev Chopra |
| **MD** | [MD-Mapping.xlsx](Madhyasth-Darshan/MD-Mapping.xlsx) | Hindi–English terminology glossary (chapter/page mapping heritage); exhaustively refreshed from MVD/SB pairs in Phase 4 (freq ≥ 2 candidates; see [`MD-Mapping-Sources/`](Madhyasth-Darshan/MD-Mapping-Sources/README.md)) |
| **KD** | [KD-karm darshan v5.pdf](Madhyasth-Darshan/KD-karm%20darshan%20v5.pdf) | *Manav Karm Darshan* (Hindi, v5); retained with the active [KD translation workspace](Madhyasth-Darshan/KD-Karm-Darshan-English/README.md), including its generated English and interleaved Hindi-English review PDFs; all four active-translation PDFs are recorded in `r2-artifacts.json` and intentionally remain in Git |
| **MSM** | [MSM-manav-sanchetnavaadi-manovigyan.pdf](Madhyasth-Darshan/MSM-manav-sanchetnavaadi-manovigyan.pdf) | *Manav Sanchetnavadi Manovigyan* (*मानव संचेतनावादी मनोविज्ञान*; Hindi, 2008 OCR edition) by A. Nagraj; official published-book download |
| **KD-Karm-Darshan-English** | [KD-Karm-Darshan-English/](Madhyasth-Darshan/KD-Karm-Darshan-English/README.md) | Full-book working English translation (front matter + ch. 1–3); not a published translation |
| **MSM-Manav-Sanchetnavadi-Manovigyan-English** | [MSM-Manav-Sanchetnavadi-Manovigyan-English/](Madhyasth-Darshan/MSM-Manav-Sanchetnavadi-Manovigyan-English/README.md) | Page-aligned translation workspace and source images; setup only, with no English translation yet |

## Advaita-Vedanta/

| Tag | File | Notes |
|-----|------|-------|
| **BU** | [BU-Brihadaranyaka-Upanishad-Madhavananda.pdf](https://analyticmadhyasthdarshan.org/References/Advaita-Vedanta/BU-Brihadaranyaka-Upanishad-Madhavananda.pdf) | Swami Madhavananda translation |
| **TU** | [Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf](https://analyticmadhyasthdarshan.org/References/Advaita-Vedanta/Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf) | Gambhirananda, *Eight Upanishads* (Advaita Ashrama; [2-vol. text PDF on Archive.org](https://archive.org/details/eight-upanishads-with-the-commentary-of-s-swami-gambhirananda)). Vol. I: Isa, Kena, Katha, Taittiriya; Vol. II: Aitareya, Mundaka, Mandukya, Prasna — both volumes in one file (719 pp.). **KU** begins at p. 97; **TU** at p. 237 |
| **KU** | [Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf](https://analyticmadhyasthdarshan.org/References/Advaita-Vedanta/Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf) | same as TU |
| **MU** | [MU-Mandukya-Upanishad-Gambhirananda.pdf](https://analyticmadhyasthdarshan.org/References/Advaita-Vedanta/MU-Mandukya-Upanishad-Gambhirananda.pdf) | With Gaudapada Karika; Swami Gambhirananda |
| **CU** | [CU-Chandogya-Upanishad-Gambhirananda.pdf](https://analyticmadhyasthdarshan.org/References/Advaita-Vedanta/CU-Chandogya-Upanishad-Gambhirananda.pdf) | Swami Gambhirananda translation |
| **BG** | [BG-Bhagavad-Gita-Shankara-Gambhirananda.pdf](https://analyticmadhyasthdarshan.org/References/Advaita-Vedanta/BG-Bhagavad-Gita-Shankara-Gambhirananda.pdf) | Shankara commentary; Swami Gambhirananda |
| **BSB** | [BSB-Brahma-Sutra-Bhashya-Gambhirananda.pdf](https://analyticmadhyasthdarshan.org/References/Advaita-Vedanta/BSB-Brahma-Sutra-Bhashya-Gambhirananda.pdf) | *Adhyasa Bhashya* is the preamble |
| **VC** | [VC-Vivekachudamani-Madhavananda.pdf](https://analyticmadhyasthdarshan.org/References/Advaita-Vedanta/VC-Vivekachudamani-Madhavananda.pdf) | Swami Madhavananda translation |
| **DDV** | [DDV-Drig-Drishya-Viveka-Nikhilananda.pdf](https://analyticmadhyasthdarshan.org/References/Advaita-Vedanta/DDV-Drig-Drishya-Viveka-Nikhilananda.pdf) | Swami Nikhilananda translation |

## Science (open-access papers)

| Tag | File | Notes |
|-----|------|-------|
| **Chalmers 1995** | [Chalmers-1995-Facing-Up-to-the-Problem-of-Consciousness.pdf](Science/Chalmers-1995-Facing-Up-to-the-Problem-of-Consciousness.pdf) | Author-hosted PDF |
| **Crockett 2013** | [Crockett-2013-Models-of-Morality.pdf](https://analyticmadhyasthdarshan.org/References/Science/Crockett-2013-Models-of-Morality.pdf) | Open access, CC BY |
| **Nagel 1974** | [Nagel-1974-What-Is-It-Like-to-Be-a-Bat.pdf](Science/Nagel-1974-What-Is-It-Like-to-Be-a-Bat.pdf) | University-hosted PDF |
| **Strawson 2006** | [Strawson-2006-Realistic-Monism-Panpsychism.pdf](Science/Strawson-2006-Realistic-Monism-Panpsychism.pdf) | Author-hosted PDF |
| **Ashtekar and Singh 2011** | [Ashtekar-Singh-2011-Loop-Quantum-Cosmology-Status-Report.pdf](Science/Ashtekar-Singh-2011-Loop-Quantum-Cosmology-Status-Report.pdf) | arXiv open access (gr-qc/1108.0893) |
| **Carroll 2010** | [Author's article](https://www.preposterousuniverse.com/blog/2010/02/22/energy-is-not-conserved/) | External canonical page; cleaned Markdown retained for verification |
| **Friston 2010** | [Friston-2010-Free-Energy-Principle.pdf](Science/Friston-2010-Free-Energy-Principle.pdf) | Author-hosted / open-access PDF |
| **Guth 2007** | [Guth-2007-Eternal-Inflation.pdf](Science/Guth-2007-Eternal-Inflation.pdf) | IOP open access |
| **Terekhovich 2015** | [Terekhovich-2015-Metaphysics-Principle-Least-Action.pdf](Science/Terekhovich-2015-Metaphysics-Principle-Least-Action.pdf) | arXiv open access (physics.hist-ph) |
| **Kotiuga and Lahtinen 2018** | [Kotiuga-Lahtinen-2018-Electrical-Engineering-Naturality.pdf](Science/Kotiuga-Lahtinen-2018-Electrical-Engineering-Naturality.pdf) | arXiv open access (math-ph) |
| **Feynman 1964** | [Feynman-1964-Principle-Least-Action-Ch19.pdf](Science/Feynman-1964-Principle-Least-Action-Ch19.pdf) | *Feynman Lectures on Physics*, Vol. II, Ch. 19 (Illinois course mirror) |
| **Arnold symplectic** | [Arnold-Symplectic-Geometry-Applications.pdf](Science/Arnold-Symplectic-Geometry-Applications.pdf) | Author-hosted scan |
| **Baehni 2019** | [Baehni-2019-Mathematical-Aspects-Classical-Mechanics.pdf](Science/Baehni-2019-Mathematical-Aspects-Classical-Mechanics.pdf) | ETH Zurich semester paper |

## Modern-Philosophy/

| Tag | File | Notes |
|-----|------|-------|
| **Frankish 2016** | [Frankish-2016-Illusionism-Theory-Consciousness.pdf](Modern-Philosophy/Frankish-2016-Illusionism-Theory-Consciousness.pdf) | Author eprint |
| **Limanowski and Blankenburg 2013** | [Limanowski-Blankenburg-2013-Minimal-Self-Models-Free-Energy-Principle.pdf](https://analyticmadhyasthdarshan.org/References/Modern-Philosophy/Limanowski-Blankenburg-2013-Minimal-Self-Models-Free-Energy-Principle.pdf) | Open access |
| **Melloni et al. 2025** | [Melloni-et-al-2025-Adversarial-Testing-Consciousness-Theories.pdf](https://analyticmadhyasthdarshan.org/References/Modern-Philosophy/Melloni-et-al-2025-Adversarial-Testing-Consciousness-Theories.pdf) | CC BY 4.0; Europe PMC mirror |
| **SEP Aesthetics of the Everyday** | [SEP entry](https://plato.stanford.edu/entries/aesthetics-of-everyday/) | External canonical page; electronic redistribution is not permitted |
| **SEP Concept of the Aesthetic** | [SEP entry](https://plato.stanford.edu/entries/aesthetic-concept/) | External canonical page; electronic redistribution is not permitted |
| **SEP Definition of Art** | [SEP entry](https://plato.stanford.edu/entries/art-definition/) | External canonical page; electronic redistribution is not permitted |
| **SEP Environmental Aesthetics** | [SEP entry](https://plato.stanford.edu/entries/environmental-aesthetics/) | External canonical page; electronic redistribution is not permitted |
| **SEP Kant Aesthetics** | [SEP entry](https://plato.stanford.edu/entries/kant-aesthetics/) | External canonical page; electronic redistribution is not permitted |
| **SEP Moral Psychology** | [SEP entry](https://plato.stanford.edu/entries/moral-psych-emp/) | External canonical page; electronic redistribution is not permitted |
| **Tufft et al. 2024** | [Tufft-et-al-2024-Flow-Active-Inference.pdf](https://analyticmadhyasthdarshan.org/References/Modern-Philosophy/Tufft-et-al-2024-Flow-Active-Inference.pdf) | Open access |
| **McTaggart 1908** | [McTaggart-1908-The-Unreality-of-Time.pdf](https://analyticmadhyasthdarshan.org/References/Modern-Philosophy/McTaggart-1908-The-Unreality-of-Time.pdf) | R2 PDF generated from the public-domain Wikisource transcription; original HTML retained privately |
| **Hashemi 2025** | [Hashemi-2025-How-to-Understand-Russellian-Panpsychism.pdf](Modern-Philosophy/Hashemi-2025-How-to-Understand-Russellian-Panpsychism.pdf) | Author preprint (PhilSci-Archive) |
| **Whitehead 1929** | [Whitehead-1929-Process-and-Reality.pdf](https://analyticmadhyasthdarshan.org/References/Modern-Philosophy/Whitehead-1929-Process-and-Reality.pdf) | 1929 Macmillan edition (public domain) |
| **Russell 1921** | [Russell-1921-The-Analysis-of-Mind.pdf](https://analyticmadhyasthdarshan.org/References/Modern-Philosophy/Russell-1921-The-Analysis-of-Mind.pdf) | Public domain |
| **Russell Basic Writings** | [Russell-Basic-Writings.pdf](https://analyticmadhyasthdarshan.org/References/Modern-Philosophy/Russell-Basic-Writings.pdf) | NDL Ethiopia mirror; public-domain anthology |
| **Mach 1914** | [Mach-1914-The-Analysis-of-Sensations.pdf](https://analyticmadhyasthdarshan.org/References/Modern-Philosophy/Mach-1914-The-Analysis-of-Sensations.pdf) | Open Court translation (public domain) |

## Applied-Studies/

| Tag | File | Notes |
|-----|------|-------|
| **MD-TOPOS** | [MD_TOPOS.pdf](https://analyticmadhyasthdarshan.org/References/Applied-Studies/MD_TOPOS.pdf) | Meena, B. (2025). *Minimal Decidable Site for the Madhyasth–Darshan Classifying Topos via Single-Flag Morleyisation*. Zenodo preprint, [DOI 10.5281/zenodo.16786431](https://doi.org/10.5281/zenodo.16786431); CC BY-NC-SA 4.0 |

## Comparative-Philosophy/

| Tag | File | Notes |
|-----|------|-------|
| **AV** | [SEP entry](https://plato.stanford.edu/entries/shankara/) | External canonical page; electronic redistribution is not permitted |
| **Poorvam Rasa** | [Publisher article](https://poorvam.com/article.php?slug=s-dh-ra-kara-a-underlying-process-for-experiencing-rasa) | External canonical page pending redistribution permission |
| **SEP Natural Law Ethics** | [SEP entry](https://plato.stanford.edu/entries/natural-law-ethics/) | External canonical page; electronic redistribution is not permitted |
| **SEP Theological Voluntarism** | [SEP entry](https://plato.stanford.edu/entries/voluntarism-theological/) | External canonical page; electronic redistribution is not permitted |
| **SV** | [SV-Vivekananda-Practical-Vedanta.pdf](Comparative-Philosophy/SV-Vivekananda-Practical-Vedanta.pdf) | *Practical Vedanta* lectures (Complete Works material) |
| **Bhattacharya** | [Bhattacharya-Jeevan-And-Brain-Relationship.pdf](https://analyticmadhyasthdarshan.org/References/Comparative-Philosophy/Bhattacharya-Jeevan-And-Brain-Relationship.pdf) | *The Relationship of Jeevan and Brain*; author-supplied copy published with permission; secondary exposition of Nagraj's works |

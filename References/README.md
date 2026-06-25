# References

Local copies of source texts cited across `Studies/`. See [MANIFEST.md](MANIFEST.md) for a citation audit and [NOT-DOWNLOADED.md](NOT-DOWNLOADED.md) for works linked externally only.

**What we store locally**

- **Madhyasth Darshan** primary texts (MVD, SB, JV, AVD, JVD) and the MD mapping spreadsheet.
- **Advaita Vedanta** translations under `Advaita-Vedanta/`.
- **Comparative philosophy, Indian aesthetics, and religious ethics** (AV, SV, SEP snapshots, rasa material) under `Comparative-Philosophy/`.
- **Open-access science papers** (Chalmers 1995, Nagel 1974, Strawson 2006, Crockett 2013, Ashtekar and Singh 2011, Carroll 2010, Friston 2010, Guth 2007) under `Science/`.
- **Open-access modern philosophy / cognitive science papers** under `Modern-Philosophy/`.

**What we do not store**

Commercial science books, **ATR**, and other restricted material are **not** copied here. Link to the original publisher or author URL instead — see [NOT-DOWNLOADED.md](NOT-DOWNLOADED.md). **Contributors: do not upload restricted material** to this folder; only add files you may redistribute.

Run `Scripts/_quote_tool.py verify` to check blockquotes in Studies against local files. Run `Scripts/_quote_tool.py cache sync` after adding or updating PDFs under `References/`. Quotes tagged to external-only works are skipped.

## Directory layout

```
References/
├── README.md
├── MANIFEST.md                 Citation audit: Studies tags → files or external
├── NOT-DOWNLOADED.md           External works with original URLs
├── Madhyasth-Darshan/          MVD, SB, JV, AVD, JVD + MD-Mapping.xlsx
├── Advaita-Vedanta/            Upanishads, Gita, BSB, prakarana texts
├── Comparative-Philosophy/     AV (SEP), SV (Vivekananda)
├── Science/                    Chalmers, Nagel, Strawson, cosmology & physics papers
└── Modern-Philosophy/          Open-access papers and SEP snapshots on consciousness, self, epistemology, and aesthetics
```

To refresh externally downloaded files (Advaita Vedanta, comparative philosophy, open-access science papers):

```powershell
python Scripts/_download_references.py
# or: .\Scripts\_download_references.ps1
```

Audit Studies bibliographies first: `python Scripts/_audit_references.py`. Agent skill:
[.agents/skills/download-references](../.agents/skills/download-references/SKILL.md).

## Studies coverage

<!-- studies-catalog -->
| Paper | Primary tags |
|-------|----------------|
| [Aesthetics.pdf](../Studies/Aesthetics/Aesthetics.pdf) | MVD, JV, SB; Advaita (TU, BU, BG, VC); modern aesthetics (SEP Concept of the Aesthetic, SEP Kant Aesthetics, SEP Definition of Art, SEP Environmental Aesthetics, SEP Aesthetics of the Everyday local); Indian aesthetics (Poorvam Rasa local; Keating 2008, Mind and Creativity Rasa external) |
| [Ethics-And-Morals-In-Human-Beings.pdf](../Studies/Ethics-And-Morals-In-Human-Beings/Ethics-And-Morals-In-Human-Beings.pdf) | MVD, SB, JV; traditional religious ethics (SEP Theological Voluntarism, SEP Natural Law Ethics local; Matthew 22, Quran 16 external); Advaita (BG, VC); modern moral science/philosophy (Crockett 2013, SEP Moral Psychology local; Curry et al. 2019, Graham et al. 2013, Greene et al. 2001, Haidt 2001, Tomasello and Vaish 2013 external) |
| [How-To-Form-Self-Sustaining-Organizations.pdf](../Studies/How-To-Form-Self-Sustaining-Organizations/How-To-Form-Self-Sustaining-Organizations.pdf) | MVD, SB, JV; AV, SV; ATR (external) |
| [Human-Behavior-And-Society.pdf](../Studies/Human-Behavior-And-Society/Human-Behavior-And-Society.pdf) | MVD, SB, JV |
| [Knowledge-Knower-And-Known.pdf](../Studies/Knowledge-Knower-And-Known/Knowledge-Knower-And-Known.pdf) | MVD, SB, JV; Advaita (CU, BG, BSB, DDV, VC); modern science/philosophy (20 works, 11 local / 9 external) |
| [Category-Theory-Explained.pdf](../Studies/Category-Theory-Explained/Category-Theory-Explained.pdf) | MVD, SB, JV |
| [The-Coexistence-Template.pdf](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) | MVD, SB, JV |
| [Nature-Of-Time.pdf](../Studies/Nature-Of-Time/Nature-Of-Time.pdf) | MVD, SB, JVD; Advaita (MU, BG, VC); Carroll 2010, Ashtekar-Singh 2011, McTaggart 1908; external (Rovelli 2018) |
| [The-Ontology-of-Coexistence.pdf](../Studies/The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.pdf) | MVD, SB, JV; Bhattacharya; Advaita (CU, TU, VC); modern science/philosophy (Chalmers 1995, Nagel 1974, Strawson 2006, Frankish 2016, Limanowski and Blankenburg 2013, Whitehead 1929, Russell 1921, Mach 1914, Friston 2010, Carroll 2010, Guth 2007, Ashtekar and Singh 2011); external (Metzinger 2003, Penrose 2010, Ishvarakrishna, Nagarjuna, Weinberg 1995) |
| [Why-Humans-Are-Not-Just-Material.pdf](../Studies/Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.pdf) | MVD, SB, JV; Bhattacharya; Advaita (BU, TU, MU, CU, KU, BG, BSB, VC, DDV); Science (12 works, 3 local / 9 external) |
| [Ethics-In-Madhyasth-Darshan.pdf](../Studies/Ethics-In-Madhyasth-Darshan/Ethics-In-Madhyasth-Darshan.pdf) | MVD, SB, JV |
<!-- /studies-catalog -->

## Madhyasth-Darshan/

| Tag | File | Notes |
|-----|------|-------|
| **MVD** | [MVD-Madhyasth-Darshan-Coexistentialism.pdf](Madhyasth-Darshan/MVD-Madhyasth-Darshan-Coexistentialism.pdf) | *Madhyasth Darshan — Co-existentialism*; English translation by Rakesh Gupta |
| **SB** | [SB-Samadhanatmak-Bhautikvad.pdf](Madhyasth-Darshan/SB-Samadhanatmak-Bhautikvad.pdf) | *Samadhanatmak Bhautikvad*; English translation by Rakesh Gupta; [bilingual Hindi and English playlist on YouTube](https://www.youtube.com/playlist?list=PL69PCoz1OQW0dhshZ0Xv3KtZ7ajJOIpgv) |
| **JV** | [JV-Jeevan-Vidya-An-Introduction.pdf](Madhyasth-Darshan/JV-Jeevan-Vidya-An-Introduction.pdf) | *Jeevan Vidya: An Introduction*; English translation by Rakesh Gupta |
| **AVD** | [AVD-Adhyatmvad.docx.pdf](Madhyasth-Darshan/AVD-Adhyatmvad.docx.pdf) | *Realisation Centred Spiritualism* (Adhyatmvad); English WIP translation by Sanjeev Chopra |
| **JVD** | [JVD-Janvad.pdf](Madhyasth-Darshan/JVD-Janvad.pdf) | *Behaviour Centred Public Discourse* (Janvad); English WIP translation by Sanjeev Chopra |
| **MD** | [MD-Mapping.xlsx](Madhyasth-Darshan/MD-Mapping.xlsx) | Chapter/page mapping spreadsheet |

## Advaita-Vedanta/

| Tag | File | Notes |
|-----|------|-------|
| **BU** | [BU-Brihadaranyaka-Upanishad-Madhavananda.pdf](Advaita-Vedanta/BU-Brihadaranyaka-Upanishad-Madhavananda.pdf) | Swami Madhavananda translation |
| **TU** | [Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf](Advaita-Vedanta/Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf) | Gambhirananda, *Eight Upanishads* (Advaita Ashrama; [2-vol. text PDF on Archive.org](https://archive.org/details/eight-upanishads-with-the-commentary-of-s-swami-gambhirananda)). Vol. I: Isa, Kena, Katha, Taittiriya; Vol. II: Aitareya, Mundaka, Mandukya, Prasna — both volumes in one file (719 pp.). **KU** begins at p. 97; **TU** at p. 237 |
| **KU** | [Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf](Advaita-Vedanta/Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf) | same as TU |
| **MU** | [MU-Mandukya-Upanishad-Gambhirananda.pdf](Advaita-Vedanta/MU-Mandukya-Upanishad-Gambhirananda.pdf) | With Gaudapada Karika; Swami Gambhirananda |
| **CU** | [CU-Chandogya-Upanishad-Gambhirananda.pdf](Advaita-Vedanta/CU-Chandogya-Upanishad-Gambhirananda.pdf) | Swami Gambhirananda translation |
| **BG** | [BG-Bhagavad-Gita-Shankara-Gambhirananda.pdf](Advaita-Vedanta/BG-Bhagavad-Gita-Shankara-Gambhirananda.pdf) | Shankara commentary; Swami Gambhirananda |
| **BSB** | [BSB-Brahma-Sutra-Bhashya-Gambhirananda.pdf](Advaita-Vedanta/BSB-Brahma-Sutra-Bhashya-Gambhirananda.pdf) | *Adhyasa Bhashya* is the preamble |
| **VC** | [VC-Vivekachudamani-Madhavananda.pdf](Advaita-Vedanta/VC-Vivekachudamani-Madhavananda.pdf) | Swami Madhavananda translation |
| **DDV** | [DDV-Drig-Drishya-Viveka-Nikhilananda.pdf](Advaita-Vedanta/DDV-Drig-Drishya-Viveka-Nikhilananda.pdf) | Swami Nikhilananda translation |

## Science (open-access papers)

| Tag | File | Notes |
|-----|------|-------|
| **Chalmers 1995** | [Chalmers-1995-Facing-Up-to-the-Problem-of-Consciousness.pdf](Science/Chalmers-1995-Facing-Up-to-the-Problem-of-Consciousness.pdf) | Author-hosted PDF |
| **Crockett 2013** | [Crockett-2013-Models-of-Morality.pdf](Science/Crockett-2013-Models-of-Morality.pdf) | Open access, CC BY |
| **Nagel 1974** | [Nagel-1974-What-Is-It-Like-to-Be-a-Bat.pdf](Science/Nagel-1974-What-Is-It-Like-to-Be-a-Bat.pdf) | University-hosted PDF |
| **Strawson 2006** | [Strawson-2006-Realistic-Monism-Panpsychism.pdf](Science/Strawson-2006-Realistic-Monism-Panpsychism.pdf) | Author-hosted PDF |
| **Ashtekar and Singh 2011** | [Ashtekar-Singh-2011-Loop-Quantum-Cosmology-Status-Report.pdf](Science/Ashtekar-Singh-2011-Loop-Quantum-Cosmology-Status-Report.pdf) | arXiv open access (gr-qc/1108.0893) |
| **Carroll 2010** | [Carroll-2010-Energy-Is-Not-Conserved.html](Science/Carroll-2010-Energy-Is-Not-Conserved.html) | Internet Archive snapshot of author blog |
| **Friston 2010** | [Friston-2010-Free-Energy-Principle.pdf](Science/Friston-2010-Free-Energy-Principle.pdf) | Author-hosted / open-access PDF |
| **Guth 2007** | [Guth-2007-Eternal-Inflation.pdf](Science/Guth-2007-Eternal-Inflation.pdf) | IOP open access |

## Modern-Philosophy/

| Tag | File | Notes |
|-----|------|-------|
| **Frankish 2016** | [Frankish-2016-Illusionism-Theory-Consciousness.pdf](Modern-Philosophy/Frankish-2016-Illusionism-Theory-Consciousness.pdf) | Author eprint |
| **Limanowski and Blankenburg 2013** | [Limanowski-Blankenburg-2013-Minimal-Self-Models-Free-Energy-Principle.pdf](Modern-Philosophy/Limanowski-Blankenburg-2013-Minimal-Self-Models-Free-Energy-Principle.pdf) | Open access |
| **Melloni et al. 2025** | [Melloni-et-al-2025-Adversarial-Testing-Consciousness-Theories.pdf](Modern-Philosophy/Melloni-et-al-2025-Adversarial-Testing-Consciousness-Theories.pdf) | CC BY 4.0; Europe PMC mirror |
| **SEP Aesthetics of the Everyday** | [SEP-Aesthetics-of-Everyday.html](Modern-Philosophy/SEP-Aesthetics-of-Everyday.html) | Stanford Encyclopedia of Philosophy snapshot |
| **SEP Concept of the Aesthetic** | [SEP-Concept-of-the-Aesthetic.html](Modern-Philosophy/SEP-Concept-of-the-Aesthetic.html) | Stanford Encyclopedia of Philosophy snapshot |
| **SEP Definition of Art** | [SEP-Definition-of-Art.html](Modern-Philosophy/SEP-Definition-of-Art.html) | Stanford Encyclopedia of Philosophy snapshot |
| **SEP Environmental Aesthetics** | [SEP-Environmental-Aesthetics.html](Modern-Philosophy/SEP-Environmental-Aesthetics.html) | Stanford Encyclopedia of Philosophy snapshot |
| **SEP Kant Aesthetics** | [SEP-Kant-Aesthetics-Teleology.html](Modern-Philosophy/SEP-Kant-Aesthetics-Teleology.html) | Stanford Encyclopedia of Philosophy snapshot |
| **SEP Moral Psychology** | [SEP-2025-Moral-Psychology-Empirical-Approaches.html](Modern-Philosophy/SEP-2025-Moral-Psychology-Empirical-Approaches.html) | Stanford Encyclopedia of Philosophy archived snapshot |
| **Tufft et al. 2024** | [Tufft-et-al-2024-Flow-Active-Inference.pdf](Modern-Philosophy/Tufft-et-al-2024-Flow-Active-Inference.pdf) | Open access |
| **McTaggart 1908** | [McTaggart-1908-The-Unreality-of-Time.html](Modern-Philosophy/McTaggart-1908-The-Unreality-of-Time.html) | Wikisource snapshot (public domain) |
| **Hashemi 2025** | [Hashemi-2025-How-to-Understand-Russellian-Panpsychism.pdf](Modern-Philosophy/Hashemi-2025-How-to-Understand-Russellian-Panpsychism.pdf) | Author preprint (PhilSci-Archive) |
| **Whitehead 1929** | [Whitehead-1929-Process-and-Reality.pdf](Modern-Philosophy/Whitehead-1929-Process-and-Reality.pdf) | 1929 Macmillan edition (public domain) |
| **Russell 1921** | [Russell-1921-The-Analysis-of-Mind.pdf](Modern-Philosophy/Russell-1921-The-Analysis-of-Mind.pdf) | Public domain |
| **Mach 1914** | [Mach-1914-The-Analysis-of-Sensations.pdf](Modern-Philosophy/Mach-1914-The-Analysis-of-Sensations.pdf) | Open Court translation (public domain) |

## Comparative-Philosophy/

| Tag | File | Notes |
|-----|------|-------|
| **AV** | [AV-Shankara-Stanford-Encyclopedia.html](Comparative-Philosophy/AV-Shankara-Stanford-Encyclopedia.html) | *Śaṅkara*, Stanford Encyclopedia of Philosophy (snapshot) |
| **Poorvam Rasa** | [Poorvam-Sadharanikarana-Rasa.html](Comparative-Philosophy/Poorvam-Sadharanikarana-Rasa.html) | Open article on sadharanikarana and rasa |
| **SEP Natural Law Ethics** | [SEP-Natural-Law-Ethics.html](Comparative-Philosophy/SEP-Natural-Law-Ethics.html) | *The Natural Law Tradition in Ethics*, Stanford Encyclopedia of Philosophy (snapshot) |
| **SEP Theological Voluntarism** | [SEP-Theological-Voluntarism.html](Comparative-Philosophy/SEP-Theological-Voluntarism.html) | *Theological Voluntarism*, Stanford Encyclopedia of Philosophy (snapshot) |
| **SV** | [SV-Vivekananda-Practical-Vedanta.pdf](Comparative-Philosophy/SV-Vivekananda-Practical-Vedanta.pdf) | *Practical Vedanta* lectures (Complete Works material) |
| **Bhattacharya** | [Bhattacharya-Jeevan-And-Brain-Relationship.pdf](Comparative-Philosophy/Bhattacharya-Jeevan-And-Brain-Relationship.pdf) | *The Relationship of Jeevan and Brain*; secondary exposition of Nagraj's works |

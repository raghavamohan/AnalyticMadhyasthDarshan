# References

Local copies of source texts cited across `Studies/`. See [MANIFEST.md](MANIFEST.md) for a citation audit and [NOT-DOWNLOADED.md](NOT-DOWNLOADED.md) for works linked externally only.

**What we store locally**

- **Madhyasth Darshan** primary texts (MVD, SB, JV, AVD, JVD) and the MD mapping spreadsheet.
- **Advaita Vedanta** translations under `Advaita-Vedanta/`.
- **Comparative philosophy** (AV, SV) under `Comparative-Philosophy/`.
- **Three author-hosted open-access papers** (Chalmers 1995, Nagel 1974, Strawson 2006) under `Science/`.

**What we do not store**

Commercial science books, **ATR**, and other restricted material are **not** copied here. Link to the original publisher or author URL instead — see [NOT-DOWNLOADED.md](NOT-DOWNLOADED.md). **Contributors: do not upload restricted material** to this folder; only add files you may redistribute.

Run `Scripts/_verify_quotes.py` to check blockquotes in Studies against local files. Quotes tagged to external-only works are skipped.

## Directory layout

```
References/
├── README.md
├── MANIFEST.md                 Citation audit: Studies tags → files or external
├── NOT-DOWNLOADED.md           External works with original URLs
├── Madhyasth-Darshan/          MVD, SB, JV, AVD, JVD + MD-Mapping.xlsx
├── Advaita-Vedanta/            Upanishads, Gita, BSB, prakarana texts
├── Comparative-Philosophy/     AV (SEP), SV (Vivekananda)
└── Science/                    Chalmers, Nagel, Strawson (author-hosted papers)
```

To refresh externally downloaded files (Advaita Vedanta, comparative philosophy, open-access science papers):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Scripts\_download_references.ps1
```

## Studies coverage

<!-- studies-catalog -->
| Paper | Primary tags |
|-------|----------------|
| [How-To-Form-Self-Sustaining-Organizations.pdf](../Studies/How-To-Form-Self-Sustaining-Organizations.pdf) | MVD, SB, JV; AV, SV; ATR (external) |
| [Human-Behavior-And-Society-In-Madhyasth-Darshan.pdf](../Studies/Human-Behavior-And-Society-In-Madhyasth-Darshan.pdf) | MVD, SB, JV |
| [Madhyasth-Darshan-Category-Theory-Explained.pdf](../Studies/Madhyasth-Darshan-Category-Theory-Explained.pdf) | MVD, SB, JV |
| [The-Coexistence-Template.pdf](../Studies/The-Coexistence-Template.pdf) | MVD, SB, JV |
| [Why-Humans-Are-Not-Just-Material.pdf](../Studies/Why-Humans-Are-Not-Just-Material.pdf) | MVD, SB, JV; Advaita (BU–BJM); Science (12 works, 3 local / 9 external) |
<!-- /studies-catalog -->

## Madhyasth-Darshan/

| Tag | File | Notes |
|-----|------|-------|
| **MVD** | [MVD-Madhyasth-Darshan-Coexistentialism.pdf](Madhyasth-Darshan/MVD-Madhyasth-Darshan-Coexistentialism.pdf) | *Madhyasth Darshan — Co-existentialism*; English translation by Rakesh Gupta |
| **SB** | [SB-Samadhanatmak-Bhautikvad.pdf](Madhyasth-Darshan/SB-Samadhanatmak-Bhautikvad.pdf) | *Samadhanatmak Bhautikvad*; English translation by Rakesh Gupta |
| **JV** | [JV-Jeevan-Vidya-An-Introduction.pdf](Madhyasth-Darshan/JV-Jeevan-Vidya-An-Introduction.pdf) | *Jeevan Vidya: An Introduction*; English translation by Rakesh Gupta |
| **AVD** | [AVD-Adhyatmvad.docx.pdf](Madhyasth-Darshan/AVD-Adhyatmvad.docx.pdf) | *Realisation Centred Spiritualism* (Adhyatmvad); English WIP translation by Sanjeev Chopra |
| **JVD** | [JVD-Janvad.pdf](Madhyasth-Darshan/JVD-Janvad.pdf) | *Behaviour Centred Public Discourse* (Janvad); English WIP translation by Sanjeev Chopra |
| **MD** | [MD-Mapping.xlsx](Madhyasth-Darshan/MD-Mapping.xlsx) | Chapter/page mapping spreadsheet |

## Advaita-Vedanta/

| Tag | File | Notes |
|-----|------|-------|
| **BU** | [BU-Brihadaranyaka-Upanishad-Madhavananda.pdf](Advaita-Vedanta/BU-Brihadaranyaka-Upanishad-Madhavananda.pdf) | Swami Madhavananda translation |
| **TU** | [Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf](Advaita-Vedanta/Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf) | Taittiriya Upanishad begins at p. 237 |
| **KU** | [Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf](Advaita-Vedanta/Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf) | Katha Upanishad begins at p. 97 |
| **MU** | [MU-Mandukya-Upanishad-Gambhirananda.pdf](Advaita-Vedanta/MU-Mandukya-Upanishad-Gambhirananda.pdf) | With Gaudapada Karika; Swami Gambhirananda |
| **CU** | [CU-Chandogya-Upanishad-Gambhirananda.pdf](Advaita-Vedanta/CU-Chandogya-Upanishad-Gambhirananda.pdf) | Swami Gambhirananda translation |
| **BG** | [BG-Bhagavad-Gita-Shankara-Gambhirananda.pdf](Advaita-Vedanta/BG-Bhagavad-Gita-Shankara-Gambhirananda.pdf) | Shankara commentary; Swami Gambhirananda |
| **BSB** | [BSB-Brahma-Sutra-Bhashya-Gambhirananda.pdf](Advaita-Vedanta/BSB-Brahma-Sutra-Bhashya-Gambhirananda.pdf) | *Adhyasa Bhashya* is the preamble |
| **VC** | [VC-Vivekachudamani-Madhavananda.pdf](Advaita-Vedanta/VC-Vivekachudamani-Madhavananda.pdf) | Swami Madhavananda translation |
| **DDV** | [DDV-Drig-Drishya-Viveka-Nikhilananda.pdf](Advaita-Vedanta/DDV-Drig-Drishya-Viveka-Nikhilananda.pdf) | Swami Nikhilananda translation |
| **BJM** | [BJM-Brahma-Jnanavali-Mala.md](Advaita-Vedanta/BJM-Brahma-Jnanavali-Mala.md) | Verbatim text from Vedanta Spiritual Library (no separate PDF available) |

## Science (author-hosted papers only)

| Tag | File | Notes |
|-----|------|-------|
| **Chalmers 1995** | [Chalmers-1995-Facing-Up-to-the-Problem-of-Consciousness.pdf](Science/Chalmers-1995-Facing-Up-to-the-Problem-of-Consciousness.pdf) | Author-hosted PDF |
| **Nagel 1974** | [Nagel-1974-What-Is-It-Like-to-Be-a-Bat.pdf](Science/Nagel-1974-What-Is-It-Like-to-Be-a-Bat.pdf) | University-hosted PDF |
| **Strawson 2006** | [Strawson-2006-Realistic-Monism-Panpsychism.pdf](Science/Strawson-2006-Realistic-Monism-Panpsychism.pdf) | Author-hosted PDF |

## Comparative-Philosophy/

| Tag | File | Notes |
|-----|------|-------|
| **AV** | [AV-Shankara-Stanford-Encyclopedia.html](Comparative-Philosophy/AV-Shankara-Stanford-Encyclopedia.html) | *Śaṅkara*, Stanford Encyclopedia of Philosophy (snapshot) |
| **SV** | [SV-Vivekananda-Practical-Vedanta.pdf](Comparative-Philosophy/SV-Vivekananda-Practical-Vedanta.pdf) | *Practical Vedanta* lectures (Complete Works material) |

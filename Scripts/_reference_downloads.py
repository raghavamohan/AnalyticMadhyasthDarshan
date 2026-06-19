"""Manifest of reference files that may be downloaded into References/.

Edit this module when adding a new local mirror. Run Scripts/_download_references.py
to fetch files and Scripts/_audit_references.py to compare Studies citations.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadEntry:
    """One file under References/ and one or more source URLs (first success wins)."""

    dest: str
    urls: tuple[str, ...]
    tag: str | None = None
    min_bytes: int = 1024
    notes: str = ""


# Commercial books, paywalled PDFs, and IEP articles belong in NOT-DOWNLOADED.md only.
DOWNLOADS: tuple[DownloadEntry, ...] = (
    DownloadEntry(
        dest="Advaita-Vedanta/BU-Brihadaranyaka-Upanishad-Madhavananda.pdf",
        urls=(
            "https://archive.org/download/Brihadaranyaka.Upanishad.Shankara.Bhashya.by.Swami.Madhavananda/Brihadaranyaka.Upanishad.Shankara.Bhashya.by.Swami.Madhavananda.pdf",
            "https://archive.org/download/in.ernet.dli.2015.20823/in.ernet.dli.2015.20823.pdf",
        ),
        tag="BU",
    ),
    DownloadEntry(
        dest="Advaita-Vedanta/CU-Chandogya-Upanishad-Gambhirananda.pdf",
        urls=("https://archive.theaum.org/books/advaita/chandogya-upanishad-swami-gambhirananda-rk.pdf",),
        tag="CU",
    ),
    DownloadEntry(
        dest="Advaita-Vedanta/BG-Bhagavad-Gita-Shankara-Gambhirananda.pdf",
        urls=(
            "http://michaelsudduth.com/wp-content/uploads/2013/01/Srimad-Bhagavad-Gita-Shankara-Bhashya-English.pdf",
        ),
        tag="BG",
    ),
    DownloadEntry(
        dest="Advaita-Vedanta/VC-Vivekachudamani-Madhavananda.pdf",
        urls=("https://www.vivekananda.net/PDFBooks/Vivekashudamani.pdf",),
        tag="VC",
    ),
    DownloadEntry(
        dest="Advaita-Vedanta/DDV-Drig-Drishya-Viveka-Nikhilananda.pdf",
        urls=("https://vivekananda.net/PDFBooks/Others/DrgDrsyaViveka1931.pdf",),
        tag="DDV",
    ),
    DownloadEntry(
        dest="Advaita-Vedanta/MU-Mandukya-Upanishad-Gambhirananda.pdf",
        urls=(
            "https://tomdas.com/wp-content/uploads/2023/09/mandukya-upanishad-with-shankaracharya-commentary-and-karika-of-gaudapada-english-trans.-by-swami-gambhirananda-advaita-ashrama-calcutta_text.pdf",
        ),
        tag="MU",
    ),
    DownloadEntry(
        dest="Advaita-Vedanta/Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf",
        urls=(
            "https://dn790002.ca.archive.org/0/items/eight-upanishads-with-the-commentary-of-s-swami-gambhirananda/Eight%20Upanishads%2C%20With%20the%20Commentary%20of%20S%20-%20Swami%20Gambhirananda.pdf",
            "https://archive.org/download/eight-upanishads-with-the-commentary-of-s-swami-gambhirananda/Eight%20Upanishads%2C%20With%20the%20Commentary%20of%20S%20-%20Swami%20Gambhirananda.pdf",
        ),
        tag="TU",
        notes="Also covers KU in the same volume.",
    ),
    DownloadEntry(
        dest="Advaita-Vedanta/BSB-Brahma-Sutra-Bhashya-Gambhirananda.pdf",
        urls=("https://estudantedavedanta.net/Brahma_Sutra_Swami_Gambhirananda.pdf",),
        tag="BSB",
    ),
    DownloadEntry(
        dest="Comparative-Philosophy/AV-Shankara-Stanford-Encyclopedia.html",
        urls=("https://plato.stanford.edu/entries/shankara/",),
        tag="AV",
        notes="SEP snapshot; existing repo practice for quote verification.",
    ),
    DownloadEntry(
        dest="Comparative-Philosophy/SV-Vivekananda-Practical-Vedanta.pdf",
        urls=("https://www.vivekananda.net/PDFBooks/PracticalVedanta.pdf",),
        tag="SV",
    ),
    DownloadEntry(
        dest="Comparative-Philosophy/Poorvam-Sadharanikarana-Rasa.html",
        urls=(
            "https://poorvam.com/article.php?slug=s-dh-ra-kara-a-underlying-process-for-experiencing-rasa",
        ),
        tag="Poorvam Rasa",
    ),
    DownloadEntry(
        dest="Science/Chalmers-1995-Facing-Up-to-the-Problem-of-Consciousness.pdf",
        urls=("https://consc.net/papers/facing.pdf",),
        tag="Chalmers 1995",
    ),
    DownloadEntry(
        dest="Science/Nagel-1974-What-Is-It-Like-to-Be-a-Bat.pdf",
        urls=("https://www.cs.ox.ac.uk/activities/ieg/e-library/sources/nagel_bat.pdf",),
        tag="Nagel 1974",
    ),
    DownloadEntry(
        dest="Science/Strawson-2006-Realistic-Monism-Panpsychism.pdf",
        urls=("https://consc.net/event/reef/strawsonmonism.pdf",),
        tag="Strawson 2006",
    ),
    DownloadEntry(
        dest="Science/Ashtekar-Singh-2011-Loop-Quantum-Cosmology-Status-Report.pdf",
        urls=("https://arxiv.org/pdf/1108.0893.pdf",),
        tag="Ashtekar and Singh 2011",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Frankish-2016-Illusionism-Theory-Consciousness.pdf",
        urls=(
            "https://raw.githubusercontent.com/k0711/kf_articles/master/Frankish_Illusionism%20as%20a%20theory%20of%20consciousness_eprint.pdf",
        ),
        tag="Frankish 2016",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Jarczewski-Riggs-2025-Socializing-Virtue-Epistemology.pdf",
        urls=(
            "https://ruj.uj.edu.pl/bitstreams/5b802d21-6dd8-4450-8767-a715e4175d9b/download",
        ),
        tag="Jarczewski and Riggs 2025",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Limanowski-Blankenburg-2013-Minimal-Self-Models-Free-Energy-Principle.pdf",
        urls=("https://www.frontiersin.org/articles/10.3389/fnhum.2013.00547/pdf",),
        tag="Limanowski and Blankenburg 2013",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Melloni-et-al-2025-Adversarial-Testing-Consciousness-Theories.pdf",
        urls=("https://www.nature.com/articles/s41586-025-08888-1.pdf",),
        tag="Melloni et al. 2025",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Piredda-2024-Tacitly-Situated-Self.pdf",
        urls=("https://link.springer.com/content/pdf/10.1007/s11245-024-10044-9.pdf",),
        tag="Piredda 2024",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Tufft-et-al-2024-Flow-Active-Inference.pdf",
        urls=("https://www.frontiersin.org/articles/10.3389/fpsyg.2024.1354719/pdf",),
        tag="Tufft et al. 2024",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Wiese-2024-Artificial-Consciousness-Free-Energy-Principle.pdf",
        urls=("https://link.springer.com/content/pdf/10.1007/s11098-024-02182-y.pdf",),
        tag="Wiese 2024",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/SEP-Concept-of-the-Aesthetic.html",
        urls=("https://plato.stanford.edu/entries/aesthetic-concept/",),
        tag="SEP Concept of the Aesthetic",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/SEP-Kant-Aesthetics-Teleology.html",
        urls=("https://plato.stanford.edu/entries/kant-aesthetics/",),
        tag="SEP Kant Aesthetics",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/SEP-Definition-of-Art.html",
        urls=("https://plato.stanford.edu/entries/art-definition/",),
        tag="SEP Definition of Art",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/SEP-Environmental-Aesthetics.html",
        urls=("https://plato.stanford.edu/entries/environmental-aesthetics/",),
        tag="SEP Environmental Aesthetics",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/SEP-Aesthetics-of-Everyday.html",
        urls=("https://plato.stanford.edu/entries/aesthetics-of-everyday/",),
        tag="SEP Aesthetics of the Everyday",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Whitehead-1929-Process-and-Reality.pdf",
        urls=(
            "https://archive.org/download/processrealityes0000unse/processrealityes0000unse.pdf",
        ),
        tag="Whitehead 1929",
        notes="Public domain edition.",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Russell-1921-The-Analysis-of-Mind.pdf",
        urls=("https://archive.org/download/analysisofmind00russ/analysisofmind00russ.pdf",),
        tag="Russell 1921",
        notes="Public domain.",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Mach-1914-The-Analysis-of-Sensations.pdf",
        urls=(
            "https://archive.org/download/analysisofsensat00machuoft/analysisofsensat00machuoft.pdf",
        ),
        tag="Mach 1914",
        notes="Public domain.",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/McTaggart-1908-The-Unreality-of-Time.html",
        urls=("https://en.wikisource.org/wiki/The_Unreality_of_Time",),
        tag="McTaggart 1908",
        notes="Public domain; Wikisource snapshot.",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Hashemi-2025-How-to-Understand-Russellian-Panpsychism.pdf",
        urls=(
            "https://philsci-archive.pitt.edu/23990/1/How%20to%20Understand%20Russellian%20Panpsychism.%209.30.24.pdf",
        ),
        tag="Hashemi 2025",
        notes="Author preprint; published in Erkenntnis.",
    ),
    DownloadEntry(
        dest="Modern-Philosophy/Kuhn-2024-Landscape-of-Consciousness.pdf",
        urls=(
            "https://www.sciencedirect.com/science/article/pii/S0079610723001958/pdfft",
            "https://philarchive.org/archive/KUHALO.pdf",
        ),
        tag="Kuhn 2024",
        notes="CC BY-NC-ND at publisher; may fail behind bot checks — keep external URL in study if download fails.",
    ),
)


def download_subdirs() -> tuple[str, ...]:
    return (
        "Madhyasth-Darshan",
        "Advaita-Vedanta",
        "Comparative-Philosophy",
        "Science",
        "Modern-Philosophy",
    )

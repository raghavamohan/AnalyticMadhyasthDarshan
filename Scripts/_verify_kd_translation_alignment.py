#!/usr/bin/env python3
"""Check the KD English body for configured, deprecated terminology variants.

This is a deterministic body-level guardrail. It does not claim to certify every
Hindi/English lexical choice; source-page images remain authoritative because the
Hindi source PDF has a corrupt embedded text layer.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
KD_MD_PATH = (
    REPO_ROOT
    / "References"
    / "Madhyasth-Darshan"
    / "KD-Karm-Darshan-English"
    / "KD-Karm-Darshan-English.md"
)

# Hindi concept, current standard, deprecated literal variants checked in the body.
EXPECTED_TERMS: list[tuple[str, str, list[str]]] = [
    ("सत्यता", "truthfulness", ["verity"]),
    ("स्वभाव", "essential nature", ["intrinsic-nature", "disposition"]),
    ("सभ्यता", "civilisation", ["civilization"]),
    ("संचेतना", "awareness", ["humane consciousness"]),
    ("श्रम-गति-परिणाम", "Effort – Motion – Result", ["effort-motion-consequence"]),
    ("जागृति क्रम", "awakening progression", ["awakening sequence"]),
    ("विकास क्रम", "development progression", ["developmental sequence"]),
    ("सत्ता में संपृक्त", "saturated in Omnipresence", ["endowed with omnipotence", "soaked in omnipotence"]),
    ("पाण्डित्य", "scholarliness", ["erudition"]),
    ("प्रसन्नता", "happiness", ["gladness"]),
    ("सदुपयोग", "right-use", ["proper use", "good-use", "good use", "right use"]),
    (
        "पदार्थावस्था / प्राणावस्था / जीवावस्था / ज्ञानावस्था",
        "material / biological / animal / knowledge order",
        [
            "material state", "prana state", "prana-state", "prana order",
            "jeevan state", "knowledge state", "knowledge-state", "four states",
        ],
    ),
    ("प्राणकोष", "biological cell", ["prana cell", "prana-cell"]),
    (
        "बल (bare/general, paired with शक्ति)",
        "strength (named physical/interaction बल remains force)",
        ["force (*bal*) and power", "where do force and power go"],
    ),
    ("विवेक", "wisdom", ["discretion"]),
    ("व्यवसाय", "vocation", ["occupation"]),
    (
        "दया / कृपा / करुणा",
        "kindness / grace / compassion",
        ["compassion, grace, and mercy", "compassion/grace/mercy", "mercy", "compassionate work-behaviour"],
    ),
    (
        "व्यापक / व्यापक वस्तु",
        "Omnipresence / omnipresent reality",
        [
            "all-pervasive", "pervasive substance", "pervasive entity",
            "pervasive reality", "pervasiveness", "omnipresent space",
            "omnipresent substance", "situated in the omnipresent",
        ],
    ),
    ("देव मानव", "deific human", ["god-human", "godly human", "godly-human"]),
    (
        "पोषण",
        "nourishment",
        ["nurture", "nurtures", "nurtured", "nurturing", "nourishes"],
    ),
    ("अनुकूल (relational chain)", "aligned", ["consonant with"]),
    (
        "प्रयास / प्रयत्न",
        "endeavour (effort reserved for श्रम)",
        [
            "endevour", "engaged in effort", "make effort", "bound to effort",
            "human effort", "tireless effort", "effort toward", "efforts have been made",
            "propensity, effort", "conception and effort", "effort at practice",
        ],
    ),
    (
        "प्रयोग",
        "application / apply",
        ["experiment", "experiments", "experimental", "experimentation", "experimenting"],
    ),
    (
        "द्वेष",
        "malice",
        [
            "accumulation, hatred", "attachment, hatred", "envy, hatred, conceit",
            "attachment and aversion", "envy, aversion, hatred", "hatred by affection",
        ],
    ),
    (
        "तदाकार",
        "absolute-resonance",
        ["take-the-form-of", "taking-the-form-of"],
    ),
    ("भोग", "enjoyment (contextual)", ["indulgence", "over-indulgence"]),
    (
        "योगाभ्यास / योग्याभ्यास",
        "study of yoga",
        ["yoga-practice", "union-worthy practice", "practice of meeting/union"],
    ),
    (
        "सत्यान्वेषण / ऐषणान्वेषण / विषयान्वेषण",
        "truth- / motive- / instincts-oriented exploration",
        [
            "truth-investigation", "desire-investigation", "object-investigation",
            "truth-investigative", "desire-investigative", "object-investigative",
            "investigation-trio",
        ],
    ),
    ("ऐषणा-त्रय", "motive-trio", ["desires-trio", "desire-trio"]),
    (
        "मेधस",
        "brain",
        ["medhas-system", "medhas composition", "medhas-composition", "the medhas"],
    ),
    ("चुम्बकीयता", "magnetism", ["magneticness"]),
    ("प्रभाव क्षेत्र", "field", ["field of effect", "fields of effect"]),
    (
        "संक्रमण / संक्रमणीयता",
        "irreversible transition / irreversibility",
        ["event of transition", "transition-ness"],
    ),
    ("विस्तार", "expanse", ["extension"]),
    ("फलन", "outcome", ["fruition"]),
    ("यथास्थिति", "existent state", ["actual condition", "actual-condition"]),
    ("तृप्ति", "satisfaction", ["satiation"]),
    (
        "सारक / मारक",
        "vitalising / devitalising",
        ["essentiality (*sarakta*)", "destructiveness (*marakta*)"],
    ),
    (
        "ज्ञेय",
        "object of knowledge",
        ["Knowledge, Knower, Known", "the known becoming meaningful"],
    ),
    (
        "दृश / दृश्य / दर्शन",
        "seer / scene / worldview",
        ["[the seeing]", "[the seen]", "seeing/philosophy", "seen, seer, and seeing"],
    ),
    (
        "ध्यान / ध्याता / ध्येय",
        "concentration / one who concentrates / object of concentration",
        ["[attention]", "[the attender]", "[the object of attention]", "attention, attender, and object of attention"],
    ),
    (
        "अध्यात्मवाद / अधिदैवीवाद / अधिभौतिकवाद",
        "Adhyatma-vada / Adhidaivika-vada / Adhibhautika-vada",
        ["spiritualism (*adhyatmavad*)", "god-centred-ism (*adhidaivikvad*)", "materialism-of-the-beyond (*adhibhautikvad*)"],
    ),
    ("नश्वरत्व", "mortality", ["perishability"]),
    (
        "देवात्मा / भूतात्मा / दिव्यात्मा",
        "deific / elemental / divine self",
        ["deific soul", "deific souls", "elemental soul", "elemental souls", "divine soul", "divine souls"],
    ),
    ("प्रभुसत्ता", "supreme order", ["lordly existence"]),
    (
        "विराग / वैराग्य / पर-वैराग्य",
        "dispassion / detachment / supreme-detachment",
        ["dispassion-toward-other", "further-detachment"],
    ),
    ("अनुप्राणित", "propagated (KD wave context)", ["animated onward"]),
    ("जीवन-पुंज", "jeevan-cloud", ["jeevan-cluster"]),
    (
        "प्राण वायु / प्राणवायु",
        "pranavayu (left transliterated)",
        ["life-breath (*pran vayu*)", "pran vayu"],
    ),
    (
        "सम्मत",
        "aligned",
        [
            "endorsed by", "truth-connected", "in accordance with dharma and justice",
            "in accordance with wisdom",
        ],
    ),
    ("X-त्रय", "X-trio", ["triad of"]),
]


def count_literal(text: str, literal: str) -> int:
    """Count case-insensitive literal phrases without matching inside words."""
    pattern = rf"(?<!\w){re.escape(literal)}(?!\w)"
    return len(re.findall(pattern, text, re.IGNORECASE))


def audit_kd_text(kd_text: str) -> list[str]:
    issues: list[str] = []
    for hindi, standard, deprecated in EXPECTED_TERMS:
        for variant in deprecated:
            count = count_literal(kd_text, variant)
            if count:
                issues.append(
                    f"'{variant}' occurs {count} time(s) for {hindi}; expected '{standard}'"
                )
    return issues


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=== KD configured terminology guardrail ===")
    if not KD_MD_PATH.is_file():
        print(f"Error: KD text file not found: {KD_MD_PATH}", file=sys.stderr)
        return 1

    issues = audit_kd_text(KD_MD_PATH.read_text(encoding="utf-8"))
    if issues:
        print(f"FAILED: {len(issues)} deprecated variant(s) remain:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("SUCCESS: no configured deprecated variants found in the KD English body.")
    print("Scope: deterministic guardrail only; contextual Hindi/English review remains manual.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

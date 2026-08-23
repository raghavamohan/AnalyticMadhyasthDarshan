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
    ("सत्ता में संपृक्त", "saturated in Omnipotence", ["endowed with omnipotence", "soaked in omnipotence"]),
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
    ("भोग", "enjoyment (contextual)", ["indulgence", "over-indulgence"]),
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

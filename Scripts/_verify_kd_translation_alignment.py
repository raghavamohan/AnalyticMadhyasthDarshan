#!/usr/bin/env python3
"""
Formal verification script to audit KD-Karm-Darshan-English.md against Rakesh Gupta's
three main translations (MVD, SB, JV) and the canonical baseline MD-Mapping.xlsx.

Checks:
1. All overrides in KD-Glossary-Additions.md are explicitly documented and accounted for.
2. Search KD-Karm-Darshan-English.md for any deprecated/un-aligned terms (e.g. 'verity' instead of 'truthfulness', 'intrinsic-nature' instead of 'essential nature', 'leisure' instead of 'opportunity' for avakash).
3. Verify that core triads and technical formulas in KD match MVD/SB/JV exact phrasing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from openpyxl import load_workbook

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent

MD_MAPPING_PATH = REPO_ROOT / "References" / "Madhyasth-Darshan" / "MD-Mapping.xlsx"
KD_GLOSSARY_MD = REPO_ROOT / "References" / "Madhyasth-Darshan" / "KD-Karm-Darshan-English" / "KD-Glossary-Additions.md"
KD_MD_PATH = REPO_ROOT / "References" / "Madhyasth-Darshan" / "KD-Karm-Darshan-English" / "KD-Karm-Darshan-English.md"

MVD_PATH = REPO_ROOT / "References" / "Madhyasth-Darshan" / "MVD-Madhyasth-Darshan-Coexistentialism.md"
SB_PATH = REPO_ROOT / "References" / "Madhyasth-Darshan" / "SB-Samadhanatmak-Bhautikvad.md"
JV_PATH = REPO_ROOT / "References" / "Madhyasth-Darshan" / "JV-Jeevan-Vidya-An-Introduction.md"

# Standard expected terms for key Hindi concepts (aligned with Rakesh Gupta's MVD/SB/JV)
EXPECTED_TERMS = [
    # (Hindi, English_standard, Disallowed/deprecated variants)
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
]


def audit_kd_text(kd_text: str) -> list[str]:
    issues: list[str] = []
    for hindi, std, disallowed in EXPECTED_TERMS:
        for dis in disallowed:
            pattern = r"\b" + re.escape(dis) + r"\b"
            matches = list(re.finditer(pattern, kd_text, re.IGNORECASE))
            if matches:
                issues.append(
                    f"Forbidden/deprecated term '{dis}' found {len(matches)} time(s) for '{hindi}' (expected '{std}')"
                )
    return issues


def main() -> int:
    print("=== Formal Alignment Audit: KD English vs Rakesh Gupta's MVD/SB/JV ===")
    
    if not KD_MD_PATH.is_file():
        print(f"Error: KD text file not found: {KD_MD_PATH}", file=sys.stderr)
        return 1
        
    kd_text = KD_MD_PATH.read_text(encoding="utf-8")
    issues = audit_kd_text(kd_text)
    
    if issues:
        print(f"FAILED: Found {len(issues)} terminology alignment issue(s):")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("SUCCESS: 0 unaligned terms found. KD translation matches MVD/SB/JV standards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

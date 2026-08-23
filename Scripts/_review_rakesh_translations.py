#!/usr/bin/env python3
"""Build an honest, reproducible KD terminology-alignment status report."""
from __future__ import annotations

import sys
from pathlib import Path

from _common import BASE
from _verify_kd_translation_alignment import EXPECTED_TERMS, count_literal

KD_DIR = BASE / "References" / "Madhyasth-Darshan" / "KD-Karm-Darshan-English"
KD_MD = KD_DIR / "KD-Karm-Darshan-English.md"
ALIGNMENT_MD_OUTPUT = KD_DIR / "KD-Rakesh-Gupta-Alignment-Audit.md"

# These require source-page/image review because the appropriate English choice is
# contextual; they are not asserted to be errors.
MANUAL_CANDIDATES = [
    ("मात्रा", "quantity / measure", "Confirm quantitative amount versus existential measure."),
]


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main() -> int:
    print("=== Building KD / Rakesh terminology alignment report ===")
    if not KD_MD.is_file():
        print(f"Error: KD body not found: {KD_MD}", file=sys.stderr)
        return 1

    body = KD_MD.read_text(encoding="utf-8")
    rows: list[tuple[str, str, str, int, str]] = []
    total_hits = 0
    for hindi, standard, deprecated in EXPECTED_TERMS:
        hit_count = sum(count_literal(body, variant) for variant in deprecated)
        total_hits += hit_count
        variants = ", ".join(f"`{variant}`" for variant in deprecated)
        status = "PASS" if hit_count == 0 else "FIX REQUIRED"
        rows.append((hindi, standard, variants, hit_count, status))

    lines = [
        "# Rakesh Gupta (MVD / SB / JV) Alignment Status for Karma Darshan",
        "",
        "**Updated:** August 23, 2026",
        "",
        "This is a deterministic body-level terminology guardrail for the working English translation. It checks known deprecated English variants against the standards established from Rakesh Gupta's MVD, SB, JV, and `MD-Mapping.xlsx`. It does **not** certify every lexical choice. The Hindi source PDF's embedded text layer is corrupt, so contextual Hindi verification must use rendered source-page images.",
        "",
        "## Confirmed alignment checks",
        "",
        "| Hindi concept | Current KD / Rakesh standard | Deprecated variants checked | Remaining hits | Status |",
        "| :--- | :--- | :--- | ---: | :--- |",
    ]
    for hindi, standard, variants, hits, status in rows:
        lines.append(
            f"| {escape_cell(hindi)} | {escape_cell(standard)} | {variants} | {hits} | **{status}** |"
        )

    lines.extend(
        [
            "",
            f"**Configured deprecated variants remaining:** {total_hits}",
            "",
            "## Approved deviations from Rakesh / MD-Mapping",
            "",
            "The default remains Rakesh Gupta's MVD/SB/JV terminology and `MD-Mapping.xlsx`. Raghava has explicitly approved these limited KD choices:",
            "",
            "- Bare/general/ontological **बल** is **strength**, instead of Rakesh's usual **force**. Named physical/interaction categories remain **force**; बल सम्पन्न / बल सम्पन्नता remain **forceful / forcefulness**.",
            "- **पोषण** is **nourishment**, where MD-Mapping's bare row has **nurturing**.",
            "- **प्रयोग** is **application / apply**, where Rakesh frequently uses **experiment / experimentation**.",
            "- Bare **भोग** is **enjoyment**, where MVD often uses **indulgence / sensory enjoyments**. Contextual फल भोगना remains **experience consequences/results**, भोक्ता is **enjoyer**, and उपभोग is **consumption**.",
            "",
            "## Follow-up decisions now resolved",
            "",
            "The August 23 follow-up also settled **अनुकूल = aligned** in relational faculty/activity chains (while environmental अनुकूल remains **favourable**), **प्रयास / प्रयत्न = endeavour** with **effort** reserved for श्रम, **द्वेष = malice** following MVD's direct definition, and the three अन्वेषण compounds as **truth- / motive- / instincts-oriented exploration**. The exact compounds are absent from MVD/JV; the last choice is compositional from their established base vocabulary. ऐषणा-त्रय is now **motive-trio**.",
            "",
            "## Items still requiring contextual alignment review",
            "",
            "These are review candidates, not confirmed errors:",
            "",
            "| Hindi term | Current candidate range | What remains to verify |",
            "| :--- | :--- | :--- |",
        ]
    )
    for hindi, choices, note in MANUAL_CANDIDATES:
        lines.append(f"| {hindi} | {choices} | {note} |")

    lines.extend(
        [
            "",
            "## Reproduce",
            "",
            "```powershell",
            "python Scripts/_verify_kd_translation_alignment.py",
            "python Scripts/_review_rakesh_translations.py",
            "```",
            "",
            "The review corpus is `MVD-Madhyasth-Darshan-Coexistentialism.md`, `SB-Samadhanatmak-Bhautikvad.md`, `JV-Jeevan-Vidya-An-Introduction.md`, and `MD-Mapping.xlsx` under `References/Madhyasth-Darshan/`.",
            "",
            "*Report generated by `Scripts/_review_rakesh_translations.py`.*",
        ]
    )

    ALIGNMENT_MD_OUTPUT.write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Wrote: {ALIGNMENT_MD_OUTPUT}")
    print(f"Configured deprecated variants remaining: {total_hits}")
    return 1 if total_hits else 0


if __name__ == "__main__":
    sys.exit(main())

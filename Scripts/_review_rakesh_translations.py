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
    ("आवेश", "excitation / charge (contextual)", "Confirm the boundary between physical charge and disturbed/excited state usages."),
    ("विन्यास", "arrangement", "Confirm whether the technical physical sense needs a more specific Rakesh-aligned rendering."),
    ("अनुभूति", "experiencing / realisation", "Current 'experiencing' distinguishes it from अनुभव; reconsider explicitly against MVD/JV usage."),
    ("काम", "kama (desire) / lust", "Current classical life-aim context is broader than 'lust'; settle the running English term explicitly."),
    ("अर्थ", "wealth / resources / meaning (contextual)", "Settle the economic and epistemic contextual rule explicitly."),
    ("कासा / आकूति / मेधा", "transliteration with contextual glosses", "Verify the obscure technical triad lexically before replacing its current glosses."),
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
            "The August 23 follow-up settled **अनुकूल = aligned** in relational faculty/activity chains (while environmental अनुकूल remains **favourable**), **प्रयास / प्रयत्न = endeavour** with **effort** reserved for श्रम, **द्वेष = malice** following MVD's direct definition, **तदाकार = absolute-resonance** following MVD p.80 and Hindi p.149 / English p.150, and the three अन्वेषण compounds as **truth- / motive- / instincts-oriented exploration**. The exact अन्वेषण compounds are absent from MVD/JV; that choice is compositional from their established base vocabulary. ऐषणा-त्रय is now **motive-trio**.",
            "",
            "A further alignment pass corrected **मेधस = brain**, **चुम्बकीयता = magnetism**, **प्रभाव क्षेत्र = field**, **संक्रमण / संक्रमणीयता = irreversible transition / irreversibility**, **विस्तार = expanse**, **फलन = outcome**, **यथास्थिति = existent state**, **तृप्ति = satisfaction**, **सारक / मारक = vitalising / devitalising**, **ज्ञेय = object of knowledge**, **दृश / दृश्य / दर्शन = seer / scene / worldview**, **ध्यान / ध्याता / ध्येय = concentration / one who concentrates / object of concentration**, the three classical vada names as transliterations, **नश्वरत्व = mortality**, **देवात्मा / भूतात्मा / दिव्यात्मा = deific / elemental / divine self**, **प्रभुसत्ता = supreme order**, and **विराग / वैराग्य / पर-वैराग्य = dispassion / detachment / supreme-detachment**.",
            "",
            "By explicit project decision, KD 3.13 uses **अनुप्राणित = propagated** in its molecule-to-molecule wave context, where MVD's 'invigorated/inspired' does not fit. The technical **क्षमता / योग्यता / पात्रता = capacity / ability / receptivity** trio is preserved because those qualities underlie recognition of relationships and evaluation; **पात्रता = worthiness** is confined to KD 3.10's reciprocal kindness/grace/compassion definition.",
            "",
            "KD 2 p.31 now follows MVD's explicit **जीवन-पुंज = jeevan-cloud**, replacing the former KD-specific **jeevan-cluster**. By explicit project decision, **प्राण वायु / प्राणवायु** is retained as ***pranavayu*** in KD rather than translated as **life-breath** or separated as *pran vayu*; MVD's different published rendering is **prana-air**.",
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

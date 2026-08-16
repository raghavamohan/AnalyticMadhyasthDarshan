#!/usr/bin/env python3
"""Derive durable external functions from the Pass-Three Jeevan matrix.

Pass Four keeps the activity rows anonymous while it performs two operations:

1. translate the frozen lifecycle features into five unnamed continuity
   channels, five durability tests, five arrangement scales, and five
   cross-cutting safeguards; and
2. compare several ways of assigning durable responsibility for those
   channels before restoring source names or Madhyasth Darshan's proposed
   social-function names.

The script uses only Python's standard library and writes LF-terminated,
deterministic research artifacts beside the source study notes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from collections import Counter
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Studies" / "The-Epistemology-of-Coexistence"
DEFAULT_ANONYMOUS = DATA_DIR / "Research-Data-Jeevan-Pass-Three-Anonymous-Matrix.csv"
DEFAULT_RESTORED = DATA_DIR / "Research-Data-Jeevan-Pass-Three-Restored-Memberships.csv"

ANONYMOUS_OUTPUT = "Research-Data-Jeevan-Pass-Four-Anonymous-Requirements.csv"
RESTORED_OUTPUT = "Research-Data-Jeevan-Pass-Four-Restored-Coverage.csv"
DIAGNOSTICS_OUTPUT = "Research-Data-Jeevan-Pass-Four-Bundle-Comparison.json"

BANNED_ANONYMOUS_TERMS = {
    "atma",
    "buddhi",
    "chitta",
    "vritti",
    "mun",
    "family",
    "institution",
    "education",
    "sanskar",
    "justice",
    "security",
    "health",
    "restraint",
    "production",
    "work",
    "exchange",
    "reserve",
    "school",
    "market",
    "government",
}


def token(prefix: str, values: Iterable[str]) -> set[str]:
    return {f"{prefix}:{value}" for value in values}


# These channel codes are unnamed in the anonymous artifact.  They distinguish
# the object whose continuity must be maintained: understood content, a claim
# between persons, bodily capability, transformed material means, or access to
# provision across persons and time.  Institution names are restored later.
CHANNEL_RULES = {
    "U01": {
        "strong": (
            token("operation", ("meaning_truth", "inquiry_discrimination", "communication_representation"))
            | token("consequence", ("meaning_truth", "inquiry_discrimination", "communication_representation"))
            | token("endpoint", ("meaning_truth", "inquiry_discrimination", "communication_representation"))
            | token("development", ("open_inquiry", "feedback_critique"))
            | token("correction", ("renewed_inquiry",))
            | token("continuity", ("inquiry_records_verification", "intergenerational_transmission"))
        ),
        "support": (
            token("locus", ("sentient_inward",))
            | token("dependency", ("accepted_meaning", "contemplative_design", "evaluation_discrimination", "realised_orientation"))
            | token("expression", ("language_representation", "consequence_visibility"))
            | token("evidence_req", ("competence_peer_review", "self_noncontradiction"))
            | token("evaluator", ("first_person", "skilled_peer"))
        ),
    },
    "U02": {
        "strong": (
            token("operation", ("care_development", "justice_protection", "reciprocal_relation"))
            | token("consequence", ("care_development", "justice_protection", "reciprocal_relation"))
            | token("endpoint", ("care_development", "justice_protection", "reciprocal_relation"))
            | token("development", ("noncoercive_agency", "relational_experience"))
            | token("correction", ("dialogue_changed_fulfilment", "protection_appeal", "repair_restitution"))
            | token("continuity", ("care_succession_agency", "relational_memory_repair", "public_review_dissent"))
        ),
        "support": (
            token("locus", ("relational",))
            | token("evaluator", ("affected_party", "counterpart"))
            | token("counterpart", ("direct", "durable"))
            | token("expression", ("counterpart_participation", "timing_discretion"))
            | token("evidence_req", ("affected_party_voice", "reciprocal_fulfilment"))
            | token("dependency", ("relational_feedback",))
        ),
    },
    "U03": {
        "strong": (
            token("operation", ("bodily_health", "aesthetic_affinity"))
            | token("consequence", ("bodily_health", "aesthetic_affinity"))
            | token("endpoint", ("bodily_health", "aesthetic_affinity"))
            | token("development", ("bodily_capability",))
            | token("correction", ("treatment_accommodation",))
        ),
        "support": (
            token("locus", ("embodied_person",))
            | token("evaluator", ("body_material",))
            | token("expression", ("embodied_capability",))
            | token("evidence_req", ("bodily_material_effect",))
            | token("false_positive", ("material_sensory_proxy", "short_term_satisfaction_proxy"))
        ),
    },
    "U04": {
        "strong": (
            token("operation", ("material_provision", "skill_design", "ecological_continuity"))
            | token("consequence", ("material_provision", "skill_design", "ecological_continuity"))
            | token("endpoint", ("material_provision", "skill_design", "ecological_continuity"))
            | token("correction", ("redesign_procedure", "retraining_changed_means", "ecological_restoration"))
            | token("continuity", ("skill_tools_maintenance", "ecological_regeneration"))
        ),
        "support": (
            token("locus", ("material_ecological",))
            | token("evaluator", ("body_material", "future_ecological", "skilled_peer"))
            | token("counterpart", ("material_ecological",))
            | token("development", ("material_access", "practice_skill"))
            | token("expression", ("material_means",))
            | token("evidence_req", ("bodily_material_effect", "long_horizon_effect"))
            | token("false_positive", ("harm_displacement_proxy", "output_efficiency_proxy"))
        ),
    },
    "U05": {
        "strong": (
            token("operation", ("collective_public", "continuity_transmission"))
            | token("consequence", ("collective_public", "continuity_transmission"))
            | token("endpoint", ("collective_public", "continuity_transmission"))
            | token("development", ("continuity_exposure", "material_access"))
            | token("continuity", ("reserve_reliable_provision", "public_review_dissent", "ecological_regeneration"))
        ),
        "support": (
            token("locus", ("collective_public", "temporal"))
            | token("evaluator", ("affected_party", "future_ecological"))
            | token("counterpart", ("collective", "durable"))
            | token("expression", ("consequence_visibility", "counterpart_participation"))
            | token("evidence_req", ("affected_party_voice", "long_horizon_effect"))
            | token("correction", ("protection_appeal", "repair_restitution", "ecological_restoration"))
            | token("false_positive", ("harm_displacement_proxy", "short_term_satisfaction_proxy"))
        ),
    },
}


DURABILITY_RULES = {
    "D01": (
        token("counterpart", ("durable",))
        | token("relation", ("sust", "trans"))
        | token(
            "continuity",
            (
                "care_succession_agency",
                "ecological_regeneration",
                "inquiry_records_verification",
                "intergenerational_transmission",
                "public_review_dissent",
                "relational_memory_repair",
                "reserve_reliable_provision",
                "skill_tools_maintenance",
            ),
        )
    ),
    "D02": (
        token("counterpart", ("collective", "direct", "durable", "material_ecological"))
        | token("evaluator", ("affected_party", "body_material", "counterpart", "future_ecological", "skilled_peer"))
        | token("expression", ("counterpart_participation",))
    ),
    "D03": (
        token("development", ("bodily_capability", "continuity_exposure", "material_access", "practice_skill"))
        | token("expression", ("embodied_capability", "language_representation", "material_means"))
        | token("continuity", ("care_succession_agency", "reserve_reliable_provision", "skill_tools_maintenance"))
    ),
    "D04": (
        token("evaluator", ("affected_party", "body_material", "future_ecological"))
        | token("correction", ("ecological_restoration", "protection_appeal", "repair_restitution", "treatment_accommodation"))
        | token(
            "false_positive",
            (
                "care_control_proxy",
                "compliance_force_proxy",
                "harm_displacement_proxy",
                "material_sensory_proxy",
                "output_efficiency_proxy",
                "short_term_satisfaction_proxy",
            ),
        )
    ),
    "D05": (
        token("evidence_req", ("affected_party_voice", "competence_peer_review", "long_horizon_effect"))
        | token("expression", ("consequence_visibility",))
        | token("correction", ("ecological_restoration", "protection_appeal", "redesign_procedure", "repair_restitution"))
        | token("continuity", ("inquiry_records_verification", "public_review_dissent"))
    ),
}


INTERFACE_RULES = {
    "X01": (
        token("development", ("feedback_critique", "open_inquiry"))
        | token("evidence_req", ("competence_peer_review", "self_noncontradiction"))
        | token("correction", ("renewed_inquiry",))
        | token("continuity", ("inquiry_records_verification",))
    ),
    "X02": (
        token("development", ("noncoercive_agency",))
        | token("evidence_req", ("affected_party_voice", "reciprocal_fulfilment"))
        | token("correction", ("dialogue_changed_fulfilment", "protection_appeal", "repair_restitution"))
        | token("continuity", ("public_review_dissent",))
    ),
    "X03": (
        token("development", ("bodily_capability", "material_access", "practice_skill"))
        | token("expression", ("embodied_capability", "material_means"))
        | token("correction", ("retraining_changed_means", "treatment_accommodation"))
    ),
    "X04": (
        token("counterpart", ("durable",))
        | token("relation", ("sust", "trans"))
        | DURABILITY_RULES["D01"]
    ),
    "X05": (
        token("evaluator", ("future_ecological",))
        | token("evidence_req", ("long_horizon_effect",))
        | token("correction", ("ecological_restoration",))
        | token("continuity", ("ecological_regeneration",))
        | token("false_positive", ("harm_displacement_proxy", "short_term_satisfaction_proxy"))
    ),
}


SCALE_RULES = {
    "S01": token("locus", ("sentient_inward", "embodied_person")) | token("evaluator", ("first_person",)),
    "S02": token("locus", ("relational",)) | token("counterpart", ("direct",)) | token("evaluator", ("counterpart",)),
    "S03": token("counterpart", ("durable",)) | token("continuity", ("care_succession_agency", "relational_memory_repair", "intergenerational_transmission")),
    "S04": token("locus", ("collective_public",)) | token("counterpart", ("collective",)) | token("continuity", ("skill_tools_maintenance", "reserve_reliable_provision")),
    "S05": token("locus", ("material_ecological", "temporal")) | token("evaluator", ("future_ecological",)) | token("evidence_req", ("long_horizon_effect",)) | token("continuity", ("ecological_regeneration", "public_review_dissent")),
}


CHANNEL_NAMES = {
    "U01": "education-sanskar",
    "U02": "justice-security",
    "U03": "health-restraint",
    "U04": "production-work",
    "U05": "exchange-reserve",
}

INTERFACE_NAMES = {
    "X01": "inquiry-and-evidence",
    "X02": "protected-participation",
    "X03": "embodiment-and-means",
    "X04": "continuity-and-succession",
    "X05": "ecological-and-long-horizon-consequence",
}

SCALE_NAMES = {
    "S01": "personal-practice",
    "S02": "direct-relation",
    "S03": "durable-care-and-intergenerational-relation",
    "S04": "shared-local-coordination",
    "S05": "wider-temporal-and-ecological-coordination",
}

DURABILITY_NAMES = {
    "D0": "no-durable-external-claim-derived",
    "D1": "supportive-or-episodic-external-condition",
    "D2": "durable-responsibility-distributed-or-conditional",
    "D3": "durable-responsibility-for-complete-lifecycle",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def row_tokens(row: dict[str, str]) -> set[str]:
    result: set[str] = set()
    for key, value in row.items():
        if key.startswith("feature_"):
            result.update(item for item in value.split(";") if item)
    return result


def channel_scores(tokens: set[str]) -> tuple[dict[str, int], dict[str, list[str]]]:
    scores: dict[str, int] = {}
    traces: dict[str, list[str]] = {}
    for channel_id, rule in CHANNEL_RULES.items():
        strong = tokens & rule["strong"]
        support = tokens & rule["support"]
        scores[channel_id] = 2 * len(strong) + len(support)
        traces[channel_id] = sorted(strong | support)
    return scores, traces


def durability_class(triggers: list[str], tokens: set[str]) -> str:
    necessary_expression = bool(tokens & token("scope", ("n_occ", "n_exp")))
    durable_relation = bool(tokens & token("relation", ("const", "prot", "sust", "trans")))
    if len(triggers) >= 4 or (len(triggers) >= 3 and (necessary_expression or durable_relation)):
        return "D3"
    if len(triggers) >= 3:
        return "D2"
    if triggers:
        return "D1"
    return "D0"


def classify_scales(tokens: set[str]) -> list[str]:
    domains = {
        item.split(":", 1)[1]
        for item in tokens
        if item.startswith(("operation:", "consequence:", "endpoint:", "evidence:"))
    }
    scales: list[str] = []
    if tokens & SCALE_RULES["S01"]:
        scales.append("S01")
    if (
        "locus:relational" in tokens
        or bool(domains & {"care_development", "justice_protection", "reciprocal_relation"})
        or {"counterpart:direct", "evaluator:counterpart"} <= tokens
    ):
        scales.append("S02")
    if (
        bool(
            tokens
            & token(
                "continuity",
                ("care_succession_agency", "intergenerational_transmission", "relational_memory_repair"),
            )
        )
        or (
            "counterpart:durable" in tokens
            and bool(domains & {"care_development", "continuity_transmission", "reciprocal_relation"})
        )
    ):
        scales.append("S03")
    if (
        "locus:collective_public" in tokens
        or bool(domains & {"collective_public", "material_provision", "skill_design"})
        or bool(tokens & token("continuity", ("public_review_dissent", "reserve_reliable_provision", "skill_tools_maintenance")))
    ):
        scales.append("S04")
    if (
        bool(tokens & SCALE_RULES["S05"])
        and (
            "locus:temporal" in tokens
            or "locus:material_ecological" in tokens
            or "evaluator:future_ecological" in tokens
            or "evidence_req:long_horizon_effect" in tokens
        )
    ):
        scales.append("S05")
    return scales


def classify_anonymous(
    row: dict[str, str], membership_ratio: float = 0.70
) -> dict[str, str]:
    tokens = row_tokens(row)
    scores, traces = channel_scores(tokens)
    domains = {
        item.split(":", 1)[1]
        for item in tokens
        if item.startswith(("operation:", "consequence:", "endpoint:", "evidence:"))
    }
    material_access_anchor = (
        "material_provision" in domains
        or "development:material_access" in tokens
        or "continuity:reserve_reliable_provision" in tokens
    )
    distribution_anchor = bool(
        tokens
        & (
            token("locus", ("collective_public", "temporal"))
            | token("counterpart", ("collective", "durable"))
            | token("evaluator", ("affected_party", "future_ecological"))
            | token("evidence_req", ("long_horizon_effect",))
        )
    )
    eligible = {channel_id for channel_id in scores if channel_id != "U05"}
    if material_access_anchor and distribution_anchor:
        eligible.add("U05")
    best_score = max(scores[channel_id] for channel_id in eligible)
    membership_threshold = max(4, math.ceil(membership_ratio * best_score))
    channels = [
        channel_id
        for channel_id, score in scores.items()
        if channel_id in eligible and score >= membership_threshold
    ]
    if not channels:
        channels = [max(eligible, key=lambda item: (scores[item], item))]
    triggers = [rule_id for rule_id, rule in DURABILITY_RULES.items() if tokens & rule]
    interfaces = [rule_id for rule_id, rule in INTERFACE_RULES.items() if tokens & rule]
    scales = classify_scales(tokens)
    trace = [f"{channel_id}=" + "+".join(traces[channel_id]) for channel_id in channels]
    return {
        "anonymous_id": row["anonymous_id"],
        "durability_triggers": ";".join(triggers),
        "durability_class": durability_class(triggers, tokens),
        "channel_memberships": ";".join(channels),
        "u01_score": str(scores["U01"]),
        "u02_score": str(scores["U02"]),
        "u03_score": str(scores["U03"]),
        "u04_score": str(scores["U04"]),
        "u05_score": str(scores["U05"]),
        "interface_requirements": ";".join(interfaces),
        "arrangement_scales": ";".join(scales),
        "input_residual": "yes" if "open:yes" in tokens else "no",
        "trace_basis": " | ".join(trace),
    }


BUNDLES = [
    {
        "id": "B01",
        "name": "stable-core-only",
        "functions": [("orientation", {"U01"}), ("care", {"U02"}), ("reciprocity", {"U02"}), ("body", {"U03"})],
        "claim": "Treat only the four stable middle cores as durable bearers; leave both bridges unassigned.",
    },
    {
        "id": "B02",
        "name": "three-domain-compression",
        "functions": [("meaning-agency", {"U01"}), ("relation", {"U02"}), ("body-material", {"U03", "U04", "U05"})],
        "claim": "Make the three stable coarse domains the durable functional partition.",
    },
    {
        "id": "B03",
        "name": "integrated-provision-four",
        "functions": [("formation", {"U01"}), ("relation", {"U02"}), ("body", {"U03"}), ("provision", {"U04", "U05"})],
        "claim": "Separate body from material provision but combine making with allocation and reserve.",
    },
    {
        "id": "B04",
        "name": "five-continuity-basis",
        "functions": [("u01", {"U01"}), ("u02", {"U02"}), ("u03", {"U03"}), ("u04", {"U04"}), ("u05", {"U05"})],
        "claim": "Assign one durable responsibility to each irreducible continuity channel.",
    },
    {
        "id": "B05",
        "name": "seven-specialized",
        "functions": [("formation", {"U01"}), ("inquiry", {"U01"}), ("care", {"U02"}), ("justice", {"U02"}), ("body", {"U03"}), ("making", {"U04"}), ("circulation", {"U05"})],
        "claim": "Split formation from inquiry and care from adjudication while retaining the other three channels.",
    },
]


HIGH_CONFLICT_PAIRS = {
    frozenset(("U01", "U02")),
    frozenset(("U02", "U04")),
    frozenset(("U02", "U05")),
    frozenset(("U03", "U04")),
    frozenset(("U03", "U05")),
    frozenset(("U04", "U05")),
}


def compare_bundle(bundle: dict, member_channels: list[set[str]]) -> dict:
    functions = bundle["functions"]
    covered = set().union(*(channels for _, channels in functions))
    total_obligations = sum(len(channels) for channels in member_channels)
    covered_obligations = sum(len(channels & covered) for channels in member_channels)
    residual_members = sum(bool(channels - covered) for channels in member_channels)
    multiplicity = Counter(channel for _, channels in functions for channel in channels)
    forced_pairs: set[frozenset[str]] = set()
    conflict_pairs: set[frozenset[str]] = set()
    for _, channels in functions:
        for left, right in itertools.combinations(sorted(channels), 2):
            pair = frozenset((left, right))
            forced_pairs.add(pair)
            if pair in HIGH_CONFLICT_PAIRS:
                conflict_pairs.add(pair)
    split_channels = {channel: count for channel, count in multiplicity.items() if count > 1}
    full_coverage = covered_obligations == total_obligations
    practical_minimal = full_coverage and not forced_pairs and not split_channels
    return {
        "id": bundle["id"],
        "name": bundle["name"],
        "claim": bundle["claim"],
        "nominal_function_count": len(functions),
        "covered_channels": sorted(covered),
        "coverage_percent": round(100 * covered_obligations / total_obligations, 2),
        "residual_member_count": residual_members,
        "forced_combination_count": len(forced_pairs),
        "high_conflict_combination_count": len(conflict_pairs),
        "unnecessary_split_count": sum(count - 1 for count in split_channels.values()),
        "independent_correction_structurally_available": not conflict_pairs,
        "full_coverage": full_coverage,
        "practical_minimal_at_selected_grain": practical_minimal,
        "numerical_uniqueness_established": False,
    }


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(anonymous_source: Path, restored_source: Path, output_dir: Path) -> dict:
    anonymous_rows = read_rows(anonymous_source)
    restored_rows = read_rows(restored_source)
    if len(anonymous_rows) != 122 or len(restored_rows) != 122:
        raise ValueError("Pass Four requires exactly 122 anonymous and restored records")
    restored_by_id = {row["anonymous_id"]: row for row in restored_rows}
    if set(restored_by_id) != {row["anonymous_id"] for row in anonymous_rows}:
        raise ValueError("Anonymous and restored Pass-Three IDs do not match")

    classified = [classify_anonymous(row) for row in anonymous_rows]
    output_dir.mkdir(parents=True, exist_ok=True)
    anonymous_path = output_dir / ANONYMOUS_OUTPUT
    anonymous_fields = list(classified[0])
    write_csv(anonymous_path, classified, anonymous_fields)

    restored_output: list[dict[str, str]] = []
    for derived in classified:
        source = restored_by_id[derived["anonymous_id"]]
        channels = derived["channel_memberships"].split(";")
        interfaces = [INTERFACE_NAMES[item] for item in derived["interface_requirements"].split(";") if item]
        scales = [SCALE_NAMES[item] for item in derived["arrangement_scales"].split(";") if item]
        restored_output.append(
            {
                "anonymous_id": derived["anonymous_id"],
                "source_id": source["source_id"],
                "member_name": source["member_name"],
                "faculty": source["faculty"],
                "middle_memberships": source["middle_memberships"],
                "durability_class": DURABILITY_NAMES[derived["durability_class"]],
                "derived_function_memberships": ";".join(CHANNEL_NAMES[item] for item in channels),
                "cross_cutting_requirements": ";".join(interfaces),
                "arrangement_scales": ";".join(scales),
                "pass_three_residual": source["residual_flag"],
            }
        )
    restored_path = output_dir / RESTORED_OUTPUT
    write_csv(restored_path, restored_output, list(restored_output[0]))

    member_channels = [set(row["channel_memberships"].split(";")) for row in classified]
    bundle_results = [compare_bundle(bundle, member_channels) for bundle in BUNDLES]
    channel_counts = Counter(channel for channels in member_channels for channel in channels)
    durable_channel_counts = Counter(
        channel
        for row, channels in zip(classified, member_channels)
        if row["durability_class"] in {"D2", "D3"}
        for channel in channels
    )
    durability_counts = Counter(row["durability_class"] for row in classified)
    interface_counts = Counter(
        interface
        for row in classified
        for interface in row["interface_requirements"].split(";")
        if interface
    )
    scale_counts = Counter(
        scale
        for row in classified
        for scale in row["arrangement_scales"].split(";")
        if scale
    )
    family_like_count = sum(
        "S03" in row["arrangement_scales"].split(";")
        and "U02" in row["channel_memberships"].split(";")
        and bool({"U01", "U03", "U04", "U05"} & set(row["channel_memberships"].split(";")))
        for row in classified
    )
    threshold_sensitivity = {}
    for ratio in (0.65, 0.70, 0.75):
        sensitivity_rows = [classify_anonymous(row, ratio) for row in anonymous_rows]
        sensitivity_channels = Counter(
            channel
            for row in sensitivity_rows
            for channel in row["channel_memberships"].split(";")
        )
        threshold_sensitivity[f"{ratio:.2f}"] = {
            "channel_obligation_count": sum(sensitivity_channels.values()),
            "channel_member_counts": dict(sorted(sensitivity_channels.items())),
            "all_five_channels_present": set(sensitivity_channels) == set(CHANNEL_RULES),
        }
    diagnostics = {
        "method": "pass-four-rule-based-anonymous-durable-function-derivation",
        "anonymous_source": anonymous_source.name,
        "restored_source": restored_source.name,
        "member_count": len(classified),
        "channel_obligation_count": sum(channel_counts.values()),
        "channel_member_counts": dict(sorted(channel_counts.items())),
        "durable_channel_member_counts": dict(sorted(durable_channel_counts.items())),
        "durability_class_counts": dict(sorted(durability_counts.items())),
        "interface_member_counts": dict(sorted(interface_counts.items())),
        "arrangement_scale_member_counts": dict(sorted(scale_counts.items())),
        "durable_relational_integrative_member_count": family_like_count,
        "membership_threshold_sensitivity": threshold_sensitivity,
        "bundle_comparisons": bundle_results,
        "selected_bundle": "B04",
        "selected_bundle_reason": "Only tested bundle with full member-channel coverage, no forced channel combination, and no unnecessary channel split at the selected grain.",
        "interpretive_limit": "Selection establishes practical minimality of five functional responsibilities at this grain, not five organizations and not numerical uniqueness across all possible decompositions.",
        "anonymous_matrix_sha256": sha256(anonymous_path),
    }
    diagnostics_path = output_dir / DIAGNOSTICS_OUTPUT
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8", newline="")
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anonymous", type=Path, default=DEFAULT_ANONYMOUS)
    parser.add_argument("--restored", type=Path, default=DEFAULT_RESTORED)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    diagnostics = run(args.anonymous, args.restored, args.output_dir)
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()

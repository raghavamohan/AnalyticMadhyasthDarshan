#!/usr/bin/env python3
"""Run the Pass-Five counterfactual validation of the Jeevan social model.

The pass does not simulate social outcomes or manufacture empirical evidence.
It records a fixed set of materially different arrangements and adverse cases,
checks each against explicit invariants and safeguards, and relates each case
back to the 122-member Pass-Four coverage register.  The outputs are a
deterministic argument register, an evidence protocol, and summary diagnostics.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Studies" / "The-Epistemology-of-Coexistence"
DEFAULT_COVERAGE = DATA_DIR / "Research-Data-Jeevan-Pass-Four-Restored-Coverage.csv"
DEFAULT_DIAGNOSTICS = DATA_DIR / "Research-Data-Jeevan-Pass-Four-Bundle-Comparison.json"

CASES_OUTPUT = "Research-Data-Jeevan-Pass-Five-Validation-Cases.csv"
EVIDENCE_OUTPUT = "Research-Data-Jeevan-Pass-Five-Evidence-Protocol.csv"
SUMMARY_OUTPUT = "Research-Data-Jeevan-Pass-Five-Validation-Summary.json"

FUNCTIONS = {
    "U01": "education-sanskar",
    "U02": "justice-security",
    "U03": "health-restraint",
    "U04": "production-work",
    "U05": "exchange-reserve",
}

SAFEGUARDS = {
    "X01": "inquiry-and-evidence",
    "X02": "protected-participation",
    "X03": "embodiment-and-means",
    "X04": "continuity-and-succession",
    "X05": "ecological-and-long-horizon-consequence",
}

FAMILY_INVARIANTS = (
    "durable-membership",
    "intergenerational-learning",
    "dependency-care",
    "reciprocal-recognition-and-voice",
    "daily-bodily-care",
    "shared-useful-work",
    "need-assessment-and-dependable-access",
    "external-protection-and-appeal",
)


def case(
    case_id: str,
    challenge_class: str,
    arrangement: str,
    functions: str,
    safeguards: str,
    invariant_test: str,
    conditions_present: str,
    conditions_absent: str,
    false_positive: str,
    observable_evidence: str,
    result: str,
    model_effect: str,
    revision_route: str,
) -> dict[str, str]:
    return {
        "case_id": case_id,
        "challenge_class": challenge_class,
        "arrangement_or_condition": arrangement,
        "function_codes": functions,
        "safeguard_codes": safeguards,
        "invariant_under_test": invariant_test,
        "conditions_present": conditions_present,
        "conditions_absent": conditions_absent,
        "false_positive_risk": false_positive,
        "observable_evidence_required": observable_evidence,
        "analytical_result": result,
        "model_effect": model_effect,
        "revision_route": revision_route,
        "empirical_status": "not-observed-counterfactual",
    }


CASES = (
    case(
        "FAM-01",
        "family-equivalence",
        "A durable non-kin shared-life group carries care, learning, work, provision, voice, and outside appeal across generations.",
        "U01;U02;U03;U04;U05",
        "X01;X02;X03;X04;X05",
        ";".join(FAMILY_INVARIANTS),
        ";".join(FAMILY_INVARIANTS),
        "",
        "legal-or-biological-label-as-proof",
        "member-level learning; dependency care; reciprocal voice; bodily condition; useful work; need access; independent appeal; continuity after turnover",
        "equivalent-arrangement",
        "survives-with-refinement",
        "Narrow family from a necessary kinship form to a durable shared-life invariant.",
    ),
    case(
        "FAM-02",
        "family-false-positive",
        "A biologically related household provides material goods but governs dependants through coercion and blocks outside appeal.",
        "U01;U02;U03;U04;U05",
        "X01;X02;X03;X04",
        ";".join(FAMILY_INVARIANTS),
        "durable-membership;daily-bodily-care;shared-useful-work;need-assessment-and-dependable-access",
        "intergenerational-learning;dependency-care;reciprocal-recognition-and-voice;external-protection-and-appeal",
        "kinship;material-provision;obedience;reported-family-unity",
        "confidential member voice; freedom to refuse; access to outside protection; evidence of learning and repair without retaliation",
        "arrangement-rejected",
        "survives",
        "Reject family status, provision, or compliance as sufficient evidence of the family invariant.",
    ),
    case(
        "FAM-03",
        "family-equivalence",
        "A multi-local care network sustains children, elders, learning, shared provision, and appeal despite migration and non-co-residence.",
        "U01;U02;U03;U04;U05",
        "X01;X02;X03;X04",
        ";".join(FAMILY_INVARIANTS),
        ";".join(FAMILY_INVARIANTS),
        "",
        "co-residence-as-proof",
        "portable care commitments; member voice across locations; continuity of provision; learning and repair after movement",
        "equivalent-with-portability",
        "survives-with-refinement",
        "Remove co-residence and locality from the invariant; add portable continuity and cross-boundary appeal.",
    ),
    case(
        "BND-01",
        "function-boundary",
        "Production and exchange share one administration while purposes, ledgers, affected-party rights, health evidence, and appeal remain distinct.",
        "U04;U05",
        "X01;X02;X03;X04;X05",
        "material-transformation-and-distributed-availability-remain-separately-evaluable",
        "separate-purpose-accounts;transparent-stocks;user-and-worker-voice;independent-health-and-ecology-review;outside-appeal",
        "",
        "administrative-unity-as-functional-unity",
        "separate production and allocation records; stop rights; stock and need visibility; independent review; correction outcomes",
        "combined-delivery-conditionally-adequate",
        "survives-with-refinement",
        "Permit administrative combination while retaining two functional responsibilities and independent correction.",
    ),
    case(
        "BND-02",
        "function-boundary",
        "One producer-distributor controls output, price, stock information, health evidence, and review.",
        "U04;U05",
        "X01;X02;X03;X04;X05",
        "material-transformation-and-distributed-availability-remain-separately-evaluable",
        "integrated-delivery",
        "separate-purpose-accounts;transparent-stocks;affected-party-voice;independent-health-and-ecology-review;outside-appeal",
        "output;profit;market-share;delivery-speed",
        "need and exclusion records; stock accuracy; worker and user voice; displaced health and ecological effects; independent remedy",
        "arrangement-rejected",
        "survives",
        "Retain the production-exchange distinction where one authority would otherwise judge its own allocation and harms.",
    ),
    case(
        "BND-03",
        "function-boundary",
        "An autonomous scientific organisation supplies inquiry, measurement, and correction across all five functions.",
        "U01;U02;U03;U04;U05",
        "X01;X05",
        "whether-science-maintains-a-sixth-continuity-object",
        "open-inquiry;method-competence;reproducible-evidence;freedom-to-report-adverse-results;cross-functional-access",
        "",
        "publication-count;prestige;technical-novelty",
        "reproducibility;adverse-result publication; affected-party access; correction of downstream decisions",
        "specialised-organisation-no-new-function",
        "survives-with-refinement",
        "Treat science as an independently organised method and safeguard spanning the five continuity objects.",
    ),
    case(
        "BND-04",
        "function-boundary",
        "A separate governing body coordinates decision rights, reasons, resources, review, and appeal across the five functions.",
        "U01;U02;U03;U04;U05",
        "X02;X04",
        "whether-governance-maintains-a-sixth-continuity-object",
        "affected-party-voice;published-reasons;limited-authority;independent-review;appeal;succession",
        "",
        "legal-compliance;administrative-order;electoral-victory",
        "access to reasons; participation distribution; appeal outcomes; correction of governing error; absence of retaliation",
        "specialised-organisation-no-new-function",
        "survives-with-refinement",
        "Treat governance as cross-functional coordination and accountability, not an additional human endpoint.",
    ),
    case(
        "BND-05",
        "function-boundary",
        "An independent ecological monitoring and protection organisation represents delayed, remote, and future material consequence.",
        "U03;U04;U05",
        "X01;X03;X05",
        "whether-ecological-protection-maintains-a-sixth-continuity-object",
        "long-horizon-measurement;remote-and-future-representation;independence-from-producer-and-beneficiary;precaution;restoration-review",
        "",
        "current-compliance;local-benefit;short-term-productivity",
        "baseline and delayed effects; remote affected-party evidence; uncertainty; prevention; restoration and recurrence",
        "specialised-organisation-no-new-function",
        "survives-with-refinement",
        "Treat ecology as an independently organised consequence horizon spanning bodily capability, material transformation, and future availability.",
    ),
    case(
        "BND-06",
        "function-boundary",
        "A specialised care organisation supports dependency, health, learning, relationship, and continuity.",
        "U01;U02;U03;U05",
        "X02;X03;X04",
        "whether-care-maintains-a-sixth-continuity-object",
        "person-centred-support;continuity;accommodation;voice;outside-review",
        "",
        "service-volume;custodial-order;caregiver-intention",
        "capability and voice of the cared-for person; bodily outcomes; continuity; relationship quality; independent complaint and remedy",
        "specialised-organisation-no-new-function",
        "survives-with-refinement",
        "Treat care as a relation and cross-channel responsibility whose concrete object remains within the five functions.",
    ),
    case(
        "ADV-01",
        "adverse-condition",
        "Severe scarcity makes simultaneous fulfilment of all stated needs impossible.",
        "U02;U03;U04;U05",
        "X01;X02;X03;X04;X05",
        "whether-scarcity-suspends-justice-health-work-or-reserve",
        "transparent-stock-and-need-evidence;participatory-priority-rules;minimum-protection;review;restoration-plan",
        "full-current-provision",
        "aggregate-output;equal-rations-with-unequal-need;emergency-necessity",
        "disaggregated need and access; avoidable harm; burden distribution; reserve use; reasons; appeal; recovery over time",
        "functions-remain-priority-rules-refined",
        "survives-with-refinement",
        "Specify priority, burden, reserve, appeal, and restoration rules rather than treating scarcity as suspension of the functions.",
    ),
    case(
        "ADV-02",
        "adverse-condition",
        "Disability or dependency prevents identical role performance and requires supported participation.",
        "U01;U02;U03;U04;U05",
        "X01;X02;X03;X04",
        "whether-universal-participation-means-identical-performance",
        "accessible-communication;accommodation;supported-choice;care;role-adaptation;representation-with-review",
        "identical-performance",
        "formal-equal-treatment;attendance;proxy-consent",
        "person-specific capability; supported preference; access and contribution; bodily condition; review of representatives; correction access",
        "equal-availability-refined",
        "survives-with-refinement",
        "Define universality as supported capability, voice, access, and correction, not identical independent performance.",
    ),
    case(
        "ADV-03",
        "adverse-condition",
        "A household or workplace controls livelihood, information, and complaint channels and punishes dissent.",
        "U01;U02;U03;U04;U05",
        "X01;X02;X03;X04",
        "whether-a-close-or-productive-unit-may-be-its-own-final-evaluator",
        "confidential-evidence;outside-protection;portable-access-to-provision;anti-retaliation;remedy",
        "safe-internal-correction",
        "obedience;low-complaint-rate;retention;reported-loyalty",
        "confidential testimony; exit feasibility; retaliation indicators; independent findings; repair and recurrence",
        "outside-correction-required",
        "survives-with-refinement",
        "Require evidence and appeal beyond every organisation whose power or conduct is being evaluated.",
    ),
    case(
        "ADV-04",
        "adverse-condition",
        "Participants disagree about relationship fulfilment, material consequence, or the meaning of evidence.",
        "U01;U02",
        "X01;X02;X04",
        "whether-consensus-is-required-as-proof-of-correct-functioning",
        "reasoned-dissent;plural-standpoints;shared-observation;revisable-decision;appeal",
        "consensus",
        "majority-support;institutional-reputation;forced-harmony",
        "reasons and counterevidence; affected-party voice; competence evidence; decision revision; remedy without retaliation",
        "plural-evidence-required",
        "survives-with-refinement",
        "Make disagreement visible and route contested claims through plural evidence and revisable correction.",
    ),
    case(
        "ADV-05",
        "adverse-condition",
        "Migration breaks locality, documentation, familiar relationships, and access to care or reserve.",
        "U01;U02;U03;U05",
        "X02;X03;X04",
        "whether-continuity-depends-on-fixed-residence-or-membership",
        "portable-records;recognised-voice;transferable-access;new-relationship-entry;cross-boundary-appeal",
        "fixed-local-continuity",
        "formal-residence;local-membership;family-presence",
        "continuity of learning, care, voice, provision, and appeal before, during, and after movement",
        "scale-and-portability-refined",
        "survives-with-refinement",
        "Add portable continuity and nested responsibility where consequence or movement crosses local boundaries.",
    ),
    case(
        "ADV-06",
        "adverse-condition",
        "A technically concentrated system controls knowledge, infrastructure, work, allocation, and its own audit.",
        "U01;U02;U03;U04;U05",
        "X01;X02;X03;X04;X05",
        "whether-technical-competence-may-substitute-for-affected-party-control-and-correction",
        "inspectability;distributed-competence;affected-party-rights;stop-and-appeal-rights;independent-audit;fallback-capability",
        "distributed-operational-control",
        "accuracy;efficiency;expert-certification;system-uptime",
        "error distribution; exclusion; bodily and material effects; contestability; audit independence; recovery after failure",
        "power-safeguards-strengthened",
        "survives-with-refinement",
        "Require technical systems to remain inspectable, contestable, interruptible, and correctable outside their controlling authority.",
    ),
    case(
        "ADV-07",
        "adverse-condition",
        "Ecological damage appears after long delay and outside the producing or consuming locality.",
        "U03;U04;U05",
        "X01;X03;X05",
        "whether-immediate-participant-evidence-is-sufficient",
        "baseline-measurement;causal-monitoring;future-and-remote-proxies;precaution;liability;restoration",
        "immediate-harm",
        "current-user-satisfaction;local-compliance;short-term-productivity",
        "long-horizon material measures; remote affected-party evidence; uncertainty bounds; restoration effectiveness; recurrence",
        "long-horizon-evidence-strengthened",
        "survives-with-refinement",
        "Give future and remote consequences representation through monitoring, precaution, responsibility, and restoration.",
    ),
    case(
        "UNI-01",
        "universal-access",
        "A competent minority understands and manages all functions while most people comply and receive outputs.",
        "U01;U02;U03;U04;U05",
        "X01;X02;X03;X04",
        "whether-function-availability-to-an-elite-satisfies-common-jeevan-capacity",
        "expert-performance;service-output",
        "each-person-understanding;meaningful-voice;capability-to-contribute;correction-access;succession-beyond-elite",
        "expertise;efficiency;aggregate-prosperity;order",
        "person-level distribution of understanding, voice, skill, access, contribution, challenge, and learning over time",
        "universality-test-failed",
        "survives-with-refinement",
        "Add a person-level availability test to every function; aggregate performance cannot establish universal fulfilment.",
    ),
    case(
        "FP-01",
        "false-positive",
        "High output and prosperity conceal unsafe work, depleted ecology, unequal access, and fragile reserve.",
        "U03;U04;U05",
        "X01;X02;X03;X05",
        "whether-output-and-aggregate-prosperity-establish-material-fulfilment",
        "high-output;aggregate-surplus",
        "safe-work;regeneration;dependable-equitable-access;resilient-reserve",
        "output;profit;aggregate-prosperity;immediate-consumption",
        "worker health; input and waste cycles; user need; access distribution; reserve resilience; delayed effects",
        "false-positive-rejected",
        "survives",
        "Require bodily, distributive, and ecological evidence alongside material output.",
    ),
    case(
        "FP-02",
        "false-positive",
        "Compliance and reported satisfaction are produced by dependence, habituation, information control, or fear of retaliation.",
        "U01;U02",
        "X01;X02;X04",
        "whether-compliance-or-self-report-alone-establishes-understanding-and-mutual-fulfilment",
        "reported-satisfaction;low-open-conflict",
        "free-inquiry;informed-voice;safe-dissent;independent-corroboration;repair",
        "compliance;consensus;reputation;reported-satisfaction",
        "confidential report; comprehension and reasons; safe dissent; counterpart evidence; independent review; correction after challenge",
        "false-positive-rejected",
        "survives",
        "Require freedom, comprehension, counterpart evidence, and correction access before accepting satisfaction or compliance as evidence.",
    ),
)


EVIDENCE_PROTOCOL = (
    {
        "function_code": "U01",
        "function": "education-sanskar",
        "continuity_object": "understood-orientation",
        "minimum_observables": "person-can-state-test-apply-and-revise;learning-visible-in-conduct;transmission-survives-teacher-turnover",
        "required_standpoints": "first-person;learner;counterpart;competent-peer",
        "insufficient_proxy": "attendance;certificate;recitation;teacher-reputation",
        "correction_test": "inquiry-and-dissent-remain-safe-and-can-change-content-or-practice",
        "person_level_test": "each-person-has-access-to-language-inquiry-feedback-and-a-path-to-demonstrated-competence",
    },
    {
        "function_code": "U02",
        "function": "justice-security",
        "continuity_object": "claims-between-persons",
        "minimum_observables": "recognition;informed-consent-or-refusal;reciprocal-fulfilment;harm-repair;non-retaliatory-appeal",
        "required_standpoints": "each-counterpart;affected-third-party;protector;independent-reviewer",
        "insufficient_proxy": "obedience;majority-support;low-complaint-rate;reported-harmony",
        "correction_test": "the-less-powerful-party-can-trigger-protection-review-and-effective-remedy",
        "person_level_test": "each-person-has-voice-boundary-refusal-reasons-appeal-and-protection",
    },
    {
        "function_code": "U03",
        "function": "health-restraint",
        "continuity_object": "bodily-capability",
        "minimum_observables": "bodily-report;condition;exposure;accommodation;intervention;delayed-outcome",
        "required_standpoints": "embodied-person;caregiver;health-skilled-peer;environmental-observer",
        "insufficient_proxy": "attendance;productivity;appearance;absence-of-diagnosis",
        "correction_test": "the-person-can-obtain-explanation-refuse-unsafe-exposure-and-secure-care-or-accommodation",
        "person_level_test": "each-person-has-sufficient-means-care-consent-accommodation-and-appeal",
    },
    {
        "function_code": "U04",
        "function": "production-work",
        "continuity_object": "transformed-material-means",
        "minimum_observables": "assessed-need;inputs;skill;labour-condition;use;maintenance;waste;ecological-effect",
        "required_standpoints": "worker;user;material-custodian;safety-witness;ecological-observer",
        "insufficient_proxy": "output;profit;saleability;efficiency;worker-compliance",
        "correction_test": "affected-persons-can-stop-unsafe-work-and-trigger-redesign-repair-restoration-or-cessation",
        "person_level_test": "each-person-has-access-to-useful-skill-safe-contribution-user-feedback-and-challenge",
    },
    {
        "function_code": "U05",
        "function": "exchange-reserve",
        "continuity_object": "distributed-availability-across-persons-and-time",
        "minimum_observables": "need;stock;terms;access;exclusion;reserve;future-reliability;displaced-effect",
        "required_standpoints": "person-stating-need;producer;receiver;custodian;future-or-remote-proxy;independent-reviewer",
        "insufficient_proxy": "transaction-volume;price;aggregate-surplus;delivery-speed",
        "correction_test": "stock-terms-and-priorities-are-inspectable-and-exclusion-or-exploitation-can-be-remedied",
        "person_level_test": "each-person-has-dependable-access-need-voice-transparent-terms-and-appeal",
    },
)


def split_codes(value: str) -> list[str]:
    return [part for part in value.split(";") if part]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_inputs(
    coverage_rows: list[dict[str, str]], diagnostics: dict[str, object]
) -> dict[str, set[str]]:
    if len(coverage_rows) != 122:
        raise ValueError(f"Expected 122 Pass-Four members, found {len(coverage_rows)}")
    if diagnostics.get("selected_bundle") != "B04":
        raise ValueError("Pass Five requires the frozen B04 Pass-Four comparison result")

    function_members: dict[str, set[str]] = {code: set() for code in FUNCTIONS}
    known_names = set(FUNCTIONS.values())
    for row in coverage_rows:
        memberships = set(split_codes(row["derived_function_memberships"]))
        unknown = memberships - known_names
        if unknown:
            raise ValueError(f"Unknown function memberships: {sorted(unknown)}")
        for code, name in FUNCTIONS.items():
            if name in memberships:
                function_members[code].add(row["anonymous_id"])

    expected = diagnostics["channel_member_counts"]
    observed = {code: len(members) for code, members in function_members.items()}
    if observed != expected:
        raise ValueError(f"Pass-Four coverage drift: expected {expected}, found {observed}")
    return function_members


def classify_cases(function_members: dict[str, set[str]]) -> list[dict[str, object]]:
    classified: list[dict[str, object]] = []
    seen: set[str] = set()
    for source in CASES:
        row: dict[str, object] = dict(source)
        case_id = source["case_id"]
        if case_id in seen:
            raise ValueError(f"Duplicate case id: {case_id}")
        seen.add(case_id)

        function_codes = split_codes(source["function_codes"])
        safeguard_codes = split_codes(source["safeguard_codes"])
        if not function_codes or not set(function_codes) <= set(FUNCTIONS):
            raise ValueError(f"Invalid function codes in {case_id}")
        if not set(safeguard_codes) <= set(SAFEGUARDS):
            raise ValueError(f"Invalid safeguard codes in {case_id}")

        exposed = set().union(*(function_members[code] for code in function_codes))
        row["affected_member_count"] = len(exposed)
        row["affected_member_percent"] = round(100 * len(exposed) / 122, 1)
        row["new_continuity_object_found"] = "no"
        classified.append(row)
    return classified


def run(coverage_path: Path, diagnostics_path: Path, output_dir: Path) -> dict[str, object]:
    coverage_rows = read_csv(coverage_path)
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    function_members = validate_inputs(coverage_rows, diagnostics)
    classified = classify_cases(function_members)

    output_dir.mkdir(parents=True, exist_ok=True)
    cases_path = output_dir / CASES_OUTPUT
    evidence_path = output_dir / EVIDENCE_OUTPUT
    summary_path = output_dir / SUMMARY_OUTPUT
    write_csv(cases_path, classified, list(classified[0]))
    write_csv(evidence_path, EVIDENCE_PROTOCOL, list(EVIDENCE_PROTOCOL[0]))

    by_class = Counter(row["challenge_class"] for row in classified)
    by_result = Counter(row["analytical_result"] for row in classified)
    by_effect = Counter(row["model_effect"] for row in classified)
    all_functions_tested = set().union(
        *(set(split_codes(row["function_codes"])) for row in classified)
    )
    all_safeguards_tested = set().union(
        *(set(split_codes(row["safeguard_codes"])) for row in classified)
    )

    summary: dict[str, object] = {
        "method": "pass-five-structured-counterfactual-and-adverse-case-validation",
        "empirical_status": "analytical-only; no field observations or causal outcome estimates",
        "pass_four_source": coverage_path.name,
        "pass_four_member_count": len(coverage_rows),
        "pass_four_selected_bundle": diagnostics["selected_bundle"],
        "case_count": len(classified),
        "challenge_class_counts": dict(sorted(by_class.items())),
        "analytical_result_counts": dict(sorted(by_result.items())),
        "model_effect_counts": dict(sorted(by_effect.items())),
        "functions_tested": sorted(all_functions_tested),
        "safeguards_tested": sorted(all_safeguards_tested),
        "family_invariant_condition_count": len(FAMILY_INVARIANTS),
        "new_continuity_object_found": False,
        "family_conclusion": (
            "The family-like requirement survives as a durable shared-life invariant, "
            "but biological kinship and co-residence are neither sufficient nor uniquely necessary."
        ),
        "function_conclusion": (
            "The five continuity responsibilities remain jointly adequate for the tested cases; "
            "administrative combination is conditional on distinct evidence, rights, and correction."
        ),
        "organization_conclusion": (
            "Exactly five organizations is rejected. Specialized scientific, governing, ecological, "
            "or care bodies may protect interfaces without adding a sixth continuity object."
        ),
        "universality_conclusion": (
            "Universal availability requires person-level capability, voice, access, contribution, "
            "and correction with accommodation; aggregate performance by a competent minority is insufficient."
        ),
        "remaining_validation": (
            "Independent recoding, real-case observation, longitudinal evidence, threshold calibration, "
            "and comparison with additional institutional bundles remain open."
        ),
        "pass_four_coverage_sha256": sha256(coverage_path),
        "cases_sha256": sha256(cases_path),
        "evidence_protocol_sha256": sha256(evidence_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--diagnostics", type=Path, default=DEFAULT_DIAGNOSTICS)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    result = run(args.coverage, args.diagnostics, args.output_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

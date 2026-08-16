#!/usr/bin/env python3
"""Derive the Pass-Three Jeevan activity spheres from the Pass-Two register.

The analysis deliberately uses only Python's standard library.  It parses the
sixteen frozen feature positions, converts the prose to a controlled structural
vocabulary, anonymizes every member, and performs deterministic average-link
clustering with field-wise weighted Jaccard similarity.  Source names, faculty
labels, pair positions, and source-embedded social vocabulary are restored only
in the second output file, after the anonymous partitions have been frozen.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    ROOT
    / "Studies"
    / "The-Epistemology-of-Coexistence"
    / "Research-Note-Jeevan-Activity-Lifecycle-Pass-Two.md"
)
DEFAULT_OUTPUT_DIR = DEFAULT_SOURCE.parent

FIELD_NAMES = [
    "feature_01_entry_form",
    "feature_02_ontological_locus",
    "feature_03_operation_field",
    "feature_04_consequence_field",
    "feature_05_evidence_and_evaluators",
    "feature_06_counterpart_and_topology",
    "feature_07_internal_dependencies",
    "feature_08_endpoint_and_provenance",
    "feature_09_development_and_orientation",
    "feature_10_expression_requirements",
    "feature_11_evidence_requirements",
    "feature_12_correction_and_protection",
    "feature_13_continuity_and_transmission",
    "feature_14_external_relations",
    "feature_15_universality",
    "feature_16_false_positive_and_open",
]

PAIR_RE = re.compile(
    r"^###\s+([ABCMV]-\d{2})\s+-\s+\*([^*]+?)\s*/\s*([^*]+?)\*\s*$"
)
EXTERNAL_RE = re.compile(
    r"\b(CONST|ENAB|EVID|PROT|CORR|SUST|TRANS)\s*;\s*"
    r"(N|S|C|U)-(OCC|EXP|EVD|COR|CON)\s*;\s*"
    r"(U-J|U-H|V-C)\s*;\s*(D|I|H|O)\b"
)

# Terms in this list may occur in the Pass-Two prose but can never occur in the
# anonymous matrix.  Their structural implications are represented by neutral
# tokens such as counterpart:direct or continuity:guided_learning.
BANNED_ANONYMOUS_TERMS = {
    "atma",
    "buddhi",
    "chitta",
    "vritti",
    "mun",
    "family",
    "institution",
    "school",
    "teacher",
    "learner",
    "mother",
    "father",
    "parent",
    "child",
    "spouse",
    "husband",
    "wife",
    "brother",
    "sister",
    "court",
    "police",
    "government",
    "market",
    "trade",
    "economy",
    "education",
    "production",
}


@dataclass(frozen=True)
class Member:
    anonymous_id: str
    source_id: str
    name: str
    faculty: str
    fields: dict[str, str]
    tokens: tuple[frozenset[str], ...]
    residual: bool


def clean_markdown(value: str) -> str:
    value = value.replace("`", "").replace("*", "")
    value = value.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", value).strip().lower()


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_members(source: Path) -> list[tuple[str, str, str, dict[str, str]]]:
    lines = source.read_text(encoding="utf-8").splitlines()
    parsed: list[tuple[str, str, str, dict[str, str]]] = []
    index = 0
    while index < len(lines):
        match = PAIR_RE.match(lines[index])
        if not match:
            index += 1
            continue
        pair_id, name_a, name_b = match.groups()
        index += 1
        while index < len(lines) and not lines[index].startswith("| Field |"):
            index += 1
        if index >= len(lines):
            raise ValueError(f"Missing table for {pair_id}")
        header = split_table_row(lines[index])
        if len(header) != 3:
            raise ValueError(f"Unexpected header for {pair_id}: {header}")
        index += 2
        rows_a: dict[str, str] = {}
        rows_b: dict[str, str] = {}
        while index < len(lines) and lines[index].startswith("|"):
            cells = split_table_row(lines[index])
            if len(cells) == 3:
                rows_a[cells[0]] = cells[1]
                rows_b[cells[0]] = cells[2]
            index += 1
        expected = {
            "Normalized location",
            "Internal dependency",
            "Development and orientation",
            "Expression and consequence",
            "Evidence and evaluator",
            "Correction",
            "Continuity and transmission",
            "External classification and risk",
        }
        if set(rows_a) != expected or set(rows_b) != expected:
            missing = expected - set(rows_a)
            raise ValueError(f"Incomplete Pass-Two table for {pair_id}: {sorted(missing)}")
        parsed.append((pair_id + "a", name_a.strip(), pair_id[0], rows_a))
        parsed.append((pair_id + "b", name_b.strip(), pair_id[0], rows_b))
    if len(parsed) != 122:
        raise ValueError(f"Expected 122 members, found {len(parsed)}")
    return parsed


def tagged(text: str, rules: dict[str, Sequence[str]], prefix: str) -> set[str]:
    clean = clean_markdown(text)
    result = {
        f"{prefix}:{label}"
        for label, patterns in rules.items()
        if any(re.search(pattern, clean) for pattern in patterns)
    }
    return result or {f"{prefix}:unspecified"}


DOMAIN_RULES = {
    "meaning_truth": (
        r"realisation|understand|meaning|truth|knowledge|awakening|resolution|conception|non-contradict|definite",
    ),
    "inquiry_discrimination": (
        r"inquiry|examin|inspect|discrimin|comparison|reason|question|observation|interpret|recognition",
    ),
    "communication_representation": (
        r"language|speech|writing|communicat|presentation|articulat|explain|hearer|recipient|representation|record",
    ),
    "agency_action": (
        r"decision|selection|action|conduct|responsib|purpose|goal|resolve|initiative|participat|endeavour|work",
    ),
    "reciprocal_relation": (
        r"relationship|relation|counterpart|mutual|recipro|value-fulfil|recognition of another|companionship|shared life",
    ),
    "care_development": (
        r"care|nurtur|help|development|receptiv|capability|dependen|support|guidance|protect",
    ),
    "justice_protection": (
        r"justice|fair|safety|voice|appeal|domination|coerc|dissent|boundary|protection|non-interference",
    ),
    "skill_design": (
        r"skill|competence|design|making|technique|artefact|performance|apprentice|tool|planning",
    ),
    "bodily_health": (
        r"body|bodily|health|organ|sensory|pain|treatment|rehabilitation|respirat|breathing|wellness|impairment",
    ),
    "material_provision": (
        r"material|object|resource|provision|need|sufficien|prosper|reserve|housing|infrastructure|medium|load",
    ),
    "ecological_continuity": (
        r"nature|ecolog|regenerat|material cycle|air|future generation|long-horizon|delayed effect",
    ),
    "collective_public": (
        r"collective|public|affected people|affected person|community|society|coordination|coworker|user",
    ),
    "continuity_transmission": (
        r"continu|transmi|intergenerational|succession|repetition|repertoire|maintain|preserv|history|through time",
    ),
    "aesthetic_affinity": (
        r"beaut|form|appearance|affinity|otherness|pleasant|unpleasant|taste|smell|soft|hard|cold|hot|sour|sweet|pungent|bitter|astringent|salty",
    ),
}

EVALUATOR_RULES = {
    "first_person": (r"first-person|bearer|self-evaluat|felt|intention|inward",),
    "counterpart": (r"counterpart|hearer|recipient|another|both spouses|guide",),
    "skilled_peer": (r"skilled|competent peer|peer|caregiver|health competence|maker",),
    "affected_party": (r"affected|user|worker|dependant|community|public",),
    "body_material": (r"body|bodily response|material evidence|measurement|organ|artefact",),
    "future_ecological": (r"ecolog|future|long-horizon|nature|material cycle",),
}

DEPENDENCY_RULES = {
    "realised_orientation": (r"realisation|realised|awakening|truth|coexistence",),
    "accepted_meaning": (r"accepted|definite|understanding|meaning|conception|knowledge",),
    "contemplative_design": (r"contemplat|memory|plan|articulat|integration",),
    "evaluation_discrimination": (r"evaluat|discrimin|compare|criterion|fitness|thought",),
    "selection_embodiment": (r"select|embod|body|execution|speech|action|making",),
    "relational_feedback": (r"counterpart|relationship|another|learner|helper|care",),
}

DEVELOPMENT_RULES = {
    "open_inquiry": (r"inquiry|examin|question|study|dialog|objection|rival",),
    "noncoercive_agency": (r"freedom|non-coerc|noncoerc|dissent|without fear|agency|choice",),
    "practice_skill": (r"practice|skill|competence|apprentice|technique|training|rehears",),
    "relational_experience": (r"relationship|counterpart|recipro|care|help|participat",),
    "material_access": (r"material|tool|resource|access|provision|environment|medium",),
    "bodily_capability": (r"body|bodily|health|sensory|care|restoration",),
    "feedback_critique": (r"feedback|critique|compare|review|measurement|consequence",),
    "continuity_exposure": (r"history|record|repeated|continu|varied|exposure|succession",),
}

EXPRESSION_RULES = {
    "language_representation": (r"language|speech|writing|communicat|presentation|representation|explain",),
    "embodied_capability": (r"body|bodily|skill|movement|sense|organ|health",),
    "material_means": (r"material|tool|resource|medium|access|provision|infrastructure",),
    "counterpart_participation": (r"counterpart|relationship|another|recipient|user|worker|participat",),
    "consequence_visibility": (r"consequence|effect|evidence|visible|response|result",),
    "timing_discretion": (r"time|timing|occasion|discretion|proportion|amount",),
}

EVIDENCE_RULES = {
    "self_noncontradiction": (r"first-person|bearer|non-contradict|inward|intention",),
    "reciprocal_fulfilment": (r"counterpart|mutual|recipro|value-fulfil|satisfaction|consent",),
    "competence_peer_review": (r"skilled|competent|peer|measurement|causal|technical|demonstration",),
    "affected_party_voice": (r"affected|user|worker|dependant|community|public|voice",),
    "bodily_material_effect": (r"body|bodily|material|organ|artefact|health|measurement",),
    "long_horizon_effect": (r"ecolog|future|long-horizon|delayed|continuity|through time",),
}

CORRECTION_RULES = {
    "renewed_inquiry": (r"renew.*inquiry|reopen.*inquiry|revisit.*meaning|clarify|return to.*content|question",),
    "dialogue_changed_fulfilment": (r"dialog|changed fulfil|expectation|relationship|recipro|boundary",),
    "protection_appeal": (r"protect|appeal|safeguard|separation|retaliation|coerc|domination|safety",),
    "retraining_changed_means": (r"retrain|skill|practice|technique|changed means|revise.*planning",),
    "repair_restitution": (r"repair|restitution|restore|restoration|harm",),
    "redesign_procedure": (r"redesign|procedure|role|incentive|tool|prototype|substitution",),
    "treatment_accommodation": (r"treat|rehabilitat|accommodat|care|impairment|injury",),
    "ecological_restoration": (r"ecolog|regenerat|long-horizon|monitor|material cycle|waste",),
}

CONTINUITY_RULES = {
    "inquiry_records_verification": (r"inquiry|record|proposal|verification|re-present|exemplar",),
    "relational_memory_repair": (r"relationship|expectation|value-fulfil|repair|recipro|remember",),
    "care_succession_agency": (r"care|respite|succession|agency|dependen|nurtur|protect",),
    "skill_tools_maintenance": (r"skill|apprentice|tool|maintenance|practice|repertoire|competence",),
    "reserve_reliable_provision": (r"reserve|provision|access|resource|sufficien|dependable",),
    "public_review_dissent": (r"public|review|dissent|appeal|accountab|independent|disagreement",),
    "ecological_regeneration": (r"ecolog|regenerat|material cycle|future|long-horizon",),
    "intergenerational_transmission": (r"intergenerational|generation|transmi|succession|learner|teach",),
}

RISK_RULES = {
    "private_state_proxy": (r"conviction|altered state|pleasure|excitement|feeling|preference|immediate response",),
    "authority_status_proxy": (r"authority|office|charisma|status|prestige|reputation|title|deference",),
    "verbal_display_proxy": (r"fluency|quotation|verbal|eloquence|slogan|recitation|display",),
    "compliance_force_proxy": (r"obedience|compliance|coerc|fear|aggression|domination|submission",),
    "output_efficiency_proxy": (r"output|efficiency|surplus|quantity|technical novelty|performance|activity mistaken",),
    "short_term_satisfaction_proxy": (r"reported satisfaction|immediate satisfaction|short-term|temporary|stimulation",),
    "material_sensory_proxy": (r"appearance|ornament|taste|smell|stimulation|intensity|attraction|aversion|sensory",),
    "care_control_proxy": (r"dependence|control|overprotection|sacrifice|possess|paternal|gender|role stereotype",),
    "harm_displacement_proxy": (r"displaced|hidden harm|waste|ecological|future|unsafe|depletion",),
}


def topology_codes(text: str) -> set[str]:
    clean = clean_markdown(text)
    return {f"topology:{code.lower()}" for code in re.findall(r"\b[JBDRCET]\b", clean.upper())}


def entry_form(normalized: str) -> str:
    text = clean_markdown(normalized)
    if re.search(
        r"person-role|participant-role|teacher-role|learner-role|mother-role|father-role|"
        r"person in (?:a |close |just |communicative )?relation|persons in participation|"
        r"reciprocal .*relationship|relationship and roles|care relation|helper in relation|"
        r"capable person in relation|cooperative participant|person in recognised relationships",
        text,
    ):
        return "role_relation"
    if re.search(
        r"physicochemical|sensory conjunction|olfactory quality|thermal quality|"
        r"tactile-mechanical|material contact|material object|artefact or performance|"
        r"inspected unit or relation as property|object, action, or arrangement relative to the body|"
        r"visible form",
        text,
    ):
        return "material_sensory_property"
    if re.search(r"body as (?:functional state|respiratory process)|bodily process|breathing", text):
        return "bodily_process_state"
    if re.search(
        r"accepted material-relational condition|material condition produced|"
        r"bodily-material relation or result|conducive unit-relation or repeated criterion|"
        r"experienced certainty of dependable sufficiency|condition or result",
        text,
    ):
        return "criterion_result"
    return "inward_operation_orientation"


def locus_tokens(normalized: str) -> set[str]:
    clean = clean_markdown(normalized)
    locus = clean.split("operation:", 1)[0]
    result: set[str] = set()
    if re.search(r"atma|buddhi|chitta|vritti|mun|jeevan|inward", locus):
        result.add("locus:sentient_inward")
    if re.search(r"person|body|bodily|embodied", locus):
        result.add("locus:embodied_person")
    if re.search(r"relation|participant|counterpart|persons|role", locus):
        result.add("locus:relational")
    if re.search(r"material|object|physicochemical|unit|artefact|medium|air", locus):
        result.add("locus:material_ecological")
    if re.search(r"collective|public|society|wider order", locus):
        result.add("locus:collective_public")
    if re.search(r"duration|time|histor", locus):
        result.add("locus:temporal")
    return result or {"locus:unspecified"}


def segment(normalized: str, start: str, ends: Sequence[str]) -> str:
    clean = clean_markdown(normalized)
    marker = start + ":"
    if marker not in clean:
        return clean
    value = clean.split(marker, 1)[1]
    positions = [value.find(end + ":") for end in ends if end + ":" in value]
    positions = [position for position in positions if position >= 0]
    return value[: min(positions)] if positions else value


def make_feature_tokens(fields: dict[str, str]) -> tuple[tuple[frozenset[str], ...], bool]:
    normalized = fields["Normalized location"]
    dependency = fields["Internal dependency"]
    development = fields["Development and orientation"]
    expression = fields["Expression and consequence"]
    evidence = fields["Evidence and evaluator"]
    correction = fields["Correction"]
    continuity = fields["Continuity and transmission"]
    external = fields["External classification and risk"]

    norm_clean = clean_markdown(normalized)
    external_clean = clean_markdown(external)
    residual = bool(re.search(r"\bd/i/o\b|\bi/o\b|remains o|criterion o|ontology remains o", norm_clean + " " + external_clean))
    provenance = set()
    for code in re.findall(r"\b[DIHO]\b", normalized.replace("*", "")):
        provenance.add(f"provenance:{code.lower()}")
    if not provenance:
        provenance.add("provenance:i")

    operation_text = segment(normalized, "operation", ("consequence", "evidence"))
    consequence_text = segment(normalized, "consequence", ("evidence",))
    evidence_text = segment(normalized, "evidence", ()) + " " + evidence

    topology = topology_codes(normalized)
    counterpart = set()
    if "topology:d" in topology:
        counterpart.add("counterpart:direct")
    if "topology:r" in topology:
        counterpart.add("counterpart:durable")
    if "topology:c" in topology:
        counterpart.add("counterpart:collective")
    if "topology:e" in topology:
        counterpart.add("counterpart:material_ecological")
    if topology == {"topology:j"}:
        counterpart.add("counterpart:none_constitutive")

    external_matches = EXTERNAL_RE.findall(external.replace("`", ""))
    relation_tokens = {
        f"relation:{relation.lower()}" for relation, _, _, _, _ in external_matches
    }
    relation_tokens.update(
        f"scope:{strength.lower()}_{scope.lower()}"
        for _, strength, scope, _, _ in external_matches
    )
    universal_tokens = {
        "universality:" + level.lower().replace("-", "_")
        for _, _, _, level, _ in external_matches
    }
    if not relation_tokens:
        relation_tokens.add("relation:unclassified")
    if not universal_tokens:
        universal_tokens.add("universality:unclassified")

    risk_text = external_clean.split("risk:", 1)[1] if "risk:" in external_clean else external_clean
    feature_sets: list[set[str]] = [
        {f"entry:{entry_form(normalized)}", "residual:open" if residual else "residual:closed"},
        locus_tokens(normalized),
        tagged(operation_text, DOMAIN_RULES, "operation"),
        tagged(consequence_text, DOMAIN_RULES, "consequence"),
        tagged(evidence_text, DOMAIN_RULES, "evidence")
        | tagged(evidence, EVALUATOR_RULES, "evaluator"),
        topology | counterpart,
        tagged(dependency, DEPENDENCY_RULES, "dependency"),
        tagged(consequence_text + " " + evidence, DOMAIN_RULES, "endpoint") | provenance,
        tagged(development, DEVELOPMENT_RULES, "development"),
        tagged(expression, EXPRESSION_RULES, "expression"),
        tagged(evidence, EVIDENCE_RULES, "evidence_req"),
        tagged(correction, CORRECTION_RULES, "correction"),
        tagged(continuity, CONTINUITY_RULES, "continuity"),
        relation_tokens,
        universal_tokens,
        tagged(risk_text, RISK_RULES, "false_positive")
        | ({"open:yes"} if residual else {"open:no"}),
    ]
    if len(feature_sets) != 16:
        raise AssertionError("Frozen feature vector must contain sixteen positions")
    return tuple(frozenset(values) for values in feature_sets), residual


def build_members(source: Path) -> list[Member]:
    faculty_names = {"A": "atma", "B": "buddhi", "C": "chitta", "V": "vritti", "M": "mun"}
    result = []
    for number, (source_id, name, faculty_code, fields) in enumerate(parse_members(source), 1):
        tokens, residual = make_feature_tokens(fields)
        result.append(
            Member(
                anonymous_id=f"X{number:03d}",
                source_id=source_id,
                name=name,
                faculty=faculty_names[faculty_code],
                fields=fields,
                tokens=tokens,
                residual=residual,
            )
        )
    return result


def filtered_tokens(member: Member, treatment: str) -> tuple[frozenset[str], ...]:
    if treatment not in {"include_open", "drop_open", "residual_holdout"}:
        raise ValueError(f"Unknown treatment: {treatment}")
    if treatment == "include_open":
        return member.tokens
    return tuple(
        frozenset(
            token
            for token in position
            if not token.startswith("open:") and not token.startswith("residual:")
        )
        for position in member.tokens
    )


def similarity(left: Sequence[frozenset[str]], right: Sequence[frozenset[str]]) -> float:
    # Every one of the sixteen frozen positions has equal weight.  A verbose
    # lifecycle row therefore cannot outweigh a short topology or provenance row.
    scores = []
    for left_set, right_set in zip(left, right):
        left_known = {
            token
            for token in left_set
            if not token.endswith(":unspecified") and not token.endswith(":unclassified")
        }
        right_known = {
            token
            for token in right_set
            if not token.endswith(":unspecified") and not token.endswith(":unclassified")
        }
        union = left_known | right_known
        # Mutual absence is not structural resemblance.  Unknown fields must not
        # manufacture a cluster merely because both records lack a coded token.
        scores.append(len(left_known & right_known) / len(union) if union else 0.0)
    return sum(scores) / len(scores)


def similarity_matrix(members: Sequence[Member], treatment: str) -> list[list[float]]:
    vectors = [filtered_tokens(member, treatment) for member in members]
    matrix = [[1.0 for _ in members] for _ in members]
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            value = similarity(vectors[i], vectors[j])
            matrix[i][j] = value
            matrix[j][i] = value
    return matrix


def cluster_similarity(left: Sequence[int], right: Sequence[int], matrix: list[list[float]]) -> float:
    values = [matrix[i][j] for i in left for j in right]
    return sum(values) / len(values)


def agglomerative(matrix: list[list[float]], target_k: int) -> list[list[int]]:
    clusters: list[tuple[int, ...]] = [(index,) for index in range(len(matrix))]
    while len(clusters) > target_k:
        best: tuple[float, tuple[int, ...], tuple[int, ...], int, int] | None = None
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                score = cluster_similarity(clusters[i], clusters[j], matrix)
                candidate = (score, tuple(-x for x in clusters[i]), tuple(-x for x in clusters[j]), i, j)
                if best is None or candidate > best:
                    best = candidate
        assert best is not None
        i, j = best[-2], best[-1]
        merged = tuple(sorted(clusters[i] + clusters[j]))
        clusters = [cluster for pos, cluster in enumerate(clusters) if pos not in {i, j}]
        clusters.append(merged)
        clusters.sort(key=lambda values: values[0])
    return [list(cluster) for cluster in clusters]


def silhouette(clusters: Sequence[Sequence[int]], matrix: list[list[float]]) -> float:
    membership = {item: cluster_index for cluster_index, cluster in enumerate(clusters) for item in cluster}
    values = []
    for item in range(len(matrix)):
        own = clusters[membership[item]]
        if len(own) == 1:
            values.append(0.0)
            continue
        a = sum(1.0 - matrix[item][other] for other in own if other != item) / (len(own) - 1)
        b = min(
            sum(1.0 - matrix[item][other] for other in cluster) / len(cluster)
            for index, cluster in enumerate(clusters)
            if index != membership[item]
        )
        values.append((b - a) / max(a, b) if max(a, b) else 0.0)
    return sum(values) / len(values)


def labels_from_clusters(clusters: Sequence[Sequence[int]], size: int) -> list[int]:
    labels = [-1] * size
    for label, cluster in enumerate(clusters):
        for item in cluster:
            labels[item] = label
    return labels


def adjusted_rand(left: Sequence[int], right: Sequence[int]) -> float:
    if len(left) != len(right):
        raise ValueError("ARI inputs must have the same length")
    size = len(left)
    if size < 2:
        return 1.0
    contingency = Counter(zip(left, right))
    left_counts = Counter(left)
    right_counts = Counter(right)
    choose2 = lambda value: value * (value - 1) // 2
    sum_cells = sum(choose2(value) for value in contingency.values())
    sum_left = sum(choose2(value) for value in left_counts.values())
    sum_right = sum(choose2(value) for value in right_counts.values())
    total = choose2(size)
    expected = sum_left * sum_right / total if total else 0.0
    maximum = (sum_left + sum_right) / 2
    return (sum_cells - expected) / (maximum - expected) if maximum != expected else 1.0


def cluster_id_map(clusters: Sequence[Sequence[int]], prefix: str) -> dict[int, str]:
    ordered = sorted(enumerate(clusters), key=lambda item: min(item[1]))
    return {original: f"{prefix}{position:02d}" for position, (original, _) in enumerate(ordered, 1)}


def primary_ids(clusters: Sequence[Sequence[int]], prefix: str, size: int) -> list[str]:
    labels = labels_from_clusters(clusters, size)
    mapping = cluster_id_map(clusters, prefix)
    return [mapping[label] for label in labels]


def overlap_ids(
    clusters: Sequence[Sequence[int]],
    matrix: list[list[float]],
    prefix: str,
) -> list[list[str]]:
    mapping = cluster_id_map(clusters, prefix)
    result: list[list[str]] = []
    for item in range(len(matrix)):
        scores = []
        for cluster_index, cluster in enumerate(clusters):
            others = [member for member in cluster if member != item]
            score = (
                sum(matrix[item][other] for other in others) / len(others)
                if others
                else matrix[item][cluster[0]]
            )
            scores.append((score, cluster_index))
        scores.sort(reverse=True)
        best = scores[0][0]
        selected = [
            mapping[cluster_index]
            for score, cluster_index in scores
            if score >= 0.20 and score >= best * 0.86 and best - score <= 0.06
        ]
        result.append(sorted(set(selected)))
    return result


def select_resolutions(members: Sequence[Member]) -> tuple[dict[str, int], list[dict[str, float]]]:
    full_matrix = similarity_matrix(members, "include_open")
    drop_matrix = similarity_matrix(members, "drop_open")
    stable_members = [member for member in members if not member.residual]
    stable_matrix = similarity_matrix(stable_members, "residual_holdout")
    stable_indices = [index for index, member in enumerate(members) if not member.residual]

    rows = []
    for k in range(2, 17):
        include_clusters = agglomerative(full_matrix, k)
        drop_clusters = agglomerative(drop_matrix, k)
        holdout_k = min(k, max(2, len(stable_members) - 1))
        holdout_clusters = agglomerative(stable_matrix, holdout_k)
        include_labels = labels_from_clusters(include_clusters, len(members))
        drop_labels = labels_from_clusters(drop_clusters, len(members))
        holdout_labels = labels_from_clusters(holdout_clusters, len(stable_members))
        include_stable_labels = [include_labels[index] for index in stable_indices]
        stability_open = adjusted_rand(include_labels, drop_labels)
        stability_holdout = adjusted_rand(include_stable_labels, holdout_labels)
        sil = silhouette(include_clusters, full_matrix)
        composite = 0.55 * sil + 0.225 * stability_open + 0.225 * stability_holdout
        rows.append(
            {
                "k": k,
                "silhouette": sil,
                "stability_drop_open": stability_open,
                "stability_holdout": stability_holdout,
                "composite": composite,
            }
        )

    def best(low: int, high: int) -> int:
        candidates = [row for row in rows if low <= row["k"] <= high]
        return int(max(candidates, key=lambda row: (row["composite"], row["silhouette"], -row["k"]))["k"])

    return {
        "coarse": best(3, 5),
        "middle": best(6, 11),
        "fine": best(12, 16),
    }, rows


def write_anonymous_matrix(path: Path, members: Sequence[Member]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["anonymous_id", *FIELD_NAMES])
        for member in members:
            writer.writerow(
                [member.anonymous_id]
                + [";".join(sorted(position)) for position in member.tokens]
            )
    lowered = path.read_text(encoding="utf-8").lower()
    found = sorted(term for term in BANNED_ANONYMOUS_TERMS if re.search(rf"\b{re.escape(term)}\b", lowered))
    if found:
        raise ValueError(f"Anonymous matrix leaked prohibited terms: {found}")


def neighbour_sets(clusters: Sequence[Sequence[int]], members: Sequence[Member]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for cluster in clusters:
        ids = {members[index].anonymous_id for index in cluster}
        for anonymous_id in ids:
            result[anonymous_id] = ids - {anonymous_id}
    return result


def set_jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def stability_score(
    anonymous_id: str,
    include_neighbours: dict[str, set[str]],
    drop_neighbours: dict[str, set[str]],
    holdout_neighbours: dict[str, set[str]],
    stable_ids: set[str],
) -> float:
    scores = [set_jaccard(include_neighbours[anonymous_id], drop_neighbours[anonymous_id])]
    if anonymous_id in holdout_neighbours:
        include_stable = include_neighbours[anonymous_id] & stable_ids
        scores.append(set_jaccard(include_stable, holdout_neighbours[anonymous_id]))
    return sum(scores) / len(scores)


def stability_label(score: float, residual: bool) -> str:
    if score >= 0.70:
        return "stable_with_open_field" if residual else "stable"
    if score >= 0.50:
        return "moderately_stable_with_open_field" if residual else "moderately_stable"
    return "sensitive_open_field" if residual else "sensitive"


def best_cluster_jaccard(
    source_ids: set[str],
    comparison: Sequence[set[str]],
) -> float:
    return max((set_jaccard(source_ids, candidate) for candidate in comparison), default=0.0)


def run(source: Path, output_dir: Path) -> dict[str, object]:
    members = build_members(source)
    output_dir.mkdir(parents=True, exist_ok=True)
    resolutions, diagnostics = select_resolutions(members)

    include_matrix = similarity_matrix(members, "include_open")
    drop_matrix = similarity_matrix(members, "drop_open")
    partitions: dict[str, list[list[int]]] = {}
    primary: dict[str, list[str]] = {}
    overlaps: dict[str, list[list[str]]] = {}
    for resolution, k in resolutions.items():
        clusters = agglomerative(include_matrix, k)
        partitions[resolution] = clusters
        prefix = {"coarse": "C", "middle": "M", "fine": "F"}[resolution]
        primary[resolution] = primary_ids(clusters, prefix, len(members))
        overlaps[resolution] = overlap_ids(clusters, include_matrix, prefix)

    middle_drop_clusters = agglomerative(drop_matrix, resolutions["middle"])
    stable_members = [member for member in members if not member.residual]
    stable_ids = {member.anonymous_id for member in stable_members}
    stable_matrix = similarity_matrix(stable_members, "residual_holdout")
    middle_holdout_clusters = agglomerative(stable_matrix, min(resolutions["middle"], len(stable_members) - 1))
    middle_include_neighbours = neighbour_sets(partitions["middle"], members)
    middle_drop_neighbours = neighbour_sets(middle_drop_clusters, members)
    middle_holdout_neighbours = neighbour_sets(middle_holdout_clusters, stable_members)
    member_scores = {
        member.anonymous_id: stability_score(
            member.anonymous_id,
            middle_include_neighbours,
            middle_drop_neighbours,
            middle_holdout_neighbours,
            stable_ids,
        )
        for member in members
    }

    anonymous_path = output_dir / "Research-Data-Jeevan-Pass-Three-Anonymous-Matrix.csv"
    restored_path = output_dir / "Research-Data-Jeevan-Pass-Three-Restored-Memberships.csv"
    summary_path = output_dir / "Research-Data-Jeevan-Pass-Three-Diagnostics.json"
    write_anonymous_matrix(anonymous_path, members)

    with restored_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "anonymous_id",
                "source_id",
                "member_name",
                "faculty",
                "coarse_primary",
                "coarse_memberships",
                "middle_primary",
                "middle_memberships",
                "fine_primary",
                "fine_memberships",
                "residual_flag",
                "middle_stability_score",
                "middle_stability",
            ]
        )
        for index, member in enumerate(members):
            writer.writerow(
                [
                    member.anonymous_id,
                    member.source_id,
                    member.name,
                    member.faculty,
                    primary["coarse"][index],
                    ";".join(overlaps["coarse"][index]),
                    primary["middle"][index],
                    ";".join(overlaps["middle"][index]),
                    primary["fine"][index],
                    ";".join(overlaps["fine"][index]),
                    "yes" if member.residual else "no",
                    f"{member_scores[member.anonymous_id]:.6f}",
                    stability_label(member_scores[member.anonymous_id], member.residual),
                ]
            )

    cluster_summaries = {}
    for resolution, clusters in partitions.items():
        prefix = {"coarse": "C", "middle": "M", "fine": "F"}[resolution]
        mapping = cluster_id_map(clusters, prefix)
        treatment_k = min(resolutions[resolution], len(stable_members) - 1)
        resolution_drop_clusters = agglomerative(drop_matrix, resolutions[resolution])
        resolution_holdout_clusters = agglomerative(stable_matrix, treatment_k)
        drop_sets = [
            {members[index].anonymous_id for index in cluster}
            for cluster in resolution_drop_clusters
        ]
        holdout_sets = [
            {stable_members[index].anonymous_id for index in cluster}
            for cluster in resolution_holdout_clusters
        ]
        cluster_summaries[resolution] = []
        for cluster_index, cluster in enumerate(clusters):
            token_counts = Counter(
                token
                for member_index in cluster
                for position in members[member_index].tokens
                for token in position
                if not token.startswith("provenance:") and token not in {"open:no", "residual:closed"}
            )
            cluster_summaries[resolution].append(
                {
                    "cluster_id": mapping[cluster_index],
                    "size": len(cluster),
                    "anonymous_members": [members[index].anonymous_id for index in cluster],
                    "top_tokens": [token for token, _ in token_counts.most_common(18)],
                    "drop_open_best_jaccard": best_cluster_jaccard(
                        {members[index].anonymous_id for index in cluster}, drop_sets
                    ),
                    "holdout_best_jaccard": best_cluster_jaccard(
                        {
                            members[index].anonymous_id
                            for index in cluster
                            if members[index].anonymous_id in stable_ids
                        },
                        holdout_sets,
                    ),
                    **(
                        {
                            "mean_member_stability": sum(
                                member_scores[members[index].anonymous_id] for index in cluster
                            )
                            / len(cluster)
                        }
                        if resolution == "middle"
                        else {}
                    ),
                }
            )
        cluster_summaries[resolution].sort(key=lambda row: row["cluster_id"])

    faculty_codes = {name: index for index, name in enumerate(sorted({member.faculty for member in members}))}
    middle_hard_labels = labels_from_clusters(partitions["middle"], len(members))
    faculty_labels = [faculty_codes[member.faculty] for member in members]
    pair_groups: dict[str, list[int]] = {}
    for index, member in enumerate(members):
        pair_groups.setdefault(member.source_id[:-1], []).append(index)

    def pair_congruence(indices: Sequence[int]) -> tuple[bool, bool]:
        left, right = indices
        same_primary = primary["middle"][left] == primary["middle"][right]
        shared_overlap = bool(set(overlaps["middle"][left]) & set(overlaps["middle"][right]))
        return same_primary, shared_overlap

    pair_results = {pair_id: pair_congruence(indices) for pair_id, indices in pair_groups.items()}
    pilot_pairs = {"A-01", "B-02", "C-04", "V-12", "V-18", "M-08", "M-13", "M-24"}
    overlap_edge_counts: Counter[tuple[str, str]] = Counter()
    for memberships in overlaps["middle"]:
        for left_index in range(len(memberships)):
            for right_index in range(left_index + 1, len(memberships)):
                overlap_edge_counts[tuple(sorted((memberships[left_index], memberships[right_index])))] += 1

    summary: dict[str, object] = {
        "source": source.name,
        "member_count": len(members),
        "residual_member_count": sum(member.residual for member in members),
        "selected_resolutions": resolutions,
        "diagnostics": diagnostics,
        "clusters": cluster_summaries,
        "posthoc_comparison": {
            "faculty_adjusted_rand_middle": adjusted_rand(middle_hard_labels, faculty_labels),
            "pair_same_primary": sum(result[0] for result in pair_results.values()),
            "pair_shared_overlap": sum(result[1] for result in pair_results.values()),
            "pair_count": len(pair_results),
            "pilot_same_primary": sum(pair_results[pair][0] for pair in pilot_pairs),
            "pilot_shared_overlap": sum(pair_results[pair][1] for pair in pilot_pairs),
            "pilot_pair_count": len(pilot_pairs),
            "middle_overlap_member_count": sum(len(values) > 1 for values in overlaps["middle"]),
            "middle_overlap_edges": [
                {"clusters": list(edge), "member_count": count}
                for edge, count in sorted(
                    overlap_edge_counts.items(), key=lambda item: (-item[1], item[0])
                )
            ],
            "middle_faculty_counts": {
                cluster_id: dict(sorted(Counter(
                    member.faculty
                    for index, member in enumerate(members)
                    if primary["middle"][index] == cluster_id
                ).items()))
                for cluster_id in sorted(set(primary["middle"]))
            },
        },
        "method": {
            "similarity": "equal-weight mean of sixteen field-wise Jaccard scores",
            "partition": "deterministic average-link agglomeration",
            "overlap_rule": "similarity >= 0.20, >= 86% of best, and within 0.06 of best",
            "sensitivity_treatments": ["include_open", "drop_open", "residual_holdout"],
            "selection_bands": {"coarse": [3, 5], "middle": [6, 11], "fine": [12, 16]},
        },
    }
    with summary_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    source = args.source.resolve()
    output_dir = args.output_dir.resolve()
    summary = run(source, output_dir)
    print(f"Parsed {summary['member_count']} members from {source}")
    print(f"Residual members: {summary['residual_member_count']}")
    print("Selected resolutions: " + json.dumps(summary["selected_resolutions"], sort_keys=True))
    print(f"Wrote Pass-Three data to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Coexistence Company — Concrete Organizational Structure

**Author:** [AnalyticMadhyasthDarshan.org](https://github.com/raghavamohan/AnalyticMadhyasthDarshan) — a group of people studying Madhyasth Darshan philosophy. Source repository: [raghavamohan/AnalyticMadhyasthDarshan](https://github.com/raghavamohan/AnalyticMadhyasthDarshan).

**Edited on:** June 24, 2026, 4:28 PM IST

**Basis:** This application instantiates the coexistence template and categorical architecture for a deliberate human assembly ([*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf); [*Category Theory Explained*](../Studies/Category-Theory-Explained/Category-Theory-Explained.pdf) §§3.5, 5, 6.1, 6.6–6.9, 6.8). It is a design blueprint, not legal advice.

**Example company:** **Saha Coexistence Works** (SCW) — a knowledge-work company (research, education, and technology services) whose product is understood coexistence made useful in the world. Scale assumed: **60 members** at steady state, expandable by **compound** team formation, not mere headcount.


## 1. Design objectives

SCW is organised to meet two objectives together ([*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) §8; P3–P4):

1. **Members are not instrumentalised** — nurturing (*poshan*), not net extraction; values fulfilled in relationships, not fear or temptation as the basis of order.
2. **The company sustains across generations of members** — relationships fulfilled (L4), understanding transmitted by education-*sanskar* (L5, τ), common cause, goal, and programme (P4).

Orientation is **completeness of relationships**, not unbounded maximisation of profit, comfort, or scale ([*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) §5).


## 2. Assembly tiers (who is a “unit”)

| Tier | SCW name | Size (example) | Composition mode | New joint conduct? |
|------|----------|----------------|------------------|-------------------|
| **Individual** | Member | 1 person | — | — |
| **Family** | **Family Team** | 7–12 members | **Compound** (*yaugik*) | Yes — one team *dharma* and outward conduct |
| **Community** | **Cluster** | 3–5 Family Teams | **Compound** colimit | Yes — shared programme across teams |
| **Undivided society** | **Company** (SCW) | All Clusters | **Compound** + gluing | Yes — one company-facing conduct |
| **Federation** (optional) | **Alliance** | 2+ aligned companies | Soc colimit | Only if overlap values agree |

**Rule:** Adding people in the same building without fused conduct is **mixture** (*mishran*) — weaker cohesion. Scale hiring only after **L3** complementarity (need/surplus) and overlap compatibility are verified ([*Category Theory Explained*](../Studies/Category-Theory-Explained/Category-Theory-Explained.pdf) §6.9; [*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) L3).


## 3. Top-level org chart

```mermaid
flowchart TD
    SC["Steward Council — ambient ground, not extraction"]
    SC --> OCG["Office of Cause, Goal & Programme"]
    SC --> CH["Charter & Ground Office"]
    SC --> REL["Relationship Registry"]
    SC --> CAP["Capability Institute"]
    SC --> VAL["Value & Justice Office"]
    SC --> EVAL["Evaluation Forum"]
    SC --> EV["Evidence & Tradition Office"]
    SC --> COMP["Composition Office"]
    SC --> SOC["Integration Office"]
    SC --> TRANS["Transmission Institute"]
    SC --> COND["Conduct Division — delivery"]
    COND --> FT["Family Teams × 6"]
    COND --> RUR["Right-Use & Regeneration"]
    FT --> CL["Clusters × 2"]
```


## 4. Functional units (departments)

Each row is a **mandatory subsystem** — the categorical analogue in [*Category Theory Explained*](../Studies/Category-Theory-Explained/Category-Theory-Explained.pdf) §6.1.

| # | Department | Template / CT role | Primary responsibility |
|---|------------|-------------------|------------------------|
| 0 | **Steward Council** | Sat — ambient ground | Holds shared coexistence frame; stewards charter; **does not** treat members as fuel for extraction (A1–A2) |
| 1 | **Office of Cause, Goal & Programme** | P4 | Documents and guards common **cause**, **goal**, and **programme** for sustainment |
| 2 | **Charter & Ground Office** | Sat, A3–A5 | Constitutional documents, ethical ground, conducive environment for natural state |
| 3 | **Relationship Registry** | Rel, D3 | Catalogue of **definite relationships** with expectation profiles **E(r)**; role charters; distinguishes relationship vs voluntary association |
| 4 | **Capability Institute** | Cap, D5a | Builds **capacity** (*kshamata*), **ability** (*yogyata*), **receptivity** (*patrata*) — onboarding, mentorship, study environment |
| 5 | **Value & Justice Office** | Val, D4, D7 | Maps **graded values** per relationship; supports justice cycle ρ → φ → μ → mutual satisfaction |
| 6 | **Evaluation Forum** | Eval, μ, D6 | Understanding-based assessment of value delivered vs inherent; guards over/under/mis-evaluation |
| 7 | **Evidence & Tradition Office** | Ev, D13 | Conduct others can recognise (*pramanikta*); records awakened tradition; closes evidence loop |
| 8 | **Composition Office** | Comp, κ, D8 | Team formation, mergers, partnerships; **mixture vs compound** decisions; **L3** admissibility |
| 9 | **Integration Office** | Soc, L4, P6 | Glues Clusters: **overlap compatibility** on shared people, clients, and resources |
| 10 | **Transmission Institute** | Trans, τ, L5 | Education-*sanskar* for every cohort; mentor lineage; succession — evidenced understanding, not rules alone |
| 11 | **Conduct Division** | Conduct, φ | Product, service, and operations that **fulfil** external and internal relationships |
| 12 | **Right-Use & Regeneration** | P5, η | Uniform right-use across domains; resource use bounded by regeneration |

**Headcount allocation (60-member example):**

| Area | FTE | Notes |
|------|-----|-------|
| Steward Council | 5 | Part-time rotation; includes Chief Steward |
| Offices 1–10 | 18 | ~2 per office at this scale; Transmission Institute largest (4 FTE) |
| Conduct Division — Family Teams | 30 | 6 teams × 5 delivery FTE (others in Cap/Trans rotation) |
| Conduct Division — leads & glue | 4 | Cluster stewards, Conduct Division coordinator |
| Right-Use & Regeneration | 3 | Facilities, procurement, ecological accounts |
| **Total** | **60** | |


## 5. Family Team structure (compound unit)

Each **Family Team** is a compound assembly: members discard separate outward conducts and present **one team conduct** with a written **sig(team)** = ⟨form, properties, essential nature, *dharma*⟩ ([*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) D1, D8).

```mermaid
flowchart LR
    subgraph FT ["Family Team (compound)"]
        TL["Team Steward"]
        MR["Mentor"]
        PR["Producers × 3–5"]
        RC["Receptivity & Records"]
        TL --> PR
        MR --> PR
        RC --> TL
    end
    EXT["Client / Partner / Earth-tier"] --> PR
```

| Role | Relationship (E(r)) | Value primarily flowing |
|------|---------------------|-------------------------|
| **Team Steward** | Stewardship ↔ team members | Protection, nurturing, resolution of blockers — not command-for-extraction |
| **Mentor** | Teacher ↔ learner | Understanding transmitted; cap(u) development |
| **Producers** | Usefulness ↔ recipient | Object value + established values in delivery |
| **Receptivity & Records** | Evidence ↔ team | Documents φ; feeds Evaluation Forum and Transmission Institute |

**Team size:** 7–12. Below 7, insufficient complementarity; above 12, prefer **compound** split into two teams with L3 need/surplus between them.


## 6. Definite relationships (company-wide registry)

The Relationship Registry maintains these **knowledge-order** relationships ([*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) §4; JV p. 109 cited in template §4):

| Relationship | Parties | Expectation profile (summary) | Value class |
|--------------|---------|------------------------------|-------------|
| **Stewardship** | Steward Council ↔ all members | Conducive environment; no instrumentalisation; nurturing | Established + civic |
| **Mentorship** | Mentor ↔ member | Understanding passed; cap(u) improved | Established |
| **Production** | Producer ↔ client/user | Usefulness-complementarity; purposeful-use | Object + established |
| **Peer complementarity** | Family Team ↔ Family Team | Surplus meets need; no internal zero-sum competition (L2) | Object + civic |
| **Earth-tier use** | Company ↔ land, energy, materials | Right-use; expenditure ≤ regeneration (P5) | Civic |
| **Succession** | Outgoing ↔ incoming member | τ: method of composition transmitted | Established |
| **Evaluation** | Member ↔ member (via Forum) | Honest μ on value delivered in role | Established |

Associations (voluntary projects, hobbies) are logged separately and **do not** inherit fixed E(r) until adopted as relationships.


## 7. Graded values in practice

| Class | SCW examples | Where monitored |
|-------|----------------|-----------------|
| **Object** | Quality of deliverable; usefulness of service | Value Office + client feedback |
| **Jeevan** | Member peace, contentment at work | Capability Institute (not KPI-targeted) |
| **Established** | Trust, respect, affection, gratitude in teams | Evaluation Forum + peer review |
| **Civic** | Right-use of body, mind, wealth; participation in orderliness | Right-Use Office + Steward Council |

**Trust** is the value deposited when fulfilment φ succeeds in a relationship ([*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) D7a). Justice is the **operation** on values, not a poster slogan.


## 8. Three completeness stages (milestones)

| Stage | Name | SCW milestone checklist |
|-------|------|---------------------------|
| **T1 — Constitutional** | *Gathanpurnata* | Charter ratified; all relationships in registry; Family Teams formed as **compound** units; cause/goal/programme published |
| **T2 — Activity** | *Kriyapurnata* | Programmes run; φ in daily work; cap(u) converts to effort; Clusters glued with compatible overlaps |
| **T3 — Conduct** | *Vyavaharpurnata* | Conduct evidenced externally (*pramanikta*); D13 loop closed; Transmission Institute producing awakened tradition |

T2–T3 are **awakening progression** inside an already-constituted company — not the same as hiring more people ([*Category Theory Explained*](../Studies/Category-Theory-Explained/Category-Theory-Explained.pdf) §6.2.1, §6.10).


## 9. Governance and decision rights

| Decision type | Decides | Guard |
|---------------|---------|-------|
| Cause, goal, programme | Steward Council + all-member consent | P4 |
| New **compound** team or Cluster | Composition Office + L3 proof + Integration Office | κ_comp, not κ_mix |
| Federation / alliance | Steward Council + Integration Office overlap audit | Soc colimit — P6 |
| Relationship recognition | Relationship Registry + affected parties | ρ |
| Value dispute | Evaluation Forum → Value Office | μ |
| Resource draw on nature | Right-Use Office | P5 regeneration bound |
| Member onboarding / offboarding | Transmission Institute + Mentor | τ evidenced |
| Right-use claim company-wide | Must pass **naturality** — all domains upgraded together | η ([*Category Theory Explained*](../Studies/Category-Theory-Explained/Category-Theory-Explained.pdf) §6.7) |

**Chief Steward** coordinates stewards; **does not** own surplus extraction from members. Profit, where it arises, is **circularity for family needs and reinvestment in transmission**, not unbounded accumulation ([*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) §8; MVD p. 265 cited there).


## 10. Operating rhythms

| Rhythm | Owner | Purpose |
|--------|-------|---------|
| **Weekly — team φ review** | Family Team | Relationships recognised? Values flowing? cap blockers? |
| **Monthly — Cluster glue check** | Integration Office | Shared clients/members: contradictory E(r)? |
| **Quarterly — μ forum** | Evaluation Forum | Evaluation quality; mis-evaluation correction |
| **Quarterly — evidence audit** | Evidence & Tradition Office | D13 loop; conduct manifest? |
| **Per cohort — transmission** | Transmission Institute | Education-*sanskar* for every new member |
| **Annual — completeness review** | Steward Council | T1/T2/T3 progress; P4 programme still common |


## 11. Onboarding pipeline (τ)

Every new member passes through Transmission Institute — **ignorance cannot flow in tradition** ([*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) §6; JV p. 49 cited there).

```mermaid
flowchart LR
    A["Offer + relationship charter"] --> B["Cause, goal, programme study"]
    B --> C["Registry: E(r) for role"]
    C --> D["Mentor assigned — cap(u) plan"]
    D --> E["Shadow fulfilment φ"]
    E --> F["Evidence review"]
    F --> G["Full member — compound team"]
```

Minimum duration: **90 days** before full membership in a compound Family Team.


## 12. Growth and merger rules

**Admissible growth (L3):** New team or hire when a documented **need** in one unit complements **surplus** in another ([*Category Theory Explained*](../Studies/Category-Theory-Explained/Category-Theory-Explained.pdf) §6.9.1).

**Admissible merger:** Only when Integration Office certifies:

1. **Compatible values** on all shared members and shared accounts (P6 / Soc).
2. **Compound** intent — fused conduct, new sig(assembly), not co-located silos.
3. **Transmission** plan for combined culture — τ_ev, not policy deck alone (P16).

**Reject** when: contradictory expectations on the same person; mixture presented as merger; selective right-use (η fails naturality).


## 13. Failure diagnostic (reverse use)

| Symptom | Likely clause broken | First responder |
|---------|---------------------|-----------------|
| Culture collapse after hiring spree | κ_mix not κ_comp; τ weak | Composition + Transmission |
| High turnover | τ / L5 | Transmission Institute |
| Toxic high performer | μ skipped; values not in E(r) | Evaluation Forum |
| Green team / exploitative HR | η non-uniform right-use | Right-Use + Steward Council |
| Merger dysfunction | Soc — overlap conflict | Integration Office |
| Burnout | Extraction culture; A1–A2 inverted | Steward Council |
| Metric gaming | Maximisation pathology | Value Office |


## 14. What this structure is not

- **Not** a conventional command hierarchy optimised for shareholder extraction.
- **Not** self-sufficient proof of coexistence — metaphysical premises remain commitments ([*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) §9).
- **Not** derivable from category theory alone — L3 complementarity, τ, and saturation are **designed in** ([*Category Theory Explained*](../Studies/Category-Theory-Explained/Category-Theory-Explained.pdf) §6.11 P8–P9, P16).

SCW is a **template instance**: bounded units, definite valued relationships, compound assembly by complementarity, persistence by fulfilment, transmission by education-*sanskar*, evaluation and evidence at the knowledge tier — structured so longevity and balance are **construction requirements**, not afterthoughts.


## References

### Application basis (this repository)

- [*The Coexistence Template*](../Studies/The-Coexistence-Template/The-Coexistence-Template.pdf) — formal template: units, relationships, values, κ, τ, L1–L7, P3–P5, §8 human organisations
- [*Category Theory Explained*](../Studies/Category-Theory-Explained/Category-Theory-Explained.pdf) — categorical architecture §6.1; cap(u) §6.6.1; right-use §6.7; society colimit §6.8; mixture/compound §6.9; propositions P6, P8–P9, P16

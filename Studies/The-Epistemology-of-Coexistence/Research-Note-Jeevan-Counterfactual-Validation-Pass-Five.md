# Research Note: Pass-Five Counterfactual Validation of the *Jeevan* Social Model

**Author:** Raghava Mohan Madhwapathi ([analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org))

**Edited on:** August 16, 2026, 10:42 AM IST

**Status:** Internal research note (not a catalog entry). Pass Five of the activity-to-sphere analysis.

**Scope:** This note stress-tests the family-like field and the five durable functions derived in [Pass Four](Research-Note-Jeevan-Durable-Functions-Pass-Four.md). It asks whether materially different arrangements can satisfy the same invariants, whether familiar arrangements can display false signs of fulfilment while failing them, and whether scarcity, disability, coercion, disagreement, migration, technological concentration, or ecological delay disclose a requirement outside the five-function basis. The cases are structured counterfactuals, not observations of actual communities. They test the coherence and discriminating power of the model; empirical validation remains a separate task.

The validation narrows the social thesis without dissolving it. A durable shared-life field remains necessary, but biological kinship, co-residence, and one household form are neither sufficient nor uniquely necessary. The five functions remain a complete basis for classifying the continuity responsibilities exposed by the test cases, but exactly five organisations is not derived. Production and exchange may share an administration only when their purposes, records, affected-party rights, and correction paths remain distinguishable. Separate scientific, governing, ecological, or care organisations may be required as safeguards or specialised bearers without introducing a sixth human continuity object.

Pass Five therefore supports a universal architecture of responsibilities and evidence, not a uniform institutional diagram. It also adds a stricter universality test: each person must have supported access to understanding, voice, bodily and material means, contribution, and correction. High aggregate performance by a competent minority does not satisfy the common capacity of *jeevan*.

## 1. What Pass Five can validate

Pass Four started from the anonymous activity matrix and recovered five objects that must remain continuous in embodied social life: understood orientation, claims between persons, bodily capability, transformed material means, and access to provision across persons and time. Those objects were restored as education-*sanskar*, justice-security, health-restraint, production-work, and exchange-reserve. The selected bundle covered all 185 channel memberships of the 122 activity records at the chosen grain.

That result left three distinct claims open. The first concerned **equivalence**: a materially different family or organisational form might preserve the same activity lifecycle. The second concerned **robustness**: scarcity, concentrated power, delay, or dependency might reveal a condition not captured by the five functions and their cross-cutting safeguards. The third concerned **evidence**: a system might look orderly, prosperous, consensual, or productive while obstructing the activity criterion it purports to maintain.

Pass Five tests those claims analytically. It does not show that any actual arrangement fulfils the invariants, determine causal effects, or independently confirm the ontology of *jeevan*. A counterfactual case can show that a stronger institutional claim is unnecessary, that a proposed arrangement is internally unsafe, or that the model needs another condition. Observation is still required to determine whether people can exercise the relevant capacities in practice.

### 1.1 The validation rule

Each case records the arrangement or adverse condition, functions placed under stress, safeguards required, invariant under test, available and missing conditions, false-positive risk, observable evidence, analytical result, and revision route. The rule is:

```text
materially different form + all relevant invariants + effective correction
    -> functionally equivalent arrangement

familiar label or desirable proxy + missing invariant
    -> false positive; arrangement rejected

adverse case + requirement already borne by one or more of U01-U05
    -> model survives, sometimes with a refined safeguard or scale rule

adverse case + non-substitutable continuity object outside U01-U05
    -> revise the Pass-Four function basis
```

The last result was a live possibility, not a result ruled out in advance. None of the nineteen specified cases disclosed such an object. This establishes closure only over the tested analytical cases. A surviving real-world counterexample would reopen the activity coding, sphere boundary, continuity channel, or bundle.

### 1.2 Frozen inputs and reproducible artifacts

The [Pass-Five validation script](../../Scripts/_validate_jeevan_pass_five.py) reads the Pass-Four restored coverage register and diagnostics, verifies the 122 members and the frozen B04 bundle, and computes how many activity members are exposed by each case's function set. It writes three deterministic artifacts:

- the [validation-case register](Research-Data-Jeevan-Pass-Five-Validation-Cases.csv), with SHA-256 digest `C1A9445197E9B3A65E541D0DBB5D57C192E1972FD3B8342507EA542DA1354FC5`;
- the [minimum-evidence protocol](Research-Data-Jeevan-Pass-Five-Evidence-Protocol.csv), with SHA-256 digest `F30FB574ADD0E37A46D90DC23C63FB4356D02FBA97CB678F9DA372AA6D39078C`; and
- the [validation summary](Research-Data-Jeevan-Pass-Five-Validation-Summary.json), which records scope, counts, conclusions, and the limit of the analysis.

The cases are declared arguments rather than machine-generated social findings. Automation preserves their schema, relates them to the frozen member register, detects input drift, and makes the result reproducible. It does not turn interpretive judgement into empirical measurement.

## 2. The nineteen validation cases

The case set includes three tests of the family-like field, six tests of function and organisation boundaries, seven adverse conditions, one person-level universality test, and two concentrated false-positive tests.

| Cases | Test | Analytical result | Consequence for the model |
|---|---|---|---|
| FAM-01 | Non-kin shared life with care, learning, work, provision, voice, and outside appeal | Equivalent arrangement | Family is a functional invariant, not a necessary genealogy |
| FAM-02 | Biologically related household with coercion and blocked appeal | Arrangement rejected | Kinship, provision, obedience, and reported unity are insufficient |
| FAM-03 | Multi-local care and provision across migration | Equivalent with portability | Co-residence is unnecessary; continuity must cross location |
| BND-01 | Production and exchange combined with distinct accounts and correction | Conditionally adequate | Functions may share an administration without being collapsed |
| BND-02 | Producer-distributor controls stock, evidence, and review | Arrangement rejected | U04 and U05 require separable evaluation and correction |
| BND-03 | Autonomous scientific organisation | No sixth function | Science is an independently organisable method and safeguard |
| BND-04 | Separate governing body | No sixth function | Governance coordinates rights and accountability across functions |
| BND-05 | Independent ecological organisation | No sixth function | Ecology represents delayed, remote, and future consequence across three functions |
| BND-06 | Specialised care organisation | No sixth function | Care joins several functions according to the person's condition |
| ADV-01 | Severe scarcity | Priority rules refined | Scarcity changes priorities, not the continuity responsibilities |
| ADV-02 | Disability and dependency | Equal availability refined | Accommodation and supported participation replace identical performance |
| ADV-03 | Coercive household or workplace | Outside correction required | No powerful unit may be its own final evaluator |
| ADV-04 | Persistent disagreement | Plural evidence required | Consensus and majority support are not sufficient evidence |
| ADV-05 | Migration | Scale and portability refined | Learning, care, access, and appeal must survive movement |
| ADV-06 | Concentrated technical power | Power safeguards strengthened | Systems must be inspectable, contestable, interruptible, and independently correctable |
| ADV-07 | Delayed and displaced ecological harm | Long-horizon evidence strengthened | Immediate participants and current satisfaction cannot close evaluation |
| UNI-01 | Competent minority operates the functions for everyone else | Universality test failed | Aggregate service and order do not show person-level capability or voice |
| FP-01 | Output and prosperity conceal harm and fragile provision | False positive rejected | Material evidence must include health, access, reserve, and ecology |
| FP-02 | Compliance and satisfaction arise under dependence or fear | False positive rejected | Freedom, comprehension, counterpart evidence, and correction are required |

Every function and all five Pass-Four safeguards are exercised somewhere in the case set. Cases affecting all five functions expose all 122 activity members; narrower cases expose the union of members assigned to the functions under stress. This linkage prevents a case from being discussed as a free-standing institutional example detached from the activity register.

## 3. What is derived about family

### 3.1 The invariant that survives

The family-like field consists of eight jointly durable conditions:

1. membership stable enough for responsibility to continue;
2. intergenerational learning;
3. care through dependency;
4. reciprocal recognition and voice;
5. daily bodily care;
6. participation in useful work;
7. need assessment and dependable access to provision; and
8. protection and appeal beyond the close group's own authority.

FAM-01 shows that these conditions can be specified without kinship. FAM-03 shows that they can persist without continuous co-residence when commitments, records, care, provision, voice, and appeal remain portable. These are counterexamples to the stronger proposition that one genealogical or residential form is necessary. They are not counterexamples to the durable shared-life invariant.

FAM-02 applies the reverse test. A biologically related household may provide food, shelter, work, and visible unity while obstructing learning, voice, care, and appeal. The family label is therefore not evidence of fulfilment. The model recognises as family-like whatever arrangement reliably carries the shared-life invariant and rejects as inadequate any named family that does not.

This is a genuine refinement of the original thesis. Knowledge of *jeevan* and its embodied lifecycle can support the need for a durable, intimate, intergenerational, productive, caring, and evaluative field. It does not by itself derive descent rules, marriage rules, household size, gendered roles, property form, continuous co-residence, or a single authority structure.

### 3.2 Why outside appeal belongs to the invariant

A close relationship provides evidence unavailable to a distant administration, but closeness also concentrates dependency and may hide coercion. The same group cannot be assumed both to exercise power and to judge every complaint against that power. A family-like field is therefore not complete by self-sufficiency alone. Confidential voice, protection, and feasible appeal must cross its boundary, while repair returns to the relationship where safe and possible.

This condition does not turn the family into a branch of one central institution. It establishes nested responsibility: fulfilment remains as close to the relationship as competence and safety permit, while evidence and correction extend beyond the unit when its own processes fail.

## 4. What is derived about five functions and organisations

### 4.1 Functions remain distinct even when organisations overlap

BND-01 and BND-02 test the most plausible four-function alternative from Pass Four: administrative combination of production and exchange. Combination is not inherently invalid. One cooperative, enterprise, or public body may make goods, maintain stock, allocate provision, and hold reserve. It remains adequate only if two questions can still be answered independently: whether material transformation is useful, safe, maintainable, and regenerative; and whether provision is transparently and dependably available across persons and time.

Separate purpose accounts, stock records, worker and user voice, health and ecological review, stop rights, and appeal preserve that distinction. When the same output authority controls price, stock information, health evidence, and review, saleability and profit can mask unsafe work, exclusion, or depleted reserve. The organisation then fails even though all operations appear administratively integrated.

The five-function conclusion is therefore about non-substitutable responsibilities, not exclusive organisational boundaries. One organisation may carry several functions with effective firewalls. One function may require many organisations at close, local, specialised, and wider scales.

### 4.2 Why science, governance, ecology, and care do not create a sixth function

The boundary test asks whether a proposed sixth function maintains a new continuity object or protects the operation and interfaces of the five already identified.

Science maintains disciplined inquiry, causal knowledge, measurement, criticism, and correction. Its work changes what is understood, how bodily conditions are assessed, how production is designed, how distribution is measured, and how remote ecological effects become visible. An autonomous research organisation may be indispensable because evidence must remain reportable against educational, commercial, or governing pressure. The object under consideration nevertheless remains one of the five: understanding, relational claim, bodily capability, material transformation, or continuity of access.

Governance coordinates authority, reasons, resources, affected-party voice, review, and correction across the same functions. A distinct governing organisation may be necessary, but governing activity without educational, just, healthy, productive, or distributive content has no additional human endpoint. Its validity is tested by whether it protects those functions without replacing understanding with command.

Ecology supplies a long-horizon and displaced-consequence standpoint on bodily capability, material transformation, and future availability. Dedicated ecological monitoring and protection may require separate organisations precisely because present producers and beneficiaries cannot be final judges of delayed harm. The continuity object remains bodily-material-regenerative capability rather than a sixth kind of fulfilment.

Care changes its concrete object with the person and condition: learning, relationship, bodily support, work capability, or continuity of provision. Specialised care can be independently organised while remaining a mode of responsibility joining several functions.

No tested case therefore adds a sixth continuity object. This conclusion does not show that five is numerically unique under every possible ontology or grain. It shows why more than five organisations can be necessary without requiring more than five functions at this grain.

## 5. Adverse conditions refine the architecture

### 5.1 Scarcity requires reasoned priority and restoration

Scarcity can make simultaneous satisfaction of all stated needs impossible. It does not suspend justice, health, production, or reserve. It increases the importance of transparent information about stock and need, minimum protection, participatory priority rules, burden visibility, appeal, and a plan to restore capability. Aggregate output or formally equal rations can remain unjust when needs and dependency differ.

The refinement is procedural and evidentiary. A scarcity decision is evaluated by avoidable harm, distribution of burdens, reserve use, stated reasons, revision, and recovery over time. “Emergency” cannot become an indefinite exemption from voice or correction.

### 5.2 Disability changes the form of participation, not its universality

The common architecture of *jeevan* does not imply identical bodies, communication modes, skills, or independent role performance. Disability and dependency require accessible communication, accommodation, supported choice, role adaptation, care, and review of representation. Equal availability means that each person can develop and exercise capability, express a standpoint, receive provision, contribute in an appropriate form, and invoke correction. It does not mean that every person performs every task without support.

This refinement prevents a formal equality test from excluding the very persons whose dependency makes durable social responsibility most visible.

### 5.3 Coercion and disagreement require evidence outside power

Coercive households, workplaces, and technical systems often generate the appearance of agreement. Low complaint rates, compliance, retention, or reported loyalty can be consequences of dependence and retaliation rather than evidence of fulfilment. Effective validation therefore requires confidential testimony, safe dissent, access to reasons and counterevidence, feasible exit or protection, independent review, and observable remedy.

Disagreement is not itself failure. A functioning order must permit contested interpretations of relationship, evidence, risk, and consequence to be stated and revised. Neither institutional reputation nor majority support establishes correctness. First-person, counterpart, competent, bodily-material, and long-horizon evidence must be brought together according to the object under evaluation.

### 5.4 Movement, concentrated technology, and ecological delay require wider scales

Migration shows that responsibility cannot be exhausted by fixed residence. Learning records, care commitments, recognised voice, access to provision, and appeal must remain portable across local boundaries. Technological concentration shows that competence alone cannot legitimate control over infrastructure, information, allocation, and audit. Critical systems must remain inspectable, contestable, interruptible, independently reviewed, and recoverable after failure.

Ecological delay extends evidence beyond present participants. Baselines, causal monitoring, uncertainty, remote effects, future representation, precaution, responsibility, and restoration are necessary where harm arrives elsewhere or later. The appropriate scale follows the consequence: responsibility stays local where local competence and evidence are adequate and expands wherever effects, dependency, mobility, or correction cross the local boundary.

## 6. Minimum evidence for the five functions

No single indicator establishes correct functioning. Evidence must match the continuity object and include a practical path from detected failure to correction.

| Function | Minimum observable field | Insufficient proxies | Person-level and correction test |
|---|---|---|---|
| Education-*sanskar* | A person can state, test, apply, and revise understanding; learning appears in conduct and survives teacher turnover | Attendance, certificate, recitation, teacher reputation | Each person has access to language, inquiry, feedback, safe dissent, and demonstrated competence |
| Justice-security | Recognition, informed consent or refusal, reciprocal fulfilment, harm repair, and non-retaliatory appeal | Obedience, majority support, low complaints, reported harmony | Each person has voice, boundaries, reasons, protection, appeal, and effective remedy |
| Health-restraint | Bodily report, condition, exposure, accommodation, intervention, and delayed outcome | Productivity, appearance, attendance, absence of diagnosis | Each person has sufficient means, informed participation, care, accommodation, refusal of unsafe exposure, and appeal |
| Production-work | Need, inputs, skill, labour conditions, use, maintenance, waste, and ecological effect | Output, profit, saleability, efficiency, worker compliance | Each person has useful skill, safe contribution, user feedback, stop rights, and a route to redesign, repair, restoration, or cessation |
| Exchange-reserve | Need, stock, terms, access, exclusion, reserve, future reliability, and displaced effect | Transaction volume, price, aggregate surplus, delivery speed | Each person has dependable access, need-voice, transparent terms, review, and remedy against exclusion or exploitation |

The evaluator set changes by function but cannot be reduced to the institution's own report. Relevant combinations include the first person, counterpart, affected third party, embodied or material evidence, skilled peer, independent reviewer, and a proxy for remote or future consequence. Convergence among these standpoints is stronger than any isolated measure. Disagreement triggers inquiry and correction rather than automatic averaging.

## 7. What survives, what is revised, and what is rejected

### 7.1 Conclusions that survive the analytical tests

- All five continuity responsibilities remain necessary somewhere in the tested cases, and none of the cases discloses a sixth non-substitutable object.
- A durable shared-life field remains necessary for integrated care, learning, relationship, bodily life, useful work, need assessment, and continuity.
- Independent evidence and correction are constitutive institutional requirements rather than optional safeguards added after performance.
- Science, ecological inquiry, communication, governance, and care operate across the five functions and may need specialised, independent organisations.
- Responsibility is polycentric: it belongs near the activity where competent fulfilment is possible and extends outward as consequence, dependency, mobility, or correction requires.

### 7.2 Conclusions that require refinement

- “Family” denotes a durable shared-life invariant. Kinship and co-residence are possible realisations, not necessary and sufficient criteria.
- “Five institutions” must be stated as five functions. Organisational count and boundaries remain variable.
- Administrative combination is permitted only when purposes, records, decision rights, evidence, and correction remain distinguishable.
- Equal availability means supported capability, voice, access, contribution, and correction, with accommodation; it does not mean identical task performance.
- Local self-reliance means dependable local capability joined to portable and wider support, not isolation.
- Practical minimality remains relative to the selected analytical grain and tested alternatives.

### 7.3 Claims rejected by the tests

- Biological relation, household designation, or co-residence alone establishes a fulfilled family.
- The five faculties or five social functions entail exactly five organisations.
- One organisation may control performance, evidence, allocation, and final appeal merely because its operations are integrated.
- Compliance, consensus, reputation, prosperity, output, efficiency, immediate satisfaction, or low complaint rates are sufficient evidence of fulfilment.
- Performance by a competent minority establishes universal availability for all persons.

These rejections make the central thesis more precise. The common architecture of *jeevan* supports universal access to a functional and relational order. It does not license a universal social blueprint whose names count as their own evidence.

## 8. The external architecture after Pass Five

The resulting environment can now be stated as nested requirements rather than predetermined institutions.

At the **personal and embodied scale**, every person needs time and freedom for inquiry, language and skill, bodily means, access to consequences, supported participation where needed, and a feasible path to correction.

At the **durable shared-life scale**, every person needs continuing relations that integrate care, learning, value-fulfilment, bodily life, useful work, assessment of need, provision, and protection. This field may take different kin, non-kin, residential, or multi-local forms if the invariant remains observable.

At the **local cooperative scale**, work, health support, skill, maintenance, exchange, conflict correction, records, and reserves need capable bearers close enough for affected persons to participate. Functional combination is possible, but evidence and appeal cannot be captive to the authority being evaluated.

At the **specialised and wider scale**, advanced knowledge, uncommon care, mobility, major harm, distributed stock, technical concentration, and ecological delay require wider competence and independent review. The boundary of coordination follows the boundary of consequence.

Across all scales, education develops each person's capability to understand and verify; justice protects reciprocal claims and correction; health preserves embodied capability and restraint; production transforms nature through useful and regenerative work; and exchange maintains transparent access and reserve across persons and time. Science disciplines inquiry within and across these functions. Governance coordinates their decision rights and accountability. Care sustains persons through dependency. Ecology extends material evidence across place and time.

This architecture is universal in availability and criterion, not uniform in administration. A proposed family, school, workplace, market, clinic, research body, cooperative, or governing arrangement belongs to the acceptable equivalence class only when it supplies the relevant lifecycle, evidence, person-level access, and correction conditions.

## 9. Limits and empirical handoff

Pass Five completes the planned counterfactual and adverse-case analysis. It does not complete empirical validation. The nineteen cases were designed from known vulnerabilities in the model and therefore cannot estimate how often arrangements succeed, how safeguards interact under real pressure, or what thresholds distinguish nominal from effective access.

The next research stage should apply the case and evidence protocol to contrasting actual arrangements. It should include people with different authority, dependency, bodily capability, work roles, and access to resources; gather first-person, counterpart, material, institutional, and long-horizon evidence; trace whether a complaint changes the condition; and observe continuity through turnover or time. Independent analysts should also recode a sample of the 122 activities and propose additional function bundles or candidate continuity objects.

A case revises the model if a real arrangement satisfies the stated evidence and correction conditions yet cannot sustain an activity lifecycle, or if a necessary continuity object cannot be represented by U01-U05 without forced combination. A case revises an arrangement, rather than the model, when the invariant identifies a missing condition and an alternative supplies it. This distinction must be preserved in later field work.

The justified conclusion after five passes is therefore conditional but substantial: the activity architecture of *jeevan*, considered in embodied relationship and material consequence, supports a universal requirement for a durable shared-life field and five non-substitutable social functions. It does not uniquely derive kinship form, administrative scale, property system, technology, or organisational count. Those remain design variables within an evidence-bound and correctable equivalence class.

## References

### Related research notes and artifacts

- [*Bottom-Up Pilot Derivation of Jeevan Activity Spheres*](Research-Note-Jeevan-Activity-Environment-Pilot-Dossiers.md) - the refined five-pass sequence and initial counterexample rules.
- [*Pass-Two Lifecycle and Evidence Coding of All 122 Jeevan Members*](Research-Note-Jeevan-Activity-Lifecycle-Pass-Two.md) - the activity-member requirements from which later spheres and functions were derived.
- [*Pass-Three Derivation of Jeevan Activity Spheres*](Research-Note-Jeevan-Activity-Spheres-Pass-Three.md) - the anonymous stable cores, bridges, residuals, and interfaces.
- [*Pass-Four Derivation of Durable Social Functions from Jeevan*](Research-Note-Jeevan-Durable-Functions-Pass-Four.md) - the five continuity channels, family-like field, and comparative bundle result placed under test here.
- [*From the Activity Architecture of Jeevan to Universal Human Order*](Research-Note-Jeevan-To-Universal-Human-Order.md) - the central social thesis refined by the Pass-Five result.
- [*Jeevan Activity-to-Sphere Dossier Template*](Research-Template-Jeevan-Activity-Environment-Dossier.md) - the reusable activity analysis and validation schema.
- [*Pass-Five Validation Cases*](Research-Data-Jeevan-Pass-Five-Validation-Cases.csv) - the complete case specifications, observables, results, and revision routes.
- [*Pass-Five Evidence Protocol*](Research-Data-Jeevan-Pass-Five-Evidence-Protocol.csv) - minimum observables, evaluator standpoints, false proxies, correction tests, and person-level tests for the five functions.
- [*Pass-Five Validation Summary*](Research-Data-Jeevan-Pass-Five-Validation-Summary.json) - reproducible counts, scope limits, and conclusions.

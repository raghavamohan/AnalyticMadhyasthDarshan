# A State-Dynamic Model of Coexistence

**Author:** [AnalyticMadhyasthDarshan.org](https://github.com/raghavamohan/AnalyticMadhyasthDarshan) — a group of people studying Madhyasth Darshan philosophy. Source repository: [raghavamohan/AnalyticMadhyasthDarshan](https://github.com/raghavamohan/AnalyticMadhyasthDarshan).

**Edited on:** August 24, 2026, 10:01 PM IST
**Status:** Draft

**The question:** Madhyasth Darshan describes existence as coexistence: countlessly many active units saturated in one unbounded, motionless Omnipresence. Within that description, the material, pranic, and animal orders continue in definite activity, while the human knowledge order can know, evaluate, and refine its own conduct. Can those claims be stated as one model — one account of state, activity, and relationship that holds from the atom to human conduct without breaking the texts' own commitments?

This paper reconstructs that account as a **typed qualitative hybrid transition system**. Omnipresence (*satta*) is state-complete; nature consists of state-dynamic units. Every unit bears form (*roop*), property (*guna*), essential nature (*svabhav*), and *dharma*, while its activity is effort, motion, and result together. Continuous change may occur within a bearer, but composition, disintegration, constitutional completeness, and body–*jeevan* association require guarded transitions between typed states.

Two development lines meet without collapsing into one. Composition closes atoms, molecules, compounds, cells, and bodies as distinct bearers. Atomic development reaches constitutional completeness (T1), yielding *jeevan*. An animal joint form combines *jeevan* with an animal body and evidences species-conformant recognition and evaluation. A human joint form combines *jeevan* with a human body and can additionally know, believe, evaluate reflexively, refine *sanskar*, and evidence understanding in relationship and work. Activity completeness (T2) names inner resolution; conduct completeness (T3) names its stable public evidence.

The primary texts supply the ontology and qualitative relations, not state vectors, transition systems, algorithms, or numerical measures. The formalism therefore keeps direct textual claims, translation choices, analytical constructions, proposed operational criteria, and open empirical questions visibly distinct.

## Standpoint and scope

These studies are written from the standpoint of a scientist and technologist trained to graduate-level physics and mathematics and familiar with conservation laws, phase-space models, and contemporary accounts of material binding. From that background, matter-first explanations are familiar: configurations evolve under forces, and consciousness is often identified with brain processes or treated as emergent from physical activity. The natural sciences constrain any credible account of material trajectory through mechanism, prediction, and public evidence, but their success does not by itself settle the hard problem of consciousness, the status of the self, or the reality of value in favour of matter-only reductionism.

The paper reads Madhyasth Darshan's primary texts, states the darshan's claims, and then reconstructs them in parallel with the mathematics of state and motion. Comparison with physics and the natural sciences is therefore one leg of the work, not the sole framework into which the philosophy must be translated. Full comparison with Advaita Vedanta and modern Western philosophy of mind, value, and society is developed in the related topical studies and is not repeated here.

The aim is rigorous comparative understanding — testing definitions, internal consistency, and the limits of the formal analogy — rather than persuasion or devotional endorsement. Logical reconstruction, first-person realisation, evidence in conduct, and instrument-based scientific confirmation are kept distinct so that agreement at one level is not mistaken for agreement at every level. Physics and dynamical-systems language do not establish immortal *jeevan*, constitutional completeness, or undivided society; those remain explicit points for examination.

Clear and checkable prose remains the series priority. This paper is a formal reconstruction of structure already stated in the topical studies; it does not require a further layer of category theory or proof, and it does not treat the reconstruction as source doctrine.

## Model at a glance

```mermaid
flowchart TD
    E["Existence as coexistence"] --> O["State-complete satta"]
    E --> U["Countlessly many state-dynamic units"]
    O -. "saturation" .-> U
    U --> ONE["Each unit: roop · guna · svabhav · dharma"]
    ONE --> EMR["One activity: effort · motion · result"]
    EMR --> MUT["Actual mutuality, recognition, complementarity and pressure"]

    U --> CL["Compositional development"]
    CL --> MAT["Atoms → molecules → compounds"]
    MAT --> BIO["Cells → plant, animal and human bodies"]

    U --> AL["Atomic development"]
    AL --> T1["T1: constitutionally complete jeevan"]
    BIO --> AB["Animal body"]
    T1 --> AJ["Animal joint form"]
    AB --> AJ
    AJ --> AE["Species-conformant recognition, hope and evaluation"]

    BIO --> HB["Human body"]
    T1 --> HJ["Human joint form"]
    HB --> HJ
    HJ --> HF["Five faculties / ten activities"]
    HF --> REC["Recognition → action → consequence → evaluation"]
    REC --> DEL["Deluded recurrence"]
    REC --> AW["Study → bodh → anubhav"]
    AW --> T2["T2: activity completeness"]
    T2 --> T3["T3: conduct completeness"]
    T3 --> PUB["Relationship, work, family, society and orderliness"]
```

The diagram shows two joints that organise the whole paper. First, the four aspects and the effort–motion–result triad describe the same active unit. Second, compositional development supplies bodies while atomic development supplies T1 *jeevan*; animal and human joint forms arise where those lines meet. The human is not a later animal composition, and *jeevan* is not produced by a body.

### Model contract

| Kind of statement | Meaning in this paper | Example |
|-------------------|-----------------------|---------|
| Direct textual claim | Stated in the primary texts in ordinary philosophical prose | Coexistence, saturation, four orders, the triad, tetrad, T1–T3, ten activities |
| Translation choice | One English running term selected where translations vary | Omnipresence for *satta*; contemplation for *chintan* |
| Analytical reconstruction | A structure introduced to keep the claims explicit and mutually consistent | Typed states, relation graph, guarded transitions, observation maps |
| Proposed operational criterion | A checkable interpretation whose exact equivalence is not stated by the texts | Qualitative predicates for T2, T3, animal evaluation and public verification |
| Open empirical question | A source claim without an accepted contemporary scientific counterpart | Physical identification of T1 and persistence of *jeevan* apart from a body |

This contract governs every symbol and diagram. A formal object may organise a textual claim without becoming a further claim of the darshan.

### Core glossary

| Term | Plain meaning |
|------|---------------|
| Coexistence (*saha-astitva*) | The inseparable presentness of state-complete *satta* and countlessly many state-dynamic units. |
| Saturation (*samprikt*) | Every unit is soaked, submerged, and surrounded in *satta*, the basis of its energy-fullness and activity. |
| Unit (*ikai*) | A bounded, countable bearer whose activity is effort, motion, and result together. |
| Effort–motion–result (*shram–gati–parinam*) | Three simultaneous aspects of one unit-activity. |
| Tetrad | Form (*roop*), property (*guna*), essential nature (*svabhav*), and *dharma* as four aspects of one unit. |
| Mutuality | The actual facing among units and the order-specific recognition through which complementarity or contradiction is evidenced. |
| Pressure | Force recognised in state; excitation-pressure is the received compulsion evident in an excited facing. Neither is an external energy reservoir. |
| Closed bearer | An atom, molecule, compound, cell, body, or joint form with its own bounded conduct and tetrad. |
| Constitutional completeness (T1) | The irreversible atomic threshold at which *jeevan* is free of molecular- and weight-bondage and bears hope-bondage. |
| *Jeevan* | The constitutionally complete sentient atom that operates through an animal or human body. |
| Animal joint form | Animal body with *jeevan*, evidencing hope to live, species-conformant recognition and limited evaluation. |
| Human joint form | Human body with *jeevan*, capable of knowing, believing, reflexive evaluation, refinement and humane conduct. |
| Activity completeness (T2) | Restfulness of effort through realised inner resolution. |
| Conduct completeness (T3) | Destination of motion through repeatable humane conduct. |

The expanded terminology and every model symbol are collected in Appendix B.

## 1. Ontological foundations

Madhyasth Darshan holds that existence is neither a collection of static material substances nor an undifferentiated idealist field. Existence is coexistence (*saha-astitva*): the inseparable, perpetual presentness of Omnipresence (*satta*) and countlessly many discrete, active units (*ikai*) (SB, pp. 48–50; MVD, pp. 11, 34). Omnipresence is **state-complete** (*sthitipurna*): unbounded, everywhere uniform, non-transforming, and free from motion and pressure. Nature is **state-dynamic** (*sthitishil*): every bounded unit is inseparably present in state and motion within the state-complete (MVD, p. 26; SB, pp. 49–50, 248; KD 3.5, p. 70; KD 3.8, p. 84). The whole neither increases nor decreases, expands nor contracts, while development and awakening become manifest within it (KD 3.5, p. 70).

Every unit is saturated (*samprikt*) in Omnipresence: soaked, submerged, and surrounded in it. Omnipresence is permeative through units and present between them. That between-ness makes their boundaries and mutual distances possible; the same condition permits joining and separation without ever separating a unit from Omnipresence (SB, pp. 48–50, 249–250; JV, p. 149). Saturation is not a transfer from a finite store and Omnipresence does not push units by an applied force. It is the ontological basis on which each unit is energised, forceful, self-regulated, and active (MVD, pp. 40–41, 46; SB, pp. 57, 61, 69, 248; JV, p. 149; KD 3.9, p. 88; KD 3.13, p. 122).

This distinction is also stated as **absolute energy** and **relative energy**. Absolute energy is Omnipresence itself: everywhere present, non-active in itself, and the basis of basic impulsion. Relative energy is the unit's power made evident in mutuality; pressure, waves, fields, heat, sound, electricity, and related effects are physical-chemical expressions of that relative power (MVD, pp. 40–41). Omnipresence is also named fundamental uniform energy, while the perpetual activity of molecules, atoms, and atomic particles evidences that each is energised (KD 3.13, p. 122). Pressure does not supply a second stock of activity or stand beside *bal* and *shakti* as an additional power. It is the unit's force recognised in state and, in the narrower excitation sense, the compulsion received in an excited mutuality; such mutual pressure can condition change without becoming an external energy source (MVD, pp. 46, 114; SB, pp. 49, 59, 256; KD 3.11, pp. 105–106; KD 3.13, p. 118).

Mutuality is inherent in coexistence. Units recognise one another according to their order, and complementarity becomes evident through offering, acceptance, influence, composition, nourishment, use, and fulfilment. Recognition in the first three orders names definite response according to constitution, seed, or species. Necessary propensity leads to recognition and mutual recognition, while natural-state motion evidences determinate conduct at a good mutual distance (KD 3.5, p. 70; KD 3.10, p. 100).

Generative (*sam*), degenerative (*visam*), and mediative (*madhyastha*) tendencies belong to property; mediative activity regulates generative and degenerative tendencies (MVD, p. 26; KD 3.10–3.11, pp. 100–104; SB, p. 248). Excitation-pressure is received compulsion where *sam–visam* excitation is evident, while the wider state sense recognises force as pressure. An unfulfilled complementarity is not by that fact alone physical pressure. Every unit has inherent strength, and progress proceeds through mutual offering and acceptance (MVD, pp. 114, 230; SB, pp. 49–51, 61; JV, pp. 157–158).

The total activity of any unit is the triad of **effort–motion–result** (*shram–gati–parinam*). These are not three successive moments on a timeline in which effort causes motion and motion later produces a result. They are simultaneous, co-extensive dimensions of one activity-whole:

> **"Every physical-chemical activity is an inseparable presence of effort, motion and result."**
> — SB, p. 58

## 2. A typed qualitative reading of the triad

The reconstruction uses continuous change only within a fixed bearer type and guarded transitions when a bearer forms, disintegrates, reaches T1, or enters or leaves a joint form. Time indexes the duration (*kaal*) of unit-activity rather than a container in which a unit is placed (see [*Nature of Time*](../Nature-Of-Time/Nature-Of-Time.pdf)). The resulting system is qualitative and hybrid: its labels and predicates preserve textual distinctions without pretending that the sources provide numerical coordinates or differential laws. Appendix A states the corresponding types and transition rules.

### 2.1 Result (*parinam*) and model state

*Parinam* is the form or configuration realised in a unit's activity: a different existent state in a quantitative and qualitative chain (KD 3.11, p. 107). The model writes that configurational result as *r*<sub>i</sub>. It writes the modeller's fuller description as *x*<sub>i</sub>, which may also record bearer kind, constitution, relations, and orientation. Keeping *r* and *x* distinct prevents spatial *roop* from being mistaken for every coordinate needed to describe a cell, body, animal, or human. Human action-consequences receive a third symbol, *y*, because bodily, relational, and natural consequences are broader than configurational *parinam* alone (§9.2).

### 2.2 Effort (*shram*) as strength in the state

Effort is strength or force (*bal*) borne by the unit. The state is the force-bearing side of activity, while power is present in motion; effort is explicitly aligned with *dharma* and *svabhav* (SB, pp. 60–61, 248, 256–257). State and motion are indivisible, and their meanings as strength and power apply across units from atoms to planetary bodies (KD 3.8, p. 84; KD 3.11, pp. 102–109). The model represents effort by a qualitative strength description *B*<sub>i</sub>, not a scalar magnitude, potential, or stored quantity. The bearer's type already carries its order-specific *dharma*; *dharma* is therefore an invariant of the admissible state and transition family, not a moment-to-moment control input. Forcefulness remains present in every state, and effort persists until its stated restfulness in completeness (SB, pp. 60–61).

> **"Strength in state evidences orderliness in oneself; power in motion evidences participation in the overall orderliness."**
> — KD 3.11, p. 106

### 2.3 Actual mutuality and recognised mutuality

No unit is met in isolation. Form is reflected, power becomes effect, and complementarity or contradiction becomes evident in reciprocity (SB, pp. 49–51, 249–252). The model separates the relation actually present, *R*<sup>actual</sup>, from the relation operatively recognised, R̂. In material and pranic activity, and in species-conformant animal activity, recognition is definite according to constitution, seed, or species. In the human, R̂ can agree with or diverge from *R*<sup>actual</sup>; this difference is indispensable for modelling misrecognition and justice. Neither term is a force or universal deficit score. Together they record which bearers meet, what coupling joins them, and what order-specific complementarity, nourishment, use, relationship, or fulfilment is at issue.

### 2.4 Motion (*gati*) as power with a *guna*-profile

Motion is the unit's power (*shakti*) in operation: displacement, change of configuration, or another order-specific transformation. Generative, degenerative, and mediative tendencies give that power its *guna*-profile γ; essential nature gives the expression its order-specific functional character. *Sam* does not already mean integration in every order, nor does *visam* already mean cruelty. The sources allow mediative regulation to remain active while generative or degenerative tendencies are evident, so γ is a qualitative profile or dominant regime rather than a one-hot selector (MVD, p. 26; SB, pp. 60–62; KD 3.10–3.11, pp. 100–107). The transition relation is typed by the bearer's kind, manifested order, coupling kind, essential nature, and γ. The order type carries *dharma* as an invariant; it is not added as a separate force.

Natural-state motion is continuing power under definite conduct, with mediative regulation maintaining orderliness. Generative and degenerative tendencies remain activities of the unit's own property. The distinction from excitation concerns the facing and its pressure-expression, not the presence or absence of inherent strength and power.

### 2.5 State-pressure and excitation-pressure

Pressure has a general and a narrow sense. Force in state is recognised as pressure and power in motion as flow; the model marks this general expression as Π<sup>state</sup> (SB, pp. 49, 256; KD 3.11, pp. 105–106). When *sam–visam* excitation is present, the received compulsion is excitation-pressure, Π<sup>exc</sup> (SB, p. 59; KD 3.13, p. 118). Departure from good mutual distance and its mediative restoration provide a material illustration (KD 3.11, pp. 103–104). Both terms belong to the force–power–property activity of units in mutuality. They may condition a transition through the relational facing, but neither is an energy reservoir, an applied force from *satta*, or a measure of every unfulfilled human relation.

### 2.6 Result and continuing transition

Over a duration, motion is evident as a changed result, and that configuration is immediately a force-bearing state in further mutuality. Effort is the grandeur of existent state, motion the spreading of effect, and result a different existent state in a quantitative and qualitative chain (KD 3.11, p. 107). Appendix A represents this continuity by transitions between complete activity-occurrences, without dividing one occurrence into effort first, motion second, and result last. Pressure and flow are simultaneous expressions within the occurrence; a transition records what becomes different across duration (MVD, pp. 40, 114; SB, pp. 58–62, 248, 256–257; KD 3.8, p. 84).

For material and pranic bearers, constitution, structure, seed, and mutuality determine the next expression without sentient comparison. Animal *jeevan* adds species-conformant recognition and evaluation; human *jeevan* adds knowing, believing, reflexive evaluation, dissatisfaction, and possible refinement of *sanskar*. These later layers relate complete activities to one another without changing the universal triad within any activity.

## 3. The tetrad in the state-dynamic model

Every unit has four inseparable aspects: form (*roop*), property (*guna*), essential nature (*svabhav*), and *dharma* (MVD, p. 47). They specify one activity-whole: effort or strength is present as *dharma–svabhav*, motion or power as *svabhav–guna*, and result as *roop* (SB, pp. 60–62). *Svabhav* crosses effort and motion; *guna* describes the relative power expressed in mutuality. The same tetrad attaches to every closed bearer — atom, molecule, cell, body, or joint form — rather than being inherited as a sum from its constituents (§5.4).

```mermaid
flowchart TB
    SATTA["State-complete satta"] -.->|"saturation"| UNIT["State-dynamic unit"]
    subgraph ACT["One inseparable unit-activity"]
      direction LR
      EFFORT["Effort / strength<br/>dharma + svabhav"]
      MOTION["Motion / power<br/>svabhav + guna-profile"]
      RESULT["Result / present form<br/>roop"]
      EFFORT --- MOTION
      MOTION --- RESULT
      RESULT --- EFFORT
    end
    UNIT --> ACT
    ACTUAL["Actual mutuality R_actual"] --> MOTION
    ACTUAL --> RECOG["Operative recognition R_hat"]
    EFFORT -.-> PSTATE["State-pressure Pi_state"]
    MOTION -.->|"when excitation is present"| PEXC["Excitation-pressure Pi_exc"]
    ACTUAL -.-> PEXC
    RESULT -->|"changed configuration across duration"| NEXT["Next complete activity-occurrence"]
```

Undirected spokes mark co-present aspects of one activity. Directed arrows mark analytical dependence or a relation across duration, not a temporal decomposition of the triad.

### 3.1 Form (*roop*): bounded configuration

*Roop* is the spatial configuration, boundary-framework (*rachna*), shape, volume, and density of the unit (MVD, p. 50; SB, pp. 249–250). It maps to configurational result *r*<sub>i</sub>, the different existent state present after motion spreads effect (KD 3.11, p. 107). The modeller's full state *x*<sub>i</sub> may contain further non-spatial and relational fields and is therefore not identical with *roop*. Form is unit-grounded; reflection presents it in mutuality without creating it (MVD, pp. 42, 49–50; KD 3.9, p. 94).

### 3.2 Property (*guna*): relative power in motion

*Guna* is relative power (*sapeksha shakti*), the effect and influence that arise when units come into mutuality (MVD, pp. 40, 47; SB, pp. 248–252, 256–257). It aligns with motion or power, which spreads effect and participates in overall orderliness (KD 3.8, p. 84; KD 3.11, pp. 102, 106–107). Generative, degenerative, and mediative activities occur across the four orders, with mediative activity regulating the generative and degenerative tendencies (MVD, p. 26; SB, p. 248; KD 3.10–3.11, pp. 100–104). The model records their qualitative profile γ without assigning weights or requiring mutual exclusivity. State-pressure and excitation-pressure describe force–power encountered in mutuality; neither is a fourth *guna*.

In the first three orders, constitution, conformance, and neighbourhood determine the expressed profile without human reflective option. In the knowledge order, the same three tendencies remain powers of *jeevan*, while their expression in conduct is answerable to understanding and freedom of action. Delusion can express degenerative property in treachery, exploitation, and war; awakening establishes mediative conduct (KD 3.10, pp. 100–101). Knowledge reorganises expression without creating the underlying power.

### 3.3 Essential nature (*svabhav*): functional character

*Svabhav* is fundamental character (*maulikata*) and the usefulness (*upayogita*) of properties (MVD, p. 47). Usefulness here is order-specific functional significance, not benefit to a human observer: the same texts include devitalising and cruel essential natures. *Svabhav* spans effort and motion, bridging strength and the order-specific expression of power. Material units integrate or disintegrate, pranic units vitalise or devitalise, animal units evidence cruel or non-cruel conduct, and knowledge-order units evidence humane or inhumane dispositions (MVD, pp. 50–51, 57–58; SB, pp. 60–61, 179–180; KD 3.9–3.10, pp. 98–102). The transition relation is therefore typed by an admissible essential nature *s* and *guna*-profile γ. Multiple tendencies may be concurrently regulated; the source lists do not establish a one-hot selection rule.

Knowledge-order essential nature is explicitly refinable. Human-opposing expression appears as baseness, wretchedness, cruelty, covetousness, and causing pain; humane and higher-humane expression appears as fortitude, valour, generosity, kindness, grace, and compassion. Education, study, and the qualitative development of *sanskar* make transformation from the former toward the latter possible (KD, pp. 8–9, 26–27; KD 3.9, pp. 98–99). This transformability belongs to the human joint form. It does not make the constitution-governed *svabhav* of a mineral or plant into a voluntary choice.

### 3.4 *Dharma*: innateness and invariant orientation

*Dharma* is innateness (*dharana*): what is borne, maintained, and characteristic of an entire order (MVD, p. 47). It is present on the side of effort with *svabhav* (SB, pp. 60–61). Existence, growth, hope to live, and happiness are stated cumulatively across the four orders (MVD, p. 115; SB, p. 179; KD 3.9–3.10, pp. 95, 100–102). Human *dharma* remains happiness through resolution and orderliness even while a deluded human misunderstands its fulfilment (JV, pp. 110, 121–123; KD 3.5, p. 69). The model treats *D*<sub>o</sub> as an invariant attached to the order type and uses a separate `fulfils_dharma` predicate for particular conduct. This preserves *dharma* on the effort side without turning it into a causal signal or physical potential.

### 3.5 The four orders

| Order | Typical bearer | Cumulative *dharma* | Essential nature emphasised here | Continuing conformance | Sentient evaluation |
|-------|----------------|----------------------|-----------------------------------|------------------------|---------------------|
| Material | Atom, molecule, compound, mineral | Existence | Integration and disintegration | Constitution or structure | None |
| Pranic | Cell, plant body, animal or human body as bodily medium | Existence and growth | Vitalising and devitalising | Seed and body lineage | None |
| Animal | Animal body with T1 *jeevan* | Existence, growth, hope to live | Cruel and non-cruel conduct | Species | Recognition of essential nature, friendliness and opposition |
| Knowledge | Human body with T1 *jeevan* | Existence, growth, hope to live, happiness | Human-opposing, humane and higher-humane conduct | *Sanskar* | Reflexive evaluation through knowing, believing, justice, *dharma,* truth and value-fulfilment |

The table separates bodily kind from manifested order. Animal and human bodies are pranic bearers; the animal and knowledge orders become manifest through their association with T1 *jeevan*.

## 4. Compositional development and closed bearers

The insentient line (*jada*) spans the material and pranic orders. A constitution-oriented atom, a molecule, a cell, and a body are not successive coordinate values of one bearer. Each closure establishes a bearer of a different type, with its own boundary, activity, tetrad, constituents, and relations. Composition is therefore represented by formation and disintegration transitions among typed bearers rather than by movement through one continuous state space.

Definiteness in this line does not mean immobility. *Roop* and result change, particles exchange, compositions form and disintegrate, and pranic bodies grow. Recognition and fulfilment occur according to constitution, structure, or seed rather than sentient evaluation. The unit remains state-dynamic while its conduct is definite by type and conformance.

### 4.1 Constraints of the material field

The material account distinguishes atomic constitution, molecular bonding, and weight-bonding. Atomic constitution (*gathan*) concerns the number and arrangement of particles in the nucleus and orbits. Hungry and overfull atoms remain open to absorption or displacement until a further definite atomic result is established (KD 3.1–3.3, pp. 56–62). **Molecular-bondage** concerns one atom joining another in a molecule rather than the particle count internal to one atom (KD 3.11, pp. 103–104). **Weight-bondage** concerns the weight-bearing relation of constitution-oriented atoms, molecules, and material bodies. Constitutionally complete *jeevan* is described as free of both bondages (MVD, p. 91; KD 3.3, p. 62). Inertia is not added as a separate doctrinal category.

### 4.2 Particle exchange, molecular joining, and closure

Before an overfull atom displaces a particle it is excited; the displaced particle can be absorbed by a hungry atom, after which both atoms establish their respective natural-state motions (KD 3.1, pp. 57–58). Molecular joining is related but distinct: atoms recognise one another and remain together at a definite good distance (KD 3.11, pp. 103–104). The model represents openness by an exchange-enabled relation and guarded displacement or absorption events, not by the failure of a trajectory to converge.

When complementary participation closes a new motion-path, a **compound** (*yaugik*) presents a new bearer with its own bounded conduct and tetrad. In a **mixture**, no new bearer closes and the components continue to exhibit their respective conducts (MVD, p. 42). A closure event creates the containing bearer and its part relation; a disintegration event removes that closure while the constituents persist according to their own types.

Composition and atomic development remain different processes. A compound, cell, or body may close as a new bearer while atomic development toward constitutional completeness proceeds on its own line (SB, pp. 75–76; KD 3.2–3.3). Their meeting in animal and human joint forms does not turn the two lines into one ladder.

### 4.3 Typed compositional bearers

The model assigns each kind of closed bearer its own qualitative state type: *X*<sub>atom</sub>, *X*<sub>molecule</sub>, *X*<sub>compound</sub>, *X*<sub>cell</sub>, *X*<sub>plant-body</sub>, *X*<sub>animal-body</sub>, and *X*<sub>human-body</sub>. Constitutive dependency among these types is a partial order, not set inclusion. A molecule depends on atoms without being an atom-state; a body depends on cells without being a cell-state. Within each type, form and relations may change while the bearer's bounded conduct remains recognisable.

The compositional sequence the texts set out on this earth runs, under conducive conditions, from constitution-oriented atoms through molecules and molecule-composed solids, liquids, and rarefied states, through compounds and minerals, through chemical resonance that yields nourishment- and composition-elements, through pranic cells, through plant-order bodies, through animal bodies, and as far as the human body whose *medhas* composition is the richest compositional plateau (KD 3.2, pp. 58–60). Four orders are perceivable in that sequence: the material state in soil and stone; the pranic state in the plant-order; the *jeevan* state and the knowledge state as joint forms of body and *jeevan* (KD 3.2, p. 59; SB, p. 179).

| Bearer type | Closed unit | Manifested order | Continuing conformance |
|-------------|-------------|------------------|------------------------|
| Atomic constitution | Atom | Material | Structure- or result-conformance |
| Molecular aggregation | Molecule | Material | Structure-conformance |
| Compound and mineral | Closed chemical composition | Material | Structure-conformance |
| Pranic cell | Cell with inherent composition-method | Pranic | Seed-conformance |
| Plant body | Organism composed of cells | Pranic | Seed-conformance |
| Animal body | Organism composed of cells | Pranic | Seed-conformance |
| Human body | Developed *medhas* composition | Pranic (expression medium) | Lineage of the body |
| Animal joint form | Animal body with *jeevan* | Animal | Species-conformance |
| Human joint form | Human body with *jeevan* | Knowledge | *Sanskar*-conformance |

The table is this paper's reconstruction of the sequence and the four-order partition. It is not a further completeness threshold numbered after T1. A plant body is a pranic composition; it is not *jeevan*. The animal order comprises animals and birds, excluding humans; the knowledge order comprises only humans (JV, p. 47). An animal or human is a joint form in which the compositional line supplies **that order's** body and the atomic line supplies constitutionally complete *jeevan* (§6). The human joint form is not the next animal. Most atoms remain engaged in physical and chemical constitution rather than attaining T1. Biological compositions return to material constituents after disintegration (MVD, pp. 8, 13; JV, pp. 47–48).

```mermaid
flowchart LR
    subgraph COMPOSITION["Compositional dependency: new closed bearers"]
      direction LR
      ATOM["Atoms"] -->|"closure"| MOL["Molecules"]
      MOL -->|"closure"| COMP["Compounds / minerals"]
      COMP -->|"closure"| CELL["Pranic cells"]
      CELL --> PLANT["Plant body"]
      CELL --> ANBODY["Animal body"]
      CELL --> HUMBODY["Human body"]
    end
    subgraph ATOMIC["Atomic development"]
      direction LR
      DEV["Developing constitution atom"] -->|"irreversible T1"| T1["Jeevan"]
    end
    ANBODY --> ANIMAL["Animal joint form"]
    T1 --> ANIMAL
    HUMBODY --> HUMAN["Human joint form"]
    T1 --> HUMAN
```

The upper arrows express constitutive dependency among bearer types, not one unit changing order. The lower lane is development in an atom. The lanes meet when an animal or human body operates with T1 *jeevan*; there is no transition from the animal joint form to the human joint form.

### 4.4 Nested dependence

Each bearer type supplies a **constitutive condition** for later closure. Molecules require atoms of the relevant kinds; compounds and minerals require molecular constituents; pranic cells require chemical substances, definite heat, and the composition-method of the *prana sutra*. Plant, animal, and human bodies require cells. The animal joint form requires an animal body and T1 *jeevan*; the human joint form requires the developed human bodily medium and T1 *jeevan* (KD 3.2, pp. 58–60; JV, pp. 47–48, 59, 69–70). The human body follows lineage tradition, whereas *jeevan* is not produced by that lineage (JV, p. 59).

Existential progression (*niyati-kram*) is the definite order in which the four orders become manifest on this earth under conducive conditions — material, pranic, animal, and knowledge (MVD, pp. 8, 13). The way of existence (*niyati-vidhi*) is the conformance by which a formed bearer maintains definite conduct. Constitutional completeness is development in the atom; compositional development closes new bearers. The two lines meet in animal and human joint forms without implying that a human is constituted from an animal joint form.

## 5. Coupled units across orders

Bearer types do not occupy separate worlds. Mineral, plant, animal, and human units share one coexistence, recognise and fulfil at the level of their orders, and evidence complementarity in mutuality (SB, pp. 49–53; JV, pp. 43, 69; KD 3.10–3.11, pp. 100–109). The reconstruction therefore uses a dynamic typed relation graph rather than one isolated trajectory. Its vertices are persistent bearers; its edges record actual facings, containment, nourishment, relationship, contact, and body–*jeevan* association. Closure and disintegration can add or remove a containing vertex or edge without creating or destroying its constituent identities.

### 5.1 Many bearers

Let a bounded scenario be a finite subgraph with an explicit environment boundary. Every vertex has a **constitutional kind** — material atom, composition, pranic body, or T1 *jeevan* — and a **manifested order or role** — material, pranic, animal joint form, or knowledge joint form. The two axes prevent T1 *jeevan* from changing constitutional kind when it operates through an animal or human body. A bearer's neighbourhood contains only its actual facings and containing relations, not a mean field over nature. Form is reflected and property becomes effect in those facings (MVD, pp. 47, 49–50; SB, pp. 249–252).

The transition family is typed by the kinds and orders of the bearers that meet, the coupling kind, the essential nature expressed, and the qualitative *guna*-profile. A material unit may integrate or disintegrate; a pranic unit may vitalise or devitalise. A constituent's neighbourhood includes the containing bearer and the parts it actually faces. State-pressure and any excitation-pressure are recorded at the bearer and facing where they are evidenced (§2.5).

### 5.2 Structural relations and modes of fulfilment

Coupling has two dimensions. The first records how bearers are structurally related; the second records what fulfilment is relevant in their facing. Keeping these dimensions separate prevents composition, nourishment, and human relationship from becoming competing members of one list.

| Structural relation | What it records |
|---------------------|-----------------|
| Mutual facing | Bearers recognise and affect one another while retaining their identities. |
| Compositional closure | Complementary constituents close a new bounded bearer such as a molecule or compound. |
| Containment and organisation | A compound, cell, or body organises parts that retain their constitutional kinds and orders. |
| Joint-form association | An animal or human body operates as the medium of T1 *jeevan*. |

| Fulfilment in the facing | Where it appears |
|--------------------------|------------------|
| Structural need and exchange | Particle displacement and absorption; molecular joining; material composition. |
| Nourishment, use, protection, and regeneration | Pranic dependence on material composition and human participation with the first three orders. |
| Species mutuality | Recognition, hope to live, friendliness or opposition, and fulfilment in the animal order. |
| Relationship, contact, and participation | Human–human mutuality in the knowledge order. |

Overfull atoms displace particles and hungry atoms absorb them; atoms also recognise and gather with other atoms to form molecules. Particle exchange and molecular joining are related expressions of complementarity, but not every molecular bond is reduced to a direct hungry–overfull pairing (KD 3.1, pp. 56–58; KD 3.11, pp. 103–104). A coupling may change existing bearers or close a new one.

Pranic units take material compositions as nourishment- and composition-elements under seed-conformance. Animals select and taste through species-conformant bodies. Humans can know, believe, recognise, and fulfil with units of all four orders (JV, pp. 69–70). Knowledge-order use is bounded by right-use, protection, and regeneration; extraction beyond regeneration evidences contradiction in the coupling (MVD, pp. 105, 264; JV, pp. 58, 77).

A **relationship** (*sambandh*) has expectations predetermined in the sense of completeness, while a **contact** or association (*sampark*) has voluntary expectations (MVD, pp. 61–62). These value-bearing forms belong to knowledge-order mutuality. Every case remains an order-typed facing in which each bearer brings its own strength and power.

```mermaid
flowchart LR
    MAT["Material bearer"] ---|"nourishment / composition"| PRAN["Pranic bearer"]
    PRAN ---|"body medium"| ANIM["Animal joint form"]
    PRAN ---|"body medium"| HUM["Human joint form"]
    J["T1 jeevan"] ---|"joint-form association"| ANIM
    J ---|"joint-form association"| HUM
    ANIM ---|"species mutuality"| ANIM
    HUM ---|"relationship / contact"| HUM
    HUM ---|"use · protection · regeneration · misuse"| ANIM
    HUM ---|"right-use / depletion"| PRAN
    HUM ---|"right-use / depletion"| MAT
```

### 5.3 Order-typed interaction

Cross-order coupling does not impose one law on every pair. Essential nature is order-specific and evidenced in a facing rather than stored as a private scalar (MVD, pp. 50–51; SB, p. 179). Two material units meet as integration or disintegration. A composition meets a pranic body as vitalising or devitalising. Animals evidence cruel or non-cruel conduct and species-conformant evaluation. Humans meet as humane or inhumane and participate with the first three orders through use, right-use, protection, regeneration, or misuse.

The transition relation is indexed by source and target kinds and orders, coupling kind κ, essential nature *s*, and *guna*-profile γ. The same profile can accompany different functional characters: generative tendency is not already vitalising, and degenerative tendency is not already cruel. In material, pranic, and animal activity, constitution and conformance make recognition definite. Human R̂ may diverge from *R*<sup>actual</sup>; freedom of action can therefore express either humane or human-opposing *svabhav* in the same objectively established relationship.

Natural-state motion continues under complementary mutuality and mediative regulation; it need not be static. Adverse environment, over-extraction, or human mis-evaluation can condition excitation without changing the unit's *dharma* or constitutional kind. The pressure profile belongs to that actual facing, while the human's recognition of the facing may be correct or mistaken (§2.3, §2.5).

### 5.4 The tetrad of a containing unit

A closed unit that contains others is a further bearer, not a bag of states. In a compound, the participating entities cease to exhibit their respective conducts as the public conduct of the whole and a new conduct appears; in a mixture they remain publicly distinct (MVD, p. 42). The reconstruction assigns a tetrad to the containing bearer while each constituent retains the tetrad of its own kind and order (SB, p. 260). The two-level description is an analytical synthesis; the texts do not supply a formal mereology.

Write *h* for a containing whole and *i* for one of its parts. The relation `part_of(i,h)` is distinct from the external neighbourhood of *h*. The whole carries its own state, strength, *guna*-profile, essential nature, *dharma*, and external facings. Each part retains its kind and order while its neighbourhood includes the whole and the other parts it actually faces.

A constitutive-consistency predicate relates the state of *h*, its parts, and their internal edges. It states that the parts realise and sustain the closed bearer without reducing its conduct to a sum. The whole reciprocally organises which part-couplings are admitted, bounded, nourished, or excited. A closure guard creates `part_of` relations and the new bearer; a disintegration guard removes them while preserving the constituent bearers.

| Aspect of *h* | Reconstructed representation | Consequence |
|---------------|------------------------------|-------------|
| Form (*roop*) | Bounded configuration *r*<sub>h</sub> | Other units meet the whole as one reflected form. |
| Property (*guna*) | Qualitative profile γ<sub>h</sub> | Generative or degenerative part-activity can remain under mediative organisation. |
| Essential nature (*svabhav*) | Order- and coupling-typed transition family | A plant body vitalises or devitalises as that body; a compound integrates or disintegrates as that compound. |
| *Dharma* | Invariant *D*<sub>o(h)</sub> attached to the whole's order | The whole bears the innateness of its order while its parts retain theirs (SB, pp. 60–61, 179). |

A mixture has no containing bearer *h*. A compound, cell, or body does. The animal and human joint forms add an association between a pranic body and T1 *jeevan* without turning either into a part of one fused substance. The body remains a pranic containing unit; *jeevan* remains one sentient atom. The model treats associations among multiple *jeevans* as relations among persistent bearers rather than composition into a larger *jeevan*.

```mermaid
flowchart TB
    PARTS["Parts(h): persistent constituent bearers"] --> CONS["Constitutive consistency"]
    INTERNAL["Internal typed edges"] --> CONS
    CONS --> WHOLE["Containing bearer h<br/>own tetrad and state"]
    WHOLE -->|"organises admitted part-couplings"| PARTS
    WHOLE -->|"one reflected form"| EXTERNAL["External neighbourhood N(h)"]
    GUARD["Closure guard"] --> WHOLE
    WHOLE --> DIS["Disintegration guard"]
    DIS -->|"remove closure; preserve parts"| PARTS
```

### 5.5 A material trace: exchange and restored motion

Consider an overfull atom, a hungry atom, and a displaced particle in mutual facing. Each row describes a complete activity-occurrence; the rows do not divide effort, motion, and result into a sequence within one occurrence.

| Occurrence | Source-level description | Reconstructed reading |
|------------|--------------------------|-----------------------|
| Mutual facing | The atoms meet with definite constitutions and complementary requirements. | Typed edges record actual distance, particle requirement, and operative recognition. |
| Excited activity | The overfull atom becomes excited before displacement; each unit remains forceful and active. | Each bears its own strength and *guna*-profile; Π<sup>state</sup> is present and Π<sup>exc</sup> records the excited facing. |
| Changed configuration | A particle is displaced and may be absorbed, changing the atomic constitutions. | An exchange guard admits the transition and produces new configurational results *r*′. |
| Restored facing | The new constitutions continue in definite natural-state motion. | The next occurrence retains strength, power, property, and mutuality even when excitation-pressure is no longer present. |

If participation closes a compound, the transition additionally creates a containing bearer and `part_of` relations. If it forms a mixture, only the mutual-facing edges change.

## 6. Constitutional completeness and joint forms

The transition from the insentient constitution-oriented atom to the sentient cognitive line is **constitutional completeness** (*gathanpurnata*, T1). It is not a further compositional plateau. When a developing atom achieves complete subatomic particle balance in its nucleus and orbits, particle hunger drops to zero and the atom crosses an irreversible threshold (SB, pp. 55, 61, 92, 144–145; KD 3.3, pp. 60–61). The compositional sequence can already have produced minerals, cells, and bodies; those remain of the order of what constitutes them. Only the atom reaches T1.

### 6.1 The T1 bifurcation and invariant constitution

At constitutional completeness, the atom becomes free of molecular- and weight-bondage and does not return to constitution-oriented status. Its particle constitution no longer undergoes the increase and decrease characteristic of hungry and overfull atoms; its strength and power are described as inexhaustible, and constitutional completeness as the immortality of result (MVD, p. 91; SB, pp. 55, 58, 61, 92; KD 3.3, pp. 61–62).

> **"An evolving-constitution atom is with molecular-bondage and weight-bondage. However, when the contraction and expansion activity increases in this atom, it instantly breaks free from its group and attains constitutional completeness, becoming a jeevan atom. The evidence of constitutional completeness is the jeevan atom's liberation from molecular-bondage and weight-bondage, and its having the hope-bondage."**
> — MVD, p. 91

The model records that invariance as a persistent core *c*<sub>J</sub>: no further particle increase or decrease and no reversal to constitution-oriented status. The primary texts do not formulate T1 in the modern vocabulary of splitting, fusion, or degradation, so those possible physical interpretations remain open rather than being included in the definition. T1 is not repeated when understanding changes; later development concerns *jeevan* activity and awakening while its constitution remains complete (KD, pp. 26–27; KD 3.16, pp. 142–145).

The same sentence that states the two liberations states what T1 adds: **hope-bondage** (*asha-bandhan*). *Jeevan* is not released into indifference. Bound to the hope for happiness, it seeks the continuity of happiness, and that seeking is what drives a body and makes the knowledge-order recursion of §7–§9 run: every human action carries the hope for happiness within it, and the evaluation of results against that hope is where delusion persists or awakening begins (MVD, p. 91; KD, pp. 1–4). Hope-bondage is therefore the sentient counterpart of the structural bondages it replaces — an orientation borne in the constitution of *jeevan*, not a physical constraint on a trajectory.

### 6.2 Pranic bodies as living media

The pranic order requires more than a plateau label. A pranic cell bears an inherent composition-method associated with the *prana sutra*; under conducive material, nourishment, heat, and environmental conditions, cells form bodies that respire, take nourishment, grow, reproduce, decline, and disintegrate according to seed-conformance (KD 3.2, pp. 58–60; JV, pp. 47–48). A plant body remains pranic. Animal and human bodies are likewise pranic compositions before association with *jeevan* and continue to maintain bodily integrity through material and pranic activity while alive.

The model therefore gives every pranic body a seed or lineage pattern, a nourishment relation, a respiration condition, a growth condition, and a bodily-integrity predicate. Growth and reproduction are guarded closure transitions; decline and death remove the body's organising closure and return its constituents to material couplings. These are qualitative types, not a biochemical growth law.

### 6.3 The animal joint form

The animal and knowledge orders are joint forms of a pranic body and constitutionally complete *jeevan* (SB, p. 55). In an animal joint form, *jeevan* expresses the hope to live through species-conformance. Evaluation appears as recognition of essential nature, including friendliness and opposition, together with animal tasting, selection, sensitivity, and bodily fulfilment (SB, p. 249; JV, pp. 49, 69–70). This sentient evaluation is definite through species-conformance; it does not include the specifically human circuit of knowing, believing, evaluation through justice–*dharma*–truth, or refinement through realised knowledge.

```mermaid
flowchart LR
    AB["Pranic animal body"] --> JOINT["Animal joint form"]
    J["T1 jeevan"] --> JOINT
    ACTUAL["Actual facing"] --> REC["Species-conformant recognition<br/>friendliness or opposition"]
    JOINT --> REC
    REC --> SELECT["Tasting, selection and body-mediated activity"]
    SELECT --> CONSEQ["Bodily and relational consequence"]
    CONSEQ -->|"next actual facing"| ACTUAL
```

The consequence of one animal activity alters the bodily and relational situation of the next. The reconstruction does not infer a human-style *sanskar* revision operator or a quantitative animal-learning law from this recurrence.

### 6.4 The human joint form and its interface

The human body remains a pranic bearer while T1 *jeevan* operates through it. The interface is bidirectional. Sensory and bodily conditions are presented to *jeevan*; selection, imaging, analysis, resolve, and evidence are expressed through the body. Bodily activity does not become knowledge, and refinement in *jeevan* does not reconstruct its invariant constitution (KD 3.16, pp. 141–145; JV, pp. 47–49, 59).

```mermaid
flowchart LR
    WORLD["Actual relational and natural situation"] --> BODY["Pranic human body"]
    BODY -->|"sensory / bodily presentation"| J["T1 jeevan<br/>refinable orientation"]
    J -->|"selection · resolve · expression"| BODY
    BODY --> CONSEQ["Internal, bodily, relational and natural consequences"]
    CONSEQ --> WORLD
    CONSEQ --> EVAL["Later reflexive evaluation by jeevan"]
    EVAL --> J
```

Every body and *jeevan* activity remains effort–motion–result. Animal evaluation and human reflexive evaluation relate complete sentient activities to their situations; neither is a fourth member of the triad. This paper models a joint form across one bodily span. Persistence of *jeevan* and *sanskar* across bodies is treated in [*Death, Continuity, and Rebirth*](../Death-Continuity-And-Rebirth/Death-Continuity-And-Rebirth.pdf).

## 7. Knowledge and the internal configuration of *jeevan*

The opening passages name an omnipresent ground of Knowledge or Omnipotence in which insentient and sentient nature are contained, while the later epistemic account names the content realised by *jeevan*. This paper keeps those uses distinct. *Jeevan* is the knower; its determinate content comprises the holistic view of coexistence, knowledge of *jeevan*, and knowledge of humane conduct. Participation in undivided society and universal orderliness is its purpose and evidence (KD, pp. 3–4; KD 3.17, pp. 145–148). The content is not made variable by one person's ignorance, but its study, enlightenment, realisation, and evidence can remain incomplete.

The human joint state is written [*x*<sub>B</sub>, *c*<sub>J</sub>, *z*<sub>H</sub>] in Appendix A: the pranic body, invariant T1 core, and refinable human orientation. The brackets record a coupled unit of analysis without making body and *jeevan* one substance. Orientation *z*<sub>H</sub> contains a faculty profile, present *sanskar*, qualitative knowledge profile, evaluation references, and operative recognition.

### 7.1 Five state-motion pairs

The five faculties each have an activity in state, expressed as strength, and a paired activity in motion, expressed as power. In awakened activity, realisation is evidenced outward through these pairs (KD 3.6, pp. 71–72; KD 3.16, p. 145; MVD, p. 78; JV, pp. 92–94).

| Faculty | State / strength activity | Motion / power activity |
|---------|---------------------------|-------------------------|
| *Atma* | Realisation (*anubhav*) | Evidence or authentication (*pramanyata*) |
| *Buddhi* | Enlightenment (*bodh*) | Resolve (*sankalp*) |
| *Chitta* | Contemplation (*chintan*) | Imaging or visualisation (*chitran*) |
| *Vritti* | Comparison or weighing (*tulana*) | Analysis (*vishleshan*) |
| *Mun* | Tasting (*asvadan*) | Selection (*chayan*) |

Each row gives paired descriptions of the forceful and projective sides of *jeevan* activity. State and motion remain indivisible as realisation and evidence, enlightenment and resolve, contemplation and imaging, comparison and analysis, and tasting and selection. A developed human body provides the medium through which all ten can be evidenced; in delusion, their full exercise remains unavailable (KD 3.16–3.17, pp. 145–147; JV, pp. 92–94).

### 7.2 Realised knowledge as orientation

Let *K*<sup>*</sup> denote the determinate content — coexistence, *jeevan*, and humane conduct. A qualitative profile *k*<sub>H</sub> records which parts have been studied, enlightened in *buddhi*, realised in *atma*, and made available as evidence. It is not a scalar degree. Enlightenment is the culmination of study, and realisation follows that enlightenment; realised content is projected through resolve, imaging, analysis, and selection (MVD, p. 100; KD 3.6, pp. 71–72; KD 3.12, p. 112; KD 3.17, pp. 145–148). No transition rule makes study automatically produce enlightenment or realisation.

### 7.3 Initial *sanskar* and deluded evaluation

Every human acts from present acceptance. Environment, study, and *sanskar* contribute to the orientation from which thought and conduct are expressed, while the body provides the sensory and motor medium (KD, pp. 6–9; KD 3.16, pp. 141–145). The faculty, knowledge, acceptance, evaluation, and recognition fields of *z*<sub>H</sub> are qualitative predicates rather than neurological measurements.

In delusion (*bhram*), identification of *jeevan* with the body leaves the upper activities unevidenced and organises comparison from sensory input. Of the ten activities, only four and a half are then effective — selection, tasting, analysis, imaging, and half of comparison — while pleasure, health, and profit become its prevailing perspectives (MVD, pp. 58, 78, 80–81; SB, pp. 91–92; JV, pp. 73–74, 93–94, 97–98). Human *dharma* remains happiness; the error lies in what is accepted as its fulfilment. Freedom of action leaves both human-opposing and humane expression possible.

### 7.4 Knowing, believing, recognising, and fulfilling

Human evidence joins four distinguishable aspects: knowing and believing organise the internal orientation; recognising relates that orientation to actual mutuality; fulfilling becomes bodily and public conduct (JV, pp. 69–70). Their agreement cannot be assumed. A person may know a proposition verbally yet misrecognise a relationship, or recognise a responsibility yet fail to fulfil it. The model therefore records a qualitative KBRF profile rather than treating knowledge as possession of information.

Study enters through typed human–human relations involving teacher, learner, language, tradition, projection, and reflection. These relations can present content for attention and evaluation, while understanding and realisation remain activities of the learner's *jeevan*. Knowledge is neither copied as a state variable nor transmitted as energy. This representation supplies an explicit route by which study can alter the material available to later reflection without predetermining awakening.

## 8. Human effort-motion-result and internal refinement

The universal triad applies to *jeevan*. Human activity differs because its orientation includes acceptance, knowledge profile, operative recognition, and evaluation references. These qualify expression through faculties and body while constitutional capacity remains invariant.

### 8.1 The knowledge-mediated tetrad

Human *dharma* *D*<sub>H</sub> remains happiness through resolution and participation in orderliness. The qualitative predicate `ComprehendsDharma(H,n)` records its present comprehension and evidence. Present *sanskar*, knowledge profile, operative recognition, and freedom of action condition the humane or human-opposing *svabhav* and *guna*-profile expressed in conduct. Human-opposing expression can be transformed toward fortitude, valour, generosity, kindness, grace, and compassion, while awakened conduct becomes mediative (KD, pp. 26–27; KD 3.9–3.10, pp. 98–101).

The invariant constitutional capacity *C*<sub>J</sub> is distinguished from its current expression *B*<sub>H,n</sub>. Power appears in selection, analysis, imaging, resolve, evidence, and body-mediated conduct. Knowledge does not replace *bal–shakti*; it qualifies its knowledge-order expression through understood purpose. The T1 core *c*<sub>J</sub> remains invariant throughout refinement.

### 8.2 Result in the knowledge order

Every human action carries the hope for happiness and yields a coupled consequence profile. The body is the medium of outward expression, while acceptance and evaluation occur in *jeevan* (KD, pp. 1–4, 26–27; KD 3.16, pp. 142–145). The model distinguishes configurational *parinam* *r* from the following consequences *Y*:

| Result aspect | What changes |
|---------------|--------------|
| Internal | The alignment and operative orientation of *atma, buddhi, chitta, vritti,* and *mun* |
| Bodily | Speech, bodily action, production, use, and the body's physical condition |
| Relational | Recognition, value-fulfilment, trust, satisfaction, or contradiction in human mutuality |
| Natural | Nourishment, right-use, protection, regeneration, imbalance, or depletion in couplings with the other orders |

The four aspects form one consequence profile; the sources do not assign the internal aspect exclusive priority. For the narrower question of how one activity conditions another, its internal consequence can be carried in *z*<sub>H</sub>, while bodily, relational, and natural states are updated in the actual graph. Results expressed through the body prompt further thought and reflection; thought arising from action can be settled again as conception through inference (KD, p. 3; KD 3.17, p. 147; MVD, p. 218).

### 8.3 Evaluation links successive activities

One consequence can become the object of a later complete activity of tasting, comparison, contemplation, enlightenment, or realisation. The model relates the consequence profile, its observation from the present standpoint, and an admissible orientation update. Evaluation itself remains effort–motion–result.

In delusion, pleasure, health, and profit organise evaluation. In humane consciousness, justice, *dharma*, and truth supply the reference points. Justice becomes evident when a relationship is recognised, its values are fulfilled, that fulfilment is evaluated, and mutual satisfaction results (JV, pp. 97–98, 137–139). Because the actual relationship and the human's operative recognition are separate fields, the model can represent error and correction without changing the relationship that was objectively present.

An update can preserve an acceptance, correct recognition, refine evaluation, or stabilise realised *sanskar*. Realisation-oriented conceptions in *buddhi* manifest in thought and action; thought arising from action is settled again as conception through inference (MVD, p. 218). Completed humane *sanskar* is understanding, honesty, responsibility, and participation (JV, p. 49). The update relation is non-deterministic: repetition does not turn error into knowledge, and one corrected act does not establish completeness.

### 8.4 Dissatisfaction, recurrence, and inquiry

The non-attainment of *jeevan* values is experienced as dissatisfaction or internal contradiction. Deluded sensory living leaves the human dissatisfied, while satisfaction becomes possible through understanding (JV, p. 76). The model records this as a qualitative predicate, not a measured error, excitation-pressure, or force applied to *jeevan*.

If the same acceptance and pleasure–health–profit references organise the next activity, the pattern can recur. If contradiction is recognised as a need for understanding, inquiry and study can begin. Study may open enlightenment; enlightenment may become realisation; realised orientation reorganises comparison, contemplation, selection, and conduct through justice, *dharma*, and truth (MVD, p. 100; KD, pp. 1–4; KD 3.6, pp. 71–72; KD 3.12, p. 112; KD 3.17, pp. 147–148). Dissatisfaction does not mechanically force this branch because freedom of action remains.

### 8.5 A human trace: one consequence, two evaluations

Suppose a person accepts responsibility in a recognised relationship but abandons it for immediate profit. This analytical example illustrates the transition schema rather than a case narrated in the primary texts.

| Moment | Activity and consequence | Reconstructed reading |
|--------|--------------------------|-----------------------|
| Present orientation | Profit organises comparison; the responsibility is recognised but not fulfilled. | *z*<sub>H,n</sub>, R̂<sub>H,n</sub>, and *q*<sub>H,n</sub> condition the expressed activity. |
| Consequence | The act produces internal contradiction, a work consequence, and diminished relational trust or satisfaction. | *Y*<sub>H,n</sub> updates internal, bodily, relational, and natural fields. |
| Recurrent evaluation | Profit remains decisive and the act is justified. | The update preserves the prior evaluation profile; dissatisfaction may recur. |
| Inquiry-oriented evaluation | Non-fulfilment is recognised as a question of relationship, value, and justice. | Study and reflection may correct R̂ and refine accepted conception. |
| Later evidence | Responsibility is fulfilled and assessed through mutual satisfaction. | Changed orientation becomes publicly testable; one act alone does not establish T2 or T3. |

The trace makes the distinction between dissatisfaction and excitation-pressure concrete. The former is a sentient consequence of unresolved value or orientation; the latter belongs to an excited force–power relation.

## 9. *Jeevan* values and completeness

The destination of this refinement is harmony within *jeevan*. Happiness, peace, contentment, and bliss are names for harmony among adjacent faculties, while realisation in coexistence at *atma* is ultimate bliss. The effect of realised *atma* reaches the remaining faculties as a nested order (MVD, pp. 100–101; JV, pp. 60, 137–138; KD 3.6, pp. 71–72).

### 9.1 Nested internal harmony

| Site of harmony | Evidence in *jeevan* |
|-----------------|----------------------|
| *Atma* realised in coexistence | Ultimate bliss (*paramanand*) |
| *Buddhi–atma* | Bliss (*anand*) |
| *Chitta–buddhi* | Contentment (*santosh*) |
| *Vritti–chitta* | Peace (*shanti*) |
| *Mun–vritti* | Happiness (*sukh*) |

The model records a qualitative harmony profile drawn from *sukh, shanti, santosh, anand,* and *paramanand*. These are nested relations among faculties, not interchangeable magnitudes. Realisation is accepted in *buddhi*, contemplated in *chitta*, compared in *vritti*, and tasted in *mun*. The internal harmonies differ from the established relational values of §10.1 while supplying the orientation from which relational conduct can remain stable (JV, pp. 137–139).

### 9.2 Activity completeness (T2 - *kriyapurnata*)

Activity completeness is the restfulness of effort (*shram ka vishram*) in realised activity (SB, p. 58; MVD, p. 103; KD 3.6, pp. 71–72). The model proposes four mutually supporting criteria: realisation of *K*<sup>*</sup>, all ten activities effective, full internal harmony, and restfulness of effort. Their conjunction is an operational reconstruction rather than an exact equivalence stated in one passage. Absence of reported dissatisfaction may accompany T2 but is not sufficient to define it.

### 9.3 Conduct completeness (T3 - *acharanpurnata*)

Conduct completeness is the lived evidence of T2 through humane conduct (*manaviya acharan*) and is named the destination of motion (*gati ka gantavya*). Humane conduct integrates character (*charitra*), ethics (*niti*), and values (*mulya*). Character is evidenced through rightfully owned wealth, marital faithfulness, and kindness in action. Ethics directs body, mind, and wealth toward right-use and protection; values are recognised and fulfilled in relationship (MVD, pp. 80, 101, 103; SB, p. 58; JV, pp. 54–55; KD, p. 67). The model treats T3 as T2 together with stable humane conduct across a relevant diversity of relationship and work contexts. “Stable” is qualitative and sustained, not a universal duration supplied by the sources.

## 10. Verification in relationship, work, and society

Madhyasth Darshan seeks harmony and integrality across the human dimensions of work, behaviour, thought, and realisation (MVD, p. 18). These domains test different effects of one orientation without reducing them to a numerical score or allowing private assertion to substitute for conduct.

### 10.1 Relationship, value, and mutual satisfaction

Human–human justice follows a definite relational sequence: actual relationship and role are present; the person operatively recognises them; inherent values are recognised and fulfilled; fulfilment is evaluated; mutual satisfaction becomes evidence (JV, pp. 97–98, 137–139). Trust, respect, affection, gratitude, and the remaining values belong to relationship, while satisfaction or dissatisfaction is the experienced consequence of their fulfilment or non-fulfilment. Separating *R*<sup>actual</sup> from R̂ makes both misrecognition and correction explicit.

### 10.2 Fourfold verification and work with *jada*

The reconstruction assigns each domain one of four statuses: supported, contradicted, undetermined, or not assessed. It does not aggregate them. Knowledge-based conduct is examined across four qualitative domains:

| Domain | Evidence and access |
|--------|---------------------|
| Thought | Deliberation organised through justice, *dharma*, and truth; accessible through first-person report and coherent expression |
| Behaviour | Actual relationship, operative recognition, value-fulfilment, contradiction, evaluation, and mutual satisfaction; jointly assessed by those involved |
| Work | Law (*niyam*), regulation (*niyantran*), balance (*santulan*), protection, right-use, regeneration, or depletion; publicly and sometimes instrumentally accessible |
| Realisation | First-person realisation in coexistence and its coherent evidence through the remaining faculties; not directly reducible to an external measurement |

Material and pranic bearers continue through their order-typed activity; animal *jeevan* retains species-conformant evaluation; human evaluation governs selection, work, use, and restraint. Education and *sanskar* concern law, regulation, balance, and justice; natural use is bounded by right-use, protection, and expenditure in proportion to regeneration (JV, pp. 58, 138–139; MVD, p. 264). Exploitation in relationship or depletion in work contradicts a present claim of complete public evidence even when inner realisation is asserted.

### 10.3 Undivided society

The primary texts link the human goals as resolved individual, prosperous family, fearless society, and universal coexistence (JV, pp. 60–61; SB, pp. 246–247):

**Resolved individual → prosperous family → fearless society → universal coexistence**

Resolution is lived as happiness, prosperity supports peace in family, fearlessness supports contentment in social order, and understanding is evidenced as bliss in participation (JV, pp. 60–61). The present formal model stops at individual and relational traces. Deriving the social chain would require family resource states, relationship networks, institutions, production–regeneration relations, and population-level participation. Until those modules are supplied, the chain remains a source-stated direction of evidence rather than a theorem of the reconstruction.

## 11. Open problems

### 11.1 Identifying T1

T1 remains a metaphysical and textual threshold without an accepted counterpart in contemporary physics. The sources state freedom from molecular- and weight-bondage, constitutional invariance, inexhaustible strength and power, and hope-bondage. They do not supply a laboratory guard, measured particle count, or observation protocol by which a developing atom could be identified as *jeevan*. The model therefore marks T1's postconditions while leaving its empirical detection undetermined.

### 11.2 Quantitative calibration

Strength, *guna*-profile, essential nature, actual mutuality, operative recognition, state-pressure, excitation-pressure, harmony, and verification are qualitative types or predicates. The sources provide no common scale, interaction kernel, potential, probability, or learning rate. Order-specific empirical submodels may eventually refine selected material or pranic transitions, but no one metric can be assumed to span atoms, bodies, values, and realisation.

### 11.3 Boundaries of a containing bearer

The distinction between mixture and compound supports the idea of new public conduct, while the persistence of constituent order supports a two-level account. The sources do not provide necessary and sufficient criteria for every compound, organism, ecosystem, institution, or other proposed whole. The constitutive-consistency predicate therefore remains a model placeholder whose application must be justified bearer by bearer.

### 11.4 Animal sentience and evaluation

Animal recognition of essential nature, friendliness, opposition, tasting, selection, and hope to live are textually stated. Their relation to learning, memory, species variation, and contemporary animal cognition remains under-specified. The present animal module distinguishes species-conformant evaluation from human reflexive evaluation but does not reduce either to behavioural conditioning.

### 11.5 The body–*jeevan* interface

The joint-form account requires bodily presentation to *jeevan* and sentient expression through the body. The sources name the faculties and bodily medium but do not provide a physical transfer mechanism or empirical interface variable. The two directed interface relations in Appendix A preserve the distinction without explaining its physical implementation.

### 11.6 Evidence and counterevidence

First-person realisation, mutual satisfaction, repeatable conduct, work with nature, instrument-based observation, and textual fidelity provide different access. No single observation proves all layers. The model can record support, contradiction, or indeterminacy, but robust criteria for counterevidence—especially for T1, T2, and claims of realisation—require further philosophical and empirical work.

### 11.7 Social-scale dynamics

The four human goals require family, resource, trust, production, institution, and relationship-network states. The present reconstruction supplies individual and relational traces but not a population model. A future extension must preserve persons as agents and relationships as value-bearing relations rather than deriving society from an aggregate satisfaction score.

### 11.8 Relation to contemporary science

Typed closure, pranic growth, animal sentience, and human cognition can be compared with chemistry, biology, neuroscience, and social science without treating the vocabularies as already equivalent. Mapping the darshan's atom, *prana sutra*, T1 *jeevan*, faculties, and completeness stages to contemporary entities remains a comparative research programme rather than an achievement of the present formalism.

## Appendix A. A typed qualitative hybrid model

### A.1 Reading the formalism

This appendix is a qualitative reconstruction, not a mathematical form found in the primary texts. It keeps different kinds of bearer, activity, relation, transition, and evidence from being collapsed into one equation. The symbols carry types and logical relations but no numerical metric, probability, force law, learning algorithm, or proof of the darshan.

The model is **hybrid** in a limited sense. Activity may continue over a duration within a stable bearer kind. Composition, disintegration, constitutional completeness, body–*jeevan* association, and changes in accepted conception are guarded transitions between complete activity-occurrences. An occurrence index *n* distinguishes such occurrences; Δ*t*<sub>n</sub> records the duration considered. Neither is an ontological container in which existence is placed.

Effort, motion, and result remain simultaneous aspects of every unit-activity. A transition relates one complete occurrence to another; it does not put effort, motion, and result in temporal sequence within one occurrence. An evaluative occurrence is likewise a complete sentient activity rather than a fourth member of the triad.

Actual mutuality can condition which activity is expressed, and environmental pressure can condition excitation. Pressure remains an expression of unit force–power in mutuality rather than an independent energy reservoir.
### A.2 Ontological types and standing invariants

Let $\mathbb{S}$ denote state-complete Omnipresence (*satta*), and let $i,j,c,b$, and $h$ denote bounded bearers or analytical joint-form handles. Two type axes remain distinct:

| Type axis | Symbol | Values used here |
|-----------|--------|------------------|
| Constitutional kind | $\kappa_i$ | Developing atom, T1 *jeevan*, molecule, compound or mineral, pranic cell, pranic body, joint-form handle |
| Manifested order or role | $o_i$ | Material $M$, pranic $P$, animal $A$, knowledge $K$, or unjoined sentient $J$ |

T1 *jeevan* retains its constitutional kind whether associated with an animal body, a human body, or no body in the bounded situation. Animal and knowledge order name joint-form roles rather than different constitutions of *jeevan*. A joint-form handle refers to the coupled body–*jeevan* unit of analysis without introducing a third substance.

The standing constraints are

$$
\operatorname{StateComplete}(\mathbb{S}),
\qquad
\mathbb{S}\notin U_n,
$$

$$
\forall i\in U_n:
\operatorname{Bounded}(i)
\land
\operatorname{Saturated}(i,\mathbb{S}).
$$

No transition changes $\mathbb{S}$, assigns motion or pressure to it, or treats saturation as an applied input. Every bearer has persistent identity $\operatorname{id}(i)$. Composition activates a containing bearer without annihilating its constituents. Disintegration deactivates that closure while constituent identities continue. T1 preserves atomic identity while irreversibly changing constitutional kind.

The order-specific *dharma* and its fulfilment are separate:

$$
D_i=D_{o_i},
\qquad
\operatorname{FulfilsDharma}(i,n)
\in
\{\mathrm{true},\mathrm{false},\mathrm{undetermined}\}.
$$

Human *dharma* can remain happiness while an occurrence fails to fulfil it. $D_i$ is neither an applied force nor an instruction determining the next state.

### A.3 A bounded situation as a dynamic typed graph

A bounded situation at occurrence $n$ is

$$
\mathcal{Q}_n=
\left(
U_n,\,
x_n,\,
E_n,\,
\prec_n,\,
\bowtie_n,\,
\partial U_n
\right).
$$

Here $U_n$ is the finite set of bearers selected for the scenario; $x_n$ assigns each one a typed state; $E_n$ is a directed typed multigraph of actual mutualities; $i\prec_n c$ means that $i$ is a constituent of containing bearer $c$; $j\bowtie_n b$ is a body–*jeevan* association; and $\partial U_n$ records relevant edges to bearers outside the local selection. The finite boundary is analytical and does not imply isolation.

The edge kinds are

$$
\mathsf{EdgeKind}=
\left\{
\begin{array}{l}
\text{mutual facing},\;
\text{complementary need},\;
\text{organisation},\\
\text{nourishment or use},\;
\text{relationship},\;
\text{contact},\\
\text{teaching or study},\;
\text{body--jeevan association}
\end{array}
\right\}.
$$

An actual edge is $e=(i,j,\lambda_e,\rho^{\mathrm{actual}}_{e,n})$, where $\lambda_e$ is its kind and $\rho^{\mathrm{actual}}_{e,n}$ records the relevant facing, distance, role, complementarity, containment, nourishment, use, expectation, or other order-typed condition. No scalar is assumed.

### A.4 State, activity, result, and consequence

The full model state of a bearer is

$$
x_{i,n}=(\phi_{i,n},\chi_{i,n}),
$$

where $\phi_i$ is bounded form or configuration and $\chi_i$ is the order-specific internal condition. Examples of $\chi_i$ include atomic constitution, bondages, seed-pattern, respiration and growth condition, and sentient orientation. The fields remain qualitative unless a separate empirical submodel supplies measurements.

One complete unit-activity is

$$
\alpha_{i,n}
=
\left\langle
B_{i,n},\,
S_{i,n},\,
P_{i,n}
\right\rangle ,
$$

where $B$ is effort or strength borne in state, $S$ is motion or power in expression, and $P$ is the presently realised configurational *parinam*. They are co-present in the typed admissibility relation

$$
\operatorname{Act}_{\kappa_i,o_i}
\left(
x_{i,n},\,
R^{\mathrm{actual}}_{i,n},\,
\widehat R_{i,n},\,
D_i,\,
s_{i,n},\,
\Gamma_{i,n};\,
\alpha_{i,n}
\right).
$$

Here $s_{i,n}$ is essential nature evidenced in the facing, and

$$
\Gamma_{i,n}
\in
\mathcal{G}_{o_i}
\subseteq
2^{\{\textit{sam},\textit{visam},\textit{madhyastha}\}}
\setminus\{\varnothing\}
$$

is the expressed *guna*-profile. Set notation permits mediative regulation to remain present with a generative or degenerative tendency; it does not assign numerical weights. $\operatorname{Act}$ is an admissibility schema rather than a deterministic vector field. It states that state, strength, motion, result, *dharma*, essential nature, property, and mutuality form one order-compatible activity-whole.

Recurrence between complete occurrences is written

$$
\left(
\mathcal{Q}_n,\,
\{\alpha_{i,n}\}_{i\in U_n}
\right)
\xRightarrow[\lambda_n]{\Delta t_n}
\mathcal{Q}_{n+1}.
$$

The transition label identifies continuity or guarded change; it does not order the members of $\alpha$.

Configurational *parinam* remains distinct from human consequence:

$$
Y_{H,n}
=
\left(
Y^{\mathrm{internal}}_n,\,
Y^{\mathrm{bodily}}_n,\,
Y^{\mathrm{relational}}_n,\,
Y^{\mathrm{natural}}_n
\right).
$$

Consequences may become content for later evaluation without redefining *roop*.

### A.5 Actual mutuality and operative recognition

For bearer $i$,

$$
R^{\mathrm{actual}}_{i,n}
=
\left\{
\rho^{\mathrm{actual}}_{e,n}:
e\in E_n
\text{ and }e\text{ is incident on }i
\right\},
$$

while operative recognition is

$$
\widehat R_{i,n}
\in
\operatorname{Recognise}_{\kappa_i,o_i}
\left(
x_{i,n},R^{\mathrm{actual}}_{i,n}
\right).
$$

Material and pranic recognition is definite according to constitution or seed. Animal recognition and evaluation are definite according to species-conformance. In the human, $\widehat R_H$ may agree with or diverge from $R^{\mathrm{actual}}_H$. Action proceeds from operative recognition while bodily, relational, and natural consequences occur in actual mutuality. This distinction makes misrecognition, correction, justice, and mutual satisfaction representable.

A human relationship edge may carry role, inherent values, fulfilled values, and mutual-satisfaction status. A contact edge instead carries voluntary expectations. They remain different edge kinds even when joining the same people.

### A.6 The two pressure descriptions

State-pressure is the received recognition of a force-bearing unit in mutuality:

$$
\operatorname{Pr}^{\mathrm{state}}_{j\to i,n}
\in
\operatorname{ReceiveForce}
\left(
B_{j,n},
\rho^{\mathrm{actual}}_{e,n}
\right).
$$

Excitation-pressure is the narrower predicate

$$
\Pi^{\mathrm{exc}}_{j\to i,n}
\Longleftrightarrow
\operatorname{Excited}(e,n)
\land
\left(
\Gamma_{e,n}
\cap
\{\textit{sam},\textit{visam}\}
\neq\varnothing
\right).
$$

The actual relational condition may guard or condition a transition. Both descriptions name how unit force–power is encountered; neither is a separate energy source or applied force from *satta*. An unfulfilled human relation does not by itself satisfy the physical excitation predicate.
### A.7 Containing units and closure

For containing bearer $c$,

$$
\operatorname{Parts}_n(c)
=
\{i\in U_n:i\prec_n c\},
$$

while its external neighbourhood is

$$
N^{\mathrm{ext}}_n(c)
=
\{j:(c,j,\lambda,\rho)\in E_n
\text{ and }j\not\prec_n c\}.
$$

A containing state is admitted only when whole and constituents satisfy an order-typed closure constraint:

$$
\operatorname{Closed}_{\kappa_c,o_c}
\left(
x_{c,n},\,
\{x_{i,n}:i\in\operatorname{Parts}_n(c)\},\,
E^{\mathrm{internal}}_n(c)
\right).
$$

The constraint does not define $x_c$ as a sum. It states that a new bounded conduct is realised by definite internal organisation. The containing bearer has its own tetrad and activity, while each constituent retains identity, kind, order, and activity. The whole organises constituent couplings; constituent continuity remains constitutively relevant to the whole.

A mixture adds facing edges among existing bearers without activating a containing bearer. A compound, cell, or body activates a new $c$ and part relations. Disintegration removes those containing relations and deactivates $c$ while constituent identities continue.

### A.8 Guarded transition kinds

A transition of kind $\lambda$ is admissible only when

$$
\operatorname{Guard}_{\lambda}(\mathcal{Q}_n)
\land
\operatorname{Transition}_{\lambda}
(\mathcal{Q}_n,\mathcal{Q}_{n+1}).
$$

| Transition | What changes | Identity and order constraint |
|------------|--------------|-------------------------------|
| Continuing activity | Configuration and actual facings within an established kind | Same bearer; no order conversion |
| Atomic exchange | Particle constitution, hunger or overfullness, and relevant couplings | Developing atom identities persist |
| Mixture formation or separation | Actual facing edges | No containing bearer |
| Compositional closure | Compound, cell, or body and part relations become active | New containing bearer; constituents retain identity and order |
| Disintegration | A containing bearer and its part relations cease | Constituents continue in lower-level couplings |
| Pranic growth or reproduction | Seed-conformant cells or bodies close, grow, or reproduce | The resulting body remains pranic |
| T1 constitutional completeness | A developing atom becomes constitutionally complete *jeevan* | Same atomic identity; irreversible constitutional change |
| Body–*jeevan* association or separation | The joint relation becomes active or ceases | Body and *jeevan* remain distinct |
| Animal evaluation | Species-conformant recognition of essential nature and bodily response | No human knowing–believing or justice criterion is inferred |
| Human evaluation and refinement | Operative recognition, conception, evaluation profile, or *sanskar* changes | T1 core and human *dharma* remain invariant |

No transition receives a probability. Dissatisfaction does not force inquiry, study does not mechanically force realisation, and individual change does not automatically establish a social theorem.
### A.9 The four order modules

| Order or role | Typed state emphasis | Conformance and distinctive activity |
|---------------|----------------------|--------------------------------------|
| Material | Form, constitution, bondages, hunger or overfullness, composition | Structure-conformance; exchange, integration, disintegration, mediative regulation |
| Pranic | Material composition, seed or *prana-sutra* pattern, respiration, reproduction, nourishment, growth, bodily integrity | Seed-conformance; growth, nourishment, reproduction, decline and return to material constituents |
| Animal joint form | Pranic animal body, invariant T1 core, species-conditioned sentient orientation | Species-conformance; hope to live, sensitivity, tasting, selection, friendliness/opposition and evaluation |
| Human joint form | Pranic human body, invariant T1 core, refinable knowledge-order orientation | *Sanskar*-conformance; knowing, believing, recognising, fulfilling, reflexive evaluation and possible refinement |

The animal and human joint states are

$$
x_{A,n}
=
\left[
x_{B_A,n},c_J,z_{A,n}
\right],
\qquad
x_{H,n}
=
\left[
x_{B_H,n},c_J,z_{H,n}
\right].
$$

The brackets describe coupled states of analysis, not fusion or three substances. $z_A$ records species-conformant hope, sensitivity, operative recognition, evaluation, tasting, and selection. No human *sanskar*-revision law is assigned to it.

### A.10 T1 and the body–*jeevan* interface

For developing atom $j$, T1 is the guarded event

$$
\begin{aligned}
&\kappa^-_j=\text{developing atom},
\qquad
\operatorname{Guard}_{T1}(x^-_j),\\
&\kappa^+_j=\text{T1 jeevan},
\qquad
\operatorname{id}(j^+)=\operatorname{id}(j^-).
\end{aligned}
$$

Its stated postconditions are

$$
\neg\operatorname{MolecularBondage}(j),
\qquad
\neg\operatorname{WeightBondage}(j),
$$

$$
\operatorname{ConstitutionInvariant}(c_J),
\qquad
\operatorname{HopeForHappiness}(j).
$$

The sources supply these qualitative postconditions but no empirically accepted guard.

For joint-form handle $h$,

$$
\operatorname{Joint}_n(h;j,b)
\Longleftrightarrow
j\bowtie_n b
\land
\operatorname{Components}(h)=\{j,b\}.
$$

The interface has two typed directions:

$$
u^{B\to J}_n
\in
\operatorname{BodilyPresentation}
\left(
x_{B,n},
R^{\mathrm{actual}}_{H,n}
\right),
$$

$$
u^{J\to B}_n
\in
\operatorname{JeevanExpression}
\left(
z_{J,n},
\widehat R_{J,n}
\right).
$$

The first records sensory and bodily presentation to *jeevan*. The second records selection, resolve, and sentient expression through the body. They condition complete activities without converting bodily motion into knowledge or transferring external energy into *jeevan*.

Body-mediated expression updates coupled states:

$$
\left(
x_{B,n+1},
Y^{\mathrm{bodily}}_n,
Y^{\mathrm{relational}}_n,
Y^{\mathrm{natural}}_n
\right)
\in
\operatorname{ExpressThroughBody}
\left(
x_{B,n},
u^{J\to B}_n,
R^{\mathrm{actual}}_{H,n}
\right).
$$

### A.11 Human knowledge and orientation

The determinate knowledge-content remains fixed:

$$
K^{*}
=
\left\{
K_{\mathrm{coexistence}},
K_{\mathrm{jeevan}},
K_{\mathrm{humane\ conduct}}
\right\}.
$$

Human orientation is

$$
z_{H,n}
=
\left(
f_{H,n},
\sigma_{H,n},
k_{H,n},
q_{H,n},
\widehat R_{H,n}
\right).
$$

Here $f_H$ is the qualitative faculty and effective-activity profile; $\sigma_H$ is present acceptance and *sanskar*-orientation; $k_H$ is a qualitative knowledge profile; $q_H$ is the evaluation-reference profile; and $\widehat R_H$ is operative recognition. Each symbol has one role, so *sanskar* is no longer duplicated inside and outside the orientation state.

The knowledge profile is

$$
k_H=
\left(
k^{\mathrm{studied}},
k^{\mathrm{bodh}},
k^{\mathrm{anubhav}},
k^{\mathrm{evidence}}
\right),
$$

with the source-aligned dependency

$$
k^{\mathrm{evidence}}
\subseteq
k^{\mathrm{anubhav}}
\subseteq
k^{\mathrm{bodh}}
\subseteq
K^*.
$$

These inclusions express logical dependence rather than automatic progression. $\operatorname{Effective}_{10}(f_H)$ means that all five state and five motion activities are effective. In delusion the profile is limited to the stated four and a half activities and $q_H$ is organised principally by pleasure, health, and profit.

Knowing, believing, recognising, and fulfilling are represented by

$$
\operatorname{KBRF}_{H,n}
=
\left(
\operatorname{Know}_{H,n},
\operatorname{Believe}_{H,n},
\operatorname{Recognise}_{H,n},
\operatorname{Fulfil}_{H,n}
\right).
$$

Knowing and believing concern internal orientation; recognising relates it to actual mutuality; fulfilling is evidenced through body-mediated conduct. Teaching and study are typed edges in $E_n$. Projection and reflection may change what is available to evaluation, but knowledge is realised by the learner's *jeevan* rather than transmitted as energy.
### A.12 Consequence, evaluation, and refinement

A human conduct occurrence is

$$
\operatorname{Act}_H
\left(
x_{H,n},
R^{\mathrm{actual}}_{H,n},
\widehat R_{H,n},
D_H,
s_{H,n},
\Gamma_{H,n};
\alpha^{\mathrm{conduct}}_{H,n}
\right).
$$

It yields $Y_{H,n}$. A later evaluative occurrence is

$$
\operatorname{Act}_H
\left(
z_{H,n},
\operatorname{Observe}(Y_{H,n}),
\widehat R_{H,n},
D_H,
s^{\mathrm{eval}}_{H,n},
\Gamma^{\mathrm{eval}}_{H,n};
\alpha^{\mathrm{eval}}_{H,n}
\right).
$$

The next orientation belongs to the admissible relation

$$
z_{H,n+1}
\in
\operatorname{Update}_H
\left(
z_{H,n},
\alpha^{\mathrm{eval}}_{H,n},
\operatorname{Study}_n,
\operatorname{ProjectionReflection}_n
\right).
$$

$\operatorname{Update}_H$ is not a learning algorithm. It permits repetition, correction of operative recognition, refinement of evaluation, and stabilisation of realised *sanskar* without making awakening automatic.

Dissatisfaction is the experienced predicate

$$
\operatorname{Dissatisfied}_H
\left(
z_{H,n},
Y_{H,n},
q_{H,n}
\right).
$$

It is neither excitation-pressure nor applied force. Both repetition and inquiry remain admissible because freedom of action prevents dissatisfaction from determining the branch.

### A.13 Harmony, T2, and T3

Let

$$
\mathcal{H}^{*}
=
\left\{
\textit{sukh},
\textit{shanti},
\textit{santosh},
\textit{anand},
\textit{paramanand}
\right\},
$$

and let $\mathcal{H}_H(z_H)\subseteq\mathcal{H}^{*}$ record the harmonies presently evidenced. The entries are named qualitative relations rather than magnitudes.

The proposed activity-completeness predicate is

$$
\begin{aligned}
T2^{*}(H)
\Longleftrightarrow\;&
\operatorname{Realised}(K^{*},H)\\
&\land\operatorname{Effective}_{10}(f_H)\\
&\land\mathcal{H}_H(z_H)=\mathcal{H}^{*}\\
&\land\operatorname{RestfulnessOfEffort}(H).
\end{aligned}
$$

Absence of presently reported dissatisfaction is expected but insufficient.

The proposed conduct-completeness predicate is

$$
T3^{*}(H)
\Longleftrightarrow
T2^{*}(H)
\land
\operatorname{StableHumaneConduct}(H,\mathcal{C},I),
$$

where $\mathcal{C}$ is a relevant diversity of relationship and work contexts and $I$ is a sustained trace. No universal duration is assigned. T2 concerns internal realisation and restfulness; T3 concerns repeatable public evidence. The asterisks mark operational reconstructions rather than source equations.

### A.14 Observation and verification

The posited state is separated from access available to different verifiers:

| Observation map | Accessible evidence |
|-----------------|--------------------|
| $\mathcal{O}^{\mathrm{first}}$ | First-person report of realisation, satisfaction, dissatisfaction, and harmony |
| $\mathcal{O}^{\mathrm{rel}}$ | Relationship recognition, value-fulfilment, contradiction, and mutual satisfaction reported by those involved |
| $\mathcal{O}^{\mathrm{conduct}}$ | Repeatable speech, bodily action, character, ethics, and participation visible to others |
| $\mathcal{O}^{\mathrm{work}}$ | Production, use, protection, regeneration, imbalance, and depletion |
| $\mathcal{O}^{\mathrm{instrument}}$ | Instrument-recordable material and pranic configurations and consequences |
| $\mathcal{O}^{\mathrm{text}}$ | Status as direct claim, translation choice, reconstruction, operational criterion, or open question |

Each judgement takes one of four statuses:

$$
\mathsf{VStatus}
=
\{
\mathrm{supported},
\mathrm{contradicted},
\mathrm{undetermined},
\mathrm{not\ assessed}
\}.
$$

For a human trace,

$$
V_H(I,\mathcal{C})
=
\left(
V_{\mathrm{thought}},
V_{\mathrm{behaviour}},
V_{\mathrm{work}},
V_{\mathrm{realisation}}
\right)
\in
\mathsf{VStatus}^{4}.
$$

The statuses are not aggregated. Contradiction in relationship or work defeats a present claim of complete public evidence even when inner realisation is asserted. Lack of an accepted instrument for T1 leaves its empirical status undetermined rather than measured.

Population-level goals are not derived by aggregating $V_H$. Family prosperity, social fearlessness, undivided society, and universal orderliness require further family, resource, network, and institutional states.
## Appendix B. Expanded glossary and notation

### B.1 Expanded conceptual glossary

| Term | Meaning in this reconstruction |
|------|--------------------------------|
| Omnipresence / absolute energy (*satta* / *nirpeksha urja*) | The unbounded, non-transforming reality in which every unit is saturated; no motion, pressure, or applied force is assigned to it. |
| Relative energy (*sapeksha urja*) | Unit power evident in mutuality as pressure, flow, waves, fields, heat, sound, electricity, and related effects. |
| Strength / force (*bal*) | Effort borne in a unit's state; represented qualitatively rather than as a scalar store. |
| Power (*shakti*) | Motion or operative expression of a force-bearing unit in mutuality. |
| State-pressure | Force relationally encountered in state; neither an additional force nor external source of activity. |
| Excitation-pressure | Received compulsion when *sam–visam* excitation is present. |
| Form (*roop*) | The real bounded configuration, shape, volume, and density of a bearer. |
| Property (*guna*) | Relative power expressed through generative, degenerative, and mediative tendencies. |
| Essential nature (*svabhav*) | Order-specific functional character or usefulness of property. |
| *Dharma* | Invariant innateness borne by an order; distinct from whether a particular activity fulfils it. |
| Constitutional kind | What a bearer is constituted as: atom, composition, pranic body, or T1 *jeevan*. |
| Manifested order | The role in which a bearer or joint form operates: material, pranic, animal, or knowledge. |
| Containing bearer | A closed compound, cell, or body with its own conduct and tetrad, realised through parts that retain identities and orders. |
| Complementarity | Order-appropriate reciprocity in structural need, nourishment, use, relationship, or participation. |
| Relationship (*sambandh*) | Human mutuality with inherent roles, expectations, and values. |
| Contact (*sampark*) | Human mutuality whose expectations are voluntary. |
| Evaluation | Sentient recognition of essential nature or fulfilment; species-conformant in animals and reflexive in humans. |
| Internal orientation | Human faculty, acceptance, knowledge, evaluation, and recognition profile. |
| *Sanskar* | Realisation-oriented acceptance evidenced as understanding, honesty, responsibility, and participation. |
| Hope-bondage (*asha-bandhan*) | The hope for happiness borne by constitutionally complete *jeevan*. |
| *Jeevan* values | *Sukh, shanti, santosh,* and *anand*, grounded in *paramanand* at realised *atma*. |
| Dissatisfaction | Experienced non-fulfilment or internal contradiction; neither physical pressure nor applied force. |
| Existential progression | Definite manifestation of material, pranic, animal, and knowledge orders under conducive conditions. |
| T1 / T2 / T3 | Constitutional completeness; activity completeness; conduct completeness. |

### B.2 Model notation

| Symbol | Meaning |
|--------|---------|
| $\mathbb{S}$ | State-complete Omnipresence; not a bearer or transition variable |
| $n,\Delta t_n$ | Activity-occurrence index and considered duration |
| $\mathcal{Q}_n$ | Complete bounded situation at occurrence $n$ |
| $U_n,\partial U_n$ | Active bearers in the local scenario and relevant external couplings |
| $\operatorname{id}(i)$ | Persistent identity of bearer $i$ |
| $\kappa_i,o_i$ | Constitutional kind and manifested order or role |
| $x_i=(\phi_i,\chi_i)$ | Full typed state: form plus order-specific internal condition |
| $D_i$ | Invariant order-specific *dharma* |
| $\operatorname{FulfilsDharma}(i,n)$ | Qualitative fulfilment status in one occurrence |
| $\operatorname{ComprehendsDharma}(H,n)$ | Human comprehension and evidence of invariant human *dharma* |
| $s_{i,n},\Gamma_{i,n}$ | Essential nature and non-empty qualitative *guna*-profile |
| $\alpha_{i,n}=\langle B_{i,n},S_{i,n},P_{i,n}\rangle$ | One complete effort–motion–result activity |
| $Y_{H,n}$ | Human consequence profile: internal, bodily, relational, and natural |
| $E_n,e,\lambda_e,\rho^{\mathrm{actual}}_e$ | Typed graph, edge, coupling kind, and actual relational condition |
| $R^{\mathrm{actual}}_i,\widehat R_i$ | Actual relational neighbourhood and operative recognition |
| $i\prec c,\operatorname{Parts}(c),N^{\mathrm{ext}}(c)$ | Part relation, constituents, and external neighbours of a containing bearer |
| $j\bowtie b$ | Body–*jeevan* association; not material containment or fusion |
| $c_J$ | Invariant constitutionally complete core of *jeevan* |
| $x_A,x_H$ | Animal and human joint states |
| $u^{B\to J},u^{J\to B}$ | Bodily presentation to *jeevan* and sentient expression through the body |
| $K^{*}$ | Fixed content: coexistence, *jeevan*, and humane conduct |
| $z_H=(f_H,\sigma_H,k_H,q_H,\widehat R_H)$ | Refinable human orientation |
| $k_H$ | Qualitative study, enlightenment, realisation, and evidence profile |
| $\operatorname{KBRF}_H$ | Knowing, believing, recognising, and fulfilling profile |
| $\operatorname{Update}_H$ | Non-deterministic admissibility relation for orientation refinement |
| $\operatorname{Pr}^{\mathrm{state}},\Pi^{\mathrm{exc}}$ | General state-pressure description and narrow excitation-pressure predicate |
| $\mathcal{H}^{*},\mathcal{H}_H$ | Full named harmony set and presently evidenced harmonies |
| $T2^{*},T3^{*}$ | Proposed operational predicates for activity and conduct completeness |
| $\mathcal{O}^{*},V_H$ | Observation maps and four-domain verification profile |
## Editorial Notes

### Running terms

The translations vary between state-complete/state-dynamic, status-complete/status-dynamic, and state-complete/state-active. This paper uses **state-complete** and **state-dynamic**. It uses **property** for *guna*, **essential nature** for *svabhav*, **effort** for *shram*, **motion** for *gati*, **result** for *parinam*, and **contact** for *sampark*. Quoted passages retain their translation wording.

### Omnipresence, Omnipotence, and absolute energy

The English sources render *satta* as Omnipresence and Omnipotence and also name it Space, uniform energy, and absolute energy. They equate Omnipotence with Omnipresence (SB, p. 250). **Omnipresence** is the running term because the same account denies motion, pressure, waves, and applied force to *satta*. **Absolute energy** is retained when the absolute–relative distinction is itself under discussion.

### The tetrad and triad

One passage aligns effort or strength with *dharma–svabhav*, motion or power with *svabhav–guna*, and result with *roop* (SB, pp. 60–62). Strength is independently aligned with state, power with motion, and result with a different existent state (KD 3.8, p. 84; KD 3.11, pp. 106–107). The paper follows those alignments without claiming a one-to-one derivation, since *svabhav* crosses effort and motion.

### *Chintan* and *sakshatkar* in *chitta*

The paired-activity enumerations name *chitta*'s state activity as contemplation (*chintan*) and its motion activity as imaging (*chitran*) (JV, p. 73; KD 3.6, pp. 71–72). The awakened account describes contemplation as direct recognition (*sakshatkar*) of justice, *dharma*, and truth, while a later summary abbreviates *chitta*'s strength as direct recognition (KD 3.8, p. 84; KD 3.16, p. 145). This paper uses **contemplation** for the activity-name and **direct recognition** for its awakened content or accomplishment.

### Knowledge as ground and realised content

The opening postulate names an omnipresent ground of Knowledge or Omnipotence containing insentient and sentient nature (KD, pp. 1–4). Later passages enumerate complete knowledge as coexistence, *jeevan*, and humane conduct, with participation in orderliness included in one formulation (KD 3.5, p. 69; KD 3.17, p. 148). $K^{*}$ represents the three-content epistemic formulation; participation is treated as purpose and evidence rather than a transmitted fourth substance.

### Four *jeevan* values and *paramanand*

One enumeration names *sukh, shanti, santosh,* and *anand* as harmonies between adjacent faculties (JV, pp. 137–138). The faculty-level account also names *paramanand* as the lasting effect of realisation at *atma*, with the four values as effects through the remaining faculties (MVD, pp. 100–101). The harmony set records this nested account without introducing a fifth reward alongside the common four-value enumeration.

### Pressure at two levels

Force in state is recognised as pressure and power in motion as flow; nature and material mutuality are also described through motion and pressure (SB, pp. 49, 256; MVD, p. 114; KD 3.11, pp. 105–106). Excitation-pressure is more narrowly the compulsion received under *sam–visam* excitation, contrasted with natural-state motion (SB, p. 59; KD 3.13, p. 118). The two descriptions concern one force–power relation. Pressure can condition change in mutuality without supplying the unit's basic impulsion or an external energy reservoir.

### Animal and human evaluation

Animal evaluation is recognition of essential nature under species-conformance, including friendliness and opposition (SB, pp. 55, 249). Human evaluation can additionally involve knowing, believing, justice, *dharma*, truth, value-fulfilment, and revision of accepted orientation (JV, pp. 69–70, 97–98). The formal model therefore supplies both an animal evaluation occurrence and a distinct human reflexive update relation.

### Composition, T1, and the containing bearer

Composition closes a new public conduct while constituents retain their own orders (MVD, p. 42; SB, p. 260). Atomic development reaches T1 instead (SB, pp. 75–76; KD 3.2–3.3). The dynamic graph and constitutive-consistency predicate are analytical devices for keeping these claims together. The sources do not formulate part relations, bearer creation events, or two simultaneous tetrads mathematically.

### Operational status of T2 and T3

Restfulness of effort, destination of motion, internal harmonies, ten effective activities, and humane conduct are separately supported (MVD, p. 103; SB, p. 58; JV, pp. 73–74, 137–139). $T2^{*}$ and $T3^{*}$ combine them into proposed operational predicates. The asterisk marks that the conjunction is a reconstruction rather than a source equation.

### Source boundary of the core mechanism

| Proposition | Status | Primary basis |
|-------------|--------|---------------|
| Omnipresence is state-complete; nature is countlessly unitised and state-dynamic | Direct textual claim | MVD p. 26; SB pp. 49–50, 248; KD p. 70 |
| Saturation is the basis of unit energy-fullness, forcefulness, regulation, and activity | Direct textual claim | MVD pp. 40–41, 46; SB pp. 57, 61, 69, 248; KD pp. 88, 122 |
| Effort, motion, and result are one inseparable activity | Direct textual claim | SB p. 58 |
| Effort aligns with *dharma–svabhav*, motion with *svabhav–guna*, result with *roop* | Direct textual alignment | SB pp. 60–62; KD pp. 84, 106–107 |
| Force in state is pressure; excitation-pressure is received compulsion under *sam–visam* excitation | Direct textual claim | SB pp. 49, 59, 256; KD pp. 105–106, 118 |
| Material, pranic, animal, and knowledge orders continue through their respective conformances | Direct textual claim | MVD pp. 8, 13; JV pp. 47–49 |
| Animal *jeevan* evaluates essential nature through species-conformant friendliness or opposition | Direct textual claim | SB pp. 55, 249; JV pp. 49, 69–70 |
| T1 *jeevan* is free of molecular- and weight-bondage and bears hope-bondage | Direct textual claim | MVD p. 91; SB pp. 55, 58, 61; KD pp. 61–62 |
| Five state and five motion activities belong to *jeevan* | Direct textual claim | JV pp. 92–94; KD pp. 71–72, 145 |
| Justice relates relationship recognition, value-fulfilment, evaluation, and mutual satisfaction | Direct textual claim | JV pp. 97–98, 137–139 |
| Constitutional kind, manifested order, typed graph, actual/recognised relation, pressure predicates, and guarded events | Analytical reconstruction | The sources supply qualitative distinctions, not these formalisms |
| Pranic, animal, body–*jeevan*, KBRF, evaluation, and observation modules | Analytical reconstruction grounded in direct claims | The sources supply activities and relations, not state schemas |
| $T2^{*}$, $T3^{*}$, and four-status verification | Proposed operational criteria | The sources supply completeness and evidence claims, not formal equivalences |
| A contemporary physical identification of T1 | Open empirical question | No accepted scientific counterpart is assumed |

## References

### Madhyasth Darshan (primary sources)

- **MVD** — Nagraj, A. [*Madhyasth Darshan — Co-existentialism*](../References/Madhyasth-Darshan/MVD-Madhyasth-Darshan-Coexistentialism.pdf). English translation by Rakesh Gupta. Cited: coexistence, state-completeness, state-dynamism, saturation, energy, and the tetrad (pp. 11, 26, 34, 40–47; §1–§3); existential progression and material hunger (pp. 8, 13; §4); compound conduct and reflected form (pp. 42, 49–50; §3.1, §4.2, §5.4); *guna, svabhav,* and *dharma* across orders (pp. 26, 49–51, 57–58, 115; §1, §3, §5); mutual pressure in material development (p. 114; §1–§2); relationship, contact, and the use-ladder (pp. 61–62, 105; §5); T1, two liberations, and hope-bondage (p. 91; §6.1); the four human dimensions (p. 18; §10.2); study, enlightenment, realisation, internal values, and completeness (pp. 100–103; §7.2, §9); faculties and delusion (pp. 58, 78, 80–81; §7); humane conduct (pp. 80, 101; §9.3); action-to-conception feedback (p. 218; §8.2–§8.3); right-use and regeneration (p. 264; §5.2, §10.2).
- **SB** — Nagraj, A. [*Samadhanatmak Bhautikvad* (*Resolution Centred Materialism*)](../References/Madhyasth-Darshan/SB-Samadhanatmak-Bhautikvad.pdf). English translation by Rakesh Gupta. Cited: coexistence, saturation, recognition, pressure, environmental excitation, directionality, and the effort–motion–result/tetrad alignment (pp. 48–61; §1–§3); energy-fullness and activeness (p. 69; §1); composition distinguished from development (pp. 75–76; §4); four orders and their *svabhav* and *dharma* (pp. 179–180; §3–§5); property, reflection, effect, state-pressure, flow, and relative power (pp. 248–257; §1–§3, §5); animal and knowledge orders as joint forms and animal evaluation of essential nature (pp. 55, 249; §6.3, §A.9); T1, atomic stability, and inexhaustible effort and motion (pp. 55, 61, 92, 144–145; §6.1); constituent order in composition (p. 260; §5.4); delusion (pp. 91–92; §7.3); undivided society (pp. 246–247; §10.3).
- **JV** — Nagraj, A. [*Jeevan Vidya: An Introduction*](../References/Madhyasth-Darshan/JV-Jeevan-Vidya-An-Introduction.pdf). English translation by Rakesh Gupta. Cited: coexistence, mutuality, inherent strength, and the absence of applied force from Omnipresence (pp. 43, 69, 149, 157–158; §1–§2, §5); four orders, conformance, animal hope, *sanskar*, body lineage, and complementarity (pp. 47–49, 59; §4–§7); values, character, ethics, right-use, protection, and human goals (pp. 54–61; §5, §9–§10); knowing, believing, recognising, and fulfilling (pp. 69–70; §5.2, §7.4); dissatisfaction under delusion and satisfaction through understanding (p. 76; §8.4); ten activities and the four-and-a-half account (pp. 73–74, 92–94; §7, §9.2); justice, relationship, values, evaluation, and mutual satisfaction (pp. 97–98, 137–139; §8–§10); human *dharma* as happiness and orderliness (pp. 110, 121–123; §3.4, §8.1).
- **KD** — Nagraj, A. *Manav Karm Darshan*. [Working English translation](../References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Karm-Darshan-English.pdf); Hindi source `KD-karm darshan v5.pdf`. Machine-assisted working translation — not a published translation; cited as corroboration only. Cited: knowledge, action, human consequence, hope for happiness, experience, inference, and absolute knowledge (pp. 1–4; §7–§8); environment, study, *sanskar*, and transformable human essential nature (pp. 6–9, 25–27; §3.3, §7–§8); humane values, character, and ethics (p. 67; §9.3); particle exchange and molecular joining (3.1, pp. 56–58; 3.11, pp. 103–104; §4–§5); compositional sequence and T1 (3.2–3.3, pp. 58–62; §4, §6); complete knowledge and five state–motion pairs (3.5–3.6, pp. 69–72; §3.4, §7–§9); state–motion indivisibility, forcefulness, and reflection (3.8–3.9, pp. 84, 88, 94; §1–§3, §5); order-specific *svabhav, dharma,* and *guna* (3.9–3.10, pp. 98–102; §2–§3, §5, §8); strength, power, result, pressure, and flow (3.11, pp. 102–109; §1–§3, §5); study and the realisation-oriented method (3.12, p. 112; §7.2, §8.4); excitation-pressure and uniform energy (3.13, pp. 118, 122; §1–§2); body–*jeevan*, faculties, result-to-reflection, knower, and object of knowledge (3.16–3.17, pp. 141–148; §6–§8).

### Related studies in this collection

- [*The Ontology of Coexistence*](../The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.pdf) — saturation, four orders, compositional versus atomic development, T1–T3, and *jeevan* (§§1.2–1.7); companion technical note [*Rūpa, Guṇa, Svabhāva, and Dharma in a State-Dynamic Unit*](../The-Ontology-of-Coexistence/Technical-Note-Roop-Guna-Svabhava-Dharma.pdf)
- [*Coexistence from First Principles*](../Coexistence-From-First-Principles/Coexistence-From-First-Principles.pdf) — compound-closure, order-relative stability, four progressions, order-typed coupling, and the guarded status of T1
- [*The Epistemology of Coexistence*](../The-Epistemology-of-Coexistence/The-Epistemology-of-Coexistence.pdf) — knowing, evidence, and the faculty architecture; companion [*A Functional Model of Jeevan*](../The-Epistemology-of-Coexistence/Research-Note-Jeevan-Functional-Model.pdf)
- [*Nature of Time*](../Nature-Of-Time/Nature-Of-Time.pdf) — *kaal* as duration of unit-activity
- [*Human Behavior and Society*](../Human-Behavior-And-Society/Human-Behavior-And-Society.pdf) — humane conduct and social organisation
- [*Family Relationships and Values*](../Family-Relationships-And-Values/Family-Relationships-And-Values.pdf) — established values and mutual satisfaction
- [*How Undivided Society Is Established*](../How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established.pdf) — family to universal order
- [*Why Humans Are Not Just Material*](../Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.pdf) — body and *jeevan*
- [*Death, Continuity, and Rebirth*](../Death-Continuity-And-Rebirth/Death-Continuity-And-Rebirth.pdf) — persistence of *jeevan* and *sanskar* across bodies

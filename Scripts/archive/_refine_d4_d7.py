"""Refine D7 (justice as operator) + D7a (trust), and repair all mangled symbols.

Archived one-off editor for The-Coexistence-Template.md.
"""
import _bootstrap  # noqa: F401
from _common import BASE

KAPPA, TAU, MU, RHO, PHI = "\u03ba", "\u03c4", "\u03bc", "\u03c1", "\u03c6"
SUBSET, ELEM, ARROW, IFF = "\u2286", "\u2208", "\u2192", "\u21d4"
LANG, RANG, SUB1, SUB2 = "\u27e8", "\u27e9", "\u2081", "\u2082"
EM = "\u2014"

p = BASE / "Studies" / "The-Coexistence-Template.md"
t = p.read_bytes().decode("cp1252")

old_d7 = (
    '**D7 (Justice).** For knowledge-order units, justice is the composite '
    '? ? ? ? ? ? mutual satisfaction: "justice ' + EM + ' manifested through '
    'relationships, values, evaluation, and mutual satisfaction" (JV p. 55). '
    'Trust, the foundational human value, is defined directly on the template: '
    '"Trust is the act of fulfilling the inherent expectation of values in '
    'mutuality" (MVD p. 73).'
)

new_d7 = (
    f'**D7 (Justice).** Justice (*nyaya*) is **not a member of V** {EM} it is the '
    f'*name the texts give to the complete operation* on a relationship at the '
    f'knowledge order: the composite **{RHO} {ARROW} {PHI} {ARROW} {MU} {ARROW} '
    f'mutual satisfaction**. This is a definition, not a gloss:\n\n'
    f'> **"Justice (nyaya): ... Recognising relationships, fulfilling values, '
    f'evaluating, and achieving mutual satisfaction is justice."**\n'
    f'> {EM} MVD p. 311 (repeated MVD p. 336); cf. "justice {EM} manifested through '
    f'relationships, values, evaluation, and mutual satisfaction" (JV p. 55)\n\n'
    f'So justice is the knowledge-order instantiation of the template\'s core cycle '
    f'(L1) with evaluation (D6) added. It is the **operator over V**, not an element '
    f'of it. The established values (D4) are the *content* it operates on; justice is '
    f'the *act* of fulfilling and evaluating them. Equivalently, "Humane behaviour in '
    f'mutuality itself is justice" (MVD p. 35).\n\n'
    f'**D7a (Trust as the {PHI}-linked value).** Trust (*vishwas*) occupies two roles '
    f'at once, which is why it stands closest to the template of all the established '
    f'values. Its own definition coincides almost verbatim with fulfilment {PHI} (D5):\n\n'
    f'> **"Trust (vishwas): Trust is the act of fulfilling the inherent expectation of '
    f'values in mutuality."**\n'
    f'> {EM} MVD p. 73 (and p. 336: "Fulfilment of values inherent in mutuality")\n\n'
    f'Thus trust is **(i)** a member of V (an established value) and **(ii)** the '
    f'value-level name of the {PHI} step itself {EM} what is established when the '
    f'fulfilment part of justice succeeds. The texts give the resulting causal order '
    f'explicitly: "happiness and peace lead to affection, affection leads to trust, '
    f'trust leads to enlightenment of coexistence" (MVD p. 72). In template terms: '
    f'successful {PHI} over the established values {ARROW} mutual satisfaction {ARROW} '
    f'affection {ARROW} **trust** {ARROW} enlightenment of coexistence. Justice is the '
    f'operation; trust is the value that operation deposits.'
)

assert old_d7 in t, "old D7 paragraph not found verbatim"
t = t.replace(old_d7, new_d7)

# Generic symbol repairs (every '?' below is a cp1252-mangled glyph).
pairs = [
    ("the operations ?, ?, ? act on", f"the operations {RHO}, {PHI}, {MU} act on"),
    ("**R ? U " + "\u00d7" + " U**", f"**R {SUBSET} U \u00d7 U**"),
    ("| **?** | The composition (assembly) operator", f"| **{KAPPA}** | The composition (assembly) operator"),
    ("| **?** | The transmission (tradition) operator", f"| **{TAU}** | The transmission (tradition) operator"),
    ("Each unit u ? U possesses", f"Each unit u {ELEM} U possesses"),
    ("**sig(u) = ?roop, gun, svabhav, dharma?**", f"**sig(u) = {LANG}roop, gun, svabhav, dharma{RANG}**"),
    ("each r = (u?, u?) ? R carries", f"each r = (u{SUB1}, u{SUB2}) {ELEM} R carries"),
    ("orders and signatures of u?, u?,", f"orders and signatures of u{SUB1}, u{SUB2},"),
    ("a valuation **v: R ? V** assigns", f"a valuation **v: R {ARROW} V** assigns"),
    ("Recognition **?** is a unit's", f"Recognition **{RHO}** is a unit's"),
    ("fulfilment **?** is conduct", f"fulfilment **{PHI}** is conduct"),
    ("Evaluation **?** is a second-order", f"Evaluation **{MU}** is a second-order"),
    ("relationship against the value inherent in it. ? is defined",
     f"relationship against the value inherent in it. {MU} is defined"),
    ("**D8 (Composition, two modes).** ? takes", f"**D8 (Composition, two modes).** {KAPPA} takes"),
    ("**D10 (Transmission).** ? re-instantiates", f"**D10 (Transmission).** {TAU} re-instantiates"),
    ("The carrier of ? differs by order", f"The carrier of {TAU} differs by order"),
    ("Every u ? U participates", f"Every u {ELEM} U participates"),
    ("**L4 (Persistence ? fulfilment).**", f"**L4 (Persistence {IFF} fulfilment).**"),
    ("| Order | Carrier of ? | Grounding |", f"| Order | Carrier of {TAU} | Grounding |"),
    ("The output of ? is a unit", f"The output of {KAPPA} is a unit"),
    ("Iterating ? under L3", f"Iterating {KAPPA} under L3"),
    ("particles ? atoms ? molecules ? molecular structures ? planets",
     f"particles {ARROW} atoms {ARROW} molecules {ARROW} molecular structures {ARROW} planets"),
    ("cells ? organisms (biological line); individual ? family ? community ? undivided society ? universal orderliness",
     f"cells {ARROW} organisms (biological line); individual {ARROW} family {ARROW} community "
     f"{ARROW} undivided society {ARROW} universal orderliness"),
    ("In the knowledge order, ?, ?, ? and ? all route",
     f"In the knowledge order, {RHO}, {PHI}, {MU} and {KAPPA} all route"),
    ("since sanskar is the only ?-carrier", f"since sanskar is the only {TAU}-carrier"),
    ("This is ? and ? restated", f"This is {PHI} and {TAU} restated"),
    ("hungry/overfull bonding ? molecules ? structures | cells ? multicellular organisms",
     f"hungry/overfull bonding {ARROW} molecules {ARROW} structures | cells {ARROW} multicellular organisms"),
    ("family ? ten-tier self-governance ? world-family order",
     f"family {ARROW} ten-tier self-governance {ARROW} world-family order"),
    ("delusion ? exploitation, war", f"delusion {ARROW} exploitation, war"),
    ("in the knowledge order, ? carries *understanding*", f"in the knowledge order, {TAU} carries *understanding*"),
    ("(? at the organism tier)", f"({TAU} at the organism tier)"),
    ("natural notation for ? and L6", f"natural notation for {KAPPA} and L6"),
    ("is the ?-condition applied", f"is the {PHI}-condition applied"),
    ("The symbols above (?, ?, ?) do not appear", f"The symbols above ({KAPPA}, {TAU}, {MU}) do not appear"),
    ("one operator ? with four carriers", f"one operator {TAU} with four carriers"),
    # D2/D5 line-3 arrows in clause list (Section 2 clause 7)
    ("particles ? atoms ? molecules ? structures; cells ? organs ? organisms; "
     "individuals ? families ? communities ? universal order.",
     f"particles {ARROW} atoms {ARROW} molecules {ARROW} structures; cells {ARROW} organs "
     f"{ARROW} organisms; individuals {ARROW} families {ARROW} communities {ARROW} universal order."),
]

missing = []
for old, new in pairs:
    if old in t:
        t = t.replace(old, new)
    else:
        missing.append(old)

p.write_text(t, encoding="utf-8")
print("MISSING:", len(missing))
for m in missing:
    print("  -", m[:70])
print("remaining '?':", t.count("?"))

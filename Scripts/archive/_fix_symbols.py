"""Repair mangled Unicode math symbols in The-Coexistence-Template.md (one-off).

Archived — kept for history; do not run on current studies without review.
"""
import _bootstrap  # noqa: F401
from pathlib import Path

from _common import BASE

KAPPA = "\u03ba"
TAU = "\u03c4"
MU = "\u03bc"
RHO = "\u03c1"
PHI = "\u03c6"
SUBSET = "\u2286"
ELEM = "\u2208"
ARROW = "\u2192"
IFF = "\u21d4"
LANG = "\u27e8"
RANG = "\u27e9"
SUB1 = "\u2081"
SUB2 = "\u2082"

p = BASE / "Studies" / "The-Coexistence-Template.md"
t = p.read_text(encoding="utf-8")

pairs = [
    ("particles ? atoms ? molecules ? structures; cells ? organs ? organisms; "
     "individuals ? families ? communities ? universal order.",
     f"particles {ARROW} atoms {ARROW} molecules {ARROW} structures; cells {ARROW} organs "
     f"{ARROW} organisms; individuals {ARROW} families {ARROW} communities {ARROW} universal order."),
    ("**R ? U \u00d7 U**", f"**R {SUBSET} U \u00d7 U**"),
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
    ("justice is the composite ? ? ? ? ? ? mutual satisfaction",
     f"justice is the composite {RHO} {ARROW} {PHI} {ARROW} {MU} {ARROW} mutual satisfaction"),
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
]

missing = []
for old, new in pairs:
    if old not in t:
        missing.append(old)
    t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print(f"Applied {len(pairs) - len(missing)}/{len(pairs)} replacements")
for m in missing:
    print("MISSING:", m[:80])
remaining = t.count("?") - t.count("why and how") * 0
print("Remaining '?' chars:", t.count("?"))

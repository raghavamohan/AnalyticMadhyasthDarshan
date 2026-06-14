"""Insert subsection 1.1 (the applied goal of the paper) at the end of Section 1.

Written via script because the workspace editors re-save as cp1252 and destroy
the Greek/arrow glyphs; this reads and writes UTF-8 and uses \\u escapes for any
non-ASCII glyph so the script source itself stays cp1252-safe.
"""
from _common import BASE

RHO, PHI, MU, TAU = "\u03c1", "\u03c6", "\u03bc", "\u03c4"
EM = "\u2014"

p = BASE / "Studies" / "The-Coexistence-Template.md"
t = p.read_text(encoding="utf-8")

anchor = (
    "differs from mainstream science.\n\n---\n\n## 2. The template, informally"
)
assert anchor in t, "anchor not found"

section = (
    f"### 1.1 Why precision: a template meant to travel\n\n"
    f"Stating the template formally is not an end in itself. Shri Nagraj elaborated it "
    f"in depth for a single tier {EM} the human {EM} and asserted, but did not work out, "
    f"its operation at the others. The point of a precise, tier-neutral statement is to "
    f"let the same structure be **carried to systems he did not himself analyse**, and "
    f"used there in two directions.\n\n"
    f"- **Design (forward use).** Given a system one wishes to build or reform {EM} an "
    f"organisation, an economy, an ecological arrangement, an institutional or software "
    f"architecture {EM} the template supplies a constructive checklist of what a *stable* "
    f"assembly requires: identifiable units; a medium that energises and regulates them; "
    f"definite relationships with explicit expectation profiles E(r); value that actually "
    f"*flows* in each relationship rather than mere incentive; composition by complementary "
    f"need rather than competition (L3); persistence made conditional on fulfilment (L4); "
    f"and an explicit carrier of transmission across member turnover (L5). The system can "
    f"then be designed so that each clause is satisfied by construction, instead of "
    f"discovering the missing clause after the system has decayed.\n\n"
    f"- **Diagnosis (reverse use).** Given a system that is failing or fragile, the template "
    f"becomes an instrument of fault localisation: walk its clauses and find the one that is "
    f"unmet. Is a relationship unrecognised ({RHO}), its value unfulfilled ({PHI}), "
    f"mis-evaluated ({MU} {EM} the three failure modes of D6), extracted beyond regeneration "
    f"(P5), or never transmitted to the next generation of members ({TAU}, L5)? Each unmet "
    f"clause names a specific, addressable failure rather than a vague malaise, and the "
    f"knowledge-order discontinuity (P3) predicts that human-tier systems will fail at "
    f"exactly these understanding-dependent steps first.\n\n"
    f"This forward/reverse use is what motivates the tier-neutral formalisation of Sections "
    f"2{EM}3: it must be stated independently of its original human framing before it can be "
    f"applied elsewhere. The applications in Section 8 are first instances; the broader claim "
    f"is that **any** system describable as units-in-relationship is a candidate for both "
    f"uses. Two cautions travel with this ambition. First, the template's metaphysical axioms "
    f"(the medium O, *jeevan*, A1{EM}A2, D6) are not established by the formalism, so any "
    f"analysis that leans on them inherits their status as commitments, not results. Second, "
    f"importing the template into a domain Shri Nagraj did not treat is itself an interpretive "
    f"act: the mapping from that domain's parts onto units, relationships, and values must be "
    f"argued, not assumed."
)

new = (
    "differs from mainstream science.\n\n"
    + section
    + "\n\n---\n\n## 2. The template, informally"
)
t = t.replace(anchor, new)

p.write_text(t, encoding="utf-8")
print("inserted 1.1; remaining '?':", t.count("?"))

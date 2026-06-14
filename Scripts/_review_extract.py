"""Extract review snippets around quoted phrases from the cached sources."""
import re

from _common import SCRIPTS, chapter_map, load_pages, norm


def find_snippet(pages: list[tuple[int, str]], phrase: str, width: int = 260) -> str:
    nphrase = norm(phrase)
    for page_num, text in pages:
        ntext = norm(text)
        idx = ntext.find(nphrase)
        if idx != -1:
            # approximate mapping back using ratio (good enough for review)
            ratio = len(text) / max(len(ntext), 1)
            start = max(0, int(idx * ratio) - 80)
            end = min(len(text), int((idx + len(nphrase)) * ratio) + width)
            snippet = re.sub(r"\s+", " ", text[start:end])
            return f"p{page_num} | {snippet}"
    return "NOT FOUND"


mvd = load_pages("MVD")
jv = load_pages("JV")
sb = load_pages("SB")
mvd_ch = chapter_map(mvd)

checks = [
    ("MVD", mvd, "Trust is the act of fulfilling the inherent expectation of values in mutuality"),
    ("MVD", mvd, "Humane behaviour in mutuality itself is justice"),
    ("MVD", mvd, "Exploitation (shoshan): Unit - Conducive unit"),
    ("MVD", mvd, "Nurturing (poshan): Unit + Conducive unit"),
    ("MVD", mvd, "Material prosperity is accomplished only by adhering to the policy"),
    ("MVD", mvd, "earning for expenditure"),
    ("MVD", mvd, "Sociality gives rise to needs"),
    ("MVD", mvd, "Fulfilling the values inherent in relationships and associations itself is sociality"),
    ("MVD", mvd, "Justice pertains to the orderliness of behaviour based on policies that protect humaneness"),
    ("MVD", mvd, "Only three causes are observed for all the fear in humans"),
    ("MVD", mvd, "a family is an integral part of the undivided society"),
    ("JV", jv, "perform study, attain mastery, then evidence it in living"),
    ("JV", jv, "religion-based-governance and economics-based-governance has failed"),
    ("JV", jv, "conflict, revolt, exploitation, and war"),
    ("JV", jv, "revolts, rebellions, exploitations, and wars"),
    ("JV", jv, "values and evaluation"),
    ("JV", jv, "dos and don'ts"),
    ("JV", jv, "labelling non-believers as sinners"),
    ("SB", sb, "Education-sanskar is the only source of enlightenment and definitive understanding"),
    ("SB", sb, "The basis of ideas of Resolution Centred Materialism is coexistence only"),
    ("SB", sb, "For humans, this complementary way is realised through recognising and fulfilling relationships"),
]

lines = []
for src, pages, phrase in checks:
    result = find_snippet(pages, phrase)
    if src == "MVD" and result.startswith("p"):
        page_num = int(result.split("|")[0].strip()[1:])
        result += f" | {mvd_ch.get(page_num, '?')}"
    lines.append(f"[{src}] {phrase}\n  -> {result}\n")

(SCRIPTS / "_review_quotes.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {SCRIPTS / '_review_quotes.txt'}")

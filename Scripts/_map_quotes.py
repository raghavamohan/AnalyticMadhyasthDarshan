"""Map quoted phrases to their page (and MVD chapter) in the cached sources."""
import re

from _common import SCRIPTS, load_pages, norm


def find_page(pages: list[tuple[int, str]], phrase: str) -> tuple[str, str]:
    nphrase = norm(phrase)
    for page_num, text in pages:
        if nphrase in norm(text):
            chapter = re.search(r"Chapter-(\d+)", text)
            return str(page_num), chapter.group(0) if chapter else "no-ch-on-page"
    joined = norm(" ".join(text for _, text in pages))
    if nphrase in joined:
        return "span", "span"
    return "NOT FOUND", ""


mvd = load_pages("MVD")
jv = load_pages("JV")
sb = load_pages("SB")

checks = [
    ("MVD", mvd, "Trust is the act of fulfilling the inherent expectation of values in mutuality"),
    ("MVD", mvd, "Humane behaviour in mutuality itself is justice"),
    ("MVD", mvd, "To disregard sentiments (values) in a relationship is indeed exploitation of that relationship"),
    ("MVD", mvd, "Humans on this Earth are engaged in endeavours and experiments"),
    ("MVD", mvd, "Sociality gives rise to needs"),
    ("MVD", mvd, "Material prosperity is accomplished only by adhering"),
    ("MVD", mvd, "earning for expenditure"),
    ("MVD", mvd, "righteous expenditure"),
    ("MVD", mvd, "more production than the needs"),
    ("MVD", mvd, "Exploitation ( shoshan ): Unit - Conducive unit"),
    ("MVD", mvd, "Nurturing ( poshan ): Unit + Conducive unit"),
    ("JV", jv, "perform study, attain mastery, then evidence it in living"),
    ("JV", jv, "religion-based-governance and economics-based-governance has failed"),
    ("JV", jv, "Profit and loss constitute a relentless cycle"),
    ("JV", jv, "The promise was that the king would ensure the security of life and property"),
    ("JV", jv, "Coexistence means living with complementarity"),
    ("JV", jv, "producing in excess of our family"),
    ("JV", jv, "values and evaluation"),
    ("JV", jv, "fear and temptation"),
    ("JV", jv, "conflict, revolt, exploitation, and war"),
    ("SB", sb, "Education-sanskar is the only source of enlightenment and definitive understanding"),
    ("SB", sb, "The basis of ideas of Resolution Centred Materialism is coexistence only"),
    ("SB", sb, "For humans, this complementary way is realised through recognising and fulfilling relationships"),
    ("MVD", mvd, "Justice pertains to the orderliness of behaviour based on policies that protect humaneness"),
    ("MVD", mvd, "Sociality: Fulfilling the values inherent in relationships and associations itself is sociality"),
]

lines = []
for src, pages, phrase in checks:
    page, chapter = find_page(pages, phrase)
    lines.append(f"{src} | p={page} | {chapter} | {phrase}")

(SCRIPTS / "_map_results.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))

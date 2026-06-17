"""Shared helpers for the Scripts directory.

All paths are derived from the script location, so these tools work no matter
which directory they are invoked from.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from pypdf import PdfReader

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent
STUDIES = BASE / "Studies"
REFERENCES = BASE / "References"
CACHE = SCRIPTS / "_pdf_cache"
SOURCE = REFERENCES / "Madhyasth-Darshan"

TAG_ABBREVS = frozenset(
    {"MVD", "SB", "JV", "AVD", "JVD", "BU", "TU", "KU", "MU", "CU", "BG", "BSB", "VC", "DDV", "Bhattacharya", "AV", "SV", "ATR"}
)
AUTHOR_YEAR_PREFIXES = (
    "Chalmers",
    "Nagel",
    "Strawson",
    "Popper",
    "Bloom",
    "Churchland",
    "Dennett",
    "Goff",
    "Kandel",
    "Kim",
    "Shapiro",
    "Tomasello",
    "Crockett",
    "Curry",
    "Frankish",
    "Graham",
    "Greene",
    "Haidt",
    "Jarczewski",
    "Jarczewski and Riggs",
    "Limanowski",
    "Limanowski and Blankenburg",
    "Melloni",
    "Melloni et al.",
    "Piredda",
    "Tufft",
    "Tufft et al.",
    "Wiese",
    "Hashemi",
    "Kuhn",
    "Massimi",
)


def norm(text: str) -> str:
    """Normalise text for fuzzy phrase matching (case, punctuation, whitespace)."""
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.lower()
    text = re.sub(r"\.{3,}|…", " ", text)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = text.replace("'", "")
    text = re.sub(r"\(\s*(\d+)\s*\)", r" \1 ", text)
    text = re.sub(r"[-/+]", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def norm_loose(text: str) -> str:
    """Like norm, but also drop isolated 1–3 digit tokens (PDF page/line artifacts)."""
    loose = norm(text)
    loose = re.sub(r"\s+\d{1,3}\s+", " ", loose)
    return re.sub(r"\s+", " ", loose).strip()


def _phrase_parts(phrase: str) -> list[str]:
    parts = re.split(r"\.{3,}|…", phrase)
    return [norm(part) for part in parts if norm(part)]


def find_phrase(pages: list[tuple[int, str]], phrase: str) -> str | None:
    """Return page location if phrase appears in pages, else None or PARTIAL(...)."""
    parts = _phrase_parts(phrase)
    if not parts:
        return None

    joined = norm(" ".join(text for _, text in pages))
    joined_loose = norm_loose(" ".join(text for _, text in pages))

    def corpus_has(part: str) -> bool:
        return part in joined or part in joined_loose

    def corpus_index(part: str, start: int = 0) -> int:
        for corpus in (joined, joined_loose):
            index = corpus.find(part, start)
            if index >= 0:
                return index
        return -1

    if not all(corpus_has(part) for part in parts):
        longest = max(parts, key=len)
        partial = longest[: min(35, len(longest))]
        if partial and (partial in joined or partial in joined_loose):
            return f"PARTIAL({partial}...)"
        return None

    search_at = 0
    for part in parts:
        index = corpus_index(part, search_at)
        if index < 0:
            partial = part[: min(35, len(part))]
            return f"PARTIAL({partial}...)"
        search_at = index + len(part)

    first_part = parts[0]
    for page_num, text in pages:
        page_norm = norm(text)
        page_loose = norm_loose(text)
        if first_part in page_norm or first_part in page_loose:
            return f"p{page_num}"
    return "yes(spans pages)"


def html_to_text(raw: str) -> str:
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.IGNORECASE | re.DOTALL)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.IGNORECASE | re.DOTALL)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return html.unescape(raw)


def load_reference_pages(path: Path, cache_key: str) -> list[tuple[int, str]]:
    """Load a reference file as (page_number, text) pairs. PDFs are cached under Scripts/_pdf_cache/."""
    cache_file = CACHE / f"{cache_key}.txt"
    CACHE.mkdir(exist_ok=True)

    if cache_file.exists() and path.suffix.lower() == ".pdf":
        raw = cache_file.read_text(encoding="utf-8", errors="replace")
        pages: list[tuple[int, str]] = []
        for chunk in raw.split("\f"):
            if not chunk.strip():
                continue
            match = re.match(r"---PAGE (\d+)---\n", chunk)
            if match:
                pages.append((int(match.group(1)), chunk[match.end() :]))
        if pages:
            return pages

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        parts = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append((index, text))
            parts.append(f"---PAGE {index}---\n{text}")
        cache_file.write_text("\f".join(parts), encoding="utf-8")
        return pages

    if suffix == ".html":
        text = html_to_text(path.read_text(encoding="utf-8", errors="replace"))
        return [(1, text)]

    if suffix == ".md":
        return [(1, path.read_text(encoding="utf-8", errors="replace"))]

    raise ValueError(f"Unsupported reference format: {path}")


def load_pages(key: str) -> list[tuple[int, str]]:
    """Load a cached PDF text file (e.g. 'MVD') as (page_number, text) pairs."""
    cache_file = CACHE / f"{key}.txt"
    if not cache_file.exists():
        raise FileNotFoundError(
            f"Cache missing for {key!r}. Run Scripts/_verify_quotes.py first to build Scripts/_pdf_cache/."
        )
    raw = cache_file.read_text(encoding="utf-8", errors="replace")
    pages: list[tuple[int, str]] = []
    for chunk in raw.split("\f"):
        match = re.match(r"---PAGE (\d+)---\n", chunk)
        if match:
            pages.append((int(match.group(1)), chunk[match.end() :]))
    return pages


def parse_reference_registry(readme_path: Path | None = None) -> dict[str, Path]:
    """Map citation tags (MVD, Chalmers 1995, …) to local files under References/."""
    readme_path = readme_path or (REFERENCES / "README.md")
    text = readme_path.read_text(encoding="utf-8", errors="replace")
    registry: dict[str, Path] = {}

    for match in re.finditer(
        r"\|\s*\*\*([^*|]+)\*\*\s*\|\s*\[([^\]]+)\]\(([^)]+)\)",
        text,
    ):
        tag = match.group(1).strip()
        link = match.group(3).strip()
        if link.startswith("http") or tag == "MD":
            continue
        if "same as" in match.group(2).lower() or "same as" in link.lower():
            continue
        path = (readme_path.parent / link).resolve()
        if path.exists():
            registry[tag] = path

    if "TU" in registry and "KU" not in registry:
        registry["KU"] = registry["TU"]

    for path in REFERENCES.rglob("*"):
        if path.suffix.lower() not in {".pdf", ".html", ".md"}:
            continue
        if path.name in {"README.md", "MANIFEST.md", "NOT-DOWNLOADED.md"}:
            continue
        author_year = re.match(r"^([A-Za-z]+)-(\d{4})-", path.stem)
        if author_year:
            tag = f"{author_year.group(1)} {author_year.group(2)}"
            registry.setdefault(tag, path.resolve())

    return registry


def chapter_map(page_list: list[tuple[int, str]]) -> dict[int, str]:
    """Map each page number to the most recent 'Chapter-N' marker seen."""
    mapping: dict[int, str] = {}
    current = "?"
    for page_num, text in page_list:
        chapter = re.search(r"Chapter-(\d+)", text)
        if chapter:
            current = chapter.group(0)
        mapping[page_num] = current
    return mapping

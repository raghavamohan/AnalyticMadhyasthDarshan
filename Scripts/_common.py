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


def study_dir(slug: str) -> Path:
    return STUDIES / slug


def study_md(slug: str) -> Path:
    return study_dir(slug) / f"{slug}.md"


def study_pdf(slug: str) -> Path:
    return study_dir(slug) / f"{slug}.pdf"


def study_html(slug: str) -> Path:
    return study_dir(slug) / f"{slug}.html"


def study_pdf_href(slug: str) -> str:
    """Relative href from Studies/index.html or Studies/README.md."""
    return f"{slug}/{slug}.pdf"


def study_pdf_ref_path(slug: str) -> str:
    """Relative path from References/ to the study PDF."""
    return f"../Studies/{slug}/{slug}.pdf"


def normalize_study_slug(value: str) -> str:
    slug = value.strip().removesuffix(".md").removesuffix(".pdf").removesuffix(".html")
    if not slug:
        raise ValueError("Study slug must not be empty.")
    return slug


def iter_study_md_paths() -> list[Path]:
    paths: list[Path] = []
    if not STUDIES.is_dir():
        return paths
    for child in sorted(STUDIES.iterdir()):
        if not child.is_dir():
            continue
        md_path = child / f"{child.name}.md"
        if md_path.is_file():
            paths.append(md_path)
    return paths


def slug_from_study_relative_path(rel: Path) -> str | None:
    parts = rel.parts
    if not parts or parts[0] in {"README.md", "index.html"}:
        return None
    slug = parts[0]
    if not (STUDIES / slug).is_dir():
        return None
    if len(parts) == 1:
        return slug
    if len(parts) == 2 and parts[1] == f"{slug}.md":
        return slug
    if (STUDIES / slug / f"{slug}.md").is_file():
        return slug
    return None


def known_study_slugs() -> list[str]:
    return sorted(path.parent.name for path in iter_study_md_paths())

TAG_ABBREVS = frozenset(
    {"MVD", "SB", "JV", "AVD", "JVD", "BU", "TU", "KU", "MU", "CU", "BG", "BSB", "VC", "DDV", "Bhattacharya", "AV", "SV", "ATR"}
)
PDF_CACHE_VERSION = "v2"
PAGE_HEADER_RE = re.compile(rf"---PAGE (\d+) {PDF_CACHE_VERSION}---\n")
MIN_CACHE_CHARS = 100

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


def ligature_norm(text: str) -> str:
    """Normalize PDF ligatures and non-breaking spaces before whitespace collapse."""
    return (
        text.replace("\u00a0", " ")
        .replace("\ufb01", "fi")
        .replace("\ufb02", "fl")
        .replace("\ufb00", "ff")
        .replace("\ufb03", "ffi")
        .replace("\ufb04", "ffl")
    )


def clean_pdf_text(text: str) -> str:
    """Collapse word-per-line PDF extraction artifacts into contiguous prose."""
    text = ligature_norm(text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def extract_pdf_page_text(raw: str) -> str:
    """Full PDF page text prep: ligatures then whitespace collapse."""
    return clean_pdf_text(raw)


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


def _parse_pdf_cache(raw: str) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    for chunk in raw.split("\f"):
        if not chunk.strip():
            continue
        match = PAGE_HEADER_RE.match(chunk)
        if match:
            pages.append((int(match.group(1)), chunk[match.end() :]))
    return pages


def _page_header(page_num: int) -> str:
    return f"---PAGE {page_num} {PDF_CACHE_VERSION}---\n"


def cache_key_for(path: Path) -> str:
    return path.stem.replace(" ", "_")


def cache_path_for(path: Path) -> Path:
    return CACHE / f"{cache_key_for(path)}.txt"


def pages_have_content(pages: list[tuple[int, str]], min_chars: int = MIN_CACHE_CHARS) -> bool:
    return sum(len(text) for _, text in pages) >= min_chars


def _write_pdf_cache(cache_file: Path, pages: list[tuple[int, str]]) -> None:
    parts = [f"{_page_header(page_num)}{text}" for page_num, text in pages]
    cache_file.write_text("\f".join(parts), encoding="utf-8")


def _read_pdf_cache(cache_file: Path, source: Path) -> list[tuple[int, str]] | None:
    if not cache_file.exists():
        return None
    try:
        if cache_file.stat().st_mtime < source.stat().st_mtime:
            return None
    except OSError:
        return None
    pages = _parse_pdf_cache(cache_file.read_text(encoding="utf-8", errors="replace"))
    if pages_have_content(pages):
        return pages
    return None


def _extract_pdf_pages(path: Path) -> list[tuple[int, str]]:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ValueError(f"Could not read PDF: {exc}") from exc
    pages: list[tuple[int, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = extract_pdf_page_text(page.extract_text() or "")
        pages.append((index, text))
    return pages


def load_reference_pages(
    path: Path,
    cache_key: str | None = None,
    *,
    force: bool = False,
) -> list[tuple[int, str]]:
    """Load a reference file as (page_number, text) pairs. PDFs are cached under Scripts/_pdf_cache/."""
    path = path.resolve()
    cache_key = cache_key or cache_key_for(path)
    cache_file = CACHE / f"{cache_key}.txt"
    CACHE.mkdir(exist_ok=True)

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        if not force:
            cached = _read_pdf_cache(cache_file, path)
            if cached is not None:
                return cached

        pages = _extract_pdf_pages(path)
        if pages_have_content(pages):
            _write_pdf_cache(cache_file, pages)
        else:
            cache_file.unlink(missing_ok=True)
        return pages

    if suffix == ".html":
        text = html_to_text(path.read_text(encoding="utf-8", errors="replace"))
        return [(1, text)]

    if suffix == ".md":
        return [(1, path.read_text(encoding="utf-8", errors="replace"))]

    raise ValueError(f"Unsupported reference format: {path}")


def iter_reference_pdfs(root: Path | None = None) -> list[Path]:
    """All PDF files under References/ (sorted, resolved)."""
    root = root or REFERENCES
    return sorted(path.resolve() for path in root.rglob("*.pdf"))


def resolve_reference_path(pdf_arg: str) -> Path:
    """Resolve a filesystem path or citation tag to a file under References/."""
    candidate = Path(pdf_arg)
    if candidate.exists():
        return candidate.resolve()

    registry = parse_reference_registry()
    if pdf_arg in registry:
        path = registry[pdf_arg]
        if path.exists():
            return path.resolve()
        raise FileNotFoundError(f"Reference file missing for tag {pdf_arg!r}: {path}")

    from_base = (BASE / pdf_arg).resolve()
    if from_base.exists():
        return from_base

    raise FileNotFoundError(
        f"Could not resolve {pdf_arg!r} as a path or citation tag. "
        f"Use a file path or a tag from References/README.md (e.g. MVD, SB)."
    )


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

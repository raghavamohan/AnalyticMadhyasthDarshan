#!/usr/bin/env python3
"""Scan citations, map old-to-new PDF pages, and diff updated reference translations.

When an ongoing primary-text translation (such as JVD, AVD, SB, AA, or KD) is
updated from Google Docs or a translator's latest draft, pagination and English
wording often shift as multi-version peer-review candidates are consolidated.

This script automates the comparison and citation audit:
  1. Exports a Google Doc URL/ID to PDF (if `--google-doc` is given) or reads `--new-pdf`.
  2. Resolves or hydrates the previous reference PDF from `References/` or
     `Scripts/_reference_cache/` via `_reference_store.py`.
  3. Scans all `.md` files (`Studies/`, `Applications/`, `Primer/`, `docs/`) and
     `.pptx` slide/notes XML (`ppt/slides/*.xml`, `ppt/notesSlides/*.xml`) for
     citations to the target sigil and extracts every cited page number.
  4. De-wraps Google Docs / Skia single-word line breaks in both Devanagari and
     English text.
  5. Uses k-word shingle overlap (`default k=5`) over Hindi and English tokens to
     map every cited old page to its corresponding page(s) in the updated PDF.
  6. Writes a side-by-side Markdown comparison report (`tmp/<sigil>-translation-diff.md`)
     for fast verification of page shifts and wording changes.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _common import BASE, configure_utf8_stdio, write_text_lf  # noqa: E402
from _reference_store import load_reference_store  # noqa: E402


@dataclass(frozen=True)
class TranslationPreset:
    sigil: str
    repo_path: str
    aliases: tuple[str, ...]


PRESETS: dict[str, TranslationPreset] = {
    "JVD": TranslationPreset(
        sigil="JVD",
        repo_path="References/Madhyasth-Darshan/JVD-Janvad.pdf",
        aliases=("JVD", "Janvad", "Janvād"),
    ),
    "AVD": TranslationPreset(
        sigil="AVD",
        repo_path="References/Madhyasth-Darshan/AVD-Adhyatmvad.docx.pdf",
        aliases=("AVD", "Adhyatmvad", "Adhyātmvād"),
    ),
    "SB": TranslationPreset(
        sigil="SB",
        repo_path="References/Madhyasth-Darshan/SB-Samadhanatmak-Bhautikvad.pdf",
        aliases=("SB", "Samadhanatmak Bhautikvad", "Samādhānātmak Bhautikvād"),
    ),
    "MVD": TranslationPreset(
        sigil="MVD",
        repo_path="References/Madhyasth-Darshan/MVD-Madhyasth-Darshan-Coexistentialism.pdf",
        aliases=("MVD", "Manav Vyavahar Darshan", "Mānav Vyavahār Darśan"),
    ),
    "JV": TranslationPreset(
        sigil="JV",
        repo_path="References/Madhyasth-Darshan/JV-Jeevan-Vidya-An-Introduction.pdf",
        aliases=("JV", "Jeevan Vidya"),
    ),
    "AA": TranslationPreset(
        sigil="AA",
        repo_path="References/Madhyasth-Darshan/AA-Avartansheel-Arthshastra-English/AA-Avartansheel-Arthshastra-English.pdf",
        aliases=("AA", "Avartansheel Arthshastra"),
    ),
    "KD": TranslationPreset(
        sigil="KD",
        repo_path="References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Karm-Darshan-English.pdf",
        aliases=("KD", "Karm Darshan"),
    ),
}

GOOGLE_DOC_ID_RE = re.compile(r"/document/d/([a-zA-Z0-9_-]+)")
RAW_DOC_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{20,}$")
MAX_RANGE_EXPANSION = 30


@dataclass(frozen=True)
class MarkdownCitation:
    rel_path: str
    line_no: int
    line_text: str
    pages: tuple[int, ...]


@dataclass(frozen=True)
class PptxCitation:
    rel_path: str
    xml_entry: str
    snippet: str
    pages: tuple[int, ...]


def extract_google_doc_id(url_or_id: str) -> str:
    """Extract the Google Docs document ID from a sharing URL or raw ID."""
    cleaned = url_or_id.strip()
    match = GOOGLE_DOC_ID_RE.search(cleaned)
    if match:
        return match.group(1)
    if RAW_DOC_ID_RE.fullmatch(cleaned):
        return cleaned
    raise ValueError(f"Could not extract Google Doc ID from {url_or_id!r}")


def download_google_doc_pdf(url_or_id: str, dest: Path) -> Path:
    """Download a Google Doc as PDF and verify the `%PDF-` magic header."""
    doc_id = extract_google_doc_id(url_or_id)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=pdf"
    req = urllib.request.Request(
        export_url,
        headers={"User-Agent": "AnalyticMadhyasthDarshan-reference-sync/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read()
    if not data.startswith(b"%PDF-"):
        raise ValueError(
            f"Downloaded content from {export_url} is not a valid PDF "
            f"(starts with {data[:32]!r})"
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest


def resolve_previous_pdf(repo_path: str, explicit_old: Path | None = None) -> Path:
    """Resolve the previous reference PDF from explicit path, local tree, or R2 cache."""
    if explicit_old is not None:
        resolved = explicit_old.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Old PDF not found: {resolved}")
        return resolved

    try:
        store = load_reference_store()
        artifact = store.find(repo_path)
    except Exception:
        artifact = None
        store = None

    if store is not None and artifact is not None:
        try:
            return store.resolve(artifact, allow_download=True)
        except ValueError:
            # Local file was already overwritten with the new PDF before manifest sync;
            # fall back to the cached or hydrated manifest copy.
            return store.hydrate(artifact, force=False)

    candidate = (BASE / repo_path).resolve()
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(
        f"Could not resolve previous PDF for {repo_path}; pass --old-pdf explicitly."
    )


def clean_page_text(text: str) -> str:
    """De-wrap Skia/Google Docs word-per-line PDF extraction into readable paragraphs."""
    cleaned = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text or "")
    lines = [line.strip() for line in cleaned.splitlines()]
    paras: list[str] = []
    curr: list[str] = []
    for line in lines:
        if not line:
            if curr:
                paras.append(" ".join(curr))
                curr = []
        else:
            curr.append(line)
    if curr:
        paras.append(" ".join(curr))
    merged = "\n".join(paras)
    merged = re.sub(r"(?<=[\u0900-\u097F।])\n(?=[\u0900-\u097F])", " ", merged)
    merged = re.sub(r"\n([a-zA-Z0-9,\.\(\)\-\'\"\/]+)\n", r" \1 ", merged)
    return merged.strip()


def extract_pages_for_sigil(text: str, sigil: str) -> tuple[int, ...]:
    """Extract cited page numbers associated with *sigil* in a line or snippet."""
    escaped = re.escape(sigil)
    patterns = [
        # e.g. "JVD, pp. 168-169" or "JVD, p. 32" or "JVD §3.7, pp. 73-81"
        re.compile(
            rf"\b{escaped}\b[^;\)\n]{{0,40}}?\bpp?\.\s*([0-9,\s–—\-]+)",
            re.IGNORECASE,
        ),
        # Bibliography entries where `**JVD**` heads the line and `(pp. 32, 35, 168-169)` appears later
        re.compile(
            rf"\*\*{escaped}\*\*[^\n]*",
            re.IGNORECASE,
        ),
    ]
    spans: list[str] = []
    for m in patterns[0].finditer(text):
        spans.append(m.group(1))
    if not spans and patterns[1].search(text):
        for pm in re.finditer(r"\bpp?\.\s*([0-9,\s–—\-]+)", text):
            spans.append(pm.group(1))

    pages: set[int] = set()
    for span in spans:
        for token in re.split(r"[,\s]+", span.strip()):
            if not token:
                continue
            range_match = re.fullmatch(r"(\d+)[–—\-](\d+)", token)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                if 0 < start <= end:
                    if end - start <= MAX_RANGE_EXPANSION:
                        pages.update(range(start, end + 1))
                    else:
                        pages.add(start)
                        pages.add(end)
                continue
            num_match = re.fullmatch(r"(\d+)", token)
            if num_match:
                val = int(num_match.group(1))
                if val > 0:
                    pages.add(val)
    return tuple(sorted(pages))


def scan_repository_citations(
    sigil: str,
    aliases: tuple[str, ...] = (),
    *,
    root: Path = BASE,
) -> tuple[list[MarkdownCitation], list[PptxCitation], list[int]]:
    """Scan Markdown and PPTX files for citations to *sigil* or *aliases*."""
    terms = tuple(dict.fromkeys([sigil, *aliases]))
    term_re = re.compile(
        "|".join(
            rf"\b{re.escape(t)}\b" if re.fullmatch(r"\w+", t) else re.escape(t)
            for t in terms
        )
    )

    md_roots = ("Studies", "Applications", "Primer", "docs")
    md_citations: list[MarkdownCitation] = []
    all_pages: set[int] = set()

    for folder in md_roots:
        dir_path = root / folder
        if not dir_path.is_dir():
            continue
        for md_path in sorted(dir_path.rglob("*.md")):
            rel = md_path.relative_to(root).as_posix()
            text = md_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(text.splitlines(), start=1):
                if not term_re.search(line):
                    continue
                pages = extract_pages_for_sigil(line, sigil)
                all_pages.update(pages)
                md_citations.append(
                    MarkdownCitation(
                        rel_path=rel,
                        line_no=idx,
                        line_text=line.strip(),
                        pages=pages,
                    )
                )

    pptx_roots = ("Studies", "Applications")
    pptx_citations: list[PptxCitation] = []
    for folder in pptx_roots:
        dir_path = root / folder
        if not dir_path.is_dir():
            continue
        for pptx_path in sorted(dir_path.rglob("*.pptx")):
            rel = pptx_path.relative_to(root).as_posix()
            try:
                with zipfile.ZipFile(pptx_path, "r") as zf:
                    for name in sorted(zf.namelist()):
                        if not name.endswith(".xml") or not (
                            name.startswith("ppt/slides/")
                            or name.startswith("ppt/notesSlides/")
                        ):
                            continue
                        raw_xml = zf.read(name).decode("utf-8", errors="ignore")
                        if not term_re.search(raw_xml):
                            continue
                        root_el = ET.fromstring(raw_xml)
                        texts = [
                            el.text
                            for el in root_el.iter()
                            if el.tag.endswith("}t") and el.text
                        ]
                        joined = " | ".join(texts)
                        for m in re.finditer(
                            rf".{{0,90}}(?:{'|'.join(re.escape(t) for t in terms)}).{{0,90}}",
                            joined,
                        ):
                            snippet = m.group(0).strip()
                            pages = extract_pages_for_sigil(snippet, sigil)
                            all_pages.update(pages)
                            pptx_citations.append(
                                PptxCitation(
                                    rel_path=rel,
                                    xml_entry=name,
                                    snippet=snippet,
                                    pages=pages,
                                )
                            )
            except zipfile.BadZipFile:
                continue

    return md_citations, pptx_citations, sorted(all_pages)


def page_shingles(text: str, shingle_size: int = 5) -> set[tuple[str, ...]]:
    """Build a set of lowercase k-word shingles from a page's text."""
    words = re.findall(r"\w+", text.lower())
    if len(words) < shingle_size:
        return {tuple(words)} if words else set()
    return {
        tuple(words[i : i + shingle_size])
        for i in range(len(words) - shingle_size + 1)
    }


def map_pages_by_shingles(
    old_pages: list[str],
    new_pages: list[str],
    target_old_pages: list[int],
    *,
    shingle_size: int = 5,
    top_k: int = 3,
) -> dict[int, list[tuple[int, int]]]:
    """Map 1-based old page numbers to top-matching `(new_page, overlap_count)` pairs."""
    new_shingle_sets = [page_shingles(text, shingle_size) for text in new_pages]
    mapping: dict[int, list[tuple[int, int]]] = {}
    for old_p in target_old_pages:
        if old_p < 1 or old_p > len(old_pages):
            mapping[old_p] = []
            continue
        old_sh = page_shingles(old_pages[old_p - 1], shingle_size)
        if not old_sh:
            mapping[old_p] = []
            continue
        scores: list[tuple[int, int]] = []
        for idx, new_sh in enumerate(new_shingle_sets):
            overlap = len(old_sh & new_sh)
            if overlap > 0:
                scores.append((idx + 1, overlap))
        scores.sort(key=lambda item: (-item[1], abs(item[0] - old_p)))
        mapping[old_p] = scores[:top_k]
    return mapping


def render_comparison_report(
    *,
    sigil: str,
    old_pdf: Path,
    new_pdf: Path,
    old_pages: list[str],
    new_pages: list[str],
    md_citations: list[MarkdownCitation],
    pptx_citations: list[PptxCitation],
    target_pages: list[int],
    mapping: dict[int, list[tuple[int, int]]],
) -> str:
    """Render a side-by-side Markdown diff report for all cited pages."""
    lines: list[str] = [
        f"# Reference Translation Sync Report: `{sigil}`",
        "",
        f"- **Previous PDF:** `{old_pdf}` ({len(old_pages)} pages)",
        f"- **Updated PDF:** `{new_pdf}` ({len(new_pages)} pages)",
        f"- **Cited pages audited:** {len(target_pages)} ({', '.join(str(p) for p in target_pages) or 'none'})",
        "",
        "## 1. Title / Status Page Comparison (Page 1)",
        "",
        "### [OLD p. 1]",
        "```text",
        old_pages[0][:1200] if old_pages else "(empty)",
        "```",
        "",
        "### [NEW p. 1]",
        "```text",
        new_pages[0][:1200] if new_pages else "(empty)",
        "```",
        "",
        "## 2. Old -> New Page Mapping Summary",
        "",
        "| Old Page | Best New Page | Top Candidates `(page, shingle_overlap)` | Status |",
        "|---:|---:|---|---|",
    ]

    for old_p in target_pages:
        candidates = mapping.get(old_p, [])
        if not candidates:
            best_str = "—"
            cand_str = "No match (out of range or empty)"
            status = "UNMATCHED"
        else:
            best_new, best_ov = candidates[0]
            best_str = f"**p. {best_new}** (`ov={best_ov}`)"
            cand_str = ", ".join(f"`p.{p}` ({ov})" for p, ov in candidates)
            status = "UNCHANGED" if best_new == old_p else f"SHIFTED (`{old_p} -> {best_new}`)"
        lines.append(f"| p. {old_p} | {best_str} | {cand_str} | {status} |")

    lines.extend(
        [
            "",
            "## 3. Repository Citation Inventory",
            "",
            f"### Markdown citations ({len(md_citations)})",
            "",
        ]
    )
    for cite in md_citations:
        pg = f" [pages: {', '.join(str(p) for p in cite.pages)}]" if cite.pages else ""
        lines.append(f"- `{cite.rel_path}:{cite.line_no}`{pg}: {cite.line_text}")

    lines.extend(
        [
            "",
            f"### PowerPoint (`.pptx`) citations ({len(pptx_citations)})",
            "",
        ]
    )
    for pcite in pptx_citations:
        pg = f" [pages: {', '.join(str(p) for p in pcite.pages)}]" if pcite.pages else ""
        lines.append(f"- `{pcite.rel_path}` (`{pcite.xml_entry}`){pg}: `{pcite.snippet}`")

    lines.extend(
        [
            "",
            "## 4. Side-by-Side Cited Page Text (`[OLD]` vs `[NEW]`)",
            "",
        ]
    )
    for old_p in target_pages:
        if old_p < 1 or old_p > len(old_pages):
            continue
        candidates = mapping.get(old_p, [])
        lines.append(f"### Old Page {old_p} -> {candidates}")
        lines.append("")
        lines.append(f"#### `[OLD p. {old_p}]`")
        lines.append(old_pages[old_p - 1])
        lines.append("")
        for idx, (new_p, ov) in enumerate(candidates[:2]):
            if idx == 0 or ov >= 15:
                lines.append(f"#### `[NEW p. {new_p} (overlap={ov})]`")
                lines.append(new_pages[new_p - 1])
                lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def load_pdf_pages(pdf_path: Path) -> list[str]:
    """Read and de-wrap all pages of a PDF using `pypdf`."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    return [clean_page_text(page.extract_text() or "") for page in reader.pages]


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sigil",
        required=True,
        help="Short source sigil (e.g. JVD, AVD, SB, AA, KD, MVD, JV).",
    )
    parser.add_argument(
        "--reference-path",
        help="Repository-relative path under References/ (defaults to preset for --sigil).",
    )
    parser.add_argument(
        "--new-pdf",
        type=Path,
        help="Path to the updated PDF file.",
    )
    parser.add_argument(
        "--google-doc",
        help="Google Docs URL or document ID to export as the updated PDF.",
    )
    parser.add_argument(
        "--old-pdf",
        type=Path,
        help="Explicit path to the previous PDF (defaults to resolving via _reference_store.py).",
    )
    parser.add_argument(
        "--pages",
        help="Optional comma-separated extra old page numbers to inspect in addition to auto-discovered citations.",
    )
    parser.add_argument(
        "--shingle-size",
        type=int,
        default=5,
        help="Word shingle length for page matching (default: 5).",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        help="Output path for the Markdown comparison report (default: tmp/<sigil>-translation-diff.md).",
    )
    args = parser.parse_args(argv)

    sigil = args.sigil.strip().upper()
    preset = PRESETS.get(sigil)
    repo_path = args.reference_path or (preset.repo_path if preset else "")
    if not repo_path:
        parser.error(
            f"Unknown sigil {sigil!r}; pass --reference-path explicitly "
            f"(known presets: {', '.join( sorted(PRESETS) )})."
        )
    aliases = preset.aliases if preset else (sigil,)

    if not args.new_pdf and not args.google_doc:
        parser.error("Provide either --new-pdf <path> or --google-doc <url-or-id>.")

    old_pdf = resolve_previous_pdf(repo_path, args.old_pdf)

    if args.google_doc:
        dest_new = args.new_pdf or (BASE / "tmp" / f"{sigil}-updated.pdf")
        print(f"Downloading Google Doc export to {dest_new}...")
        new_pdf = download_google_doc_pdf(args.google_doc, dest_new)
    else:
        new_pdf = args.new_pdf.resolve()
        if not new_pdf.is_file():
            raise FileNotFoundError(f"Updated PDF not found: {new_pdf}")

    print(f"Scanning repository (.md and .pptx) for {sigil} citations...")
    md_citations, pptx_citations, target_pages = scan_repository_citations(
        sigil, aliases, root=BASE
    )
    if args.pages:
        extra = extract_pages_for_sigil(f"{sigil}, pp. {args.pages}", sigil)
        target_pages = sorted(set(target_pages) | set(extra))

    print(f"Extracting text from old PDF ({old_pdf}) and new PDF ({new_pdf})...")
    old_pages = load_pdf_pages(old_pdf)
    new_pages = load_pdf_pages(new_pdf)
    print(f"  Old PDF pages: {len(old_pages)}")
    print(f"  New PDF pages: {len(new_pages)}")
    print(f"  Markdown citation lines: {len(md_citations)}")
    print(f"  PPTX citation snippets:  {len(pptx_citations)}")
    print(f"  Distinct cited pages:    {target_pages}")

    mapping = map_pages_by_shingles(
        old_pages,
        new_pages,
        target_pages,
        shingle_size=args.shingle_size,
    )

    print("\n=== OLD -> NEW PAGE MAP ===")
    for old_p in target_pages:
        candidates = mapping.get(old_p, [])
        if not candidates:
            print(f"  Old p.{old_p:3d} -> UNMATCHED")
        else:
            best_new, best_ov = candidates[0]
            flag = "==" if best_new == old_p else "->"
            print(f"  Old p.{old_p:3d} {flag} New p.{best_new:3d} (overlap={best_ov}) | top={candidates}")

    report_path = args.output_report or (BASE / "tmp" / f"{sigil.lower()}-translation-diff.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_text = render_comparison_report(
        sigil=sigil,
        old_pdf=old_pdf,
        new_pdf=new_pdf,
        old_pages=old_pages,
        new_pages=new_pages,
        md_citations=md_citations,
        pptx_citations=pptx_citations,
        target_pages=target_pages,
        mapping=mapping,
    )
    write_text_lf(report_path, report_text)
    print(f"\nWrote side-by-side comparison report to: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

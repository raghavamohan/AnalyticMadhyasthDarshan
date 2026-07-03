"""Layout-aware PDF to markdown conversion for study import.

Uses PyMuPDF for block/span structure and pdfplumber for tables. Tuned for
text-native scholarly PDFs; scanned documents without a text layer fail fast.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import fitz
import pdfplumber

from _common import ligature_norm

BlockKind = Literal["heading", "paragraph", "bullet", "numbered", "blockquote", "table"]

BULLET_CHARS = frozenset("•◦·▪▫‣⁃")
BULLET_PREFIX_RE = re.compile(r"^[\u2022\u25e6\u00b7\u25aa\u25ab\u2023\u2043\-\*]\s+")
NUMBERED_PREFIX_RE = re.compile(r"^(\d+)[.)]\s+")
HEADING_KEYWORDS = (
    "introduction",
    "references",
    "standpoint and scope",
    "open problems",
    "conclusion",
    "summary",
    "abstract",
)
DEFAULT_MIN_CHARS = 200


@dataclass
class ConversionReport:
    pages_processed: int = 0
    headings_found: int = 0
    tables_found: int = 0
    lists_found: int = 0
    blockquotes_found: int = 0
    low_confidence_blocks: int = 0
    empty_pages: int = 0
    total_chars: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pages_processed": self.pages_processed,
            "headings_found": self.headings_found,
            "tables_found": self.tables_found,
            "lists_found": self.lists_found,
            "blockquotes_found": self.blockquotes_found,
            "low_confidence_blocks": self.low_confidence_blocks,
            "empty_pages": self.empty_pages,
            "total_chars": self.total_chars,
            "warnings": list(self.warnings),
        }


@dataclass
class _Span:
    text: str
    size: float
    flags: int
    x0: float
    y0: float


@dataclass
class _Block:
    text: str
    x0: float
    y0: float
    y1: float
    size: float
    italic_ratio: float
    bold_ratio: float
    page: int
    kind: BlockKind = "paragraph"
    heading_level: int = 0
    confidence: float = 1.0
    table_md: str = ""


def _normalize_line(text: str) -> str:
    text = ligature_norm(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _span_is_bold(flags: int) -> bool:
    return bool(flags & 2**4)


def _span_is_italic(flags: int) -> bool:
    return bool(flags & 2**1)


def _extract_blocks(doc: fitz.Document) -> list[_Block]:
    blocks: list[_Block] = []
    for page_index, page in enumerate(doc, start=1):
        payload = page.get_text("dict")
        for block in payload.get("blocks", []):
            if block.get("type") != 0:
                continue
            spans: list[_Span] = []
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if not text.strip():
                        continue
                    spans.append(
                        _Span(
                            text=text,
                            size=float(span.get("size", 0)),
                            flags=int(span.get("flags", 0)),
                            x0=float(span.get("bbox", [0, 0, 0, 0])[0]),
                            y0=float(span.get("bbox", [0, 0, 0, 0])[1]),
                        )
                    )
            if not spans:
                continue
            text = _normalize_line("".join(s.text for s in spans))
            if not text:
                continue
            sizes = [s.size for s in spans if s.size > 0]
            avg_size = sum(sizes) / len(sizes) if sizes else 0.0
            char_weights = [max(len(s.text), 1) for s in spans]
            italic_ratio = sum(
                w for s, w in zip(spans, char_weights) if _span_is_italic(s.flags)
            ) / max(sum(char_weights), 1)
            bold_ratio = sum(
                w for s, w in zip(spans, char_weights) if _span_is_bold(s.flags)
            ) / max(sum(char_weights), 1)
            bbox = block.get("bbox", [0, 0, 0, 0])
            blocks.append(
                _Block(
                    text=text,
                    x0=float(bbox[0]),
                    y0=float(bbox[1]),
                    y1=float(bbox[3]),
                    size=avg_size,
                    italic_ratio=italic_ratio,
                    bold_ratio=bold_ratio,
                    page=page_index,
                )
            )
    blocks.sort(key=lambda b: (b.page, b.y0, b.x0))
    return blocks


def _body_font_size(blocks: list[_Block]) -> float:
    sizes = [round(b.size, 1) for b in blocks if b.size > 0 and len(b.text) > 40]
    if not sizes:
        sizes = [round(b.size, 1) for b in blocks if b.size > 0]
    if not sizes:
        return 11.0
    return Counter(sizes).most_common(1)[0][0]


def _median_body_x0(blocks: list[_Block]) -> float:
    xs = sorted(b.x0 for b in blocks if b.kind == "paragraph" and len(b.text) > 40)
    if not xs:
        xs = sorted(b.x0 for b in blocks)
    if not xs:
        return 0.0
    mid = len(xs) // 2
    return xs[mid] if len(xs) % 2 else (xs[mid - 1] + xs[mid]) / 2


def _heading_level(size: float, body_size: float) -> int:
    if body_size <= 0:
        return 0
    ratio = size / body_size
    if ratio >= 1.55:
        return 1
    if ratio >= 1.28:
        return 2
    if ratio >= 1.12:
        return 3
    return 0


def _looks_like_heading_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped or len(stripped) > 120:
        return False
    if stripped.endswith("."):
        return False
    lower = stripped.lower()
    if lower in HEADING_KEYWORDS:
        return True
    if re.match(r"^(\d+\.)+\s+\S", stripped):
        return True
    if re.match(r"^\d+\.\s+[A-Z]", stripped):
        return True
    if stripped.isupper() and len(stripped.split()) <= 8:
        return True
    return False


def _classify_blocks(blocks: list[_Block], report: ConversionReport) -> None:
    body_size = _body_font_size(blocks)
    median_x0 = _median_body_x0(blocks)

    for block in blocks:
        text = block.text
        stripped = text.strip()

        if BULLET_PREFIX_RE.match(stripped) or (
            stripped and stripped[0] in BULLET_CHARS
        ):
            block.kind = "bullet"
            report.lists_found += 1
            continue

        numbered = NUMBERED_PREFIX_RE.match(stripped)
        if numbered:
            block.kind = "numbered"
            report.lists_found += 1
            continue

        indent = block.x0 - median_x0
        if indent > 18 and (block.italic_ratio >= 0.55 or stripped.startswith('"')):
            block.kind = "blockquote"
            report.blockquotes_found += 1
            continue

        level = _heading_level(block.size, body_size)
        if level and (_looks_like_heading_text(stripped) or block.bold_ratio >= 0.6):
            block.kind = "heading"
            block.heading_level = level
            report.headings_found += 1
            continue

        if _looks_like_heading_text(stripped) and len(stripped.split()) <= 14:
            block.kind = "heading"
            block.heading_level = max(level, 2) or 2
            report.headings_found += 1
            continue

        if level >= 2 and len(stripped) < 90 and block.bold_ratio >= 0.4:
            block.kind = "heading"
            block.heading_level = level
            report.headings_found += 1
            continue

        block.kind = "paragraph"
        if len(stripped) < 25 and block.size > body_size * 1.05:
            block.confidence = 0.5
            report.low_confidence_blocks += 1


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _table_to_markdown(table: list[list[str | None]]) -> str:
    if not table:
        return ""
    rows = [[_escape_table_cell(cell or "") for cell in row] for row in table if row]
    rows = [row for row in rows if any(cell for cell in row)]
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    header = normalized[0]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in normalized[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _extract_tables(
    pdf_path: Path,
    report: ConversionReport,
) -> list[tuple[int, float, float, float, float, str]]:
    """Return (page, x0, y0, x1, y1, markdown) for each detected table."""
    tables: list[tuple[int, float, float, float, float, str]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            try:
                found = page.find_tables() or []
            except Exception:
                found = []
            for table in found:
                data = table.extract()
                md = _table_to_markdown(data or [])
                if not md:
                    continue
                bbox = table.bbox
                tables.append((page_index, bbox[0], bbox[1], bbox[2], bbox[3], md))
                report.tables_found += 1
    return tables


def _block_in_bbox(block: _Block, x0: float, y0: float, x1: float, y1: float) -> bool:
    cx = (block.x0 + block.x0 + 40) / 2
    cy = (block.y0 + block.y1) / 2
    return x0 <= cx <= x1 and y0 <= cy <= y1


def _strip_bullet(text: str) -> str:
    text = BULLET_PREFIX_RE.sub("", text.strip())
    if text and text[0] in BULLET_CHARS:
        text = text[1:].lstrip()
    return text.strip()


def _strip_numbered(text: str) -> str:
    return NUMBERED_PREFIX_RE.sub("", text.strip(), count=1)


def _emit_block_markdown(block: _Block) -> str:
    if block.kind == "table":
        return block.table_md

    text = block.text.strip()
    if block.kind == "bullet":
        return f"- {_strip_bullet(text)}"
    if block.kind == "numbered":
        return f"1. {_strip_numbered(text)}"
    if block.kind == "blockquote":
        cleaned = text.strip('"').strip()
        return f"> {cleaned}"
    if block.kind == "heading":
        level = min(max(block.heading_level, 1), 3)
        heading = re.sub(r"^\d+(\.\d+)*\s+", "", text).strip()
        return f"{'#' * level} {heading}"
    return text


def _merge_page_items(
    blocks: list[_Block],
    tables: list[tuple[int, float, float, float, float, str]],
    page: int,
) -> list[_Block | tuple[str, float]]:
    page_blocks = [b for b in blocks if b.page == page]
    page_tables = [t for t in tables if t[0] == page]
    items: list[tuple[float, int, _Block | str]] = []

    for block in page_blocks:
        inside_table = any(
            _block_in_bbox(block, t[1], t[2], t[3], t[4]) for t in page_tables
        )
        if inside_table:
            continue
        items.append((block.y0, 0, block))

    for table in page_tables:
        _, x0, y0, x1, y1, md = table
        table_block = _Block(
            text="",
            x0=x0,
            y0=y0,
            y1=y1,
            size=0,
            italic_ratio=0,
            bold_ratio=0,
            page=page,
            kind="table",
            table_md=md,
        )
        items.append((y0, 1, table_block))

    items.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in items]


def _postprocess_markdown(md: str, report: ConversionReport) -> str:
    lines = md.splitlines()
    out: list[str] = []
    prev_blank = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not prev_blank:
                out.append("")
            prev_blank = True
            continue
        prev_blank = False
        out.append(line.rstrip())

    result = "\n".join(out).strip()
    if not re.search(r"^##\s+References\b", result, re.MULTILINE | re.IGNORECASE):
        report.warnings.append(
            "No '## References' heading detected; placeholder section appended."
        )
        result += (
            "\n\n## References\n\n"
            "- *(Review and add bibliography entries — link to `../References/` "
            "where available, or to the original publisher URL.)*\n"
        )
    if not re.search(r"^##\s+Standpoint and scope\b", result, re.MULTILINE | re.IGNORECASE):
        report.warnings.append(
            "No '## Standpoint and scope' section detected; add manually for topical studies."
        )
    return result + "\n"


def convert_pdf_to_markdown(
    pdf_path: Path,
    *,
    min_chars: int = DEFAULT_MIN_CHARS,
) -> tuple[str, ConversionReport]:
    """Convert a text-native PDF to markdown body text."""
    pdf_path = pdf_path.resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    report = ConversionReport()
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise ValueError(f"Could not read PDF: {exc}") from exc

    try:
        report.pages_processed = doc.page_count
        blocks = _extract_blocks(doc)
        tables = _extract_tables(pdf_path, report)
        _classify_blocks(blocks, report)

        emitted: list[str] = []
        for page in range(1, report.pages_processed + 1):
            page_items = _merge_page_items(blocks, tables, page)
            if not page_items:
                report.empty_pages += 1
                continue
            for item in page_items:
                if isinstance(item, _Block):
                    emitted.append(_emit_block_markdown(item))
                else:
                    emitted.append(item)

        md = "\n\n".join(chunk for chunk in emitted if chunk.strip())
        md = _postprocess_markdown(md, report)
        report.total_chars = len(re.sub(r"\s+", "", md))

        if report.total_chars < min_chars:
            raise ValueError(
                f"PDF text extraction yielded only {report.total_chars} characters "
                f"(minimum {min_chars}). The file may be scanned, image-only, or "
                "password-protected."
            )
        if report.empty_pages == report.pages_processed:
            raise ValueError(
                "No extractable text found in any page. The PDF may be scanned "
                "or image-only."
            )
        return md, report
    finally:
        doc.close()

"""Shared catalog, timestamp, and PDF helpers for add/remove study scripts."""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from zoneinfo import ZoneInfo

from _common import (
    BASE,
    REFERENCES,
    SCRIPTS,
    STUDIES,
    application_discussion_href,
    application_html_href,
    application_pdf_href,
    iter_study_md_paths,
    known_study_slugs,
    study_discussion_href,
    study_html_href,
    study_md,
    study_pdf_href,
    study_pdf_ref_path,
)

IST = ZoneInfo("Asia/Kolkata")

TOPICAL_CATALOG_START = "<!-- studies-catalog -->"
TOPICAL_CATALOG_END = "<!-- /studies-catalog -->"
FORMAL_CATALOG_START = "<!-- formal-studies-catalog -->"
FORMAL_CATALOG_END = "<!-- /formal-studies-catalog -->"
APPLIED_CATALOG_START = "<!-- applied-studies-catalog -->"
APPLIED_CATALOG_END = "<!-- /applied-studies-catalog -->"
REFERENCES_CATALOG_START = "<!-- studies-catalog -->"
REFERENCES_CATALOG_END = "<!-- /studies-catalog -->"

STUDIES_README_TOPICAL_HEADER = (
    "| Document | Category | Description | Status |\n"
    "|----------|----------|-------------|--------|"
)
STUDIES_README_FORMAL_HEADER = (
    "| Document | Formal Focus | Description | Status |\n"
    "|----------|--------------|-------------|--------|"
)
STUDIES_README_APPLIED_HEADER = (
    "| Document | Applied Focus | Description | Status |\n"
    "|----------|---------------|-------------|--------|"
)
REFERENCES_README_TABLE_HEADER = "| Paper | Primary tags |\n|-------|----------------|"

MONTH_FULL_TO_ABBR = {
    "January": "Jan",
    "February": "Feb",
    "March": "Mar",
    "April": "Apr",
    "May": "May",
    "June": "Jun",
    "July": "Jul",
    "August": "Aug",
    "September": "Sep",
    "October": "Oct",
    "November": "Nov",
    "December": "Dec",
}
MONTH_ABBR_TO_FULL = {v: k for k, v in MONTH_FULL_TO_ABBR.items()}

EDITED_ON_RE = re.compile(
    r"^\*\*Edited on:\*\*\s+(.+?)\s+IST\s*$",
    re.MULTILINE,
)
STATUS_MD_RE = re.compile(
    r"^\*\*Status:\*\*\s+(Draft|Released)\s*$",
    re.MULTILINE,
)
CATALOG_TIMESTAMP_RE = re.compile(
    r"Last updated on:\s+(\w+)\s+(\d+),\s+(\d{4}),\s+(\d+:\d+\s+[AP]M)\s+IST"
)
ONGOING_DESC_PREFIX_RE = re.compile(r"^Ongoing\.+\s*", re.IGNORECASE)
CATALOG_JSON_SCRIPT_RE = re.compile(
    r'<script\s+type="application/json"\s+id="([^"]+)"\s*>\s*(.*?)\s*</script>',
    re.DOTALL,
)


class StudyStatus(str, Enum):
    ONGOING = "ongoing"
    DRAFT = "draft"
    RELEASED = "released"


class StudyTable(str, Enum):
    TOPICAL = "topical"
    FORMAL = "formal"
    APPLIED = "applied"


CATALOG_TABLES = (
    StudyTable.TOPICAL,
    StudyTable.FORMAL,
    StudyTable.APPLIED,
)


@dataclass
class StudyRow:
    slug: str
    category: str
    description: str
    status: StudyStatus
    edited_at: datetime | None = None
    table: StudyTable = StudyTable.TOPICAL
    pdf_href: str | None = None

    @property
    def has_pdf(self) -> bool:
        return self.status != StudyStatus.ONGOING


def catalog_markers(table: StudyTable) -> tuple[str, str]:
    if table == StudyTable.FORMAL:
        return FORMAL_CATALOG_START, FORMAL_CATALOG_END
    if table == StudyTable.APPLIED:
        return APPLIED_CATALOG_START, APPLIED_CATALOG_END
    return TOPICAL_CATALOG_START, TOPICAL_CATALOG_END


def now_ist() -> datetime:
    return datetime.now(IST).replace(second=0, microsecond=0)


def format_edited_on_md(dt: datetime) -> str:
    month = dt.strftime("%B")
    day = dt.day
    year = dt.year
    time_part = dt.strftime("%I:%M %p").lstrip("0")
    return f"**Edited on:** {month} {day}, {year}, {time_part} IST"


def format_status_catalog(dt: datetime | None, status: StudyStatus) -> str:
    if status == StudyStatus.ONGOING:
        return "Ongoing"
    label = "Draft" if status == StudyStatus.DRAFT else "Released"
    if dt is None:
        raise ValueError(f"{label} status requires edited_at timestamp.")
    month = MONTH_FULL_TO_ABBR[dt.strftime("%B")]
    day = dt.day
    year = dt.year
    time_part = dt.strftime("%I:%M %p").lstrip("0")
    return f"{label}<br>Last updated on: {month} {day}, {year}, {time_part} IST"


def parse_edited_on(md_text: str) -> datetime | None:
    match = EDITED_ON_RE.search(md_text)
    if not match:
        return None
    return parse_timestamp_text(match.group(1).strip())


def parse_timestamp_text(text: str) -> datetime | None:
    """Parse 'June 17, 2026, 1:13 PM' or 'Jun 17, 2026, 1:13 PM'."""
    match = re.match(
        r"^(\w+)\s+(\d+),\s+(\d{4}),\s+(\d+:\d+\s+[AP]M)$",
        text.strip(),
    )
    if not match:
        return None
    month_token, day_s, year_s, time_s = match.groups()
    month_name = MONTH_ABBR_TO_FULL.get(month_token, month_token)
    try:
        dt = datetime.strptime(
            f"{month_name} {day_s} {year_s} {time_s}",
            "%B %d %Y %I:%M %p",
        )
    except ValueError:
        return None
    return dt.replace(tzinfo=IST)


def parse_status_cell(status_cell: str) -> tuple[StudyStatus, datetime | None]:
    text = status_cell.strip()
    if text == "Ongoing":
        return StudyStatus.ONGOING, None
    if text.startswith("Draft"):
        ts = _parse_catalog_timestamp(text)
        return StudyStatus.DRAFT, ts
    if text.startswith("Released"):
        ts = _parse_catalog_timestamp(text)
        return StudyStatus.RELEASED, ts
    raise ValueError(f"Unrecognized status cell: {text!r}")


def _parse_catalog_timestamp(text: str) -> datetime | None:
    match = CATALOG_TIMESTAMP_RE.search(text.replace("<br>", " "))
    if not match:
        return None
    month_abbr, day_s, year_s, time_s = match.groups()
    month_name = MONTH_ABBR_TO_FULL.get(month_abbr, month_abbr)
    try:
        dt = datetime.strptime(
            f"{month_name} {day_s} {year_s} {time_s}",
            "%B %d %Y %I:%M %p",
        )
    except ValueError:
        return None
    return dt.replace(tzinfo=IST)


def set_edited_on(md_text: str, dt: datetime) -> str:
    line = format_edited_on_md(dt)
    if EDITED_ON_RE.search(md_text):
        return EDITED_ON_RE.sub(line, md_text, count=1)
    author_match = re.search(r"^(\*\*Author:\*\*[^\n]*\n)", md_text, re.MULTILINE)
    if not author_match:
        raise ValueError("Could not find **Author:** line in markdown.")
    insert_at = author_match.end()
    return md_text[:insert_at] + "\n" + line + "\n" + md_text[insert_at:]


def format_status_md(status: StudyStatus) -> str:
    if status == StudyStatus.ONGOING:
        raise ValueError("Ongoing studies do not carry a **Status:** field.")
    label = "Draft" if status == StudyStatus.DRAFT else "Released"
    return f"**Status:** {label}"


def parse_status_md(md_text: str) -> StudyStatus | None:
    match = STATUS_MD_RE.search(md_text)
    if not match:
        return None
    return StudyStatus.DRAFT if match.group(1) == "Draft" else StudyStatus.RELEASED


def strip_status_for_pdf(md_text: str) -> str:
    """Remove **Status:** from markdown before PDF rendering (watermark/catalog carry status)."""
    return re.sub(
        r"^\*\*Status:\*\*\s+(?:Draft|Released)\s*\n+",
        "",
        md_text,
        count=1,
        flags=re.MULTILINE,
    )


def set_status_md(md_text: str, status: StudyStatus) -> str:
    line = format_status_md(status)
    if STATUS_MD_RE.search(md_text):
        return STATUS_MD_RE.sub(line, md_text, count=1)
    edited_match = EDITED_ON_RE.search(md_text)
    if edited_match:
        insert_at = edited_match.end()
        suffix = md_text[insert_at:]
        if suffix.startswith("\n"):
            suffix = suffix[1:]
        return md_text[:insert_at] + "\n\n" + line + "\n\n" + suffix
    author_match = re.search(r"^(\*\*Author:\*\*[^\n]*\n)", md_text, re.MULTILINE)
    if not author_match:
        raise ValueError("Could not find **Author:** or **Edited on:** in markdown.")
    insert_at = author_match.end()
    return md_text[:insert_at] + "\n\n" + line + "\n\n" + md_text[insert_at:]


def escape_md_cell(text: str) -> str:
    return text.replace("|", "\\|")


def replace_catalog_block(content: str, start: str, end: str, new_block: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(content):
        raise ValueError(f"Catalog markers {start!r} / {end!r} not found.")
    return pattern.sub(f"{start}\n{new_block}\n{end}", content, count=1)


def extract_catalog_block(content: str, start: str, end: str) -> str:
    match = re.search(
        re.escape(start) + r"(.*?)" + re.escape(end),
        content,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"Catalog markers {start!r} / {end!r} not found.")
    return match.group(1)


def catalog_script_id(table: StudyTable) -> str:
    if table == StudyTable.FORMAL:
        return "catalog-formal"
    if table == StudyTable.APPLIED:
        return "catalog-applied"
    return "catalog-topical"


def catalog_json_filename(table: StudyTable) -> str:
    return f"{catalog_script_id(table)}.json"


def catalog_json_path(table: StudyTable) -> Path:
    return STUDIES / catalog_json_filename(table)


def split_categories(category: str) -> list[str]:
    return [part.strip() for part in category.split(",") if part.strip()]


def normalize_description(description: str, status: StudyStatus) -> str:
    text = description.strip()
    if status == StudyStatus.ONGOING:
        return ONGOING_DESC_PREFIX_RE.sub("", text).strip()
    return text


def format_catalog_updated(dt: datetime) -> str:
    month = MONTH_FULL_TO_ABBR[dt.strftime("%B")]
    day = dt.day
    year = dt.year
    time_part = dt.strftime("%I:%M %p").lstrip("0")
    return f"{month} {day}, {year}, {time_part} IST"


def row_to_catalog_entry(row: StudyRow) -> dict:
    entry: dict = {
        "slug": row.slug,
        "title": display_title(row),
        "category": row.category,
        "categories": split_categories(row.category),
        "description": normalize_description(row.description, row.status),
        "status": row.status.value,
    }
    if row.status != StudyStatus.ONGOING and row.edited_at is not None:
        entry["updated"] = format_catalog_updated(row.edited_at)
    pdf_href = row_pdf_href(row)
    if pdf_href:
        entry["pdf"] = pdf_href
    html_href = row_html_href(row)
    if html_href:
        entry["html"] = html_href
    discussion_href = row_discussion_href(row)
    if discussion_href:
        entry["discussion"] = discussion_href
    return entry


def catalog_entry_to_row(entry: dict, table: StudyTable) -> StudyRow:
    status_raw = entry.get("status", "")
    try:
        status = StudyStatus(status_raw)
    except ValueError as exc:
        raise ValueError(f"Invalid catalog status {status_raw!r}") from exc

    category = entry.get("category", "")
    if not category and entry.get("categories"):
        category = ", ".join(entry["categories"])

    edited_at: datetime | None = None
    updated = entry.get("updated")
    if updated:
        edited_at = parse_timestamp_text(str(updated).replace(" IST", ""))

    return StudyRow(
        slug=str(entry["slug"]),
        category=str(category),
        description=str(entry.get("description", "")),
        status=status,
        edited_at=edited_at,
        table=table,
        pdf_href=entry.get("pdf"),
    )


def catalog_json_payload(rows: list[StudyRow]) -> list[dict]:
    return [row_to_catalog_entry(row) for row in rows]


def serialize_catalog_json_text(rows: list[StudyRow], *, pretty: bool = False) -> str:
    payload = catalog_json_payload(rows)
    if pretty:
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def serialize_catalog_json_block(rows: list[StudyRow], table: StudyTable) -> str:
    script_id = catalog_script_id(table)
    json_text = serialize_catalog_json_text(rows, pretty=True).strip()
    return f'<script type="application/json" id="{script_id}">\n{json_text}\n</script>'


def parse_catalog_json_file(table: StudyTable) -> list[StudyRow]:
    path = catalog_json_path(table)
    if not path.is_file():
        return []
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"Catalog JSON for {table.value} must be a list.")
    return [catalog_entry_to_row(entry, table) for entry in entries]


def write_catalog_json_file(rows: list[StudyRow], table: StudyTable) -> None:
    catalog_json_path(table).write_text(
        serialize_catalog_json_text(rows),
        encoding="utf-8",
    )


def _parse_legacy_html_tr_rows(block: str, table: StudyTable) -> list[StudyRow]:
    rows: list[StudyRow] = []
    for tr_match in re.finditer(r"<tr>\s*(.*?)\s*</tr>", block, re.DOTALL):
        cells = re.findall(r"<td>(.*?)</td>", tr_match.group(1), re.DOTALL)
        if len(cells) != 4:
            continue
        first, category, description, status_raw = cells
        first = first.strip()
        link_match = re.search(
            r'<a href="([^"]+\.pdf)">([^<]+)</a>',
            first,
        )
        if link_match:
            slug = Path(link_match.group(1)).stem
        else:
            em_match = re.search(
                r'<em(?:\s+data-slug="([^"]+)")?>([^<]+)</em>',
                first,
            )
            if not em_match:
                continue
            slug = html.unescape((em_match.group(1) or em_match.group(2)).strip())
        status, edited_at = parse_status_cell(status_raw)
        rows.append(
            StudyRow(
                slug=slug,
                category=html.unescape(re.sub(r"<br\s*/?>", " ", category)).strip(),
                description=html.unescape(
                    re.sub(r"<br\s*/?>", " ", description)
                ).strip(),
                status=status,
                edited_at=edited_at,
                table=table,
            )
        )
    return rows


def parse_catalog_json(content: str, table: StudyTable) -> list[StudyRow]:
    block = extract_catalog_block(content, *catalog_markers(table))
    script_match = CATALOG_JSON_SCRIPT_RE.search(block)
    if script_match:
        raw_json = script_match.group(2).strip()
    elif block.strip().startswith("["):
        raw_json = block.strip()
    else:
        return _parse_legacy_html_tr_rows(block, table)

    entries = json.loads(raw_json)
    if not isinstance(entries, list):
        raise ValueError(f"Catalog JSON for {table.value} must be a list.")
    return [catalog_entry_to_row(entry, table) for entry in entries]


def parse_html_rows(content: str, table: StudyTable) -> list[StudyRow]:
    return parse_catalog_json(content, table)


def parse_md_rows(content: str, table: StudyTable) -> list[StudyRow]:
    block = extract_catalog_block(content, *catalog_markers(table))
    rows: list[StudyRow] = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|--"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) != 4:
            continue
        doc_cell, category, description, status_raw = parts
        link_match = re.match(r"\[([^\]]+)\]\(([^)]+\.(?:pdf|html))\)", doc_cell)
        pdf_href: str | None = None
        if link_match:
            pdf_href = link_match.group(2)
            slug = Path(pdf_href).stem
        elif doc_cell.startswith("*"):
            comment_match = re.search(r"<!--\s*slug:\s*(.+?)\s*-->", doc_cell)
            if comment_match:
                slug = comment_match.group(1).strip()
            else:
                slug = doc_cell.strip().strip("*").strip()
        else:
            continue
        status, edited_at = parse_status_cell(status_raw)
        rows.append(
            StudyRow(
                slug=slug,
                category=category,
                description=description,
                status=status,
                edited_at=edited_at,
                table=table,
                pdf_href=pdf_href,
            )
        )
    return rows


# Words kept lowercase in a title unless they are the first or last word.
_TITLE_SMALL_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "in",
    "into", "nor", "of", "on", "onto", "or", "over", "per", "the",
    "to", "vs", "via", "with",
}

# Explicit display-title overrides for slugs whose automatic derivation is
# not ideal — e.g. internal compounds like "self-sustaining" whose hyphen is
# indistinguishable from a word separator once the slug is split. Keyed by
# slug; anything not listed falls back to slug_to_title().
SLUG_TITLE_OVERRIDES: dict[str, str] = {
    "How-To-Form-Self-Sustaining-Organizations":
        "How to Form Self-Sustaining Organizations",
    "Coexistence-Company-Org-Structure":
        "Coexistence Company — Concrete Organizational Structure",
}


def slug_to_title(slug: str) -> str:
    """Convert a hyphenated directory slug into a human-readable title.

    Splits the slug on hyphens and applies title case, keeping common
    connective words lowercase unless they are the first or last word.
    Tokens that are already deliberately cased (acronyms like "AI",
    mixed-case names like "McKinsey") are preserved as-is.
    """
    words = [w for w in slug.split("-") if w]
    if not words:
        return slug
    last = len(words) - 1
    titled: list[str] = []
    for i, word in enumerate(words):
        lower = word.lower()
        already_cased = word != lower and word != word.capitalize()
        if already_cased:
            titled.append(word)
        elif i not in (0, last) and lower in _TITLE_SMALL_WORDS:
            titled.append(lower)
        else:
            titled.append(word[:1].upper() + word[1:].lower())
    return " ".join(titled)


def display_title(row: StudyRow) -> str:
    """Human-readable title for a row: explicit override, else derived."""
    return SLUG_TITLE_OVERRIDES.get(row.slug) or slug_to_title(row.slug)


def row_pdf_href(row: StudyRow) -> str | None:
    if row.pdf_href:
        return row.pdf_href
    if row.has_pdf:
        if row.table == StudyTable.APPLIED:
            return application_pdf_href(row.slug)
        return study_pdf_href(row.slug)
    return None


def row_html_href(row: StudyRow) -> str | None:
    if not row.has_pdf:
        return None
    if row.table == StudyTable.APPLIED:
        return application_html_href(row.slug)
    return study_html_href(row.slug)


def row_discussion_href(row: StudyRow) -> str | None:
    if row.table == StudyTable.APPLIED:
        return application_discussion_href(row.slug)
    return study_discussion_href(row.slug)


def serialize_md_row(row: StudyRow) -> str:
    status_cell = format_status_catalog(row.edited_at, row.status)
    title = display_title(row)
    description = normalize_description(row.description, row.status)
    href = row_html_href(row) or row_pdf_href(row)
    discuss_href = row_discussion_href(row)
    if href:
        doc_cell = f"[{title}]({href})"
        if discuss_href:
            doc_cell += f" · [Discuss]({discuss_href})"
    else:
        doc_cell = f"*{title}* <!-- slug: {row.slug} -->"
        if discuss_href:
            doc_cell = f"*{title}* · [Discuss]({discuss_href}) <!-- slug: {row.slug} -->"
    return (
        f"| {doc_cell} | {escape_md_cell(row.category)} | "
        f"{escape_md_cell(description)} | {status_cell} |"
    )


def serialize_md_rows(rows: list[StudyRow], table: StudyTable) -> str:
    if table == StudyTable.FORMAL:
        header = STUDIES_README_FORMAL_HEADER
    elif table == StudyTable.APPLIED:
        header = STUDIES_README_APPLIED_HEADER
    else:
        header = STUDIES_README_TOPICAL_HEADER
    return header + "\n" + "\n".join(serialize_md_row(row) for row in rows)


def upsert_study_row(rows: list[StudyRow], new_row: StudyRow) -> list[StudyRow]:
    for index, row in enumerate(rows):
        if row.slug == new_row.slug:
            updated = list(rows)
            updated[index] = new_row
            return updated
    return rows + [new_row]


def remove_study_row(rows: list[StudyRow], slug: str) -> list[StudyRow]:
    return [row for row in rows if row.slug != slug]


def find_study_table(slug: str) -> StudyTable | None:
    for table in CATALOG_TABLES:
        if any(row.slug == slug for row in load_catalog_rows(table)):
            return table
    return None


def load_catalog_rows(table: StudyTable) -> list[StudyRow]:
    rows = parse_catalog_json_file(table)
    if rows:
        return rows
    index_path = STUDIES / "index.html"
    if index_path.is_file():
        return parse_html_rows(index_path.read_text(encoding="utf-8"), table)
    return []


def get_study_row(slug: str) -> tuple[StudyRow, StudyTable] | None:
    for table in CATALOG_TABLES:
        for row in load_catalog_rows(table):
            if row.slug == slug:
                return row, table
    return None


def write_studies_catalog(rows: list[StudyRow], table: StudyTable) -> None:
    write_catalog_json_file(rows, table)

    readme_path = STUDIES / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")
    start, end = catalog_markers(table)
    readme_path.write_text(
        replace_catalog_block(readme_text, start, end, serialize_md_rows(rows, table)),
        encoding="utf-8",
    )
    write_study_feedback_template()

    from _build_discussion_pages import build_discussion_pages_for_rows

    build_discussion_pages_for_rows(rows)


STUDY_FEEDBACK_TEMPLATE_PATH = BASE / ".github" / "ISSUE_TEMPLATE" / "study-feedback.yml"

STUDY_FEEDBACK_TEMPLATE_HEADER = """name: Study feedback
description: Suggest a correction or comment on an existing study
title: "Study feedback: "
labels:
  - study-feedback
body:
  - type: markdown
    attributes:
      value: |
        Quick feedback on a published study — typos, terminology, citations, or clarity.

        For **new studies** or full rewrites, use [My Submissions](https://analyticmadhyasthdarshan.org/Studies/submit.html) instead.

  - type: dropdown
    id: study
    attributes:
      label: Which study?
      description: Choose the study your comment is about.
      options:
"""


STUDY_FEEDBACK_TEMPLATE_FOOTER = """
    validations:
      required: true

  - type: dropdown
    id: feedback_type
    attributes:
      label: What kind of feedback?
      options:
        - Typo or formatting
        - Terminology / translation
        - Factual or citation
        - Clarity / readability
        - Other
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Your comment
      description: Optional — mention a section (e.g. §2.3) or paste a short quote so we can find the passage.
      placeholder: |
        In §1.7, *sanskar* could use a brief gloss on first use...
    validations:
      required: true
"""


def _yaml_quote(value: str) -> str:
    if re.search(r'[:#"\'\n]', value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _load_feedback_study_titles() -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()
    for filename in ("catalog-topical.json", "catalog-formal.json", "catalog-applied.json"):
        path = STUDIES / filename
        if not path.is_file():
            continue
        entries = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("status") not in {"draft", "released"}:
                continue
            title = str(entry.get("title") or entry.get("slug") or "").strip()
            if title and title not in seen:
                seen.add(title)
                titles.append(title)
    titles.sort(key=str.casefold)
    titles.append("General — catalog or website")
    return titles


def write_study_feedback_template() -> Path:
    """Regenerate GitHub study-feedback issue template from catalog JSON."""
    options = "\n".join(
        f"        - {_yaml_quote(title)}" for title in _load_feedback_study_titles()
    )
    content = STUDY_FEEDBACK_TEMPLATE_HEADER + options + STUDY_FEEDBACK_TEMPLATE_FOOTER
    STUDY_FEEDBACK_TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STUDY_FEEDBACK_TEMPLATE_PATH.write_text(content, encoding="utf-8")
    return STUDY_FEEDBACK_TEMPLATE_PATH


def parse_references_readme_rows(content: str) -> list[tuple[str, str]]:
    block = extract_catalog_block(
        content,
        REFERENCES_CATALOG_START,
        REFERENCES_CATALOG_END,
    )
    rows: list[tuple[str, str]] = []
    for line in block.splitlines():
        match = re.match(
            r"\|\s*\[([^\]]+\.pdf)\]\(../Studies/([^)]+)\)\s*\|\s*(.+?)\s*\|",
            line.strip(),
        )
        if match:
            rows.append((Path(match.group(1)).stem, match.group(3).strip()))
    return rows


def references_readme_row(slug: str, tags: str) -> str:
    return f"| [{slug}.pdf]({study_pdf_ref_path(slug)}) | {escape_md_cell(tags)} |"


def write_references_readme_row(slug: str, tags: str, *, remove: bool = False) -> None:
    ref_readme_path = REFERENCES / "README.md"
    ref_text = ref_readme_path.read_text(encoding="utf-8")
    rows = parse_references_readme_rows(ref_text)
    if remove:
        rows = [(s, t) for s, t in rows if s != slug]
    else:
        rows = [(s, t) for s, t in rows if s != slug]
        rows.append((slug, tags))
    ref_block = REFERENCES_README_TABLE_HEADER + "\n" + "\n".join(
        references_readme_row(s, t) for s, t in rows
    )
    ref_readme_path.write_text(
        replace_catalog_block(
            ref_text,
            REFERENCES_CATALOG_START,
            REFERENCES_CATALOG_END,
            ref_block,
        ),
        encoding="utf-8",
    )


def manifest_row(slug: str, tags: str, status: str = "TBD") -> str:
    return f"| [{slug}.pdf]({study_pdf_ref_path(slug)}) | {escape_md_cell(tags)} | {status} |"


def append_manifest_row(content: str, slug: str, tags: str) -> str:
    pdf_name = f"{slug}.pdf"
    if pdf_name in content:
        return content
    row = manifest_row(slug, tags)
    marker = "\n## By tag"
    if marker not in content:
        raise ValueError("Could not find '## By tag' section in MANIFEST.md")
    return content.replace(marker, f"\n{row}\n{marker}", 1)


def remove_manifest_paper_block(content: str, slug: str) -> str:
    pdf_link = f"[{slug}.pdf]({study_pdf_ref_path(slug)})"
    lines = content.splitlines()
    kept: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if pdf_link in line and line.lstrip().startswith("|"):
            index += 1
            while index < len(lines) and re.match(r"\|\s*\|", lines[index]):
                index += 1
            continue
        kept.append(line)
        index += 1
    trailing = "\n" if content.endswith("\n") else ""
    return "\n".join(kept) + trailing


def verify_catalog_json_sync(table: StudyTable) -> list[str]:
    """Ensure Studies/catalog-*.json matches README.md markdown rows."""
    errors: list[str] = []
    json_path = catalog_json_path(table)
    readme_path = STUDIES / "README.md"
    if not json_path.is_file():
        errors.append(f"Missing catalog file {json_path.name}.")
        return errors

    json_rows = {row.slug: row for row in parse_catalog_json_file(table)}
    md_rows = {
        row.slug: row
        for row in parse_md_rows(readme_path.read_text(encoding="utf-8"), table)
    }

    json_slugs = set(json_rows)
    md_slugs = set(md_rows)
    for slug in sorted(json_slugs - md_slugs):
        errors.append(f"{slug}: in {json_path.name} but missing from README.md.")
    for slug in sorted(md_slugs - json_slugs):
        errors.append(
            f"{slug}: in README.md {table.value} table but missing from {json_path.name}."
        )

    for slug in sorted(json_slugs & md_slugs):
        json_row = json_rows[slug]
        md_row = md_rows[slug]
        if json_row.status != md_row.status:
            errors.append(
                f"{slug}: status mismatch between {json_path.name} ({json_row.status.value}) "
                f"and README.md ({md_row.status.value})."
            )
        if json_row.category != md_row.category:
            errors.append(f"{slug}: category mismatch between {json_path.name} and README.md.")
        json_desc = normalize_description(json_row.description, json_row.status)
        md_desc = normalize_description(md_row.description, md_row.status)
        if json_desc != md_desc:
            errors.append(f"{slug}: description mismatch between {json_path.name} and README.md.")
        if json_row.status in {StudyStatus.DRAFT, StudyStatus.RELEASED}:
            if json_row.edited_at != md_row.edited_at:
                errors.append(
                    f"{slug}: timestamp mismatch between {json_path.name} and README.md."
                )

    return errors


def verify_all_catalog_sync() -> list[str]:
    errors: list[str] = []
    for table in CATALOG_TABLES:
        errors.extend(verify_catalog_json_sync(table))
    return errors


def verify_timestamp_sync(slug: str) -> list[str]:
    errors: list[str] = []
    md_path = study_md(slug)
    if not md_path.exists():
        if find_study_table(slug) is not None:
            errors.append(f"{slug}: catalog entry exists but {md_path.name} is missing.")
        return errors

    md_text = md_path.read_text(encoding="utf-8")
    md_ts = parse_edited_on(md_text)
    md_status = parse_status_md(md_text)
    if md_ts is None:
        errors.append(f"{slug}: missing **Edited on:** in {md_path.name}.")

    table = find_study_table(slug)
    if table is None:
        errors.append(f"{slug}: not found in Studies catalog JSON files.")
        return errors

    readme_path = STUDIES / "README.md"
    json_rows = {row.slug: row for row in load_catalog_rows(table)}
    md_rows = {row.slug: row for row in parse_md_rows(readme_path.read_text(encoding="utf-8"), table)}

    json_row = json_rows.get(slug)
    md_row = md_rows.get(slug)
    if json_row is None:
        errors.append(
            f"{slug}: missing from Studies/{catalog_json_filename(table)} catalog."
        )
    if md_row is None:
        errors.append(f"{slug}: missing from Studies/README.md {table.value} catalog.")

    if json_row and md_row:
        if json_row.status != md_row.status:
            errors.append(
                f"{slug}: status mismatch between {catalog_json_filename(table)} "
                f"({json_row.status.value}) and README.md ({md_row.status.value})."
            )
        if json_row.status in {StudyStatus.DRAFT, StudyStatus.RELEASED}:
            if json_row.edited_at != md_row.edited_at:
                errors.append(
                    f"{slug}: timestamp mismatch between {catalog_json_filename(table)} "
                    "and README.md."
                )
            if md_ts is not None and json_row.edited_at != md_ts:
                errors.append(
                    f"{slug}: catalog timestamp does not match **Edited on:** in markdown."
                )
            if md_status is not None and md_status != json_row.status:
                errors.append(
                    f"{slug}: **Status:** in markdown ({md_status.value}) does not match "
                    f"catalog ({json_row.status.value})."
                )

    return errors


def regenerate_pdf(md_path: Path, status: StudyStatus) -> None:
    if status == StudyStatus.ONGOING:
        return
    from _convert_to_pdf import convert_to_html
    from _verify_pdf_diagrams import verify_study_pdf_diagrams
    from _verify_pdf_fenced_code import verify_study_pdf_fenced_code
    from _verify_pdf_outline import verify_study_pdf_outline
    from _verify_study_svgs import verify_study_svgs

    verify_study_svgs(md_path)

    html_path = md_path.with_suffix(".html")
    pdf_path = md_path.with_suffix(".pdf")
    build_pdf_path = md_path.with_name(f"{md_path.stem}.build.pdf")
    convert_to_html(
        md_path,
        is_draft=status == StudyStatus.DRAFT,
        include_web_chrome=True,
    )
    html_to_pdf_cmd = ["node", str(SCRIPTS / "_html_to_pdf.js"), str(html_path)]
    if status == StudyStatus.DRAFT:
        html_to_pdf_cmd.append("Draft")
    else:
        html_to_pdf_cmd.append("")
    html_to_pdf_cmd.append(str(build_pdf_path))
    subprocess.run(
        html_to_pdf_cmd,
        check=True,
        cwd=SCRIPTS.parent,
    )
    build_pdf_path.replace(pdf_path)
    if build_pdf_path.exists():
        build_pdf_path.unlink()
    verify_study_pdf_diagrams(md_path, pdf_path)
    verify_study_pdf_fenced_code(md_path, pdf_path)
    verify_study_pdf_outline(md_path, pdf_path)

    from _build_discussion_pages import write_discussion_page

    row_info = get_study_row(md_path.parent.name)
    if row_info:
        write_discussion_page(row_info[0])


def title_to_slug(title: str) -> str:
    words = re.findall(r"[\w']+", title.strip())
    if not words:
        raise ValueError("Title must contain at least one word.")
    return "-".join(word[:1].upper() + word[1:] for word in words)

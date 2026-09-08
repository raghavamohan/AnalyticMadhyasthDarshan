#!/usr/bin/env python3
"""PDF-facing study metadata with no dependency on catalog publication code.

The catalog writer also imports these definitions, but PDF builders import this
small module directly.  A change to sitemap, API, or LLM-catalog serialization
therefore cannot invalidate every generated PDF.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo

from _common import STUDIES

IST = ZoneInfo("Asia/Kolkata")

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
MONTH_ABBR_TO_FULL = {value: key for key, value in MONTH_FULL_TO_ABBR.items()}

EDITED_ON_RE = re.compile(
    r"^\*\*Edited on:\*\*\s+(.+?)\s+IST\s*$",
    re.MULTILINE,
)
_STATUS_LINE_BODY = r"\*\*Status:\*\*[ \t]+(Draft|Released)[ \t]*"
STATUS_MD_RE = re.compile(rf"^{_STATUS_LINE_BODY}$", re.MULTILINE)
_BLANK_LINE_RUN = r"\n(?:[ \t]*\n)*"
STATUS_MD_WITH_SURROUNDING_BLANKS_RE = re.compile(
    rf"(?:{_BLANK_LINE_RUN})?^{_STATUS_LINE_BODY}$(?:{_BLANK_LINE_RUN})?",
    re.MULTILINE,
)
ONGOING_DESC_PREFIX_RE = re.compile(r"^Ongoing\.+\s*", re.IGNORECASE)


class StudyStatus(str, Enum):
    ONGOING = "ongoing"
    DRAFT = "draft"
    RELEASED = "released"


@dataclass(frozen=True)
class PdfStudyRow:
    """The catalog fields that can affect a generated reader or PDF."""

    slug: str
    description: str
    status: StudyStatus
    collection: str = "Studies"


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


def parse_edited_on(md_text: str) -> datetime | None:
    match = EDITED_ON_RE.search(md_text)
    if not match:
        return None
    return parse_timestamp_text(match.group(1).strip())


def parse_status_md(md_text: str) -> StudyStatus | None:
    match = STATUS_MD_RE.search(md_text)
    if not match:
        return None
    return StudyStatus.DRAFT if match.group(1) == "Draft" else StudyStatus.RELEASED


def strip_status_for_pdf(md_text: str) -> str:
    """Remove the document status line while preserving one paragraph break."""
    if not STATUS_MD_RE.search(md_text):
        raise ValueError(
            "strip_status_for_pdf: no **Status:** Draft|Released line found. Every "
            "Draft/Released study must carry one (AGENTS.md §1) before PDF rendering."
        )
    return STATUS_MD_WITH_SURROUNDING_BLANKS_RE.sub("\n\n", md_text, count=1)


def iter_pdf_study_rows() -> tuple[PdfStudyRow, ...]:
    """Read the public catalog without importing its writers or serializers."""
    found: list[PdfStudyRow] = []
    for filename, collection in (
        ("catalog-topical.json", "Studies"),
        ("catalog-formal.json", "Studies"),
        ("catalog-applied.json", "Applications"),
    ):
        path = STUDIES / filename
        if not path.is_file():
            continue
        rows = json.loads(path.read_text(encoding="utf-8"))
        for row in rows:
            found.append(PdfStudyRow(
                slug=str(row["slug"]),
                description=str(row.get("description") or ""),
                status=StudyStatus(str(row["status"])),
                collection=collection,
            ))
    return tuple(found)


def get_pdf_study_row(slug: str) -> PdfStudyRow | None:
    """Read only the catalog fields that influence generated document output."""
    for row in iter_pdf_study_rows():
        if row.slug == slug:
            return row
    return None

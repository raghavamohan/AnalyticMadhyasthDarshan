#!/usr/bin/env python3
"""Build sitemap.xml for the published site from catalog JSON files."""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _common import BASE, site_base_url  # noqa: E402
from _study_catalog import (  # noqa: E402
    CATALOG_TABLES,
    StudyRow,
    StudyTable,
    parse_catalog_json_file,
    parse_edited_on,
)

SITEMAP_PATH = BASE / "sitemap.xml"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

# Published companion pages that intentionally remain outside the study catalog.
# Keep this list curated: internal research notes are not sitemap entries by default.
SUPPLEMENTAL_PAGES = (
    (
        "Studies/The-Ontology-of-Coexistence/Technical-Note-Roop-Guna-Svabhava-Dharma.html",
        "Studies/The-Ontology-of-Coexistence/Technical-Note-Roop-Guna-Svabhava-Dharma.md",
    ),
)


def _absolute_url(path: str) -> str:
    base = site_base_url().rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _lastmod_from_row(row: StudyRow) -> str | None:
    if row.edited_at is not None:
        return row.edited_at.strftime("%Y-%m-%d")
    return None


def _lastmod_from_markdown(path: Path) -> str | None:
    if not path.is_file():
        return None
    edited_at = parse_edited_on(path.read_text(encoding="utf-8"))
    if edited_at is not None:
        return edited_at.strftime("%Y-%m-%d")
    return None


def _study_html_site_path(slug: str, table: StudyTable) -> str:
    if table == StudyTable.APPLIED:
        return f"Applications/{slug}/{slug}.html"
    return f"Studies/{slug}/{slug}.html"


def _study_discussion_site_path(slug: str, table: StudyTable) -> str:
    if table == StudyTable.APPLIED:
        return f"Applications/{slug}/discussion.html"
    return f"Studies/{slug}/discussion.html"


def _add_url(
    root: ET.Element,
    loc: str,
    *,
    lastmod: str | None = None,
    changefreq: str | None = None,
    priority: str | None = None,
) -> None:
    url_el = ET.SubElement(root, "url")
    ET.SubElement(url_el, "loc").text = loc
    if lastmod:
        ET.SubElement(url_el, "lastmod").text = lastmod
    if changefreq:
        ET.SubElement(url_el, "changefreq").text = changefreq
    if priority:
        ET.SubElement(url_el, "priority").text = priority


def collect_sitemap_entries() -> list[tuple[str, str | None, str | None, str | None]]:
    """Return (loc, lastmod, changefreq, priority) tuples in stable order."""
    entries: list[tuple[str, str | None, str | None, str | None]] = []
    seen: set[str] = set()

    def add(
        path: str,
        *,
        lastmod: str | None = None,
        changefreq: str | None = None,
        priority: str | None = None,
    ) -> None:
        loc = _absolute_url(path)
        if loc in seen:
            return
        seen.add(loc)
        entries.append((loc, lastmod, changefreq, priority))

    rows_by_table = {table: parse_catalog_json_file(table) for table in CATALOG_TABLES}

    # The landing page changes when the catalog changes. Its file mtime tracked
    # the last local rebuild instead, so this entry moved to the current date on
    # every run; the newest study timestamp is stable across machines.
    catalog_lastmods = [
        stamp
        for rows in rows_by_table.values()
        for stamp in (_lastmod_from_row(row) for row in rows)
        if stamp
    ]
    add(
        "Studies/index.html",
        lastmod=max(catalog_lastmods, default=None),
        changefreq="weekly",
        priority="1.0",
    )

    for table in CATALOG_TABLES:
        for row in rows_by_table[table]:
            # Planned studies carry no catalog timestamp. Falling back to file
            # mtime made lastmod track the last local regeneration rather than
            # the last content change, so every rebuild rewrote those entries
            # to the current date. lastmod is optional in the sitemap schema;
            # omitting it is stabler than publishing a build artefact's mtime.
            lastmod = _lastmod_from_row(row)

            html_site_path = _study_html_site_path(row.slug, table)
            html_repo_path = BASE / Path(html_site_path)
            if html_repo_path.is_file():
                add(
                    html_site_path,
                    lastmod=lastmod,
                    changefreq="monthly",
                    priority="0.8",
                )

            discuss_site_path = _study_discussion_site_path(row.slug, table)
            discuss_repo_path = BASE / Path(discuss_site_path)
            if discuss_repo_path.is_file():
                add(
                    discuss_site_path,
                    lastmod=lastmod,
                    changefreq="weekly",
                    priority="0.5",
                )

    for html_site_path, markdown_site_path in SUPPLEMENTAL_PAGES:
        if not (BASE / Path(html_site_path)).is_file():
            continue
        add(
            html_site_path,
            lastmod=_lastmod_from_markdown(BASE / Path(markdown_site_path)),
            changefreq="monthly",
            priority="0.6",
        )

    return entries


def render_sitemap_xml(entries: list[tuple[str, str | None, str | None, str | None]]) -> str:
    root = ET.Element("urlset", xmlns=SITEMAP_NS)
    for loc, lastmod, changefreq, priority in entries:
        _add_url(root, loc, lastmod=lastmod, changefreq=changefreq, priority=priority)
    ET.indent(root, space="  ")
    xml_body = ET.tostring(root, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_body}\n'


def write_sitemap() -> Path:
    entries = collect_sitemap_entries()
    SITEMAP_PATH.write_text(
        render_sitemap_xml(entries), encoding="utf-8", newline="\n"
    )
    return SITEMAP_PATH


def main() -> int:
    entries = collect_sitemap_entries()
    path = write_sitemap()
    print(f"Wrote {len(entries)} URLs to {path.relative_to(BASE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

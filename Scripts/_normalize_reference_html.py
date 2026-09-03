#!/usr/bin/env python3
"""Normalize archived reference webpages into reviewable, script-free Markdown."""
from __future__ import annotations

import argparse
import hashlib
import html
import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from _common import BASE, REFERENCES, configure_utf8_stdio, write_text_lf
from _reference_artifacts import load_manifest


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _escape_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _inline(node: NavigableString | Tag, base_url: str) -> str:
    if isinstance(node, Comment):
        return ""
    if isinstance(node, NavigableString):
        return _escape_text(str(node))
    name = node.name.lower()
    content = "".join(
        part for child in node.children if (part := _inline(child, base_url))
    )
    content = _collapse(content)
    if not content and name != "br":
        return ""
    if name in {"em", "i", "cite"}:
        return f"*{content}*"
    if name in {"strong", "b"}:
        return f"**{content}**"
    if name == "code":
        return f"`{content.replace('`', '``')}`"
    if name == "a":
        href = node.get("href", "").strip()
        if not href:
            return content
        target = urljoin(base_url, href)
        return f"[{content or target}]({target})"
    if name == "br":
        return "  \n"
    if name in {"sub", "sup"}:
        return f"<{name}>{html.escape(content)}</{name}>"
    return content


def _list_item(item: Tag, base_url: str, prefix: str, depth: int) -> list[str]:
    direct: list[str] = []
    nested: list[Tag] = []
    for child in item.children:
        if isinstance(child, Tag) and child.name in {"ul", "ol"}:
            nested.append(child)
        else:
            rendered = _inline(child, base_url) if isinstance(child, (Tag, NavigableString)) else ""
            if rendered:
                direct.append(rendered)
    lines = [f"{'  ' * depth}{prefix} {_collapse(' '.join(direct))}"]
    for child in nested:
        lines.extend(_render_list(child, base_url, depth + 1))
    return lines


def _render_list(node: Tag, base_url: str, depth: int = 0) -> list[str]:
    lines: list[str] = []
    ordered = node.name == "ol"
    for index, item in enumerate(node.find_all("li", recursive=False), start=1):
        lines.extend(_list_item(item, base_url, f"{index}." if ordered else "-", depth))
    return lines


def _render_table(node: Tag, base_url: str) -> list[str]:
    rows: list[list[str]] = []
    for tr in node.find_all("tr"):
        cells = [_collapse(_inline(cell, base_url)).replace("|", "\\|") for cell in tr.find_all(["th", "td"], recursive=False)]
        if cells:
            rows.append(cells)
    if not rows:
        return []
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    return [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
        *("| " + " | ".join(row) + " |" for row in rows[1:]),
    ]


def _blocks(node: Tag, base_url: str) -> list[str]:
    blocks: list[str] = []
    for child in node.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            text = _collapse(str(child))
            if text:
                blocks.append(text)
            continue
        name = child.name.lower()
        if name in {"script", "style", "form", "iframe", "noscript", "nav", "button"}:
            continue
        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(name[1])
            anchor = child.get("id")
            if anchor:
                blocks.append(f'<a id="{html.escape(anchor, quote=True)}"></a>')
            blocks.append(f"{'#' * level} {_inline(child, base_url)}")
        elif name == "p":
            text = _inline(child, base_url)
            if text:
                blocks.append(text)
        elif name in {"ul", "ol"}:
            rendered = _render_list(child, base_url)
            if rendered:
                blocks.append("\n".join(rendered))
        elif name == "blockquote":
            text = _inline(child, base_url)
            if text:
                blocks.append("\n".join(f"> {line}" for line in text.splitlines()))
        elif name == "pre":
            blocks.append(f"```text\n{child.get_text().strip()}\n```")
        elif name == "table":
            rendered = _render_table(child, base_url)
            if rendered:
                blocks.append("\n".join(rendered))
        else:
            blocks.extend(_blocks(child, base_url))
    return blocks


def _manifest_row(source: Path) -> dict:
    repo_path = source.resolve().relative_to(BASE).as_posix()
    rows = [row for row in load_manifest()["artifacts"] if row["repo_path"] == repo_path]
    if len(rows) != 1:
        raise ValueError(f"expected one manifest row for {repo_path}, found {len(rows)}")
    return rows[0]


def _source_url(row: dict, fallback: str) -> str:
    urls = (row.get("source") or {}).get("urls") or []
    return urls[0] if urls else fallback


def _archival_header(
    *, title: str, author: str, publication: str, source_url: str, row: dict, note: str = ""
) -> list[str]:
    lines = [
        f"# {title}",
        "",
        f"**Author:** {author or 'Not recorded'}",
        "",
        f"**Publication:** {publication}",
        "",
        f"**Original source:** <{source_url}>",
        "",
        f"**Snapshot:** `{row['repo_path']}`; SHA-256 `{row['source']['sha256']}`",
    ]
    if note:
        lines.extend(["", f"**Edition note:** {note}"])
    lines.extend(
        [
            "",
            "> Normalized, script-free archival reading copy. The original HTML bytes are\n"
            "> retained in the private reference archive for fidelity verification.",
        ]
    )
    return lines


def _finish_markdown(header: list[str], blocks: list[str]) -> str:
    text = "\n\n".join([*header, *blocks])
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    if "<script" in text.casefold() or "javascript:" in text.casefold():
        raise ValueError("normalized Markdown contains executable content")
    return text


def _sep_markdown(source: Path, row: dict) -> str:
    soup = BeautifulSoup(source.read_bytes(), "html.parser")
    article = soup.select_one("#aueditable")
    if article is None:
        raise ValueError("SEP profile requires #aueditable")
    title = _collapse((article.find("h1") or soup.title).get_text(" ", strip=True))
    creator = soup.find("meta", attrs={"name": "DC.creator"})
    author = _collapse(creator.get("content", "")) if creator else ""
    base_url = _source_url(row, "https://plato.stanford.edu/")
    pubinfo = article.select_one("#pubinfo")
    copyright_node = soup.select_one("#article-copyright")

    selected: list[Tag] = []
    for selector in ("#preamble", "#main-text", "#bibliography"):
        node = article.select_one(selector)
        if node is not None:
            selected.append(node)
    if len(selected) != 3:
        raise ValueError("SEP profile requires preamble, main text, and bibliography")

    header = _archival_header(
        title=title,
        author=author,
        publication="Stanford Encyclopedia of Philosophy",
        source_url=base_url,
        row=row,
        note=_collapse(pubinfo.get_text(" ", strip=True)) if pubinfo else "",
    )

    blocks: list[str] = []
    for node in selected:
        blocks.extend(_blocks(node, base_url))
    if copyright_node:
        blocks.extend(["## Copyright", _collapse(copyright_node.get_text(" ", strip=True))])

    return _finish_markdown(header, blocks)


def _wikisource_markdown(source: Path, row: dict, soup: BeautifulSoup) -> str:
    content = soup.select_one(".mw-parser-output")
    if content is None:
        raise ValueError("Wikisource profile requires .mw-parser-output")
    title_node = soup.select_one("#firstHeading")
    author_node = content.select_one("#ws-author")
    year_node = content.select_one("#ws-year")
    title = _collapse(title_node.get_text(" ", strip=True)) if title_node else source.stem
    author = _collapse(author_node.get_text(" ", strip=True)) if author_node else ""
    year = _collapse(year_node.get_text(" ", strip=True)) if year_node else ""
    for node in content.select("style, .ws-noexport, #ws-data, .licenseContainer"):
        node.decompose()
    base_url = _source_url(row, "https://en.wikisource.org/")
    header = _archival_header(
        title=title,
        author=author,
        publication="Mind: A Quarterly Review of Psychology and Philosophy; Wikisource transcription",
        source_url=base_url,
        row=row,
        note=f"Originally published {year}; public-domain transcription." if year else "Public-domain transcription.",
    )
    return _finish_markdown(header, _blocks(content, base_url))


def _carroll_markdown(source: Path, row: dict, soup: BeautifulSoup) -> str:
    content = soup.select_one("article.post .entry-content")
    title_node = soup.select_one("article.post .entry-title")
    if content is None or title_node is None:
        raise ValueError("Sean Carroll profile requires article.post content and title")
    published = soup.find("meta", property="article:published_time")
    note = "Archived blog snapshot"
    if published and published.get("content"):
        note += f"; published {published['content'].split('T', 1)[0]}"
    base_url = _source_url(row, "https://www.preposterousuniverse.com/")
    header = _archival_header(
        title=_collapse(title_node.get_text(" ", strip=True)),
        author="Sean Carroll",
        publication="Preposterous Universe",
        source_url=base_url,
        row=row,
        note=note,
    )
    return _finish_markdown(header, _blocks(content, base_url))


def _poorvam_markdown(source: Path, row: dict, soup: BeautifulSoup) -> str:
    content = soup.select_one("#articleBodyText")
    title_node = soup.select_one("h1.article-title")
    if content is None or title_node is None:
        raise ValueError("Poorvam profile requires #articleBodyText and h1.article-title")
    for node in content.select(".reading-time-bar, meta"):
        node.decompose()
    authors = [
        _collapse(node.get("content", ""))
        for node in soup.find_all("meta", attrs={"name": "citation_author"})
        if node.get("content")
    ]
    published = soup.find("meta", property="article:published_time")
    note = f"Published {published['content'].split('T', 1)[0]}" if published and published.get("content") else ""
    base_url = _source_url(row, "https://poorvam.com/")
    header = _archival_header(
        title=_collapse(title_node.get_text(" ", strip=True)),
        author="; ".join(authors),
        publication="Poorvam International Journal of Creative Arts and Cultural Expressions",
        source_url=base_url,
        row=row,
        note=note,
    )
    return _finish_markdown(header, _blocks(content, base_url))


def normalize(source: Path) -> str:
    source = source.resolve()
    if not source.is_relative_to(REFERENCES) or source.suffix.lower() != ".html":
        raise ValueError("source must be an HTML file under References/")
    row = _manifest_row(source)
    soup = BeautifulSoup(source.read_bytes(), "html.parser")
    if soup.select_one("#aueditable") is not None:
        return _sep_markdown(source, row)
    if soup.select_one(".mw-parser-output") is not None:
        return _wikisource_markdown(source, row, soup)
    if soup.select_one("article.post .entry-content") is not None:
        return _carroll_markdown(source, row, soup)
    if soup.select_one("#articleBodyText") is not None:
        return _poorvam_markdown(source, row, soup)
    raise ValueError(f"no normalization profile matches {source.relative_to(BASE)}")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--check", action="store_true", help="Fail if sibling Markdown is absent or stale.")
    args = parser.parse_args()
    try:
        rendered = normalize(args.source)
        output = args.source.resolve().with_suffix(".md")
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
                print(f"Stale or missing normalized Markdown: {output.relative_to(BASE)}")
                return 1
            print(f"OK: {output.relative_to(BASE)} is synchronized and script-free.")
            return 0
        changed = write_text_lf(output, rendered)
        print(f"{'Wrote' if changed else 'Unchanged'} {output.relative_to(BASE)}")
        print(f"Characters: {len(rendered)}; SHA-256: {hashlib.sha256(rendered.encode()).hexdigest()}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Reference HTML normalization failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

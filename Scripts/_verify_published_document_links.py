#!/usr/bin/env python3
"""Verify study HTML navigation and manifest-backed reference delivery links."""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup

from _common import APPLICATIONS, BASE, STUDIES, configure_utf8_stdio, site_base_url
from _reference_artifacts import load_manifest, public_delivery_url

SITE_ROOT = site_base_url().rstrip("/")
SITE_HOST = urlsplit(SITE_ROOT).netloc.casefold()
ACTIVE_TRANSLATION_PREFIXES = (
    "References/Madhyasth-Darshan/KD-Karm-Darshan-English/",
    "References/Madhyasth-Darshan/MSM-Manav-Sanchetnavadi-Manovigyan-English/",
)


def _document_html_paths() -> list[Path]:
    paths: list[Path] = []
    for root in (STUDIES, APPLICATIONS):
        if not root.is_dir():
            continue
        for html_path in root.glob("*/*.html"):
            markdown_path = html_path.with_suffix(".md")
            if markdown_path.is_file() and not _is_pre_catalog_placeholder(markdown_path):
                paths.append(html_path)
    return sorted(paths)


def _is_pre_catalog_placeholder(path: Path) -> bool:
    if path.parent.parent not in {STUDIES, APPLICATIONS}:
        return False
    if path.stem != path.parent.name:
        return False
    return "**Status:**" not in path.read_text(encoding="utf-8")


def _site_target(href: str, source: Path):
    absolute = urljoin(f"{SITE_ROOT}/{source.relative_to(BASE).as_posix()}", href)
    parsed = urlsplit(absolute)
    if parsed.netloc.casefold() != SITE_HOST:
        return None
    return unquote(parsed.path.lstrip("/")), unquote(parsed.fragment)


@lru_cache(maxsize=None)
def _html_ids(path_text: str) -> frozenset[str]:
    target = Path(path_text)
    soup = BeautifulSoup(target.read_text(encoding="utf-8", errors="replace"), "html.parser")
    return frozenset(str(node["id"]) for node in soup.find_all(id=True))


def verify_html(path: Path, manifest: dict | None = None) -> list[str]:
    errors: list[str] = []
    manifest = manifest or load_manifest()
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for link in soup.find_all("a", href=True):
        href = str(link["href"]).strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        target = _site_target(href, path)
        if target is None:
            continue
        repo_path, fragment = target
        suffix = PurePosixPath(repo_path).suffix.lower()

        if repo_path.startswith(("Studies/", "Applications/")):
            target_path = BASE / repo_path
            source_markdown = target_path.with_suffix(".md")
            if suffix in {".md", ".pdf"} and source_markdown.is_file():
                if suffix == ".pdf" and link.has_attr("download"):
                    continue
                errors.append(f"study navigation must target HTML, not {suffix}: {href}")
                continue
            if suffix == ".html" and source_markdown.is_file():
                if not target_path.is_file():
                    errors.append(f"missing study HTML target: {href}")
                    continue
                if fragment:
                    if fragment not in _html_ids(str(target_path.resolve())):
                        errors.append(f"missing study HTML fragment #{fragment}: {href}")
            continue

        if not repo_path.startswith("References/"):
            continue
        if any(repo_path.startswith(prefix) for prefix in ACTIVE_TRANSLATION_PREFIXES):
            if suffix == ".md":
                errors.append(f"active translation link must use its PDF, not Markdown: {href}")
            continue
        expected = public_delivery_url(repo_path, manifest)
        if expected:
            actual = f"{SITE_ROOT}/{repo_path}"
            if suffix != ".pdf" or expected != actual:
                errors.append(f"reference citation must target manifest PDF {expected}: {href}")
        elif suffix in {".md", ".html"}:
            sibling = str(PurePosixPath(repo_path).with_suffix(".pdf"))
            sibling_url = public_delivery_url(sibling, manifest)
            if sibling_url:
                errors.append(f"reference citation must target manifest PDF {sibling_url}: {href}")
    return errors


def main() -> int:
    configure_utf8_stdio()
    manifest = load_manifest()
    failures: list[str] = []
    paths = _document_html_paths()
    for path in paths:
        for error in verify_html(path, manifest):
            failures.append(f"{path.relative_to(BASE).as_posix()}: {error}")
    if failures:
        print("Published document link verification failed:\n  - " + "\n  - ".join(failures))
        return 1
    print(f"Published document links verified ({len(paths)} generated HTML pages).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

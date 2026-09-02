"""Cross-study Markdown link inspection shared by lifecycle scripts and CI."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from _common import BASE, iter_study_md_paths

MARKDOWN_LINK_RE = re.compile(r"\]\((?P<target>[^)]+)\)")
SECTION_RE = re.compile(
    r"§{1,2}\s*(?P<sections>\d+(?:\.\d+)*"
    r"(?:(?:\s*(?:,|;|and|to|[–—-])\s*)§{0,2}\s*\d+(?:\.\d+)*)*)",
    re.IGNORECASE,
)
HEADING_NUMBER_RE = re.compile(r"^#{2,6}\s+(?P<number>\d+(?:\.\d+)*)\b", re.MULTILINE)


@dataclass(frozen=True)
class StudyLink:
    source: Path
    source_slug: str | None
    target: str
    target_slug: str
    sections: tuple[str, ...]
    line: int


def _strip_markdown_target(raw: str) -> str:
    """Remove optional angle brackets/title text from one Markdown href."""
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    # Local repository links do not need titles, but tolerate ``path "title"``.
    return value.split(maxsplit=1)[0]


def _target_repo_parts(target: str, source: Path, base: Path) -> tuple[str, ...] | None:
    parsed = urlparse(target)
    if parsed.scheme in {"http", "https"}:
        parts = tuple(part for part in unquote(parsed.path).split("/") if part)
    elif parsed.scheme:
        return None
    else:
        # Path handles forward slashes on every supported platform; normalize
        # backslashes as well for links authored on Windows.
        path_text = unquote(parsed.path).replace("\\", "/")
        candidate = (source.parent / Path(path_text)).resolve()
        try:
            parts = candidate.relative_to(base.resolve()).parts
        except ValueError:
            return None

    for root in ("Studies", "Applications"):
        if root in parts:
            index = parts.index(root)
            if len(parts) >= index + 3:
                candidate = parts[index:]
                # Repository study markdown conventionally links primary
                # sources as ../References/...; path resolution from the study
                # folder makes that look like Studies/References/..., but it is
                # not a study slug and must not enter cross-study validation.
                if candidate[1] == "References":
                    continue
                return candidate
    return None


def study_links_in_file(path: Path, *, base: Path = BASE) -> list[StudyLink]:
    text = path.read_text(encoding="utf-8")
    try:
        source_parts = path.resolve().relative_to(base.resolve()).parts
    except ValueError:
        source_parts = ()
    source_slug = (
        source_parts[1]
        if len(source_parts) >= 3 and source_parts[0] in {"Studies", "Applications"}
        else None
    )
    links: list[StudyLink] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        target = _strip_markdown_target(match.group("target"))
        parts = _target_repo_parts(target, path, base)
        if parts is None:
            continue
        # Section references can follow immediately or after a short
        # description (common in Further Reading entries). Attribute only text
        # up to the next Markdown link or line ending so a later link's section
        # number is not assigned to this target as well.
        line_end = text.find("\n", match.end())
        if line_end == -1:
            line_end = len(text)
        next_link = MARKDOWN_LINK_RE.search(text, match.end(), line_end)
        tail_end = next_link.start() if next_link else line_end
        sections = tuple(
            dict.fromkeys(
                section
                for section_match in SECTION_RE.finditer(text, match.end(), tail_end)
                for section in re.findall(
                    r"\d+(?:\.\d+)*",
                    section_match.group("sections"),
                )
            )
        )
        links.append(
            StudyLink(
                source=path,
                source_slug=source_slug,
                target=target,
                target_slug=parts[1],
                sections=sections,
                line=text.count("\n", 0, match.start()) + 1,
            )
        )
    return links


def links_to_slug(
    slug: str,
    *,
    paths: list[Path] | None = None,
    base: Path = BASE,
) -> list[StudyLink]:
    """Return local Markdown links that still target ``slug``."""
    inspect_paths = list(paths) if paths is not None else iter_study_md_paths()
    for extra in (base / "References" / "README.md", base / "References" / "MANIFEST.md"):
        if paths is None and extra.is_file():
            inspect_paths.append(extra)
    return [
        link
        for path in inspect_paths
        if path.is_file()
        for link in study_links_in_file(path, base=base)
        if link.target_slug == slug
    ]


def cross_study_section_errors(
    focus_slugs: set[str],
    *,
    paths: list[Path] | None = None,
    base: Path = BASE,
) -> list[str]:
    """Validate section references entering or leaving changed studies.

    Checking both directions is what makes a section renumber safe: editing the
    target validates every inbound reference, while editing a referring paper
    validates the outbound reference it just changed.
    """
    if not focus_slugs:
        return []
    inspect_paths = list(paths) if paths is not None else iter_study_md_paths()
    by_slug = {path.parent.name: path for path in inspect_paths if path.is_file()}
    heading_numbers = {
        slug: set(HEADING_NUMBER_RE.findall(path.read_text(encoding="utf-8")))
        for slug, path in by_slug.items()
    }

    errors: list[str] = []
    for path in inspect_paths:
        if not path.is_file():
            continue
        for link in study_links_in_file(path, base=base):
            if not link.sections:
                continue
            if link.source_slug not in focus_slugs and link.target_slug not in focus_slugs:
                continue
            target_headings = heading_numbers.get(link.target_slug)
            if target_headings is None:
                errors.append(
                    f"{path.relative_to(base)}:{link.line}: cross-study target "
                    f"{link.target_slug} has no canonical markdown source."
                )
                continue
            missing = [section for section in link.sections if section not in target_headings]
            if missing:
                errors.append(
                    f"{path.relative_to(base)}:{link.line}: {link.target_slug} has no "
                    f"section(s) {', '.join('§' + value for value in missing)}."
                )
    return errors

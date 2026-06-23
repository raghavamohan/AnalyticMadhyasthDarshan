"""Audit Studies/ reference links against References/ and NOT-DOWNLOADED.md.

Usage (from repo root):
    python Scripts/_audit_references.py
    python Scripts/_audit_references.py --study Nature-Of-Time
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from _common import REFERENCES, STUDIES, iter_study_md_paths, is_linkable_reference_file, parse_reference_registry

REF_SECTION_RE = re.compile(r"^## References\s*$", re.MULTILINE)
REF_ENTRY_RE = re.compile(r"^- \*\*([^*]+)\*\*\s*[—\-]")
LINK_RE = re.compile(r"\]\(([^)]+)\)")
DOWNLOAD_MANIFEST = Path(__file__).resolve().parent / "_reference_downloads.py"


@dataclass
class ReferenceRow:
    study: str
    tag: str
    link: str
    kind: str
    ok: bool
    detail: str = ""


@dataclass
class AuditReport:
    rows: list[ReferenceRow] = field(default_factory=list)

    @property
    def external(self) -> list[ReferenceRow]:
        return [row for row in self.rows if row.kind == "external"]

    @property
    def local_missing(self) -> list[ReferenceRow]:
        return [row for row in self.rows if row.kind == "local" and not row.ok]

    @property
    def download_candidates(self) -> list[ReferenceRow]:
        return [
            row
            for row in self.rows
            if row.kind == "external"
            and row.link.startswith("http")
            and "github.com/raghavamohan" not in row.link
            and "analyticmadhyasth" not in row.link.lower()
        ]


def _study_paths(study: str | None) -> list[Path]:
    paths = iter_study_md_paths()
    if study:
        paths = [path for path in paths if path.parent.name == study]
    if study and not paths:
        raise SystemExit(f"No study markdown found for slug {study!r}.")
    return paths


def _references_block(text: str) -> str:
    match = REF_SECTION_RE.search(text)
    if not match:
        return ""
    tail = text[match.end() :]
    next_section = re.search(r"^## [^#]", tail, re.MULTILINE)
    return tail[: next_section.start()] if next_section else tail


def _classify_link(raw_link: str, registry: dict[str, Path]) -> tuple[str, bool, str]:
    link = raw_link.strip()
    if link.startswith("../References/"):
        rel = link.removeprefix("../References/").split("#", 1)[0]
        path = (REFERENCES / rel).resolve()
        if not path.exists():
            return "local", False, f"missing file References/{rel}"
        if not is_linkable_reference_file(path):
            return "local", False, f"unusable file References/{rel} (empty or not a valid PDF/HTML)"
        return "local", True, str(path.relative_to(REFERENCES.parent))
    if link.startswith("http://") or link.startswith("https://"):
        host = urlparse(link).netloc.casefold()
        if host.endswith("github.com"):
            return "meta", True, "repository link"
        return "external", True, link
    if link.endswith(".pdf") and not link.startswith("http"):
        return "internal", True, "companion study link"
    if "NOT-DOWNLOADED.md" in link:
        return "external-index", True, "NOT-DOWNLOADED.md pointer"
    return "other", True, link


def audit_references(*, study: str | None = None) -> AuditReport:
    registry = parse_reference_registry()
    report = AuditReport()

    for md_path in _study_paths(study):
        block = _references_block(md_path.read_text(encoding="utf-8", errors="replace"))
        if not block:
            continue
        for line in block.splitlines():
            entry_match = REF_ENTRY_RE.match(line.strip())
            if not entry_match:
                continue
            tag = entry_match.group(1).strip()
            link_match = LINK_RE.search(line)
            if not link_match:
                report.rows.append(
                    ReferenceRow(
                        study=md_path.parent.name,
                        tag=tag,
                        link="",
                        kind="other",
                        ok=True,
                        detail="no markdown link on entry",
                    )
                )
                continue
            kind, ok, detail = _classify_link(link_match.group(1), registry)
            report.rows.append(
                ReferenceRow(
                    study=md_path.stem,
                    tag=tag,
                    link=link_match.group(1),
                    kind=kind,
                    ok=ok,
                    detail=detail,
                )
            )
    return report


def _print_report(report: AuditReport) -> int:
    local = [r for r in report.rows if r.kind == "local"]
    external = report.external
    missing = report.local_missing

    print(f"Studies reference entries: {len(report.rows)}")
    print(f"  local links: {len(local)} ({len(missing)} broken)")
    print(f"  external links: {len(external)}")
    print(f"  download manifest entries: see Scripts/_reference_downloads.py")

    if missing:
        print("\nBroken local bibliography links:")
        for row in missing:
            print(f"  [{row.study}] {row.tag}: {row.detail}")

    print("\nExternal-only tags (sample — full list in References/NOT-DOWNLOADED.md):")
    seen: set[str] = set()
    for row in external:
        if row.tag in seen:
            continue
        seen.add(row.tag)
        print(f"  {row.tag}: {row.link}")

    print("\nNext steps for new local mirrors:")
    print("  1. Confirm redistribution rights (public domain, CC, or author preprint).")
    print("  2. Add entry to Scripts/_reference_downloads.py")
    print("  3. python Scripts/_download_references.py --tag \"<Tag>\"")
    print("  4. Update References/README.md, MANIFEST.md; remove from NOT-DOWNLOADED.md if applicable")
    print("  5. Point study References entry to ../References/... ; run quote verify + cache sync")

    return 1 if missing else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Studies/ bibliography links.")
    parser.add_argument("--study", help="Limit audit to one study slug.")
    args = parser.parse_args()
    report = audit_references(study=args.study)
    raise SystemExit(_print_report(report))


if __name__ == "__main__":
    main()

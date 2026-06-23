"""Run all reference integrity checks for Studies/ and References/.

Usage (from repo root):
    python Scripts/_check_references.py
    python Scripts/_check_references.py --study Knowledge-Knower-And-Known
    python Scripts/_check_references.py --skip-pdf

Checks:
  1. Bibliography entries in ## References (via _audit_references)
  2. Every ../References/ link anywhere in study markdown
  3. Every mirror file under References/ (valid PDF/HTML, not empty or HTML-as-PDF)
  4. Local reference links embedded in study PDFs (site URLs + no file:// leftovers)

Exit code 1 when any check fails.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse

from pypdf import PdfReader

from _audit_references import audit_references
from _common import BASE, REFERENCES, STUDIES, is_linkable_reference_file, iter_study_md_paths, site_base_url, study_pdf

LOCAL_REF_LINK = re.compile(r"\]\((\.\./References/[^)#]+)\)")
SKIP_REFERENCE_NAMES = frozenset({"README.md", "MANIFEST.md", "NOT-DOWNLOADED.md"})


@dataclass
class CheckIssue:
    category: str
    location: str
    detail: str


@dataclass
class CheckReport:
    issues: list[CheckIssue] = field(default_factory=list)

    def add(self, category: str, location: str, detail: str) -> None:
        self.issues.append(CheckIssue(category=category, location=location, detail=detail))

    @property
    def ok(self) -> bool:
        return not self.issues


def _study_md_paths(study: str | None) -> list[Path]:
    paths = iter_study_md_paths()
    if study:
        paths = [path for path in paths if path.parent.name == study]
        if not paths:
            raise SystemExit(f"No study markdown found for slug {study!r}.")
    return paths


def _resolve_local_reference(rel: str) -> Path:
    return (REFERENCES / rel.removeprefix("../References/").split("#", 1)[0]).resolve()


def check_bibliography(report: CheckReport, *, study: str | None) -> None:
    audit = audit_references(study=study)
    for row in audit.local_missing:
        report.add(
            "bibliography",
            f"{row.study} / {row.tag}",
            row.detail,
        )


def check_markdown_local_links(report: CheckReport, *, study: str | None) -> None:
    for md_path in _study_md_paths(study):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        seen: set[str] = set()
        for match in LOCAL_REF_LINK.finditer(text):
            rel = match.group(1).split("#", 1)[0]
            if rel in seen:
                continue
            seen.add(rel)
            target = _resolve_local_reference(rel)
            if not target.is_file():
                report.add(
                    "markdown-link",
                    str(md_path.relative_to(BASE)),
                    f"missing local file for {rel}",
                )
            elif not is_linkable_reference_file(target):
                report.add(
                    "markdown-link",
                    str(md_path.relative_to(BASE)),
                    f"unusable local file for {rel} (empty or invalid PDF/HTML)",
                )


def check_mirror_files(report: CheckReport) -> None:
    for path in sorted(REFERENCES.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIP_REFERENCE_NAMES:
            continue
        if path.suffix.lower() not in {".pdf", ".html"}:
            continue
        rel = path.relative_to(REFERENCES).as_posix()
        if not is_linkable_reference_file(path):
            size = path.stat().st_size
            if path.suffix.lower() == ".pdf" and size >= 500:
                head = path.read_bytes()[:5]
                detail = f"invalid PDF header {head!r} ({size} bytes) — likely a publisher HTML page"
            else:
                detail = f"empty or too small ({size} bytes)"
            report.add("mirror-file", f"References/{rel}", detail)


def _pdf_local_uri_issues(pdf_path: Path) -> list[str]:
    if not pdf_path.is_file():
        return []
    site_prefix = site_base_url().rstrip("/") + "/"
    problems: list[str] = []
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        return [f"cannot read PDF: {exc}"]

    for page in reader.pages:
        for annot_ref in page.get("/Annots") or []:
            annot = annot_ref.get_object()
            if annot.get("/Subtype") != "/Link":
                continue
            action = annot.get("/A")
            if not action or "/URI" not in action:
                continue
            uri = unquote(action["/URI"])
            if uri.startswith("file:"):
                problems.append(f"file:// link in PDF (not usable on the website): {uri}")
                continue
            if uri.startswith(site_prefix):
                rel = uri.removeprefix(site_prefix).split("#", 1)[0]
                target = (BASE / rel).resolve()
                if not is_linkable_reference_file(target):
                    problems.append(f"PDF link target missing or unusable: {uri}")
    return problems


def check_study_pdf_links(report: CheckReport, *, study: str | None) -> None:
    for md_path in _study_md_paths(study):
        slug = md_path.parent.name
        pdf_path = study_pdf(slug)
        if not pdf_path.is_file():
            continue
        for detail in _pdf_local_uri_issues(pdf_path):
            report.add("pdf-link", str(pdf_path.relative_to(BASE)), detail)


def run_checks(*, study: str | None = None, skip_pdf: bool = False) -> CheckReport:
    report = CheckReport()
    check_bibliography(report, study=study)
    check_markdown_local_links(report, study=study)
    if study is None:
        check_mirror_files(report)
    if not skip_pdf:
        check_study_pdf_links(report, study=study)
    return report


def print_report(report: CheckReport, *, study: str | None) -> int:
    scope = f"study {study}" if study else "repository"
    print(f"Reference checks ({scope}): {len(report.issues)} issue(s)")

    if report.ok:
        print("OK: all reference checks passed.")
        return 0

    by_category: dict[str, list[CheckIssue]] = {}
    for issue in report.issues:
        by_category.setdefault(issue.category, []).append(issue)

    labels = {
        "bibliography": "Bibliography (## References)",
        "markdown-link": "Markdown ../References/ links",
        "mirror-file": "References/ mirror files",
        "pdf-link": "Study PDF embedded links",
    }
    for category, label in labels.items():
        items = by_category.get(category, [])
        if not items:
            continue
        print(f"\n{label}:")
        for item in items:
            print(f"  [{item.location}] {item.detail}")

    print("\nFix broken local mirrors with download-references skill, or use external DOI/URL links only.")
    print("Re-run: python Scripts/_check_references.py")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run bibliography, mirror-file, and study PDF reference checks.",
    )
    parser.add_argument("--study", help="Limit checks to one study slug.")
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Skip study PDF link checks (faster; use when PDFs are not regenerated yet).",
    )
    args = parser.parse_args()
    report = run_checks(study=args.study, skip_pdf=args.skip_pdf)
    raise SystemExit(print_report(report, study=args.study))


if __name__ == "__main__":
    main()

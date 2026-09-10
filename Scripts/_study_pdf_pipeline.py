#!/usr/bin/env python3
"""Render and verify one Markdown-derived study PDF.

This module deliberately excludes catalog publication and discussion-page work.
It is the dependency root used by the generated-PDF builder and cache planner.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from _common import SCRIPTS
from _convert_to_pdf import convert_to_html
from _pdf_metadata import normalize_study_pdf, stamp_for_markdown
from _study_pdf_metadata import StudyStatus, parse_status_md
from _verify_pdf_diagrams import verify_study_pdf_diagrams
from _verify_pdf_fenced_code import verify_study_pdf_fenced_code
from _verify_pdf_math import verify_study_pdf_math
from _verify_pdf_outline import verify_study_pdf_outline
from _verify_study_svgs import verify_study_svgs


def render_status(md_path: Path) -> StudyStatus:
    """Resolve a canonical study status or the unwatermarked companion status."""
    status = parse_status_md(md_path.read_text(encoding="utf-8"))
    if status is not None:
        return status
    if md_path.stem != md_path.parent.name:
        return StudyStatus.RELEASED
    raise ValueError(f"**Status:** missing in {md_path}")


def regenerate_pdf(md_path: Path, status: StudyStatus, *, refresh_web: bool = True) -> None:
    """CI builds use a sibling intermediate, leaving published readers untouched."""
    html_path = md_path.with_suffix('.html') if refresh_web else md_path.with_suffix('.render.html')
    try:
        _regenerate_pdf(md_path, status, html_path, refresh_web)
    finally:
        if not refresh_web:
            html_path.unlink(missing_ok=True)


def _regenerate_pdf(md_path: Path, status: StudyStatus, html_path: Path, refresh_web: bool) -> None:
    if status == StudyStatus.ONGOING:
        return

    verify_study_svgs(md_path)

    pdf_path = md_path.with_suffix(".pdf")
    build_pdf_path = md_path.with_name(f"{md_path.stem}.build.pdf")
    convert_to_html(
        md_path,
        is_draft=status == StudyStatus.DRAFT,
        include_web_chrome=True,
        output_path=html_path,
        update_search=refresh_web,
    )

    html_to_pdf_cmd = ["node", str(SCRIPTS / "_html_to_pdf.js"), str(html_path)]
    html_to_pdf_cmd.append("Draft" if status == StudyStatus.DRAFT else "")
    html_to_pdf_cmd.append(str(build_pdf_path))
    html_to_pdf_cmd.append(stamp_for_markdown(md_path))
    subprocess.run(
        html_to_pdf_cmd,
        check=True,
        cwd=SCRIPTS.parent,
    )
    build_pdf_path.replace(pdf_path)
    if build_pdf_path.exists():
        build_pdf_path.unlink()

    normalize_study_pdf(md_path, pdf_path)
    verify_study_pdf_diagrams(md_path, pdf_path)
    verify_study_pdf_fenced_code(md_path, pdf_path)
    verify_study_pdf_math(md_path, pdf_path, html_path=html_path)
    verify_study_pdf_outline(md_path, pdf_path)

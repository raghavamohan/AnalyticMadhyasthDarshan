"""Convert an external PDF to a study markdown file for maintainer import.

Usage:
  python Scripts/_pdf_to_study_md.py path/to/submission.pdf --slug My-Study --title "Title"
  python Scripts/_pdf_to_study_md.py paper.pdf --stdout --no-metadata
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _add_study import ensure_author_block, parse_status_arg
from _common import study_md
from _pdf_to_md import DEFAULT_MIN_CHARS, convert_pdf_to_markdown
from _study_catalog import StudyStatus, format_edited_on_md, now_ist, set_status_md


def _print_report(report, report_format: str) -> None:
    if report_format == "json":
        print(json.dumps(report.to_dict(), indent=2), file=sys.stderr)
        return
    print("Conversion report:", file=sys.stderr)
    print(f"  Pages processed:       {report.pages_processed}", file=sys.stderr)
    print(f"  Headings found:        {report.headings_found}", file=sys.stderr)
    print(f"  Tables found:          {report.tables_found}", file=sys.stderr)
    print(f"  Lists found:           {report.lists_found}", file=sys.stderr)
    print(f"  Blockquotes found:     {report.blockquotes_found}", file=sys.stderr)
    print(f"  Low-confidence blocks: {report.low_confidence_blocks}", file=sys.stderr)
    print(f"  Empty pages:           {report.empty_pages}", file=sys.stderr)
    print(f"  Total characters:      {report.total_chars}", file=sys.stderr)
    for warning in report.warnings:
        print(f"  Warning: {warning}", file=sys.stderr)


def build_study_markdown(
    body: str,
    *,
    title: str | None,
    author: str | None,
    edited_at,
    status: StudyStatus,
) -> str:
    md = body.strip() + "\n"
    if title:
        md = ensure_author_block(md, fallback_title=title)
    elif author:
        if "**Author:**" not in md:
            h1_end = md.find("\n\n")
            if h1_end == -1:
                md = f"{md.rstrip()}\n\n**Author:** {author}\n\n"
            else:
                md = md[: h1_end + 2] + f"**Author:** {author}\n\n" + md[h1_end + 2 :]
    else:
        md = ensure_author_block(md)

    if "**Edited on:**" not in md:
        h1_match_end = md.find("\n\n")
        insert_at = h1_match_end + 2 if h1_match_end != -1 else 0
        if "**Author:**" in md:
            author_end = md.find("\n\n", md.index("**Author:**"))
            insert_at = author_end + 2 if author_end != -1 else insert_at
        md = md[:insert_at] + format_edited_on_md(edited_at) + "\n\n" + md[insert_at:]

    if status != StudyStatus.ONGOING:
        md = set_status_md(md, status)
    return md


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a PDF to study markdown for maintainer review.",
    )
    parser.add_argument("pdf", type=Path, help="Path to the source PDF")
    parser.add_argument("--slug", help="Study slug (default: derived from --title or filename)")
    parser.add_argument("--title", help="Study title for metadata and H1 fallback")
    parser.add_argument("--author", help="Override default author block with a plain author line")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write markdown to this path (default: Studies/<slug>/<slug>.md when --slug set)",
    )
    parser.add_argument(
        "--status",
        default="draft",
        help="Status line to inject: draft (default), released, or ongoing",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=DEFAULT_MIN_CHARS,
        help=f"Minimum extracted characters (default: {DEFAULT_MIN_CHARS})",
    )
    parser.add_argument("--stdout", action="store_true", help="Print markdown to stdout")
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Emit converted body only (no author/edited-on/status injection)",
    )
    parser.add_argument(
        "--report",
        choices=("text", "json"),
        default="text",
        help="Conversion report format on stderr (default: text)",
    )
    args = parser.parse_args()

    body, report = convert_pdf_to_markdown(args.pdf.resolve(), min_chars=args.min_chars)
    _print_report(report, args.report)

    if args.no_metadata:
        md = body
    else:
        md = build_study_markdown(
            body,
            title=args.title,
            author=args.author,
            edited_at=now_ist(),
            status=parse_status_arg(args.status),
        )

    if args.stdout:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
        sys.stdout.write(md)
        return

    if args.output:
        out_path = args.output.resolve()
    elif args.slug:
        out_path = study_md(args.slug)
    else:
        raise SystemExit("Specify --output or --slug when not using --stdout.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

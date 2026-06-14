"""Add a new study PDF to Studies/ and update catalog files.

Usage:
  python Scripts\\_add_study.py path\\to\\paper.pdf
  python Scripts\\_add_study.py paper.pdf --title "My Study" --description "Summary" --tags "MVD, SB, JV"
  python Scripts\\_add_study.py paper.pdf --dry-run

Copies the PDF into Studies/, creates a stub markdown source if missing, and updates
index.html, Studies/README.md, References/README.md, and References/MANIFEST.md.
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from pathlib import Path

from _common import REFERENCES, STUDIES

GITHUB_REPO = "https://github.com/raghavamohan/AnalyticMadhyasthDarshan"
AUTHOR_BLOCK = (
    f"**Author:** [AnalyticMadhyasthDarshan.org]({GITHUB_REPO}) — a group of people "
    f"studying Madhyasth Darshan philosophy. Source repository: "
    f"[raghavamohan/AnalyticMadhyasthDarshan]({GITHUB_REPO})."
)

CATALOG_START = "<!-- studies-catalog -->"
CATALOG_END = "<!-- /studies-catalog -->"

STUDIES_README_TABLE_HEADER = "| Document | Description |\n|----------|-------------|"
REFERENCES_README_TABLE_HEADER = "| Paper | Primary tags |\n|-------|----------------|"


def title_to_slug(title: str) -> str:
    """Convert a title to kebab-case slug (Why-Humans-Are-Not-Just-Material style)."""
    words = re.findall(r"[\w']+", title.strip())
    if not words:
        raise ValueError("Title must contain at least one word.")
    return "-".join(word[:1].upper() + word[1:] for word in words)


def slug_to_title(slug: str) -> str:
    """Convert slug to display title."""
    return " ".join(part.capitalize() for part in slug.split("-"))


def escape_md_cell(text: str) -> str:
    return text.replace("|", "\\|")


def build_stub_markdown(title: str, description: str) -> str:
    return f"""# {title}

{AUTHOR_BLOCK}

{description}

> This study was added from a PDF. Expand this markdown source (sections, citations, references) and regenerate the PDF with `Scripts/_convert_to_pdf.py` when ready.

## References

- *(Add references here — link to files under `../References/` where available, or to the original publisher URL.)*
"""


def html_row(slug: str, description: str) -> str:
    safe_desc = html.escape(description, quote=False)
    return (
        f"    <tr>\n"
        f'      <td><a href="{slug}.pdf">{slug}</a></td>\n'
        f"      <td>{safe_desc}</td>\n"
        f"    </tr>"
    )


def readme_row(slug: str, description: str) -> str:
    return f"| [{slug}]({slug}.pdf) | {escape_md_cell(description)} |"


def references_readme_row(slug: str, tags: str) -> str:
    return (
        f"| [{slug}.pdf](../Studies/{slug}.pdf) | {escape_md_cell(tags)} |"
    )


def manifest_row(slug: str, tags: str, status: str = "TBD") -> str:
    return f"| [{slug}.pdf](../Studies/{slug}.pdf) | {escape_md_cell(tags)} | {status} |"


def replace_catalog_block(content: str, new_block: str) -> str:
    pattern = re.compile(
        re.escape(CATALOG_START) + r".*?" + re.escape(CATALOG_END),
        re.DOTALL,
    )
    if not pattern.search(content):
        raise ValueError(
            f"Catalog markers {CATALOG_START!r} / {CATALOG_END!r} not found in file."
        )
    return pattern.sub(f"{CATALOG_START}\n{new_block}\n{CATALOG_END}", content, count=1)


def parse_html_rows(content: str) -> list[tuple[str, str]]:
    block = re.search(
        re.escape(CATALOG_START) + r"(.*?)" + re.escape(CATALOG_END),
        content,
        re.DOTALL,
    )
    if not block:
        return []
    rows: list[tuple[str, str]] = []
    for match in re.finditer(
        r'<a href="([^"]+\.pdf)">([^<]+)</a></td>\s*<td>([^<]*)</td>',
        block.group(1),
    ):
        rows.append((Path(match.group(1)).stem, html.unescape(match.group(3))))
    return rows


def parse_md_rows(content: str) -> list[tuple[str, str]]:
    block = re.search(
        re.escape(CATALOG_START) + r"(.*?)" + re.escape(CATALOG_END),
        content,
        re.DOTALL,
    )
    if not block:
        return []
    rows: list[tuple[str, str]] = []
    for line in block.group(1).splitlines():
        match = re.match(r"\|\s*\[([^\]]+)\]\(([^)]+\.pdf)\)\s*\|\s*(.+?)\s*\|", line)
        if match:
            rows.append((Path(match.group(2)).stem, match.group(3).strip()))
    return rows


def parse_references_readme_rows(content: str) -> list[tuple[str, str]]:
    block = re.search(
        re.escape(CATALOG_START) + r"(.*?)" + re.escape(CATALOG_END),
        content,
        re.DOTALL,
    )
    if not block:
        return []
    rows: list[tuple[str, str]] = []
    for line in block.group(1).splitlines():
        match = re.match(
            r"\|\s*\[([^\]]+\.pdf)\]\(../Studies/([^)]+)\)\s*\|\s*(.+?)\s*\|",
            line,
        )
        if match:
            rows.append((Path(match.group(1)).stem, match.group(3).strip()))
    return rows


def append_manifest_row(content: str, slug: str, tags: str) -> str:
    pdf_name = f"{slug}.pdf"
    if pdf_name in content:
        return content
    row = manifest_row(slug, tags)
    marker = "\n## By tag"
    if marker not in content:
        raise ValueError("Could not find '## By tag' section in MANIFEST.md")
    return content.replace(marker, f"\n{row}\n{marker}", 1)


def upsert_row(rows: list[tuple], key: str, new_row: tuple) -> list[tuple]:
    filtered = [row for row in rows if row[0] != key]
    filtered.append(new_row)
    return sorted(filtered, key=lambda row: row[0].lower())


def prompt_if_missing(value: str | None, label: str, default: str | None = None) -> str:
    if value and value.strip():
        return value.strip()
    suffix = f" [{default}]" if default else ""
    while True:
        answer = input(f"{label}{suffix}: ").strip()
        if answer:
            return answer
        if default:
            return default
        print("  (required)")


def add_study(
    pdf_path: Path,
    *,
    title: str | None,
    slug: str | None,
    description: str | None,
    tags: str | None,
    dry_run: bool,
    force: bool,
) -> None:
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise SystemExit(f"Expected a .pdf file, got: {pdf_path}")

    derived_slug = slug or title_to_slug(title or pdf_path.stem.replace("_", " "))
    study_title = title or slug_to_title(derived_slug)
    study_description = description or ""
    study_tags = tags or ""

    if not dry_run and sys.stdin.isatty():
        if not description:
            study_description = prompt_if_missing(
                None,
                "Description (one line, shown in the catalog)",
                default=f"Study on {study_title}",
            )
        if not tags:
            study_tags = prompt_if_missing(
                None,
                "Primary tags (e.g. MVD, SB, JV)",
                default="MVD, SB, JV",
            )
    else:
        study_description = study_description or f"Study on {study_title}"
        study_tags = study_tags or "MVD, SB, JV"

    dest_pdf = STUDIES / f"{derived_slug}.pdf"
    dest_md = STUDIES / f"{derived_slug}.md"

    if dest_pdf.exists() and not force:
        raise SystemExit(
            f"Study already exists: {dest_pdf}\nUse --force to overwrite the PDF and refresh catalog entries."
        )

    print(f"Slug:        {derived_slug}")
    print(f"Title:       {study_title}")
    print(f"Description: {study_description}")
    print(f"Tags:        {study_tags}")
    print(f"PDF dest:    {dest_pdf}")

    if dry_run:
        print("\nDry run — no files changed.")
        return

    STUDIES.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf_path, dest_pdf)
    print(f"Copied PDF to {dest_pdf}")

    if not dest_md.exists() or force:
        dest_md.write_text(build_stub_markdown(study_title, study_description), encoding="utf-8")
        print(f"Wrote stub markdown to {dest_md}")

    index_path = STUDIES / "index.html"
    readme_path = STUDIES / "README.md"
    ref_readme_path = REFERENCES / "README.md"
    manifest_path = REFERENCES / "MANIFEST.md"

    index_text = index_path.read_text(encoding="utf-8")
    html_rows = parse_html_rows(index_text)
    html_rows = upsert_row(html_rows, derived_slug, (derived_slug, study_description))
    index_html_block = "\n".join(html_row(slug, desc) for slug, desc in html_rows)
    index_path.write_text(replace_catalog_block(index_text, index_html_block), encoding="utf-8")
    print(f"Updated {index_path}")

    readme_text = readme_path.read_text(encoding="utf-8")
    md_rows = parse_md_rows(readme_text)
    md_rows = upsert_row(md_rows, derived_slug, (derived_slug, study_description))
    readme_md_block = STUDIES_README_TABLE_HEADER + "\n" + "\n".join(
        readme_row(slug, desc) for slug, desc in md_rows
    )
    readme_path.write_text(replace_catalog_block(readme_text, readme_md_block), encoding="utf-8")
    print(f"Updated {readme_path}")

    ref_text = ref_readme_path.read_text(encoding="utf-8")
    ref_rows = parse_references_readme_rows(ref_text)
    ref_rows = upsert_row(ref_rows, derived_slug, (derived_slug, study_tags))
    ref_block = REFERENCES_README_TABLE_HEADER + "\n" + "\n".join(
        references_readme_row(slug, t) for slug, t in ref_rows
    )
    ref_readme_path.write_text(replace_catalog_block(ref_text, ref_block), encoding="utf-8")
    print(f"Updated {ref_readme_path}")

    manifest_text = manifest_path.read_text(encoding="utf-8")
    if f"{derived_slug}.pdf" in manifest_text and force:
        manifest_text = re.sub(
            rf"\| \[{re.escape(derived_slug)}\.pdf\]\(../Studies/{re.escape(derived_slug)}\.pdf\) \|[^\n]+\n",
            "",
            manifest_text,
        )
    manifest_path.write_text(
        append_manifest_row(manifest_text, derived_slug, study_tags),
        encoding="utf-8",
    )
    print(f"Updated {manifest_path}")

    print("\nDone. Next steps:")
    print(f"  1. Edit {dest_md} — expand content and add a References section.")
    print(f"  2. Update tag details in {manifest_path} (change TBD to present/external rows as needed).")
    print(f"  3. Open {index_path} in a browser to verify the catalog.")
    print("  4. Commit the new .pdf, .md, and updated catalog files.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add a study PDF to Studies/ and update catalog files.",
    )
    parser.add_argument("pdf", type=Path, help="Path to the study PDF")
    parser.add_argument("--title", help="Study title (default: derived from filename)")
    parser.add_argument("--slug", help="Filename slug without extension (default: from title)")
    parser.add_argument("--description", help="One-line catalog description")
    parser.add_argument(
        "--tags",
        help='Primary citation tags for References/README (e.g. "MVD, SB, JV")',
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing PDF and catalog entry")
    args = parser.parse_args()

    pdf_path = args.pdf.resolve()
    add_study(
        pdf_path,
        title=args.title,
        slug=args.slug,
        description=args.description,
        tags=args.tags,
        dry_run=args.dry_run,
        force=args.force,
    )


if __name__ == "__main__":
    main()

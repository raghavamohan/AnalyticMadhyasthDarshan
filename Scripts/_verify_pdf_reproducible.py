#!/usr/bin/env python3
"""Assert the study PDF pipeline is reproducible: same markdown, same bytes.

Regenerates each named study twice and compares SHA-256 digests. This guards the
property that `Scripts/_pdf_metadata.py` exists to provide — Chrome and pdf-lib
both stamp wall-clock dates, and before those were pinned, every CI run pushed a
fresh multi-megabyte PDF for no change in content.

The two branches of the pipeline pin dates by different mechanisms, so covering
one of each is what makes this test meaningful:

* a **Released** study takes Chrome's output untouched, and its dates are patched
  in place at equal byte length;
* a **Draft** study passes through pdf-lib for the watermark, which rewrites the
  info dict into a compressed stream, so its dates are pinned there instead.

Note this rewrites each study's generated `.pdf` and `.html` in place — the
pipeline has no out-of-tree mode. That is harmless in CI. Locally, restore with
`git checkout -- Studies/<Slug>` afterwards if you have nothing else in flight.

Examples (from repo root):

    python Scripts/_verify_pdf_reproducible.py Nature-Of-Time Human-Behavior-And-Society
    python Scripts/_verify_pdf_reproducible.py --list-defaults
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import study_md, study_pdf  # noqa: E402
from _study_catalog import (  # noqa: E402
    StudyStatus,
    get_study_row,
    parse_status_md,
    regenerate_pdf,
)

# One Released and one Draft study, so both date-pinning mechanisms are covered.
DEFAULT_SLUGS = ("Nature-Of-Time", "Human-Behavior-And-Society")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_status(slug: str) -> StudyStatus:
    md_path = study_md(slug)
    md_status = parse_status_md(md_path.read_text(encoding="utf-8"))
    if md_status:
        return StudyStatus(md_status.lower())
    located = get_study_row(slug)
    if located is None:
        raise SystemExit(f"{slug}: no **Status:** line and no catalog row.")
    return located[0].status


def check_slug(slug: str) -> tuple[bool, str]:
    md_path = study_md(slug)
    if not md_path.is_file():
        raise SystemExit(f"Study markdown not found: {md_path}")
    pdf_path = study_pdf(slug)
    status = resolve_status(slug)
    if status == StudyStatus.ONGOING:
        return True, f"{slug}: skipped (Ongoing studies have no PDF)"

    regenerate_pdf(md_path, status)
    first = digest(pdf_path)
    regenerate_pdf(md_path, status)
    second = digest(pdf_path)

    label = f"{slug} ({status.value})"
    if first == second:
        return True, f"{label}: reproducible — {first[:16]}… ({pdf_path.stat().st_size} bytes)"
    return False, (
        f"{label}: NOT reproducible\n"
        f"    run 1 {first}\n"
        f"    run 2 {second}\n"
        "    Something in the pipeline is stamping non-deterministic data. See "
        "Scripts/_pdf_metadata.py."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate each study twice and assert the PDF bytes match.",
    )
    parser.add_argument("slugs", nargs="*", help=f"Study slugs (default: {' '.join(DEFAULT_SLUGS)})")
    parser.add_argument(
        "--list-defaults", action="store_true",
        help="Print the default slugs and exit",
    )
    args = parser.parse_args(argv)

    if args.list_defaults:
        print(" ".join(DEFAULT_SLUGS))
        return 0

    slugs = args.slugs or list(DEFAULT_SLUGS)
    failures = 0
    for slug in slugs:
        ok, message = check_slug(slug)
        print(("ok   " if ok else "FAIL ") + message)
        if not ok:
            failures += 1

    if failures:
        print(f"\n{failures} of {len(slugs)} study PDF(s) not reproducible.")
        return 1
    print(f"\nAll {len(slugs)} study PDF(s) reproducible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
import re
import sys
import zlib
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


def resolve_status(slug: str) -> StudyStatus:
    md_path = study_md(slug)
    md_status = parse_status_md(md_path.read_text(encoding="utf-8"))
    if md_status:
        return StudyStatus(md_status.lower())
    located = get_study_row(slug)
    if located is None:
        raise SystemExit(f"{slug}: no **Status:** line and no catalog row.")
    return located[0].status


ISO_TIMESTAMP_RE = re.compile(rb"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
PDF_DATE_RE = re.compile(rb"D:\d{14}")


def describe_difference(first: bytes, second: bytes) -> str:
    """Explain where two runs diverge, so a failure is actionable from the log."""
    lines = [f"    sizes: {len(first)} vs {len(second)}"]

    offsets = [i for i in range(min(len(first), len(second))) if first[i] != second[i]]
    if not offsets:
        lines.append("    common prefix identical; one file is longer")
        return "\n".join(lines)

    lines.append(f"    {len(offsets)} differing byte(s), first at offset {offsets[0]}")
    start = max(0, offsets[0] - 110)
    end = offsets[0] + 60
    lines.append(f"    run 1 context: {first[start:end]!r}")
    lines.append(f"    run 2 context: {second[start:end]!r}")

    # Timestamps are the usual culprit. Report every form we can spot, in both the
    # plain bytes and any decompressed object stream, so a compressed-away date
    # does not hide.
    for label, buf in (("run 1", first), ("run 2", second)):
        plain_pdf = sorted(set(PDF_DATE_RE.findall(buf)))
        plain_iso = sorted(set(ISO_TIMESTAMP_RE.findall(buf)))
        inflated_pdf: set[bytes] = set()
        inflated_iso: set[bytes] = set()
        for chunk in re.findall(rb"stream\r?\n(.*?)endstream", buf, re.S):
            try:
                raw = zlib.decompress(chunk)
            except zlib.error:
                continue
            inflated_pdf |= set(PDF_DATE_RE.findall(raw))
            inflated_iso |= set(ISO_TIMESTAMP_RE.findall(raw))
        lines.append(
            f"    {label} dates — plain: {plain_pdf + plain_iso} "
            f"in-stream: {sorted(inflated_pdf | inflated_iso)}"
        )
    return "\n".join(lines)


def check_slug(slug: str, runs: int = 2) -> tuple[bool, str]:
    md_path = study_md(slug)
    if not md_path.is_file():
        raise SystemExit(f"Study markdown not found: {md_path}")
    pdf_path = study_pdf(slug)
    status = resolve_status(slug)
    if status == StudyStatus.ONGOING:
        return True, f"{slug}: skipped (Ongoing/Planned entries have no public study PDF)"

    outputs: list[bytes] = []
    for _ in range(max(2, runs)):
        regenerate_pdf(md_path, status)
        outputs.append(pdf_path.read_bytes())

    digests = [hashlib.sha256(buf).hexdigest() for buf in outputs]
    label = f"{slug} ({status.value})"
    if len(set(digests)) == 1:
        return True, (
            f"{label}: reproducible across {len(outputs)} runs — "
            f"{digests[0][:16]}… ({len(outputs[0])} bytes)"
        )

    # Report against the first run that disagrees, not just run 2 — the divergence
    # may be intermittent and appear only on a later pass.
    odd = next(i for i, d in enumerate(digests) if d != digests[0])
    listing = "\n".join(f"    run {i + 1} {d}" for i, d in enumerate(digests))
    return False, (
        f"{label}: NOT reproducible ({len(set(digests))} distinct outputs in "
        f"{len(outputs)} runs)\n"
        f"{listing}\n"
        f"{describe_difference(outputs[0], outputs[odd])}\n"
        "    Something in the pipeline is stamping non-deterministic data. See "
        "Scripts/_pdf_metadata.py."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate each study twice and assert the PDF bytes match.",
    )
    parser.add_argument("slugs", nargs="*", help=f"Study slugs (default: {' '.join(DEFAULT_SLUGS)})")
    parser.add_argument(
        "--runs", type=int, default=2, metavar="N",
        help="Regenerations per study (minimum 2). Raise it to hunt an intermittent "
             "divergence.",
    )
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
        ok, message = check_slug(slug, args.runs)
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

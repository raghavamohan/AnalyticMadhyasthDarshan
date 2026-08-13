#!/usr/bin/env python3
"""Pin study PDF metadata so identical markdown yields identical bytes.

Two things in the output vary between runs on unchanged input: wall-clock dates
and Chrome's tagged-PDF structure node IDs.

Both branches of the PDF pipeline stamp wall-clock timestamps: Chrome writes
``/CreationDate`` and ``/ModDate`` into the info dict for Released studies, and
pdf-lib rewrites them when it draws the Draft watermark. Re-running the pipeline
on unchanged markdown therefore produced a byte-different PDF every time, which
defeated the "nothing changed" check in CI and pushed a fresh multi-megabyte
blob on every run of every study PR.

Normalising those two dates makes the output reproducible. This module patches
them **in place, at identical byte length**, so every xref offset stays valid and
no object is rewritten. Two alternatives were tried and rejected:

* A full re-save through pdf-lib remapped a subset font's encoding and flipped an
  apostrophe (U+2019) to an opening quote (U+2018) on two pages of *Nature of
  Time* — a visible regression, confirmed by pixel comparison.
* pypdf's incremental mode appends a corrected info object but leaves the
  original varying dates in the base bytes, so the file still differs run to run.

Chrome writes the dates as plain text in a fixed-width form
(``D:YYYYMMDDHHMMSS+00'00'``), which is what makes the equal-length swap safe.
The Draft branch keeps its dates inside a compressed object stream, where no such
patch is possible; ``_html_to_pdf.js`` pins those during the pdf-lib pass it
already performs for the watermark, so no extra rewrite is introduced there
either. This function simply reports how many fields it patched, and patching
nothing is a valid outcome for a Draft PDF.

The stamp is derived from the study's ``**Edited on:**`` line, so the PDF's dates
stay meaningful and change exactly when the study does. Months are matched from
an explicit table rather than ``%B`` because ``strptime`` month names are
locale-dependent, and the digits are treated as UTC because interpreting them in
local time would make the bytes depend on the build machine's timezone.

The second source of drift is the accessibility structure tree. When a document
contains a table, Chrome tags it and labels each structure element with an ID
drawn from a counter that is global to the browser session, not to the document
(``/ID (node00000155)``, ``/Headers [(node00000219)]``, and the ``/Names`` tree
that indexes them). The counter's starting value depends on what the renderer
did beforehand, so two builds of the same markdown emitted the same 39 IDs
shifted by a constant — hundreds of differing bytes describing an identical
document. Renumbering them from 1 in ascending order restores reproducibility.
Ascending order matters twice over: it keeps the byte length fixed, and because
the IDs are zero-padded to a fixed width their lexical order matches their
numeric order, so the ``/Names`` tree stays sorted and its ``/Limits`` stay
valid for binary search.
"""
from __future__ import annotations

import re
from pathlib import Path

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}

# Used when a document has no parseable `**Edited on:**` line.
FALLBACK_STAMP = "D:20200101000000+00'00'"

EDITED_ON_RE = re.compile(r"\*\*Edited on:\*\*\s*([^\r\n]+)", re.IGNORECASE)
DATE_RE = re.compile(
    r"^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4}),\s*(\d{1,2}):(\d{2})\s*([AaPp])\.?[Mm]",
)


def pdf_date_from_edited_on(text: str | None) -> str | None:
    """Convert ``June 30, 2026, 11:33 AM IST`` to a PDF date string."""
    if not text:
        return None
    match = DATE_RE.match(text.strip())
    if not match:
        return None
    month = MONTHS.get(match.group(1).lower())
    if month is None:
        return None
    hour = int(match.group(4)) % 12
    if match.group(6).lower() == "p":
        hour += 12
    return "D:%04d%02d%02d%02d%02d00+00'00'" % (
        int(match.group(3)), month, int(match.group(2)), hour, int(match.group(5)),
    )


def stamp_for_markdown(md_path: Path) -> str:
    """Deterministic PDF date stamp for a study markdown file."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_STAMP
    match = EDITED_ON_RE.search(text)
    stamp = pdf_date_from_edited_on(match.group(1) if match else None)
    return stamp or FALLBACK_STAMP


# The prefix and closing paren are captured so they can be re-emitted verbatim:
# reconstructing them (e.g. always inserting a space) would change the byte
# length whenever the source omitted one, shifting every later xref offset.
DATE_FIELD_RE = re.compile(rb"(/(?:CreationDate|ModDate)\s*\()(D:[^)]*)(\))")


def normalize_pdf_dates(pdf_path: Path, stamp: str) -> int:
    """Patch the PDF's dates in place at equal byte length.

    Returns the number of fields replaced. A field whose current value differs in
    length from ``stamp`` is left untouched, because changing the byte length
    would invalidate every following xref offset.
    """
    raw = pdf_path.read_bytes()
    target = stamp.encode("ascii")
    patched = 0

    def substitute(match: re.Match[bytes]) -> bytes:
        nonlocal patched
        if len(match.group(2)) != len(target):
            return match.group(0)
        patched += 1
        return match.group(1) + target + match.group(3)

    updated = DATE_FIELD_RE.sub(substitute, raw)
    if patched:
        assert len(updated) == len(raw), "date patch must not change file length"
        pdf_path.write_bytes(updated)
    return patched


# Matched with the enclosing string delimiters so the pattern cannot fire on
# coincidental bytes inside a font or image stream: Chrome only ever writes these
# as complete PDF strings — `/ID (node00000219)`, `/Headers [(node00000219)]`,
# and the `/Names` and `/Limits` arrays of the structure-tree name tree.
STRUCT_NODE_RE = re.compile(rb"\(node(\d{8})\)")
STRUCT_NODE_DIGITS = 8


def normalize_struct_node_ids(pdf_path: Path) -> int:
    """Renumber tagged-PDF structure node IDs from 1. Returns how many were renamed.

    Rewrites in place at equal byte length, like ``normalize_pdf_dates``, so no
    xref offset moves. Returns 0 when the document has no structure IDs (it has
    no tables) or when they are already canonical.
    """
    raw = pdf_path.read_bytes()
    old_ids = sorted({int(value) for value in STRUCT_NODE_RE.findall(raw)})
    # The upper bound keeps the replacement inside the fixed width; a document
    # with 10^8 structure elements would widen the field and shift every offset.
    if not old_ids or len(old_ids) >= 10**STRUCT_NODE_DIGITS:
        return 0

    renumbered = {old: new for new, old in enumerate(old_ids, start=1) if old != new}
    if not renumbered:
        return 0

    def substitute(match: re.Match[bytes]) -> bytes:
        old = int(match.group(1))
        return b"(node%0*d)" % (STRUCT_NODE_DIGITS, renumbered.get(old, old))

    updated = STRUCT_NODE_RE.sub(substitute, raw)
    assert len(updated) == len(raw), "node renumbering must not change file length"
    pdf_path.write_bytes(updated)
    return len(renumbered)


def normalize_study_pdf(md_path: Path, pdf_path: Path) -> str:
    """Make ``pdf_path`` reproducible; dates come from ``md_path``. Returns the stamp."""
    stamp = stamp_for_markdown(md_path)
    normalize_pdf_dates(pdf_path, stamp)
    normalize_struct_node_ids(pdf_path)
    return stamp


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Pin a study PDF's dates and structure node IDs for reproducible output.",
    )
    parser.add_argument("markdown", type=Path, help="Study markdown (source of the date)")
    parser.add_argument(
        "pdf", type=Path, nargs="?",
        help="PDF to normalize (default: the markdown's sibling .pdf)",
    )
    args = parser.parse_args(argv)

    md_path = args.markdown.expanduser().resolve()
    pdf_path = (args.pdf or md_path.with_suffix(".pdf")).expanduser().resolve()
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    stamp = stamp_for_markdown(md_path)
    dates = normalize_pdf_dates(pdf_path, stamp)
    nodes = normalize_struct_node_ids(pdf_path)
    print(f"Pinned {pdf_path.name}: {dates} date field(s) set to {stamp}, {nodes} node ID(s) renumbered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

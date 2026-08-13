"""Tests for the reproducibility patches applied to generated study PDFs."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _pdf_metadata import (
    normalize_pdf_dates,
    normalize_struct_node_ids,
    pdf_date_from_edited_on,
)

# A structure tree as Chrome writes it: elements carrying an /ID, a /Headers
# back-reference, and the name tree that indexes them with its /Limits.
TEMPLATE = (
    b"/Type /StructElem /ID (node%08d)\n"
    b"/Type /StructElem /ID (node%08d) /Headers [(node%08d)]\n"
    b"/Type /StructElem /ID (node%08d) /Headers [(node%08d)]\n"
    b"/Limits [(node%08d) (node%08d)]\n"
    b"/Names [(node%08d) 12 0 R (node%08d) 13 0 R (node%08d) 14 0 R]\n"
)


def _tagged_pdf(first: int, second: int, third: int) -> bytes:
    return TEMPLATE % (
        first,
        second, first,
        third, first,
        first, third,
        first, second, third,
    )


def _write(data: bytes) -> Path:
    handle = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    handle.write(data)
    handle.close()
    return Path(handle.name)


def test_shifted_counters_converge() -> None:
    """The bug: two runs number the same document from a different start."""
    first = _write(_tagged_pdf(155, 219, 905))
    second = _write(_tagged_pdf(156, 220, 906))
    assert first.read_bytes() != second.read_bytes()

    assert normalize_struct_node_ids(first) == 3
    assert normalize_struct_node_ids(second) == 3
    assert first.read_bytes() == second.read_bytes()
    assert b"(node00000001)" in first.read_bytes()


def test_byte_length_is_preserved() -> None:
    """Any change in length would invalidate every following xref offset."""
    path = _write(_tagged_pdf(9, 4013, 77))
    before = path.stat().st_size
    normalize_struct_node_ids(path)
    assert path.stat().st_size == before


def test_ascending_order_is_preserved() -> None:
    """The name tree is binary-searched, so /Names must stay sorted."""
    path = _write(_tagged_pdf(300, 40, 1200))
    normalize_struct_node_ids(path)
    text = path.read_bytes()
    assert b"/Limits [(node00000002) (node00000003)]" in text
    assert b"/Names [(node00000002) 12 0 R (node00000001) 13 0 R (node00000003) 14 0 R]" in text


def test_already_canonical_is_left_alone() -> None:
    path = _write(_tagged_pdf(1, 2, 3))
    before = path.read_bytes()
    assert normalize_struct_node_ids(path) == 0
    assert path.read_bytes() == before


def test_renumbering_is_idempotent() -> None:
    path = _write(_tagged_pdf(155, 219, 905))
    normalize_struct_node_ids(path)
    once = path.read_bytes()
    assert normalize_struct_node_ids(path) == 0
    assert path.read_bytes() == once


def test_untagged_pdf_is_untouched() -> None:
    path = _write(b"%PDF-1.4\n/Type /Page\n")
    before = path.read_bytes()
    assert normalize_struct_node_ids(path) == 0
    assert path.read_bytes() == before


def test_bare_digits_are_not_matched() -> None:
    """Guards against the pattern firing inside font or image stream bytes."""
    path = _write(b"stream\nnode00000155 node00000905\nendstream\n")
    before = path.read_bytes()
    assert normalize_struct_node_ids(path) == 0
    assert path.read_bytes() == before


def test_dates_are_pinned_at_equal_length() -> None:
    stamp = pdf_date_from_edited_on("August 13, 2026, 4:05 PM IST")
    assert stamp == "D:20260813160500+00'00'"
    path = _write(b"/CreationDate (D:20260101093000+00'00')/ModDate (D:20260102010203+00'00')")
    before = path.stat().st_size
    assert normalize_pdf_dates(path, stamp) == 2
    assert path.read_bytes().count(stamp.encode()) == 2
    assert path.stat().st_size == before


def main() -> int:
    tests = [
        test_shifted_counters_converge,
        test_byte_length_is_preserved,
        test_ascending_order_is_preserved,
        test_already_canonical_is_left_alone,
        test_renumbering_is_idempotent,
        test_untagged_pdf_is_untouched,
        test_bare_digits_are_not_matched,
        test_dates_are_pinned_at_equal_length,
    ]
    failed = 0
    for test in tests:
        name = test.__name__
        try:
            test()
            print(f"PASS {name}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {name}: {exc}")
    if failed:
        print(f"\n{failed} test(s) failed.")
        return 1
    print(f"\nAll {len(tests)} test(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

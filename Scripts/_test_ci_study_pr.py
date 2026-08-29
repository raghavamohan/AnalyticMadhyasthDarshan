"""Tests for the study-PR CI router and the PDF metadata pinning.

`_ci_study_pr.py` only ever executes inside GitHub Actions on a labelled pull
request, so a mistake in it surfaces as a broken study PR rather than a failed
local run. These tests cover the parts that decide behaviour — label dispatch,
slug resolution, the diff reader, and the rule that decides whether a PDF needs
rebuilding — by driving them with synthetic diffs and PR bodies.

Run from the repository root:

    python Scripts/_test_ci_study_pr.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import _ci_study_pr as ci
from _common import BASE
from _pdf_metadata import (
    FALLBACK_STAMP,
    normalize_pdf_dates,
    pdf_date_from_edited_on,
    stamp_for_markdown,
)

REAL_SLUG = "The-Ontology-of-Coexistence"


def _fake_diff(entries: list[tuple[str, str]]):
    """Return a `_git` stand-in that yields `entries` as --name-status output."""
    lines = "\n".join("\t".join(parts) for parts in entries) + "\n"

    def fake_git(*args: str) -> str:
        return lines if "--name-status" in args else ""

    return fake_git


def _with_diff(entries, fn):
    """Run `fn()` with `changed_paths` backed by a synthetic diff."""
    original = ci._git
    ci._git = _fake_diff(entries)
    ci.changed_paths.cache_clear()
    try:
        return fn()
    finally:
        ci._git = original
        ci.changed_paths.cache_clear()


# --------------------------------------------------------------- label dispatch
def test_handlers_cover_every_label() -> None:
    assert set(ci.HANDLERS) == set(ci.PR_LABELS)
    for label, handler in ci.HANDLERS.items():
        assert callable(handler), label


def test_active_pr_label() -> None:
    assert ci.active_pr_label([{"name": "study-update"}]) == "study-update"
    assert ci.active_pr_label([{"name": "documentation"}]) is None
    assert ci.active_pr_label([]) is None
    try:
        ci.active_pr_label([{"name": "new-study"}, {"name": "study-update"}])
    except SystemExit as exc:
        assert "only one study PR label" in str(exc)
    else:
        raise AssertionError("two study labels must be rejected")


# ------------------------------------------------------------------ slug parsing
def test_normalize_pr_slug_strips_trailing_notes() -> None:
    cases = {
        "The-Ontology-of-Coexistence": "The-Ontology-of-Coexistence",
        "The-Ontology-of-Coexistence.md": "The-Ontology-of-Coexistence",
        "The-Ontology-of-Coexistence (companion deck)": "The-Ontology-of-Coexistence",
        "The-Ontology-of-Coexistence — deck only": "The-Ontology-of-Coexistence",
        "  Nature-Of-Time  ": "Nature-Of-Time",
        "Nature-Of-Time, pptx only": "Nature-Of-Time",
    }
    for raw, expected in cases.items():
        assert ci.normalize_pr_slug(raw) == expected, raw


def test_resolve_slug_prefers_body_over_fallbacks() -> None:
    body = "Study slug: Nature-Of-Time\n"
    assert ci.resolve_slug(body, "origin/master", allow_changed=True) == "Nature-Of-Time"
    # Legacy `Slug:` key still accepted.
    assert ci.resolve_slug("Slug: Aesthetics\n") == "Aesthetics"


def test_resolve_slug_falls_back_to_rename_target() -> None:
    got = ci.resolve_slug("no slug here", "origin/master", rename=("Old-Name", "New-Name"))
    assert got == "New-Name"


def test_resolve_slug_falls_back_to_single_changed_study() -> None:
    entries = [("M", f"Studies/{REAL_SLUG}/{REAL_SLUG}.md")]
    got = _with_diff(entries, lambda: ci.resolve_slug("", "origin/master", allow_changed=True))
    assert got == REAL_SLUG


def test_resolve_slug_rejects_ambiguous_and_missing() -> None:
    # Two studies changed and no body field: cannot guess.
    entries = [
        ("M", f"Studies/{REAL_SLUG}/{REAL_SLUG}.md"),
        ("M", "Studies/Nature-Of-Time/Nature-Of-Time.md"),
    ]
    try:
        _with_diff(entries, lambda: ci.resolve_slug("", "origin/master", allow_changed=True))
    except SystemExit as exc:
        assert "Study slug:" in str(exc)
    else:
        raise AssertionError("ambiguous diff must be rejected")

    # status-change has no fallbacks at all.
    try:
        ci.resolve_slug("Target status: released")
    except SystemExit as exc:
        assert "Study slug:" in str(exc)
    else:
        raise AssertionError("missing slug must be rejected")


# -------------------------------------------------------------------- diff reader
def test_changed_paths_flattens_renames() -> None:
    entries = [("R100", "Studies/Old/Old.md", "Studies/New/New.md"), ("M", "README.md")]
    got = _with_diff(entries, lambda: ci.changed_paths("origin/master"))
    assert ("D", "Studies/Old/Old.md") in got
    assert ("A", "Studies/New/New.md") in got
    assert ("M", "README.md") in got


def test_detect_study_rename_from_git_record() -> None:
    entries = [("R100", "Studies/Old-Slug/Old-Slug.md", "Studies/New-Slug/New-Slug.md")]
    got = _with_diff(entries, lambda: ci.detect_study_rename("origin/master"))
    assert got == ("Old-Slug", "New-Slug")


def test_detect_study_rename_inferred_from_add_delete() -> None:
    entries = [
        ("D", "Studies/Old-Slug/Old-Slug.md"),
        ("A", "Studies/New-Slug/New-Slug.md"),
    ]
    got = _with_diff(entries, lambda: ci.detect_study_rename("origin/master"))
    assert got == ("Old-Slug", "New-Slug")


def test_study_was_removed_requires_a_complete_deletion() -> None:
    slug = "Removed-Study-For-CI-Test"
    deleted = [
        ("D", f"Studies/{slug}/{slug}.md"),
        ("D", f"Studies/{slug}/{slug}.pdf"),
    ]
    assert _with_diff(deleted, lambda: ci.study_was_removed("origin/master", slug)) is True

    mixed = deleted + [("A", f"Studies/{slug}/replacement.md")]
    assert _with_diff(mixed, lambda: ci.study_was_removed("origin/master", slug)) is False
    assert _with_diff(
        [("M", "Studies/README.md")],
        lambda: ci.study_was_removed("origin/master", slug),
    ) is False


def test_references_changed() -> None:
    assert _with_diff([("M", "References/MANIFEST.md")],
                      lambda: ci.references_changed("origin/master")) is True
    assert _with_diff([("M", "README.md")],
                      lambda: ci.references_changed("origin/master")) is False


# ------------------------------------------------------- PDF regeneration guard
def _reason(entries) -> str | None:
    return _with_diff(entries, lambda: ci.pdf_regeneration_reason("origin/master", REAL_SLUG))


def test_pdf_rebuild_when_markdown_changes() -> None:
    reason = _reason([("M", f"Studies/{REAL_SLUG}/{REAL_SLUG}.md")])
    assert reason and "markdown changed" in reason


def test_pdf_rebuild_when_study_figure_changes() -> None:
    reason = _reason([("M", f"Studies/{REAL_SLUG}/1-orders-planes.svg")])
    assert reason and "figure changed" in reason


def test_pdf_rebuild_when_pipeline_changes() -> None:
    for path in ("Scripts/_html_to_pdf.js", "Scripts/_convert_to_pdf.py",
                 "Scripts/_pdf_metadata.py", "Scripts/package-lock.json"):
        reason = _reason([("M", path)])
        assert reason and "pipeline changed" in reason, path


def test_pdf_skipped_for_companion_only_changes() -> None:
    """The case that motivated the guard: a deck-only study-update PR."""
    entries = [
        ("M", f"Studies/{REAL_SLUG}/The-Ontology-of-Existence-Madhyasth-Darshan.pptx"),
        ("M", f"Studies/{REAL_SLUG}/Presenters-Companion-Ontology-of-Existence.md"),
        ("M", f"Studies/{REAL_SLUG}/Presenters-Companion-Ontology-of-Existence.notes.json"),
    ]
    assert _reason(entries) is None


def test_pdf_skipped_for_unrelated_and_other_study_changes() -> None:
    assert _reason([("M", "Scripts/README.md"), ("M", "AGENTS.md")]) is None
    # A figure in a *different* study must not trigger this study's rebuild.
    assert _reason([("M", "Studies/Nature-Of-Time/1-some-figure.svg")]) is None


# ------------------------------------------------------------- PDF date pinning
def test_pdf_date_parsing() -> None:
    assert pdf_date_from_edited_on("June 30, 2026, 11:33 AM IST") == "D:20260630113300+00'00'"
    assert pdf_date_from_edited_on("July 26, 2026, 7:40 PM IST") == "D:20260726194000+00'00'"
    assert pdf_date_from_edited_on("January 1, 2026, 12:00 AM IST") == "D:20260101000000+00'00'"
    assert pdf_date_from_edited_on("December 9, 2025, 12:05 PM IST") == "D:20251209120500+00'00'"
    for bad in ("", None, "garbage", "Smarch 3, 2026, 1:00 AM"):
        assert pdf_date_from_edited_on(bad) is None, bad


def test_stamp_falls_back_when_markdown_has_no_edited_on() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "x.md"
        md.write_text("# Title\n\nNo edited-on line here.\n", encoding="utf-8")
        assert stamp_for_markdown(md) == FALLBACK_STAMP
        assert stamp_for_markdown(Path(tmp) / "missing.md") == FALLBACK_STAMP


def test_stamp_reads_real_study() -> None:
    md = BASE / "Studies" / REAL_SLUG / f"{REAL_SLUG}.md"
    if md.is_file():
        stamp = stamp_for_markdown(md)
        assert stamp.startswith("D:") and len(stamp) == len(FALLBACK_STAMP)


def test_date_patch_preserves_byte_length() -> None:
    stamp = "D:20260630113300+00'00'"
    original = (
        b"%PDF-1.7\n/Creator (x)\n/CreationDate (D:20260727041505+00'00')\n"
        b"/ModDate (D:20260727041506+00'00')\ntrailer\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "t.pdf"
        pdf.write_bytes(original)
        patched = normalize_pdf_dates(pdf, stamp)
        result = pdf.read_bytes()
        assert patched == 2, patched
        assert len(result) == len(original), "byte length must not change"
        assert result.count(stamp.encode()) == 2
        # Idempotent: a second pass changes nothing.
        pdf.write_bytes(result)
        normalize_pdf_dates(pdf, stamp)
        assert pdf.read_bytes() == result


def test_date_patch_skips_mismatched_length() -> None:
    """A differently-sized date is left alone rather than shifting xref offsets."""
    original = b"/CreationDate (D:2026)\n"
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "t.pdf"
        pdf.write_bytes(original)
        assert normalize_pdf_dates(pdf, "D:20260630113300+00'00'") == 0
        assert pdf.read_bytes() == original


def test_date_patch_preserves_spacing_variants() -> None:
    """No space after the key must stay that way, or offsets shift by one byte."""
    stamp = "D:20260630113300+00'00'"
    original = b"/CreationDate(D:20260727041505+00'00')\n"
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "t.pdf"
        pdf.write_bytes(original)
        assert normalize_pdf_dates(pdf, stamp) == 1
        result = pdf.read_bytes()
        assert len(result) == len(original)
        assert result.startswith(b"/CreationDate(D:2026063")


def test_handle_study_update_multi_study() -> None:
    """handle_study_update must process all changed study slugs when multiple studies are in the diff."""
    entries = [
        ("M", f"Studies/{REAL_SLUG}/{REAL_SLUG}.md"),
        ("M", "Studies/Nature-Of-Time/Nature-Of-Time.md"),
    ]
    slugs = _with_diff(entries, lambda: ci.changed_study_slugs("origin/master"))
    assert set(slugs) == {REAL_SLUG, "Nature-Of-Time"}


def main() -> int:
    tests = [obj for name, obj in sorted(globals().items())
             if name.startswith("test_") and callable(obj)]
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - test harness boundary
            failed += 1
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"ok   {test.__name__}")
    if failed:
        print(f"\n{failed} test(s) failed.")
        return 1
    print(f"\nAll {len(tests)} test(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

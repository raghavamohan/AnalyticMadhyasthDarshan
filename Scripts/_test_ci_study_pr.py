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

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

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


def test_git_diff_failure_is_not_treated_as_an_empty_change_set() -> None:
    original = ci.subprocess.run
    ci.subprocess.run = lambda *_args, **_kwargs: SimpleNamespace(
        returncode=128,
        stdout="",
        stderr="bad revision",
    )
    try:
        try:
            ci._git("diff", "missing...HEAD")
        except SystemExit as exc:
            assert "bad revision" in str(exc)
        else:
            raise AssertionError("Git failures must stop study PR routing")
    finally:
        ci.subprocess.run = original


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


def test_detect_study_rename_ignores_moved_companion_files() -> None:
    entries = [
        (
            "R100",
            "Studies/Old-Slug/diagram.svg",
            "Studies/New-Slug/diagram.svg",
        )
    ]
    got = _with_diff(entries, lambda: ci.detect_study_renames("origin/master"))
    assert got == []


def test_detect_multiple_canonical_study_renames() -> None:
    entries = [
        ("R100", "Studies/Old-One/Old-One.md", "Studies/New-One/New-One.md"),
        ("R100", "Studies/Old-Two/Old-Two.md", "Studies/New-Two/New-Two.md"),
    ]
    got = _with_diff(entries, lambda: ci.detect_study_renames("origin/master"))
    assert got == [("Old-One", "New-One"), ("Old-Two", "New-Two")]


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


def test_registry_row_removal_counts_as_retirement_cleanup() -> None:
    slug = "Metadata-Only-Study"
    registry = {
        "version": 1,
        "proposals": [{"slug": slug, "phase": "pre-catalog"}],
    }
    original_git = ci._git
    original_lookup = ci.registry_row_for_slug

    def fake_git(*args: str) -> str:
        if "--name-status" in args:
            return "M\tStudies/proposal-registry.json\n"
        if args[:1] == ("show",):
            return json.dumps(registry)
        raise AssertionError(f"Unexpected git call: {args}")

    ci._git = fake_git
    ci.registry_row_for_slug = lambda _slug: None
    ci.changed_paths.cache_clear()
    try:
        assert ci.registry_row_was_removed("origin/master", slug) is True
    finally:
        ci._git = original_git
        ci.registry_row_for_slug = original_lookup
        ci.changed_paths.cache_clear()


def test_portal_study_deletion_runs_supported_lifecycle() -> None:
    calls: list[tuple[str, object]] = []
    originals = {
        "resolve_slug": ci.resolve_slug,
        "reject_other_study_changes": ci.reject_other_study_changes,
        "verify_removal_metadata": ci.verify_removal_metadata,
        "run_reference_checks": ci.run_reference_checks,
        "subprocess_run": ci.subprocess.run,
    }
    try:
        ci.resolve_slug = lambda *_args, **_kwargs: "Remove-Me"
        ci.reject_other_study_changes = lambda *_args, **_kwargs: calls.append(("scope", None))
        ci.verify_removal_metadata = lambda slug: calls.append(("verify", slug))
        ci.run_reference_checks = lambda **kwargs: calls.append(("references", kwargs))
        ci.subprocess.run = lambda command, **_kwargs: calls.append(("run", command))
        ci.handle_study_update(
            "Study slug: Remove-Me\nOperation: delete-study\n",
            "origin/master",
        )
    finally:
        ci.resolve_slug = originals["resolve_slug"]
        ci.reject_other_study_changes = originals["reject_other_study_changes"]
        ci.verify_removal_metadata = originals["verify_removal_metadata"]
        ci.run_reference_checks = originals["run_reference_checks"]
        ci.subprocess.run = originals["subprocess_run"]

    run_command = next(value for name, value in calls if name == "run")
    assert str(run_command[1]).endswith("_remove_study.py")
    assert run_command[-2:] == ["Remove-Me", "--yes"]
    assert ("verify", "Remove-Me") in calls
    assert ("references", {"full_repo": True}) in calls


def test_references_changed() -> None:
    assert _with_diff([("M", "References/MANIFEST.md")],
                      lambda: ci.references_changed("origin/master")) is True
    assert _with_diff([("M", "README.md")],
                      lambda: ci.references_changed("origin/master")) is False


def test_changed_study_slugs_includes_multiple_removals() -> None:
    entries = [
        ("D", "Studies/Removed-One/Removed-One.md"),
        ("D", "Studies/Removed-One/Removed-One.pdf"),
        ("D", "Studies/Removed-Two/Removed-Two.md"),
    ]
    got = _with_diff(entries, lambda: ci.changed_study_slugs("origin/master"))
    assert got == ["Removed-One", "Removed-Two"]


def test_changed_study_slugs_ignores_generated_pdf_only_changes() -> None:
    entries = [
        ("D", "Studies/One/One.pdf"),
        ("M", "Applications/Two/Two.pdf"),
    ]
    got = _with_diff(entries, lambda: ci.changed_study_slugs("origin/master"))
    assert got == []


def test_single_purpose_labels_reject_other_study_changes() -> None:
    entries = [
        ("M", f"Studies/{REAL_SLUG}/{REAL_SLUG}.md"),
        ("M", "Studies/Nature-Of-Time/Nature-Of-Time.md"),
    ]

    def run():
        try:
            ci.reject_other_study_changes("origin/master", {REAL_SLUG}, "status-change")
        except SystemExit as exc:
            assert "Nature-Of-Time" in str(exc)
            assert "study-update" in str(exc)
        else:
            raise AssertionError("extra study changes must be rejected")

    _with_diff(entries, run)


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
    for path in (
        "Scripts/_html_to_pdf.js",
        "Scripts/_convert_to_pdf.py",
        "Scripts/_pdf_metadata.py",
        "Scripts/_render_katex_math.js",
        "Scripts/_glossary_tooltips.py",
        "Scripts/package-lock.json",
        "Studies/glossary.json",
        "Assets/KaTeX/fonts/KaTeX_Main-Regular.woff2",
        "requirements.txt",
        "CNAME",
    ):
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


def test_only_generated_html_change_is_allowed_for_ongoing_placeholder() -> None:
    slug = "Chitta-Brain-And-Memory"
    html_only = [("M", f"Studies/{slug}/{slug}.html")]
    assert _with_diff(html_only, lambda: ci.only_generated_html_changed("origin/master", slug)) is True

    source_change = [("M", f"Studies/{slug}/{slug}.md")]
    assert _with_diff(source_change, lambda: ci.only_generated_html_changed("origin/master", slug)) is False

    mixed_change = html_only + [("M", f"Studies/{slug}/figure.svg")]
    assert _with_diff(mixed_change, lambda: ci.only_generated_html_changed("origin/master", slug)) is False


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


# ------------------------------------------------- studies-index gate parity
def test_ci_gate_uses_the_shared_collector() -> None:
    """The PR gate must run the very checks the master-push gate runs.

    _ci_study_pr.py used to assemble its own subset (verify_all_catalog_sync +
    verify_index_shell_sync). The latter calls strip_catalog_blocks(), so it
    structurally cannot see the inlined bootstrap: a stale Studies/index.html
    passed its PR and turned master red only after the merge (#343).
    """
    import _verify_studies_index as vsi

    assert ci.collect_index_errors is vsi.collect_index_errors


def test_ci_gate_fails_on_every_collected_error() -> None:
    original = ci.collect_index_errors
    ci.collect_index_errors = lambda: ["sentinel drift"]
    try:
        message = None
        try:
            ci.verify_studies_index()
        except SystemExit as exc:
            message = str(exc)
        assert message is not None, "verify_studies_index must raise on errors"
        assert "sentinel drift" in message
    finally:
        ci.collect_index_errors = original


def test_collect_index_errors_runs_every_check() -> None:
    """verify_catalog_bootstrap_sync is the check that caught #343; keep it in.

    Listing the names explicitly is the point: a new check that is added to
    collect_index_errors() but not here would run unnoticed, and one that is
    dropped would go unnoticed too.
    """
    import _verify_studies_index as vsi

    names = [
        "verify_all_catalog_sync",
        "verify_index_shell_sync",
        "verify_catalog_bootstrap_sync",
        "verify_start_here_sync",
        "verify_discussion_pages",
    ]
    called: list[str] = []
    originals = {name: getattr(vsi, name) for name in names}

    def recorder(name):
        def _fn():
            called.append(name)
            return []
        return _fn

    try:
        for name in names:
            setattr(vsi, name, recorder(name))
        assert vsi.collect_index_errors() == []
    finally:
        for name, fn in originals.items():
            setattr(vsi, name, fn)
    assert called == names, called


# ------------------------------------------- index rebuild on catalog writes
def test_catalog_write_rebuilds_the_index_by_default() -> None:
    """Every catalog write must refresh Studies/index.html.

    write_studies_catalog() wrote catalog JSON, README, discussion pages and the
    sitemap but not the index, so _set_study_status.py left the landing page
    advertising a released study as Draft (#343).
    """
    import inspect

    import _build_studies_index as bsi
    import _study_catalog as sc

    default = inspect.signature(sc.write_studies_catalog).parameters["rebuild_index"].default
    assert default is True, "a catalog write must refresh the index unless told otherwise"
    assert callable(bsi.write_index_html)


def test_index_builder_opts_out_to_avoid_recursion() -> None:
    """main() rebuilds the index itself, so its own catalog writes must not."""
    import inspect

    import _build_studies_index as bsi

    code_lines = [
        line for line in inspect.getsource(bsi.main).splitlines()
        if not line.strip().startswith("#")
    ]
    hits = sum(line.count("rebuild_index=False") for line in code_lines)
    # one proposal sync + three per-table catalog writes
    assert hits == 4, hits


# ------------------------------------------------ Start-here pill generation
def test_render_start_here_status_writes_pills_from_the_catalog() -> None:
    """The pills were hand-maintained literals and two of 23 had drifted.

    syncStartHere() repaired them in the browser, so the drift was invisible
    there and wrong everywhere else: first paint, and any reader not running
    scripts.
    """
    import _build_studies_index as bsi
    from _study_catalog import StudyRow, StudyStatus

    markup = (
        '<div class="path-core" data-study-slug="Alpha">'
        '<span class="path-status draft" data-study-status>Draft</span></div>'
        '<li data-study-slug="Beta">'
        '<span class="path-status released" data-study-status>Released</span></li>'
    )
    rows = [
        StudyRow(slug="Alpha", category="", description="", status=StudyStatus.RELEASED),
        StudyRow(slug="Beta", category="", description="", status=StudyStatus.ONGOING),
    ]
    out = bsi.render_start_here_status(markup, rows)
    assert 'path-status released" data-study-status>Released' in out
    # ongoing has no Start-here word of its own, so it renders as planned,
    # matching the fallback in syncStartHere().
    assert 'path-status planned" data-study-status>In progress' in out


def test_render_start_here_status_leaves_unknown_slugs_alone() -> None:
    """syncStartHere() returns early for a slug the catalog does not carry."""
    import _build_studies_index as bsi

    markup = (
        '<li data-study-slug="Ghost">'
        '<span class="path-status planned" data-study-status>In progress</span></li>'
    )
    assert bsi.render_start_here_status(markup, []) == markup


def test_start_here_verifier_rejects_unknown_slug_after_rename_or_removal() -> None:
    import _build_studies_index as bsi

    markup = (
        '<li data-study-slug="Retired-Slug">'
        '<span class="path-status planned" data-study-status>In progress</span></li>'
    )
    errors = bsi.start_here_sync_errors(markup, {})
    assert len(errors) == 1 and "Retired-Slug" in errors[0]


def test_start_here_pill_regex_does_not_cross_entries() -> None:
    """An entry with no pill must not capture the next entry's pill."""
    import _build_studies_index as bsi

    markup = (
        '<li data-study-slug="NoPill"></li>'
        '<li data-study-slug="HasPill">'
        '<span class="path-status draft" data-study-status>Draft</span></li>'
    )
    found = [(m.group(2), m.group(3)) for m in bsi.START_HERE_PILL_RE.finditer(markup)]
    assert found == [("HasPill", "draft")], found


def test_shipped_index_start_here_matches_the_catalog() -> None:
    """The end-to-end guard: Studies/index.html against catalog-*.json."""
    import _build_studies_index as bsi

    assert bsi.verify_start_here_sync() == []


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

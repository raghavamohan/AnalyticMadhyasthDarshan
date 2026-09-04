"""Regression tests for add/remove/rename lifecycle edge cases."""
from __future__ import annotations

import json
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import _add_study as add
import _remove_study as remove
import _rename_study as rename
import _set_study_status as set_status
import _study_catalog as catalog
from _common import validate_study_slug
from _study_catalog import StudyRow, StudyStatus, StudyTable
from _study_links import cross_study_section_errors, links_to_slug, study_links_in_file


@contextmanager
def swapped(obj, **values):
    originals = {name: getattr(obj, name) for name in values}
    try:
        for name, value in values.items():
            setattr(obj, name, value)
        yield
    finally:
        for name, value in originals.items():
            setattr(obj, name, value)


def test_rename_only_changes_the_canonical_stem() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        studies = base / "Studies"
        applications = base / "Applications"
        old = studies / "Old-Slug"
        old.mkdir(parents=True)
        for name in (
            "Old-Slug.md",
            "Old-Slug.html",
            "Old-Slug.pdf",
            "Old-Slug-Madhyasth-Darshan.pptx",
            "Old-Slug-Madhyasth-Darshan.pdf",
            "Old-Slug-Madhyasth-Darshan-notes.pdf",
        ):
            (old / name).write_bytes(b"test")

        with swapped(rename, STUDIES=studies, APPLICATIONS=applications):
            rename.rename_study_files("Old-Slug", "New-Slug", dry_run=False)

        new = studies / "New-Slug"
        assert (new / "New-Slug.md").is_file()
        assert (new / "New-Slug.html").is_file()
        assert (new / "New-Slug.pdf").is_file()
        assert (new / "Old-Slug-Madhyasth-Darshan.pptx").is_file()
        assert (new / "Old-Slug-Madhyasth-Darshan.pdf").is_file()
        assert (new / "Old-Slug-Madhyasth-Darshan-notes.pdf").is_file()


def test_rename_preserves_catalog_position() -> None:
    rows = [
        StudyRow("First", "", "", StudyStatus.DRAFT, table=StudyTable.TOPICAL),
        StudyRow("Old-Slug", "", "", StudyStatus.DRAFT, table=StudyTable.TOPICAL),
        StudyRow("Last", "", "", StudyStatus.DRAFT, table=StudyTable.TOPICAL),
    ]
    captured: list[StudyRow] = []

    def fake_get(slug):
        return (rows[1], StudyTable.TOPICAL) if slug == "Old-Slug" else None

    def fake_write(updated, _table, **_kwargs):
        captured.extend(updated)

    with swapped(
        rename,
        get_study_row=fake_get,
        load_catalog_rows=lambda _table: list(rows),
        write_studies_catalog=fake_write,
    ):
        rename.update_catalog_row("Old-Slug", "New-Slug", "New title", dry_run=False)

    assert [row.slug for row in captured] == ["First", "New-Slug", "Last"]


def test_applied_study_meta_stays_under_applications() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        studies = base / "Studies"
        applications = base / "Applications"
        new_dir = applications / "New-Slug"
        new_dir.mkdir(parents=True)
        meta = new_dir / ".proposal-meta.json"
        meta.write_text(json.dumps({"slug": "Old-Slug", "proposalIssue": 7}), encoding="utf-8")

        with swapped(rename, STUDIES=studies, APPLICATIONS=applications):
            rename.update_proposal_meta_file(
                "Old-Slug",
                "New-Slug",
                "New title",
                7,
                dry_run=False,
            )

        assert not (studies / "New-Slug" / ".proposal-meta.json").exists()
        assert json.loads(meta.read_text(encoding="utf-8"))["slug"] == "New-Slug"


def test_rename_updates_reference_link_labels_and_targets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        refs = Path(tmp) / "References"
        refs.mkdir()
        for name in ("README.md", "MANIFEST.md"):
            (refs / name).write_text(
                "| [Old-Slug.pdf](../Studies/Old-Slug/Old-Slug.pdf) | tags |\n",
                encoding="utf-8",
            )
        with swapped(rename, REFERENCES=refs):
            rename.update_reference_paths("Old-Slug", "New-Slug", dry_run=False)
        for name in ("README.md", "MANIFEST.md"):
            text = (refs / name).read_text(encoding="utf-8")
            assert "[New-Slug.pdf](../Studies/New-Slug/New-Slug.pdf)" in text
            assert "Old-Slug" not in text


def test_rename_finishes_a_partially_preupdated_registry() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        studies = base / "Studies"
        applications = base / "Applications"
        studies.mkdir()
        registry = studies / "proposal-registry.json"
        registry.write_text(
            json.dumps(
                {
                    "version": 1,
                    "proposals": [
                        {
                            "slug": "New-Slug",
                            "title": "Old title",
                            "issueNumber": 19,
                            "category": "General",
                            "description": "Description",
                            "phase": "catalog-draft",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        with swapped(
            rename,
            STUDIES=studies,
            APPLICATIONS=applications,
            REGISTRY_PATH=registry,
        ):
            assert rename.resolve_issue_number("Old-Slug", None, "New-Slug") == 19
            rename.update_registry(
                "Old-Slug",
                "New-Slug",
                "New title",
                19,
                dry_run=False,
            )

        row = json.loads(registry.read_text(encoding="utf-8"))["proposals"][0]
        assert row["slug"] == "New-Slug"
        assert row["title"] == "New title"
        assert row["issueNumber"] == 19


def test_rename_requires_github_auth_before_local_mutation() -> None:
    local_mutation_started = False

    def fail_if_called(*_args, **_kwargs):
        nonlocal local_mutation_started
        local_mutation_started = True
        raise AssertionError("local mutation started before GitHub auth preflight")

    with (
        patch.dict(
            rename.os.environ,
            {"GITHUB_TOKEN": "", "GITHUB_REPOSITORY": ""},
        ),
        swapped(
            rename,
            resolve_issue_number=lambda *_args: 19,
            rename_study_files=fail_if_called,
        ),
    ):
        try:
            rename.rename_study(
                "Old-Slug",
                "New-Slug",
                skip_pdf=True,
                dry_run=False,
            )
        except SystemExit as exc:
            assert "must be set before renaming" in str(exc)
        else:
            raise AssertionError("rename proceeded without GitHub issue auth")

    assert local_mutation_started is False


def test_remove_registry_row_prevents_proposal_recreation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = Path(tmp) / "proposal-registry.json"
        registry.write_text(
            json.dumps(
                {
                    "version": 1,
                    "proposals": [
                        {"slug": "Keep"},
                        {"slug": "Remove-Me", "phase": "published"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        with swapped(remove, PROPOSAL_REGISTRY_PATH=registry):
            assert remove.remove_registry_row("Remove-Me", dry_run=True) is True
            assert len(json.loads(registry.read_text(encoding="utf-8"))["proposals"]) == 2
            assert remove.remove_registry_row("Remove-Me", dry_run=False) is True
        data = json.loads(registry.read_text(encoding="utf-8"))
        assert [row["slug"] for row in data["proposals"]] == ["Keep"]


def test_remove_study_unregisters_its_presentations() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        study_directory = base / "Studies" / "Remove-Me"
        study_directory.mkdir(parents=True)
        manifest = base / "Scripts" / "presentation-pipeline.json"
        manifest.parent.mkdir()
        manifest.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "decks": [
                        {"id": "remove", "source": "Studies/Remove-Me/Deck.pptx"},
                        {"id": "keep", "source": "Studies/Keep/Deck.pptx"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        with swapped(remove, BASE=base, PRESENTATION_MANIFEST_PATH=manifest):
            assert remove.remove_presentation_manifest_entries(
                "Remove-Me", dry_run=True, directory=study_directory
            ) == 1
            assert len(json.loads(manifest.read_text(encoding="utf-8"))["decks"]) == 2
            assert remove.remove_presentation_manifest_entries(
                "Remove-Me", dry_run=False, directory=study_directory
            ) == 1
        remaining = json.loads(manifest.read_text(encoding="utf-8"))["decks"]
        assert [deck["id"] for deck in remaining] == ["keep"]


def test_manifest_removal_preserves_other_citations() -> None:
    aliases = {"Why-Humans", "Why-Humans-Are-Not-Just-Material"}
    assert remove.strip_cited_in("Why-Humans, Aesthetics", aliases) == "Aesthetics"
    assert remove.strip_cited_in("Aesthetics, Why-Humans (Katha at p. 97)", aliases) == "Aesthetics"
    assert remove.strip_cited_in("Why-Humans", aliases).startswith("(none")
    assert remove.strip_cited_in("all Studies papers above", aliases) == "all Studies papers above"


def test_reference_readme_removal_handles_applied_rows() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        references = Path(tmp) / "References"
        references.mkdir()
        readme = references / "README.md"
        readme.write_text(
            "# References\n\n<!-- studies-catalog -->\n"
            "| Paper | Primary tags |\n|-------|----------------|\n"
            "| [Keep.pdf](../Studies/Keep/Keep.pdf) | MVD |\n"
            "| [Applied.pdf](../Applications/Applied/Applied.pdf) | SB |\n"
            "<!-- /studies-catalog -->\n",
            encoding="utf-8",
        )

        with swapped(catalog, REFERENCES=references):
            catalog.write_references_readme_row("Applied", "", remove=True)

        updated = readme.read_text(encoding="utf-8")
        assert "../Studies/Keep/Keep.pdf" in updated
        assert "Applied.pdf" not in updated


def test_reference_readme_add_preserves_applied_rows() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        references = Path(tmp) / "References"
        references.mkdir()
        readme = references / "README.md"
        readme.write_text(
            "# References\n\n<!-- studies-catalog -->\n"
            "| Paper | Primary tags |\n|-------|----------------|\n"
            "| [Applied.pdf](../Applications/Applied/Applied.pdf) | SB |\n"
            "<!-- /studies-catalog -->\n",
            encoding="utf-8",
        )

        with swapped(catalog, REFERENCES=references):
            catalog.write_references_readme_row("New-Study", "MVD")

        updated = readme.read_text(encoding="utf-8")
        assert "../Applications/Applied/Applied.pdf" in updated
        assert "../Studies/New-Study/New-Study.pdf" in updated


def test_manifest_removal_handles_applied_paper_blocks() -> None:
    content = (
        "| [Keep.pdf](../Studies/Keep/Keep.pdf) | MVD | present |\n"
        "| [Applied.pdf](../Applications/Applied/Applied.pdf) | SB | present |\n"
        "| | JV | external |\n"
        "| [After.pdf](../Studies/After/After.pdf) | KD | present |\n"
    )
    updated = catalog.remove_manifest_paper_block(content, "Applied")
    assert "Applied.pdf" not in updated
    assert "| | JV |" not in updated
    assert "Keep.pdf" in updated
    assert "After.pdf" in updated


def test_cross_study_section_changes_validate_inbound_and_outbound_links() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source_dir = base / "Studies" / "Source"
        target_dir = base / "Studies" / "Target"
        other_dir = base / "Studies" / "Other"
        source_dir.mkdir(parents=True)
        target_dir.mkdir(parents=True)
        other_dir.mkdir(parents=True)
        source = source_dir / "Source.md"
        target = target_dir / "Target.md"
        other = other_dir / "Other.md"
        source.write_text(
            "# Source\n\n[Target](../Target/Target.pdf) — details in §§1.1, 1.2; "
            "[Other](../Other/Other.pdf) §9.9\n"
            "[Primary source](../References/Book.pdf) §7.1\n",
            encoding="utf-8",
        )
        target.write_text("# Target\n\n## 1. First\n\n### 1.1 Present\n", encoding="utf-8")
        other.write_text("# Other\n\n## 9. Topic\n\n### 9.9 Present\n", encoding="utf-8")
        paths = [source, target, other]
        parsed = study_links_in_file(source, base=base)
        assert [(link.target_slug, link.sections) for link in parsed] == [
            ("Target", ("1.1", "1.2")),
            ("Other", ("9.9",)),
        ]

        inbound = cross_study_section_errors({"Target"}, paths=paths, base=base)
        outbound = cross_study_section_errors({"Source"}, paths=paths, base=base)
        assert len(inbound) == 1 and "1.2" in inbound[0]
        assert len(outbound) == 1 and "1.2" in outbound[0]

        target.write_text(
            "# Target\n\n## 1. First\n\n### 1.1 Present\n\n### 1.2 Restored\n",
            encoding="utf-8",
        )
        assert cross_study_section_errors({"Target"}, paths=paths, base=base) == []


def test_removed_slug_link_discovery_does_not_require_the_target_to_exist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source_dir = base / "Studies" / "Source"
        source_dir.mkdir(parents=True)
        source = source_dir / "Source.md"
        source.write_text(
            "# Source\n\n[Retired](../Retired/Retired.pdf) §1.1\n",
            encoding="utf-8",
        )
        found = links_to_slug("Retired", paths=[source], base=base)
        assert len(found) == 1 and found[0].target_slug == "Retired"


def test_study_slug_contract_is_shared_by_add_and_rename() -> None:
    validate_study_slug("Valid-Study-42")
    for bad in ("has spaces", "has_underscore", "x" * 61):
        try:
            validate_study_slug(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid slug accepted: {bad}")


def test_destructive_lifecycle_commands_reject_path_like_slugs() -> None:
    for normalize in (remove.normalize_slug, set_status.normalize_slug):
        try:
            normalize("../Outside")
        except SystemExit as exc:
            assert "Invalid study slug" in str(exc)
        else:
            raise AssertionError("path-like slug reached a destructive lifecycle command")

    try:
        rename.rename_study(
            "../Outside",
            "Valid-New-Slug",
            metadata_only=True,
            skip_issue=True,
            skip_pdf=True,
            dry_run=True,
        )
    except SystemExit as exc:
        assert "Invalid study slug" in str(exc)
    else:
        raise AssertionError("rename accepted a path-like source slug")


def test_ongoing_pdf_import_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "Proposal.pdf"
        pdf.write_bytes(b"%PDF-test")
        try:
            add.add_study(
                pdf,
                title="Proposal",
                slug="Proposal",
                category="",
                description="",
                tags="",
                status=StudyStatus.ONGOING,
                formal=False,
                dry_run=True,
                force=False,
                skip_pdf=False,
                check_timestamps=True,
                convert=False,
                no_keep_pdf=False,
            )
        except SystemExit as exc:
            assert "markdown only" in str(exc)
        else:
            raise AssertionError("ongoing PDF import must be rejected")


def main() -> int:
    tests = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
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

#!/usr/bin/env python3
"""Regression tests for the My Submissions companion-artifact registry."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import _companion_artifacts as artifacts

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE
from _companion_artifacts import OUTPUT, build_registry, render_registry

SUBMISSIONS_PAGE = BASE / "Studies" / "submit.html"
SUBMISSIONS_WORKER = BASE / "infra" / "worker" / "src" / "index.js"


def test_checked_in_registry_matches_repository() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render_registry()


def test_registry_paths_exist_and_are_safe() -> None:
    registry = build_registry()
    assert registry["schemaVersion"] == 1
    assert registry["studies"]
    for study in registry["studies"]:
        directory = BASE / study["root"] / study["slug"]
        assert (directory / f"{study['slug']}.md").is_file()
        for name in study["notes"]:
            assert name == Path(name).name
            assert (directory / name).is_file()
        for name in study["presentations"]:
            assert name == Path(name).name
            assert name.lower().endswith(".pptx")
            assert (directory / name).is_file()


def test_registry_tracks_multiple_and_deleted_companions() -> None:
    # Inventory assertions belong to a fixture: real companions may be retired.
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        directory = root / 'Applications/Example'
        directory.mkdir(parents=True)
        (root/'Scripts').mkdir()
        (root/'Scripts/companion-pipeline.json').write_bytes(b'{"schema":1,"companions":[]}')
        (root/'Scripts/presentation-pipeline.json').write_bytes(b'{"decks":[]}')
        catalog = root/'catalog.json'
        catalog.write_bytes(b'[{"slug":"Example","status":"draft"}]')
        names = ['Example.md','Technical-Note-One.md','Research-Note-Two.md','Deck-One.pptx','Deck-Two.pptx']
        for name in names:
            (directory/name).write_bytes(b'fixture')
        with patch.object(artifacts,'BASE',root), patch.object(artifacts,'CATALOGS',((catalog,root/'Applications','Applications'),)):
            row = build_registry()['studies'][0]
            assert len(row['notes']) == len(row['presentations']) == 2
            for name in names[1:]:
                (directory/name).unlink()
            row = build_registry()['studies'][0]
            assert row['notes'] == row['presentations'] == []
            assert (directory/'Example.md').is_file()


def test_my_submissions_groups_updates_inside_each_study_card() -> None:
    page = SUBMISSIONS_PAGE.read_text(encoding="utf-8")
    assert "Update existing study files" not in page
    assert 'class="submission-files"' in page
    assert "function renderSubmissionFiles(item)" in page
    assert "Manage files" in page
    assert "Edit, add or delete" in page
    assert "artifactUpdateUrl(item.slug, 'note', '__new__')" in page
    assert "artifactUpdateUrl(item.slug, 'presentation', '__new__')" in page
    assert "function inlineDeleteArtifact(" in page
    assert "'/api/delete-artifact'" in page
    assert "Type the study slug to confirm deletion" in page
    assert "isDashboard || isUpdate" in page
    assert "'Replace a presentation'" in page


def test_deletion_endpoint_is_registry_and_owner_guarded() -> None:
    worker = SUBMISSIONS_WORKER.read_text(encoding="utf-8")
    assert "router.post('/api/delete-artifact'" in worker
    assert "await assertStudyOwnedBySession(session, slug, env)" in worker
    assert "!registered.includes(targetName)" in worker
    assert "assertNoOpenStudyPr(slug" in worker
    assert "Operation: ${operation}" in worker


def main() -> int:
    tests = [obj for name, obj in sorted(globals().items())
             if name.startswith("test_") and callable(obj)]
    for test in tests:
        test()
        print(f"ok   {test.__name__}")
    print(f"\nAll {len(tests)} test(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

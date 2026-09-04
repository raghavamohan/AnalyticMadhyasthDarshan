#!/usr/bin/env python3
"""Tests for the R2 reference-artifact manifest."""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from _reference_artifacts import (
    ACTIVE_TRANSLATION_OUTPUT_PDFS,
    ACTIVE_TRANSLATION_RETAINED_PDFS,
    ACTIVE_TRANSLATION_SOURCE_PDFS,
    SITE_OWNER_APPROVED_PATHS,
    build_initial_manifest,
    load_manifest,
    manifest_errors,
)


def test_checked_in_manifest_matches_pre_migration_tree() -> None:
    initial = build_initial_manifest()
    actual = load_manifest()
    assert not manifest_errors(actual)
    initial_paths = {row["repo_path"] for row in initial["artifacts"]}
    actual_paths = {row["repo_path"] for row in actual["artifacts"]}
    assert initial_paths <= actual_paths


def test_scope_and_translation_exceptions() -> None:
    data = load_manifest()
    artifacts = data["artifacts"]
    assert len(artifacts) >= 53
    by_rel = {
        entry["repo_path"].removeprefix("References/"): entry for entry in artifacts
    }
    assert set(ACTIVE_TRANSLATION_RETAINED_PDFS) <= set(by_rel)
    for rel in ACTIVE_TRANSLATION_RETAINED_PDFS:
        assert by_rel[rel]["state"] == "git-retained"
        assert by_rel[rel]["target"]["storage"] == "git-retained-active-translation"
    assert all(
        by_rel[rel]["kind"] == "active-translation-source-pdf"
        for rel in ACTIVE_TRANSLATION_SOURCE_PDFS
    )
    assert all(
        by_rel[rel]["kind"] == "active-translation-output-pdf"
        for rel in ACTIVE_TRANSLATION_OUTPUT_PDFS
    )
    assert sum(
        entry["kind"] == "third-party-html-snapshot" for entry in artifacts
    ) == 12


def test_normalized_pdf_registration_contract() -> None:
    artifacts = load_manifest()["artifacts"]
    normalized = [row for row in artifacts if row.get("kind") == "normalized-reference-pdf"]
    for row in normalized:
        assert row["state"] in {"generated-local", "r2-published"}
        assert row["target"]["storage"] in {
            "r2-public",
            "external-only-rights-review",
        }
        if row["target"]["storage"] == "r2-public":
            assert row["target"]["public_url"].endswith(row["repo_path"])
        else:
            assert row["target"]["public_url"].startswith(("http://", "https://"))
        assert row["generation"]["source_markdown"].endswith(".md")
        assert row["generation"]["original_html"].endswith(".html")
        if row["target"]["storage"] == "r2-public":
            assert row["generation"]["pages"] > 0
            assert len(row["generation"]["text_sha256"]) == 64
        original = next(
            item for item in artifacts if item["repo_path"] == row["generation"]["original_html"]
        )
        assert original["target"]["storage"] == "r2-private-original"
        assert original["tags"] == []
        assert original["delivery"]["artifact_repo_path"] == row["repo_path"]


def test_unresolved_publication_rights_remain_git_served() -> None:
    artifacts = load_manifest()["artifacts"]
    unresolved = [
        row
        for row in artifacts
        if (row.get("rights") or {}).get("status") == "review-required"
        and row.get("kind") == "reference-pdf"
    ]
    assert unresolved
    assert all(row["target"]["storage"] == "git-retained-rights-review" for row in unresolved)


def test_approved_advaita_pdfs_are_r2_public() -> None:
    artifacts = load_manifest()["artifacts"]
    advaita = [
        row
        for row in artifacts
        if row["repo_path"].startswith("References/Advaita-Vedanta/")
        and row["repo_path"].endswith(".pdf")
    ]
    assert len(advaita) == 8
    assert {
        row["repo_path"].removeprefix("References/") for row in advaita
    } <= SITE_OWNER_APPROVED_PATHS
    assert all(row["rights"]["status"] == "existing-site-publication-approved" for row in advaita)
    assert all(row["target"]["storage"] == "r2-public" for row in advaita)
    assert all(row["target"]["r2_key"] == row["repo_path"] for row in advaita)


def test_manifest_rejects_duplicate_and_unsafe_keys() -> None:
    data = load_manifest()
    keyed_indexes = [
        index
        for index, entry in enumerate(data["artifacts"])
        if (entry.get("target") or {}).get("r2_key")
    ]
    assert len(keyed_indexes) >= 2
    first, second = keyed_indexes[:2]
    duplicate = copy.deepcopy(data)
    duplicate["artifacts"][second]["target"]["r2_key"] = duplicate["artifacts"][first][
        "target"
    ]["r2_key"]
    assert any("duplicate R2 key" in error for error in manifest_errors(duplicate))

    unsafe = copy.deepcopy(data)
    unsafe["artifacts"][first]["target"]["r2_key"] = "../escape.pdf"
    assert any("unsafe reference artifact path" in error for error in manifest_errors(unsafe))


def test_manifest_loader_requires_object_root() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "manifest.json"
        path.write_text(json.dumps([]), encoding="utf-8")
        try:
            load_manifest(path)
        except ValueError as exc:
            assert "root must be an object" in str(exc)
        else:
            raise AssertionError("list root should be rejected")


def main() -> int:
    tests = [
        test_checked_in_manifest_matches_pre_migration_tree,
        test_scope_and_translation_exceptions,
        test_normalized_pdf_registration_contract,
        test_unresolved_publication_rights_remain_git_served,
        test_approved_advaita_pdfs_are_r2_public,
        test_manifest_rejects_duplicate_and_unsafe_keys,
        test_manifest_loader_requires_object_root,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:  # pragma: no cover - CLI diagnostics
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

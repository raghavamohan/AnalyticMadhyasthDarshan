#!/usr/bin/env python3
"""Regression tests for the My Submissions companion-artifact registry."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _common import BASE
from _companion_artifacts import OUTPUT, build_registry, render_registry


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


def test_registry_has_known_multi_artifact_studies() -> None:
    by_slug = {row["slug"]: row for row in build_registry()["studies"]}
    epistemology = by_slug["The-Epistemology-of-Coexistence"]
    assert len(epistemology["notes"]) >= 2
    assert len(epistemology["presentations"]) >= 2
    ontology = by_slug["The-Ontology-of-Coexistence"]
    assert "Technical-Note-Roop-Guna-Svabhava-Dharma.md" in ontology["notes"]
    assert len(ontology["presentations"]) >= 2


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

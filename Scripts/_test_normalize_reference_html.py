#!/usr/bin/env python3
"""Tests for checked-in script-free reference normalizations.

The private original HTML is available while developing the normalizer and is
removed from Git after its checksum-verified R2 upload.  A fresh clone therefore
validates the reviewed Markdown output; a pre-cutover checkout also re-runs the
normalizer against the original bytes.
"""
from __future__ import annotations

from pathlib import Path

from _common import BASE
from _normalize_reference_html import normalize

CANARY = BASE / "References/Comparative-Philosophy/AV-Shankara-Stanford-Encyclopedia.html"
MCTAGGART = BASE / "References/Modern-Philosophy/McTaggart-1908-The-Unreality-of-Time.html"
CARROLL = BASE / "References/Science/Carroll-2010-Energy-Is-Not-Conserved.html"
POORVAM = BASE / "References/Comparative-Philosophy/Poorvam-Sadharanikarana-Rasa.html"


def normalized_text(source: Path) -> str:
    if source.is_file():
        return normalize(source)
    return source.with_suffix(".md").read_text(encoding="utf-8")


def test_sep_canary_preserves_article_structure() -> None:
    text = normalized_text(CANARY)
    assert text.startswith("# Śaṅkara\n")
    assert "## 1. Life and Works" in text
    assert "### 2.1 Existence, Reality, and Causation" in text
    assert "## Bibliography" in text
    assert "## Copyright" in text
    assert len(text) > 70_000


def test_sep_canary_removes_executable_and_navigation_content() -> None:
    folded = normalized_text(CANARY).casefold()
    for forbidden in ("<script", "<iframe", "<form", "javascript:", "search this archive"):
        assert forbidden not in folded


def test_sep_links_are_absolute_or_fragments() -> None:
    text = normalized_text(CANARY)
    assert "](https://" in text
    assert "](../../" not in text


def test_wikisource_profile_keeps_text_and_drops_site_chrome() -> None:
    text = normalized_text(MCTAGGART)
    assert text.startswith("# The Unreality of Time\n")
    assert "John McTaggart Ellis McTaggart" in text
    assert "It doubtless seems highly paradoxical" in text
    assert "sister projects" not in text
    assert len(text) > 40_000


def test_carroll_profile_keeps_post_and_excludes_comments() -> None:
    text = normalized_text(CARROLL)
    assert text.startswith("# Energy Is Not Conserved\n")
    assert "**Author:** Sean Carroll" in text
    assert "I’ve been meaning to link" in text
    assert "56 Comments" not in text
    assert len(text) > 6_000


def test_poorvam_profile_keeps_article_and_authors() -> None:
    text = normalized_text(POORVAM)
    assert text.startswith("# Sādhāraṇīkaraṇa")
    assert "Dr Rakesh Das; Prolay Nandi" in text
    assert "## Introduction" in text or "# Introduction" in text
    assert "Double-click any word" not in text
    assert len(text) > 35_000


def main() -> int:
    tests = [
        test_sep_canary_preserves_article_structure,
        test_sep_canary_removes_executable_and_navigation_content,
        test_sep_links_are_absolute_or_fragments,
        test_wikisource_profile_keeps_text_and_drops_site_chrome,
        test_carroll_profile_keeps_post_and_excludes_comments,
        test_poorvam_profile_keeps_article_and_authors,
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

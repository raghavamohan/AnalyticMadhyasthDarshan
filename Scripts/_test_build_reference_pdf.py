#!/usr/bin/env python3
"""Offline tests for safe reference reading HTML generation."""
from __future__ import annotations

import tempfile
from pathlib import Path

from _common import BASE
from _build_reference_pdf import _display_path, render_html

CANARY = BASE / "References/Comparative-Philosophy/AV-Shankara-Stanford-Encyclopedia.md"


def test_rendered_canary_is_safe_and_structured() -> None:
    rendered = render_html(CANARY)
    folded = rendered.casefold()
    assert "<h1" in folded and "śaṅkara" in folded
    assert "<h2" in folded and "bibliography" in folded
    for forbidden in ("<script", "<iframe", "<form", "javascript:", " onclick="):
        assert forbidden not in folded


def test_renderer_removes_executable_raw_html() -> None:
    # Exercise the final sanitizer independently of the HTML normalizer.
    original = CANARY.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "unsafe.md"
        path.write_text(original + '\n<script>alert(1)</script>\n', encoding="utf-8", newline="\n")
        rendered = render_html(path).casefold()
        assert "<script" not in rendered
        assert "alert(1)" not in rendered


def test_output_logging_accepts_runner_temp_outside_repository() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir).resolve() / "reference.pdf"
        assert _display_path(path) == str(path)


def main() -> int:
    tests = [
        test_rendered_canary_is_safe_and_structured,
        test_renderer_removes_executable_raw_html,
        test_output_logging_accepts_runner_temp_outside_repository,
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

#!/usr/bin/env python3
"""Focused tests for published study/reference link policy."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from _common import BASE
from _verify_published_document_links import verify_html


def test_repository_pages_satisfy_link_contract() -> None:
    from _verify_published_document_links import _document_html_paths

    failures = [
        f"{path.relative_to(BASE)}: {error}"
        for path in _document_html_paths()
        for error in verify_html(path)
    ]
    assert not failures, "\n".join(failures)


def test_cross_study_pdf_is_rejected() -> None:
    with tempfile.TemporaryDirectory(dir=BASE) as temp:
        path = Path(temp) / "source.html"
        path.write_text(
            '<a href="../Studies/Nature-Of-Time/Nature-Of-Time.pdf">time</a>',
            encoding="utf-8",
        )
        with patch(
            "_verify_published_document_links._site_target",
            return_value=("Studies/Nature-Of-Time/Nature-Of-Time.pdf", ""),
        ):
            assert any("must target HTML" in error for error in verify_html(path))


def test_explicit_study_pdf_download_is_allowed() -> None:
    with tempfile.TemporaryDirectory(dir=BASE) as temp:
        path = Path(temp) / "source.html"
        path.write_text(
            '<a href="../Studies/Nature-Of-Time/Nature-Of-Time.pdf" download>PDF</a>',
            encoding="utf-8",
        )
        with patch(
            "_verify_published_document_links._site_target",
            return_value=("Studies/Nature-Of-Time/Nature-Of-Time.pdf", ""),
        ):
            assert not verify_html(path)


def main() -> int:
    tests = [
        test_repository_pages_satisfy_link_contract,
        test_cross_study_pdf_is_rejected,
        test_explicit_study_pdf_download_is_allowed,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

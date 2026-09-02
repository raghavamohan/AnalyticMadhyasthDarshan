"""Tests for the fixed MSM source-page mapping and image-set checker."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _msm_render_page_images import (
    EXPECTED_PAGE_COUNT,
    check_outputs,
    logical_printed_page,
    output_name,
)


class MsmPageImageTests(unittest.TestCase):
    def test_front_matter_uses_pdf_page_as_logical_key(self) -> None:
        self.assertEqual(logical_printed_page(1), 1)
        self.assertEqual(logical_printed_page(12), 12)
        self.assertEqual(output_name(12), "p012_print012.png")

    def test_body_restarts_at_printed_page_one(self) -> None:
        self.assertEqual(logical_printed_page(13), 1)
        self.assertEqual(logical_printed_page(266), 254)
        self.assertEqual(output_name(13), "p013_print001.png")
        self.assertEqual(output_name(266), "p266_print254.png")

    def test_trailing_pages_continue_the_logical_sequence(self) -> None:
        self.assertEqual(output_name(267), "p267_print255.png")
        self.assertEqual(output_name(268), "p268_print256.png")

    def test_checker_requires_exact_nonempty_image_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            for page in range(1, EXPECTED_PAGE_COUNT + 1):
                (out_dir / output_name(page)).write_bytes(b"png")
            self.assertEqual(check_outputs(out_dir), [])

            (out_dir / output_name(2)).unlink()
            (out_dir / output_name(3)).write_bytes(b"")
            (out_dir / "unexpected.png").write_bytes(b"png")
            issues = check_outputs(out_dir)
            self.assertTrue(any("missing 1 image" in issue for issue in issues))
            self.assertTrue(any("unexpected 1 image" in issue for issue in issues))
            self.assertTrue(any("empty 1 image" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()

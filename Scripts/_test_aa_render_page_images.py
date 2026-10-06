"""Tests for the fixed AA source-page mapping and image-set checker."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _aa_render_page_images import (
    EXPECTED_PAGE_COUNT,
    check_outputs,
    logical_printed_page,
    output_name,
)


class AaPageImageTests(unittest.TestCase):
    def test_front_matter_uses_pdf_page_as_logical_key(self) -> None:
        self.assertEqual(logical_printed_page(1), 1)
        self.assertEqual(logical_printed_page(10), 10)
        self.assertEqual(output_name(10), "p010_print010.png")

    def test_body_restarts_at_printed_page_one(self) -> None:
        self.assertEqual(logical_printed_page(11), 1)
        self.assertEqual(logical_printed_page(159), 149)
        self.assertEqual(output_name(11), "p011_print001.png")
        self.assertEqual(output_name(159), "p159_print149.png")

    def test_trailing_pages_continue_the_logical_sequence(self) -> None:
        self.assertEqual(output_name(160), "p160_print150.png")
        self.assertEqual(output_name(164), "p164_print154.png")

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

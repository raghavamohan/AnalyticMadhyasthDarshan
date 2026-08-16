import hashlib
import tempfile
import unittest
from pathlib import Path

import _analyze_jeevan_pass_four as pass_four


class JeevanPassFourAnalysisTests(unittest.TestCase):
    def test_activity_coverage_and_selected_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            result = pass_four.run(
                pass_four.DEFAULT_ANONYMOUS,
                pass_four.DEFAULT_RESTORED,
                Path(directory),
            )
            self.assertEqual(result["member_count"], 122)
            self.assertEqual(result["channel_obligation_count"], 185)
            self.assertEqual(
                result["channel_member_counts"],
                {"U01": 59, "U02": 61, "U03": 23, "U04": 30, "U05": 12},
            )
            self.assertEqual(result["durability_class_counts"], {"D1": 2, "D2": 2, "D3": 118})
            self.assertTrue(
                all(
                    treatment["all_five_channels_present"]
                    for treatment in result["membership_threshold_sensitivity"].values()
                )
            )
            self.assertEqual(result["selected_bundle"], "B04")
            selected = next(
                bundle for bundle in result["bundle_comparisons"] if bundle["id"] == "B04"
            )
            self.assertEqual(selected["coverage_percent"], 100.0)
            self.assertEqual(selected["residual_member_count"], 0)
            self.assertTrue(selected["practical_minimal_at_selected_grain"])
            self.assertFalse(selected["numerical_uniqueness_established"])

    def test_outputs_are_anonymous_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            pass_four.run(pass_four.DEFAULT_ANONYMOUS, pass_four.DEFAULT_RESTORED, output_dir)
            first_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(output_dir.iterdir())
            }
            pass_four.run(pass_four.DEFAULT_ANONYMOUS, pass_four.DEFAULT_RESTORED, output_dir)
            second_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(output_dir.iterdir())
            }
            self.assertEqual(first_hashes, second_hashes)
            anonymous = (output_dir / pass_four.ANONYMOUS_OUTPUT).read_text(encoding="utf-8").lower()
            for term in pass_four.BANNED_ANONYMOUS_TERMS:
                self.assertNotRegex(anonymous, rf"\b{term}\b")


if __name__ == "__main__":
    unittest.main()

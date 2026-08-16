import hashlib
import tempfile
import unittest
from pathlib import Path

import _validate_jeevan_pass_five as pass_five


class JeevanPassFiveValidationTests(unittest.TestCase):
    def test_counterfactual_scope_and_conclusions(self):
        with tempfile.TemporaryDirectory() as directory:
            result = pass_five.run(
                pass_five.DEFAULT_COVERAGE,
                pass_five.DEFAULT_DIAGNOSTICS,
                Path(directory),
            )
            self.assertEqual(result["pass_four_member_count"], 122)
            self.assertEqual(result["pass_four_selected_bundle"], "B04")
            self.assertEqual(result["case_count"], 19)
            self.assertEqual(result["functions_tested"], ["U01", "U02", "U03", "U04", "U05"])
            self.assertEqual(result["safeguards_tested"], ["X01", "X02", "X03", "X04", "X05"])
            self.assertFalse(result["new_continuity_object_found"])
            self.assertEqual(result["family_invariant_condition_count"], 8)
            self.assertIn("Exactly five organizations is rejected", result["organization_conclusion"])

    def test_required_boundary_and_false_positive_cases_exist(self):
        rows = list(pass_five.CASES)
        by_id = {row["case_id"]: row for row in rows}
        self.assertEqual(by_id["FAM-01"]["analytical_result"], "equivalent-arrangement")
        self.assertEqual(by_id["FAM-02"]["analytical_result"], "arrangement-rejected")
        self.assertEqual(
            by_id["BND-01"]["analytical_result"],
            "combined-delivery-conditionally-adequate",
        )
        self.assertEqual(by_id["BND-02"]["analytical_result"], "arrangement-rejected")
        self.assertEqual(by_id["UNI-01"]["analytical_result"], "universality-test-failed")
        self.assertTrue(any(row["challenge_class"] == "false-positive" for row in rows))
        self.assertTrue(any("ecological" in row["arrangement_or_condition"].lower() for row in rows))

    def test_outputs_are_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            pass_five.run(pass_five.DEFAULT_COVERAGE, pass_five.DEFAULT_DIAGNOSTICS, output_dir)
            first_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(output_dir.iterdir())
            }
            pass_five.run(pass_five.DEFAULT_COVERAGE, pass_five.DEFAULT_DIAGNOSTICS, output_dir)
            second_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(output_dir.iterdir())
            }
            self.assertEqual(first_hashes, second_hashes)


if __name__ == "__main__":
    unittest.main()

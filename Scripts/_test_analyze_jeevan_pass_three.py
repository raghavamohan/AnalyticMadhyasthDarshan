import hashlib
import tempfile
import unittest
from pathlib import Path

import _analyze_jeevan_pass_three as pass_three


class JeevanPassThreeAnalysisTests(unittest.TestCase):
    def test_parser_and_frozen_vector_cover_all_members(self):
        members = pass_three.build_members(pass_three.DEFAULT_SOURCE)
        self.assertEqual(len(members), 122)
        self.assertEqual(len({member.anonymous_id for member in members}), 122)
        self.assertTrue(all(len(member.tokens) == 16 for member in members))
        self.assertEqual(sum(member.residual for member in members), 34)

    def test_outputs_are_anonymous_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            first = pass_three.run(pass_three.DEFAULT_SOURCE, output_dir)
            paths = sorted(output_dir.iterdir())
            first_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
            }
            second = pass_three.run(pass_three.DEFAULT_SOURCE, output_dir)
            second_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
            }
            self.assertEqual(first["selected_resolutions"], {"coarse": 3, "middle": 8, "fine": 14})
            self.assertEqual(first["selected_resolutions"], second["selected_resolutions"])
            self.assertEqual(first_hashes, second_hashes)
            anonymous = (
                output_dir / "Research-Data-Jeevan-Pass-Three-Anonymous-Matrix.csv"
            ).read_text(encoding="utf-8").lower()
            for term in pass_three.BANNED_ANONYMOUS_TERMS:
                self.assertNotRegex(anonymous, rf"\b{term}\b")


if __name__ == "__main__":
    unittest.main()

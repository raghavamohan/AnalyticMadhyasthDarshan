"""Real SQLite regressions for discussion reply delivery and moderation."""
from pathlib import Path
import subprocess
import unittest

class DiscussionFeaturesTests(unittest.TestCase):
    def test_sqlite_worker_flows(self):
        result = subprocess.run(["node", str(Path(__file__).with_suffix(".mjs"))], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == "__main__":
    unittest.main()

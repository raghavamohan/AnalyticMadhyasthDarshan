"""Regression checks for dependency-free production monitoring and failure reports."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import _api_synthetics as synthetics


class SyntheticTests(unittest.TestCase):
    def test_startup_without_site_packages_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-S", str(Path(synthetics.__file__).resolve()), "--help"],
                cwd=directory, capture_output=True, text=True, timeout=30,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--json-out", result.stdout)

    def test_network_failures_produce_complete_report_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "reports" / "synthetics.json"
            with patch.object(synthetics, "request", side_effect=OSError("network unavailable")):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    result = synthetics.main(["--json-out", str(report_path)])
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(result, 1)
        self.assertFalse(report["success"])
        self.assertEqual(len(report["checks"]), 11)
        self.assertTrue(all(not check["ok"] for check in report["checks"]))
        self.assertTrue(all(check["detail"] == "network unavailable" for check in report["checks"]))
        self.assertEqual(json.loads(output.getvalue()), report)


if __name__ == "__main__":
    unittest.main()

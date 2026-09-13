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
        self.assertEqual(len(report["checks"]), 13)
        self.assertTrue(all(not check["ok"] for check in report["checks"]))
        self.assertTrue(all(check["detail"] == "network unavailable" for check in report["checks"]))
        self.assertEqual(json.loads(output.getvalue()), report)

    def test_mcp_http_success_with_tool_error_fails(self):
        for payload in ({"error": {"message": "failed"}}, {"result": {"isError": True}},
                        {"result": {"structuredContent": {"studies": []}}}):
            with self.subTest(payload=payload), patch.object(
                synthetics, "expect_json", return_value=(payload, "request-id", 1)
            ):
                self.assertFalse(synthetics.run_check("mcp", synthetics.mcp_search).ok)

    def test_empty_discussion_database_is_healthy(self):
        with patch.object(synthetics, "expect_json", return_value=(
            {"threads": [], "meta": {"total": 0}}, "request-id", 1
        )):
            self.assertTrue(synthetics.run_check("db", synthetics.discussion_read).ok)

    def test_invalid_discussion_result_fails(self):
        with patch.object(synthetics, "expect_json", return_value=({}, "request-id", 1)):
            self.assertFalse(synthetics.run_check("db", synthetics.discussion_read).ok)


if __name__ == "__main__":
    unittest.main()

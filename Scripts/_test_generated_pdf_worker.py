#!/usr/bin/env python3
"""Run the generated-PDF Worker behavior tests under Node."""
from __future__ import annotations

import subprocess
import unittest

from _common import BASE
from _publish_generated_pdf_worker import check_sources, remote_coverage_errors


class FakeHeadClient:
    def __init__(self, records):
        self.records = records

    def head_object(self, key):
        return self.records.get(key)


class GeneratedPdfWorkerTests(unittest.TestCase):
    def test_checked_in_allowlist_matches_generated_inventory(self) -> None:
        self.assertEqual(check_sources(), [])

    def test_worker_http_contract(self) -> None:
        completed = subprocess.run(
            ["node", str(BASE / "Scripts" / "_test_generated_pdf_worker.mjs")],
            cwd=BASE,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    def test_production_route_gate_requires_published_pdf_metadata(self) -> None:
        keys = ("Studies/Good/Good.pdf", "Studies/Missing/Missing.pdf")
        errors = remote_coverage_errors(FakeHeadClient({
            keys[0]: {
                "content-type": "application/pdf",
                "x-amz-meta-sha256": "abc",
            }
        }), keys)
        self.assertEqual(errors, [f"missing R2 object: {keys[1]}"])

    def test_production_route_gate_rejects_wrong_type_and_missing_checksum(self) -> None:
        key = "Studies/Bad/Bad.pdf"
        errors = remote_coverage_errors(FakeHeadClient({key: {"content-type": "text/plain"}}), (key,))
        self.assertEqual(errors, [
            f"R2 object is not application/pdf: {key}",
            f"R2 object has no publisher checksum metadata: {key}",
        ])


if __name__ == "__main__":
    unittest.main()

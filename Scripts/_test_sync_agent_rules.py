"""Regression tests for Git-index validation in _sync_agent_rules.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from _sync_agent_rules import check_opencode_index


class OpenCodeIndexSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        self.git("init", "--quiet")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def git(self, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

    def write_skill(self, root: str, name: str, body: str) -> Path:
        path = self.repo / root / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8", newline="\n")
        return path

    def test_matching_staged_fallback_copy_passes(self) -> None:
        body = "---\nname: demo\ndescription: Demo skill.\n---\n"
        self.write_skill(".agents/skills", "demo", body)
        self.write_skill(".opencode/skills", "demo", body)
        self.git("add", ".agents/skills", ".opencode/skills")

        self.assertEqual(check_opencode_index(self.repo), [])

    def test_stale_staged_fallback_copy_is_reported(self) -> None:
        old = "---\nname: demo\ndescription: Old.\n---\n"
        new = "---\nname: demo\ndescription: New.\n---\n"
        self.write_skill(".agents/skills", "demo", old)
        self.write_skill(".opencode/skills", "demo", old)
        self.git("add", ".agents/skills", ".opencode/skills")
        self.write_skill(".agents/skills", "demo", new)
        self.git("add", ".agents/skills/demo/SKILL.md")

        errors = check_opencode_index(self.repo)

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "stale indexed .opencode/skills/demo/SKILL.md",
            errors[0],
        )

    def test_missing_and_orphan_staged_copies_are_reported(self) -> None:
        body = "---\nname: demo\ndescription: Demo skill.\n---\n"
        self.write_skill(".agents/skills", "canonical-only", body)
        self.write_skill(".opencode/skills", "mirror-only", body)
        self.git("add", ".agents/skills", ".opencode/skills")

        errors = check_opencode_index(self.repo)

        self.assertTrue(
            any(
                "missing indexed .opencode/skills/canonical-only/SKILL.md" in error
                for error in errors
            )
        )
        self.assertTrue(
            any(
                "orphan indexed .opencode/skills/mirror-only/SKILL.md" in error
                for error in errors
            )
        )


if __name__ == "__main__":
    unittest.main()

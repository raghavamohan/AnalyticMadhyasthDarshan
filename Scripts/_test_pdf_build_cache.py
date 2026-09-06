#!/usr/bin/env python3
"""Regression checks for source invalidation and the PDF cache trust boundary."""
from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import _build_reference_pdfs as reference_builder
from _pdf_build_cache import BASE, COMMON_INPUTS, FAMILIES, fingerprint, seal, verify


class PdfBuildCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixtures = {name: "# fixture\n" for name in COMMON_INPUTS}
        fixtures.update({
            "Scripts/_build_markdown_pdfs.py": "from _shared import value\nhelper = '_convert_to_pdf.py'\n",
            "Scripts/_convert_to_pdf.py": "from _safe_study_html import clean\n",
            "Scripts/_safe_study_html.py": "clean = True\n",
            "Scripts/_build_reference_pdfs.py": "from _shared import value\n",
            "Scripts/_shared.py": "value = 1\n",
            "Scripts/_build_presentations.py": "from _presentation_pipeline import value\n",
            "Scripts/_presentation_pipeline.py": "value = 1\n",
            "Scripts/package-lock.json": "{}",
            "Scripts/_html_to_pdf.js": "// renderer\n",
            "Scripts/_pdf_helper.mjs": "// ESM helper\n",
            "Scripts/presentation-pipeline.json": "{}",
            "Studies/A/A.md": "# A\n",
            "Studies/A/figure.svg": "<svg/>\n",
            "Studies/A/A.html": "<main>A</main>\n",
            "Studies/A/Deck.pptx": "deck bytes",
            "Studies/catalog-topical.json": "[]",
            "Studies/submit.html": "portal",
            "References/r2-artifacts.json": "{}",
            "References/Source.md": "reference source",
            "Assets/KaTeX/fonts/font.woff2": "font bytes",
            "Assets/reader/reader.css": "@media screen { body { color: black; } }",
            "Assets/reader/reader.js": "// browser reader",
            "infra/worker/src/index.js": "portal worker",
        })
        for name, value in fixtures.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value.encode("utf-8"))
        self.git("init", "-q")
        self.git("add", ".")

    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def keys(self, image: str = "fixture-image") -> dict[str, str]:
        return {family: fingerprint(family, self.root, image=image) for family in FAMILIES}

    def test_only_affected_build_families_are_invalidated(self) -> None:
        initial = self.keys()
        cases = {
            "Studies/A/A.md": {"markdown"},
            "Studies/A/figure.svg": {"markdown"},
            "Studies/catalog-topical.json": {"markdown"},
            "Studies/A/Deck.pptx": {"presentations"},
            "References/Source.md": {"references"},
            "References/r2-artifacts.json": {"markdown", "references"},
            "Scripts/_safe_study_html.py": {"markdown"},
            "Scripts/_shared.py": {"markdown", "references"},
            "Scripts/package-lock.json": {"markdown", "references"},
            "Scripts/_html_to_pdf.js": {"markdown", "references"},
            "Scripts/_pdf_helper.mjs": {"markdown", "references"},
            "requirements.txt": set(FAMILIES),
            "Assets/KaTeX/fonts/font.woff2": set(FAMILIES),
            "Assets/reader/reader.css": set(),
            "Assets/reader/reader.js": set(),
            "Studies/A/A.html": set(),
            "Studies/submit.html": set(),
            "infra/worker/src/index.js": set(),
        }
        for name, expected in cases.items():
            with self.subTest(path=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n# changed\n")
                actual = self.keys()
                self.assertEqual({family for family in FAMILIES if actual[family] != initial[family]}, expected)
                path.write_bytes(original)
        self.assertEqual(self.keys(), initial)
        self.assertTrue(all(self.keys("new-runner-image")[family] != initial[family] for family in FAMILIES))

    def test_addition_removal_and_link_target_names_invalidate(self) -> None:
        original = self.keys()
        source = self.root / "Studies/A/Note.md"
        source.write_bytes(b"# New note\n")
        self.git("add", "Studies/A/Note.md")
        self.assertNotEqual(self.keys()["markdown"], original["markdown"])
        self.git("rm", "--cached", "Studies/A/Note.md")
        source.unlink()
        self.assertEqual(self.keys(), original)
        target = self.root / "Studies/A/Note.html"
        target.write_bytes(b"reader")
        self.git("add", "Studies/A/Note.html")
        self.assertNotEqual(self.keys()["markdown"], original["markdown"])
        before_removal = self.keys()
        self.git("rm", "--cached", "Studies/A/A.md")
        (self.root / "Studies/A/A.md").unlink()
        self.assertNotEqual(self.keys()["markdown"], before_removal["markdown"])

    def test_complete_cached_tree_requires_exact_key_and_checksums(self) -> None:
        artifact_root = self.root / "artifacts"
        artifact_root.mkdir()
        pdf = artifact_root / "document.pdf"
        pdf.write_bytes(b"test PDF bytes")
        seal(artifact_root, "markdown", "input-key")
        verify(artifact_root, "markdown", "input-key")
        with self.assertRaises(ValueError):
            verify(artifact_root, "markdown", "old-input-key")
        original = pdf.read_bytes()
        pdf.write_bytes(b"damaged")
        with self.assertRaises(ValueError):
            verify(artifact_root, "markdown", "input-key")
        pdf.write_bytes(original)
        extra = artifact_root / "unexpected.pdf"
        extra.write_bytes(b"unexpected")
        with self.assertRaises(ValueError):
            verify(artifact_root, "markdown", "input-key")
        extra.unlink()
        pdf.unlink()
        with self.assertRaises(ValueError):
            verify(artifact_root, "markdown", "input-key")

    def test_empty_inventory_cannot_be_saved_as_a_complete_build(self) -> None:
        with self.assertRaises(ValueError):
            seal(self.root, "markdown", "key")

    def test_reference_cache_validation_never_renders_or_downloads(self) -> None:
        artifact_root = self.root / "reference-artifacts"
        pdf = artifact_root / "References/source.pdf"
        pdf.parent.mkdir(parents=True)
        body = b"immutable source PDF fixture"
        pdf.write_bytes(body)
        row = {"repo_path": "References/source.pdf", "kind": "source-pdf",
               "source": {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}}
        with patch.object(reference_builder, "load_manifest", return_value={}), \
             patch.object(reference_builder, "manifest_errors", return_value=[]), \
             patch.object(reference_builder, "public_rows", return_value=[row]), \
             patch.object(reference_builder, "ReferenceStore") as store, \
             patch.object(reference_builder, "build") as render:
            reference_builder.build_all(artifact_root, verify_only=True)
            render.assert_not_called()
            store.return_value.resolve.assert_not_called()
            pdf.write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                reference_builder.build_all(artifact_root, verify_only=True)

    def test_workflow_limits_cache_writes_and_keeps_publication_gates(self) -> None:
        workflow = (BASE / ".github/workflows/generated-pdf-publish.yml").read_text(encoding="utf-8")
        for block in workflow.split("      - name: ")[1:]:
            if "uses: actions/cache/save@v6" in block:
                self.assertIn("github.ref == 'refs/heads/master'", block)
                self.assertIn("github.event_name != 'pull_request'", block)
            if "uses: actions/cache/restore@v6" in block:
                self.assertNotIn("restore-keys:", block)
                self.assertTrue("github.event_name == 'push'" in block or
                                "github.event_name != 'workflow_dispatch'" in block)
        publication = workflow.split("\n  publish-and-deploy:\n", 1)[1]
        self.assertIn("needs: [pdfs, presentations]", publication)
        self.assertIn("github.ref == 'refs/heads/master'", publication)
        self.assertIn("--check-r2-coverage", publication)
        self.assertIn("--check-reference-r2-coverage", publication)
        self.assertIn("--deploy-canary", publication)
        self.assertIn("--public --all", publication)


if __name__ == "__main__":
    unittest.main()

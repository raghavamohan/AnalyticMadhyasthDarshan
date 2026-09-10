#!/usr/bin/env python3
"""Regression checks for source invalidation and the PDF cache trust boundary."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import _build_reference_pdfs as reference_builder
from _pdf_build_cache import (
    BASE,
    FAMILIES,
    affected_families,
    fingerprint,
    seal,
    verify,
)


class PdfBuildCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixtures = {
            'CNAME': 'example.test', 'requirements.txt': 'dependencies',
            'Scripts/_study_pdf_pipeline.py': 'from _convert_to_pdf import convert\nfrom _study_pdf_metadata import metadata\n',
            'Scripts/_convert_to_pdf.py': 'from _safe_study_html import clean\n',
            'Scripts/_safe_study_html.py': 'clean = True',
            'Scripts/_study_pdf_metadata.py': 'metadata = True',
            'Scripts/_study_catalog.py': 'catalog only',
            'Scripts/_build_reference_pdfs.py': 'approved immutable staging',
            'Scripts/_build_presentations.py': 'from _presentation_pipeline import value',
            'Scripts/_presentation_pipeline.py': 'value = 1',
            'Scripts/package-lock.json': '{}',
            'Scripts/_html_to_pdf.js': '// renderer',
            'Scripts/presentation-pipeline.json': json.dumps({'productionProfile': 'pinned',
                'rendererProfiles': {'pinned': {'version': '1'}}, 'decks': [{'id': 'a',
                'source': 'Studies/A/Deck.pptx', 'slidesPdf': 'Studies/A/Deck.pdf',
                'notesPdf': 'Studies/A/Deck-notes.pdf'}]}),
            'Studies/A/A.md': '# A\n\n![figure](figure.svg)\n',
            'Studies/A/figure.svg': '<svg/>', 'Studies/A/A.html': '<main>A</main>',
            'Studies/A/Deck.pptx': 'deck bytes',
            'Studies/catalog-topical.json': '[{"slug":"A","status":"draft"}]',
            'Studies/glossary.json': '{"terms":[]}', 'Studies/submit.html': 'portal',
            'References/r2-artifacts.json': json.dumps({'artifacts': [{
                'kind': 'normalized-reference-pdf', 'state': 'r2-published',
                'repo_path': 'References/Source.pdf', 'source': {'sha256': 'a'*64, 'bytes': 123},
                'generation': {'source_markdown': 'References/Source.md'},
                'target': {'storage': 'r2-public', 'r2_key': 'References/Source.pdf'}}]}),
            'References/Source.md': 'reference source', 'References/README.md': 'catalog',
            'Assets/KaTeX/fonts/font.woff2': 'font bytes',
            'Assets/reader/reader.js': '// browser only', 'reader-sw.js': '// offline only',
        }
        for name, value in fixtures.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value.encode("utf-8"))
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                 "commit", "-qm", "fixture")

    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def keys(self, image: str = "fixture-image") -> dict[str, str]:
        return {family: fingerprint(family, self.root, image=image) for family in FAMILIES}

    def test_only_affected_build_families_are_invalidated(self) -> None:
        initial = self.keys()
        cases = {
            'Studies/A/A.md': {'markdown'}, 'Studies/A/figure.svg': {'markdown'},
            'Studies/A/Deck.pptx': {'presentations'}, 'References/Source.md': {'references'},
            'Scripts/_build_reference_pdfs.py': {'references'},
            'Scripts/_safe_study_html.py': {'markdown'}, 'Scripts/_study_pdf_metadata.py': {'markdown'},
            'Scripts/_html_to_pdf.js': {'markdown'}, 'requirements.txt': {'markdown', 'presentations'},
            'Assets/KaTeX/fonts/font.woff2': {'markdown'},
            'References/README.md': set(), 'Scripts/_study_catalog.py': set(),
            'Assets/reader/reader.js': set(), 'reader-sw.js': set(),
            'Studies/A/A.html': set(), 'Studies/submit.html': set(),
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
        self.assertEqual(self.keys("new-runner-image"), initial)

    def test_change_plan_excludes_catalog_only_code(self) -> None:
        self.assertEqual(affected_families({"Scripts/_study_catalog.py"}, self.root), set())
        self.assertEqual(
            affected_families({"Scripts/_study_pdf_metadata.py"}, self.root),
            {"markdown"},
        )
        self.assertEqual(
            affected_families({"References/Source.md"}, self.root),
            {"references"},
        )
        self.assertEqual(
            affected_families({"References/README.md"}, self.root),
            set(),
        )

    def test_shared_glossary_is_reader_only(self) -> None:
        path = self.root / "Studies/glossary.json"
        initial = self.keys()
        path.write_text(
            '{"terms":[{"id":"satta","match":["satta"],'
            '"display":"Space","definition":"Updated tooltip."}]}\n',
            encoding="utf-8",
        )
        self.assertEqual(self.keys(), initial)
        self.assertEqual(
            affected_families(
                {"Studies/glossary.json"},
                self.root,
            ),
            set(),
        )

        path.write_text(
            '{"terms":[{"id":"satta","match":["satta","space"],'
            '"display":"Space","definition":"Updated tooltip."}]}\n',
            encoding="utf-8",
        )
        self.assertEqual(self.keys(), initial)
        self.assertEqual(
            affected_families(
                {"Studies/glossary.json"},
                self.root,
            ),
            set(),
        )

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
        self.assertEqual(self.keys()["markdown"], original["markdown"])
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
        workflow = (BASE / '.github/workflows/generated-pdf-publish.yml').read_text(encoding='utf-8')
        self.assertIn("if: github.ref == 'refs/heads/master' && github.event_name != 'pull_request'", workflow)
        coherent = workflow.split('\n  coherent-site:\n', 1)[1]
        self.assertIn('needs: [plan, validate, pdfs, presentations]', coherent)
        self.assertIn("needs.validate.result == 'success'", coherent)
        self.assertIn('--verify-approved', coherent)
        self.assertIn('--plan "$RUNNER_TEMP/publication-plan.json"', coherent)
        self.assertIn('_publish_site_release.py', coherent)
        self.assertIn('secrets.CLOUDFLARE_API_TOKEN', coherent)
        self.assertNotIn('publish-and-deploy:', workflow)
        self.assertIn("needs.plan.outputs.any_build == 'true'", coherent)


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Tests for generated-PDF inventory and R2 publisher behavior."""
from __future__ import annotations

import os
import tempfile
import unittest
import uuid
from unittest.mock import patch
from pathlib import Path

import fitz

from _generated_pdf_inventory import GeneratedPdfSpec, generated_pdf_specs, inventory_errors
from _publish_generated_pdfs import (
    delete_removed_objects,
    main,
    publish_artifacts,
    removed_object_keys,
    stale_object_keys,
    verify_artifacts,
)
from _publish_reference_artifacts import (
    _object_matches_manifest,
    _source_path as reference_source_path,
)
from _r2_s3 import R2S3Client, load_r2_config
from _reference_artifacts import artifact_local_path


class FakeClient:
    def __init__(self, checksum: str = ""):
        self.headers = {"x-amz-meta-sha256": checksum, "content-length": "0"} if checksum else None
        self.puts: list[str] = []

    def head_object(self, key: str):
        return self.headers

    def put_object(self, key: str, body: bytes, *, metadata, cache_control, content_disposition):
        self.puts.append(key)
        self.headers = {
            "x-amz-meta-sha256": metadata["sha256"],
            "content-length": str(len(body)),
        }
        return self.headers


class FakeListingClient:
    def list_objects(self, prefix: str):
        if prefix == "Studies/":
            return [
                "Studies/Nature-Of-Time/Nature-Of-Time.pdf",
                "Studies/Retired/Retired.pdf",
            ]
        return ["Applications/Retired/Retired.pdf", "Applications/readme.txt"]


class FakeDeleteClient:
    def __init__(self, present: set[str]):
        self.present = set(present)
        self.deleted: list[str] = []

    def head_object(self, key: str):
        return {"content-length": "1"} if key in self.present else None

    def delete_object(self, key: str):
        self.deleted.append(key)
        self.present.discard(key)

class InventoryTests(unittest.TestCase):
    def test_inventory_covers_current_and_future_generated_pdfs(self) -> None:
        specs = generated_pdf_specs()
        self.assertEqual(inventory_errors(specs), [])
        self.assertEqual(len(specs), 46)
        self.assertFalse(any(
            spec.key == "Studies/Chitta-Brain-And-Memory/Chitta-Brain-And-Memory.pdf"
            for spec in specs
        ))
        self.assertEqual(sum(spec.kind == "markdown" for spec in specs), 32)
        self.assertEqual(sum(spec.kind == "presentation-slides" for spec in specs), 7)
        self.assertEqual(sum(spec.kind == "presentation-notes" for spec in specs), 7)
        self.assertEqual(
            __import__("subprocess").run(
                ["git", "ls-files", "--", "Studies/**/*.pdf", "Applications/**/*.pdf"],
                cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True, check=True,
            ).stdout.strip(),
            "",
        )

    def test_current_environment_aliases_resolve_without_exposing_values(self) -> None:
        config = load_r2_config({
            "R2_ENDPOINT": "https://example.r2.cloudflarestorage.com",
            "R2_ACCESS_KEY_ID": "id",
            "R2_SECRET_ACCESS_KEY": "secret",
            "R2_BUCKET_NAME": "bucket",
            "R2_REGION": "auto",
        }, dotenv_path=Path("missing.env"))
        self.assertEqual(config.region, "auto")
        self.assertEqual(config.bucket, "bucket")


class PublisherTests(unittest.TestCase):
    def _artifact(self, root: Path):
        source = root / "source.md"
        output = root / "document.pdf"
        source.write_text("source", encoding="utf-8")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "verified PDF")
        doc.save(output, no_new_id=True)
        doc.close()
        spec = GeneratedPdfSpec("Studies/Test/document.pdf", source, output, "markdown")
        # Configure output as if it were rooted at the repository for mapped_path.
        from _common import BASE
        configured = BASE / "Studies/Test/document.pdf"
        spec = GeneratedPdfSpec(spec.key, source, configured, spec.kind)
        target = root / "Studies/Test"
        target.mkdir(parents=True)
        output.replace(target / "document.pdf")
        return verify_artifacts((spec,), root)[0]

    def test_unchanged_checksum_is_not_uploaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            artifact = self._artifact(Path(temp))
            client = FakeClient(artifact.sha256)
            self.assertEqual(
                publish_artifacts([artifact], client, dry_run=False),
                [(artifact.spec.key, "unchanged")],
            )
            self.assertEqual(client.puts, [])

    def test_changed_checksum_uploads_and_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            artifact = self._artifact(Path(temp))
            client = FakeClient("different")
            self.assertEqual(
                publish_artifacts([artifact], client, dry_run=False),
                [(artifact.spec.key, "uploaded")],
            )
            self.assertEqual(client.puts, [artifact.spec.key])

    def test_stale_listing_is_scoped_to_pdf_keys_under_generated_prefixes(self) -> None:
        self.assertEqual(
            stale_object_keys(FakeListingClient()),
            ["Applications/Retired/Retired.pdf", "Studies/Retired/Retired.pdf"],
        )

    def test_removed_keys_are_derived_from_deleted_sources_and_base_manifest(self) -> None:
        diff = "\n".join([
            "Studies/Retired/Retired.md",
            "Studies/Retired/Research-Note-Detail.md",
            "Studies/Retired/Research-Template-Worksheet.md",
            "Studies/Retired/Deck.pptx",
        ])
        manifest = '{"decks":[{"source":"Studies/Retired/Deck.pptx","slidesPdf":"Studies/Retired/Deck.pdf","notesPdf":"Studies/Retired/Deck-notes.pdf"}]}'
        active = (
            GeneratedPdfSpec(
                "Studies/Retired/Deck.pdf", Path("Deck.pptx"), Path("Deck.pdf"), "presentation-slides"
            ),
        )
        self.assertEqual(
            removed_object_keys(
                "base",
                diff_text=diff,
                base_manifest_text=manifest,
                current_specs=active,
            ),
            [
                "Studies/Retired/Deck-notes.pdf",
                "Studies/Retired/Research-Note-Detail.pdf",
                "Studies/Retired/Retired.pdf",
            ],
        )

    def test_removed_object_deletion_is_exact_and_verified(self) -> None:
        client = FakeDeleteClient({"Studies/Retired/Retired.pdf"})
        results = delete_removed_objects(
            ["Studies/Retired/Missing.pdf", "Studies/Retired/Retired.pdf"],
            client,
            dry_run=False,
        )
        self.assertEqual(results, [
            ("Studies/Retired/Missing.pdf", "absent"),
            ("Studies/Retired/Retired.pdf", "deleted"),
        ])
        self.assertEqual(client.deleted, ["Studies/Retired/Retired.pdf"])

    def test_kind_selection_is_available_for_split_ci_builds(self) -> None:
        with patch("_publish_generated_pdfs.verify_artifacts", return_value=[]) as verify, patch(
            "_publish_generated_pdfs.load_r2_config",
            side_effect=AssertionError("offline dry-run must not load credentials"),
        ):
            self.assertEqual(main(["--kind", "presentation-slides", "--dry-run", "--offline"]), 0)
        selected = verify.call_args.args[0]
        self.assertTrue(selected)
        self.assertTrue(all(spec.kind == "presentation-slides" for spec in selected))

    def test_reference_artifact_root_does_not_shadow_private_original_html(self) -> None:
        row = {
            "repo_path": "References/Archive/original.html",
            "state": "r2-published",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated_html = root / row["repo_path"]
            generated_html.parent.mkdir(parents=True)
            generated_html.write_text("generated reading copy", encoding="utf-8")
            self.assertEqual(reference_source_path(row, root), artifact_local_path(row))

    def test_reference_artifact_root_supplies_ci_built_pdf(self) -> None:
        row = {
            "repo_path": "References/Archive/reference.pdf",
            "state": "r2-published",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generated_pdf = root / row["repo_path"]
            generated_pdf.parent.mkdir(parents=True)
            generated_pdf.write_bytes(b"%PDF-1.4\n")
            self.assertEqual(reference_source_path(row, root), generated_pdf)

    def test_matching_reference_object_is_idempotent(self) -> None:
        source = {"bytes": 123, "sha256": "abc"}
        headers = {"content-length": "123", "x-amz-meta-sha256": "abc"}
        self.assertTrue(_object_matches_manifest(headers, source))
        self.assertFalse(_object_matches_manifest(None, source))
        self.assertFalse(
            _object_matches_manifest({**headers, "content-length": "124"}, source)
        )


@unittest.skipUnless(os.environ.get("AMD_RUN_LIVE_R2_TEST") == "1", "live R2 test not enabled")
class LiveR2Tests(unittest.TestCase):
    def test_put_head_delete_canary(self) -> None:
        client = R2S3Client(load_r2_config())
        key = f".canary/codex-generated-pdf-publisher-{uuid.uuid4().hex}.bin"
        body = b"r2 publisher permission canary"
        digest = __import__("hashlib").sha256(body).hexdigest()
        try:
            headers = client.put_object(
                key, body,
                metadata={"sha256": digest, "kind": "canary", "schema": "1"},
                cache_control="no-store", content_disposition="inline",
            )
            self.assertEqual(headers.get("x-amz-meta-sha256"), digest)
            self.assertEqual(int(headers.get("content-length", "-1")), len(body))
        finally:
            client.delete_object(key)
        self.assertIsNone(client.head_object(key))


if __name__ == "__main__":
    unittest.main()

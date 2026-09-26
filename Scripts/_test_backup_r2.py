"""Backup regressions: corruption, concurrent changes, pagination, and safe recovery."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import _backup_r2 as backup
from _r2_s3 import R2Config, R2S3Client


class FakeClient:
    def __init__(self, bucket="bucket", content=None):
        self.name = bucket
        self.content = content or {"a.pdf": b"example"}
        self.gets = []

    def bucket(self):
        return self.name

    def _object_path(self, key):
        return "/" + self.name + "/" + key

    def rows(self):
        return [{"bucket": self.name, "key": key, "bytes": len(body),
                 "etag": '"' + hashlib.md5(body, usedforsecurity=False).hexdigest() + '"',
                 "last_modified": "2026-09-26T00:00:00Z"}
                for key, body in sorted(self.content.items())]

    def _request(self, method, path, headers=None, **kwargs):
        assert method == "GET"
        key = path[len(self.name) + 2:]
        self.gets.append(key)
        body = self.content[key]
        etag = next(row["etag"] for row in self.rows() if row["key"] == key)
        assert headers == {"if-match": etag}
        return 200, {"etag": etag, "content-type": "application/pdf",
                     "x-amz-meta-sha256": hashlib.sha256(body).hexdigest()}, body


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "snapshot"

    def snapshot(self, client=None, part_bytes=1024):
        client = client or FakeClient()
        with patch.object(backup, "inventory", side_effect=lambda c: c.rows()):
            return backup.snapshot(self.root, {client.bucket(): client}, 2, part_bytes)

    def test_two_buckets_deduplicate_and_recover_unsafe_remote_keys(self):
        clients = {"bucket": FakeClient(content={"../escape": b"same", "A": b"different", "a": b"same"}),
                   "references": FakeClient("references", {"archive/原本.html": b"same"})}
        with patch.object(backup, "inventory", side_effect=lambda c: c.rows()):
            manifest = backup.snapshot(self.root, clients, 2, 8)
        self.assertEqual(manifest["object_count"], 4)
        self.assertEqual(sum(len(p["blobs"]) for p in manifest["parts"]), 2)
        self.assertEqual(len(manifest["parts"]), 2)
        output = Path(self.temp.name) / "recovered"
        backup.extract(self.root, output)
        self.assertEqual(len(list((output / "objects").iterdir())), 2)
        self.assertFalse((Path(self.temp.name) / "escape").exists())
        self.assertEqual(json.loads((output / "manifest.json").read_text(encoding="utf-8")), manifest)

    def test_reject_corrupt_archive_and_missing_part(self):
        manifest = self.snapshot()
        path = self.root / manifest["parts"][0]["name"]
        original = path.read_bytes()
        path.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, "Archive checksum"):
            backup.verify(self.root)
        path.unlink()
        with self.assertRaises(OSError):
            backup.verify(self.root)

    def test_reject_source_checksum_mismatch(self):
        client = FakeClient()
        original = client._request
        def corrupt(*args, **kwargs):
            status, headers, body = original(*args, **kwargs)
            headers["x-amz-meta-sha256"] = "0" * 64
            return status, headers, body
        with patch.object(client, "_request", side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, "Source SHA-256"):
                self.snapshot(client)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_reject_bucket_changes_without_completion_marker(self):
        client = FakeClient()
        with patch.object(backup, "inventory", side_effect=[client.rows(), []]):
            with self.assertRaisesRegex(ValueError, "Bucket changed"):
                backup.snapshot(self.root, {"bucket": client}, 2, 1024)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_download_cache_is_rehashed_and_corruption_redownloaded(self):
        client = FakeClient()
        row = client.rows()[0]
        first = backup.download(client, self.root, row)
        self.assertEqual(backup.download(client, self.root, row), first)
        self.assertEqual(len(client.gets), 1)
        path, _ = backup.cache_paths(self.root, row)
        path.write_bytes(b"damaged")
        self.assertEqual(backup.download(client, self.root, row), first)
        self.assertEqual(len(client.gets), 2)

    def test_complete_backup_cannot_be_overwritten(self):
        self.snapshot()
        with self.assertRaisesRegex(ValueError, "never overwritten"):
            self.snapshot()

    def test_failed_verification_never_writes_completion_manifest(self):
        with patch.object(backup, "verify", side_effect=ValueError("verification failed")):
            with self.assertRaisesRegex(ValueError, "verification failed"):
                self.snapshot()
        self.assertFalse((self.root / "manifest.json").exists())

    def test_manifest_path_traversal_rejected_before_extracting(self):
        manifest = self.snapshot()
        manifest["parts"][0]["name"] = "../escape.zip"
        backup.write_json(self.root / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "archive filename"):
            backup.extract(self.root, Path(self.temp.name) / "restore")

    def test_inventory_paginates_and_rejects_repeated_token(self):
        client = R2S3Client(R2Config("https://r2.example.test", "key", "secret", "bucket"))
        def page(key, token=""):
            return (200, {}, (f'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
                    f'<Contents><Key>{key}</Key><Size>5</Size><ETag>etag</ETag></Contents>'
                    f'<IsTruncated>{"true" if token else "false"}</IsTruncated>'
                    f'<NextContinuationToken>{token}</NextContinuationToken></ListBucketResult>').encode())
        with patch.object(client, "_request", side_effect=[page("a", "next"), page("b")]) as request:
            self.assertEqual([row["key"] for row in backup.inventory(client)], ["a", "b"])
            self.assertEqual(request.call_args.kwargs["query"]["continuation-token"], "next")
        with patch.object(client, "_request", side_effect=[page("a", "same"), page("b", "same")]):
            with self.assertRaisesRegex(ValueError, "continuation token"):
                backup.inventory(client)


if __name__ == "__main__":
    unittest.main()

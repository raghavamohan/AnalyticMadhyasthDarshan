#!/usr/bin/env python3
"""Tests for hash-verified reference resolution and hydration."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from _reference_store import ReferenceStore

PAYLOAD = b"%PDF-test-reference\n"


class FakeResponse:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, size: int = -1) -> bytes:
        if self.offset >= len(self.data):
            return b""
        if size < 0:
            size = len(self.data) - self.offset
        chunk = self.data[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


def _manifest(path: Path, *, public: bool = True) -> Path:
    data = {
        "schema_version": 1,
        "artifacts": [
            {
                "repo_path": "References/Science/Test.pdf",
                "kind": "reference-pdf",
                "state": "r2-published",
                "tags": ["Test 2026"],
                "source": {
                    "bytes": len(PAYLOAD),
                    "sha256": hashlib.sha256(PAYLOAD).hexdigest(),
                    "media_type": "application/pdf",
                },
                "target": {
                    "storage": "r2-public" if public else "r2-private-original",
                    "r2_key": "References/Science/Test.pdf",
                    "public_url": "https://example.test/References/Science/Test.pdf" if public else None,
                },
            }
        ],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_local_file_precedes_cache_and_network() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        references = root / "References"
        local = references / "Science" / "Test.pdf"
        local.parent.mkdir(parents=True)
        local.write_bytes(PAYLOAD)
        store = ReferenceStore(
            manifest_path=_manifest(root / "manifest.json"),
            references_root=references,
            cache_root=root / "cache",
        )
        with patch("urllib.request.urlopen", side_effect=AssertionError("network used")):
            assert store.resolve("Science/Test.pdf", allow_download=True) == local.resolve()


def test_hydration_is_atomic_and_hash_verified() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        store = ReferenceStore(
            manifest_path=_manifest(root / "manifest.json"),
            references_root=root / "References",
            cache_root=root / "cache",
        )
        with patch("urllib.request.urlopen", return_value=FakeResponse(PAYLOAD)):
            path = store.resolve("Test 2026", allow_download=True)
        assert path.read_bytes() == PAYLOAD
        assert not list(path.parent.glob("*.partial"))


def test_corrupt_download_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        store = ReferenceStore(
            manifest_path=_manifest(root / "manifest.json"),
            references_root=root / "References",
            cache_root=root / "cache",
        )
        with patch("urllib.request.urlopen", return_value=FakeResponse(b"wrong")):
            try:
                store.resolve("Science/Test.pdf", allow_download=True)
            except ValueError as exc:
                assert "size mismatch" in str(exc)
            else:
                raise AssertionError("corrupt download should fail")
        assert not store.cache_path(store.artifacts[0]).exists()


def test_private_original_cannot_be_hydrated_publicly() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        store = ReferenceStore(
            manifest_path=_manifest(root / "manifest.json", public=False),
            references_root=root / "References",
            cache_root=root / "cache",
        )
        try:
            store.resolve("Science/Test.pdf", allow_download=True)
        except ValueError as exc:
            assert "not publicly hydratable" in str(exc)
        else:
            raise AssertionError("private artifact should not hydrate from the public site")


def test_traversal_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        store = ReferenceStore(
            manifest_path=_manifest(root / "manifest.json"),
            references_root=root / "References",
            cache_root=root / "cache",
        )
        assert store.find("../outside.pdf") is None


def main() -> int:
    tests = [
        test_local_file_precedes_cache_and_network,
        test_hydration_is_atomic_and_hash_verified,
        test_corrupt_download_is_rejected,
        test_private_original_cannot_be_hydrated_publicly,
        test_traversal_is_rejected,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:  # pragma: no cover - CLI diagnostics
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

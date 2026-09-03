#!/usr/bin/env python3
"""Integration tests for common reference-path resolution."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from _common import resolve_reference_path


class FakeStore:
    def __init__(self, resolved: Path):
        self.resolved = resolved

    def find(self, value):
        return "artifact" if str(value) == "Remote 2026" else None

    def resolve(self, artifact, *, allow_download: bool):
        assert artifact == "artifact"
        assert allow_download
        return self.resolved


def test_missing_registry_file_falls_through_to_manifest_hydration() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        missing = root / "References" / "Remote.pdf"
        hydrated = root / "cache" / "Remote.pdf"
        hydrated.parent.mkdir(parents=True)
        hydrated.write_bytes(b"%PDF-hydrated")
        fake = FakeStore(hydrated)
        with (
            patch("_common.parse_reference_registry", return_value={"Remote 2026": missing}),
            patch("_reference_store.ReferenceStore", return_value=fake),
        ):
            assert resolve_reference_path("Remote 2026") == hydrated


def test_existing_explicit_path_still_wins() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "local.pdf"
        path.write_bytes(b"%PDF-local")
        assert resolve_reference_path(str(path)) == path.resolve()


def main() -> int:
    tests = [
        test_missing_registry_file_falls_through_to_manifest_hydration,
        test_existing_explicit_path_still_wins,
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

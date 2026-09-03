#!/usr/bin/env python3
"""Verify approved reference PDFs through workers.dev or the public site."""
from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path

from _common import BASE, configure_utf8_stdio
from _publish_generated_pdf_worker import CANARY_WORKER_NAME
from _reference_artifacts import load_manifest
from _reference_store import ReferenceStore, load_reference_store
from _verify_generated_pdf_delivery import _base_url, _request, verify_artifact


def public_rows() -> list[dict]:
    return [
        row
        for row in load_manifest()["artifacts"]
        if (row.get("target") or {}).get("storage") == "r2-public"
        and str((row.get("target") or {}).get("r2_key", "")).lower().endswith(".pdf")
    ]


def _local_path(
    row: dict, artifact_root: Path | None, store: ReferenceStore
) -> Path:
    if artifact_root is not None:
        candidate = artifact_root.resolve() / row["repo_path"]
        if candidate.is_file():
            return candidate
    artifact = store.find(row["repo_path"])
    if artifact is None:
        raise ValueError(f"reference is absent from resolver: {row['repo_path']}")
    return store.resolve(artifact, allow_download=True)


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--workers-dev", action="store_true")
    target.add_argument("--public", action="store_true")
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--worker-name", default=CANARY_WORKER_NAME)
    args = parser.parse_args(argv)

    try:
        base_url = _base_url(args.workers_dev, args.worker_name)
        errors: list[str] = []
        rows = public_rows()
        store = load_reference_store()
        for index, row in enumerate(rows):
            key = row["target"]["r2_key"]
            path = _local_path(row, args.artifact_root, store)
            item_errors = verify_artifact(
                base_url,
                key,
                path,
                wait_for_ready=args.workers_dev and index == 0,
            )
            if item_errors:
                errors.extend(item_errors)
            else:
                print(f"OK {key}")

        unknown_url = base_url.rstrip("/") + "/References/__worker_probe__/unknown.pdf"
        status, headers, _ = _request(unknown_url)
        if status != 404 or headers.get("cache-control") != "no-store":
            errors.append("unknown reference PDF did not return the controlled no-store 404")

        if args.public:
            control_url = base_url.rstrip("/") + "/References/README.md"
            status, headers, body = _request(control_url)
            if status != 200 or headers.get("x-amd-pdf-origin") == "r2" or not body:
                errors.append("non-PDF reference control document did not pass through to origin")
            retained = next(
                row
                for row in load_manifest()["artifacts"]
                if (row.get("target") or {}).get("storage") == "git-retained-rights-review"
            )
            retained_url = base_url.rstrip("/") + "/" + urllib.parse.quote(
                retained["repo_path"], safe="/"
            )
            status, headers, _ = _request(retained_url, method="HEAD")
            if status != 200 or headers.get("x-amd-pdf-origin") == "r2":
                errors.append("rights-review reference PDF did not pass through to origin")

        if errors:
            print("Reference delivery verification failed:\n  - " + "\n  - ".join(errors))
            return 1
        print(f"Reference delivery verified ({len(rows)} R2 PDFs) via {base_url}")
        return 0
    except (OSError, RuntimeError, StopIteration, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

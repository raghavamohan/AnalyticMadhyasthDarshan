#!/usr/bin/env python3
"""Hydrate hash-verified R2-backed references into the ignored local cache."""
from __future__ import annotations

import argparse
import json

from _common import configure_utf8_stdio
from _reference_store import Artifact, ReferenceStore


def _selected(store: ReferenceStore, paths: list[str], tags: list[str], all_public: bool) -> list[Artifact]:
    selected: dict[str, Artifact] = {}
    for value in paths:
        artifact = store.find(value)
        if artifact is None:
            raise ValueError(f"reference path is absent from manifest: {value}")
        selected[artifact.repo_path] = artifact
    for tag in tags:
        artifact = store.find_tag(tag)
        if artifact is None:
            raise ValueError(f"reference tag is absent from manifest: {tag}")
        selected[artifact.repo_path] = artifact
    if all_public:
        for artifact in store.public_artifacts():
            selected[artifact.repo_path] = artifact
    return [selected[key] for key in sorted(selected)]


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", default=[], help="Repository or References-relative path.")
    parser.add_argument("--tag", action="append", default=[], help="Reference tag from the manifest.")
    parser.add_argument("--all-public", action="store_true", help="Hydrate every public R2 target.")
    parser.add_argument("--list", action="store_true", help="List manifest artifacts without hydrating.")
    parser.add_argument("--force", action="store_true", help="Replace an existing cached copy.")
    args = parser.parse_args()

    try:
        store = ReferenceStore()
        if args.list:
            for artifact in store.artifacts:
                print(
                    f"{artifact.repo_path}\t{artifact.storage}\t"
                    f"{artifact.bytes}\t{','.join(artifact.tags)}"
                )
            return 0
        selected = _selected(store, args.path, args.tag, args.all_public)
        if not selected:
            parser.error("select --path, --tag, --all-public, or --list")
        failures = 0
        hydrated_bytes = 0
        for artifact in selected:
            try:
                path = store.resolve(artifact, allow_download=True, force=args.force)
                hydrated_bytes += artifact.bytes
                print(f"OK {artifact.repo_path} -> {path}")
            except (FileNotFoundError, KeyError, OSError, ValueError) as exc:
                failures += 1
                print(f"FAIL {artifact.repo_path}: {exc}")
        print(
            f"Hydration complete: {len(selected) - failures}/{len(selected)} artifact(s), "
            f"{hydrated_bytes / 1024 / 1024:.2f} MiB verified."
        )
        return 1 if failures else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Reference hydration error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

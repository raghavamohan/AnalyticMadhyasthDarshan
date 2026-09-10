#!/usr/bin/env python3
"""Fingerprint PDF build inputs and verify exact, complete build-cache trees.

Uses the shared consumed-input graph after installing Python dependencies.
Keys describe source bytes and paths, never HEAD or the current time. Python
imports and literal helper-script references are followed conservatively so a
shared helper change cannot silently reuse an obsolete build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from _build_inputs import script_dependencies, file_hash

BASE = Path(__file__).resolve().parent.parent
FAMILIES = ("markdown", "references", "presentations")
def tracked_files(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True,
    )
    return {name for name in result.stdout.decode("utf-8").split("\0") if name}


def input_paths(family: str, root: Path, tracked: set[str]) -> set[str]:
    from _artifact_graph import build_graph
    return {path for item in build_graph(root).values() if item['family'] == family for path in item['inputs']}


def affected_families(changed_paths: set[str], root: Path = BASE, *, base: str | None = None) -> set[str]:
    from _artifact_graph import affected_outputs, build_graph
    nodes = build_graph(root)
    selected = affected_outputs(changed_paths, root=root, base=base, nodes=nodes)
    return {nodes[key]['family'] for key in selected}


def git_changed_paths(base: str, root: Path = BASE) -> set[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"git diff {base} HEAD failed: {detail}")
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}



def fingerprint(family: str, root: Path = BASE, *, image: str = "") -> str:
    from _artifact_graph import build_graph, fingerprint as content_fingerprint
    # The runner image label is deliberately not a rendering contract.
    return content_fingerprint({key: item['fingerprint'] for key, item in build_graph(root).items()
                                if item['family'] == family})


def manifest_name(family: str) -> str:
    return f"{family}-cache-manifest.json"


def artifact_hashes(root: Path, family: str) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Cache contains a link outside its artifact tree: {path}")
        if path.is_file() and path.name != manifest_name(family):
            files[path.relative_to(root).as_posix()] = file_hash(path)
    if not any(name.endswith(".pdf") for name in files):
        raise ValueError("A complete PDF build cache must contain PDFs")
    return files


def seal(root: Path, family: str, key: str) -> None:
    data = {"schema": 1, "family": family, "fingerprint": key, "files": artifact_hashes(root, family)}
    (root / manifest_name(family)).write_bytes((json.dumps(data, sort_keys=True) + "\n").encode("utf-8"))


def verify(root: Path, family: str, key: str) -> None:
    data = json.loads((root / manifest_name(family)).read_text(encoding="utf-8"))
    if (data.get("schema"), data.get("family"), data.get("fingerprint")) != (1, family, key):
        raise ValueError("PDF cache does not match the requested family and build inputs")
    if data.get("files") != artifact_hashes(root, family):
        raise ValueError("PDF cache is incomplete or its checksums differ; use a manual full rebuild")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--keys", action="store_true")
    action.add_argument("--seal", choices=FAMILIES)
    action.add_argument("--verify", choices=FAMILIES)
    parser.add_argument("--changed-since")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--fingerprint")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    if args.keys:
        image = f"{os.environ.get('ImageOS', os.name)}:{os.environ.get('ImageVersion', 'local')}"
        lines = [f"{family}={fingerprint(family, image=image)}" for family in FAMILIES]
        affected = (
            affected_families(git_changed_paths(args.changed_since), base=args.changed_since)
            if args.changed_since
            else set(FAMILIES)
        )
        lines.extend(
            f"{family}_changed={'true' if family in affected else 'false'}"
            for family in FAMILIES
        )
        print("\n".join(lines))
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write("\n".join(lines) + "\n")
        return 0
    if args.root is None or not args.fingerprint:
        parser.error("--root and --fingerprint are required for cache verification/sealing")
    family = args.seal or args.verify
    if args.seal:
        seal(args.root, family, args.fingerprint)
    else:
        verify(args.root, family, args.fingerprint)
    print(f"{family}: {'sealed verified build' if args.seal else 'verified cached build'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

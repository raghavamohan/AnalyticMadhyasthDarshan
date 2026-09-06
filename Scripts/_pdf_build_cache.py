#!/usr/bin/env python3
"""Fingerprint PDF build inputs and verify exact, complete build-cache trees.

Standard library only: cache lookup happens before installing rendering tools.
Keys describe source bytes and paths, never HEAD or the current time. Python
imports and literal helper-script references are followed conservatively so a
shared helper change cannot silently reuse an obsolete build.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FAMILIES = ("markdown", "references", "presentations")
ROOT_SCRIPTS = {
    "markdown": ("_build_markdown_pdfs.py",),
    "references": ("_build_reference_pdfs.py",),
    "presentations": ("_build_presentations.py",),
}
COMMON_INPUTS = {
    "Scripts/_pdf_build_cache.py", "requirements.txt", "CNAME",
    ".github/actions/setup-study-env/action.yml",
    ".github/workflows/generated-pdf-publish.yml",
}
IMAGE_SUFFIXES = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp"}


def tracked_files(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True,
    )
    return {name for name in result.stdout.decode("utf-8").split("\0") if name}


def script_dependencies(root: Path, names: tuple[str, ...]) -> set[str]:
    pending = list(names)
    found: set[str] = set()
    while pending:
        name = pending.pop()
        relative = "Scripts/" + name
        path = root / relative
        if relative in found or not path.is_file():
            continue
        found.add(relative)
        if path.suffix != ".py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                pending.append(node.module.split(".")[0] + ".py")
            elif isinstance(node, ast.Import):
                pending.extend(alias.name.split(".")[0] + ".py" for alias in node.names)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Subprocess helpers are often not imported as Python modules.
                candidate = node.value.replace("\\", "/").split("/")[-1]
                if candidate.startswith("_") and Path(candidate).suffix in {".py", ".js", ".cjs", ".mjs"}:
                    pending.append(candidate)
    return found


def input_paths(family: str, root: Path, tracked: set[str]) -> set[str]:
    selected = COMMON_INPUTS | script_dependencies(root, ROOT_SCRIPTS[family])
    for name in tracked:
        path = Path(name)
        suffix = path.suffix.lower()
        # These assets are linked as screen-only CSS and browser JS. PDF
        # loading disables reader scripts; neither can affect printed output.
        if name.startswith("Assets/") and name not in {
            "Assets/reader/reader.css", "Assets/reader/reader.js", "Assets/reader/search.css",
            "Assets/reader/search.js", "Assets/reader/reader-features.js",
            "Assets/reader/notes-core.js", "Assets/reader/study-tools.js", "Assets/reader/study-tools.css",
            "Assets/reader/offline-client.js", "Assets/reader/offline-policy.js",
            "Assets/Mermaid/mermaid.min.js", "Assets/Mermaid/LICENSE", "Assets/Mermaid/vendor.json", "Assets/Mermaid/.gitattributes",
            "Assets/reader/notes-core.js", "Assets/reader/study-tools.js", "Assets/reader/study-tools.css",
            "Assets/reader/offline-client.js", "Assets/reader/offline-policy.js",
            "Assets/Mermaid/mermaid.min.js", "Assets/Mermaid/LICENSE", "Assets/Mermaid/vendor.json",
        }:
            selected.add(name)
        if family == "presentations":
            if name == "Scripts/presentation-pipeline.json" or (
                name.startswith(("Studies/", "Applications/")) and suffix == ".pptx"
            ) or name == "Scripts/_install_presentation_renderer.ps1":
                selected.add(name)
        else:
            if name in {"Scripts/package.json", "Scripts/package-lock.json", "References/r2-artifacts.json"}:
                selected.add(name)
            # JS require/import dependencies and renderer utilities are small;
            # include them all rather than maintain an incomplete JS parser.
            if name.startswith("Scripts/") and suffix in {".js", ".cjs", ".mjs"}:
                selected.add(name)
            if family == "markdown":
                if name.startswith(("Studies/", "Applications/")) and not name.startswith("Studies/search-data/") and name != "Studies/offline-manifest.json" and suffix in (
                    {".md", ".json"} | IMAGE_SUFFIXES
                ):
                    selected.add(name)
                selected.add("Scripts/presentation-pipeline.json")
            elif name.startswith("References/") and suffix in ({".md", ".html", ".pdf"} | IMAGE_SUFFIXES):
                selected.add(name)
    return selected


def file_hash(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def fingerprint(family: str, root: Path = BASE, *, image: str = "") -> str:
    tracked = tracked_files(root)
    inputs = input_paths(family, root, tracked)
    records = []
    for name in sorted(inputs):
        path = root / name
        records.append((name, file_hash(path) if path.is_file() else "missing"))
    # Cross-document link rewriting depends on the existence of HTML/PDF paths,
    # not their generated bytes. Include tracked names without invalidating a
    # study build for an unrelated edit to a reader's HTML or the portal.
    targets = sorted(name for name in tracked if name.startswith(("Studies/", "Applications/", "References/"))
                     and Path(name).suffix.lower() in {".html", ".pdf"}) if family == "markdown" else []
    payload = {"schema": 1, "family": family, "image": image, "files": records, "targets": targets}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


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
    parser.add_argument("--root", type=Path)
    parser.add_argument("--fingerprint")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    if args.keys:
        image = f"{os.environ.get('ImageOS', os.name)}:{os.environ.get('ImageVersion', 'local')}"
        lines = [f"{family}={fingerprint(family, image=image)}" for family in FAMILIES]
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

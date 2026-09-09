"""Stage lifecycle outputs by contract, including deletions and root discovery files.

Run after preparation in a clean checkout. Unexpected writes fail before any
path is staged; ignored PDFs are never candidates. The same contract is used by
both bot writers and by their post-commit cleanliness check.
"""
from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import subprocess

BASE = Path(__file__).resolve().parent.parent
ROOT_OUTPUTS = {
    "sitemap.xml", "llms.txt", "llms-full.txt",
    ".github/ISSUE_TEMPLATE/study-feedback.yml",
    "infra/generated-pdf-worker/src/generated-pdf-keys.js",
    "Scripts/presentation-pipeline.json",
}
STUDIES_OUTPUTS = {
    "README.md", "index.html", "catalog-topical.json", "catalog-formal.json",
    "catalog-applied.json", "catalog-all.json", "feed.json", "studies.txt",
    "companion-artifacts.json", "proposal-registry.json", "search.html",
    "notebook.html", "offline-manifest.json",
}


def permits(name: str, *, deleted: bool = False) -> bool:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        return False
    if name in ROOT_OUTPUTS:
        return True
    if len(path.parts) == 2 and path.parts[0] == "Studies":
        return path.name in STUDIES_OUTPUTS
    if name.startswith("Studies/search-data/"):
        return path.suffix == ".json"
    if len(path.parts) >= 3 and path.parts[0] in {"Studies", "Applications"}:
        # Lifecycle removal may delete every tracked authoring input. Generation
        # may only create/update text readers, canonical sources and metadata.
        return deleted or path.suffix in {".html", ".md"} or path.name == ".proposal-meta.json"
    if name.startswith("References/"):
        return deleted or path.suffix == ".md"
    return False


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True).stdout


def changed_paths(root: Path) -> list[str]:
    return sorted({p.decode("utf-8") for p in (git(
        root, "ls-files", "--modified", "--deleted", "--others", "--exclude-standard", "-z"
    ) + git(root, "diff", "--cached", "--name-only", "-z")).split(b"\0") if p})


def stage(root: Path) -> list[str]:
    paths = changed_paths(root)
    unexpected = [p for p in paths if not permits(p, deleted=not (root / p).exists())
                  or (root / p).is_symlink() or not (root / p).resolve().is_relative_to(root.resolve())]
    if unexpected:
        raise ValueError("Preparation wrote paths outside its output contract: " + ", ".join(unexpected))
    if paths:
        subprocess.run(["git", "add", "-A", "--", *paths], cwd=root, check=True)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--check-clean", action="store_true")
    args = parser.parse_args()
    if args.stage:
        for name in stage(BASE):
            print(name)
    if args.check_clean:
        pending = changed_paths(BASE)
        staged = git(BASE, "diff", "--cached", "--name-only").decode().splitlines()
        if pending or staged:
            raise SystemExit("Uncommitted preparation outputs: " + ", ".join(sorted(set(pending + staged))))


if __name__ == "__main__":
    main()

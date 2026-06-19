"""Download open-access / public-domain references into References/.

Usage (from repo root):
    python Scripts/_download_references.py
    python Scripts/_download_references.py --tag "McTaggart 1908" --tag "Hashemi 2025"
    python Scripts/_download_references.py --dry-run
    python Scripts/_download_references.py --force
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from _common import REFERENCES
from _reference_downloads import DOWNLOADS, download_subdirs

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _normalize_tag(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def _entry_tags(entry) -> set[str]:
    tags: set[str] = set()
    if entry.tag:
        tags.add(_normalize_tag(entry.tag))
    stem = Path(entry.dest).stem
    author_year = stem.split("-")
    if len(author_year) >= 2 and author_year[1].isdigit():
        tags.add(_normalize_tag(f"{author_year[0]} {author_year[1]}"))
    tags.add(_normalize_tag(stem.replace("-", " ")))
    return tags


def _filter_entries(tags: set[str] | None):
    if not tags:
        return DOWNLOADS
    wanted = {_normalize_tag(t) for t in tags}
    selected = [entry for entry in DOWNLOADS if _entry_tags(entry) & wanted]
    if not selected:
        known = sorted({entry.tag or Path(entry.dest).name for entry in DOWNLOADS})
        raise SystemExit(
            "No download entries matched --tag. Known tags include:\n  "
            + "\n  ".join(known)
        )
    return tuple(selected)


def _save_url(url: str, dest_path: Path, min_bytes: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(data)
    if len(data) < min_bytes:
        dest_path.unlink(missing_ok=True)
        raise ValueError(f"Download too small ({len(data)} bytes), likely failed")


def download_references(
    *,
    tags: set[str] | None = None,
    dry_run: bool = False,
    force: bool = False,
    skip_cache_sync: bool = False,
) -> int:
    """Download manifest entries. Returns process exit code (0 = all OK)."""
    entries = _filter_entries(tags)
    failures = 0

    for subdir in download_subdirs():
        (REFERENCES / subdir).mkdir(parents=True, exist_ok=True)

    for entry in entries:
        dest_path = REFERENCES / entry.dest.replace("\\", "/")
        label = entry.tag or entry.dest
        if dest_path.exists() and not force:
            print(f"Skip (exists): {label} -> {dest_path.relative_to(REFERENCES.parent)}")
            continue
        if dry_run:
            print(f"Dry-run: {label} -> {dest_path.relative_to(REFERENCES.parent)}")
            for url in entry.urls:
                print(f"  try {url}")
            continue

        saved = False
        last_error = ""
        for url in entry.urls:
            try:
                print(f"Downloading {entry.dest} ...")
                _save_url(url, dest_path, entry.min_bytes)
                print(f"  saved {dest_path.name} ({dest_path.stat().st_size} bytes)")
                saved = True
                break
            except (urllib.error.URLError, ValueError, OSError) as exc:
                last_error = str(exc)
                print(f"  failed {url}: {last_error}")
        if not saved:
            failures += 1
            print(f"WARNING: all URLs failed for {entry.dest} ({last_error})")

    if dry_run:
        return 0

    if not skip_cache_sync:
        print("Syncing PDF text cache ...")
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "_quote_tool.py"), "cache", "sync"],
            check=False,
        )
        if result.returncode != 0:
            return result.returncode

    if failures:
        print(
            f"\n{failures} download(s) failed. See References/NOT-DOWNLOADED.md for external-only works."
        )
        return 1

    print("Reference download complete. See References/README.md and References/NOT-DOWNLOADED.md.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Download reference files into References/.")
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        metavar="TAG",
        help="Download only entries matching this citation tag (repeatable).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned downloads only.")
    parser.add_argument("--force", action="store_true", help="Re-download even when file exists.")
    parser.add_argument(
        "--skip-cache-sync",
        action="store_true",
        help="Do not run quote-tool cache sync after downloading.",
    )
    args = parser.parse_args()
    tag_set = set(args.tags) if args.tags else None
    raise SystemExit(
        download_references(
            tags=tag_set,
            dry_run=args.dry_run,
            force=args.force,
            skip_cache_sync=args.skip_cache_sync,
        )
    )


if __name__ == "__main__":
    main()

"""Build a public, document-sharded passage index without a search service.

The converter updates one shard; catalog writes reconcile the public inventory.
HTML is a compilation of the canonical Markdown, never a second indexed source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup

from _common import BASE, write_text_lf, favicon_link_tags
from _study_catalog import CATALOG_TABLES, StudyStatus, StudyTable, load_catalog_rows
from _study_passages import clean_text, search_text

DATA = BASE / "Studies" / "search-data"
ASSETS = BASE / "Assets" / "reader"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def serialize(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def eligible_documents() -> dict[Path, dict]:
    tracked = set(subprocess.check_output(
        ["git", "ls-files", "-z", "Studies/**/*.md", "Applications/**/*.md"], cwd=BASE,
    ).decode("utf-8").split("\0"))
    found = {}
    for table in CATALOG_TABLES:
        for row in load_catalog_rows(table):
            if row.status == StudyStatus.ONGOING:
                continue
            parent = BASE / ("Applications" if table == StudyTable.APPLIED else "Studies") / row.slug
            for source in sorted(parent.glob("*.md")):
                relative = source.relative_to(BASE).as_posix()
                if relative not in tracked or source.stem.startswith("Research-Template-"):
                    continue
                canonical = source.stem == row.slug
                found[source] = {
                    "key": digest(relative.encode())[:16],
                    "url": "/" + source.with_suffix(".html").relative_to(BASE).as_posix(),
                    "kind": "study" if canonical else "companion",
                    "status": row.status.value if canonical else "note",
                }
    return found


def document_data(source: Path, rendered: str) -> dict:
    soup = BeautifulSoup(rendered, "html.parser")
    version = soup.find("meta", attrs={"name": "amd-source-version"})
    title = soup.find("h1")
    main = soup.find("main", id="main")
    headings = {node["id"]: clean_text(node.get_text()) for node in main.select("h2[id],h3[id],h4[id]")} if main else {}
    passages = []
    for node in main.select("[data-reader-passage]") if main else []:
        if 'mermaid' in node.get('class', []):
            continue  # Diagram source syntax is not a readable search passage.
        text = search_text(node)
        if not text and (image := node.find("img")):
            text = clean_text(image.get("alt", ""))
        if not text or text.startswith(("Author:", "Edited on:", "Status:")):
            continue
        section = node.get("data-reader-heading", "")
        passages.append({"id": node["id"], "heading": section, "section": headings.get(section, "Introduction"), "text": text})
    return {
        "schema": 1, "title": clean_text(title.get_text()) if title else source.stem,
        "language": soup.html.get("lang", "en") if soup.html else "en",
        "version": version.get("content", "") if version else "",
        "passages": passages,
    }


def shard_path(metadata: dict) -> Path:
    return DATA / ("study-" + metadata["key"] + ".json")


def search_page(manifest_version: str) -> str:
    css = digest((ASSETS / "search.css").read_bytes())[:16]
    js = digest((ASSETS / "search.js").read_bytes())[:16]
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Search study passages</title><meta name="description" content="Find words and phrases across published studies and companion notes."/>
<link rel="canonical" href="https://analyticmadhyasthdarshan.org/Studies/search.html"/>
{favicon_link_tags()}
<link rel="stylesheet" href="../Assets/reader/search.css?v={css}"/>
<script defer src="../Assets/reader/search.js?v={js}"></script></head>
<body class="search-page"><a class="search-back" href="index.html">← All studies</a>
<main><h1>Find a passage</h1><p>Search the text of published studies and companion notes. Open a result at its passage, then use its sources to check the claim.</p>
<section class="study-search" id="collection-search" data-manifest="search-data/manifest.json?v={manifest_version}" aria-label="Search published documents">
<form class="search-form"><label for="collection-query">Words or phrase</label><div class="search-input-row"><input id="collection-query" type="search" maxlength="200" placeholder='e.g. "duration of activity"' required/><button type="submit">Search</button></div>
<p class="search-help">All words must occur in the same passage. Use quotation marks for a phrase. Latin accents are ignored; Hindi spelling is preserved.</p>
<div class="search-filters">
<label>Document<select id="search-document"><option value="">All documents</option></select></label>
<label>Type<select id="search-kind"><option value="">Studies and notes</option><option value="study">Studies</option><option value="companion">Companion notes</option></select></label>
<label>Status<select id="search-status"><option value="">All statuses</option><option value="released">Released</option><option value="draft">Draft</option><option value="note">Companion notes</option></select></label>
<label>Language<select id="search-language"><option value="">All languages</option></select></label>
</div></form>
<p class="search-status" role="status" aria-live="polite">Enter a word or phrase to begin.</p>
<ol class="search-results"></ol><button type="button" class="search-more" hidden>Show more results</button>
</section><p class="search-help">Search runs in your browser. The selected documents load when you search. Primary-source PDFs, private submissions and in-progress studies are outside this index.</p>
<noscript><p>Enable JavaScript for passage search, or open a study and use your browser’s Find command.</p></noscript></main></body></html>
'''


def manifest_content(documents: dict[Path, dict]) -> str:
    records = []
    for source, metadata in documents.items():
        path = shard_path(metadata)
        if not path.is_file():
            continue  # New studies acquire their shard when the reader is built.
        raw = path.read_bytes()
        data = json.loads(raw)
        records.append({**metadata, "title": data["title"], "language": data["language"],
                        "version": data["version"], "index": path.name + "?v=" + digest(raw)[:16],
                        "bytes": len(raw), "passages": len(data["passages"])})
    return serialize({"schema": 1, "documents": sorted(records, key=lambda doc: (doc["title"].casefold(), doc["key"]))})


def write_search_catalog() -> None:
    documents = eligible_documents()
    DATA.mkdir(parents=True, exist_ok=True)
    expected = {shard_path(metadata) for metadata in documents.values()}
    # Only generator-owned files inside this exact directory may be removed.
    for path in DATA.glob("study-*.json"):
        if path not in expected and re.fullmatch(r"study-[a-f0-9]{16}\.json", path.name):
            if path.is_symlink() or path.resolve().parent != DATA.resolve():
                raise ValueError(f"Unsafe search artifact: {path}")
            path.unlink()
    manifest = manifest_content(documents)
    write_text_lf(DATA / "manifest.json", manifest)
    write_text_lf(BASE / "Studies/search.html", search_page(digest(manifest.encode("utf-8"))[:16]))


def write_search_document(source: Path, rendered: str) -> None:
    # Test fixtures, references and proposal stubs cannot enter the public index.
    if source.parent.parent not in (BASE / "Studies", BASE / "Applications"):
        return
    metadata = eligible_documents().get(source)
    if metadata is None:
        return
    DATA.mkdir(parents=True, exist_ok=True)
    write_text_lf(shard_path(metadata), serialize(document_data(source, rendered)))
    write_search_catalog()


def verify_search() -> list[str]:
    errors = []
    documents = eligible_documents()
    for source, metadata in documents.items():
        path, reader = shard_path(metadata), source.with_suffix(".html")
        if not path.is_file() or not reader.is_file():
            errors.append(f"Missing search artifact for {source.relative_to(BASE)}; rebuild its reader")
            continue
        expected = document_data(source, reader.read_text(encoding="utf-8"))
        if expected["version"] != digest(source.read_bytes()) or not expected["passages"]:
            errors.append(f"Stale reader passages for {source.relative_to(BASE)}; rebuild its reader")
        if path.read_text(encoding="utf-8") != serialize(expected):
            errors.append(f"Stale passage index: {path.relative_to(BASE)}")
    expected_paths = {shard_path(metadata) for metadata in documents.values()}
    if set(DATA.glob("study-*.json")) != expected_paths:
        errors.append("Search inventory differs from published documents; run Scripts/_study_search.py --rebuild")
    try:
        manifest = manifest_content(documents)
    except (ValueError, KeyError, TypeError) as error:
        return errors + [f"Invalid search catalog data; rebuild passage indexes: {error}"]
    for path, content in ((DATA / "manifest.json", manifest),
                          (BASE / "Studies/search.html", search_page(digest(manifest.encode("utf-8"))[:16]))):
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            errors.append(f"Stale search page/catalog: {path.relative_to(BASE)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true", help="Rebuild indexes from the generated readers")
    args = parser.parse_args()
    if args.rebuild:
        DATA.mkdir(parents=True, exist_ok=True)
        for source, metadata in eligible_documents().items():
            write_text_lf(shard_path(metadata), serialize(document_data(source, source.with_suffix(".html").read_text(encoding="utf-8"))))
        write_search_catalog()
    errors = verify_search()
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Verified passage search for {len(eligible_documents())} public documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

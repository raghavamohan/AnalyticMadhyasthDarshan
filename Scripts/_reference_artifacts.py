#!/usr/bin/env python3
"""Build and verify the Cloudflare R2 reference-artifact manifest.

The manifest is bootstrapped from the repository's immutable PDF/HTML payloads
before migration.  After cutover it remains the source of truth even when those
payloads are no longer tracked locally; routine verification reads the checked-in
manifest and does not regenerate it from the filesystem.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import unicodedata
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from pypdf import PdfReader

from _common import BASE, REFERENCES, configure_utf8_stdio, site_base_url, write_text_lf
from _reference_downloads import DOWNLOADS

MANIFEST_PATH = REFERENCES / "r2-artifacts.json"
SCHEMA_VERSION = 1

ACTIVE_TRANSLATION_DIRS = (
    "Madhyasth-Darshan/KD-Karm-Darshan-English/",
    "Madhyasth-Darshan/MSM-Manav-Sanchetnavadi-Manovigyan-English/",
)
ACTIVE_TRANSLATION_SOURCE_PDFS = frozenset(
    {
        "Madhyasth-Darshan/KD-karm darshan v5.pdf",
        "Madhyasth-Darshan/MSM-manav-sanchetnavaadi-manovigyan.pdf",
    }
)
SITE_OWNER_APPROVED_PATHS = frozenset(
    {
        "Advaita-Vedanta/BG-Bhagavad-Gita-Shankara-Gambhirananda.pdf",
        "Advaita-Vedanta/BSB-Brahma-Sutra-Bhashya-Gambhirananda.pdf",
        "Advaita-Vedanta/BU-Brihadaranyaka-Upanishad-Madhavananda.pdf",
        "Advaita-Vedanta/CU-Chandogya-Upanishad-Gambhirananda.pdf",
        "Advaita-Vedanta/DDV-Drig-Drishya-Viveka-Nikhilananda.pdf",
        "Advaita-Vedanta/Eight-Upanishads-Vol1-KU-TU-Gambhirananda.pdf",
        "Advaita-Vedanta/MU-Mandukya-Upanishad-Gambhirananda.pdf",
        "Advaita-Vedanta/VC-Vivekachudamani-Madhavananda.pdf",
        "Madhyasth-Darshan/AVD-Adhyatmvad.docx.pdf",
        "Madhyasth-Darshan/JV-Jeevan-Vidya-An-Introduction.pdf",
        "Madhyasth-Darshan/JVD-Janvad.pdf",
        "Madhyasth-Darshan/MVD-Madhyasth-Darshan-Coexistentialism.pdf",
        "Madhyasth-Darshan/Nagraj-Recorded-Sessions/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.pdf",
        "Madhyasth-Darshan/SB-Samadhanatmak-Bhautikvad.pdf",
    }
)
THIRD_PARTY_HTML_PREFIXES = (
    "Advaita-Vedanta/",
    "Applied-Studies/",
    "Comparative-Philosophy/",
    "Modern-Philosophy/",
    "Science/",
)

README_ROW_RE = re.compile(
    r"\|\s*\*\*([^*|]+)\*\*\s*\|\s*\[([^\]]+)\]\(([^)]+)\)"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generated_pdf_signature(path: Path) -> dict[str, int | str]:
    """Return a content signature stable across Chromium host platforms."""
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        text = unicodedata.normalize("NFC", page.extract_text() or "")
        lines = [" ".join(line.split()) for line in text.replace("\r", "\n").split("\n")]
        pages.append("\n".join(line for line in lines if line))
    canonical_text = "\n\f\n".join(pages).encode("utf-8")
    return {
        "pages": len(reader.pages),
        "text_sha256": hashlib.sha256(canonical_text).hexdigest(),
    }


def _safe_relative_path(raw: str) -> str:
    normalized = raw.replace("\\", "/").lstrip("/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe reference artifact path: {raw!r}")
    return path.as_posix()


def _reference_payloads() -> list[Path]:
    paths: list[Path] = []
    for path in REFERENCES.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".html"}:
            continue
        rel = path.relative_to(REFERENCES).as_posix()
        if any(rel.startswith(prefix) for prefix in ACTIVE_TRANSLATION_DIRS):
            continue
        paths.append(path)
    return sorted(paths, key=lambda item: item.relative_to(REFERENCES).as_posix())


def _tags_by_path() -> dict[str, list[str]]:
    text = (REFERENCES / "README.md").read_text(encoding="utf-8", errors="replace")
    result: dict[str, list[str]] = {}
    for match in README_ROW_RE.finditer(text):
        tag = match.group(1).strip()
        href = unquote(match.group(3).strip()).split("#", 1)[0]
        if href.startswith(("http://", "https://")):
            continue
        try:
            rel = _safe_relative_path(href)
        except ValueError:
            continue
        result.setdefault(rel, []).append(tag)

    # The combined Eight Upanishads volume is registered under TU in the table
    # and is also the local source for KU.
    for rel, tags in result.items():
        if "TU" in tags and "KU" not in tags:
            tags.append("KU")
    return {key: sorted(set(value)) for key, value in result.items()}


def _download_sources() -> dict[str, dict]:
    return {
        _safe_relative_path(entry.dest): {
            "urls": list(entry.urls),
            "minimum_bytes": entry.min_bytes,
            "notes": entry.notes,
        }
        for entry in DOWNLOADS
    }


def _rights_status(notes: str, rel: str = "") -> str:
    if rel in SITE_OWNER_APPROVED_PATHS:
        return "existing-site-publication-approved"
    folded = notes.casefold()
    if re.search(r"public[- ]domain", folded):
        return "public-domain-recorded"
    if re.search(r"cc by[-– ]nc[-– ]sa 4\.0", folded):
        return "cc-by-nc-sa-4.0-recorded"
    if re.search(r"cc by[-– ]nc[-– ]nd", folded):
        return "cc-by-nc-nd-recorded"
    if "cc by 4.0" in folded:
        return "cc-by-4.0-recorded"
    if "cc by" in folded or "creative commons attribution license" in folded:
        return "cc-by-recorded"
    return "review-required"


def _normalized_pdf_target(html_row: dict, pdf_repo_path: str) -> dict:
    rights_status = (html_row.get("rights") or {}).get("status")
    site_root = site_base_url().rstrip("/")
    if rights_status != "review-required":
        return {
            "storage": "r2-public",
            "r2_key": pdf_repo_path,
            "public_url": f"{site_root}/{pdf_repo_path}",
        }
    urls = list((html_row.get("source") or {}).get("urls") or [])
    if not urls:
        raise ValueError(f"rights-blocked normalized reference has no canonical URL: {pdf_repo_path}")
    canonical_url = next((url for url in urls if "web.archive.org" not in url), urls[0])
    return {
        "storage": "external-only-rights-review",
        "r2_key": None,
        "public_url": canonical_url,
    }


def _mime_type(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return "application/pdf"
    if path.suffix.lower() == ".html":
        return "text/html; charset=utf-8"
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def _is_third_party_html(rel: str) -> bool:
    return rel.endswith(".html") and rel.startswith(THIRD_PARTY_HTML_PREFIXES)


def _entry(path: Path, tags: dict[str, list[str]], downloads: dict[str, dict]) -> dict:
    rel = path.relative_to(REFERENCES).as_posix()
    repo_path = f"References/{rel}"
    source = downloads.get(rel, {"urls": [], "minimum_bytes": 500, "notes": ""})
    retained = rel in ACTIVE_TRANSLATION_SOURCE_PDFS
    third_party_html = _is_third_party_html(rel)
    site_root = site_base_url().rstrip("/")

    if retained:
        target = {
            "storage": "git-retained-active-translation",
            "r2_key": None,
            "public_url": f"{site_root}/{repo_path}",
        }
        state = "git-retained"
        kind = "active-translation-source-pdf"
    elif third_party_html:
        target = {
            "storage": "r2-private-original",
            "r2_key": f"archive/original-html/{rel}",
            "public_url": None,
        }
        state = "git-source"
        kind = "third-party-html-snapshot"
    elif path.suffix.lower() == ".html" and path.with_suffix(".md").is_file():
        target = {
            "storage": "generated-on-demand",
            "r2_key": None,
            "public_url": None,
        }
        state = "generated-in-git"
        kind = "generated-reference-html"
    else:
        rights_status = _rights_status(source["notes"], rel)
        approved = rights_status != "review-required"
        target = {
            "storage": "r2-public" if approved else "git-retained-rights-review",
            "r2_key": repo_path if approved else None,
            "public_url": f"{site_root}/{repo_path}",
        }
        state = "git-source" if approved else "git-retained"
        kind = "reference-pdf" if path.suffix.lower() == ".pdf" else "generated-reference-html"

    result = {
        "repo_path": repo_path,
        "kind": kind,
        "state": state,
        "tags": tags.get(rel, []),
        "source": {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "media_type": _mime_type(path),
            "urls": source["urls"],
            "minimum_bytes": source["minimum_bytes"],
            "notes": source["notes"],
        },
        "rights": {
            "status": _rights_status(source["notes"], rel),
            "notes": source["notes"],
        },
        "target": target,
    }
    if third_party_html:
        pdf_rel = str(PurePosixPath(rel).with_suffix(".pdf"))
        result["delivery"] = {
            "status": "pending-normalization",
            "source_format": "cleaned-markdown",
            "media_type": "application/pdf",
            "r2_key": f"References/{pdf_rel}",
            "public_url": f"{site_root}/References/{pdf_rel}",
        }
    return result


def build_initial_manifest() -> dict:
    tags = _tags_by_path()
    downloads = _download_sources()
    entries = [_entry(path, tags, downloads) for path in _reference_payloads()]
    return {
        "schema_version": SCHEMA_VERSION,
        "policy": {
            "public_reference_origin": site_base_url().rstrip("/"),
            "active_translation_projects": ["KD", "MSM"],
            "original_third_party_html_is_public": False,
            "study_reference_delivery_format": "pdf",
        },
        "artifacts": entries,
    }


def _canonical_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_initial_manifest(*, force: bool = False) -> None:
    if MANIFEST_PATH.exists() and not force:
        raise FileExistsError(
            f"{MANIFEST_PATH.relative_to(BASE)} already exists; use --force only while "
            "the complete pre-migration source tree is still present"
        )
    manifest = build_initial_manifest()
    write_text_lf(MANIFEST_PATH, _canonical_json(manifest))
    print(
        f"Wrote {MANIFEST_PATH.relative_to(BASE)} "
        f"({len(manifest['artifacts'])} immutable artifacts)."
    )


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("reference artifact manifest root must be an object")
    return data


def public_delivery_url(repo_path: str, data: dict | None = None) -> str | None:
    """Return the public delivery URL, following an HTML snapshot to its PDF."""
    normalized = _safe_relative_path(repo_path)
    manifest = data or load_manifest()
    by_path = {row.get("repo_path"): row for row in manifest.get("artifacts", [])}
    row = by_path.get(normalized)
    if row is None and PurePosixPath(normalized).suffix.lower() == ".md":
        row = by_path.get(str(PurePosixPath(normalized).with_suffix(".pdf")))
    if row is None:
        return None
    delivery_path = (row.get("delivery") or {}).get("artifact_repo_path")
    if delivery_path:
        row = by_path.get(delivery_path)
        if row is None:
            return None
    target = row.get("target") or {}
    if target.get("storage") not in {
        "r2-public",
        "git-retained-active-translation",
        "git-retained-rights-review",
        "external-only-rights-review",
    }:
        return None
    return target.get("public_url")


def artifact_local_path(entry: dict) -> Path:
    """Return the authoritative local bytes for a manifest row."""
    generation = entry.get("generation") or {}
    build_path = generation.get("build_path")
    if entry.get("state") == "generated-local" and build_path:
        return BASE / _safe_relative_path(str(build_path))
    return BASE / _safe_relative_path(str(entry.get("repo_path", "")))


def register_normalized_pdf(source_html: Path, pdf_path: Path) -> None:
    """Register one cleaned-Markdown PDF while retaining its original HTML privately."""
    source_html = source_html.resolve()
    pdf_path = pdf_path.resolve()
    try:
        source_rel = source_html.relative_to(REFERENCES.resolve()).as_posix()
        build_rel = pdf_path.relative_to(BASE.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("source HTML and generated PDF must be inside the repository") from exc
    if source_html.suffix.lower() != ".html" or not source_html.is_file():
        raise ValueError(f"normalization source is not a local HTML file: {source_html}")
    if pdf_path.suffix.lower() != ".pdf" or not pdf_path.is_file():
        raise ValueError(f"normalization output is not a local PDF file: {pdf_path}")
    if not pdf_path.read_bytes().startswith(b"%PDF-"):
        raise ValueError(f"normalization output is not a valid PDF: {pdf_path}")

    markdown_path = source_html.with_suffix(".md")
    if not markdown_path.is_file():
        raise ValueError(f"cleaned Markdown source is missing: {markdown_path}")

    data = load_manifest()
    html_repo_path = f"References/{source_rel}"
    html_rows = [row for row in data["artifacts"] if row.get("repo_path") == html_repo_path]
    if len(html_rows) != 1 or html_rows[0].get("kind") != "third-party-html-snapshot":
        raise ValueError(f"manifest does not contain one third-party HTML row for {html_repo_path}")
    html_row = html_rows[0]

    pdf_repo_path = f"References/{PurePosixPath(source_rel).with_suffix('.pdf')}"
    existing = [row for row in data["artifacts"] if row.get("repo_path") == pdf_repo_path]
    if existing:
        data["artifacts"].remove(existing[0])

    site_root = site_base_url().rstrip("/")
    pdf_row = {
        "repo_path": pdf_repo_path,
        "kind": "normalized-reference-pdf",
        "state": "generated-local",
        "tags": list(html_row.get("tags") or []),
        "source": {
            "bytes": pdf_path.stat().st_size,
            "sha256": _sha256(pdf_path),
            "media_type": "application/pdf",
            "urls": list((html_row.get("source") or {}).get("urls") or []),
            "minimum_bytes": 500,
            "notes": "Generated deterministically from cleaned Markdown; original HTML retained privately.",
        },
        "rights": dict(html_row.get("rights") or {}),
        "target": _normalized_pdf_target(html_row, pdf_repo_path),
        "generation": {
            "source_markdown": markdown_path.relative_to(BASE).as_posix(),
            "original_html": html_repo_path,
            "build_path": build_rel,
            **generated_pdf_signature(pdf_path),
        },
    }
    html_row["tags"] = []
    html_row["delivery"] = {
        "status": "generated-local",
        "artifact_repo_path": pdf_repo_path,
        "source_format": "cleaned-markdown",
        "markdown_path": markdown_path.relative_to(BASE).as_posix(),
        "build_path": build_rel,
        "bytes": pdf_path.stat().st_size,
        "sha256": _sha256(pdf_path),
    }
    data["artifacts"].append(pdf_row)
    data["artifacts"].sort(key=lambda row: row.get("repo_path", ""))
    by_repo_path = {row.get("repo_path"): row for row in data["artifacts"]}
    for generated in data["artifacts"]:
        if generated.get("state") != "generated-local":
            continue
        generated_path = artifact_local_path(generated)
        if not generated_path.is_file():
            continue
        generated["source"]["bytes"] = generated_path.stat().st_size
        generated["source"]["sha256"] = _sha256(generated_path)
        original_path = (generated.get("generation") or {}).get("original_html")
        original_row = by_repo_path.get(original_path)
        if original_row and original_row.get("delivery"):
            original_row["delivery"]["bytes"] = generated_path.stat().st_size
            original_row["delivery"]["sha256"] = generated["source"]["sha256"]
    errors = manifest_errors(data, require_local_sources=True)
    if errors:
        raise ValueError("updated manifest is invalid:\n  - " + "\n  - ".join(errors))
    write_text_lf(MANIFEST_PATH, _canonical_json(data))
    print(f"Registered normalized PDF: {pdf_repo_path}")


def refresh_source_metadata() -> None:
    """Refresh provenance metadata without rebuilding or discarding migration state."""
    data = load_manifest()
    downloads = _download_sources()
    changed = 0
    for row in data["artifacts"]:
        generation = row.get("generation") or {}
        original = generation.get("original_html")
        source_repo_path = original or row.get("repo_path", "")
        if not source_repo_path.startswith("References/"):
            continue
        rel = source_repo_path.removeprefix("References/")
        metadata = downloads.get(rel)
        if metadata is None:
            continue
        source = row.get("source") or {}
        before = (source.get("urls"), source.get("minimum_bytes"), source.get("notes"))
        source["urls"] = list(metadata["urls"])
        source["minimum_bytes"] = metadata["minimum_bytes"]
        if row.get("kind") != "normalized-reference-pdf":
            source["notes"] = metadata["notes"]
        row["source"] = source
        rights = row.get("rights") or {}
        rights["status"] = _rights_status(metadata["notes"], rel)
        rights["notes"] = metadata["notes"]
        row["rights"] = rights
        after = (source.get("urls"), source.get("minimum_bytes"), source.get("notes"))
        changed += before != after
    errors = manifest_errors(data, require_local_sources=True)
    if errors:
        raise ValueError("refreshed manifest is invalid:\n  - " + "\n  - ".join(errors))
    write_text_lf(MANIFEST_PATH, _canonical_json(data))
    print(f"Refreshed provenance metadata for {changed} artifact(s).")


def apply_storage_policy() -> None:
    """Reconcile targets with rights decisions and generated-file policy."""
    data = load_manifest()
    site_root = site_base_url().rstrip("/")
    by_path = {row["repo_path"]: row for row in data["artifacts"]}
    changed = 0
    for row in data["artifacts"]:
        repo_path = row["repo_path"]
        rel = repo_path.removeprefix("References/")
        old = (row.get("state"), dict(row.get("target") or {}), dict(row.get("rights") or {}))
        rights = row.get("rights") or {}
        if rel in SITE_OWNER_APPROVED_PATHS:
            rights["status"] = "existing-site-publication-approved"
            rights["notes"] = "Existing site publication; R2 storage migration approved by the site owner."
        row["rights"] = rights
        storage = (row.get("target") or {}).get("storage")

        if storage == "git-retained-active-translation":
            continue
        if row.get("kind") == "third-party-html-snapshot":
            row["state"] = "r2-published" if row.get("state") == "r2-published" else "git-source"
            row["target"] = {
                "storage": "r2-private-original",
                "r2_key": f"archive/original-html/{rel}",
                "public_url": None,
            }
        elif row.get("kind") == "generated-reference-html":
            row["state"] = "generated-in-git"
            row["target"] = {
                "storage": "generated-on-demand",
                "r2_key": None,
                "public_url": None,
            }
        elif row.get("kind") == "normalized-reference-pdf":
            original_path = (row.get("generation") or {}).get("original_html")
            original = by_path.get(original_path)
            if original is None:
                raise ValueError(f"normalized PDF has no original manifest row: {repo_path}")
            row["target"] = _normalized_pdf_target(original, repo_path)
            if row["target"]["storage"] == "external-only-rights-review":
                row["state"] = "generated-local"
        elif rights.get("status") == "review-required":
            row["state"] = "git-retained"
            row["target"] = {
                "storage": "git-retained-rights-review",
                "r2_key": None,
                "public_url": f"{site_root}/{repo_path}",
            }
        else:
            row["state"] = "r2-published" if row.get("state") == "r2-published" else "git-source"
            row["target"] = {
                "storage": "r2-public",
                "r2_key": repo_path,
                "public_url": f"{site_root}/{repo_path}",
            }
        new = (row.get("state"), dict(row.get("target") or {}), dict(row.get("rights") or {}))
        changed += old != new

    # Already-published R2 sources are intentionally absent from a post-migration
    # checkout. Newly approved rows become ``git-source`` above, so the normal
    # manifest gate still requires their local bytes before policy can advance.
    errors = manifest_errors(data)
    if errors:
        raise ValueError("storage policy produced an invalid manifest:\n  - " + "\n  - ".join(errors))
    write_text_lf(MANIFEST_PATH, _canonical_json(data))
    print(f"Applied reference storage policy to {changed} artifact(s).")


def manifest_errors(data: dict, *, require_local_sources: bool = False) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        return errors + ["artifacts must be an array"]

    repo_paths: set[str] = set()
    r2_keys: set[str] = set()
    public_urls: set[str] = set()
    for index, entry in enumerate(artifacts):
        label = f"artifacts[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        repo_path = entry.get("repo_path")
        try:
            normalized = _safe_relative_path(str(repo_path))
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue
        if not normalized.startswith("References/"):
            errors.append(f"{label}: repo_path must start with References/")
        if normalized in repo_paths:
            errors.append(f"duplicate repo_path: {normalized}")
        repo_paths.add(normalized)

        source = entry.get("source") or {}
        if not isinstance(source.get("bytes"), int) or source.get("bytes", 0) <= 0:
            errors.append(f"{normalized}: source.bytes must be positive")
        if not re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256", ""))):
            errors.append(f"{normalized}: source.sha256 must be lowercase SHA-256")

        if (
            entry.get("kind") == "normalized-reference-pdf"
            and (entry.get("target") or {}).get("storage") == "r2-public"
        ):
            generation = entry.get("generation") or {}
            if not isinstance(generation.get("pages"), int) or generation.get("pages", 0) <= 0:
                errors.append(f"{normalized}: generation.pages must be positive")
            if not re.fullmatch(r"[0-9a-f]{64}", str(generation.get("text_sha256", ""))):
                errors.append(f"{normalized}: generation.text_sha256 must be lowercase SHA-256")

        target = entry.get("target") or {}
        for key_name in (target.get("r2_key"), (entry.get("delivery") or {}).get("r2_key")):
            if not key_name:
                continue
            try:
                safe_key = _safe_relative_path(str(key_name))
            except ValueError as exc:
                errors.append(f"{normalized}: {exc}")
                continue
            if safe_key in r2_keys:
                errors.append(f"duplicate R2 key: {safe_key}")
            r2_keys.add(safe_key)
        for url in (target.get("public_url"), (entry.get("delivery") or {}).get("public_url")):
            if not url:
                continue
            if url in public_urls:
                errors.append(f"duplicate public URL: {url}")
            public_urls.add(url)

        try:
            local = artifact_local_path(entry)
        except ValueError as exc:
            errors.append(f"{normalized}: {exc}")
            continue
        must_exist = require_local_sources or entry.get("state") in {
            "git-source",
            "git-retained",
        }
        if must_exist and not local.is_file():
            errors.append(f"missing required local source: {normalized}")
            continue
        if local.is_file():
            is_public_derivative = (
                entry.get("kind") == "normalized-reference-pdf"
                and target.get("storage") == "r2-public"
            )
            if is_public_derivative:
                signature = generated_pdf_signature(local)
                generation = entry.get("generation") or {}
                expected = {
                    "pages": generation.get("pages"),
                    "text_sha256": generation.get("text_sha256"),
                }
                if signature != expected:
                    errors.append(
                        f"{normalized}: generated content signature mismatch "
                        f"(manifest {expected}, local {signature})"
                    )
            else:
                actual_size = local.stat().st_size
                if actual_size != source.get("bytes"):
                    errors.append(
                        f"{normalized}: size mismatch "
                        f"(manifest {source.get('bytes')}, local {actual_size})"
                    )
                actual_hash = _sha256(local)
                if actual_hash != source.get("sha256"):
                    errors.append(f"{normalized}: SHA-256 mismatch")

    if artifacts != sorted(artifacts, key=lambda item: item.get("repo_path", "")):
        errors.append("artifacts must be sorted by repo_path")
    return errors


def print_summary(data: dict) -> None:
    artifacts = data.get("artifacts") or []
    by_storage: dict[str, list[dict]] = {}
    for entry in artifacts:
        storage = (entry.get("target") or {}).get("storage", "unknown")
        by_storage.setdefault(storage, []).append(entry)
    print(f"Reference artifact manifest: {len(artifacts)} artifact(s)")
    for storage in sorted(by_storage):
        rows = by_storage[storage]
        total = sum((row.get("source") or {}).get("bytes", 0) for row in rows)
        print(f"  {storage}: {len(rows)} artifact(s), {total / 1024 / 1024:.2f} MiB")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--bootstrap", action="store_true", help="Create the initial manifest.")
    actions.add_argument("--check", action="store_true", help="Validate the checked-in manifest.")
    actions.add_argument("--summary", action="store_true", help="Summarize the checked-in manifest.")
    actions.add_argument(
        "--register-normalized",
        metavar="SOURCE_HTML",
        help="Register the generated PDF for one third-party HTML snapshot.",
    )
    actions.add_argument(
        "--refresh-source-metadata",
        action="store_true",
        help="Refresh download URLs and rights notes without rebuilding migration state.",
    )
    actions.add_argument(
        "--apply-storage-policy",
        action="store_true",
        help="Reconcile R2, Git-retained, external-only, and generated targets.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing manifest during pre-migration bootstrap only.",
    )
    parser.add_argument(
        "--require-local-sources",
        action="store_true",
        help="Require every manifest source to be present locally.",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Generated PDF path used with --register-normalized.",
    )
    args = parser.parse_args()

    try:
        if args.bootstrap:
            write_initial_manifest(force=args.force)
            return 0
        if args.register_normalized:
            if args.pdf is None:
                parser.error("--register-normalized requires --pdf")
            register_normalized_pdf(Path(args.register_normalized), args.pdf)
            return 0
        if args.refresh_source_metadata:
            refresh_source_metadata()
            return 0
        if args.apply_storage_policy:
            apply_storage_policy()
            return 0
        data = load_manifest()
        if args.summary:
            print_summary(data)
            return 0
        errors = manifest_errors(data, require_local_sources=args.require_local_sources)
        if errors:
            print("Reference artifact manifest check failed:\n  - " + "\n  - ".join(errors))
            return 1
        print_summary(data)
        print("OK: reference artifact manifest is valid and local sources match.")
        return 0
    except (FileExistsError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Reference artifact manifest error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

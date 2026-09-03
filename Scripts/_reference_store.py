"""Resolve manifest-backed reference artifacts from Git, cache, or public delivery."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent
REFERENCES = BASE / "References"
MANIFEST_PATH = REFERENCES / "r2-artifacts.json"
DEFAULT_CACHE = SCRIPTS / "_reference_cache"
USER_AGENT = "AnalyticMadhyasthDarshan-reference-hydrator/1"


def _safe_relative_path(raw: str) -> str:
    normalized = urllib.parse.unquote(raw).replace("\\", "/").lstrip("/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe reference path: {raw!r}")
    return path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cache_root(environ: dict[str, str] | None = None) -> Path:
    values = os.environ if environ is None else environ
    configured = values.get("AMD_REFERENCE_CACHE", "").strip()
    return Path(configured).resolve() if configured else DEFAULT_CACHE


@dataclass(frozen=True)
class Artifact:
    repo_path: str
    kind: str
    state: str
    tags: tuple[str, ...]
    bytes: int
    sha256: str
    media_type: str
    storage: str
    r2_key: str | None
    public_url: str | None
    build_path: str | None


class ReferenceStore:
    def __init__(
        self,
        *,
        manifest_path: Path = MANIFEST_PATH,
        references_root: Path = REFERENCES,
        cache_root: Path | None = None,
        public_origin_override: str | None = None,
    ) -> None:
        self.manifest_path = manifest_path
        self.references_root = references_root.resolve()
        self.cache_root = (cache_root or _cache_root()).resolve()
        self.public_origin_override = (
            public_origin_override.rstrip("/") if public_origin_override else None
        )
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = raw.get("artifacts")
        if not isinstance(rows, list):
            raise ValueError("reference artifact manifest has no artifacts array")
        self.artifacts = tuple(self._artifact(row) for row in rows)
        self._by_repo_path = {item.repo_path: item for item in self.artifacts}
        self._by_tag = {
            tag: item for item in self.artifacts for tag in item.tags
        }
        self._by_public_url = {
            item.public_url: item for item in self.artifacts if item.public_url
        }

    @staticmethod
    def _artifact(row: dict) -> Artifact:
        source = row.get("source") or {}
        target = row.get("target") or {}
        repo_path = _safe_relative_path(str(row.get("repo_path", "")))
        if not repo_path.startswith("References/"):
            raise ValueError(f"manifest repo path is outside References/: {repo_path}")
        return Artifact(
            repo_path=repo_path,
            kind=str(row.get("kind", "")),
            state=str(row.get("state", "")),
            tags=tuple(str(tag) for tag in row.get("tags") or []),
            bytes=int(source.get("bytes", 0)),
            sha256=str(source.get("sha256", "")),
            media_type=str(source.get("media_type", "application/octet-stream")),
            storage=str(target.get("storage", "")),
            r2_key=str(target["r2_key"]) if target.get("r2_key") else None,
            public_url=str(target["public_url"]) if target.get("public_url") else None,
            build_path=(
                str((row.get("generation") or {})["build_path"])
                if (row.get("generation") or {}).get("build_path")
                else None
            ),
        )

    @staticmethod
    def normalize_repo_path(value: str | Path) -> str:
        raw = value.as_posix() if isinstance(value, Path) else str(value)
        normalized = _safe_relative_path(raw.split("#", 1)[0].split("?", 1)[0])
        if normalized.startswith("References/"):
            return normalized
        return f"References/{normalized}"

    def find(self, value: str | Path) -> Artifact | None:
        raw = str(value)
        if raw in self._by_tag:
            return self._by_tag[raw]
        candidate = Path(raw)
        if candidate.is_absolute():
            try:
                rel = candidate.resolve().relative_to(self.references_root).as_posix()
            except ValueError:
                return None
            return self._by_repo_path.get(f"References/{rel}")
        if raw.startswith(("http://", "https://")):
            clean = raw.split("#", 1)[0]
            direct = self._by_public_url.get(clean)
            if direct:
                return direct
            path = urllib.parse.urlsplit(clean).path.lstrip("/")
            try:
                return self._by_repo_path.get(self.normalize_repo_path(path))
            except ValueError:
                return None
        try:
            return self._by_repo_path.get(self.normalize_repo_path(value))
        except ValueError:
            return None

    def find_tag(self, tag: str) -> Artifact | None:
        return self._by_tag.get(tag)

    def local_path(self, artifact: Artifact) -> Path:
        if artifact.state == "generated-local" and artifact.build_path:
            candidate = (BASE / _safe_relative_path(artifact.build_path)).resolve()
            if not candidate.is_relative_to(BASE):
                raise ValueError(f"generated build path escaped repository: {artifact.build_path}")
            return candidate
        rel = artifact.repo_path.removeprefix("References/")
        return (self.references_root / rel).resolve()

    def cache_path(self, artifact: Artifact) -> Path:
        rel = artifact.repo_path.removeprefix("References/")
        candidate = (self.cache_root / rel).resolve()
        if not candidate.is_relative_to(self.cache_root):
            raise ValueError(f"cache path escaped cache root: {artifact.repo_path}")
        return candidate

    @staticmethod
    def verify_file(path: Path, artifact: Artifact) -> None:
        if not path.is_file():
            raise FileNotFoundError(path)
        actual_size = path.stat().st_size
        if actual_size != artifact.bytes:
            raise ValueError(
                f"reference size mismatch for {artifact.repo_path}: "
                f"expected {artifact.bytes}, got {actual_size}"
            )
        actual_hash = _sha256(path)
        if actual_hash != artifact.sha256:
            raise ValueError(
                f"reference SHA-256 mismatch for {artifact.repo_path}: "
                f"expected {artifact.sha256}, got {actual_hash}"
            )

    def _download_url(self, artifact: Artifact) -> str:
        if not artifact.public_url:
            raise ValueError(
                f"reference is not publicly hydratable: {artifact.repo_path} "
                f"({artifact.storage})"
            )
        if not self.public_origin_override:
            return artifact.public_url
        path = urllib.parse.urlsplit(artifact.public_url).path
        return f"{self.public_origin_override}/{path.lstrip('/')}"

    def hydrate(self, artifact: Artifact, *, force: bool = False) -> Path:
        cache = self.cache_path(artifact)
        if cache.is_file() and not force:
            self.verify_file(cache, artifact)
            return cache

        url = self._download_url(artifact)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        cache.parent.mkdir(parents=True, exist_ok=True)
        temp_name = ""
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                with tempfile.NamedTemporaryFile(
                    mode="wb", prefix=f".{cache.name}.", suffix=".partial",
                    dir=cache.parent, delete=False,
                ) as handle:
                    temp_name = handle.name
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
            temp_path = Path(temp_name)
            self.verify_file(temp_path, artifact)
            temp_path.replace(cache)
            return cache
        except (OSError, ValueError, urllib.error.URLError):
            if temp_name:
                Path(temp_name).unlink(missing_ok=True)
            raise

    def resolve(
        self,
        value: str | Path | Artifact,
        *,
        allow_download: bool = False,
        force: bool = False,
    ) -> Path:
        artifact = value if isinstance(value, Artifact) else self.find(value)
        if artifact is None:
            raise KeyError(f"reference is absent from manifest: {value}")

        local = self.local_path(artifact)
        if local.is_file() and not force:
            self.verify_file(local, artifact)
            return local
        cache = self.cache_path(artifact)
        if cache.is_file() and not force:
            self.verify_file(cache, artifact)
            return cache
        if allow_download:
            return self.hydrate(artifact, force=force)
        raise FileNotFoundError(
            f"reference is not local or cached: {artifact.repo_path}; "
            "run Scripts/_hydrate_references.py"
        )

    def public_artifacts(self) -> Iterable[Artifact]:
        return (item for item in self.artifacts if item.public_url and item.storage == "r2-public")


def load_reference_store() -> ReferenceStore:
    return ReferenceStore()

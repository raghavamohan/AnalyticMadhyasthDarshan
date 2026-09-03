"""Shared manifest and provenance helpers for companion presentations."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _common import APPLICATIONS, BASE, STUDIES

MANIFEST_PATH = Path(__file__).with_name("presentation-pipeline.json")
SUPPORTED_ENGINES = {"powerpoint", "libreoffice"}


@dataclass(frozen=True)
class RendererProfile:
    name: str
    engine: str
    version: str
    status: str
    installer_url: str | None = None
    installer_sha256: str | None = None


@dataclass(frozen=True)
class DeckSpec:
    id: str
    source: Path
    slides_pdf: Path
    notes_pdf: Path
    required_fonts: tuple[str, ...]


@dataclass(frozen=True)
class PresentationManifest:
    schema_version: int
    production_profile: str
    renderer_profiles: dict[str, RendererProfile]
    decks: tuple[DeckSpec, ...]

    def profile(self, name: str | None = None) -> RendererProfile:
        selected = name or self.production_profile
        try:
            return self.renderer_profiles[selected]
        except KeyError as exc:
            raise ValueError(f"Unknown renderer profile: {selected}") from exc

    def deck(self, deck_id: str) -> DeckSpec:
        for spec in self.decks:
            if spec.id == deck_id:
                return spec
        raise ValueError(f"Unknown presentation id: {deck_id}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty repository-relative path")
    raw = Path(value.replace("\\", "/"))
    if raw.is_absolute() or ".." in raw.parts:
        raise ValueError(f"{field} must stay inside the repository: {value}")
    resolved = (BASE / raw).resolve()
    try:
        resolved.relative_to(BASE.resolve())
    except ValueError as exc:
        raise ValueError(f"{field} escapes the repository: {value}") from exc
    return resolved


def load_manifest(path: Path = MANIFEST_PATH) -> PresentationManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise ValueError("presentation manifest schemaVersion must be 1")

    raw_profiles = data.get("rendererProfiles")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise ValueError("presentation manifest requires rendererProfiles")
    profiles: dict[str, RendererProfile] = {}
    for name, raw in raw_profiles.items():
        engine = raw.get("engine")
        if engine not in SUPPORTED_ENGINES:
            raise ValueError(f"renderer profile {name!r} has unsupported engine {engine!r}")
        installer = raw.get("installer") or {}
        profiles[name] = RendererProfile(
            name=name,
            engine=engine,
            version=str(raw.get("version") or ""),
            status=str(raw.get("status") or ""),
            installer_url=installer.get("url"),
            installer_sha256=installer.get("sha256"),
        )
        if not profiles[name].version or not profiles[name].status:
            raise ValueError(f"renderer profile {name!r} requires version and status")

    production = data.get("productionProfile")
    if production not in profiles:
        raise ValueError("productionProfile must name a rendererProfiles entry")

    raw_decks = data.get("decks")
    if not isinstance(raw_decks, list) or not raw_decks:
        raise ValueError("presentation manifest requires at least one deck")
    decks: list[DeckSpec] = []
    for index, raw in enumerate(raw_decks):
        prefix = f"decks[{index}]"
        fonts = raw.get("requiredFonts")
        if not isinstance(fonts, list) or not fonts or not all(isinstance(x, str) for x in fonts):
            raise ValueError(f"{prefix}.requiredFonts must be a non-empty string list")
        decks.append(DeckSpec(
            id=str(raw.get("id") or ""),
            source=_repo_path(raw.get("source"), f"{prefix}.source"),
            slides_pdf=_repo_path(raw.get("slidesPdf"), f"{prefix}.slidesPdf"),
            notes_pdf=_repo_path(raw.get("notesPdf"), f"{prefix}.notesPdf"),
            required_fonts=tuple(fonts),
        ))
        if not decks[-1].id:
            raise ValueError(f"{prefix}.id must be non-empty")

    return PresentationManifest(1, production, profiles, tuple(decks))


def manifest_errors(manifest: PresentationManifest) -> list[str]:
    """Return coverage and path-safety errors without rendering any artifact."""
    errors: list[str] = []
    ids = [spec.id for spec in manifest.decks]
    if len(ids) != len(set(ids)):
        errors.append("presentation ids are not unique")

    sources = [spec.source for spec in manifest.decks]
    if len(sources) != len(set(sources)):
        errors.append("presentation source paths are not unique")

    outputs = [path for spec in manifest.decks for path in (spec.slides_pdf, spec.notes_pdf)]
    if len(outputs) != len(set(outputs)):
        errors.append("presentation output paths are not unique")

    discovered = {
        path
        for path in set(STUDIES.glob("*/*.pptx")) | set(APPLICATIONS.glob("*/*.pptx"))
        if not path.name.startswith("~$")
    }
    declared = set(sources)
    for path in sorted(discovered - declared):
        errors.append(f"unmanifested PPTX: {path.relative_to(BASE).as_posix()}")
    for path in sorted(declared - discovered):
        errors.append(f"manifest source is missing: {path.relative_to(BASE).as_posix()}")

    for spec in manifest.decks:
        if spec.source.suffix.lower() != ".pptx":
            errors.append(f"{spec.id}: source must end in .pptx")
        for label, path in (("slidesPdf", spec.slides_pdf), ("notesPdf", spec.notes_pdf)):
            if path.suffix.lower() != ".pdf":
                errors.append(f"{spec.id}: {label} must end in .pdf")
            if path.parent != spec.source.parent:
                errors.append(f"{spec.id}: {label} must stay beside its PPTX")
        canonical_md = spec.source.parent / f"{spec.source.parent.name}.md"
        canonical_pdf = canonical_md.with_suffix(".pdf")
        if canonical_md.is_file() and spec.slides_pdf == canonical_pdf:
            errors.append(
                f"{spec.id}: slidesPdf collides with canonical study PDF; use an explicit "
                "presentation filename"
            )
        if spec.notes_pdf == spec.slides_pdf:
            errors.append(f"{spec.id}: notesPdf collides with slidesPdf")
    return errors


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(BASE.resolve()).as_posix()

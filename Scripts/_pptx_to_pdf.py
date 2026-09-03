#!/usr/bin/env python3
"""Convert a PowerPoint (.pptx) deck to PDF.

The renderer is selected from ``presentation-pipeline.json`` and its version is
asserted before conversion.  Callers may choose another declared profile, but
there is no host-dependent fallback: the same source must not silently use a
different renderer on another machine.

Examples (from repo root):

  python Scripts/_pptx_to_pdf.py Studies/The-Ontology-of-Coexistence/The-Ontology-of-Existence-Madhyasth-Darshan.pptx
  python Scripts/_pptx_to_pdf.py Studies/The-Ontology-of-Coexistence/The-Ontology-of-Existence-Madhyasth-Darshan.pptx --engine libreoffice
  python Scripts/_pptx_to_pdf.py --study The-Ontology-of-Coexistence --deck The-Ontology-of-Existence-Madhyasth-Darshan.pptx
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _common import STUDIES, configure_utf8_stdio
from _presentation_pipeline import load_manifest

POWERPOINT_CONVERTER = Path(__file__).with_name("_powerpoint_to_pdf.ps1")
POWERPOINT_CANDIDATES = (
    Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    / "Microsoft Office"
    / "root"
    / "Office16"
    / "POWERPNT.EXE",
    Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    / "Microsoft Office"
    / "Office16"
    / "POWERPNT.EXE",
)
LIBREOFFICE_CANDIDATES = (
    Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    / "LibreOffice"
    / "program"
    / "soffice.exe",
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    / "LibreOffice"
    / "program"
    / "soffice.exe",
)


def _find_first(candidates: tuple[Path, ...], *, path_names: tuple[str, ...]) -> Path | None:
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    for name in path_names:
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def find_powerpoint() -> Path | None:
    return _find_first(POWERPOINT_CANDIDATES, path_names=("POWERPNT.EXE", "powerpnt"))


def find_libreoffice() -> Path | None:
    return _find_first(LIBREOFFICE_CANDIDATES, path_names=("soffice", "soffice.exe"))


def resolve_pptx(path: Path | None, study: str | None, deck: str | None) -> Path:
    if path is not None:
        pptx = path.expanduser().resolve()
    elif study and deck:
        pptx = (STUDIES / study / deck).resolve()
    elif study:
        study_dir = STUDIES / study
        if not study_dir.is_dir():
            raise SystemExit(f"Study directory not found: {study_dir}")
        decks = sorted(study_dir.glob("*.pptx"))
        if not decks:
            raise SystemExit(f"No .pptx found under {study_dir}")
        if len(decks) > 1:
            names = ", ".join(p.name for p in decks)
            raise SystemExit(
                f"Multiple .pptx under {study_dir}; pass --deck <file> or a path.\nFound: {names}"
            )
        pptx = decks[0].resolve()
    else:
        raise SystemExit("Provide a .pptx path, or --study [and optional --deck].")

    if not pptx.is_file():
        raise SystemExit(f"PPTX not found: {pptx}")
    if pptx.suffix.lower() != ".pptx":
        raise SystemExit(f"Expected a .pptx file, got: {pptx}")
    return pptx


def _manifest_output(pptx: Path) -> Path | None:
    manifest = load_manifest()
    source = pptx.resolve()
    for spec in manifest.decks:
        if spec.source == source:
            return spec.slides_pdf
    return None


def resolve_output(pptx: Path, output: Path | None) -> Path:
    if output is None:
        declared = _manifest_output(pptx)
        if declared is not None:
            return declared
        try:
            pptx.resolve().relative_to(STUDIES.resolve())
        except ValueError:
            return pptx.with_suffix(".pdf")
        raise SystemExit(
            f"Deck is under Studies but absent from presentation-pipeline.json: {pptx}"
        )
    out = output.expanduser().resolve()
    if out.suffix.lower() != ".pdf":
        raise SystemExit(f"Output must end with .pdf: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def convert_with_powerpoint(pptx: Path, pdf: Path) -> None:
    if sys.platform != "win32":
        raise RuntimeError("Microsoft PowerPoint COM conversion requires Windows.")
    if find_powerpoint() is None:
        raise RuntimeError(
            "Microsoft PowerPoint (POWERPNT.EXE) not found. "
            "Install Office or use --engine libreoffice."
        )

    completed = subprocess.run(
        [
            "powershell.exe", "-NoProfile", "-NonInteractive", "-File",
            str(POWERPOINT_CONVERTER), "-InputPath", str(pptx.resolve()),
            "-OutputPath", str(pdf.resolve()),
        ],
        check=False, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(
            f"PowerPoint conversion failed (exit {completed.returncode}). {detail}"
        )


def convert_with_libreoffice(pptx: Path, pdf: Path) -> None:
    soffice = find_libreoffice()
    if soffice is None:
        raise RuntimeError(
            "LibreOffice soffice.exe not found. Install LibreOffice or use --engine powerpoint."
        )

    with tempfile.TemporaryDirectory(prefix="pptx2pdf_") as tmp:
        tmp_dir = Path(tmp)
        cmd = [
            str(soffice),
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmp_dir),
            str(pptx.resolve()),
        ]
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            cwd=str(tmp_dir),
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(
                f"LibreOffice conversion failed (exit {completed.returncode}). {detail}"
            )
        produced = tmp_dir / f"{pptx.stem}.pdf"
        if not produced.is_file():
            # Rare: LibreOffice may alter the stem; pick the only PDF.
            pdfs = list(tmp_dir.glob("*.pdf"))
            if len(pdfs) != 1:
                raise RuntimeError(f"LibreOffice did not write an expected PDF in {tmp_dir}")
            produced = pdfs[0]
        shutil.move(str(produced), str(pdf))


def renderer_version(engine: str) -> str:
    """Return the exact executable version used by a declared renderer."""
    if engine == "libreoffice":
        executable = find_libreoffice()
        if executable is None:
            raise RuntimeError("LibreOffice is not installed or not on PATH.")
        completed = subprocess.run(
            [str(executable), "--version"], check=False, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
        detail = (completed.stdout or completed.stderr or "").strip()
        match = __import__("re").search(r"\b(\d+\.\d+\.\d+\.\d+)\b", detail)
        if completed.returncode != 0 or match is None:
            raise RuntimeError(f"Could not determine LibreOffice version: {detail}")
        return match.group(1)
    if engine == "powerpoint":
        executable = find_powerpoint()
        if executable is None:
            raise RuntimeError("Microsoft PowerPoint is not installed.")
        if sys.platform != "win32":
            raise RuntimeError("Microsoft PowerPoint version detection requires Windows.")
        escaped = str(executable).replace("'", "''")
        completed = subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                f"(Get-Item -LiteralPath '{escaped}').VersionInfo.FileVersion",
            ],
            check=False, capture_output=True, text=True, encoding="utf-8",
            errors="replace",
        )
        version = completed.stdout.strip()
        if completed.returncode != 0 or not version:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(f"Could not determine PowerPoint version: {detail}")
        return version
    raise ValueError(f"Unknown engine: {engine}")


def assert_renderer_version(engine: str, expected: str) -> str:
    actual = renderer_version(engine)
    if actual != expected:
        message = f"{engine} version {actual} does not match required {expected}"
        if os.environ.get("AMD_ALLOW_PRESENTATION_RENDERER_MISMATCH") == "1":
            print(f"WARNING: {message}", file=sys.stderr)
        else:
            raise RuntimeError(
                message + ". Set AMD_ALLOW_PRESENTATION_RENDERER_MISMATCH=1 only "
                "for a diagnostic comparison; do not publish that output."
            )
    return actual


def renderer_profile_for_engine(engine: str | None, profile_name: str | None):
    manifest = load_manifest()
    if profile_name:
        profile = manifest.profile(profile_name)
        if engine and engine != profile.engine:
            raise ValueError(
                f"--engine {engine} conflicts with renderer profile {profile_name} "
                f"({profile.engine})"
            )
        return profile
    if engine:
        matches = [p for p in manifest.renderer_profiles.values() if p.engine == engine]
        if len(matches) != 1:
            raise ValueError(f"Engine {engine!r} does not resolve to exactly one profile")
        return matches[0]
    return manifest.profile()


def convert_pptx_to_pdf(
    pptx: Path,
    pdf: Path,
    *,
    engine: str | None = None,
    expected_version: str | None = None,
) -> tuple[str, str]:
    """Convert PPTX atomically. Return ``(engine, renderer_version)``."""
    profile = renderer_profile_for_engine(engine, None)
    selected = profile.engine
    required = expected_version or profile.version
    actual = assert_renderer_version(selected, required)
    pdf.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{pdf.stem}-", suffix=".pdf", dir=pdf.parent)
    os.close(handle)
    temp_pdf = Path(temp_name)
    temp_pdf.unlink(missing_ok=True)
    try:
        if selected == "powerpoint":
            convert_with_powerpoint(pptx, temp_pdf)
        else:
            convert_with_libreoffice(pptx, temp_pdf)
        if not temp_pdf.is_file() or temp_pdf.stat().st_size < 100:
            raise RuntimeError(f"{selected} produced a missing or empty PDF: {temp_pdf}")
        os.replace(temp_pdf, pdf)
    finally:
        temp_pdf.unlink(missing_ok=True)
    return selected, actual


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Convert a study companion .pptx deck to PDF "
        "with an exact renderer profile declared in presentation-pipeline.json.",
    )
    parser.add_argument(
        "pptx",
        nargs="?",
        type=Path,
        help="Path to the .pptx file",
    )
    parser.add_argument(
        "--study",
        help="Study slug under Studies/ (use with optional --deck)",
    )
    parser.add_argument(
        "--deck",
        help="Deck filename under Studies/<Slug>/ (default: the only .pptx there)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output .pdf path (default: the manifest mapping for repository decks)",
    )
    parser.add_argument(
        "--engine",
        choices=("powerpoint", "libreoffice"),
        help="Declared conversion engine (default: production profile)",
    )
    parser.add_argument(
        "--profile",
        help="Renderer profile from presentation-pipeline.json",
    )
    args = parser.parse_args(argv)

    pptx = resolve_pptx(args.pptx, args.study, args.deck)
    pdf = resolve_output(pptx, args.output)

    try:
        profile = renderer_profile_for_engine(args.engine, args.profile)
        used, version = convert_pptx_to_pdf(
            pptx, pdf, engine=profile.engine, expected_version=profile.version
        )
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Wrote {pdf} (engine={used}, version={version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

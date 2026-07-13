#!/usr/bin/env python3
"""Convert a PowerPoint (.pptx) deck to PDF.

Preferred on Windows: Microsoft PowerPoint COM (best fidelity for hand-built decks).
Fallback: LibreOffice ``soffice --headless --convert-to pdf``.

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
import time
from pathlib import Path

from _common import STUDIES

try:
    import win32com.client as win32com_client  # type: ignore
except ImportError:  # pragma: no cover - optional on non-Windows / bare venv
    win32com_client = None  # type: ignore

PP_SAVE_AS_PDF = 32
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


def resolve_output(pptx: Path, output: Path | None) -> Path:
    if output is None:
        return pptx.with_suffix(".pdf")
    out = output.expanduser().resolve()
    if out.suffix.lower() != ".pdf":
        raise SystemExit(f"Output must end with .pdf: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def convert_with_powerpoint(pptx: Path, pdf: Path) -> None:
    if sys.platform != "win32":
        raise RuntimeError("Microsoft PowerPoint COM conversion requires Windows.")
    if win32com_client is None:
        raise RuntimeError(
            "pywin32 is required for the PowerPoint engine. "
            "Install with: pip install pywin32"
        )
    if find_powerpoint() is None:
        raise RuntimeError(
            "Microsoft PowerPoint (POWERPNT.EXE) not found. "
            "Install Office or use --engine libreoffice."
        )

    powerpoint = None
    presentation = None
    # PowerPoint COM requires absolute Windows paths and integer flags (not Python bools).
    pptx_abs = str(pptx.resolve())
    pdf_abs = str(pdf.resolve())
    try:
        powerpoint = win32com_client.DispatchEx("PowerPoint.Application")
        try:
            powerpoint.Visible = -1
        except Exception:
            pass
        try:
            powerpoint.DisplayAlerts = 1  # ppAlertsNone on some builds is 1; 0 also used
        except Exception:
            pass
        # Open(FileName, ReadOnly, Untitled, WithWindow) — use ints for COM marshalling.
        presentation = powerpoint.Presentations.Open(pptx_abs, 1, 0, 0)
        # Prefer ExportAsFixedFormat; fall back to SaveAs(ppSaveAsPDF).
        try:
            presentation.ExportAsFixedFormat(pdf_abs, PP_SAVE_AS_PDF)
        except Exception:
            presentation.SaveAs(pdf_abs, PP_SAVE_AS_PDF)
    finally:
        if presentation is not None:
            presentation.Close()
        if powerpoint is not None:
            powerpoint.Quit()
        # Give COM a moment to release file locks on Windows.
        time.sleep(0.4)


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


def convert_pptx_to_pdf(
    pptx: Path,
    pdf: Path,
    *,
    engine: str = "auto",
) -> str:
    """Convert pptx → pdf. Returns the engine name used."""
    engines: list[str]
    if engine == "auto":
        engines = []
        if (
            sys.platform == "win32"
            and win32com_client is not None
            and find_powerpoint() is not None
        ):
            engines.append("powerpoint")
        if find_libreoffice() is not None:
            engines.append("libreoffice")
        if not engines:
            raise RuntimeError(
                "No conversion engine available. Install Microsoft PowerPoint "
                "(with pywin32) or LibreOffice."
            )
    elif engine == "powerpoint":
        engines = ["powerpoint"]
    elif engine == "libreoffice":
        engines = ["libreoffice"]
    else:
        raise ValueError(f"Unknown engine: {engine}")

    errors: list[str] = []
    for name in engines:
        try:
            if name == "powerpoint":
                convert_with_powerpoint(pptx, pdf)
            else:
                convert_with_libreoffice(pptx, pdf)
            if not pdf.is_file() or pdf.stat().st_size < 100:
                raise RuntimeError(f"{name} produced a missing or empty PDF: {pdf}")
            return name
        except Exception as exc:  # noqa: BLE001 - try next engine
            errors.append(f"{name}: {exc}")
            if pdf.exists() and pdf.stat().st_size < 100:
                pdf.unlink(missing_ok=True)

    raise RuntimeError("PPTX → PDF failed.\n" + "\n".join(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a study companion .pptx deck to PDF "
        "(PowerPoint COM on Windows, else LibreOffice).",
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
        help="Output .pdf path (default: same directory and stem as the .pptx)",
    )
    parser.add_argument(
        "--engine",
        choices=("auto", "powerpoint", "libreoffice"),
        default="auto",
        help="Conversion engine (default: auto — PowerPoint then LibreOffice)",
    )
    args = parser.parse_args(argv)

    pptx = resolve_pptx(args.pptx, args.study, args.deck)
    pdf = resolve_output(pptx, args.output)

    try:
        used = convert_pptx_to_pdf(pptx, pdf, engine=args.engine)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Wrote {pdf} (engine={used})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

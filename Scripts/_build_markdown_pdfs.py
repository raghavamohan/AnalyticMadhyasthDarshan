#!/usr/bin/env python3
"""Build and verify Markdown-derived generated PDFs into an artifact tree."""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


from _common import BASE, configure_utf8_stdio
from _generated_pdf_inventory import GeneratedPdfSpec, generated_pdf_specs, inventory_errors
from _presentation_pipeline import repo_relative
from _publish_generated_pdfs import verify_artifacts
from _study_pdf_pipeline import regenerate_pdf, render_status
from _build_inputs import file_hash
import hashlib
import platform

def markdown_specs() -> tuple[GeneratedPdfSpec, ...]:
    return tuple(spec for spec in generated_pdf_specs() if spec.kind == "markdown")


def select_specs(
    changed_paths: tuple[str, ...],
    specs: tuple[GeneratedPdfSpec, ...] | None = None,
    *, base: str | None = None,
) -> tuple[GeneratedPdfSpec, ...]:
    from _artifact_graph import affected_outputs, document_node, print_inputs
    available = markdown_specs() if specs is None else specs
    shared = print_inputs()
    nodes = {spec.key: document_node(spec.source, shared_inputs=shared) for spec in available}
    selected = affected_outputs(set(changed_paths), base=base, nodes=nodes)
    return tuple(spec for spec in available if spec.key in selected)


def changed_paths(base: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        cwd=BASE,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"git diff {base} HEAD failed: {detail}")
    return tuple(line.strip() for line in completed.stdout.splitlines() if line.strip())


def document_link_targets(source: Path, *, root: Path = BASE) -> list[tuple[str, str]]:
    from _artifact_graph import link_inputs
    records = []
    for target, value in link_inputs(source, root).items():
        records.append((target, json.dumps(value, sort_keys=True)))
        if isinstance(value, dict) and 'status' in value:
            records.append((f"catalog:{Path(target).parent.name}", value['status'] or 'missing'))
    return sorted(records)


@lru_cache(maxsize=1)
def renderer_host_inputs() -> tuple[tuple[str, str], ...]:
    """Conservatively cover every installed face, including Unicode fallbacks.

    A regular-face fc-match probe misses bold/italic and language fallback
    changes. Hash the complete installed inventory and fontconfig rules instead
    of treating an arbitrary runner image label as a font contract.
    """
    records: list[tuple[str, str]] = []
    executable = shutil.which("fc-list")
    if executable:
        result = subprocess.run([executable, '--format=%{file}\\n'], check=True,
                                capture_output=True, text=True, encoding='utf-8')
        for filename in sorted(set(result.stdout.splitlines())):
            path = Path(filename.strip())
            if path.is_file():
                records.append((f'font:{path.as_posix()}', file_hash(path)))
        for path in sorted(Path('/etc/fonts').rglob('*')):
            if path.is_file():
                records.append((f'fontconfig:{path.as_posix()}', file_hash(path)))
    elif platform.system() == "Windows":
        directories = [Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts']
        if os.environ.get('LOCALAPPDATA'):
            directories.append(Path(os.environ['LOCALAPPDATA']) / 'Microsoft/Windows/Fonts')
        for directory in directories:
            for path in sorted(directory.rglob('*')):
                if path.is_file() and path.suffix.lower() in {'.ttf', '.ttc', '.otf', '.fon'}:
                    records.append((f'font:{path.as_posix()}', file_hash(path)))
    if not records:
        records.extend((
            ("host-image", f'{os.environ.get("ImageOS", os.name)}:{os.environ.get("ImageVersion", "local")}'),
            ("platform-version", platform.version()),
        ))
    return tuple(sorted(set(records)))


def document_fingerprint(spec: GeneratedPdfSpec) -> str:
    from _artifact_graph import document_node
    data = {"input": document_node(spec.source)['fingerprint'],
            "runtime": [sys.version, platform.system(), platform.machine(),
                        subprocess.check_output(["node", "--version"], text=True).strip(), renderer_host_inputs()]}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def build(specs: tuple[GeneratedPdfSpec, ...], output_root: Path, cache_root: Path | None = None) -> None:
    from _artifact_graph import document_node
    proof_path = output_root / 'review-build-proof.json'
    prepared = json.loads(proof_path.read_bytes()).get('artifacts', {}) if proof_path.is_file() else {}
    for spec in specs:
        target = output_root / Path(spec.key)
        target.parent.mkdir(parents=True, exist_ok=True)
        prior = prepared.get(spec.key, {})
        if prior.get('node') == document_node(spec.source) and target.is_file() and prior.get('sha256') == file_hash(target):
            print(f'Reused exact-input preparation PDF: {spec.key}', flush=True)
            continue
        fingerprint = document_fingerprint(spec) if cache_root else None
        cached = cache_root / f"{fingerprint}.pdf" if cache_root else None
        seal = cache_root / f"{fingerprint}.json" if cache_root else None
        if cached and cached.is_file() and seal.is_file():
            if json.loads(seal.read_bytes()).get("sha256") != file_hash(cached):
                raise ValueError(f"Corrupt document cache for {spec.key}")
            shutil.copy2(cached, target)
            print(f"Reused verified document inputs: {spec.key}", flush=True)
        else:
            print(f"Building {spec.key} from {repo_relative(spec.source)}", flush=True)
            regenerate_pdf(spec.source, render_status(spec.source), refresh_web=False)
            shutil.copy2(spec.output, target)
            verify_artifacts((spec,), output_root)
            if cached:
                cache_root.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, cached)
                seal.write_bytes(json.dumps({"sha256": file_hash(cached)}).encode())

    verified = verify_artifacts(specs, output_root)
    manifest = {
        "schemaVersion": 1,
        "artifacts": [
            {
                "key": artifact.spec.key,
                "kind": artifact.spec.kind,
                "sha256": artifact.sha256,
                "sourceSha256": artifact.source_sha256,
                "pages": artifact.pages,
            }
            for artifact in verified
        ],
    }
    manifest_path = output_root / "markdown-build-provenance.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Verified {len(verified)} Markdown-derived PDFs")
    print(f"Wrote {manifest_path}")


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true")
    selection.add_argument("--plan", type=Path, help="Protected publication plan selecting exact output keys")
    selection.add_argument("--changed-since", metavar="GIT_REF")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, help="Verified document cache restored only from protected-branch builds")
    args = parser.parse_args(argv)

    errors = inventory_errors()
    if errors:
        print("Generated PDF inventory errors:\n  - " + "\n  - ".join(errors), file=sys.stderr)
        return 1
    try:
        if args.plan:
            from _publication_plan import selected_specs
            specs = selected_specs(args.plan, 'markdown')
        else:
            specs = markdown_specs() if args.all else select_specs(changed_paths(args.changed_since), base=args.changed_since)
        output_root = args.output_root.expanduser().resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        if not specs:
            (output_root / "markdown-build-provenance.json").write_text(
                '{"schemaVersion":1,"artifacts":[]}\n', encoding="utf-8", newline="\n"
            )
            print("No Markdown-derived PDFs selected.")
            return 0
        build(specs, output_root, args.cache_root)
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

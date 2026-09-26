"""Record and enforce the actual runtime and complete font inventory in CI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent.parent


def font_inventory() -> list[tuple[str, str]]:
    files = set()
    if platform.system() == 'Windows':
        roots = [Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts']
        if os.environ.get('LOCALAPPDATA'):
            roots.append(Path(os.environ['LOCALAPPDATA']) / 'Microsoft/Windows/Fonts')
        for root in roots:
            files.update(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in {'.ttf', '.ttc', '.otf', '.fon'})
    else:
        executable = shutil.which('fc-list')
        if not executable:
            raise ValueError('Font inventory requires fontconfig')
        names = subprocess.check_output([executable, '--format=%{file}\\n'], text=True).splitlines()
        files.update(Path(name.strip()) for name in names if Path(name.strip()).is_file())
        files.update(p for p in Path('/etc/fonts').rglob('*') if p.is_file())
    if not files:
        raise ValueError('Renderer font inventory is empty')
    return sorted((p.as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in files)


def observe() -> dict:
    fonts = font_inventory()
    return {'schema': 1, 'platform': platform.system(), 'machine': platform.machine(),
            'python': platform.python_version(),
            'node': subprocess.check_output(['node', '--version'], text=True).strip().removeprefix('v'),
            'imageOS': os.environ.get('ImageOS', 'local'), 'imageVersion': os.environ.get('ImageVersion', 'local'),
            'fontsSha256': hashlib.sha256(json.dumps(fonts, separators=(',', ':')).encode()).hexdigest(),
            'fonts': fonts}


def enforce(family: str) -> dict:
    report = observe()
    contract = json.loads((BASE / 'Scripts/render-contract.json').read_bytes())[family]
    expected = contract['environments'][report['platform']]
    for name in ('python', 'node', 'fontsSha256'):
        if report[name] != expected[name]:
            raise ValueError(f'{family} renderer {name} drift: {report[name]} != {expected[name]}; '
                             'review the new runtime/font inventory and repeat-render before updating the contract')
    return report


def enforce_ci(family: str) -> dict | None:
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        return enforce(family)
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--enforce', choices=('markdown', 'presentations'))
    args = parser.parse_args()
    report = enforce(args.enforce) if args.enforce else observe()
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'fonts'}))

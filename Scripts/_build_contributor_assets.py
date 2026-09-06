"""Pin portal asset URLs to their content, without touching PDF inputs."""
import argparse
import hashlib
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]
PORTAL = BASE / 'Studies/portal'


def expected(path, sources):
    text = path.read_text(encoding='utf-8')
    for url, source in sources.items():
        version = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
        pattern = re.escape(url) + r'(?:\?v=[a-f0-9]+)?(?=[\'\"])'
        text, count = re.subn(pattern, url + '?v=' + version, text)
        if not count:
            raise ValueError(f'Missing asset link {url} in {path.name}')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    targets = [
        (PORTAL / 'preview.js', {'../../Assets/Mermaid/mermaid.min.js':BASE / 'Assets/Mermaid/mermaid.min.js'}),
        (PORTAL / 'preview.html', {name:PORTAL / name for name in ['preview.css','preview.js','vendor/katex.min.css','vendor/katex.min.js','vendor/markdown-it.min.js','vendor/purify.min.js']}),
        (BASE / 'Studies/submit.html', {'portal/' + name:PORTAL / name for name in ['drafts.js','contributor.js','contributor.css','preview.html']}),
    ]
    for path,sources in targets:
        text = expected(path,sources)
        if path.read_bytes() != text.encode('utf-8'):
            if args.check: raise SystemExit(f'Stale portal assets in {path.relative_to(BASE)}. Run python Scripts/_build_contributor_assets.py.')
            path.write_text(text,encoding='utf-8',newline='\n')
    print('Contributor asset versions verified.' if args.check else 'Contributor asset versions synchronized.')


if __name__ == '__main__':
    main()

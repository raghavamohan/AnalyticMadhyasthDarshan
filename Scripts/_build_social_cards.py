"""Render Open Graph share cards for the site and every catalogued study.

Large study icons and short, high-contrast titles stay recognizable in mobile
link previews. A brief catalog description supports the title in smaller type.
Icons come from the approved website theme kit.

Rendered through headless Chrome (Scripts/_html_to_png.js) rather than a
Pillow-drawn bitmap so the type matches the site exactly and no font has to be
vendored into the repo. Generated PNGs are committed, so a maintainer only reruns
this when a title, description, category, status or icon changes:

    python Scripts/_build_social_cards.py            # all cards
    python Scripts/_build_social_cards.py --slug X   # one study
    python Scripts/_build_social_cards.py --check    # report what is missing
"""

from __future__ import annotations

import argparse
import html
import json
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

from _common import BASE, STUDIES
from _study_catalog import (
    StudyTable,
    load_catalog_rows,
)

SCRIPTS = Path(__file__).resolve().parent
HTML_TO_PNG = SCRIPTS / "_html_to_png.js"
SOCIAL_DIR = BASE / "Assets" / "Social"
CARD_WIDTH = 1200
CARD_HEIGHT = 630
DEFAULT_CARD = "og-default.png"

_STATUS_LABELS = {
    "released": "Released",
    "draft": "Draft",
    "ongoing": "In progress",
}

# The site's own tokens, so a card set beside the page it links to looks related.
_CARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: {width}px; height: {height}px; }}
  body {{
    padding: 48px 64px;
    background: #f7f4ef;
    color: #1a1612;
    font-family: 'Segoe UI', system-ui, sans-serif;
    border-top: 10px solid #1a5276;
    display: flex;
    flex-direction: column;
  }}
  .eyebrow {{
    font-size: 26px;
    font-weight: 600;
    color: #1a5276;
    letter-spacing: .025em;
  }}
  .main {{ display: flex; align-items: center; gap: 48px; flex: 1; min-height: 0; }}
  .icon {{
    width: 224px; height: 224px; flex: 0 0 224px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 48px; background: #eee8df;
  }}
  .icon svg {{ width: 168px; height: 168px; display: block; }}
  .copy {{ flex: 1; min-width: 0; }}
  .title {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: {title_size}px;
    line-height: 1.13;
    font-weight: 700;
    text-wrap: balance;
    overflow-wrap: anywhere;
  }}
  .blurb {{
    margin-top: 20px;
    font-size: 26px;
    line-height: 1.4;
    color: #5c5348;
  }}
  .foot {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 24px; padding-top: 24px; border-top: 2px solid #d9d1c5;
    font-size: 24px; color: #5c5348;
  }}
  .cats {{ flex: 1; min-width: 0; }}
  .status {{
    padding: 8px 20px; border-radius: 999px; font-weight: 600;
    background: #e4f0e0; color: #2f6b28; white-space: nowrap;
  }}
  .status.draft {{ background: #fef3c7; color: #92400e; }}
  .status.progress {{ background: #f5ebe0; color: #8b5e34; }}
</style>
</head>
<body>
<p class="eyebrow">{eyebrow}</p>
<div class="main">
  <div class="icon" aria-hidden="true">{icon}</div>
  <div class="copy">
    <h1 class="title">{title}</h1>
    {blurb}
  </div>
</div>
<div class="foot">
  <span class="cats">{cats}</span>
  {status}
</div>
</body>
</html>
"""


def _title_size(title: str) -> int:
    """Step the display size down so long titles still fit two or three lines."""
    length = len(title)
    if length <= 34:
        return 74
    if length <= 52:
        return 64
    if length <= 78:
        return 54
    return 46


def _truncate(text: str, limit: int) -> str:
    """Shorten to `limit`, breaking on a word so the card never cuts mid-word."""
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= limit:
        return cleaned
    head = cleaned[:limit]
    space = head.rfind(" ")
    if space > limit // 2:
        head = head[:space]
    return head.rstrip(" ,;:.—-") + "…"


def render_card(
    output: Path,
    *,
    eyebrow: str,
    title: str,
    blurb: str | None,
    status: str | None,
    cats: str,
    icon: str = "coexistence",
) -> None:
    status_html = ""
    if status:
        label = _STATUS_LABELS.get(status, status.title())
        css = {"draft": " draft", "ongoing": " progress"}.get(status, "")
        status_html = f'<span class="status{css}">{html.escape(label)}</span>'
    from _theme_icons import topic_icon_html

    page = _CARD_TEMPLATE.format(
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        title_size=_title_size(title),
        eyebrow=html.escape(eyebrow),
        title=html.escape(title),
        blurb=f'<p class="blurb">{html.escape(_truncate(blurb, 120))}</p>' if blurb else '',
        icon=topic_icon_html(icon),
        status=status_html,
        cats=html.escape(cats),
    )
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "card.html"
        # lf-exempt: temp file handed straight to node, never tracked
        source.write_text(page, encoding="utf-8")
        result = subprocess.run(
            [
                "node",
                str(HTML_TO_PNG),
                str(source),
                str(output),
                str(CARD_WIDTH),
                str(CARD_HEIGHT),
            ],
            cwd=SCRIPTS,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()
        raise RuntimeError(f"Card render failed for {output.name}: {detail}")


def _catalog_rows() -> list:
    rows = []
    for table in (StudyTable.TOPICAL, StudyTable.FORMAL, StudyTable.APPLIED):
        try:
            rows.extend(load_catalog_rows(table))
        except (OSError, ValueError):
            continue
    return rows


def card_path(slug: str) -> Path:
    return SOCIAL_DIR / f"{slug}.png"


CARD_MANIFEST = SCRIPTS / 'social-cards.json'


def card_contracts() -> dict:
    from _theme_icons import study_icon_name

    cards = {DEFAULT_CARD: dict(eyebrow="Analytic Madhyasth Darshan", title="Studies of Madhyasth Darshan",
              blurb="Comparative studies of Madhyasth Darshan read against the sciences, Advaita Vedanta, and modern philosophy.",
              status=None, cats="Open and independent", icon="coexistence")}
    for row in _catalog_rows():
        cards[card_path(row.slug).name] = dict(eyebrow="Analytic Madhyasth Darshan", title=row.title,
            icon=study_icon_name(row.slug) or "coexistence",
            blurb=row.description, status=row.status.value if row.status else None,
            cats=_truncate(str(row.category or '').strip() or 'Madhyasth Darshan', 60))
    return cards


def card_fingerprint(fields: dict) -> str:
    from _build_inputs import file_hash
    from _theme_icons import IDENTITY_NAMES
    dependencies = {name: file_hash(SCRIPTS / name) for name in
                    ('_build_social_cards.py', '_html_to_png.js', '_chrome.js', 'package.json', 'package-lock.json')}
    dependencies['_theme_icons.py'] = file_hash(SCRIPTS / '_theme_icons.py')
    icon = fields.get('icon', 'coexistence')
    variant = 'compact' if icon in IDENTITY_NAMES else 'light'
    dependencies['icon'] = file_hash(BASE / 'Assets' / 'Theme' / 'icons' / f'{icon}-{variant}.svg')
    return hashlib.sha256(json.dumps({'fields': fields, 'renderer': dependencies}, sort_keys=True).encode()).hexdigest()


def verify_social_cards() -> list[str]:
    from _build_inputs import file_hash
    records = json.loads(CARD_MANIFEST.read_bytes()).get('cards', {}) if CARD_MANIFEST.is_file() else {}
    errors = []
    for name, fields in card_contracts().items():
        path, record = SOCIAL_DIR / name, records.get(name, {})
        if (not path.is_file() or record.get('fingerprint') != card_fingerprint(fields)
                or record.get('sha256') != file_hash(path)):
            errors.append(f'Stale social card: {name}; run python Scripts/_build_social_cards.py')
    return errors


def build(slug_filter: str | None = None, *, check_only: bool = False) -> int:
    from _build_inputs import file_hash
    if check_only:
        errors = verify_social_cards()
        print('\n'.join(errors) if errors else 'Social card inputs and output checksums are current.')
        return int(bool(errors))
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    records = json.loads(CARD_MANIFEST.read_bytes()).get('cards', {}) if CARD_MANIFEST.is_file() else {}
    contracts = card_contracts()
    built = 0
    for name, fields in contracts.items():
        if slug_filter and name != slug_filter + '.png':
            continue
        target = SOCIAL_DIR / name
        key = card_fingerprint(fields)
        old = records.get(name, {})
        if old.get('fingerprint') == key and target.is_file() and old.get('sha256') == file_hash(target):
            continue
        render_card(target, **fields)
        records[name] = {'fingerprint': key, 'sha256': file_hash(target)}
        built += 1
        print(f'  {name}', flush=True)
    # Remove only previously registered generator-owned cards after retirement.
    for name in set(records) - set(contracts):
        target = SOCIAL_DIR / name
        if target.is_symlink() or target.resolve().parent != SOCIAL_DIR.resolve():
            raise ValueError(f'Unsafe retired social card: {name}')
        target.unlink(missing_ok=True)
        del records[name]
    CARD_MANIFEST.write_bytes((json.dumps({'schema': 1, 'cards': records}, sort_keys=True, indent=2) + '\n').encode())
    print(f'Rendered {built} changed social cards.')
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", help="Render only this study's card")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify source fingerprints and generated PNG checksums without rendering",
    )
    args = parser.parse_args()
    sys.exit(build(args.slug, check_only=args.check))


if __name__ == "__main__":
    main()

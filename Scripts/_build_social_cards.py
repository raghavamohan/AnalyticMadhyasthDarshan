"""Render Open Graph share cards for the site and every catalogued study.

Nothing on the site declared an og:image, and twitter:card was "summary", so a
link shared into Slack, WhatsApp, X or LinkedIn rendered as a bare text row. The
cards are typographic rather than pictorial: the study title in the site's
Georgia, its categories and status in Segoe UI, on the site's paper ground.

Rendered through headless Chrome (Scripts/_html_to_png.js) rather than a
Pillow-drawn bitmap so the type matches the site exactly and no font has to be
vendored into the repo. Generated PNGs are committed, so a maintainer only reruns
this when a title, category or status changes:

    python Scripts/_build_social_cards.py            # all cards
    python Scripts/_build_social_cards.py --slug X   # one study
    python Scripts/_build_social_cards.py --check    # report what is missing
"""

from __future__ import annotations

import argparse
import html
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
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 64px 72px 58px;
    background: #f7f4ef;
    /* A single warm wash off the top-left, so the card is not a flat slab. */
    background-image: radial-gradient(120% 90% at 0% 0%, #fffdf9 0%, #f7f4ef 55%);
    color: #2a241c;
    font-family: 'Segoe UI', system-ui, sans-serif;
  }}
  .rule {{
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 10px;
    background: #1a5276;
  }}
  .eyebrow {{
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #8b5e34;
  }}
  .title {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: {title_size}px;
    line-height: 1.14;
    font-weight: 700;
    color: #1a1612;
    text-wrap: balance;
    max-width: 15.5em;
  }}
  .blurb {{
    font-size: 24px;
    line-height: 1.45;
    color: #5c5348;
    max-width: 40ch;
    margin-top: 22px;
  }}
  .foot {{
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
    font-size: 21px;
  }}
  .status {{
    padding: 5px 16px;
    border-radius: 999px;
    font-weight: 600;
    background: #e4f0e0;
    color: #2f6b28;
  }}
  .status.draft {{ background: #fef3c7; color: #92400e; }}
  .status.progress {{ background: #f5ebe0; color: #8b5e34; }}
  .cats {{ color: #5c5348; }}
  .site {{
    margin-left: auto;
    font-weight: 600;
    color: #1a5276;
  }}
</style>
</head>
<body>
<div class="rule"></div>
<div>
  <p class="eyebrow">{eyebrow}</p>
  <h1 class="title">{title}</h1>
  {blurb}
</div>
<div class="foot">
  {status}
  <span class="cats">{cats}</span>
  <span class="site">analyticmadhyasthdarshan.org</span>
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
) -> None:
    status_html = ""
    if status:
        label = _STATUS_LABELS.get(status, status.title())
        css = {"draft": " draft", "ongoing": " progress"}.get(status, "")
        status_html = f'<span class="status{css}">{html.escape(label)}</span>'
    blurb_html = ""
    if blurb:
        blurb_html = f'<p class="blurb">{html.escape(_truncate(blurb, 150))}</p>'

    page = _CARD_TEMPLATE.format(
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        title_size=_title_size(title),
        eyebrow=html.escape(eyebrow),
        title=html.escape(title),
        blurb=blurb_html,
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


def build(slug_filter: str | None = None, *, check_only: bool = False) -> int:
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []
    built = 0

    if slug_filter is None:
        target = SOCIAL_DIR / DEFAULT_CARD
        if check_only:
            if not target.is_file():
                missing.append(DEFAULT_CARD)
        else:
            render_card(
                target,
                eyebrow="Analytic Madhyasth Darshan",
                title="Studies of Madhyasth Darshan",
                blurb=(
                    "Comparative studies of Madhyasth Darshan read against the sciences, "
                    "Advaita Vedanta, and modern philosophy."
                ),
                status=None,
                cats="Open and independent",
            )
            built += 1
            print(f"  {DEFAULT_CARD}")

    for row in _catalog_rows():
        if slug_filter and row.slug != slug_filter:
            continue
        target = card_path(row.slug)
        if check_only:
            if not target.is_file():
                missing.append(target.name)
            continue
        # StudyRow.category is a single string that may itself list several
        # categories; it is the display value the catalog card already uses.
        cats = str(row.category or "").strip() or "Madhyasth Darshan"
        render_card(
            target,
            eyebrow="A study in the collection",
            title=row.title,
            blurb=row.description,
            status=row.status.value if row.status else None,
            cats=_truncate(cats, 60),
        )
        built += 1
        print(f"  {target.name}")

    if check_only:
        if missing:
            print(f"Missing {len(missing)} social card(s):")
            for name in missing:
                print(f"  {name}")
            return 1
        print("All social cards present.")
        return 0

    print(f"Rendered {built} social card(s) into {SOCIAL_DIR.relative_to(BASE).as_posix()}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", help="Render only this study's card")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report cards that are missing without rendering anything",
    )
    args = parser.parse_args()
    sys.exit(build(args.slug, check_only=args.check))


if __name__ == "__main__":
    main()

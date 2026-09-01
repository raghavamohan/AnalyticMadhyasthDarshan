#!/usr/bin/env python3
"""Write Studies/index.html landing page shell and external catalog JSON files."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _build_discussion_pages import ASSET_VERSION as DISCUSS_ASSET_VERSION  # noqa: E402
from _common import BASE, STUDIES, favicon_link_tags, write_text_lf  # noqa: E402
from _study_catalog import (  # noqa: E402
    CATALOG_TABLES,
    STUDY_FEEDBACK_TEMPLATE_PATH,
    StudyRow,
    StudyStatus,
    StudyTable,
    catalog_json_path,
    catalog_json_payload,
    catalog_markers,
    load_catalog_rows,
    parse_catalog_json,
    parse_catalog_json_file,
    row_to_catalog_entry,
    split_categories,
    write_studies_catalog,
)

CATALOG_SHELL_PLACEHOLDER = "<!-- @catalog-data@ -->"
CATALOG_BOOTSTRAP_PLACEHOLDER = "<!-- @catalog-bootstrap@ -->"
CATALOG_BUILD_ID_PLACEHOLDER = "@catalog-build-id@"
DISCUSS_ASSET_VERSION_PLACEHOLDER = "@discuss-asset-version@"
HERO_SCOPE_PLACEHOLDER = "<!-- @hero-scope@ -->"
FAVICON_LINKS_PLACEHOLDER = "<!-- @favicon-links@ -->"
START_HERE_STATUS_PLACEHOLDER = "@start-here-status@"
PILL_STATUS_SUB_RE = r'(<span class="path-status )[a-z-]+("[^>]*data-study-status[^>]*>)[^<]*(</span>)'
PILL_STATUS_SUB_REPL = (
    "\1" + START_HERE_STATUS_PLACEHOLDER + "\2" + START_HERE_STATUS_PLACEHOLDER + "\3"
)

# Mirrors START_HERE_STATUS_WORDS in the shipped syncStartHere() script. The two
# must agree: the builder writes these words into the static markup and the page
# recomputes them from the catalog on load, so a mismatch would make the pill
# visibly change on first paint.
START_HERE_STATUS_WORDS = {"released": "Released", "draft": "Draft", "planned": "In progress"}

# Pairs a Start-here entry with its own status pill. The inner guard refuses to
# cross into the next data-study-slug element, so a study whose pill is missing
# cannot silently capture the following study's pill.
START_HERE_PILL_RE = re.compile(
    r'(data-study-slug="([^"]+)"(?:(?!data-study-slug=).)*?<span class="path-status )'
    r'([a-z-]+)("[^>]*data-study-status[^>]*>)([^<]*)(</span>)',
    re.DOTALL,
)

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Studies of Madhyasth Darshan</title>
<meta name="description" content="An open comparative study of Madhyasth Darshan, following a path from the human question through existence, knowledge, value, lived participation, and formal synthesis."/>
<meta name="color-scheme" content="light dark"/>
<link rel="canonical" href="https://analyticmadhyasthdarshan.org/Studies/index.html"/>
<!-- @favicon-links@ -->
<meta property="og:type" content="website"/>
<meta property="og:site_name" content="AnalyticMadhyasthDarshan.org"/>
<meta property="og:title" content="Studies of Madhyasth Darshan"/>
<meta property="og:description" content="An open comparative study of Madhyasth Darshan, following a path through existence, knowledge, value, lived participation, and formal synthesis."/>
<meta property="og:url" content="https://analyticmadhyasthdarshan.org/Studies/index.html"/>
<meta property="og:image" content="https://analyticmadhyasthdarshan.org/Assets/Social/og-default.png"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta property="og:image:alt" content="Studies of Madhyasth Darshan"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="Studies of Madhyasth Darshan"/>
<meta name="twitter:description" content="An open comparative study of Madhyasth Darshan, following a path through existence, knowledge, value, lived participation, and formal synthesis."/>
<meta name="twitter:image" content="https://analyticmadhyasthdarshan.org/Assets/Social/og-default.png"/>
<script src="/webmcp.js" defer></script>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"CollectionPage","name":"Studies of Madhyasth Darshan","description":"An open comparative study of Madhyasth Darshan, following a path from the human question through existence, knowledge, value, lived participation, and formal synthesis.","url":"https://analyticmadhyasthdarshan.org/Studies/index.html","isPartOf":{"@type":"WebSite","name":"AnalyticMadhyasthDarshan.org","url":"https://analyticmadhyasthdarshan.org/"},"image":"https://analyticmadhyasthdarshan.org/Assets/Social/og-default.png","license":"https://creativecommons.org/licenses/by/4.0/"}
</script>
<script>
(function(){try{var t=localStorage.getItem("amd-theme");if(t!=="light"&&t!=="dark"){t=window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";}document.documentElement.setAttribute("data-theme",t);}catch(e){document.documentElement.setAttribute("data-theme","light");}})();
</script>
<style>
  :root {
    --bg: #f7f4ef;
    --surface: #ffffff;
    --text: #2a241c;
    --text-muted: #5c5348;
    --accent: #1a5276;
    --accent-soft: #e8f1f6;
    --accent-hover: #13405c;
    --warm: #8b5e34;
    --warm-soft: #f5ebe0;
    --border: #e3dcd2;
    --shadow: 0 2px 12px rgba(42, 36, 28, 0.06);
    --radius: 10px;
    --sans: 'Segoe UI', system-ui, sans-serif;
  }

  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }

  body {
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 16px;
    line-height: 1.6;
    color: var(--text);
    background: var(--bg);
    margin: 0;
    padding: 0;
  }

  a {
    color: var(--accent);
    text-decoration-thickness: 1px;
    text-underline-offset: 2px;
    transition: color 0.15s ease;
  }
  a:hover { color: var(--accent-hover); }

  .page { max-width: 1060px; margin: 0 auto; padding: 28px 20px 56px; }

  .hero {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 0;
    margin-bottom: 0;
  }

  .eyebrow {
    margin: 0 0 12px;
    font-family: var(--sans);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--warm);
  }

  h1 {
    font-size: 38px;
    font-weight: normal;
    line-height: 1.15;
    margin: 0 0 14px;
    color: #1a1612;
    border: none;
    padding: 0;
  }

  .lead {
    font-size: 19px;
    line-height: 1.5;
    color: var(--text-muted);
    margin: 0 0 6px;
  }

  .dialogue-row {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 3px 12px;
    margin: 0 0 6px;
  }
  .dialogue-label {
    margin: 0;
    font-family: var(--sans);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-muted);
  }
  .dialogue {
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0;
    font-family: var(--sans);
    font-size: 16px;
  }
  .dialogue li { display: flex; align-items: center; }
  .dialogue li:not(:last-child)::after {
    content: "";
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--warm);
    opacity: 0.5;
    margin: 0 12px;
  }
  .dialogue span { color: var(--text); font-weight: 600; }

  .scope {
    font-family: var(--sans);
    font-size: 16px;
    color: var(--text-muted);
    margin: 0 0 20px;
  }
  .scope strong { color: var(--text); font-weight: 600; }
  #hero-scope { margin-bottom: 6px; }
  .hero .scope:last-child { margin-bottom: 0; }

  .hero-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 14px;
    margin: 0 0 20px;
    font-family: var(--sans);
  }

  .btn-primary {
    display: inline-block;
    font-family: var(--sans);
    font-size: 15px;
    font-weight: 600;
    color: #fff;
    background: var(--accent);
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    text-decoration: none;
    transition: background 0.15s ease;
  }
  .btn-primary:hover { background: var(--accent-hover); color: #fff; }

  .btn-secondary {
    display: inline-block;
    font-family: var(--sans);
    font-size: 15px;
    font-weight: 600;
    color: var(--accent);
    background: var(--accent-soft);
    border: 1px solid #a5c4d9;
    border-radius: 8px;
    padding: 9px 18px;
    text-decoration: none;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .btn-secondary:hover { background: #d4e6f2; color: var(--accent-hover); }

  .page-nav {
    border: none;
    border-radius: 0;
    box-shadow: none;
    padding: 0;
    margin-top: 22px;
    margin-bottom: 22px;
    position: -webkit-sticky;
    position: sticky;
    top: 0;
    z-index: 20;
    -webkit-backdrop-filter: blur(8px);
    backdrop-filter: blur(8px);
    background: rgba(247, 244, 239, 0.92);
  }

  .page-nav-anchor {
    display: none;
    height: 0;
  }

  .page-nav-inner {
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    gap: 10px 14px;
  }

  .page-nav-tools {
    display: flex;
    flex: 0 0 auto;
    align-items: center;
    gap: 8px;
    margin-left: auto;
  }

  .page-nav-submit {
    font-family: var(--sans);
    font-size: 13px;
    font-weight: 600;
    color: var(--accent);
    text-decoration: none;
    white-space: nowrap;
    padding: 5px 12px;
    border: 1px solid transparent;
    border-radius: 999px;
  }
  .page-nav-submit:hover {
    background: var(--accent-soft);
    border-color: #a5c4d9;
  }

  .page-nav-label {
    margin: 0;
    flex: 0 0 auto;
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .toc {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin: 0;
    padding: 0;
    list-style: none;
    flex: 1 1 auto;
    min-width: 0;
  }

  .toc li { flex: 0 0 auto; }

  .toc a {
    display: inline-block;
    font-family: var(--sans);
    font-size: 13px;
    padding: 6px 13px;
    background: var(--warm-soft);
    border: 1px solid #e0d0be;
    border-radius: 999px;
    color: var(--warm);
    text-decoration: none;
    white-space: nowrap;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  }
  .toc a:hover { background: #ede0d0; border-color: #cdb89e; color: #6b4520; }
  .toc a.active {
    background: var(--accent-soft);
    border-color: #a5c4d9;
    color: var(--accent);
    font-weight: 600;
  }

  main { width: 100%; min-width: 0; }

  .skip-link {
    position: absolute;
    left: -9999px;
    top: 0;
    z-index: 100;
    padding: 8px 14px;
    background: var(--accent);
    color: #fff;
    font-family: var(--sans);
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;
    border-radius: 0 0 8px 0;
  }
  .skip-link:focus {
    left: 0;
    outline: 2px solid var(--accent-hover);
    outline-offset: 2px;
  }

  .section { scroll-margin-top: 64px; margin-bottom: 22px; }
  .section.is-targeted {
    animation: section-target-flash 1.6s ease-out forwards;
  }
  .catalog-group.is-targeted {
    animation: section-target-flash 1.6s ease-out forwards;
  }

  @keyframes section-target-flash {
    0% {
      background: #e8f4fa;
      border-radius: var(--radius);
      box-shadow: 0 0 0 3px rgba(26, 82, 118, 0.22);
    }
    100% { background: transparent; box-shadow: none; }
  }

  h2 {
    font-size: 26px;
    font-weight: 600;
    margin: 0 0 6px;
    color: #1a1612;
  }
  .section > h2 {
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 14px;
  }

  h3 {
    font-size: 20px;
    font-weight: 600;
    color: #1a1612;
    margin: 20px 0 8px;
  }
  .section-card h3:first-child { margin-top: 0; }

  p { margin: 9px 0; text-align: left; }
  .section-intro { color: var(--text-muted); font-size: 16px; margin: 0 0 14px; }

  .section-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: 24px 28px 22px;
  }
  .section-card ul, .section-card ol { margin: 9px 0 12px 20px; padding: 0; }
  .section-card li { margin: 5px 0; }
  .section-card li::marker { color: var(--warm); }

  .browse-heading {
    scroll-margin-top: 64px;
    margin: 26px 0 12px;
  }
  .browse-heading h2 {
    margin: 0 0 5px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }
  .browse-heading p {
    margin: 0;
    color: var(--text-muted);
    font-size: 15px;
  }
  .toolbar {
    display: flex; flex-wrap: wrap; align-items: flex-end; gap: 10px 12px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); box-shadow: var(--shadow);
    padding: 12px 14px; margin: 0 0 4px;
  }
  .search { position: relative; flex: 1 1 240px; min-width: 180px; }
  .search svg {
    position: absolute; left: 11px; top: 50%; transform: translateY(-50%);
    width: 15px; height: 15px; color: var(--text-muted); pointer-events: none;
  }
  .search input {
    width: 100%; font-family: var(--sans); font-size: 14px; color: var(--text);
    padding: 9px 12px 9px 32px; border: 1px solid var(--border);
    border-radius: 8px; background: #fdfcfa;
  }
  .search input::placeholder { color: #9a8f80; }
  .search input { padding-right: 30px; }
  .search-clear {
    position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
    width: 22px; height: 22px; display: none; align-items: center; justify-content: center;
    border: none; background: transparent; color: var(--text-muted);
    font-size: 16px; line-height: 1; cursor: pointer; border-radius: 50%; padding: 0;
  }
  .search-clear:hover { color: var(--accent); background: var(--accent-soft); }
  .search.has-value .search-clear { display: inline-flex; }
  .theme-toggle {
    flex: 0 0 auto;
    font-family: var(--sans); font-size: 13px; font-weight: 600;
    color: var(--text-muted); background: #fdfcfa; border: 1px solid var(--border);
    border-radius: 999px; padding: 5px 12px; cursor: pointer; white-space: nowrap;
    display: inline-flex; align-items: center; gap: 6px;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  }
  .theme-toggle:hover { color: var(--accent); border-color: #a5c4d9; }
  .theme-toggle .theme-toggle-icon { font-size: 14px; line-height: 1; }
  .seg {
    display: inline-flex; border: 1px solid var(--border); border-radius: 8px;
    overflow: hidden; background: #fdfcfa;
  }
  .seg-group {
    display: flex; flex-direction: column; gap: 4px; min-width: 0;
  }
  .filter-notice {
    font-family: var(--sans); font-size: 13px; color: var(--text-muted);
    margin: 0 0 8px; padding: 0 2px;
  }
  .filter-notice-action {
    font-family: var(--sans); font-size: 13px; font-weight: 600;
    color: var(--accent); background: none; border: none; padding: 0;
    cursor: pointer; text-decoration: underline; text-underline-offset: 2px;
  }
  .filter-notice-action:hover { color: var(--accent-hover); }
  .filter-notice-action:focus-visible {
    outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 3px;
  }
  .seg-label {
    font-family: var(--sans); font-size: 11px; font-weight: 600;
    letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-muted);
  }
  .seg button {
    font-family: var(--sans); font-size: 13px; color: var(--text-muted);
    background: transparent; border: none; padding: 8px 13px; cursor: pointer;
    border-right: 1px solid var(--border);
    transition: background 0.15s ease, color 0.15s ease;
  }
  .seg button:last-child { border-right: none; }
  .seg button:hover { background: #f4efe8; }
  .seg button[aria-pressed="true"] {
    background: var(--accent-soft); color: var(--accent); font-weight: 600;
  }
  .field {
    font-family: var(--sans); font-size: 13px; color: var(--text);
    padding: 8px 30px 8px 11px; border: 1px solid var(--border); border-radius: 8px;
    background-color: #fdfcfa;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%235c5348' stroke-width='2'><path d='M6 9l6 6 6-6'/></svg>");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 12px 12px;
    -webkit-appearance: none; appearance: none; cursor: pointer;
  }
  .field::-ms-expand { display: none; }

  .btn-reset-filters {
    font-family: var(--sans); font-size: 13px; font-weight: 600;
    color: var(--accent); background: #fdfcfa; border: 1px solid #c5d9e6;
    border-radius: 8px; padding: 8px 14px; cursor: pointer; white-space: nowrap;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  }
  .btn-reset-filters:hover:not(:disabled) { background: var(--accent-soft); border-color: #a5c4d9; }
  .btn-reset-filters:disabled {
    color: #9a8f80; border-color: var(--border); cursor: default; opacity: 0.65;
  }

  .cat-list-panel {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); box-shadow: var(--shadow);
    padding: 10px 14px 12px; margin: 0 0 8px;
  }
  .cat-list-label {
    display: block; font-family: var(--sans); font-size: 11px; font-weight: 600;
    letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-muted);
    margin: 0 0 8px;
  }
  .cat-list {
    display: flex; flex-wrap: wrap; gap: 6px; margin: 0; padding: 0; list-style: none;
  }
  .cat-filter {
    font-family: var(--sans); font-size: 12px; color: var(--warm);
    background: var(--warm-soft); border: 1px solid #e7d8c6; border-radius: 999px;
    padding: 4px 11px; cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  }
  .cat-filter:hover { background: #ede0d0; border-color: #cdb89e; }
  .cat-filter.is-active {
    color: var(--accent); background: var(--accent-soft);
    border-color: #a5c4d9; font-weight: 600;
  }
  .cat-filter .cat-count {
    font-size: 10px; font-weight: 600; opacity: 0.75; margin-left: 2px;
  }

  .cat-group-label {
    font-family: var(--sans);
    font-size: 12px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
    color: var(--text-muted); margin: 20px 0 0;
    display: flex; align-items: baseline; justify-content: space-between; gap: 10px;
  }
  .cat-group-label .count { font-weight: 400; text-transform: none; letter-spacing: 0; }

  .grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
    gap: 16px; margin: 12px 0 4px; padding: 0; list-style: none;
  }

  .card {
    position: relative; display: flex; flex-direction: column;
    background: var(--surface); border: 1px solid var(--border);
    border-left: 4px solid var(--warm); border-radius: var(--radius);
    box-shadow: var(--shadow); padding: 16px 18px 14px;
    scroll-margin-top: 64px;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .card.is-targeted {
    animation: section-target-flash 1.6s ease-out forwards;
  }
  .card.is-available { border-left-color: var(--accent); }
  .card.is-released { border-left-color: #2d6a4f; }
  .card.is-draft { border-left-color: #b45309; }
  .card.is-planned {
    opacity: 0.72;
  }
  .card.is-available:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(42, 36, 28, 0.10);
  }
  .card-title { font-size: 17px; line-height: 1.3; margin: 0 0 9px; }
  .card-title a {
    color: var(--accent); text-decoration: none;
    border-bottom: 1px solid rgba(26, 82, 118, 0.32);
  }
  .card-title a:hover { color: var(--accent-hover); border-bottom-color: var(--accent); }
  .card.is-planned .card-title { color: var(--text-muted); font-style: italic; }
  .card.is-planned .card-title a {
    color: var(--text-muted);
    font-style: italic;
    border-bottom-color: rgba(92, 83, 72, 0.35);
  }
  .card.is-planned .card-title a:hover { color: var(--accent); border-bottom-color: var(--accent); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 10px; }
  .chip {
    font-family: var(--sans); font-size: 11px; color: var(--warm);
    background: var(--warm-soft); border: 1px solid #e7d8c6; border-radius: 999px;
    padding: 2px 9px; cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  .chip:hover { background: #ede0d0; border-color: #cdb89e; }
  .card-desc { font-size: 14px; line-height: 1.5; color: var(--text); margin: 0 0 14px; flex: 1 1 auto; }
  .card.is-planned .card-desc { color: var(--text-muted); }
  .card-foot {
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    font-family: var(--sans); font-size: 12px; color: var(--text-muted);
    border-top: 1px solid #efe9e1; padding-top: 11px;
  }
  .badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-family: var(--sans); font-size: 11px; font-weight: 600;
    letter-spacing: 0.02em; border-radius: 999px; padding: 3px 10px;
  }
  .badge-dot { width: 6px; height: 6px; border-radius: 50%; }
  .badge.released { color: #1b4332; background: #d8f3dc; border: 1px solid #95d5b2; }
  .badge.released .badge-dot { background: #2d6a4f; }
  .badge.draft { color: #92400e; background: #fef3c7; border: 1px solid #fcd34d; }
  .badge.draft .badge-dot { background: #d97706; }
  .badge.planned { color: var(--warm); background: var(--warm-soft); border: 1px solid #e0d0be; }
  .badge.planned .badge-dot { background: var(--warm); }

  .start-here {
    margin: 0 0 20px;
    padding: 24px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    container-type: inline-size;
    container-name: start-path;
  }
  .start-here-kicker {
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--warm);
    margin: 0 0 5px;
  }
  .start-here h2 {
    font-family: inherit;
    font-size: 23px;
    font-weight: 600;
    color: var(--accent);
    margin: 0 0 8px;
    border: none;
    padding: 0;
    letter-spacing: normal;
    text-transform: none;
  }
  .start-here-intro {
    font-size: 15px;
    line-height: 1.55;
    color: var(--text-muted);
    max-width: 920px;
    margin: 0 0 20px;
  }
  .study-path {
    display: grid;
    grid-template-columns: 1fr;
    grid-template-areas:
      "rail"
      "panel"
      "alongside"
      "invite";
    gap: 0;
    margin: 0;
    padding: 0;
  }
  .path-rail {
    position: relative;
    display: flex;
    flex-wrap: nowrap;
    align-items: flex-start;
    gap: 0;
    grid-area: rail;
    margin: 0 0 7px;
  }
  .path-rail-step {
    position: relative;
    display: flex;
    flex: 0 1 auto;
    min-width: 0;
  }
  .path-rail-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    margin: 0;
    padding: 3px 9px 0;
    cursor: pointer;
    font-family: var(--sans);
  }
  .path-dot {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 32px;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    color: var(--text-muted);
    background: var(--surface);
    border: 1.5px solid var(--border);
    font-family: var(--sans);
    font-size: 13px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
  }
  .path-stage-name {
    font-family: var(--sans);
    font-size: 13.5px;
    font-weight: 500;
    line-height: 1.25;
    color: var(--text-muted);
    text-align: center;
    text-wrap: balance;
  }
  .path-rail-item:hover .path-dot {
    border-color: var(--accent);
    color: var(--accent);
  }
  .path-rail-item:hover .path-stage-name {
    color: var(--text);
  }
  .path-rail-step:has(.path-radio:checked) .path-dot {
    color: #fff;
    background: var(--accent);
    border-color: var(--accent);
    box-shadow: 0 0 0 4px var(--accent-soft);
  }
  .path-rail-step:has(.path-radio:checked) .path-stage-name {
    color: var(--accent);
    font-weight: 700;
  }
  .path-radio.sr-only:focus-visible + .path-rail-item .path-dot {
    outline: 2px solid var(--accent);
    outline-offset: 3px;
  }
  .path-because {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    align-self: flex-start;
    flex: 1 1 0;
    min-width: 0;
    min-height: 38px;
    font-family: var(--sans);
    font-size: 10.5px;
    line-height: 1.25;
    color: var(--text-muted);
    text-align: center;
  }
  .path-because::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    top: 18px;
    height: 2px;
    background: var(--border);
  }
  .path-because span {
    position: relative;
    max-width: 100%;
    padding: 0 8px;
    background: var(--surface);
  }
  .path-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 26px;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    color: #fff;
    background: var(--accent);
    font-family: var(--sans);
    font-size: 12px;
    font-weight: 700;
  }
  .path-domain {
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
  }
  .path-alongside {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 14px;
    grid-area: alongside;
    margin: 16px 0 0;
    padding: 13px 0 0;
    background: transparent;
    border: 0;
    border-top: 1px solid var(--border);
    border-radius: 0;
  }
  .path-alongside-label {
    flex: 0 0 auto;
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--warm);
  }
  .path-alongside-studies {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    flex: 1 1 240px;
  }
  .parallel-study {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px 8px;
    padding: 6px 10px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-family: var(--sans);
    font-size: 12px;
  }
  .parallel-study a { font-weight: 700; }
  .parallel-study .path-status { margin: 0; }
  .parallel-study .path-slides { margin: 0; }
  .path-invite {
    grid-area: invite;
    font-size: 14px;
    line-height: 1.55;
    color: var(--text-muted);
    margin: 13px 0 0;
    padding: 13px 0 0;
    border-top: 1px solid var(--border);
  }
  .path-panel {
    display: flex;
    flex-direction: column;
    visibility: hidden;
    pointer-events: none;
    z-index: 0;
    grid-area: panel;
    padding: 18px 20px 10px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: 10px;
  }
  .study-path:has(#path-stage-1:checked) .path-panel[data-stage="1"],
  .study-path:has(#path-stage-2:checked) .path-panel[data-stage="2"],
  .study-path:has(#path-stage-3:checked) .path-panel[data-stage="3"],
  .study-path:has(#path-stage-4:checked) .path-panel[data-stage="4"],
  .study-path:has(#path-stage-5:checked) .path-panel[data-stage="5"] {
    visibility: visible;
    pointer-events: auto;
    z-index: 1;
  }
  .path-panel-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }
  .path-panel h3 {
    font-size: 22px;
    line-height: 1.25;
    margin: 0 0 8px;
  }
  .path-core-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(200px, 0.4fr);
    gap: 18px 24px;
    padding-top: 14px;
    border-top: 1px solid var(--border);
    align-items: stretch;
  }
  .path-core {
    min-width: 0;
  }
  .path-core-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
  }
  .path-core-label {
    font-family: var(--sans);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
  }
  .path-study-title {
    font-size: 18px;
    font-weight: 700;
    line-height: 1.3;
    margin: 0 0 4px;
  }
  .path-study-title a {
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px solid rgba(26, 82, 118, 0.32);
  }
  .path-study-title a:hover {
    color: var(--accent-hover);
    border-bottom-color: var(--accent);
  }
  .path-study-blurb {
    font-size: 14px;
    line-height: 1.45;
    color: var(--text-muted);
    margin: 0 0 14px;
  }
  .path-core-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
  }
  .path-continue {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
    margin: 0;
    padding: 14px 16px;
    background: var(--accent-soft);
    border: 1px solid #a5c4d9;
    border-radius: 10px;
    cursor: pointer;
    font-family: var(--sans);
    text-align: left;
    appearance: none;
    -webkit-appearance: none;
  }
  .path-continue:hover {
    border-color: var(--accent);
  }
  .path-continue:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  .path-continue-kicker {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 0 0 6px;
  }
  .path-continue-stage {
    font-size: 13px;
    font-weight: 700;
    color: var(--accent);
    margin: 0 0 8px;
  }
  .path-continue-text {
    font-size: 13px;
    line-height: 1.4;
    color: var(--text-muted);
    margin: 0 0 12px;
    flex: 1 1 auto;
  }
  .path-continue-link {
    font-size: 13px;
    font-weight: 700;
    color: var(--accent);
    text-decoration: underline;
    text-underline-offset: 2px;
  }
  .path-status {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 2px 8px;
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 700;
  }
  .path-status.released { color: #1b4332; background: #d8f3dc; }
  .path-status.draft { color: #92400e; background: #fef3c7; }
  .path-status.planned { color: var(--warm); background: var(--warm-soft); }
  .path-action, .path-slides {
    display: inline-block;
    margin: 0;
    font-family: var(--sans);
    font-size: 13px;
    font-weight: 700;
  }
  .path-related {
    margin-top: 6px;
    padding-top: 0;
    font-family: var(--sans);
    font-size: 13px;
    color: var(--text-muted);
  }
  .path-related summary {
    cursor: pointer;
    font-weight: 700;
    color: var(--accent);
  }
  .path-related ul {
    margin: 8px 0 0;
    padding: 0;
    list-style: none;
    max-width: 36em;
  }
  .path-related li {
    padding: 8px 0;
    border-top: 1px solid var(--border);
    line-height: 1.3;
  }
  .path-related li a { font-weight: 600; }
  .path-related .path-status {
    margin: 4px 0 0;
    padding: 1px 7px;
    font-size: 10px;
  }
  .card-actions {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-left: auto;
  }
  .discuss-link {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid #c5d9e6;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 12px;
    font-weight: 700;
    text-decoration: none;
    white-space: nowrap;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  }
  .discuss-link:hover {
    color: var(--accent-hover);
    background: #d4e6f2;
    border-color: #a5c4d9;
  }
  .discuss-link--active {
    padding-right: 8px;
  }
  .discuss-link--unread {
    border-color: #d4a574;
    background: #fff4e5;
    color: #8b5e34;
  }
  .discuss-link--unread:hover {
    background: #fdebd0;
    border-color: #c9924d;
    color: #6b4518;
  }
  .discuss-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    margin-left: 6px;
    padding: 0 5px;
    border-radius: 999px;
    background: var(--accent);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    line-height: 1;
  }
  .discuss-badge--empty {
    visibility: hidden;
  }
  .discuss-link--unread .discuss-badge {
    background: #b45309;
  }
  .pdf-download {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    color: var(--accent);
    background: var(--accent-soft);
    border: 1px solid #c5d9e6;
    border-radius: 8px;
    text-decoration: none;
    flex: 0 0 auto;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  }
  .pdf-download:hover {
    color: var(--accent-hover);
    background: #d4e6f2;
    border-color: #a5c4d9;
  }
  .pdf-download svg {
    width: 16px;
    height: 16px;
    display: block;
  }
  .empty {
    font-family: var(--sans); font-size: 13px; color: var(--text-muted);
    background: var(--surface); border: 1px dashed var(--border);
    border-radius: var(--radius); padding: 22px; text-align: center; margin: 12px 0 4px;
  }
  .empty button {
    font-family: var(--sans); font-size: 13px; color: var(--accent);
    background: none; border: none; text-decoration: underline; cursor: pointer; padding: 0;
  }

  .triad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 14px 0 4px; }
  .triad-item { border: 1px solid var(--border); border-radius: 8px; padding: 13px 15px; background: #fdfcfa; }
  .triad-item .k {
    font-family: var(--sans); font-size: 11px; font-weight: 600;
    letter-spacing: 0.03em; text-transform: uppercase; margin: 0 0 5px;
  }
  .triad-item .v { font-size: 13.5px; color: var(--text-muted); margin: 0; line-height: 1.45; }
  .triad-item.t1 { border-top: 3px solid var(--accent); } .triad-item.t1 .k { color: var(--accent); }
  .triad-item.t2 { border-top: 3px solid var(--warm); } .triad-item.t2 .k { color: var(--warm); }
  .triad-item.t3 { border-top: 3px solid #9a8f80; } .triad-item.t3 .k { color: #6f655a; }

  .contribute-paths {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin: 16px 0 4px;
    align-items: stretch;
  }
  .contribute-path {
    display: flex;
    flex-direction: column;
    height: 100%;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px;
    background: #fdfcfa;
  }
  .contribute-path h3 {
    margin: 0 0 10px;
    font-size: 19px;
    color: #1a1612;
  }
  .contribute-path ol {
    margin: 10px 0 14px 20px;
    padding: 0;
  }
  .contribute-path li { margin: 6px 0; }
  .contribute-path .path-lead {
    color: var(--text-muted);
    font-size: 15px;
    margin: 0 0 12px;
  }
  .contribute-path p.path-note {
    color: var(--text-muted);
    font-size: 14px;
    margin: 0 0 0;
  }
  .contribute-path .path-action {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: auto;
    padding-top: 18px;
    margin-bottom: 0;
  }
  .contribute-path--feedback { border-top: 3px solid var(--warm); }
  .contribute-path--feedback h3 { color: var(--warm); }
  .contribute-path--study { border-top: 3px solid var(--accent); }
  .contribute-path--study h3 { color: var(--accent); }

  .catalog-group { scroll-margin-top: 64px; }
  .license-line {
    font-family: var(--sans); font-size: 13px; color: var(--text-muted);
    margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--border);
  }

  .sr-only {
    position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
    overflow: hidden; clip: rect(0,0,0,0); border: 0;
  }
  .is-hidden { display: none !important; }

  a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, .chip:focus-visible, .cat-filter:focus-visible, .btn-reset-filters:focus-visible {
    outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 6px;
  }

  :root[data-theme="dark"] {
    --bg: #1a1815;
    --surface: #26231e;
    --text: #e6dfd6;
    --text-muted: #aca194;
    --accent: #5ba3d3;
    --accent-soft: #233e52;
    --accent-hover: #7ebbed;
    --warm: #d5a477;
    --warm-soft: #423020;
    --border: #423b33;
    --shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    color-scheme: dark;
  }
  [data-theme="dark"] h1, [data-theme="dark"] h2, [data-theme="dark"] h3 { color: #f5f1ec; }
  [data-theme="dark"] .start-here h2 { color: var(--accent); }
  [data-theme="dark"] .path-dot { background: #1e1b18; }
  [data-theme="dark"] .path-rail-step:has(.path-radio:checked) .path-dot {
    background: var(--accent);
  }
  [data-theme="dark"] .path-rail-step:has(.path-radio:checked) .path-dot,
  [data-theme="dark"] .path-panel-head .path-number { color: #10202b; }
  [data-theme="dark"] .path-panel { background: #1e1b18; }
  [data-theme="dark"] .path-status.released { color: #8fd4a8; background: #1a2e22; }
  [data-theme="dark"] .path-status.draft { color: #f0c78a; background: #3a2818; }
  [data-theme="dark"] .parallel-study { background: #1e1b18; }
  [data-theme="dark"] .path-continue { border-color: #3d6278; }
  [data-theme="dark"] .page-nav { background: rgba(26, 24, 21, 0.92); }
  [data-theme="dark"] .search input, [data-theme="dark"] .seg, [data-theme="dark"] .triad-item { background: #1e1b18; }
  [data-theme="dark"] .search input::placeholder { color: #6f655a; }
  [data-theme="dark"] .seg button:hover { background: #2f2a24; }
  [data-theme="dark"] .btn-reset-filters { background: #1e1b18; }
  [data-theme="dark"] .btn-reset-filters:disabled { color: #6f655a; }
  [data-theme="dark"] .card.is-available:hover { box-shadow: 0 6px 18px rgba(0, 0, 0, 0.5); }
  [data-theme="dark"] .pdf-download { background: #233e52; border-color: #3d6278; color: #7ebbed; }
  [data-theme="dark"] .pdf-download:hover { background: #2f4f63; border-color: #5ba3d3; color: #b8daf3; }
  [data-theme="dark"] .discuss-link { background: #1a2e22; border-color: #355940; color: #8fd4a8; }
  [data-theme="dark"] .discuss-link:hover { background: #243b2c; border-color: #4f8f66; color: #c2efd0; }
  [data-theme="dark"] .discuss-link--unread { background: #3a2818; border-color: #8b5e34; color: #f0c78a; }
  [data-theme="dark"] .discuss-link--unread:hover { background: #4a3220; border-color: #b07a3c; color: #ffe3b8; }
  [data-theme="dark"] .discuss-badge { background: #2f6fed; }
  [data-theme="dark"] .discuss-link--unread .discuss-badge { background: #d97706; }
  [data-theme="dark"] .triad-item.t3 { border-top: 3px solid #6f655a; }
  [data-theme="dark"] .triad-item.t3 .k { color: #aca194; }
  [data-theme="dark"] .contribute-path { background: #1e1b18; }
  [data-theme="dark"] .contribute-path h3 { color: #f5f1ec; }
  [data-theme="dark"] .contribute-path--feedback h3 { color: var(--warm); }
  [data-theme="dark"] .contribute-path--study h3 { color: var(--accent); }
  [data-theme="dark"] .theme-toggle { background: #1e1b18; }
  [data-theme="dark"] .page-nav-submit:hover { background: var(--accent-soft); border-color: #3d6278; }
  [data-theme="dark"] .skip-link { color: #1a1815; }
  [data-theme="dark"] .search-clear { color: #aca194; }
  [data-theme="dark"] .field {
    background-color: #1e1b18;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23aca194' stroke-width='2'><path d='M6 9l6 6 6-6'/></svg>");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 12px 12px;
  }

  @media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
    * { transition: none !important; animation: none !important; }
    .card.is-available:hover { transform: none; }
  }

  @media (max-width: 820px) {
    .page {
      padding-top: calc(var(--page-nav-offset, 56px) + 28px);
    }
    .page-nav {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      width: 100%;
      margin: 0;
      padding: 8px 14px;
      padding-top: max(8px, env(safe-area-inset-top));
      -webkit-backdrop-filter: none;
      backdrop-filter: none;
      background: var(--bg);
      border-bottom: 1px solid var(--border);
      box-shadow: var(--shadow);
    }
    /* The fixed bar has no backdrop-filter here, so it must be fully opaque.
       Needs the [data-theme] prefix to outrank the translucent desktop rule. */
    [data-theme="dark"] .page-nav { background: var(--bg); }
    .page-nav-inner {
      max-width: 1060px;
      margin: 0 auto;
      flex-wrap: wrap;
      row-gap: 8px;
    }
    .page-nav-label { flex: 0 0 100%; }
    .page-nav-anchor {
      display: none;
      height: 0;
    }
    .toc { flex-wrap: wrap; flex: 1 1 100%; min-width: 0; }
    .page-nav-tools { margin-left: auto; }
    .section { scroll-margin-top: calc(var(--page-nav-offset, 56px) + 12px); }
    .catalog-group { scroll-margin-top: calc(var(--page-nav-offset, 56px) + 12px); }
    .browse-heading { scroll-margin-top: calc(var(--page-nav-offset, 56px) + 12px); }
    .card { scroll-margin-top: calc(var(--page-nav-offset, 56px) + 12px); }
    h1 { font-size: 30px; }
    .triad { grid-template-columns: 1fr; }
  }

  @media (max-width: 600px) {
    .page { padding: calc(var(--page-nav-offset, 56px) + 18px) 14px 44px; }
    .hero { padding: 0; }
    .section-card { padding: 18px 16px; }
    h1 { font-size: 26px; }
    .lead { font-size: 17px; }
    .search { flex-basis: 100%; }
    .seg, .field { flex: 1 1 auto; }
    .seg { display: flex; }
    .seg button { flex: 1; }
    .start-here { padding: 19px 16px; }
    .start-here h2 { font-size: 21px; }
    .path-domain { font-size: 10px; letter-spacing: 0.03em; }
    .path-panel { padding: 16px 14px 10px; }
    .path-panel h3 { font-size: 20px; }
    .path-core-layout { grid-template-columns: 1fr; }
  }

  /* Below this width the between-stage reasons cannot hold one line, so the
     spine is drawn once behind evenly spaced dots and the reasons are carried
     by the "Next" card inside each stage panel instead. */
  @container start-path (max-width: 830px) {
    .path-because { display: none; }
    .path-rail::before {
      content: "";
      position: absolute;
      left: 10%;
      right: 10%;
      top: 18px;
      height: 2px;
      background: var(--border);
    }
    .path-rail-step { flex: 1 1 0; }
    .path-rail-item { width: 100%; padding: 3px 3px 0; }
  }

  @container start-path (max-width: 640px) {
    .path-core-layout { grid-template-columns: 1fr; }
  }

  @container start-path (max-width: 470px) {
    .path-rail::before { top: 16px; }
    .path-rail-item { gap: 7px; padding: 3px 1px 0; }
    .path-dot { flex: 0 0 28px; width: 28px; height: 28px; font-size: 12px; }
    .path-stage-name { font-size: 11px; }
  }
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<div class="page">

<header class="hero">
  <h1>Studies of Madhyasth Darshan</h1>
  <p class="lead">An open and growing collection of comparative studies of <strong>Madhyasth Darshan</strong> (Co-existentialism), the philosophy founded by <strong>Shri A. Nagraj</strong>. The collection follows a single line of inquiry while inviting others to examine its arguments, question its interpretations, and contribute to its development.</p>

  <div class="dialogue-row">
    <p class="dialogue-label" id="dialogue-label">Each study is read in dialogue with</p>
    <ul class="dialogue" aria-labelledby="dialogue-label">
      <li><span>Madhyasth Darshan</span></li>
      <li><span>Sciences &amp; technology</span></li>
      <li><span>Advaita Vedanta</span></li>
      <li><span>Modern philosophy</span></li>
    </ul>
  </div>

  <p class="scope" id="hero-scope"><!-- @hero-scope@ --></p>
</header>

<nav class="page-nav" aria-label="On this page">
  <div class="page-nav-inner">
    <ul class="toc" id="toc">
      <li><a href="#start-here">Start here</a></li>
      <li><a href="#browse-studies">Browse studies</a></li>
      <li><a href="#approach">How we work</a></li>
      <li><a href="#contribute">How to contribute</a></li>
      <li><a href="#about">About</a></li>
    </ul>
    <div class="page-nav-tools">
      <a class="page-nav-submit" href="submit.html">My Submissions</a>
      <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Switch color theme">
        <span class="theme-toggle-icon" id="theme-toggle-icon" aria-hidden="true">&#9789;</span>
        <span id="theme-toggle-label">Dark</span>
      </button>
    </div>
  </div>
</nav>
<div class="page-nav-anchor" aria-hidden="true"></div>

<main id="main">

<section class="section" id="studies">

  <noscript>
    <p class="section-intro">JavaScript is required for search and filters on this page. Browse the <a href="README.md">full catalog</a> instead.</p>
  </noscript>

  <div class="start-here" id="start-here">
    <p class="start-here-kicker">A guided path through the collection</p>
    <h2>Start here: the study path we are following</h2>
    <p class="start-here-intro">Is a human only matter? The body by itself does not settle it, and what that leaves open becomes the next question, and the next: existence, then knowledge, then value, then living. Each stage below is the question the one before it could not close.</p>

    <div class="study-path">
      <div class="path-rail" role="radiogroup" aria-label="Five stages in the study path">
        <div class="path-rail-step">
          <input class="path-radio sr-only" type="radio" name="start-path" id="path-stage-1" checked>
          <label class="path-rail-item" for="path-stage-1"><span class="path-dot">1</span><span class="path-stage-name">Human</span></label>
        </div>
        <span class="path-because" aria-hidden="true"><span>so what is there?</span></span>
        <div class="path-rail-step">
          <input class="path-radio sr-only" type="radio" name="start-path" id="path-stage-2">
          <label class="path-rail-item" for="path-stage-2"><span class="path-dot">2</span><span class="path-stage-name">Existence</span></label>
        </div>
        <span class="path-because" aria-hidden="true"><span>how is it known?</span></span>
        <div class="path-rail-step">
          <input class="path-radio sr-only" type="radio" name="start-path" id="path-stage-3">
          <label class="path-rail-item" for="path-stage-3"><span class="path-dot">3</span><span class="path-stage-name">Knowledge</span></label>
        </div>
        <span class="path-because" aria-hidden="true"><span>what has value?</span></span>
        <div class="path-rail-step">
          <input class="path-radio sr-only" type="radio" name="start-path" id="path-stage-4">
          <label class="path-rail-item" for="path-stage-4"><span class="path-dot">4</span><span class="path-stage-name">Value</span></label>
        </div>
        <span class="path-because" aria-hidden="true"><span>how is it lived?</span></span>
        <div class="path-rail-step">
          <input class="path-radio sr-only" type="radio" name="start-path" id="path-stage-5">
          <label class="path-rail-item" for="path-stage-5"><span class="path-dot">5</span><span class="path-stage-name">Living</span></label>
        </div>
      </div>

      <article class="path-panel" data-stage="1">
        <div class="path-panel-head"><span class="path-number">1</span><span class="path-domain">Human</span></div>
        <h3>Is a human only a body?</h3>
        <div class="path-core-layout">
          <div class="path-core" data-study-slug="Why-Humans-Are-Not-Just-Material" data-presentation-pdf="Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material-presentation.pdf">
            <div class="path-core-meta"><span class="path-core-label">Core study</span><span class="path-status released" data-study-status>Released</span></div>
            <p class="path-study-title"><a data-study-link href="Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.html" title="Read the study">Why Humans Are Not Just Material</a></p>
            <p class="path-study-blurb">This study tests whether a human is exhausted by a physicochemical body and brain, comparing a physicalist reading of the sciences with Advaita Vedanta and Madhyasth Darshan&rsquo;s body-and-jeevan account.</p>
            <div class="path-core-actions">
              <a class="path-action" data-study-link href="Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.html">Read the study</a>
              <a class="path-action" data-study-action href="Why-Humans-Are-Not-Just-Material/discussion.html">Discuss this stage</a>
              <a class="path-slides" data-study-slides href="Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material-presentation.pdf" title="Open presentation slides">Slides</a>
            </div>
            <details class="path-related">
              <summary>3 related studies</summary>
              <ul>
                <li data-study-slug="Philosophy-Of-Mind-And-Jeevan"><a data-study-link href="Philosophy-Of-Mind-And-Jeevan/discussion.html">Philosophy of Mind and Jeevan</a><br><span class="path-status planned" data-study-status>In progress</span></li>
                <li data-study-slug="Chitta-Brain-And-Memory"><a data-study-link href="Chitta-Brain-And-Memory/discussion.html">Chitta, Brain, and Memory</a><br><span class="path-status planned" data-study-status>In progress</span></li>
                <li data-study-slug="Death-Continuity-And-Rebirth"><a data-study-link href="Death-Continuity-And-Rebirth/discussion.html">Death, Continuity, and Rebirth</a><br><span class="path-status planned" data-study-status>In progress</span></li>
              </ul>
            </details>
          </div>
          <button type="button" class="path-continue" data-go-stage="2" aria-label="Continue to Existence">
            <span class="path-continue-kicker">Next</span>
            <span class="path-continue-stage">2 Existence</span>
            <span class="path-continue-text">If the body does not already answer what a human is, the leftover questions are about existence: what is there, and where we stand in it.</span>
            <span class="path-continue-link">Continue to Existence</span>
          </button>
        </div>
      </article>

      <article class="path-panel" data-stage="2">
        <div class="path-panel-head"><span class="path-number">2</span><span class="path-domain">Existence</span></div>
        <h3>What exists&mdash;and what are we?</h3>
        <div class="path-core-layout">
          <div class="path-core" data-study-slug="The-Ontology-of-Coexistence" data-presentation-pdf="The-Ontology-of-Coexistence/The-Ontology-of-Existence-Madhyasth-Darshan.pdf">
            <div class="path-core-meta"><span class="path-core-label">Core study</span><span class="path-status released" data-study-status>Released</span></div>
            <p class="path-study-title"><a data-study-link href="The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.html" title="Read the study">The Ontology of Coexistence</a></p>
            <p class="path-study-blurb">This study asks what exists: coexistence of omnipresence and units, the four orders of nature, and the claim that the human belongs to the knowledge order rather than being only a material organism.</p>
            <div class="path-core-actions">
              <a class="path-action" data-study-link href="The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.html">Read the study</a>
              <a class="path-action" data-study-action href="The-Ontology-of-Coexistence/discussion.html">Discuss this stage</a>
              <a class="path-slides" data-study-slides href="The-Ontology-of-Coexistence/The-Ontology-of-Existence-Madhyasth-Darshan.pdf" title="Open presentation slides">Slides</a>
            </div>
            <details class="path-related">
              <summary>3 related studies</summary>
              <ul>
                <li data-study-slug="Nature-Of-Time"><a data-study-link href="Nature-Of-Time/Nature-Of-Time.html">Nature of Time</a><br><span class="path-status released" data-study-status>Released</span></li>
                <li data-study-slug="Nature-Ecology-And-Right-Use"><a data-study-link href="Nature-Ecology-And-Right-Use/discussion.html">Nature, Ecology, and Right Use</a><br><span class="path-status planned" data-study-status>In progress</span></li>
                <li data-study-slug="God-Divinity-And-The-Sacred"><a data-study-link href="God-Divinity-And-The-Sacred/discussion.html">God, Divinity, and the Sacred</a><br><span class="path-status planned" data-study-status>In progress</span></li>
              </ul>
            </details>
          </div>
          <button type="button" class="path-continue" data-go-stage="3" aria-label="Continue to Knowledge">
            <span class="path-continue-kicker">Next</span>
            <span class="path-continue-stage">3 Knowledge</span>
            <span class="path-continue-text">Once that picture of existence is stated, the next study asks how it can be known, and what the knower must know.</span>
            <span class="path-continue-link">Continue to Knowledge</span>
          </button>
        </div>
      </article>

      <article class="path-panel" data-stage="3">
        <div class="path-panel-head"><span class="path-number">3</span><span class="path-domain">Knowledge</span></div>
        <h3>What must the knower know?</h3>
        <div class="path-core-layout">
          <div class="path-core" data-study-slug="The-Epistemology-of-Coexistence" data-presentation-pdf="The-Epistemology-of-Coexistence/The-Epistemology-of-Coexistence-Madhyasth-Darshan.pdf">
            <div class="path-core-meta"><span class="path-core-label">Core study</span><span class="path-status released" data-study-status>Released</span></div>
            <p class="path-study-title"><a data-study-link href="The-Epistemology-of-Coexistence/The-Epistemology-of-Coexistence.html" title="Read the study">The Epistemology of Coexistence</a></p>
            <p class="path-study-blurb">This study asks what knowledge is, who the knower is, and how understanding of coexistence must become evident in evaluation, conduct, and tradition rather than remaining unused information.</p>
            <div class="path-core-actions">
              <a class="path-action" data-study-link href="The-Epistemology-of-Coexistence/The-Epistemology-of-Coexistence.html">Read the study</a>
              <a class="path-action" data-study-action href="The-Epistemology-of-Coexistence/discussion.html">Discuss this stage</a>
              <a class="path-slides" data-study-slides href="The-Epistemology-of-Coexistence/The-Epistemology-of-Coexistence-Madhyasth-Darshan.pdf" title="Open presentation slides">Slides</a>
            </div>
            <details class="path-related">
              <summary>4 related studies</summary>
              <ul>
                <li data-study-slug="Methodology-And-Hermeneutics"><a data-study-link href="Methodology-And-Hermeneutics/discussion.html">Methodology and Hermeneutics</a><br><span class="path-status planned" data-study-status>In progress</span></li>
                <li data-study-slug="Work-Action-And-Karma"><a data-study-link href="Work-Action-And-Karma/discussion.html">Work, Action, and Karma</a><br><span class="path-status planned" data-study-status>In progress</span></li>
                <li data-study-slug="Free-Will-Choice-And-Agency"><a data-study-link href="Free-Will-Choice-And-Agency/discussion.html">Free Will, Choice, and Agency</a><br><span class="path-status planned" data-study-status>In progress</span></li>
                <li data-study-slug="Language-Meaning-And-Definition"><a data-study-link href="Language-Meaning-And-Definition/discussion.html">Language, Meaning, and Definition</a><br><span class="path-status planned" data-study-status>In progress</span></li>
              </ul>
            </details>
          </div>
          <button type="button" class="path-continue" data-go-stage="4" aria-label="Continue to Value">
            <span class="path-continue-kicker">Next</span>
            <span class="path-continue-stage">4 Value</span>
            <span class="path-continue-text">If understanding must show itself in evaluation, the next study asks what a value is, and what makes relationship definite.</span>
            <span class="path-continue-link">Continue to Value</span>
          </button>
        </div>
      </article>

      <article class="path-panel" data-stage="4">
        <div class="path-panel-head"><span class="path-number">4</span><span class="path-domain">Value</span></div>
        <h3>What makes value and relationship definite?</h3>
        <div class="path-core-layout">
          <div class="path-core" data-study-slug="Axiology-Value-Theory">
            <div class="path-core-meta"><span class="path-core-label">Core study</span><span class="path-status released" data-study-status>Released</span></div>
            <p class="path-study-title"><a data-study-link href="Axiology-Value-Theory/Axiology-Value-Theory.html" title="Read the study">Axiology: Value Theory</a></p>
            <p class="path-study-blurb">This study asks what a value is, whether it is conferred by preference or already present in participation, and how evaluation can be correct or mistaken in relationship and conduct.</p>
            <div class="path-core-actions">
              <a class="path-action" data-study-link href="Axiology-Value-Theory/Axiology-Value-Theory.html">Read the study</a>
              <a class="path-action" data-study-action href="Axiology-Value-Theory/discussion.html">Discuss this stage</a>
            </div>
            <details class="path-related">
              <summary>3 related studies</summary>
              <ul>
                <li data-study-slug="Ethics-And-Morals-In-Human-Beings"><a data-study-link href="Ethics-And-Morals-In-Human-Beings/Ethics-And-Morals-In-Human-Beings.html">Ethics and Morals in Human Beings</a><br><span class="path-status draft" data-study-status>Draft</span></li>
                <li data-study-slug="Family-Relationships-And-Values"><a data-study-link href="Family-Relationships-And-Values/discussion.html">Family Relationships and Values</a><br><span class="path-status planned" data-study-status>In progress</span></li>
                <li data-study-slug="Aesthetics"><a data-study-link href="Aesthetics/Aesthetics.html">Aesthetics</a><br><span class="path-status draft" data-study-status>Draft</span></li>
              </ul>
            </details>
          </div>
          <button type="button" class="path-continue" data-go-stage="5" aria-label="Continue to Living">
            <span class="path-continue-kicker">Next</span>
            <span class="path-continue-stage">5 Living</span>
            <span class="path-continue-text">Values that are definite still have to be lived. The next study asks how coexistence is established in family, education, and society.</span>
            <span class="path-continue-link">Continue to Living</span>
          </button>
        </div>
      </article>

      <article class="path-panel" data-stage="5">
        <div class="path-panel-head"><span class="path-number">5</span><span class="path-domain">Living</span></div>
        <h3>How is coexistence lived?</h3>
        <div class="path-core-layout">
          <div class="path-core" data-study-slug="How-Undivided-Society-Is-Established" data-presentation-pdf="How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established-presentation.pdf">
            <div class="path-core-meta"><span class="path-core-label">Core study</span><span class="path-status released" data-study-status>Released</span></div>
            <p class="path-study-title"><a data-study-link href="How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established.html" title="Read the study">How Undivided Society Is Established</a></p>
            <p class="path-study-blurb">This study asks what would make humankind an undivided society, and how that is established through family, education, organisations, and institutions as the test of the earlier understanding.</p>
            <div class="path-core-actions">
              <a class="path-action" data-study-link href="How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established.html">Read the study</a>
              <a class="path-action" data-study-action href="How-Undivided-Society-Is-Established/discussion.html">Discuss this stage</a>
              <a class="path-slides" data-study-slides href="How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established-presentation.pdf" title="Open presentation slides">Slides</a>
            </div>
            <details class="path-related">
              <summary>3 related studies</summary>
              <ul>
                <li data-study-slug="Human-Behavior-And-Society"><a data-study-link href="Human-Behavior-And-Society/Human-Behavior-And-Society.html">Human Behavior and Society</a><br><span class="path-status draft" data-study-status>Draft</span></li>
                <li data-study-slug="How-To-Form-Self-Sustaining-Organizations"><a data-study-link href="How-To-Form-Self-Sustaining-Organizations/How-To-Form-Self-Sustaining-Organizations.html">How to Form Self-Sustaining Organizations</a><br><span class="path-status released" data-study-status>Released</span></li>
                <li data-study-slug="Education-And-Sanskar"><a data-study-link href="Education-And-Sanskar/discussion.html">Education and Sanskar</a><br><span class="path-status planned" data-study-status>In progress</span></li>
              </ul>
            </details>
          </div>
          <button type="button" class="path-continue" data-go-stage="1" aria-label="Return to Human">
            <span class="path-continue-kicker">The path</span>
            <span class="path-continue-stage">Return to Human</span>
            <span class="path-continue-text">The path does not continue to another stage. Understanding is tested in living, and can be walked again from the human question.</span>
            <span class="path-continue-link">Return to Human</span>
          </button>
        </div>
      </article>

      <div class="path-alongside">
        <span class="path-alongside-label">Also across the path</span>
        <div class="path-alongside-studies">
          <div class="parallel-study" data-study-slug="A-State-Dynamic-Model-Of-Coexistence" data-presentation-pdf="A-State-Dynamic-Model-Of-Coexistence/A-State-Dynamic-Model-Of-Coexistence-Madhyasth-Darshan.pdf"><a data-study-link href="A-State-Dynamic-Model-Of-Coexistence/A-State-Dynamic-Model-Of-Coexistence.html" title="Read the study">From Unit Activity to Human Orderliness</a><span class="path-status draft" data-study-status>Draft</span><a class="path-slides" data-study-slides href="A-State-Dynamic-Model-Of-Coexistence/A-State-Dynamic-Model-Of-Coexistence-Madhyasth-Darshan.pdf" title="Open presentation slides">Slides</a></div>
          <div class="parallel-study" data-study-slug="Science-Technology-And-Human-Purpose"><a data-study-link href="Science-Technology-And-Human-Purpose/discussion.html">Science, Technology, and Human Purpose</a><span class="path-status planned" data-study-status>In progress</span></div>
        </div>
      </div>

      <p class="path-invite">Follow the stages in order, question the order, or <a href="#contribute">take up a stage that is still unwritten</a>. To read outside the path, <a href="#browse-studies">browse the full collection</a>.</p>
    </div>
  </div>

  <div class="browse-heading" id="browse-studies">
    <h2>Browse all studies</h2>
    <p>Search the complete collection by topic, status, or type. Released studies are stable versions, drafts are available for review, and in-progress studies are open for discussion and development.</p>
  </div>

  <div class="toolbar" role="search">
    <label class="search">
      <span class="sr-only">Search studies</span>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
      <input type="text" id="q" placeholder="Search title, topic, or category&hellip;" autocomplete="off"/>
      <button type="button" class="search-clear" id="search-clear" aria-label="Clear search">&times;</button>
    </label>
    <div class="seg-group">
      <span class="seg-label" id="coll-seg-label">Collection</span>
      <div class="seg" id="coll-seg" role="group" aria-labelledby="coll-seg-label">
        <button type="button" data-coll="all" aria-pressed="true">All</button>
        <button type="button" data-coll="topical" aria-pressed="false">Topical</button>
        <button type="button" data-coll="formal" aria-pressed="false">Formal</button>
        <button type="button" data-coll="applied" aria-pressed="false">Applied</button>
      </div>
    </div>
    <div class="seg-group">
      <span class="seg-label" id="status-seg-label">Status</span>
      <div class="seg" id="status-seg" role="group" aria-labelledby="status-seg-label">
        <button type="button" data-status="all" aria-pressed="false">All</button>
        <button type="button" data-status="available" aria-pressed="true">Available</button>
        <button type="button" data-status="planned" aria-pressed="false">In progress</button>
      </div>
    </div>
    <div class="seg-group">
      <label class="seg-label" for="sort">Sort</label>
      <select class="field" id="sort">
        <option value="recent">Recently updated</option>
        <option value="az">Title A&ndash;Z</option>
      </select>
    </div>
    <button type="button" class="btn-reset-filters" id="reset-filters" disabled>Reset filters</button>
  </div>

  <div class="cat-list-panel">
    <span class="cat-list-label" id="cat-list-label">Categories</span>
    <div class="cat-list" id="cat-list" role="group" aria-labelledby="cat-list-label"></div>
  </div>

  <p class="filter-notice is-hidden" id="filter-notice" aria-live="polite"></p>

  <p class="sr-only" id="count" aria-live="polite"></p>

  <div class="catalog-group" id="topical-studies">
  <p class="cat-group-label">Topical studies <span class="count" data-count-for="topical"></span></p>
  <ul class="grid" id="grid-topical"></ul>
  <p class="empty is-hidden" id="empty-topical">No topical studies match these filters. <button type="button" class="clear-all">Clear filters</button></p>
  </div>

  <div class="catalog-group" id="formal-studies">
  <p class="cat-group-label">Formal studies <span class="count" data-count-for="formal"></span></p>
  <ul class="grid" id="grid-formal"></ul>
  <p class="empty is-hidden" id="empty-formal">No formal studies match these filters. <button type="button" class="clear-all">Clear filters</button></p>
  </div>

  <div class="catalog-group" id="applied-studies">
  <p class="cat-group-label">Applied studies <span class="count" data-count-for="applied"></span></p>
  <ul class="grid" id="grid-applied"></ul>
  <p class="empty is-hidden" id="empty-applied">No applied studies match these filters. <button type="button" class="clear-all">Clear filters</button></p>
  </div>
</section>

<section class="section" id="approach">
  <h2>How we work</h2>
  <div class="section-card">
    <h3>Our approach</h3>
    <p>The project reads primary <strong>Madhyasth Darshan</strong> texts closely, reconstructs their claims as clearly as possible, and compares them with the natural sciences, Advaita Vedanta, and modern philosophy. The aim is rigorous comparative understanding: to test definitions, internal consistency, explanatory scope, and compatibility with evidence &mdash; not to persuade or offer devotional endorsement.</p>

    <h3>What we keep separate</h3>
    <p class="section-intro" style="margin-bottom:4px;">Throughout, three things are held clearly apart:</p>
    <div class="triad">
      <div class="triad-item t1">
        <p class="k">The source position</p>
        <p class="v">What the primary Madhyasth Darshan texts state, grounded in definitions and citations.</p>
      </div>
      <div class="triad-item t2">
        <p class="k">Our analysis</p>
        <p class="v">Interpretation, comparison, criticism, and formal reconstruction undertaken by this project.</p>
      </div>
      <div class="triad-item t3">
        <p class="k">Open questions</p>
        <p class="v">Claims that remain unclear, disputed, insufficiently supported, or in need of further study.</p>
      </div>
    </div>

    <h3>Objectives</h3>
    <ol>
      <li>Understand each topic closely enough to state its definitions, claims, and arguments clearly.</li>
      <li>Compare traditions using explicit questions and consistent standards of evidence and reasoning.</li>
      <li>Develop formal representations where they clarify structure, without confusing mathematical analogy or reconstruction with source doctrine.</li>
      <li>Examine what these ideas imply for relationships, conduct, institutions, science, and technology.</li>
    </ol>

    <h3>From study to understanding</h3>
    <p>Reading and logical reconstruction are the beginning, not the endpoint. This path treats understanding as something to be tested in observation, relationships, decisions, and participation in family and society. Practice does not replace argument or evidence; it is where claims about value and conduct encounter lived consequences.</p>
  </div>
</section>

<section class="section" id="contribute">
  <h2>How to contribute</h2>
  <div class="section-card">
    <p class="section-intro">Contributions can improve an existing study or help create one that has not yet been written.</p>
    <div class="contribute-paths">
      <div class="contribute-path contribute-path--feedback" id="comments-and-corrections">
        <h3>Discuss or improve a study</h3>
        <p class="path-lead">Open <strong>Discuss</strong> to ask a question, challenge an interpretation, suggest sources, or help shape an in-progress study. Use <strong>Suggest a correction</strong> when you can identify a specific factual, textual, citation, or presentation problem.</p>
        <ol>
          <li>Select <strong>Discuss</strong> on any study to join its ongoing inquiry.</li>
          <li>Select <strong>Suggest a correction</strong> for a concrete change to a published study.</li>
          <li>For an in-progress study, contribute questions, sources, proposed structure, or comparative material through its discussion.</li>
        </ol>
        <p class="path-note">Corrections go directly to the maintainers for review; a separate study proposal is not required. A GitHub account is required to file a correction.</p>
        <p class="path-action"><a class="btn-secondary" href="?status=all&amp;sort=recent#browse-studies">Browse discussions</a> <a class="btn-primary" href="https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-feedback.yml">Suggest a correction</a></p>
      </div>
      <div class="contribute-path contribute-path--study" id="propose-a-new-study">
        <h3>Write or substantially revise a study</h3>
        <p class="path-lead">Use the Web Submission Portal if you want to take responsibility for a new analytic paper or a substantial revision. Read the <a href="https://github.com/raghavamohan/AnalyticMadhyasthDarshan/blob/master/Studies/README.md">study format guide</a> and the <a href="https://github.com/raghavamohan/AnalyticMadhyasthDarshan/blob/master/CONTRIBUTING.md">contributor guide</a> before you start.</p>
        <p class="path-note">A free <a href="https://github.com/signup" target="_blank" rel="noopener">GitHub account</a> is required to propose or submit &mdash; it is how we track your proposal, pull request, and review history, and how you receive updates. Creating one takes a minute; reading studies never requires an account.</p>
        <ol>
          <li>Sign in to <a href="submit.html"><strong>My Submissions</strong></a> and submit a proposal.</li>
          <li>After approval, prepare the study using the provided template and submit the draft.</li>
          <li>Track review, checks, revisions, and release status from the same page.</li>
        </ol>
        <p class="path-action"><a class="btn-primary" href="submit.html">Open My Submissions</a></p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="about">
  <h2>About us</h2>
  <div class="section-card">
    <p><a href="https://analyticmadhyasthdarshan.org/"><strong>AnalyticMadhyasthDarshan.org</strong></a> is an independent collaborative project. It is not an official publication of Divya Path Sansthan. For official Madhyasth Darshan texts and lectures, visit <a href="https://www.madhyasth.org/">madhyasth.org</a>.</p>
    <p>Anyone is welcome to read the studies, inspect their sources, join a discussion, or contribute through the project&rsquo;s <a href="https://github.com/raghavamohan/AnalyticMadhyasthDarshan">GitHub repository</a>. Every study ends with a list of its sources, linking to the original texts wherever they are freely available.</p>
    <p class="license-line"><strong>License:</strong> <a href="https://creativecommons.org/licenses/by/4.0/">CC-BY-4.0</a> &mdash; attribution required. Cite <strong>AnalyticMadhyasthDarshan.org</strong> and link to the repository.</p>
  </div>
</section>

</main>

</div>

<script type="application/json" id="catalog-bootstrap">
<!-- @catalog-bootstrap@ -->
</script>

<script>
(() => {
  const CATALOG_BUILD_ID = "@catalog-build-id@";
  const DISCUSS_ASSET_VERSION = "@discuss-asset-version@";
  const catalogSources = [
    { url: `catalog-topical.json?cb=${CATALOG_BUILD_ID}`, coll: "topical" },
    { url: `catalog-formal.json?cb=${CATALOG_BUILD_ID}`, coll: "formal" },
    { url: `catalog-applied.json?cb=${CATALOG_BUILD_ID}`, coll: "applied" },
  ];

  const mapEntries = (entries, coll) => {
    if (!Array.isArray(entries)) return [];
    return entries.map(entry => ({
      t: entry.title,
      slug: entry.slug,
      coll,
      status: entry.status === "ongoing" ? "planned" : entry.status,
      updated: entry.updated || null,
      cats: entry.categories || [],
      d: entry.description || "",
      pdf: entry.pdf || null,
      html: entry.html || null,
      discussion: entry.discussion || null
    }));
  };

  let STUDIES = [];
  let discussStats = {};
  let lastGridPaint = {};
  const DISCUSS_SEEN_KEY = "amd-discuss-seen";
  const SITE_HOST = "analyticmadhyasthdarshan.org";
  const DISCUSS_API_FALLBACK = "https://amd-discussions.raghavamohan.workers.dev";

  const discussApiBase = () => (window.location.hostname === SITE_HOST ? "" : DISCUSS_API_FALLBACK);

  const readDiscussSeenMap = () => {
    try {
      return JSON.parse(localStorage.getItem(DISCUSS_SEEN_KEY) || "{}");
    } catch {
      return {};
    }
  };

  const discussStatsFor = slug => discussStats[slug] || { count: 0, latestAt: 0 };

  const isDiscussUnread = slug => {
    const { count, latestAt } = discussStatsFor(slug);
    if (!count || !latestAt) return false;
    const seen = Number(readDiscussSeenMap()[slug] || 0);
    return latestAt > seen;
  };

  const discussLinkHtml = s => {
    const href = studyDiscussionHref(s);
    const { count } = discussStatsFor(s.slug);
    const unread = isDiscussUnread(s.slug);
    const classes = ["discuss-link"];
    if (count) classes.push("discuss-link--active");
    if (unread) classes.push("discuss-link--unread");
    const badge = `<span class="discuss-badge${count ? "" : " discuss-badge--empty"}" aria-hidden="true">${count || ""}</span>`;
    const unreadNote = unread ? " — new comments since your last visit" : "";
    const countNote = count ? ` — ${count} comment${count === 1 ? "" : "s"}` : "";
    return `<a class="${classes.join(" ")}" href="${href}" title="Discussion board${countNote}${unreadNote}" aria-label="Discuss ${escAttr(s.t)}${countNote}${unreadNote}">Discuss${badge}</a>`;
  };

  const loadDiscussStats = async () => {
    try {
      const response = await fetch(discussApiBase() + "/api/discussions/stats");
      if (!response.ok) return;
      const data = await response.json();
      const map = {};
      for (const row of data.threads || []) {
        if (!row?.slug) continue;
        map[row.slug] = {
          count: Number(row.count || 0),
          latestAt: Number(row.latestAt || 0),
        };
      }
      discussStats = map;
    } catch {
      discussStats = {};
    }
  };

  const parseBootstrap = () => {
    const bootstrap = document.getElementById("catalog-bootstrap");
    if (!bootstrap) return [];
    const text = bootstrap.textContent.trim();
    if (!text || text.charAt(0) === "<") return [];
    try {
      const data = JSON.parse(text);
      return [
        ...mapEntries(data.topical || [], "topical"),
        ...mapEntries(data.formal || [], "formal"),
        ...mapEntries(data.applied || [], "applied"),
      ];
    } catch {
      return [];
    }
  };

  const fetchCatalogs = async () => {
    const parts = await Promise.all(
      catalogSources.map(async ({ url, coll }) => {
        try {
          const res = await fetch(url);
          if (!res.ok) return [];
          return mapEntries(await res.json(), coll);
        } catch {
          return [];
        }
      })
    );
    const fetched = parts.flat();
    return fetched.length ? fetched : null;
  };

  const isAvail = s => s.status === "draft" || s.status === "released";
  const ts = s => s.updated ? Date.parse(s.updated) : -Infinity;
  const DEFAULT_STATUS = "available";
  const state = { q: "", coll: "all", status: DEFAULT_STATUS, cat: "all", sort: "recent" };

  const updateSearchClear = () => {
    const input = document.getElementById("q");
    const wrap = input ? input.closest(".search") : null;
    if (wrap) wrap.classList.toggle("has-value", !!state.q);
  };

  const syncControlsToState = () => {
    const input = document.getElementById("q");
    if (input) input.value = state.q;
    updateSearchClear();
    const sortEl = document.getElementById("sort");
    if (sortEl) sortEl.value = state.sort;
    const coll = document.getElementById("coll-seg");
    if (coll) Array.from(coll.querySelectorAll("button")).forEach(b => {
      b.setAttribute("aria-pressed", b.dataset.coll === state.coll ? "true" : "false");
    });
    const status = document.getElementById("status-seg");
    if (status) Array.from(status.querySelectorAll("button")).forEach(b => {
      b.setAttribute("aria-pressed", b.dataset.status === state.status ? "true" : "false");
    });
  };

  const writeStateToUrl = () => {
    const params = new URLSearchParams();
    if (state.q) params.set("q", state.q);
    if (state.coll !== "all") params.set("coll", state.coll);
    if (state.status !== DEFAULT_STATUS) params.set("status", state.status);
    if (state.cat !== "all") params.set("cat", state.cat);
    if (state.sort !== "recent") params.set("sort", state.sort);
    const qs = params.toString();
    const next = window.location.pathname + (qs ? `?${qs}` : "") + window.location.hash;
    history.replaceState(null, "", next);
  };

  const readStateFromUrl = () => {
    const params = new URLSearchParams(window.location.search);
    state.q = params.get("q") || "";
    state.coll = params.get("coll") || "all";
    state.status = params.get("status") || DEFAULT_STATUS;
    state.cat = params.get("cat") || "all";
    state.sort = params.get("sort") || "recent";
    syncControlsToState();
    initHashStudyTarget();
  };

  const updateHeroScope = () => {
    const scope = document.getElementById("hero-scope");
    if (!scope) return;
    const total = STUDIES.length;
    const available = STUDIES.filter(isAvail).length;
    const cats = {};
    STUDIES.forEach(s => s.cats.forEach(c => { cats[c] = true; }));
    const topicCount = Object.keys(cats).length;
    scope.innerHTML = `<strong>${available} of ${total}</strong> studies available &middot; <strong>${topicCount}</strong> topics &middot; open &amp; independent`;
  };

  const escAttr = value => String(value).replace(/"/g, "&quot;").replace(/</g, "&lt;");

  const matchesStatus = s => {
    if (state.status === "available" && !isAvail(s)) return false;
    if (state.status === "planned" && isAvail(s)) return false;
    return true;
  };

  const matchesSearch = s => {
    if (!state.q) return true;
    const hay = `${s.t} ${s.d} ${s.cats.join(" ")}`.toLowerCase();
    return hay.includes(state.q.toLowerCase());
  };

  const matchesColl = s => state.coll === "all" || s.coll === state.coll;

  const matchesBase = s => matchesStatus(s) && matchesSearch(s) && matchesColl(s);

  const matches = s => {
    if (!matchesBase(s)) return false;
    if (state.cat !== "all" && !s.cats.includes(state.cat)) return false;
    return true;
  };

  const filtersActive = () => !!(state.q || state.coll !== "all" || state.status !== DEFAULT_STATUS || state.cat !== "all" || state.sort !== "recent");

  const categoryCounts = () => {
    const counts = {};
    STUDIES.forEach(s => {
      if (!matchesBase(s)) return;
      s.cats.forEach(c => {
        counts[c] = (counts[c] || 0) + 1;
      });
    });
    return counts;
  };

  const buildCategoryList = () => {
    const list = document.getElementById("cat-list");
    if (!list) return;

    const counts = categoryCounts();
    const cats = Object.keys(counts).sort();

    if (state.cat !== "all" && !counts[state.cat]) {
      state.cat = "all";
    }

    const parts = [
      `<button type="button" class="cat-filter${state.cat === "all" ? " is-active" : ""}" data-cat="all" aria-pressed="${state.cat === "all" ? "true" : "false"}">All</button>`
    ];

    cats.forEach(c => {
      const active = state.cat === c;
      parts.push(
        `<button type="button" class="cat-filter${active ? " is-active" : ""}" data-cat="${escAttr(c)}" aria-pressed="${active ? "true" : "false"}">${c} <span class="cat-count">(${counts[c]})</span></button>`
      );
    });

    list.innerHTML = parts.join("");
  };

  const updateResetButton = () => {
    const btn = document.getElementById("reset-filters");
    if (btn) btn.disabled = !filtersActive();
  };

  const resetFilters = () => {
    state.q = "";
    state.coll = "all";
    state.status = DEFAULT_STATUS;
    state.cat = "all";
    state.sort = "recent";
    if (qInput) qInput.value = "";
    if (sortSelect) sortSelect.value = "recent";
    if (collSeg) {
      Array.from(collSeg.querySelectorAll("button")).forEach(x => {
        x.setAttribute("aria-pressed", x.dataset.coll === "all" ? "true" : "false");
      });
    }
    if (statusSeg) {
      Array.from(statusSeg.querySelectorAll("button")).forEach(x => {
        x.setAttribute("aria-pressed", x.dataset.status === DEFAULT_STATUS ? "true" : "false");
      });
    }
    renderCatalog();
  };

  const updatedDate = updated => {
    if (!updated) return "";
    const match = String(updated).match(/^([A-Za-z]+\\s+\\d{1,2},\\s*\\d{4})/);
    return match ? match[1] : String(updated);
  };

  const pdfVersionQuery = updated => {
    if (!updated) return "";
    const t = Date.parse(String(updated).replace(/\\s+IST\\s*$/i, " GMT+0530"));
    if (Number.isFinite(t)) return `?v=${t}`;
    const digits = String(updated).replace(/[^0-9]/g, "");
    return digits ? `?v=${digits}` : "";
  };

  const studyHtmlHref = s => {
    const base = s.html || (s.pdf ? s.pdf.replace(/\\.pdf$/i, ".html") : `${s.slug}/${s.slug}.html`);
    return `${base}${pdfVersionQuery(s.updated)}`;
  };

  const studyPdfHref = s => {
    const base = s.pdf || `${s.slug}/${s.slug}.pdf`;
    return `${base}${pdfVersionQuery(s.updated)}`;
  };

  const studyDiscussionHref = s => {
    const base = s.discussion || `${s.slug}/discussion.html`;
    const versionQuery = pdfVersionQuery(s.updated);
    if (!DISCUSS_ASSET_VERSION) return `${base}${versionQuery}`;
    const sep = versionQuery ? "&" : "?";
    return `${base}${versionQuery}${sep}dv=${DISCUSS_ASSET_VERSION}`;
  };

  const PDF_DOWNLOAD_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 3a1 1 0 0 1 1 1v9.59l2.3-2.3a1 1 0 1 1 1.4 1.42l-4 4a1 1 0 0 1-1.4 0l-4-4a1 1 0 1 1 1.4-1.42l2.3 2.3V4a1 1 0 0 1 1-1Zm-7 14a1 1 0 0 1 1 1v1h12v-1a1 1 0 1 1 2 0v2a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1Z"/></svg>';

  const hasReadLinks = s => isAvail(s) || Boolean(s.html || s.pdf);

  const cardHTML = s => {
    const avail = isAvail(s);
    const readable = hasReadLinks(s);
    const chips = s.cats.map(c => `<button type="button" class="chip" data-cat="${c.replace(/"/g, "&quot;")}">${c}</button>`).join("");
    const htmlHref = readable ? studyHtmlHref(s) : null;
    const pdfHref = readable ? studyPdfHref(s) : null;
    const discussHref = studyDiscussionHref(s);
    const titleInner = readable
      ? `<a href="${htmlHref}">${s.t}</a>`
      : `<a href="${discussHref}">${s.t}</a>`;
    const cardClass = !avail ? "is-planned" : (s.status === "released" ? "is-released is-available" : "is-draft is-available");
    const badgeClass = !avail ? "planned" : (s.status === "released" ? "released" : "draft");
    const badgeLabel = !avail ? "In progress" : (s.status === "released" ? "Released" : "Draft");
    const draftTitle = s.status === "draft" ? ' title="Draft PDF includes a watermark"' : "";
    const readActions = readable
      ? `<a class="pdf-download" href="${pdfHref}" download title="Download PDF" aria-label="Download PDF for ${escAttr(s.t)}">${PDF_DOWNLOAD_ICON}</a>`
      : "";
    const foot = avail
      ? `<span class="badge ${badgeClass}"${draftTitle}><span class="badge-dot"></span>${badgeLabel}</span><span class="card-actions">${discussLinkHtml(s)}${readActions}</span>`
      : `<span class="badge planned"><span class="badge-dot"></span>In progress</span><span class="card-actions">${discussLinkHtml(s)}${readActions}</span>`;
    const dateLine = avail && s.updated
      ? `<div class="card-foot" style="border:none;padding:6px 0 0;color:#9a8f80;">Updated ${updatedDate(s.updated)}</div>`
      : "";
    return `<li class="card ${cardClass}" id="study-${escAttr(s.slug)}">
      <h3 class="card-title">${titleInner}</h3>
      <div class="chips">${chips}</div>
      <p class="card-desc">${s.d}</p>
      <div class="card-foot">${foot}</div>${dateLine}</li>`;
  };

  const renderCatalog = () => {
    if (state.coll !== "all" && !STUDIES.some(s => s.coll === state.coll)) {
      state.coll = "all";
      syncControlsToState();
    }
    buildCategoryList();
    updateResetButton();

    let shown = 0;
    ["topical", "formal", "applied"].forEach(coll => {
      const total = STUDIES.filter(s => s.coll === coll).length;
      const collButton = document.querySelector(`#coll-seg [data-coll="${coll}"]`);
      if (collButton) collButton.hidden = total === 0;
      const group = document.getElementById(`${coll}-studies`);
      const groupHidden = total === 0 || (state.coll !== "all" && state.coll !== coll);
      if (group) group.classList.toggle("is-hidden", groupHidden);
      if (groupHidden) return;

      const items = STUDIES.filter(s => s.coll === coll && matches(s));
      items.sort((a, b) => state.sort === "az" ? a.t.localeCompare(b.t) : ts(b) - ts(a));
      shown += items.length;
      const grid = document.getElementById(`grid-${coll}`);
      if (grid) {
        const key = items.map(s => [s.slug, s.status, s.updated || "", s.t, s.d, (s.cats || []).join("\\u001f"), s.html || "", s.pdf || ""].join("\\t")).join("\\n") + `|${state.sort}`;
        const existingSlugs = Array.from(grid.querySelectorAll(".card")).map(el => el.id.slice(6));
        const sameOrder = existingSlugs.length === items.length && existingSlugs.every((slug, i) => slug === items[i].slug);
        if (lastGridPaint[coll] == null && sameOrder && !filtersActive()) {
          lastGridPaint[coll] = key;
        } else if (lastGridPaint[coll] !== key) {
          grid.innerHTML = items.map(cardHTML).join("");
          lastGridPaint[coll] = key;
        }
      }
      const empty = document.getElementById(`empty-${coll}`);
      if (empty) empty.classList.toggle("is-hidden", items.length > 0);
      const countEl = document.querySelector(`[data-count-for="${coll}"]`);
      if (countEl) countEl.textContent = `${items.length} of ${total} shown`;
    });
    const count = document.getElementById("count");
    if (count) count.textContent = `${shown} studies shown`;
    const notice = document.getElementById("filter-notice");
    if (notice) {
      const hidden = STUDIES.filter(s => !isAvail(s)).length;
      const hiding = state.status === "available" && hidden > 0;
      notice.classList.toggle("is-hidden", !hiding);
      if (hiding) {
        notice.innerHTML =
          `Showing studies available to read. ` +
          `<button type="button" class="filter-notice-action" id="filter-notice-show-all">` +
          `Include the ${hidden} in progress</button>`;
        const showAll = document.getElementById("filter-notice-show-all");
        if (showAll) {
          showAll.addEventListener("click", () => {
            state.status = "all";
            syncControlsToState();
            renderCatalog();
          });
        }
      }
    }
    writeStateToUrl();
    applyHashStudyTarget();
  };

  const qInput = document.getElementById("q");
  let searchTimer = null;
  if (qInput) qInput.addEventListener("input", e => {
    state.q = e.target.value;
    updateSearchClear();
    clearTimeout(searchTimer);
    searchTimer = setTimeout(renderCatalog, 120);
  });

  const searchClear = document.getElementById("search-clear");
  if (searchClear) searchClear.addEventListener("click", () => {
    state.q = "";
    if (qInput) { qInput.value = ""; qInput.focus(); }
    updateSearchClear();
    renderCatalog();
  });

  document.addEventListener("keydown", e => {
    if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
    const target = e.target;
    const tag = (target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || target.isContentEditable) return;
    if (qInput) { e.preventDefault(); qInput.focus(); }
  });

  const applyThemeUi = theme => {
    const isDark = theme === "dark";
    const icon = document.getElementById("theme-toggle-icon");
    const label = document.getElementById("theme-toggle-label");
    const btn = document.getElementById("theme-toggle");
    if (icon) icon.innerHTML = isDark ? "&#9728;" : "&#9789;";
    if (label) label.textContent = isDark ? "Light" : "Dark";
    if (btn) btn.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
  };

  const currentTheme = () => document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";

  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    applyThemeUi(currentTheme());
    themeToggle.addEventListener("click", () => {
      const next = currentTheme() === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("amd-theme", next); } catch {}
      applyThemeUi(next);
    });
  }

  document.querySelectorAll("#start-here .path-radio").forEach(radio => {
    radio.addEventListener("change", () => {
      document.querySelectorAll("#start-here .path-related").forEach(details => {
        details.open = false;
      });
    });
  });

  const startHere = document.getElementById("start-here");
  if (startHere) {
    startHere.addEventListener("click", e => {
      const go = e.target.closest("[data-go-stage]");
      if (!go) return;
      const radio = document.getElementById(`path-stage-${go.dataset.goStage}`);
      if (!radio || radio.checked) return;
      radio.checked = true;
      radio.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  const collSeg = document.getElementById("coll-seg");
  if (collSeg) collSeg.addEventListener("click", e => {
    const btn = e.target.closest("button");
    if (!btn) return;
    state.coll = btn.dataset.coll || "all";
    Array.from(collSeg.querySelectorAll("button")).forEach(b => {
      b.setAttribute("aria-pressed", b === btn ? "true" : "false");
    });
    renderCatalog();
  });

  const statusSeg = document.getElementById("status-seg");
  if (statusSeg) statusSeg.addEventListener("click", e => {
    const btn = e.target.closest("button");
    if (!btn) return;
    state.status = btn.dataset.status;
    Array.from(statusSeg.querySelectorAll("button")).forEach(b => {
      b.setAttribute("aria-pressed", b === btn ? "true" : "false");
    });
    renderCatalog();
  });

  const sortSelect = document.getElementById("sort");
  if (sortSelect) sortSelect.addEventListener("change", e => { state.sort = e.target.value; renderCatalog(); });

  const catList = document.getElementById("cat-list");
  if (catList) {
    catList.addEventListener("click", e => {
      const btn = e.target.closest(".cat-filter");
      if (!btn) return;
      state.cat = btn.dataset.cat || "all";
      renderCatalog();
    });
  }

  const resetBtn = document.getElementById("reset-filters");
  if (resetBtn) resetBtn.addEventListener("click", resetFilters);

  document.addEventListener("click", e => {
    const chip = e.target.closest(".chip");
    if (!chip || chip.closest("#cat-list")) return;
    state.cat = chip.dataset.cat || "all";
    renderCatalog();
    const studies = document.getElementById("studies");
    if (studies) studies.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  Array.from(document.querySelectorAll(".clear-all")).forEach(b => {
    b.addEventListener("click", resetFilters);
  });

  const refreshDiscussLinks = () => {
    document.querySelectorAll(".card[id^='study-']").forEach(card => {
      const slug = card.id.slice("study-".length);
      const study = STUDIES.find(s => s.slug === slug);
      if (!study) return;
      const existing = card.querySelector(".discuss-link");
      if (!existing) return;
      const wrap = document.createElement("template");
      wrap.innerHTML = discussLinkHtml(study);
      const next = wrap.content.firstElementChild;
      if (!next || existing.outerHTML === next.outerHTML) return;
      existing.replaceWith(next);
    });
  };

  const START_HERE_STATUS_WORDS = { released: "Released", draft: "Draft", planned: "In progress" };
  const START_HERE_ACTION_WORDS = {
    released: "Discuss this stage",
    draft: "Review the draft",
    planned: "Help develop this study"
  };
  const syncStartHere = studies => {
    const studyBySlug = {};
    (studies || []).forEach(s => { if (s.slug) studyBySlug[s.slug] = s; });
    document.querySelectorAll("#start-here [data-study-slug]").forEach(item => {
      const study = studyBySlug[item.dataset.studySlug];
      if (!study) return;
      const own = sel => Array.from(item.querySelectorAll(sel)).filter(
        el => el.closest("[data-study-slug]") === item
      );

      const status = START_HERE_STATUS_WORDS[study.status] ? study.status : "planned";
      const badge = own("[data-study-status]")[0];
      if (badge) {
        badge.classList.remove("released", "draft", "planned");
        badge.classList.add(status);
        badge.textContent = START_HERE_STATUS_WORDS[status];
      }

      own("[data-study-link]").forEach(studyLink => {
        if (hasReadLinks(study)) {
          studyLink.href = studyHtmlHref(study);
          studyLink.title = "Read the study";
        } else {
          studyLink.href = studyDiscussionHref(study);
          studyLink.title = "Open discussion";
        }
      });

      const slidesLink = own("[data-study-slides]")[0];
      if (slidesLink) {
        const presentationPdf = item.dataset.presentationPdf;
        if (presentationPdf) {
          slidesLink.hidden = false;
          slidesLink.href = `${presentationPdf}?cb=${CATALOG_BUILD_ID}`;
          slidesLink.title = "Open presentation slides";
        } else {
          slidesLink.hidden = true;
        }
      }

      const action = own("[data-study-action]")[0];
      if (action) {
        action.href = studyDiscussionHref(study);
        action.textContent = START_HERE_ACTION_WORDS[status];
      }
    });
  };

  // Support returning from a study's HTML page to the exact card it was opened
  // from (via a `#study-<slug>` hash on the "All studies" link) instead of always
  // landing back at the top of the catalog. Catalog data arrives in stages (inline
  // bootstrap, then a background fetch, then discussion stats), each of which
  // re-renders the grid and would otherwise drop a highlight added on an earlier
  // pass, so re-apply it for a few seconds after load rather than only once.
  let hashStudySlug = null;
  let hashStudyExpiresAt = 0;
  let hashStudyScrolled = false;

  const initHashStudyTarget = () => {
    const match = /^#study-(.+)$/.exec(window.location.hash);
    hashStudySlug = match ? decodeURIComponent(match[1]) : null;
    hashStudyExpiresAt = hashStudySlug ? Date.now() + 4000 : 0;
  };

  const applyHashStudyTarget = () => {
    if (!hashStudySlug) return;
    if (Date.now() > hashStudyExpiresAt) {
      hashStudySlug = null;
      return;
    }
    const target = document.getElementById(`study-${hashStudySlug}`);
    if (!target) {
      // The linked study may be hidden by the current status/collection filter
      // (e.g. its status changed since the link was generated); widen to "all"
      // so it stays reachable, then let the resulting re-render try again.
      if (STUDIES.some(s => s.slug === hashStudySlug) && (state.status !== "all" || state.coll !== "all")) {
        state.status = "all";
        state.coll = "all";
        syncControlsToState();
        renderCatalog();
      }
      return;
    }
    if (!hashStudyScrolled) {
      target.scrollIntoView({ behavior: "auto", block: "center" });
      hashStudyScrolled = true;
    }
    target.classList.add("is-targeted");
    window.setTimeout(() => { target.classList.remove("is-targeted"); }, 1600);
  };

  const bootCatalog = () => {
    updateHeroScope();
    renderCatalog();
    syncStartHere(STUDIES);
  };

  const scheduleCatalogBoot = () => {
    const run = () => {
      readStateFromUrl();
      const boot = parseBootstrap();
      if (boot.length) {
        STUDIES = boot;
        bootCatalog();
      }
      fetchCatalogs().then(fetched => {
        if (fetched) {
          STUDIES = fetched;
          bootCatalog();
        } else if (!boot.length) {
          bootCatalog();
        }
        loadDiscussStats().then(() => {
          if (Object.keys(discussStats).length) refreshDiscussLinks();
        });
      });
    };
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", run, { once: true });
    } else {
      run();
    }
  };

  scheduleCatalogBoot();
})();

(() => {
  const tocLinks = Array.from(document.querySelectorAll("#toc a"));
  const mainSpyIds = ["start-here", "browse-studies", "approach", "contribute", "about"];
  let lockActiveUntil = 0;
  let lockedId = null;

  const scrollMarker = () => {
    const nav = document.querySelector(".page-nav");
    return (nav ? nav.offsetHeight : 0) + 20;
  };

  const syncMobileNavOffset = () => {
    const nav = document.querySelector(".page-nav");
    if (!nav) return;
    const mobileNav = window.matchMedia("(max-width: 820px)").matches;
    if (mobileNav) {
      const height = nav.getBoundingClientRect().height;
      document.documentElement.style.setProperty("--page-nav-offset", `${height}px`);
    } else {
      document.documentElement.style.removeProperty("--page-nav-offset");
    }
  };

  syncMobileNavOffset();
  window.addEventListener("resize", syncMobileNavOffset);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(syncMobileNavOffset);
  }

  const setActive = id => {
    tocLinks.forEach(a => {
      const match = a.getAttribute("href") === `#${id}`;
      a.classList.toggle("active", match);
      if (match) {
        a.setAttribute("aria-current", "true");
      } else {
        a.removeAttribute("aria-current");
      }
    });
  };

  const updateActiveFromScroll = () => {
    if (lockedId && Date.now() < lockActiveUntil) {
      setActive(lockedId);
      return;
    }

    const marker = scrollMarker();
    let currentId = "topical-studies";

    mainSpyIds.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.getBoundingClientRect().top <= marker) {
        currentId = id;
      }
    });

    setActive(currentId);
  };

  let scrollTick = false;
  const onScroll = () => {
    if (scrollTick) return;
    scrollTick = true;
    window.requestAnimationFrame(() => {
      scrollTick = false;
      updateActiveFromScroll();
    });
  };

  tocLinks.forEach(link => {
    link.addEventListener("click", () => {
      const href = link.getAttribute("href");
      if (!href || href.charAt(0) !== "#") return;
      const id = href.slice(1);
      lockedId = id;
      lockActiveUntil = Date.now() + 1500;
      setActive(id);
      const target = document.getElementById(id);
      if (target) {
        target.classList.add("is-targeted");
        window.setTimeout(() => { target.classList.remove("is-targeted"); }, 1600);
      }
    });
  });

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", updateActiveFromScroll);
  updateActiveFromScroll();
})();
</script>
</body>
</html>
"""


def minify_inline_css(html: str) -> str:
    """Collapse whitespace in the first inline <style> block for a smaller catalog page."""

    def _minify(match: re.Match[str]) -> str:
        css = match.group(1)
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        css = re.sub(r"\s+", " ", css)
        # Keep whitespace around + so calc() stays valid (calc(a + b) requires spaces).
        css = re.sub(r"\s*([{}:;,>~])\s*", r"\1", css)
        return f"<style>\n{css.strip()}\n</style>"

    return re.sub(r"<style>(.*?)</style>", _minify, html, count=1, flags=re.DOTALL)


def load_rows_for_build(legacy_index_text: str, table: StudyTable) -> list:
    if catalog_json_path(table).is_file():
        return parse_catalog_json_file(table)
    if legacy_index_text:
        return parse_catalog_json(legacy_index_text, table)
    return []


def serialize_catalog_bootstrap_json(
    topical_rows: list,
    formal_rows: list,
    applied_rows: list,
) -> str:
    payload = {
        "topical": catalog_json_payload(topical_rows),
        "formal": catalog_json_payload(formal_rows),
        "applied": catalog_json_payload(applied_rows),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_hero_scope_html(rows: list) -> str:
    total = len(rows)
    available = sum(
        1 for row in rows if row.status in (StudyStatus.DRAFT, StudyStatus.RELEASED)
    )
    categories: set[str] = set()
    for row in rows:
        categories.update(split_categories(row.category))
    topic_count = len(categories)
    return (
        f"<strong>{available} of {total}</strong> studies available &middot; "
        f"<strong>{topic_count}</strong> topics &middot; open &amp; independent"
    )


# Kept byte-for-byte in sync with the JavaScript `PDF_DOWNLOAD_ICON` in INDEX_TEMPLATE
# so the pre-rendered cards and the client re-render produce identical markup.
PDF_DOWNLOAD_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path fill="currentColor" d="M12 3a1 1 0 0 1 1 1v9.59l2.3-2.3a1 1 0 1 1 1.4 1.42l-4 4a1 1 0 0 1-1.4 0l-4-4a1 1 0 1 1 1.4-1.42l2.3 2.3V4a1 1 0 0 1 1-1Zm-7 14a1 1 0 0 1 1 1v1h12v-1a1 1 0 1 1 2 0v2a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1Z"/>'
    "</svg>"
)


def _card_esc_attr(value: str) -> str:
    """Mirror the JavaScript `escAttr` helper in INDEX_TEMPLATE."""
    return str(value).replace('"', "&quot;").replace("<", "&lt;")


def _card_version_query(row: StudyRow) -> str:
    """Match the JS `pdfVersionQuery`: `?v=<epoch-ms>` from the `Edited on` time.

    The client parses the catalog `updated` string reformatted to `GMT+0530`; the
    tz-aware IST ``edited_at`` produces the same epoch milliseconds.
    """
    if row.edited_at is None:
        return ""
    return f"?v={int(row.edited_at.timestamp() * 1000)}"


def _card_html_href(entry: dict, version_query: str) -> str:
    base = entry.get("html")
    if not base:
        pdf = entry.get("pdf")
        if pdf:
            base = re.sub(r"\.pdf$", ".html", pdf, flags=re.IGNORECASE)
        else:
            base = f"{entry['slug']}/{entry['slug']}.html"
    return f"{base}{version_query}"


def _card_pdf_href(entry: dict, version_query: str) -> str:
    base = entry.get("pdf") or f"{entry['slug']}/{entry['slug']}.pdf"
    return f"{base}{version_query}"


def _card_discussion_href(entry: dict, version_query: str) -> str:
    base = entry.get("discussion") or f"{entry['slug']}/discussion.html"
    if not DISCUSS_ASSET_VERSION:
        return f"{base}{version_query}"
    sep = "&" if version_query else "?"
    return f"{base}{version_query}{sep}dv={DISCUSS_ASSET_VERSION}"


_UPDATED_DATE_RE = re.compile(r"^([A-Za-z]+\s+\d{1,2},\s*\d{4})")


def _updated_date_only(updated: str | None) -> str:
    """Drop the time from a catalog card's "Updated" line.

    Several studies share an edit date, so minute precision became the only
    thing telling their cards apart without being anything a reader wants. The
    full stamp is kept in the catalog data for sorting and the PDF
    cache-buster, and on the study page itself.
    """
    if not updated:
        return ""
    match = _UPDATED_DATE_RE.match(str(updated))
    return match.group(1) if match else str(updated)


def _card_discuss_link_html(entry: dict, version_query: str) -> str:
    """Initial (pre-stats) discussion link: no comment count badge, matching the
    JS `discussLinkHtml` before `/api/discussions/stats` resolves."""
    href = _card_discussion_href(entry, version_query)
    title = entry["title"]
    return (
        f'<a class="discuss-link" href="{href}" title="Discussion board" '
        f'aria-label="Discuss {_card_esc_attr(title)}">Discuss'
        f'<span class="discuss-badge discuss-badge--empty" aria-hidden="true"></span></a>'
    )


def _render_catalog_card(row: StudyRow, entry: dict) -> str:
    """Reproduce the JS `cardHTML` for an available (draft/released) study so the
    server-rendered card and the client re-render have identical layout height."""
    version_query = _card_version_query(row)
    status = entry["status"]
    released = status == "released"
    card_class = "is-released is-available" if released else "is-draft is-available"
    badge_class = "released" if released else "draft"
    badge_label = "Released" if released else "Draft"
    draft_title = ' title="Draft PDF includes a watermark"' if status == "draft" else ""

    title = entry["title"]
    title_inner = f'<a href="{_card_html_href(entry, version_query)}">{title}</a>'
    chips = "".join(
        f'<button type="button" class="chip" data-cat="{c.replace(chr(34), "&quot;")}">{c}</button>'
        for c in entry["categories"]
    )
    read_actions = (
        f'<a class="pdf-download" href="{_card_pdf_href(entry, version_query)}" download '
        f'title="Download PDF" aria-label="Download PDF for {_card_esc_attr(title)}">'
        f"{PDF_DOWNLOAD_ICON}</a>"
    )
    foot = (
        f'<span class="badge {badge_class}"{draft_title}>'
        f'<span class="badge-dot"></span>{badge_label}</span>'
        f'<span class="card-actions">'
        f"{_card_discuss_link_html(entry, version_query)}{read_actions}</span>"
    )
    updated = _updated_date_only(entry.get("updated"))
    date_line = (
        f'<div class="card-foot" style="border:none;padding:6px 0 0;color:#9a8f80;">'
        f"Updated {updated}</div>"
        if updated
        else ""
    )
    return (
        f'<li class="card {card_class}" id="study-{_card_esc_attr(entry["slug"])}">\n'
        f'      <h3 class="card-title">{title_inner}</h3>\n'
        f'      <div class="chips">{chips}</div>\n'
        f'      <p class="card-desc">{entry["description"]}</p>\n'
        f'      <div class="card-foot">{foot}</div>{date_line}</li>'
    )


def render_catalog_cards(rows: list[StudyRow]) -> str:
    """Render the default-visible (status "available") cards for one collection,
    in catalog-file order to match the client's stable "recently updated" sort."""
    parts: list[str] = []
    for row in rows:
        if row.status not in (StudyStatus.DRAFT, StudyStatus.RELEASED):
            continue
        parts.append(_render_catalog_card(row, row_to_catalog_entry(row)))
    return "".join(parts)


def inject_catalog_cards(html: str, rows_by_coll: dict[str, list[StudyRow]]) -> str:
    """Pre-render the default catalog cards into the empty grids so the first paint
    reserves their height (eliminating the JS-fill layout shift).

    The grid ``<ul>`` is located by its ``id`` (tolerant of attribute order and
    whitespace) rather than an exact string, and a missing target raises instead
    of silently skipping pre-rendering if INDEX_TEMPLATE markup changes.
    """
    for coll, rows in rows_by_coll.items():
        cards = render_catalog_cards(rows)
        pattern = re.compile(
            rf'(<ul\b[^>]*\bid="grid-{re.escape(coll)}"[^>]*>).*?(</ul>)',
            flags=re.DOTALL,
        )
        # A replacement function avoids re-interpreting backslashes/group refs in card markup.
        html, replaced = pattern.subn(
            lambda m: f"{m.group(1)}{cards}{m.group(2)}", html, count=1
        )
        if not replaced:
            raise ValueError(
                f'Could not find grid container id="grid-{coll}" in INDEX_TEMPLATE '
                "to inject pre-rendered catalog cards."
            )
    return html


def strip_grid_contents(content: str) -> str:
    """Blank the pre-rendered catalog cards so shell verification compares only the
    static template markup (cards are build-time data, like the catalog bootstrap).

    Matches every catalog grid container (``id="grid-*"``, tolerant of attribute
    order) so verification stays aligned as collections are added or reordered.
    """
    return re.sub(
        r'(<ul\b[^>]*\bid="grid-[^"]+"[^>]*>).*?(</ul>)',
        r"\1\2",
        content,
        flags=re.DOTALL,
    )


def normalize_shell_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.splitlines()).strip() + "\n"


def strip_build_time_data(content: str) -> str:
    result = re.sub(
        r'(<script type="application/json" id="catalog-bootstrap">)\s*.*?\s*(</script>)',
        rf"\1\n{CATALOG_BOOTSTRAP_PLACEHOLDER}\n\2",
        content,
        count=1,
        flags=re.DOTALL,
    )
    result = re.sub(
        r'const CATALOG_BUILD_ID = "[^"]*";',
        f'const CATALOG_BUILD_ID = "{CATALOG_BUILD_ID_PLACEHOLDER}";',
        result,
        count=1,
    )
    result = re.sub(
        r'const DISCUSS_ASSET_VERSION = "[^"]*";',
        f'const DISCUSS_ASSET_VERSION = "{DISCUSS_ASSET_VERSION_PLACEHOLDER}";',
        result,
        count=1,
    )
    # Start-here pills are written from the catalog by render_start_here_status(),
    # so they are build-time data like the cards and the bootstrap. Blank them on
    # both sides; verify_start_here_sync() checks them against the catalog.
    result = re.sub(
        PILL_STATUS_SUB_RE,
        PILL_STATUS_SUB_REPL,
        result,
    )
    return re.sub(
        r'(<p class="scope" id="hero-scope">).*?(</p>)',
        rf"\1{HERO_SCOPE_PLACEHOLDER}\2",
        result,
        count=1,
        flags=re.DOTALL,
    )


def strip_catalog_blocks(content: str) -> str:
    result = content
    for table in StudyTable:
        start, end = catalog_markers(table)
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
        if pattern.search(result):
            result = pattern.sub(f"{start}\n{CATALOG_SHELL_PLACEHOLDER}\n{end}", result, count=1)
    return result


def start_here_status_key(status) -> str:
    """Catalog status -> Start-here pill key, exactly as syncStartHere() does it.

    The script falls back to "planned" for anything it has no word for, which is
    how `ongoing` renders as "In progress". Keep this fallback identical.
    """
    key = getattr(status, "value", status)
    return key if key in START_HERE_STATUS_WORDS else "planned"


def render_start_here_status(html: str, rows: list[StudyRow]) -> str:
    """Write each Start-here pill from the catalog.

    These pills used to be hand-maintained literals in INDEX_TEMPLATE, and two of
    the 23 had drifted: a released study still advertised Draft, and a draft study
    still advertised In progress. syncStartHere() repaired them on load, so the
    drift was invisible in a browser and wrong everywhere else -- first paint, and
    any reader of the HTML that does not run scripts.
    """
    status_by_slug = {row.slug: start_here_status_key(row.status) for row in rows}

    def rewrite(match: re.Match) -> str:
        head, slug, _cls, mid, _label, tail = match.groups()
        key = status_by_slug.get(slug)
        if key is None:
            # Unknown slug: leave the markup alone, matching syncStartHere(),
            # which returns early when the catalog has no such study.
            return match.group(0)
        return f"{head}{key}{mid}{START_HERE_STATUS_WORDS[key]}{tail}"

    return START_HERE_PILL_RE.sub(rewrite, html)


def verify_start_here_sync() -> list[str]:
    """Ensure the Start-here pills still match catalog-*.json.

    strip_build_time_data() blanks these pills before the shell comparison, so
    verify_index_shell_sync() can no longer see them. This is the check that
    takes over -- without it, blanking them would remove the only guard.
    """
    index_path = STUDIES / "index.html"
    if not index_path.exists():
        return ["Studies/index.html is missing."]

    status_by_slug = {}
    for table in StudyTable:
        for row in parse_catalog_json_file(table):
            status_by_slug[row.slug] = start_here_status_key(row.status)

    errors = []
    for match in START_HERE_PILL_RE.finditer(index_path.read_text(encoding="utf-8")):
        _head, slug, cls, _mid, label, _tail = match.groups()
        expected = status_by_slug.get(slug)
        if expected is None:
            continue
        if cls != expected or label != START_HERE_STATUS_WORDS[expected]:
            errors.append(
                f"Studies/index.html: Start-here pill for {slug} says "
                f"{cls}/{label!r}, catalog says {expected}/"
                f"{START_HERE_STATUS_WORDS[expected]!r}. "
                "Run python Scripts/_build_studies_index.py."
            )
    return errors


def verify_catalog_bootstrap_sync() -> list[str]:
    """Ensure the inlined bootstrap matches the catalog JSON fetched at runtime.

    index.html paints its cards from the inlined island and then rehydrates from
    catalog-*.json. verify_index_shell_sync deliberately strips the island, so
    nothing else compares the two: they drifted apart once already, and a
    planned study rendered with a PDF link until rehydration removed it.
    """
    index_path = STUDIES / "index.html"
    if not index_path.exists():
        return ["Studies/index.html is missing."]

    match = re.search(
        r'<script type="application/json" id="catalog-bootstrap">\s*(.*?)\s*</script>',
        index_path.read_text(encoding="utf-8"),
        flags=re.DOTALL,
    )
    if match is None:
        return ["Studies/index.html: catalog bootstrap island not found."]

    expected = serialize_catalog_bootstrap_json(
        parse_catalog_json_file(StudyTable.TOPICAL),
        parse_catalog_json_file(StudyTable.FORMAL),
        parse_catalog_json_file(StudyTable.APPLIED),
    ).replace("</", "<\\/")
    if match.group(1) != expected:
        return [
            "Studies/index.html: inlined catalog bootstrap does not match "
            "catalog-*.json. Run python Scripts/_build_studies_index.py."
        ]
    return []


def verify_index_shell_sync() -> list[str]:
    """Ensure Studies/index.html shell matches INDEX_TEMPLATE (catalog JSON excluded)."""
    index_path = STUDIES / "index.html"
    if not index_path.exists():
        return ["Studies/index.html is missing."]

    actual = normalize_shell_text(
        strip_build_time_data(
            strip_catalog_blocks(strip_grid_contents(index_path.read_text(encoding="utf-8")))
        )
    )
    expected = normalize_shell_text(
        strip_build_time_data(
            strip_catalog_blocks(strip_grid_contents(minify_inline_css(INDEX_TEMPLATE)))
        )
    )

    if actual != expected:
        return [
            "Studies/index.html landing-page shell differs from "
            "Scripts/_build_studies_index.py INDEX_TEMPLATE. "
            "Edit INDEX_TEMPLATE, then run: python Scripts/_build_studies_index.py"
        ]
    return []


def catalog_build_id() -> str:
    """Cache-buster for the catalog JSON and the presentation PDFs.

    Derived from the content it busts, not from git HEAD. Keying it on
    `git rev-parse HEAD` meant the value changed on every commit, so rebuilding
    the index on a clean tree always rewrote Studies/index.html -- breaking the
    invariant in AGENTS.md §2 that a no-change rebuild produces no diff, and
    making it easy to commit incidental churn without noticing. It was also a
    poor cache key in both directions: a commit that touched nothing cacheable
    still busted every reader's cache, while a deck rebuilt without a commit
    busted nothing.

    Hashing the bytes fixes both. The value changes exactly when a cached
    resource changes, and two builds of the same content agree.
    """
    digest = hashlib.sha256()
    for table in CATALOG_TABLES:
        path = catalog_json_path(table)
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes() if path.is_file() else b"")
    # Slides are served with this same query, so their content has to feed it or
    # a deck update would never reach a reader holding a cached copy.
    for pdf in sorted(_presentation_pdf_paths()):
        digest.update(pdf.relative_to(BASE).as_posix().encode("utf-8"))
        digest.update(pdf.read_bytes())
    return digest.hexdigest()[:12]


def _presentation_pdf_paths() -> list[Path]:
    """Presentation PDFs the index links, taken from the template itself."""
    paths = []
    for rel in re.findall(r'data-presentation-pdf="([^"]+)"', INDEX_TEMPLATE):
        candidate = STUDIES / rel
        if candidate.is_file():
            paths.append(candidate)
    return paths


INDEX_TEMPLATE = INDEX_TEMPLATE.replace(FAVICON_LINKS_PLACEHOLDER, favicon_link_tags())


def write_index_html() -> dict[str, list[StudyRow]] | None:
    """Render Studies/index.html from the catalog rows currently on disk.

    Split out of main() so write_studies_catalog() can call it. Studies/index.html
    inlines the catalog as a JSON island and renders a card per row, so any path
    that edits a catalog row must refresh it too; when _set_study_status.py did
    not, the landing page kept advertising a released study as Draft and only the
    master-push check noticed (#343).

    Writes nothing but index.html, in particular no catalog JSON, so the call
    from write_studies_catalog() cannot recurse back into this function.

    Returns the rows per collection, or None when no catalog rows exist at all.
    """
    index_path = STUDIES / "index.html"
    legacy_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    topical_rows = load_rows_for_build(legacy_text, StudyTable.TOPICAL)
    formal_rows = load_rows_for_build(legacy_text, StudyTable.FORMAL)
    applied_rows = load_rows_for_build(legacy_text, StudyTable.APPLIED)

    if not topical_rows and not formal_rows and not applied_rows:
        return None

    all_rows = topical_rows + formal_rows + applied_rows
    html = INDEX_TEMPLATE.replace(HERO_SCOPE_PLACEHOLDER, build_hero_scope_html(all_rows))
    html = html.replace(CATALOG_BUILD_ID_PLACEHOLDER, catalog_build_id())
    html = html.replace(DISCUSS_ASSET_VERSION_PLACEHOLDER, DISCUSS_ASSET_VERSION)
    bootstrap_json = serialize_catalog_bootstrap_json(topical_rows, formal_rows, applied_rows)
    # Guard against premature </script> termination inside the inlined JSON island.
    bootstrap_json = bootstrap_json.replace("</", "<\\/")
    html = html.replace(CATALOG_BOOTSTRAP_PLACEHOLDER, bootstrap_json)
    html = inject_catalog_cards(
        html,
        {"topical": topical_rows, "formal": formal_rows, "applied": applied_rows},
    )
    html = render_start_here_status(html, all_rows)
    write_text_lf(index_path, minify_inline_css(html))
    return {"topical": topical_rows, "formal": formal_rows, "applied": applied_rows}


def main() -> int:
    from _study_catalog import sync_pre_catalog_proposals_to_catalog

    # rebuild_index=False here and on the writes below: this function rebuilds
    # index.html itself, once, from the fully synced rows.
    sync_pre_catalog_proposals_to_catalog(rebuild_index=False)

    rows_by_collection = write_index_html()
    if rows_by_collection is None:
        print("No catalog rows found in index.html or catalog JSON files", file=sys.stderr)
        return 1
    print("Wrote Studies/index.html shell with inlined catalog bootstrap (and catalog-*.json for runtime refresh).")

    topical_rows = rows_by_collection["topical"]
    formal_rows = rows_by_collection["formal"]
    applied_rows = rows_by_collection["applied"]

    if topical_rows:
        write_studies_catalog(
            topical_rows,
            StudyTable.TOPICAL,
            rebuild_discussion=False,
            rebuild_feedback_template=False,
            rebuild_index=False,
        )
        print(f"Wrote {len(topical_rows)} topical catalog entries to catalog-topical.json.")
    if formal_rows:
        write_studies_catalog(
            formal_rows,
            StudyTable.FORMAL,
            rebuild_discussion=False,
            rebuild_feedback_template=False,
            rebuild_index=False,
        )
        print(f"Wrote {len(formal_rows)} formal catalog entries to catalog-formal.json.")
    if applied_rows:
        write_studies_catalog(
            applied_rows,
            StudyTable.APPLIED,
            rebuild_discussion=False,
            rebuild_feedback_template=False,
            rebuild_index=False,
        )
        print(f"Wrote {len(applied_rows)} applied catalog entries to catalog-applied.json.")

    if STUDY_FEEDBACK_TEMPLATE_PATH.is_file():
        print(
            f"Wrote study feedback template to "
            f"{STUDY_FEEDBACK_TEMPLATE_PATH.relative_to(BASE)}."
        )

    from _build_sitemap import write_sitemap

    sitemap_path = write_sitemap()
    print(f"Wrote sitemap to {sitemap_path.relative_to(BASE)}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

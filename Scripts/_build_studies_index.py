#!/usr/bin/env python3
"""Write Studies/index.html landing page shell and external catalog JSON files."""
from __future__ import annotations

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
from _common import BASE, STUDIES  # noqa: E402
from _study_catalog import (  # noqa: E402
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

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Studies of Madhyasth Darshan</title>
<meta name="description" content="An open comparative study of Madhyasth Darshan, following a path from the human question through existence, knowledge, value, lived participation, and formal synthesis."/>
<meta name="color-scheme" content="light dark"/>
<link rel="canonical" href="https://analyticmadhyasthdarshan.org/Studies/index.html"/>
<meta property="og:type" content="website"/>
<meta property="og:site_name" content="AnalyticMadhyasthDarshan.org"/>
<meta property="og:title" content="Studies of Madhyasth Darshan"/>
<meta property="og:description" content="An open comparative study of Madhyasth Darshan, following a path through existence, knowledge, value, lived participation, and formal synthesis."/>
<meta property="og:url" content="https://analyticmadhyasthdarshan.org/Studies/index.html"/>
<meta name="twitter:card" content="summary"/>
<meta name="twitter:title" content="Studies of Madhyasth Darshan"/>
<meta name="twitter:description" content="An open comparative study of Madhyasth Darshan, following a path through existence, knowledge, value, lived participation, and formal synthesis."/>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"CollectionPage","name":"Studies of Madhyasth Darshan","description":"An open comparative study of Madhyasth Darshan, following a path from the human question through existence, knowledge, value, lived participation, and formal synthesis.","url":"https://analyticmadhyasthdarshan.org/Studies/index.html","isPartOf":{"@type":"WebSite","name":"AnalyticMadhyasthDarshan.org","url":"https://analyticmadhyasthdarshan.org/"},"license":"https://creativecommons.org/licenses/by/4.0/"}
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

  .dialogue {
    margin: 0 0 6px;
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
  .dialogue li:first-child span { color: var(--accent); }

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
    display: flex; flex-wrap: wrap; align-items: center; gap: 10px;
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
    flex: 0 0 auto; margin-left: auto;
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
    color: var(--text-muted);
    max-width: 920px;
    margin: 0 0 20px;
  }
  .study-path {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 12px;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .path-stage {
    display: flex;
    flex-direction: column;
    min-width: 0;
    padding: 15px 14px 13px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent);
    border-radius: 10px;
  }
  .path-stage-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
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
  .path-stage h3 {
    font-size: 17px;
    line-height: 1.3;
    margin: 0 0 8px;
  }
  .path-stage-desc {
    font-size: 13px;
    line-height: 1.48;
    color: var(--text-muted);
    margin: 0 0 14px;
  }
  .path-core {
    margin-top: auto;
    padding-top: 11px;
    border-top: 1px solid var(--border);
  }
  .path-core-label {
    display: block;
    margin-bottom: 4px;
    font-family: var(--sans);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
  }
  .path-study-line {
    line-height: 1.35;
  }
  .path-study-line a {
    font-size: 13px;
    font-weight: 700;
  }
  .path-status {
    display: inline-flex;
    align-items: center;
    margin: 5px 0 0;
    border-radius: 999px;
    padding: 2px 8px;
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 700;
  }
  .path-status.released { color: #1b4332; background: #d8f3dc; }
  .path-status.draft { color: #92400e; background: #fef3c7; }
  .path-status.planned { color: var(--warm); background: var(--warm-soft); }
  .path-updated {
    display: block;
    min-height: 16px;
    margin-top: 4px;
    font-family: var(--sans);
    font-size: 10px;
    color: var(--text-muted);
  }
  .path-action {
    display: inline-block;
    margin-top: 8px;
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 700;
  }
  .path-related {
    margin-top: 10px;
    font-family: var(--sans);
    font-size: 11px;
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
  }
  .path-related li {
    padding: 6px 0;
    border-top: 1px solid var(--border);
    line-height: 1.3;
  }
  .path-related li a { font-weight: 600; }
  .path-related .path-status {
    margin: 3px 0 0;
    padding: 1px 7px;
    font-size: 9px;
  }
  .parallel-track {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(260px, 0.55fr);
    gap: 18px;
    align-items: center;
    margin-top: 14px;
    padding: 16px 18px;
    background: var(--warm-soft);
    border: 1px solid #e0d0be;
    border-radius: 10px;
  }
  .parallel-track-label {
    display: block;
    margin-bottom: 4px;
    font-family: var(--sans);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--warm);
  }
  .parallel-track h3 {
    font-size: 17px;
    margin: 0 0 5px;
  }
  .parallel-track p {
    margin: 0;
    font-size: 13px;
    color: var(--text-muted);
  }
  .parallel-studies {
    display: grid;
    gap: 8px;
    font-family: var(--sans);
    font-size: 12px;
  }
  .parallel-study {
    padding: 8px 10px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  .parallel-study a { font-weight: 700; }
  .parallel-study .path-status { margin-left: 5px; }
  .path-invitation {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
  }
  .path-invitation p {
    margin: 0;
    font-size: 13px;
    color: var(--text-muted);
  }
  .path-invitation strong { color: var(--text); }
  .path-invitation-actions {
    display: flex;
    flex: 0 0 auto;
    gap: 8px;
  }
  .path-invitation .btn-primary,
  .path-invitation .btn-secondary {
    padding: 8px 13px;
    font-size: 12px;
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
  [data-theme="dark"] .path-stage { background: #1e1b18; }
  [data-theme="dark"] .path-status.released { color: #8fd4a8; background: #1a2e22; }
  [data-theme="dark"] .path-status.draft { color: #f0c78a; background: #3a2818; }
  [data-theme="dark"] .parallel-track { border-color: #5a4632; }
  [data-theme="dark"] .parallel-study { background: #26231e; }
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

  @media (max-width: 1000px) {
    .study-path { grid-template-columns: repeat(3, minmax(0, 1fr)); }
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
    .section { scroll-margin-top: calc(var(--page-nav-offset, 56px) + 12px); }
    .catalog-group { scroll-margin-top: calc(var(--page-nav-offset, 56px) + 12px); }
    .browse-heading { scroll-margin-top: calc(var(--page-nav-offset, 56px) + 12px); }
    .card { scroll-margin-top: calc(var(--page-nav-offset, 56px) + 12px); }
    h1 { font-size: 30px; }
    .triad { grid-template-columns: 1fr; }
    .study-path { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .parallel-track { grid-template-columns: 1fr; }
    .path-invitation { align-items: flex-start; flex-direction: column; }
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
    .study-path { grid-template-columns: 1fr; }
    .path-stage { padding: 15px; }
    .path-invitation-actions { width: 100%; flex-direction: column; }
    .path-invitation .btn-primary, .path-invitation .btn-secondary { text-align: center; }
  }
</style>
</head>
<body>
<div class="page">

<header class="hero">
  <h1>Studies of Madhyasth Darshan</h1>
  <p class="lead">An open and growing collection of comparative studies of <strong>Madhyasth Darshan</strong> (Co-existentialism), the philosophy founded by <strong>Shri A. Nagraj</strong>. The collection follows a personal path of inquiry while inviting others to examine its arguments, question its interpretations, and contribute to its development.</p>

  <ul class="dialogue" aria-label="Each study is read in dialogue with">
    <li><span>Madhyasth Darshan</span></li>
    <li><span>Sciences &amp; technology</span></li>
    <li><span>Advaita Vedanta</span></li>
    <li><span>Modern philosophy</span></li>
  </ul>

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
      <li><a href="submit.html">My Submissions</a></li>
    </ul>
    <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Switch color theme">
      <span class="theme-toggle-icon" id="theme-toggle-icon" aria-hidden="true">&#9789;</span>
      <span id="theme-toggle-label">Dark</span>
    </button>
  </div>
</nav>
<div class="page-nav-anchor" aria-hidden="true"></div>

<main>

<section class="section" id="studies">

  <noscript>
    <p class="section-intro">JavaScript is required for search and filters on this page. Browse the full catalog in <a href="README.md">Studies/README.md</a>.</p>
  </noscript>

  <div class="start-here" id="start-here">
    <p class="start-here-kicker">A guided path through the collection</p>
    <h2>Start here: the study path I am following</h2>
    <p class="start-here-intro">This collection records the path I am taking: beginning with the question of what a human is, then moving through existence, knowledge, value, and lived participation. You are welcome to follow the same sequence, question it, and contribute wherever the work is incomplete.</p>

    <ol class="study-path" aria-label="Five stages in the study path">
      <li class="path-stage">
        <div class="path-stage-head"><span class="path-number">1</span><span class="path-domain">Human</span></div>
        <h3>Is a human only a body?</h3>
        <p class="path-stage-desc">Test whether a human is exhausted by the body by comparing scientific accounts and their physicalist interpretation with Advaita Vedanta and Madhyasth Darshan.</p>
        <div class="path-core" data-study-slug="Why-Humans-Are-Not-Just-Material" data-presentation-pdf="Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material-presentation.pdf">
          <span class="path-core-label">Core study</span>
          <div class="path-study-line"><a data-study-link href="Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material-presentation.pdf" title="Open presentation PDF">Why Humans Are Not Just Material</a></div>
          <span class="path-status released" data-study-status>Released</span>
          <span class="path-updated" data-study-updated></span>
          <a class="path-action" data-study-action href="Why-Humans-Are-Not-Just-Material/discussion.html">Discuss this stage</a>
        </div>
        <details class="path-related">
          <summary>3 related studies</summary>
          <ul>
            <li data-study-slug="Philosophy-Of-Mind-And-Jeevan"><a data-study-link href="Philosophy-Of-Mind-And-Jeevan/discussion.html">Philosophy of Mind and Jeevan</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="Chitta-Brain-And-Memory"><a data-study-link href="Chitta-Brain-And-Memory/discussion.html">Chitta, Brain, and Memory</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="Death-Continuity-And-Rebirth"><a data-study-link href="Death-Continuity-And-Rebirth/discussion.html">Death, Continuity, and Rebirth</a><br><span class="path-status planned" data-study-status>In progress</span></li>
          </ul>
        </details>
      </li>

      <li class="path-stage">
        <div class="path-stage-head"><span class="path-number">2</span><span class="path-domain">Existence</span></div>
        <h3>What exists&mdash;and what are we?</h3>
        <p class="path-stage-desc">Examine coexistence, units, and nature&rsquo;s orders, including Madhyasth Darshan&rsquo;s claim that the human belongs to the knowledge order.</p>
        <div class="path-core" data-study-slug="The-Ontology-of-Coexistence" data-presentation-pdf="The-Ontology-of-Coexistence/The-Ontology-of-Existence-Madhyasth-Darshan.pdf">
          <span class="path-core-label">Core study</span>
          <div class="path-study-line"><a data-study-link href="The-Ontology-of-Coexistence/The-Ontology-of-Existence-Madhyasth-Darshan.pdf" title="Open presentation PDF">The Ontology of Coexistence</a></div>
          <span class="path-status released" data-study-status>Released</span>
          <span class="path-updated" data-study-updated></span>
          <a class="path-action" data-study-action href="The-Ontology-of-Coexistence/discussion.html">Discuss this stage</a>
        </div>
        <details class="path-related">
          <summary>3 related studies</summary>
          <ul>
            <li data-study-slug="Nature-Of-Time"><a data-study-link href="Nature-Of-Time/Nature-Of-Time.html">Nature of Time</a><br><span class="path-status released" data-study-status>Released</span></li>
            <li data-study-slug="Nature-Ecology-And-Right-Use"><a data-study-link href="Nature-Ecology-And-Right-Use/discussion.html">Nature, Ecology, and Right Use</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="God-Divinity-And-The-Sacred"><a data-study-link href="God-Divinity-And-The-Sacred/discussion.html">God, Divinity, and the Sacred</a><br><span class="path-status planned" data-study-status>In progress</span></li>
          </ul>
        </details>
      </li>

      <li class="path-stage">
        <div class="path-stage-head"><span class="path-number">3</span><span class="path-domain">Knowledge</span></div>
        <h3>What must the knower know?</h3>
        <p class="path-stage-desc">Ask what knowledge is, what must be known, and how understanding of coexistence and humane conduct guides action toward lasting fulfilment.</p>
        <div class="path-core" data-study-slug="Knowledge-Knower-And-Known" data-presentation-pdf="Knowledge-Knower-And-Known/The-Epistemology-of-Coexistence-Madhyasth-Darshan.pdf">
          <span class="path-core-label">Core study</span>
          <div class="path-study-line"><a data-study-link href="Knowledge-Knower-And-Known/The-Epistemology-of-Coexistence-Madhyasth-Darshan.pdf" title="Open presentation PDF">Knowledge Knower and Known</a></div>
          <span class="path-status released" data-study-status>Released</span>
          <span class="path-updated" data-study-updated></span>
          <a class="path-action" data-study-action href="Knowledge-Knower-And-Known/discussion.html">Discuss this stage</a>
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
      </li>

      <li class="path-stage">
        <div class="path-stage-head"><span class="path-number">4</span><span class="path-domain">Value</span></div>
        <h3>What makes value and relationship definite?</h3>
        <p class="path-stage-desc">Study whether values and relationships have a definite structure, and how understanding is tested and deepened through conduct.</p>
        <div class="path-core" data-study-slug="Axiology-Value-Theory">
          <span class="path-core-label">Core study</span>
          <div class="path-study-line"><a data-study-link href="Axiology-Value-Theory/discussion.html">Axiology Value Theory</a></div>
          <span class="path-status planned" data-study-status>In progress</span>
          <span class="path-updated" data-study-updated></span>
          <a class="path-action" data-study-action href="Axiology-Value-Theory/discussion.html">Help develop this study</a>
        </div>
        <details class="path-related">
          <summary>3 related studies</summary>
          <ul>
            <li data-study-slug="Ethics-And-Morals-In-Human-Beings"><a data-study-link href="Ethics-And-Morals-In-Human-Beings/Ethics-And-Morals-In-Human-Beings.html">Ethics and Morals in Human Beings</a><br><span class="path-status draft" data-study-status>Draft</span></li>
            <li data-study-slug="Family-Relationships-And-Values"><a data-study-link href="Family-Relationships-And-Values/discussion.html">Family Relationships and Values</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="Aesthetics"><a data-study-link href="Aesthetics/Aesthetics.html">Aesthetics</a><br><span class="path-status draft" data-study-status>Draft</span></li>
          </ul>
        </details>
      </li>

      <li class="path-stage">
        <div class="path-stage-head"><span class="path-number">5</span><span class="path-domain">Living</span></div>
        <h3>How is coexistence lived?</h3>
        <p class="path-stage-desc">Begin with family and extend participation through education, society, governance, economy, ecology, and spiritual practice. This widening participation is where understanding is tested in living.</p>
        <div class="path-core" data-study-slug="How-Undivided-Society-Is-Established" data-presentation-pdf="How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established-presentation.pdf">
          <span class="path-core-label">Current anchor</span>
          <div class="path-study-line"><a data-study-link href="How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established-presentation.pdf" title="Open presentation PDF">How Undivided Society Is Established</a></div>
          <span class="path-status released" data-study-status>Released</span>
          <span class="path-updated" data-study-updated></span>
          <a class="path-action" data-study-action href="How-Undivided-Society-Is-Established/discussion.html">Discuss this stage</a>
        </div>
        <details class="path-related">
          <summary>8 related studies</summary>
          <ul>
            <li data-study-slug="Family-Relationships-And-Values"><a data-study-link href="Family-Relationships-And-Values/discussion.html">Family Relationships and Values</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="Education-And-Sanskar"><a data-study-link href="Education-And-Sanskar/discussion.html">Education and Sanskar</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="Human-Behavior-And-Society"><a data-study-link href="Human-Behavior-And-Society/Human-Behavior-And-Society.html">Human Behavior and Society</a><br><span class="path-status draft" data-study-status>Draft</span></li>
            <li data-study-slug="Governance-Justice-And-Undivided-Society"><a data-study-link href="Governance-Justice-And-Undivided-Society/discussion.html">Governance, Justice, and Undivided Society</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="Prosperity-Economics-And-Right-Use"><a data-study-link href="Prosperity-Economics-And-Right-Use/discussion.html">Prosperity, Economics, and Right Use</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="Nature-Ecology-And-Right-Use"><a data-study-link href="Nature-Ecology-And-Right-Use/discussion.html">Nature, Ecology, and Right Use</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="Spiritual-Practice-And-Realization"><a data-study-link href="Spiritual-Practice-And-Realization/discussion.html">Spiritual Practice and Realization</a><br><span class="path-status planned" data-study-status>In progress</span></li>
            <li data-study-slug="How-To-Form-Self-Sustaining-Organizations"><a data-study-link href="How-To-Form-Self-Sustaining-Organizations/How-To-Form-Self-Sustaining-Organizations.html">How to Form Self-Sustaining Organizations</a><br><span class="path-status released" data-study-status>Released</span></li>
          </ul>
        </details>
      </li>
    </ol>

    <div class="parallel-track">
      <div>
        <span class="parallel-track-label">Parallel track &middot; formal and contemporary synthesis</span>
        <h3>Can the pieces form a coherent framework?</h3>
        <p>Alongside every stage, I relate the framework to science, technology, and current developments, formalise its claims, and test whether it can grow into a coherent explanatory system.</p>
      </div>
      <div class="parallel-studies">
        <div class="parallel-study" data-study-slug="Coexistence-From-First-Principles" data-presentation-pdf="Coexistence-From-First-Principles/Coexistence-From-First-Principles-MD-Practitioner.pdf"><a data-study-link href="Coexistence-From-First-Principles/Coexistence-From-First-Principles-MD-Practitioner.pdf" title="Open presentation PDF">Coexistence from First Principles</a><span class="path-status draft" data-study-status>Draft</span></div>
        <div class="parallel-study" data-study-slug="Science-Technology-And-Human-Purpose"><a data-study-link href="Science-Technology-And-Human-Purpose/discussion.html">Science, Technology, and Human Purpose</a><span class="path-status planned" data-study-status>In progress</span></div>
      </div>
    </div>

    <div class="path-invitation">
      <p><strong>Follow the path, or help shape it.</strong> Status badges show where the work stands now. Use a study&rsquo;s discussion to question an argument, review a draft, suggest sources, or help develop an in-progress study.</p>
      <div class="path-invitation-actions">
        <a class="btn-secondary" href="?status=all&amp;sort=recent#topical-studies">Browse current work</a>
        <a class="btn-primary" href="#contribute">How to contribute</a>
      </div>
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
    <div class="seg" id="coll-seg" role="group" aria-label="Filter by collection">
      <button type="button" data-coll="all" aria-pressed="true">All</button>
      <button type="button" data-coll="topical" aria-pressed="false">Topical</button>
      <button type="button" data-coll="formal" aria-pressed="false">Formal</button>
      <button type="button" data-coll="applied" aria-pressed="false">Applied</button>
    </div>
    <div class="seg" id="status-seg" role="group" aria-label="Filter by status">
      <button type="button" data-status="all" aria-pressed="false">All</button>
      <button type="button" data-status="available" aria-pressed="true">Available</button>
      <button type="button" data-status="planned" aria-pressed="false">In progress</button>
    </div>
    <label class="sr-only" for="sort">Sort</label>
    <select class="field" id="sort" aria-label="Sort studies">
      <option value="recent">Recently updated</option>
      <option value="az">Title A&ndash;Z</option>
    </select>
    <button type="button" class="btn-reset-filters" id="reset-filters" disabled>Reset filters</button>
  </div>

  <div class="cat-list-panel">
    <span class="cat-list-label" id="cat-list-label">Categories</span>
    <div class="cat-list" id="cat-list" role="group" aria-labelledby="cat-list-label"></div>
  </div>

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
    <p>These studies are written from the standpoint of a <strong>scientist and technologist</strong> trained in physics and mathematics. That starting point takes matter-first scientific explanations seriously, while recognising that consciousness, selfhood, and value remain contested and are not settled simply by assuming materialism.</p>
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
        <p class="path-lead">Use the Web Submission Portal if you want to take responsibility for a new analytic paper or a substantial revision. Read the study format in <a href="https://github.com/raghavamohan/AnalyticMadhyasthDarshan/blob/master/Studies/README.md">Studies/README.md</a> and <a href="https://github.com/raghavamohan/AnalyticMadhyasthDarshan/blob/master/CONTRIBUTING.md">CONTRIBUTING.md</a> before you start.</p>
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
    <p>This collection began as one researcher&rsquo;s attempt to understand <strong>Madhyasth Darshan</strong> in dialogue with science, Advaita Vedanta, and modern philosophy. It is published openly so that others can follow the path, challenge its arguments, improve its sources, and contribute studies of their own.</p>
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
    const badge = count
      ? `<span class="discuss-badge" aria-hidden="true">${count}</span>`
      : "";
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
      ? `<div class="card-foot" style="border:none;padding:6px 0 0;color:#9a8f80;">Updated ${s.updated}</div>`
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
      if (grid) grid.innerHTML = items.map(cardHTML).join("");
      const empty = document.getElementById(`empty-${coll}`);
      if (empty) empty.classList.toggle("is-hidden", items.length > 0);
      const countEl = document.querySelector(`[data-count-for="${coll}"]`);
      if (countEl) countEl.textContent = `${items.length} of ${total} shown`;
    });
    const count = document.getElementById("count");
    if (count) count.textContent = `${shown} studies shown`;
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

      const status = START_HERE_STATUS_WORDS[study.status] ? study.status : "planned";
      const badge = item.querySelector("[data-study-status]");
      if (badge) {
        badge.classList.remove("released", "draft", "planned");
        badge.classList.add(status);
        badge.textContent = START_HERE_STATUS_WORDS[status];
      }

      const studyLink = item.querySelector("[data-study-link]");
      if (studyLink) {
        const presentationPdf = item.dataset.presentationPdf;
        if (presentationPdf) {
          studyLink.href = `${presentationPdf}?cb=${CATALOG_BUILD_ID}`;
          studyLink.title = "Open presentation PDF";
        } else {
          studyLink.href = hasReadLinks(study) ? studyHtmlHref(study) : studyDiscussionHref(study);
        }
      }

      const updated = item.querySelector("[data-study-updated]");
      if (updated) updated.textContent = study.updated ? `Updated ${study.updated}` : "Work not yet published";

      const action = item.querySelector("[data-study-action]");
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
          if (Object.keys(discussStats).length) renderCatalog();
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


def _card_discuss_link_html(entry: dict, version_query: str) -> str:
    """Initial (pre-stats) discussion link: no comment count badge, matching the
    JS `discussLinkHtml` before `/api/discussions/stats` resolves."""
    href = _card_discussion_href(entry, version_query)
    title = entry["title"]
    return (
        f'<a class="discuss-link" href="{href}" title="Discussion board" '
        f'aria-label="Discuss {_card_esc_attr(title)}">Discuss</a>'
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
    updated = entry.get("updated")
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
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=BASE,
        )
        build_id = result.stdout.strip()
        if build_id:
            return build_id
    except (OSError, subprocess.CalledProcessError):
        pass
    ist = ZoneInfo("Asia/Kolkata")
    return datetime.now(ist).strftime("%Y%m%d%H%M")


def main() -> int:
    from _study_catalog import sync_pre_catalog_proposals_to_catalog

    sync_pre_catalog_proposals_to_catalog()

    index_path = STUDIES / "index.html"
    legacy_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    topical_rows = load_rows_for_build(legacy_text, StudyTable.TOPICAL)
    formal_rows = load_rows_for_build(legacy_text, StudyTable.FORMAL)
    applied_rows = load_rows_for_build(legacy_text, StudyTable.APPLIED)

    if not topical_rows and not formal_rows and not applied_rows:
        print("No catalog rows found in index.html or catalog JSON files", file=sys.stderr)
        return 1

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
    index_path.write_text(minify_inline_css(html), encoding="utf-8")
    print("Wrote Studies/index.html shell with inlined catalog bootstrap (and catalog-*.json for runtime refresh).")

    if topical_rows:
        write_studies_catalog(
            topical_rows,
            StudyTable.TOPICAL,
            rebuild_discussion=False,
            rebuild_feedback_template=False,
        )
        print(f"Wrote {len(topical_rows)} topical catalog entries to catalog-topical.json.")
    if formal_rows:
        write_studies_catalog(
            formal_rows,
            StudyTable.FORMAL,
            rebuild_discussion=False,
            rebuild_feedback_template=False,
        )
        print(f"Wrote {len(formal_rows)} formal catalog entries to catalog-formal.json.")
    if applied_rows:
        write_studies_catalog(
            applied_rows,
            StudyTable.APPLIED,
            rebuild_discussion=False,
            rebuild_feedback_template=False,
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

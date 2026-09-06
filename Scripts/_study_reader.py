"""Screen-only reader controls and content-versioned shared assets."""
import hashlib
import os
from pathlib import Path

from _common import BASE

ASSETS = BASE / "Assets" / "reader"


def reader_assets(source: Path) -> tuple[str, str]:
    prefix = Path(os.path.relpath(ASSETS, source.parent)).as_posix()
    def url(name: str) -> str:
        version = hashlib.sha256((ASSETS / name).read_bytes()).hexdigest()[:16]
        return f"{prefix}/{name}?v={version}"
    return (
        f'<link rel="stylesheet" media="screen" href="{url("reader.css")}"/>\n'
        f'<link rel="stylesheet" media="screen" href="{url("search.css")}"/>\n'
        f'<link rel="stylesheet" media="screen" href="{url("study-tools.css")}"/>',
        f'<script defer src="{url("search.js")}"></script>\n'
        f'<script defer src="{url("reader-features.js")}"></script>\n'
        f'<script defer src="{url("notes-core.js")}"></script>\n'
        f'<script defer src="{url("study-tools.js")}" data-offline-client="{url("offline-client.js")}"></script>\n'
        f'<script defer src="{url("reader.js")}"></script>',
    )


def reader_bootstrap() -> str:
    # Whitelists match ReaderCore.preferences; no storage value becomes markup.
    return """<script>
(()=>{try{
 const r=document.documentElement,t=localStorage.getItem('amd-theme');
 if(['light','dark','sepia'].includes(t))r.dataset.theme=t;
 const p=JSON.parse(localStorage.getItem('amd-reader-prefs-v1')||'{}');
 if([16,18,20,22,24].includes(p.fontSize))r.style.setProperty('--reader-font',p.fontSize+'px');
 if([1.5,1.75,2].includes(p.lineHeight))r.style.setProperty('--reader-line',p.lineHeight);
 if([56,68,80].includes(p.width))r.style.setProperty('--reader-width',p.width+'ch');
}catch(e){}})();
</script>
"""


def reader_controls() -> str:
    return """<section class="reader-resume reader-chrome" id="reader-resume" aria-label="Saved reading position" hidden>
  <div><strong>Continue reading</strong><span id="reader-resume-label"></span></div>
  <button type="button" id="reader-resume-go">Resume</button>
  <button type="button" id="reader-resume-dismiss">Start here</button>
</section>
<dialog id="reader-tools" class="reader-chrome" aria-labelledby="reader-tools-title">
  <header class="reader-panel-header"><h2 id="reader-tools-title">Study tools</h2><button type="button" id="reader-close" aria-label="Close study tools">&#215;</button></header>
  <div class="reader-tabs" role="tablist" aria-label="Study tools">
    <button type="button" role="tab" id="reader-tab-contents" aria-controls="reader-contents" aria-selected="true">Contents</button>
    <button type="button" role="tab" id="reader-tab-search" aria-controls="reader-search" aria-selected="false" tabindex="-1">Find</button>
    <button type="button" role="tab" id="reader-tab-notes" aria-controls="reader-notes" aria-selected="false" tabindex="-1">Notes</button>
    <button type="button" role="tab" id="reader-tab-bookmarks" aria-controls="reader-bookmarks" aria-selected="false" tabindex="-1">Bookmarks</button>
    <button type="button" role="tab" id="reader-tab-listen" aria-controls="reader-listen" aria-selected="false" tabindex="-1">Listen</button>
    <button type="button" role="tab" id="reader-tab-display" aria-controls="reader-display" aria-selected="false" tabindex="-1">Display</button>
  </div>
  <section id="reader-contents" class="reader-tab-panel" role="tabpanel" aria-labelledby="reader-tab-contents" tabindex="0">
    <button type="button" id="reader-passage-tools">Link &amp; sources for this passage</button>
    <p class="reader-helper">Select text to choose a passage, or use the passage at the top of the page. Click a citation code to preview its source.</p>
    <nav id="reader-outline" aria-label="Study contents"></nav>
  </section>
  <section id="reader-search" class="reader-tab-panel study-search" role="tabpanel" aria-labelledby="reader-tab-search" tabindex="0" hidden>
    <form id="reader-search-form" class="search-form"><label for="reader-search-query">Find in this document</label>
      <div class="search-input-row"><input id="reader-search-query" type="search" maxlength="200" placeholder="Word or quoted phrase"/><button type="submit">Find</button></div>
    </form>
    <p class="reader-helper">All words must occur in a passage. Use quotes for a phrase. Latin accents are ignored; Hindi spelling is preserved.</p>
    <a id="reader-search-all" href="/Studies/search.html">Search all studies and notes →</a>
    <p id="reader-search-status" class="search-status" role="status" aria-live="polite">Enter a word or phrase.</p>
    <ol id="reader-search-results" class="search-results"></ol>
    <button type="button" id="reader-search-more" hidden>Show more results</button>
  </section>
  <section id="reader-notes" class="reader-tab-panel" role="tabpanel" aria-labelledby="reader-tab-notes" tabindex="0" hidden>
    <p class="reader-helper">Select text to highlight or annotate it. With no selection, add a note to the passage at the top of the page.</p>
    <button type="button" id="notes-new">Highlight or add a note</button>
    <p id="notes-status" class="reader-helper" role="status" aria-live="polite">Opening private notes…</p>
    <form id="notes-editor" hidden>
      <p id="notes-quote"></p>
      <label for="notes-color">Highlight color</label><select id="notes-color"><option value="yellow">Yellow</option><option value="green">Green</option><option value="blue">Blue</option><option value="rose">Rose</option></select>
      <label for="notes-text">Your private note</label><textarea id="notes-text" rows="6" maxlength="12000" placeholder="What does this claim mean? What should I check?"></textarea>
      <p id="notes-save-state" role="status" aria-live="polite"></p>
      <div class="study-tool-actions"><button type="submit">Save note</button><button type="button" id="notes-cancel">Close editor</button></div>
      <button type="button" id="notes-reload" hidden>Reload saved note</button>
      <button type="button" id="notes-reattach">Attach to current selection</button>
    </form>
    <label for="notes-scope">Show notes</label><select id="notes-scope"><option value="document">This document</option><option value="all">All documents</option></select>
    <ol id="notes-list" class="study-note-list" aria-label="Private notes"></ol>
    <details><summary>Export or restore notes</summary><p class="reader-helper">Exports include the notes shown above and any unsaved editor text. Conflicting imported notes are kept as separate copies.</p>
      <div class="study-tool-actions"><button type="button" id="notes-export-md">Export Markdown</button><button type="button" id="notes-export-json">Export JSON</button></div>
      <label for="notes-import">Restore a JSON backup</label><input id="notes-import" type="file" accept="application/json,.json"/>
      <div id="notes-import-review" hidden><p id="notes-import-description"></p><button type="button" id="notes-import-confirm">Import these notes</button><button type="button" id="notes-import-cancel">Cancel import</button></div>
    </details>
    <p class="reader-helper">Notes stay on this device and are not sent to the website. Anyone using this browser profile can read them. Export a backup before clearing browser data.</p>
    <a href="/Studies/notebook.html">My notes &amp; saved studies →</a>
  </section>
  <section id="reader-listen" class="reader-tab-panel" role="tabpanel" aria-labelledby="reader-tab-listen" tabindex="0" hidden>
    <p class="reader-helper">Select a passage, then read it using a voice installed on this device. No audio starts automatically.</p>
    <label for="listen-voice">Device voice</label><select id="listen-voice"></select>
    <label for="listen-speed">Reading speed</label><select id="listen-speed"><option value="0.75">0.75×</option><option value="1" selected>1×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option></select>
    <div class="study-tool-actions"><button type="button" id="listen-start">Read selection</button><button type="button" id="listen-pause" disabled>Pause</button><button type="button" id="listen-resume" disabled>Resume</button><button type="button" id="listen-stop" disabled>Stop</button></div>
    <p id="listen-status" role="status" aria-live="polite">Open Listen to check device voices.</p>
    <p class="reader-helper">Only voices reported by your browser as local are offered. Voice availability and offline support vary by device. Pronunciation of Sanskrit, Hindi, formulas and abbreviations may be imperfect. Highlighting follows each spoken sentence or short chunk.</p>
  </section>
  <section id="reader-bookmarks" class="reader-tab-panel" role="tabpanel" aria-labelledby="reader-tab-bookmarks" tabindex="0" hidden>
    <form id="reader-bookmark-form">
      <label for="reader-bookmark-name">Name this place</label>
      <input id="reader-bookmark-name" type="text" maxlength="80" placeholder="e.g. Return to the definition" autocomplete="off"/>
      <button type="submit" class="reader-primary">Bookmark this place</button>
    </form>
    <p id="reader-bookmark-empty" class="reader-helper">No bookmarks in this study yet.</p>
    <ol id="reader-bookmark-list" aria-label="Saved places"></ol>
  </section>
  <section id="reader-display" class="reader-tab-panel" role="tabpanel" aria-labelledby="reader-tab-display" tabindex="0" hidden>
    <label for="reader-font-size">Text size</label>
    <select id="reader-font-size"><option value="16">Small · 16</option><option value="18">Default · 18</option><option value="20">Large · 20</option><option value="22">Larger · 22</option><option value="24">Largest · 24</option></select>
    <label for="reader-line-height">Line spacing</label>
    <select id="reader-line-height"><option value="1.5">Compact</option><option value="1.75">Comfortable</option><option value="2">Spacious</option></select>
    <label for="reader-column-width">Text width</label>
    <select id="reader-column-width"><option value="56">Narrow</option><option value="68">Comfortable</option><option value="80">Wide</option></select>
    <label for="reader-color-theme">Page color</label>
    <select id="reader-color-theme"><option value="system">Follow device</option><option value="light">Light</option><option value="sepia">Sepia</option><option value="dark">Dark</option></select>
    <button type="button" id="reader-reset-display">Reset display</button>
    <p class="reader-helper">Display choices apply to study pages. PDF and print keep their original layout.</p>
    <details id="reader-offline-tools"><summary>Offline reading</summary>
      <p class="reader-helper">Save this document and its reading tools, images and fonts in this browser. Source PDFs, discussions and collection search require a connection.</p>
      <div class="study-tool-actions"><button type="button" id="offline-save">Save for offline reading</button><button type="button" id="offline-remove" hidden>Remove saved copy</button></div>
      <p id="offline-status" role="status" aria-live="polite">Open this section to check saved copies.</p>
      <a href="/Studies/notebook.html">My notes &amp; saved studies →</a>
      <p class="reader-helper">Browser storage can be cleared or evicted. Notes and downloaded backups are separate from saved study copies.</p>
    </details>
  </section>
  <footer class="reader-panel-footer"><p id="reader-storage-hint">Reading position and bookmarks stay in this browser on this device.</p>
    <button type="button" id="reader-clear-data">Clear saved places for this study</button>
    <div id="reader-clear-confirm" hidden><p>Remove this study’s saved position and bookmarks?</p><button type="button" id="reader-clear-yes">Remove saved places</button><button type="button" id="reader-clear-no">Keep them</button></div>
  </footer>
</dialog>
<div id="reader-selection-tools" class="reader-chrome" role="region" aria-label="Selected text tools" hidden><button type="button" id="selection-highlight">Highlight</button><button type="button" id="selection-note">Note</button><button type="button" id="selection-listen">Listen</button><button type="button" id="selection-dismiss" aria-label="Hide selection tools">&#215;</button></div>
<p id="reader-offline-banner" class="reader-chrome" role="status" hidden></p>
<dialog id="reader-viewer" class="reader-chrome" aria-labelledby="reader-viewer-title">
  <header class="reader-panel-header"><h2 id="reader-viewer-title">Passage tools</h2><button type="button" id="reader-viewer-close" aria-label="Close preview">&#215;</button></header>
  <p id="reader-viewer-status" role="status" aria-live="polite"></p>
  <div id="reader-source-view">
    <p id="reader-passage-excerpt"></p><button type="button" id="reader-copy-passage">Copy passage link</button>
    <label id="reader-copy-label" for="reader-copy-fallback" hidden>Copy this text</label><textarea id="reader-copy-fallback" rows="3" readonly hidden></textarea>
    <div id="reader-source-detail" hidden><h3 id="reader-source-title"></h3><p id="reader-source-citation"></p><p id="reader-source-note" class="reader-helper"></p>
      <a id="reader-source-open" target="_blank" rel="noopener noreferrer">Open source in a new tab ↗</a> <button type="button" id="reader-copy-citation">Copy citation</button>
    </div>
    <label for="reader-source-query">Find a reference in this study</label><input id="reader-source-query" type="search" placeholder="Source code, title or author"/>
    <p id="reader-source-status" class="reader-helper"></p><ul id="reader-source-list"></ul>
  </div>
  <div id="reader-visual-view" hidden><div class="reader-zoom-controls"><button type="button" id="reader-zoom-out" aria-label="Zoom out">−</button><output id="reader-zoom-level" aria-live="polite">100%</output><button type="button" id="reader-zoom-in" aria-label="Zoom in">+</button><button type="button" id="reader-zoom-fit">Fit</button><button type="button" id="reader-zoom-reset">100%</button></div>
    <p class="reader-helper">Scroll or swipe inside the viewer to see the whole figure or table.</p><div id="reader-visual-stage" tabindex="0" role="region" aria-label="Enlarged figure or table"><div id="reader-visual-canvas"><div id="reader-visual-content"></div></div></div>
  </div>
</dialog>
<div id="reader-message" class="reader-chrome" role="status" aria-live="polite" hidden></div>
"""

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
        f'<link rel="stylesheet" media="screen" href="{url("reader.css")}"/>',
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
    <button type="button" role="tab" id="reader-tab-bookmarks" aria-controls="reader-bookmarks" aria-selected="false" tabindex="-1">Bookmarks</button>
    <button type="button" role="tab" id="reader-tab-display" aria-controls="reader-display" aria-selected="false" tabindex="-1">Display</button>
  </div>
  <section id="reader-contents" class="reader-tab-panel" role="tabpanel" aria-labelledby="reader-tab-contents" tabindex="0">
    <p class="reader-helper">Follow the argument, section by section.</p>
    <nav id="reader-outline" aria-label="Study contents"></nav>
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
  </section>
  <footer class="reader-panel-footer"><p id="reader-storage-hint">Reading position and bookmarks stay in this browser on this device.</p>
    <button type="button" id="reader-clear-data">Clear saved places for this study</button>
    <div id="reader-clear-confirm" hidden><p>Remove this study’s saved position and bookmarks?</p><button type="button" id="reader-clear-yes">Remove saved places</button><button type="button" id="reader-clear-no">Keep them</button></div>
  </footer>
</dialog>
<div id="reader-message" class="reader-chrome" role="status" aria-live="polite" hidden></div>
"""

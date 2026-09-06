/* Progressive reader enhancement. No accounts, network calls or third-party storage. */
(() => {
  'use strict';
  const cleanText = value => String(value || '').replace(/\s+/g, ' ').trim().normalize('NFC');
  const bounded = (value, max) => typeof value === 'string' ? value.slice(0, max) : '';
  function preferences(raw) {
    const p = raw && typeof raw === 'object' ? raw : {};
    return {
      fontSize: [16,18,20,22,24].includes(p.fontSize) ? p.fontSize : 18,
      lineHeight: [1.5,1.75,2].includes(p.lineHeight) ? p.lineHeight : 1.75,
      width: [56,68,80].includes(p.width) ? p.width : 68,
      sidebar: typeof p.sidebar === 'boolean' ? p.sidebar : true,
    };
  }
  function passageKey(text) {
    let a = 2166136261, b = 2246822519;
    for (const character of cleanText(text)) {
      const code = character.codePointAt(0);
      a = Math.imul(a ^ code, 16777619);
      b = Math.imul(b ^ code, 3266489917);
    }
    return 'reader-p-' + (a >>> 0).toString(16).padStart(8,'0') + (b >>> 0).toString(16).padStart(8,'0');
  }
  function cursor(raw) {
    if (!raw || typeof raw !== 'object' || typeof raw.anchor !== 'string' || !raw.anchor
        || raw.anchor.length > 400 || !Number.isFinite(raw.fraction)) return null;
    return { anchor: raw.anchor, heading: bounded(raw.heading,400), quote: bounded(raw.quote,160),
      label: bounded(raw.label,200), fraction: Math.max(0,Math.min(1,raw.fraction)) };
  }
  function state(raw) {
    if (!raw || raw.version !== 1 || !Array.isArray(raw.bookmarks)) throw new Error('Unrecognized reading data');
    const seen = new Set();
    return { version: 1, position: cursor(raw.position), bookmarks: raw.bookmarks.slice(0,100).flatMap(mark => {
      const place = cursor(mark?.place);
      if (!place || !/^[a-z0-9-]{1,64}$/i.test(mark.id || '') || seen.has(mark.id)) return [];
      seen.add(mark.id);
      return [{ id: mark.id, name: bounded(mark.name,80) || place.label || 'Saved place', place }];
    }) };
  }
  function resolvePlace(place, passages, headings) {
    if (!place) return null;
    const exact = passages.find(item => item.id === place.anchor
      && (!place.heading || item.heading === place.heading)
      && (!place.quote || item.text.includes(place.quote)));
    if (exact) return { item: exact, fraction: place.fraction, changed: false };
    // Only an unambiguous excerpt in its original section can recover a changed
    // paragraph. Otherwise open the saved heading and tell the reader why.
    const matching = place.quote.length >= 24 ? passages.filter(item => item.heading === place.heading && item.text.includes(place.quote)) : [];
    if (matching.length === 1) return { item: matching[0], fraction: 0, changed: true };
    const section = headings.find(item => item.id === place.heading);
    return section ? { item: section, fraction: 0, changed: true } : null;
  }
  function lastBefore(items, y) {
    let lo = 0, hi = items.length - 1, answer = -1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (items[mid].top <= y) { answer = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return answer;
  }
  const Core = { preferences, passageKey, cursor, state, resolvePlace, lastBefore };
  if (typeof module !== 'undefined' && module.exports) module.exports = Core;
  if (typeof document === 'undefined') return;

  const root = document.documentElement, main = document.getElementById('main');
  const tools = document.getElementById('reader-tools'), opener = document.getElementById('reader-open');
  if (!main || !tools || !opener || typeof tools.showModal !== 'function') return;
  const $ = id => document.getElementById(id);
  const wide = matchMedia('(min-width: 1180px)'), system = matchMedia('(prefers-color-scheme: dark)');
  const preferenceKey = 'amd-reader-prefs-v1', documentKey = 'amd-reader-v1:' + location.pathname;
  const emptyState = () => ({ version: 1, position: null, bookmarks: [] });
  let model = emptyState(), prefs = preferences(null), corrupt = false, storageAvailable = true;
  let messageTimer, saveTimer, geometryTimer, pendingPlace = null, frame = 0, editId = null, tracking = false;
  function message(text, permanent = false) {
    clearTimeout(messageTimer);
    $('reader-message').textContent = text;
    $('reader-message').hidden = !text;
    if (!permanent) messageTimer = setTimeout(() => { $('reader-message').hidden = true; }, 6000);
  }
  function storageFailure() {
    storageAvailable = false;
    $('reader-storage-hint').textContent = 'Browser storage is unavailable. Changes last for this visit only.';
  }
  function read(key) {
    try { return localStorage.getItem(key); } catch (_) { storageFailure(); return null; }
  }
  function write(key, value) {
    if (!storageAvailable) return false;
    try {
      if (value === null) localStorage.removeItem(key); else localStorage.setItem(key,value);
      return true;
    } catch (_) { storageFailure(); return false; }
  }
  try { prefs = preferences(JSON.parse(read(preferenceKey) || '{}')); } catch (_) { /* defaults */ }
  const rawState = read(documentKey);
  if (rawState) {
    try {
      if (rawState.length > 200000) throw new Error('Reading data is too large');
      model = state(JSON.parse(rawState));
    } catch (_) {
      corrupt = true;
      $('reader-storage-hint').textContent = 'Saved reading data could not be read. Clear this study’s saved places to reset it.';
    }
  }
  function updateState(change) {
    // Merge the latest value so an autosave cannot erase bookmarks from another tab.
    if (!corrupt && storageAvailable) {
      const latest = read(documentKey);
      if (storageAvailable) {
        try {
          if (latest && latest.length > 200000) throw new Error('Reading data is too large');
          model = latest ? state(JSON.parse(latest)) : emptyState();
        } catch (_) { corrupt = true; }
      }
    }
    change(model);
    return !corrupt && write(documentKey,JSON.stringify(model));
  }
  function savePreferences() { write(preferenceKey,JSON.stringify(prefs)); }
  function applyPreferences() {
    root.style.setProperty('--reader-font',prefs.fontSize + 'px');
    root.style.setProperty('--reader-line',prefs.lineHeight);
    root.style.setProperty('--reader-width',prefs.width + 'ch');
    $('reader-font-size').value = String(prefs.fontSize);
    $('reader-line-height').value = String(prefs.lineHeight);
    $('reader-column-width').value = String(prefs.width);
  }
  function paintTheme() {
    const chosen = root.dataset.theme;
    const active = chosen || (system.matches ? 'dark' : 'light');
    const next = active === 'dark' ? 'light' : 'dark';
    $('reader-color-theme').value = chosen || 'system';
    $('study-theme-toggle').setAttribute('aria-label','Switch to ' + next + ' theme');
    $('study-theme-toggle').querySelector('span').textContent = next === 'dark' ? 'Dark' : 'Light';
  }
  function setTheme(theme) {
    if (!['light','dark','sepia'].includes(theme)) {
      delete root.dataset.theme;
      write('amd-theme',null);
    } else { root.dataset.theme = theme; write('amd-theme',theme); }
    paintTheme();
  }
  applyPreferences(); paintTheme();
  $('reader-color-theme').addEventListener('change',event => setTheme(event.target.value));
  $('study-theme-toggle').addEventListener('click',() => {
    const active = root.dataset.theme || (system.matches ? 'dark' : 'light');
    setTheme(active === 'dark' ? 'light' : 'dark');
  });
  system.addEventListener('change',paintTheme);

  const headingNodes = [...main.querySelectorAll('h2[id],h3[id],h4[id]')];
  let section = '';
  const headings = headingNodes.map(node => {
    if (node.tagName === 'H2') section = node.id;
    return { id: node.id, node, text: cleanText(node.textContent), heading: section, top: 0 };
  });
  const sections = headings.filter(item => item.node.tagName === 'H2');
  const passages = [], counts = new Map();
  section = '';
  for (const node of main.querySelectorAll('h2[id],h3[id],h4[id],p,li,table,pre,.mermaid')) {
    if (node.closest('.study-toc,.study-reading-key') || node.parentElement.closest('li,table,pre,.mermaid')) continue;
    if (node.tagName === 'H2') section = node.id;
    const text = cleanText(node.dataset.readerSource || node.textContent) || cleanText(node.querySelector('img')?.getAttribute('alt'));
    if (!text) continue;
    if (!node.id) {
      const key = passageKey(section + '\n' + text), count = (counts.get(key) || 0) + 1;
      counts.set(key,count);
      let id = key + (count === 1 ? '' : '-' + count);
      while (document.getElementById(id)) id += '-p';
      node.id = id;
    }
    node.dataset.readerPassage = '';
    passages.push({ id: node.id, node, text, heading: section, top: 0, height: 0 });
  }
  const toolbar = document.querySelector('.study-toolbar');
  const marker = () => toolbar.offsetHeight + 12;
  function capture() {
    const y = scrollY + marker(), item = passages[Math.max(0,lastBefore(passages,y))];
    if (!item) return null;
    return { anchor: item.id, heading: item.heading, quote: item.text.slice(0,160),
      label: headings.find(h => h.id === item.heading)?.text || 'Introduction',
      fraction: Math.max(0,Math.min(1,(y - item.top) / Math.max(1,item.height))) };
  }
  function measure() {
    root.style.setProperty('--study-toolbar-height',toolbar.offsetHeight + 'px');
    for (const item of [...headings,...passages]) {
      const rect = item.node.getBoundingClientRect();
      item.top = rect.top + scrollY; item.height = rect.height;
    }
    updatePosition();
  }
  function scheduleMeasure(place = null) {
    if (place) pendingPlace = place;
    clearTimeout(geometryTimer);
    geometryTimer = setTimeout(() => {
      const restore = pendingPlace; pendingPlace = null;
      measure();
      if (restore) go(restore,{ focus: false, history: false, announce: false });
    },50);
  }
  function startTracking() {
    tracking = true;
    if (!$('reader-resume').hidden) { $('reader-resume').hidden = true; scheduleMeasure(); }
  }
  function persistPosition() {
    if (tracking) { const place = capture(); if (place) updateState(data => { data.position = place; }); }
  }
  function go(place, options = {}) {
    const { focus = true, history: useHistory = true, announce = true } = options;
    const found = resolvePlace(place,passages,headings);
    if (!found) { if (announce) message('This passage is no longer available. Choose a section from Contents.'); return false; }
    const target = found.item.node;
    if (useHistory) { startTracking(); history.pushState(null,'','#' + encodeURIComponent(found.item.id)); }
    clearTimeout(geometryTimer); pendingPlace = null;
    // Refresh after the resume banner or drawer changes the layout.
    measure();
    scrollTo({ top: Math.max(0,target.getBoundingClientRect().top + scrollY + found.fraction * target.getBoundingClientRect().height - marker()), behavior: 'instant' });
    if (focus) { target.tabIndex = -1; target.focus({ preventScroll: true }); }
    updatePosition();
    if (useHistory) persistPosition();
    if (announce && found.changed) message('The text has changed. Opened the closest saved passage or section.');
    return true;
  }
  function visitHeading(item) {
    if (!item) return;
    if (!wide.matches) closePanel(false,false);
    go({ anchor:item.id, heading:item.id, fraction:0, quote:'', label:item.text });
  }
  const outlineLinks = new Map(), groups = new Map();
  let currentGroup = null, activeId = '', activeSection = '', currentIndex = -2, sectionIndex = -2;
  for (const item of headings) {
    if (item.node.tagName === 'H2' || !currentGroup) {
      const group = document.createElement('div'); group.className = 'reader-outline-group';
      const row = document.createElement('div'); row.className = 'reader-outline-row';
      const children = document.createElement('div'); children.className = 'reader-outline-children'; children.hidden = true;
      const toggle = document.createElement('button'); toggle.type = 'button'; toggle.textContent = '+';
      toggle.setAttribute('aria-label','Show subsections for ' + item.text); toggle.setAttribute('aria-expanded','false');
      toggle.hidden = true;
      toggle.addEventListener('click',() => setGroup(item.heading,!children.hidden ? false : true));
      group.append(row,children); $('reader-outline').append(group);
      currentGroup = { row,children,toggle,title:item.text,first:item.id };
      groups.set(item.heading,currentGroup);
    }
    const link = document.createElement('a'); link.href = '#' + encodeURIComponent(item.id); link.textContent = item.text;
    if (item.node.dataset.depth) link.dataset.depth = item.node.dataset.depth;
    link.addEventListener('click',event => { event.preventDefault(); visitHeading(item); });
    if (currentGroup.first === item.id) currentGroup.row.append(link,currentGroup.toggle);
    else { currentGroup.children.append(link); currentGroup.toggle.hidden = false; }
    outlineLinks.set(item.id,link);
  }
  if (!headings.length) $('reader-outline').textContent = 'This note has no section headings.';
  function setGroup(id, open) {
    const group = groups.get(id); if (!group) return;
    group.children.hidden = !open; group.toggle.textContent = open ? '−' : '+';
    group.toggle.setAttribute('aria-expanded',String(open));
    group.toggle.setAttribute('aria-label',(open ? 'Hide' : 'Show') + ' subsections for ' + group.title);
  }
  function navLink(id, item, label) {
    const link = $(id); link.textContent = label;
    link.classList.toggle('is-disabled',!item); link.setAttribute('aria-disabled',String(!item));
    if (item) { link.href = '#' + encodeURIComponent(item.id); link.title = item.text; }
    else { link.removeAttribute('href'); link.removeAttribute('title'); }
  }
  function updatePosition() {
    const y = scrollY + marker(), index = lastBefore(headings,y), major = lastBefore(sections,y);
    const current = headings[index];
    if (index !== currentIndex) {
      currentIndex = index;
      $('reader-current').textContent = current?.text || 'Introduction';
      $('reader-current').title = current?.text || 'Introduction';
    }
    if (major !== sectionIndex) {
      sectionIndex = major;
      navLink('study-section-prev',major > 0 ? sections[major - 1] : null,'← Previous');
      navLink('study-section-next',sections[major + 1],'Next →');
    }
    if ((current?.id || '') !== activeId) {
      outlineLinks.get(activeId)?.removeAttribute('aria-current');
      activeId = current?.id || '';
      const link = outlineLinks.get(activeId); link?.setAttribute('aria-current','location');
      if ((current?.heading || '') !== activeSection) {
        activeSection = current?.heading || '';
        for (const id of groups.keys()) setGroup(id,id === activeSection);
      }
      const panel = $('reader-contents');
      if (link && tools.open && !panel.hidden && !tools.contains(document.activeElement) && !tools.matches(':hover')) {
        const bounds = panel.getBoundingClientRect(), rect = link.getBoundingClientRect();
        if (rect.top < bounds.top || rect.bottom > bounds.bottom) panel.scrollTop += rect.top - bounds.top - 20;
      }
    }
  }
  $('study-section-prev').addEventListener('click',event => {
    event.preventDefault(); const i = lastBefore(sections,scrollY + marker()); if (i > 0) visitHeading(sections[i - 1]);
  });
  $('study-section-next').addEventListener('click',event => {
    event.preventDefault(); visitHeading(sections[lastBefore(sections,scrollY + marker()) + 1]);
  });
  window.addEventListener('scroll',() => {
    if (!frame) frame = requestAnimationFrame(() => { frame = 0; updatePosition(); });
    clearTimeout(saveTimer); saveTimer = setTimeout(persistPosition,700);
  },{ passive: true });
  for (const type of ['wheel','touchmove','keydown']) document.addEventListener(type,event => {
    if (tools.contains(event.target)) return;
    if (type === 'keydown' && (event.target.closest?.('input,textarea,select')
        || !['ArrowDown','ArrowUp','PageDown','PageUp','Home','End',' '].includes(event.key)
        || (event.key === ' ' && event.target.closest?.('button')))) return;
    pendingPlace = null;
    startTracking();
  },{ passive: true });
  window.addEventListener('pagehide',persistPosition);
  document.addEventListener('visibilitychange',() => { if (document.hidden) persistPosition(); });
  window.addEventListener('resize',() => scheduleMeasure());
  new ResizeObserver(() => scheduleMeasure()).observe(main);
  new ResizeObserver(() => scheduleMeasure()).observe(toolbar);
  document.fonts?.ready.then(() => scheduleMeasure());

  function selectTab(name, focus = false) {
    for (const tab of tools.querySelectorAll('[role="tab"]')) {
      const chosen = tab.id === 'reader-tab-' + name;
      tab.setAttribute('aria-selected',String(chosen)); tab.tabIndex = chosen ? 0 : -1;
      $(tab.getAttribute('aria-controls')).hidden = !chosen;
      if (chosen && focus) tab.focus();
    }
  }
  const tabs = [...tools.querySelectorAll('[role="tab"]')];
  for (const [index,tab] of tabs.entries()) {
    tab.addEventListener('click',() => selectTab(tab.id.replace('reader-tab-','')));
    tab.addEventListener('keydown',event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); selectTab(tabs[next].id.replace('reader-tab-',''),true); }
    });
  }
  function openPanel(user = true) {
    const place = capture();
    if (!tools.open) {
      if (wide.matches) { tools.setAttribute('open',''); root.dataset.readerPanel = 'open'; }
      else { tools.showModal(); root.dataset.readerModal = ''; }
    }
    opener.setAttribute('aria-expanded','true');
    if (user) {
      if (wide.matches) { prefs.sidebar = true; savePreferences(); }
      tools.querySelector('[role="tab"][aria-selected="true"]').focus();
    }
    scheduleMeasure(wide.matches && scrollY > 0 ? place : null);
  }
  function closePanel(returnFocus = true, remember = true) {
    const place = capture(), wasWide = root.dataset.readerPanel === 'open';
    tools.close(); delete root.dataset.readerPanel; delete root.dataset.readerModal;
    opener.setAttribute('aria-expanded','false');
    if (remember && wide.matches) { prefs.sidebar = false; savePreferences(); }
    if (returnFocus) opener.focus({ preventScroll: true });
    scheduleMeasure(wasWide && scrollY > 0 ? place : null);
  }
  opener.addEventListener('click',() => openPanel());
  $('reader-close').addEventListener('click',() => closePanel());
  tools.addEventListener('cancel',event => { event.preventDefault(); closePanel(); });
  tools.addEventListener('keydown',event => {
    if (event.key === 'Escape' && wide.matches) { event.preventDefault(); closePanel(); }
  });
  wide.addEventListener('change',() => { closePanel(false,false); if (wide.matches && prefs.sidebar) openPanel(false); });
  for (const [id,field] of [['reader-font-size','fontSize'],['reader-line-height','lineHeight'],['reader-column-width','width']]) {
    $(id).addEventListener('change',event => {
      const place = capture(); prefs = preferences({ ...prefs,[field]: Number(event.target.value) });
      applyPreferences(); savePreferences(); scheduleMeasure(place);
    });
  }
  $('reader-reset-display').addEventListener('click',() => {
    const place = capture(); prefs = preferences({ sidebar:prefs.sidebar });
    applyPreferences(); savePreferences(); setTheme('system'); scheduleMeasure(place);
  });

  function resetForm() {
    editId = null; $('reader-bookmark-name').value = '';
    $('reader-bookmark-form').querySelector('[type="submit"]').textContent = 'Bookmark this place';
    $('reader-cancel-rename').hidden = true;
  }
  const cancelRename = document.createElement('button'); cancelRename.type = 'button';
  cancelRename.id = 'reader-cancel-rename'; cancelRename.textContent = 'Cancel rename'; cancelRename.hidden = true;
  cancelRename.addEventListener('click',resetForm); $('reader-bookmark-form').append(cancelRename);
  function renderBookmarks() {
    const list = $('reader-bookmark-list'); list.replaceChildren();
    $('reader-bookmark-empty').hidden = model.bookmarks.length > 0;
    for (const mark of model.bookmarks) {
      const row = document.createElement('li'), visit = document.createElement('button');
      visit.type = 'button'; visit.className = 'reader-bookmark-go'; visit.textContent = mark.name;
      visit.addEventListener('click',() => { if (!wide.matches) closePanel(false,false); go(mark.place); });
      const quote = document.createElement('p'); quote.className = 'reader-bookmark-excerpt'; quote.textContent = mark.place.quote;
      const actions = document.createElement('div'); actions.className = 'reader-bookmark-actions';
      for (const action of ['Rename','Remove']) {
        const button = document.createElement('button'); button.type = 'button'; button.textContent = action;
        button.setAttribute('aria-label',action + ' bookmark: ' + mark.name);
        button.addEventListener('click',() => {
          if (action === 'Rename') {
            editId = mark.id; $('reader-bookmark-name').value = mark.name;
            $('reader-bookmark-form').querySelector('[type="submit"]').textContent = 'Save name';
            cancelRename.hidden = false; $('reader-bookmark-name').focus();
          } else {
            const saved = updateState(data => { data.bookmarks = data.bookmarks.filter(item => item.id !== mark.id); });
            if (editId === mark.id) resetForm(); renderBookmarks();
            message(saved ? 'Bookmark removed.' : 'Removed for this visit; browser storage could not be updated.');
            $('reader-bookmark-name').focus();
          }
        }); actions.append(button);
      }
      row.append(visit,quote,actions); list.append(row);
    }
  }
  $('reader-bookmark-form').addEventListener('submit',event => {
    event.preventDefault(); const place = capture(); if (!place) return;
    const name = cleanText($('reader-bookmark-name').value).slice(0,80) || place.label;
    let limited = false;
    const saved = updateState(data => {
      if (editId) { const mark = data.bookmarks.find(item => item.id === editId); if (mark) mark.name = name; }
      else if (data.bookmarks.length >= 100) limited = true;
      else data.bookmarks.push({ id: crypto.randomUUID(),name,place });
    });
    if (limited) { message('This study has 100 bookmarks. Remove one before adding another.'); return; }
    resetForm(); renderBookmarks(); message(saved ? 'Bookmark saved in this browser.' : 'Bookmark kept for this visit; browser storage is unavailable.');
  });
  $('reader-clear-data').addEventListener('click',() => { $('reader-clear-confirm').hidden = false; $('reader-clear-no').focus(); });
  $('reader-clear-no').addEventListener('click',() => { $('reader-clear-confirm').hidden = true; $('reader-clear-data').focus(); });
  $('reader-clear-yes').addEventListener('click',() => {
    clearTimeout(saveTimer); tracking = false; model = emptyState(); corrupt = false;
    const removed = write(documentKey,null); resetForm(); renderBookmarks();
    $('reader-resume').hidden = true; $('reader-clear-confirm').hidden = true;
    if (removed) $('reader-storage-hint').textContent = 'Reading position and bookmarks stay in this browser on this device.';
    message(removed ? 'Saved places cleared for this study.' : 'Cleared for this visit; browser storage could not be updated.');
    $('reader-clear-data').focus();
  });
  window.addEventListener('storage',event => {
    if (event.key === documentKey) {
      try {
        if (event.newValue && event.newValue.length > 200000) return;
        model = event.newValue ? state(JSON.parse(event.newValue)) : emptyState();
        corrupt = false; renderBookmarks();
        savedPosition = model.position;
        if (!savedPosition) $('reader-resume').hidden = true;
        else $('reader-resume-label').textContent = savedPosition.label || 'Your saved passage';
      } catch (_) { /* preserve this tab */ }
    }
  });

  function followHash() {
    let id; try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const item = passages.find(p => p.id === id) || headings.find(h => h.id === id);
    if (item) { startTracking(); go({ anchor:id,heading:item.heading,fraction:0,quote:'',label:item.text },{ focus:false,history:false }); }
  }
  window.addEventListener('hashchange',followHash);
  window.addEventListener('popstate',() => { if (location.hash) followHash(); });
  renderBookmarks(); opener.hidden = false;
  const fallback = $('study-contents'); if (fallback) fallback.hidden = true;
  measure();
  if (wide.matches && prefs.sidebar) openPanel(false);
  let savedPosition = model.position;
  tracking = !savedPosition || Boolean(location.hash);
  if (savedPosition && !location.hash) {
    $('reader-resume-label').textContent = savedPosition.label || 'Your saved passage';
    $('reader-resume').hidden = false;
  }
  $('reader-resume-go').addEventListener('click',() => go(savedPosition));
  $('reader-resume-dismiss').addEventListener('click',() => { startTracking(); measure(); persistPosition(); });
  requestAnimationFrame(() => { measure(); if (location.hash) followHash(); });
})();

/* Private annotations, optional device speech and explicit offline saving. */
(() => {
  'use strict';
  const C = window.AMDNotes, $ = id => document.getElementById(id);
  const noteCount = count => `${count} ${count === 1 ? 'note' : 'notes'}`;
  const script = document.currentScript, offlineScript = script?.dataset.offlineClient;
  let offlinePromise;
  const loadOffline = () => offlinePromise ||= new Promise((resolve,reject) => {
    const node = document.createElement('script'); node.src = offlineScript;
    node.onload = () => resolve(window.AMDOffline);
    node.onerror = () => { offlinePromise = null; node.remove(); reject(new Error('Offline tools could not load. Reconnect and try again.')); };
    document.head.append(node);
  });
  function download(value,filename,type) {
    const url = URL.createObjectURL(new Blob([value],{type})), a = document.createElement('a');
    a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url),30000);
  }
  window.AMDStudyTools = async context => {
    if (!C || !$('notes-list')) return;
    const path = context ? location.pathname : null;
    const version = document.querySelector('meta[name="amd-source-version"]')?.content;
    const title = document.querySelector('h1')?.textContent.trim().slice(0,250) || 'Study';
    // KaTeX's hidden MathML duplicates its visible text. Keep selection offsets
    // and highlight ranges on the same visible text nodes, without rewriting DOM.
    function textNodes(root) {
      const walker = document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:node => node.parentElement.closest('.katex-mathml,script,style') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
      const result = []; let node; while ((node = walker.nextNode())) result.push(node); return result;
    }
    let passageCache;
    const candidates = () => passageCache ||= context ? context.passages.filter(p => !p.node.matches('.mermaid') && !p.text.startsWith('Author:') && !p.text.startsWith('Edited on:'))
      .map(p => ({...p,text:textNodes(p.node).map(node => node.textContent).join('')})) : [];
    let notes = [], store, volatile = false, editor = null, expected = null, dirty = false, selection = null, pendingImport = null, shown = 20;
    const status = value => { $('notes-status').textContent = value; };
    let channel;
    try { channel = new BroadcastChannel('amd-study-notes'); } catch (_) { /* Reload still reads current records. */ }
    const signal = () => channel?.postMessage('changed');
    function setDirty(value) { dirty = value; $('notes-save-state').textContent = value ? 'Unsaved changes.' : 'Saved.'; }
    const visible = () => notes.filter(n => !path || $('notes-scope').value === 'all' || n.document === path).sort((a,b) => b.updated.localeCompare(a.updated));
    function domRange(passage,start,end) {
      const range = document.createRange(); let offset = 0, started = false;
      for (const node of textNodes(passage.node)) {
        const next = offset + node.length;
        if (!started && start >= offset && start < next) { range.setStart(node,start - offset); started = true; }
        if (started && end > offset && end <= next) { range.setEnd(node,end - offset); return range; }
        offset = next;
      }
      return null;
    }
    function paintNotes() {
      if (!context) return;
      context.main.querySelectorAll('[data-reader-note]').forEach(n => n.removeAttribute('data-reader-note'));
      const currentNotes = notes.filter(n => n.document === path);
      if (!currentNotes.length) { for (const color of C.COLORS) window.CSS?.highlights?.delete('reader-notes-' + color); return; }
      const ranges = new Map(C.COLORS.map(color => [color,[]])), passages = candidates();
      for (const note of currentNotes) for (const anchor of note.anchors) {
        const found = C.resolve(anchor,passages); if (!found) continue;
        found.passage.node.dataset.readerNote = '';
        const range = domRange(found.passage,found.start,found.end); if (range) ranges.get(note.color).push(range);
      }
      if (window.CSS?.highlights && window.Highlight) for (const [color,items] of ranges) CSS.highlights.set('reader-notes-' + color,new Highlight(...items));
    }
    function noteState(note) {
      if (!context || note.document !== path) return 'Source version ' + note.version.slice(0,8);
      if (note.anchors.some(a => !C.resolve(a,candidates()))) return 'Passage changed or unavailable. The original quote is preserved.';
      return note.version !== version ? 'The study has been updated. Check this note against the current text.' : 'Attached to this version.';
    }
    const more = document.createElement('button'); more.type = 'button'; more.textContent = 'Show more notes'; $('notes-list').after(more);
    more.addEventListener('click',() => { shown += 20; render(); });
    function render() {
      const all = visible(), list = $('notes-list'); list.replaceChildren(); more.hidden = all.length <= shown;
      if (!all.length) { const empty = document.createElement('li'); empty.textContent = 'No notes here yet.'; list.append(empty); }
      for (const note of all.slice(0,shown)) {
        const li = document.createElement('li'), link = document.createElement('a'), quote = document.createElement('p'), body = document.createElement('p'), meta = document.createElement('p');
        link.href = C.link(note,location.origin); link.textContent = note.title;
        quote.className = 'note-quote'; quote.textContent = note.quote.slice(0,300) + (note.quote.length > 300 ? '…' : '');
        quote.style.setProperty('--note-color',({yellow:'#a89020',green:'#42854b',blue:'#4783b0',rose:'#b85d7e'})[note.color]);
        body.className = 'note-body'; body.textContent = note.note.slice(0,1000) + (note.note.length > 1000 ? '…' : '');
        meta.className = 'note-meta'; meta.textContent = new Date(note.updated).toLocaleString() + ' · ' + noteState(note);
        const actions = document.createElement('div'); actions.className = 'study-tool-actions';
        const edit = document.createElement('button'), remove = document.createElement('button'); edit.type = remove.type = 'button';
        edit.textContent = 'Edit note'; edit.addEventListener('click',() => begin(note));
        remove.textContent = 'Delete note'; remove.addEventListener('click',() => {
          if (li.querySelector('.note-delete-confirm')) return;
          const confirm = document.createElement('div'); confirm.className = 'note-delete-confirm';
          const prompt = document.createElement('p'); prompt.textContent = 'Delete this note and highlight?';
          const yes = document.createElement('button'), no = document.createElement('button'); yes.type = no.type = 'button'; yes.textContent = 'Delete permanently'; no.textContent = 'Keep note';
          yes.addEventListener('click',async () => { try { await store.remove(note.id,note.revision); if (editor?.id === note.id) closeEditor(); signal(); await refresh(); status('Note deleted.'); } catch (error) { status(error.message); } });
          no.addEventListener('click',() => { confirm.remove(); remove.focus(); }); confirm.append(prompt,yes,no); actions.after(confirm); yes.focus();
        });
        link.addEventListener('click',event => {
          if (!context || note.document !== path || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
          event.preventDefault(); const found = C.resolve(note.anchors[0],candidates());
          const target = found?.passage || context.headings.find(h => h.id === note.anchors[0].heading);
          if (!target) { status('The original passage is unavailable. Its quote remains in this note.'); return; }
          if (!context.wide.matches) context.closePanel(false,false);
          context.go({anchor:target.id,heading:target.heading,quote:'',label:target.text,fraction:0});
          if (!found) context.message('Opened the original section. This note’s passage has changed.',true);
        });
        actions.append(edit,remove); li.append(link,quote,body,meta,actions); list.append(li);
      }
      paintNotes();
    }
    async function refresh() { notes = await store.all(); render(); }
    function openNotes() { if (context) { context.selectTab('notes'); context.openPanel(); } }
    function begin(note) {
      if (dirty) { status('Save or close the current editor before opening another note.'); $('notes-text').focus(); return; }
      editor = structuredClone(note); expected = notes.find(n => n.id === note.id)?.revision || null;
      $('notes-cancel').textContent = 'Close editor'; delete $('notes-cancel').dataset.confirm;
      $('notes-editor').hidden = false; $('notes-quote').textContent = note.quote; $('notes-text').value = note.note; $('notes-color').value = note.color;
      $('notes-reload').hidden = !expected; $('notes-reattach').hidden = !context || note.document !== path;
      setDirty(!expected); openNotes(); $('notes-text').focus();
    }
    function closeEditor() { editor = null; expected = null; dirty = false; $('notes-editor').hidden = true; $('notes-text').value = ''; }
    function draft() { return editor && {...editor,note:$('notes-text').value,color:$('notes-color').value,revision:crypto.randomUUID(),updated:new Date().toISOString()}; }
    $('notes-text').addEventListener('input',() => setDirty(true)); $('notes-color').addEventListener('change',() => setDirty(true));
    $('notes-cancel').addEventListener('click',() => {
      if (dirty && $('notes-cancel').dataset.confirm !== 'true') { $('notes-cancel').dataset.confirm = 'true'; $('notes-cancel').textContent = 'Discard unsaved changes'; return; }
      closeEditor(); $('notes-cancel').textContent = 'Close editor'; delete $('notes-cancel').dataset.confirm;
    });
    $('notes-reload').addEventListener('click',async () => {
      try { await refresh(); const saved = notes.find(n => n.id === editor?.id); if (!saved) { status('This note was deleted elsewhere. Export or copy your unsaved text.'); return; }
        dirty = false; begin(saved);
      } catch (error) { status(error.message); }
    });
    $('notes-editor').addEventListener('submit',async event => {
      event.preventDefault(); if (!editor) return;
      const value = draft();
      try { await store.put(value,expected); editor = value; expected = value.revision; setDirty(false); $('notes-reload').hidden = false; signal(); await refresh(); status(volatile ? 'Kept for this visit only. Export a backup before leaving.' : 'Note saved on this device.'); }
      catch (error) { $('notes-save-state').textContent = error.message + ' Export includes your unsaved text.'; }
    });
    $('notes-scope').addEventListener('change',() => { shown = 20; render(); });
    function snapshot() {
      if (!context) return null;
      const selected = getSelection(); if (!selected?.rangeCount || selected.isCollapsed) return null;
      const range = selected.getRangeAt(0), anchors = [];
      if (!context.main.contains(range.commonAncestorContainer)) return null;
      for (const p of candidates()) {
        if (!range.intersectsNode(p.node)) continue;
        let offset = 0, start = null, end = 0;
        for (const node of textNodes(p.node)) {
          if (range.intersectsNode(node)) {
            const from = range.startContainer === node ? range.startOffset : range.comparePoint(node,0) < 0 ? node.length : 0;
            const to = range.endContainer === node ? range.endOffset : range.comparePoint(node,node.length) > 0 ? 0 : node.length;
            if (to > from) { if (start === null) start = offset + from; end = offset + to; }
          }
          offset += node.length;
        }
        if (start !== null && p.text.slice(start,end).trim()) anchors.push(C.makeAnchor(p,start,end));
      }
      const quote = anchors.map(a => a.quote).join('\n');
      return anchors.length && anchors.length <= 20 && quote.length <= 6000 ? {anchors,quote} : null;
    }
    function currentSelection(fallback = false) {
      if (selection) return selection;
      if (!fallback || !context) return null;
      const current = context.capture()?.anchor, toolbarBottom = document.querySelector('.study-toolbar')?.getBoundingClientRect().bottom || 0;
      const p = candidates().find(p => p.id === current) || candidates().find(p => p.node.getBoundingClientRect().bottom > toolbarBottom);
      if (!p || !p.text.trim()) return null;
      const end = Math.min(6000,p.text.length); return {anchors:[C.makeAnchor(p,0,end)],quote:p.text.slice(0,end)};
    }
    function newNote(selected) {
      const now = new Date().toISOString();
      return {id:crypto.randomUUID(),revision:crypto.randomUUID(),document:path,title,version,color:'yellow',note:'',created:now,updated:now,...selected};
    }
    $('notes-new').addEventListener('click',() => { const selected = currentSelection(true); if (selected) begin(newNote(selected)); else status('Select up to 6,000 characters of study text first.'); });
    $('notes-reattach').addEventListener('click',() => {
      if (!selection || !editor || editor.document !== path) { status('Select the replacement passage in this study, then return here.'); return; }
      editor = {...editor,...selection,version}; $('notes-quote').textContent = editor.quote; setDirty(true);
    });
    async function exportNotes(format) {
      try {
        await refresh(); let chosen = visible();
        if (dirty && editor) { const pending = C.record(draft()); chosen = [...chosen.filter(n => n.id !== pending.id),pending]; }
        download(format === 'json' ? C.backup(chosen) : C.markdown(chosen),'study-notes.' + (format === 'json' ? 'json' : 'md'),format === 'json' ? 'application/json' : 'text/markdown;charset=utf-8');
        status(`Exported ${noteCount(chosen.length)}${dirty ? ', including unsaved text' : ''}.`);
      } catch (error) { status(error.message); }
    }
    $('notes-export-json').addEventListener('click',() => exportNotes('json')); $('notes-export-md').addEventListener('click',() => exportNotes('md'));
    $('notes-import').addEventListener('change',async event => {
      const file = event.target.files[0]; if (!file) return;
      try { if (file.size > 10000000) throw new Error('Choose a JSON backup smaller than 10 MB.'); pendingImport = C.parseBackup(await file.text());
        $('notes-import-description').textContent = `Import ${noteCount(pendingImport.length)}? Existing notes will be retained.`; $('notes-import-review').hidden = false;
      } catch (error) { pendingImport = null; $('notes-import-review').hidden = true; status(error.message); }
      event.target.value = '';
    });
    $('notes-import-cancel').addEventListener('click',() => { pendingImport = null; $('notes-import-review').hidden = true; });
    $('notes-import-confirm').addEventListener('click',async () => {
      if (!pendingImport) return;
      try { const result = await store.restore(pendingImport); pendingImport = null; $('notes-import-review').hidden = true; signal(); await refresh(); status(`Imported ${noteCount(result.added)}; ${noteCount(result.skipped)} already present and identical.${volatile ? ' Kept for this visit only.' : ''}`); }
      catch (error) { status(error.message); }
    });
    window.addEventListener('beforeunload',event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
    if (channel) channel.onmessage = () => { refresh().then(() => { if (dirty) status('Notes changed in another tab. Your unsaved text is still in the editor.'); }).catch(error => status(error.message)); };
    const loadingControls = [...document.querySelectorAll('#reader-notes button,#reader-notes input,#notebook-notes button,#notebook-notes input,#selection-note,#selection-highlight')];
    loadingControls.forEach(node => { node.disabled = true; });
    if (context) {
      // Speech and native selection must work even while IndexedDB is opening.
      const updateSpeechSelection = setupSpeech(context,() => selection,domRange,candidates);
      let selectionTimer;
      function captureSelectionNow() {
        clearTimeout(selectionTimer);
        const next = snapshot(), native = window.getSelection();
        if (next || (!native?.isCollapsed && context.main.contains(native?.anchorNode))) {
          selection = next; $('reader-selection-tools').hidden = !next; updateSpeechSelection();
        }
      }
      const captureSelection = () => { clearTimeout(selectionTimer); selectionTimer = setTimeout(captureSelectionNow,100); };
      const clearSelection = () => { clearTimeout(selectionTimer); selection = null; $('reader-selection-tools').hidden = true; updateSpeechSelection(); };
      // Android's long-press handles can move without another pointerup.
      document.addEventListener('selectionchange',captureSelection);
      context.main.addEventListener('pointerup',captureSelection); context.main.addEventListener('keyup',captureSelection);
      context.main.addEventListener('pointerdown',clearSelection);
      // Opening the mobile dialog moves focus and may collapse the DOM range.
      // Freeze it before the toolbar's click handler or pointer default action.
      const preserveSelection = event => { if (event.target.closest('.reader-chrome,.study-toolbar')) captureSelectionNow(); };
      document.addEventListener('pointerdown',preserveSelection,true);
      document.addEventListener('click',preserveSelection,true);
      $('selection-dismiss').addEventListener('click',clearSelection);
      $('selection-note').addEventListener('click',() => { if (selection) { begin(newNote(selection)); $('reader-selection-tools').hidden = true; } });
      $('selection-highlight').addEventListener('click',async () => {
        if (!selection) return;
        try { await store.put(newNote(selection)); signal(); await refresh(); $('reader-selection-tools').hidden = true; context.message(volatile ? 'Highlight kept for this visit. Export a backup.' : 'Highlight saved. Open Notes to add your thoughts.'); }
        catch (error) { context.message(error.message,true); }
      });
      $('reader-offline-tools').addEventListener('toggle',() => { if ($('reader-offline-tools').open) loadOffline().then(api => api.reader(path)).catch(error => { $('offline-status').textContent = error.message; }); });
      if (document.documentElement.hasAttribute('data-offline-copy')) { $('reader-offline-banner').hidden = false; $('reader-offline-banner').textContent = 'Reading a saved copy. Open Display → Offline reading to check its date or update it.'; }
    } else {
      $('notes-new').hidden = true; $('notes-scope').value = 'all'; $('notes-scope').disabled = true;
      loadOffline().then(api => api.library()).catch(error => { $('offline-library-status').textContent = error.message; });
    }
    try { store = await C.openStore(); await refresh(); status(`${noteCount(notes.filter(n => !path || n.document === path).length)} saved on this device.`); }
    catch (_) {
      volatile = true; const memory = new Map();
      store = {all:async () => [...memory.values()],put:async n => { C.record(n); C.limits([...memory.values()].filter(v => v.id !== n.id).concat(n)); memory.set(n.id,n); },remove:async id => memory.delete(id),restore:async incoming => {
        const staged = new Map(memory); let added = 0, skipped = 0;
        for (let n of incoming) { n = C.record(n); if (staged.has(n.id)) { if (JSON.stringify(staged.get(n.id)) === JSON.stringify(n)) { skipped++; continue; } n = {...n,id:crypto.randomUUID(),revision:crypto.randomUUID()}; } staged.set(n.id,n); added++; }
        C.limits([...staged.values()]); memory.clear(); for (const [id,n] of staged) memory.set(id,n); return {added,skipped};
      }};
      status('Device storage is unavailable or unreadable. Existing stored data is untouched. New notes last only for this visit; export before leaving.'); render();
    }
    loadingControls.forEach(node => { node.disabled = false; });
  };
  function setupSpeech(context,getSelection,domRange,candidates) {
    const synth = window.speechSynthesis, S = window.AMDReaderSpeech;
    let voices = [], state = 'idle', ranges = [], testing = false;
    const status = text => { $('listen-status').textContent = text; };
    const clearHighlight = () => window.CSS?.highlights?.delete('reader-speaking');
    function controls(value = state) {
      state = value; const active = state !== 'idle';
      $('listen-start').disabled = active || !voices.length || !getSelection();
      $('listen-test').disabled = active || !voices.length;
      $('listen-pause').disabled = state !== 'speaking'; $('listen-resume').disabled = state !== 'paused';
      $('listen-stop').disabled = !active; $('listen-voice').disabled = $('listen-speed').disabled = active || !voices.length;
      if (state !== 'speaking') clearHighlight();
    }
    function updateSelection() {
      const selected = getSelection();
      $('listen-selection-label').textContent = selected ? `Selected passage · ${selected.quote.length.toLocaleString()} characters` : 'No passage selected';
      $('listen-selection-preview').textContent = selected ? selected.quote.slice(0,240) + (selected.quote.length > 240 ? '…' : '') : 'Close tools and select up to 6,000 characters in the study. Then open Listen.';
      controls();
    }
    if (!synth || !window.SpeechSynthesisUtterance || !S) {
      status('Read-aloud is not available in this browser.'); updateSelection(); return updateSelection;
    }
    const player = S.createPlayer({synth,Utterance:window.SpeechSynthesisUtterance,
      onState:value => { controls(value); if (value === 'starting') status('Starting device voice…'); if (value === 'paused') status('Paused. Resume restarts this sentence or short chunk.'); },
      onChunk:(piece,index,total) => {
        status(testing ? 'Playing the test voice.' : `Reading ${index + 1} of ${total} sentences or chunks.`);
        if (window.CSS?.highlights && window.Highlight) {
          const highlights = ranges.filter(r => r.from < piece.end && r.to > piece.start).map(r => domRange(r.passage,r.start + Math.max(0,piece.start - r.from),r.start + Math.min(r.to - r.from,piece.end - r.from))).filter(Boolean);
          CSS.highlights.set('reader-speaking',new Highlight(...highlights));
        }
      },
      onError:code => status(code === 'start-timeout' ? 'The device voice did not start. Try Test voice or another voice. Open “No sound?” below for phone settings.' : 'The device could not read aloud (' + code + '). Try another voice or open “No sound?” below.'),
      onFinish:() => status(testing ? 'Voice test finished. If you heard nothing, open “No sound?” below.' : 'Finished reading the selection.'),
    });
    function refreshVoices() {
      if (state !== 'idle') return;
      const previous = $('listen-voice').value;
      try { voices = synth.getVoices().filter(v => v.localService); } catch (_) { voices = []; }
      const preferred = S.chooseVoice(voices,previous,document.documentElement.lang || 'en',navigator.languages);
      $('listen-voice').replaceChildren();
      for (const voice of voices) { const option = document.createElement('option'); option.value = voice.voiceURI; option.textContent = `${voice.name} · ${voice.lang}`; $('listen-voice').append(option); }
      if (preferred) $('listen-voice').value = preferred.voiceURI;
      controls(); status(voices.length ? 'Choose Read selection, or Test voice to check sound.' : 'No device voices are available yet. Reopen Listen after installing a voice in your phone’s text-to-speech settings. See “No sound?” below.');
    }
    $('reader-tab-listen').addEventListener('click',refreshVoices);
    $('selection-listen').addEventListener('click',() => { context.selectTab('listen'); context.openPanel(); $('reader-selection-tools').hidden = true; refreshVoices(); });
    synth.addEventListener('voiceschanged',refreshVoices);
    $('listen-stop').addEventListener('click',() => { player.stop(); status('Stopped.'); });
    $('listen-pause').addEventListener('click',() => player.pause());
    $('listen-resume').addEventListener('click',() => player.resume());
    window.addEventListener('pagehide',() => player.stop());
    const voice = () => voices.find(v => v.voiceURI === $('listen-voice').value);
    $('listen-test').addEventListener('click',() => {
      const chosen = voice(); if (!chosen) return;
      testing = true; ranges = []; player.play({text:'This is a test of the reading voice on your device.',voice:chosen,rate:Number($('listen-speed').value)});
    });
    $('listen-start').addEventListener('click',() => {
      const selected = getSelection(), chosen = voice();
      if (!selected || !chosen) { status('Select study text and choose an available device voice first.'); return; }
      const resolved = selected.anchors.map(a => C.resolve(a,candidates()));
      if (resolved.some(a => !a)) { status('The selected passage has changed. Select it again.'); return; }
      let offset = 0;
      ranges = resolved.map((found,i) => { const start = offset; offset += selected.anchors[i].quote.length + 1; return {...found,from:start,to:offset - 1}; });
      testing = false; player.play({text:selected.anchors.map(a => a.quote).join('\n'),voice:chosen,rate:Number($('listen-speed').value)});
    });
    updateSelection(); refreshVoices();
    // Some mobile engines initialize lazily and deliver voiceschanged late.
    const retries = [300,1000,3000].map(delay => setTimeout(() => { if (!voices.length) refreshVoices(); },delay));
    window.addEventListener('pagehide',() => retries.forEach(clearTimeout),{once:true});
    return updateSelection;
  }
  const startNotebook = () => { if ($('notebook')) window.AMDStudyTools(null).catch(() => { $('notes-status').textContent = 'Notes could not open. Reload the page to retry; existing device data is retained.'; }); };
  if (document.readyState !== 'complete') document.addEventListener('DOMContentLoaded',startNotebook,{once:true});
  else startNotebook();
})();

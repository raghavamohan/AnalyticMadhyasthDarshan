/* Find, inspect and share public study passages. No source document is fetched here. */
(() => {
  'use strict';
  const safeURL = (value, base) => {
    try { const url = new URL(value,base); return ['http:','https:'].includes(url.protocol) ? url.href : null; }
    catch (_) { return null; }
  };
  const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const cited = (text, tag) => new RegExp('(^|[^\\p{L}\\p{N}_])' + escape(tag) + '(?=$|[^\\p{L}\\p{N}_])','u').test(text);
  if (typeof module !== 'undefined' && module.exports) module.exports = { safeURL,cited };
  if (typeof window === 'undefined') return;
  window.AMDReaderFeatures = context => {
    const {main,passages,headings,tools,wide,capture,go,measure,scheduleMeasure,closePanel,message,cleanText} = context;
    const S = window.AMDSearch, $ = id => document.getElementById(id);
    const viewer = $('reader-viewer'), toolbar = document.querySelector('.study-toolbar');
    if (!S || !viewer?.showModal) return;
    const version = document.querySelector('meta[name="amd-source-version"]')?.content || '';
    const pageURL = document.querySelector('link[rel="canonical"]')?.href || location.href;
    const placeFor = item => ({anchor:item.id,heading:item.heading,quote:'',label:item.text,fraction:0});
    const currentItem = () => passages.find(p => p.id === capture()?.anchor) || passages[0];
    let selected = null;
    document.addEventListener('selectionchange',() => {
      const selection = getSelection();
      const element = selection?.anchorNode?.parentElement;
      if (!selection?.isCollapsed && element && main.contains(element)) {
        const node = element.closest('[data-reader-passage]');
        selected = passages.find(p => p.node === node) || null;
      }
    });
    window.addEventListener('scroll',() => { if (getSelection()?.isCollapsed) selected = null; },{passive:true});

    // One result is a passage. Text-range highlights leave citation/Math/DOM intact.
    let results = [], active = -1, shown = 0, queryTerms = [];
    const input = $('reader-search-query'), resultList = $('reader-search-results');
    const searchable = passages.filter(p => !p.node.matches('.mermaid') && !p.text.startsWith('Author:') && !p.text.startsWith('Edited on:'))
      .map(p => ({...p,text:S.readableText(p.node) || p.text}));
    const bar = document.createElement('div'); bar.id = 'reader-findbar'; bar.className = 'reader-chrome'; bar.hidden = true;
    const previous = document.createElement('button'), next = document.createElement('button'), clear = document.createElement('button'), count = document.createElement('span');
    for (const button of [previous,next,clear]) button.type = 'button';
    previous.textContent = '←'; previous.setAttribute('aria-label','Previous matching passage');
    next.textContent = '→'; next.setAttribute('aria-label','Next matching passage');
    clear.textContent = 'Clear'; clear.setAttribute('aria-label','Clear passage search');
    bar.append(previous,count,next,clear); toolbar.append(bar);
    function paintHit(item) {
      main.querySelector('.reader-search-hit')?.classList.remove('reader-search-hit');
      window.CSS?.highlights?.delete('reader-search');
      if (!item) return;
      item.node.classList.add('reader-search-hit');
      if (!window.CSS?.highlights || !window.Highlight) return;
      const nodes = [], walker = document.createTreeWalker(item.node,NodeFilter.SHOW_TEXT);
      let text = '', node;
      while ((node = walker.nextNode())) { nodes.push({node,start:text.length,end:text.length + node.length}); text += node.textContent; }
      const ranges = [];
      for (const [start,end] of S.match(text,queryTerms).slice(0,250)) {
        const a = nodes.find(n => n.start <= start && n.end > start), b = nodes.find(n => n.start < end && n.end >= end);
        if (!a || !b) continue;
        const range = document.createRange(); range.setStart(a.node,start - a.start); range.setEnd(b.node,end - b.start); ranges.push(range);
      }
      CSS.highlights.set('reader-search',new Highlight(...ranges));
    }
    function resultPosition() {
      count.textContent = active < 0 ? `${results.length} passages` : `${active + 1} of ${results.length}`;
      previous.disabled = active <= 0; next.disabled = active >= results.length - 1;
      resultList.querySelectorAll('[aria-current]').forEach(node => node.removeAttribute('aria-current'));
      resultList.querySelector(`[data-result="${active}"]`)?.setAttribute('aria-current','location');
    }
    function visit(index) {
      const found = results[index]; if (!found) return;
      active = index; bar.hidden = false;
      if (!wide.matches) closePanel(false,false);
      paintHit(found.passage); go(placeFor(found.passage)); resultPosition();
    }
    function moreResults() {
      for (let index = shown; index < Math.min(shown + 15,results.length); index++) {
        const {passage,hits} = results[index], li = document.createElement('li'), link = document.createElement('a'), snippet = document.createElement('p');
        link.href = '#' + passage.id; link.dataset.result = String(index);
        link.textContent = headings.find(h => h.id === passage.heading)?.text || 'Introduction';
        link.addEventListener('click',event => { if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return; event.preventDefault(); visit(index); });
        S.markText(snippet,S.excerpt(passage.text,hits),queryTerms); li.append(link,snippet); resultList.append(li);
      }
      shown = Math.min(shown + 15,results.length); $('reader-search-more').hidden = shown >= results.length;
      resultPosition();
    }
    function find() {
      const place = capture();
      try { queryTerms = S.terms(input.value); }
      catch (error) { $('reader-search-status').textContent = error.message; return; }
      results = S.search(searchable,queryTerms); active = -1; shown = 0; resultList.replaceChildren(); paintHit(null);
      bar.hidden = !results.length;
      $('reader-search-status').textContent = queryTerms.length ? `${results.length} matching passages.` + (!results.length ? ' Try fewer words or a different spelling.' : '') : 'Enter a word or phrase.';
      const collection = new URL('/Studies/search.html',location.origin); if (input.value.trim()) collection.searchParams.set('q',input.value.trim());
      $('reader-search-all').href = collection.href; moreResults(); scheduleMeasure(place);
    }
    $('reader-search-form').addEventListener('submit',event => { event.preventDefault(); find(); });
    $('reader-search-more').addEventListener('click',moreResults);
    previous.addEventListener('click',() => visit(active - 1)); next.addEventListener('click',() => visit(active + 1));
    clear.addEventListener('click',() => { input.value = ''; find(); });

    // The bibliography supplies metadata and links; source text is never invented.
    const references = [], byURL = new Map(), byTag = new Map();
    const referencesHeading = headings.find(h => /^References$/i.test(h.text));
    for (const passage of passages) {
      if (!referencesHeading || passage.heading !== referencesHeading.id || !['LI','P'].includes(passage.node.tagName)) continue;
      const link = passage.node.querySelector('a[href]'); const url = link && safeURL(link.getAttribute('href'),location.href);
      if (!url) continue;
      const strong = passage.node.querySelector('strong'), tag = strong ? cleanText(strong.textContent).replace(/\s*[—–-]\s*$/,'') : '';
      const entry = {node:passage.node,title:cleanText(link.textContent),text:cleanText(passage.node.textContent),url,tag:tag.length <= 60 ? tag : ''};
      references.push(entry); passage.node.dataset.readerReference = '';
      const key = new URL(url); key.hash = ''; byURL.set(key.href,entry);
      if (entry.tag && !byTag.has(entry.tag)) byTag.set(entry.tag,entry); else if (entry.tag) byTag.set(entry.tag,null);
    }
    let returnPlace, returnTarget, passageItem, chosenSource;
    function openViewer(trigger, visual = false) {
      returnPlace = capture(); returnTarget = trigger;
      if (!wide.matches && tools.open) closePanel(false,false);
      $('reader-source-view').hidden = visual; $('reader-visual-view').hidden = !visual;
      $('reader-copy-fallback').hidden = true; $('reader-copy-label').hidden = true;
      $('reader-viewer-status').textContent = '';
      viewer.showModal(); $('reader-viewer-close').focus({preventScroll:true});
    }
    function closeViewer() {
      viewer.close(); $('reader-visual-content').replaceChildren();
      if (returnPlace) go(returnPlace,{focus:false,history:false,announce:false});
      if (returnTarget?.isConnected && returnTarget.getClientRects().length) returnTarget.focus({preventScroll:true});
      else if (passageItem) { passageItem.node.tabIndex = -1; passageItem.node.focus({preventScroll:true}); }
    }
    $('reader-viewer-close').addEventListener('click',closeViewer);
    viewer.addEventListener('cancel',event => { event.preventDefault(); closeViewer(); });
    async function copy(text) {
      try { await navigator.clipboard.writeText(text); $('reader-viewer-status').textContent = 'Copied.'; }
      catch (_) {
        $('reader-copy-label').hidden = false; $('reader-copy-fallback').hidden = false;
        $('reader-copy-fallback').value = text; $('reader-copy-fallback').focus(); $('reader-copy-fallback').select();
        $('reader-viewer-status').textContent = 'Copy the selected text using your browser or keyboard.';
      }
    }
    function showSource(entry) {
      chosenSource = entry; $('reader-source-detail').hidden = false;
      $('reader-source-title').textContent = entry.tag ? `${entry.tag} · ${entry.title}` : entry.title;
      $('reader-source-citation').textContent = entry.text;
      $('reader-source-open').href = entry.url;
      $('reader-source-note').textContent = /\.pdf(?:$|[?#])/i.test(entry.url)
        ? 'Bibliography entry from this study. Cited page numbers refer to the named edition; PDF viewer page numbers may differ.'
        : 'Bibliography entry from this study. Open the source to check the cited material.';
    }
    function renderSources() {
      const list = $('reader-source-list'); list.replaceChildren();
      const query = S.fold($('reader-source-query').value.trim());
      const relevant = references.filter(entry => entry.tag && passageItem && cited(passageItem.text,entry.tag));
      const entries = query ? references.filter(entry => S.fold(entry.text).includes(query)) : relevant.length ? relevant : references;
      $('reader-source-status').textContent = query ? `${entries.length} matching references.` : relevant.length
        ? 'Source codes found in this passage. Search above to browse other references.'
        : 'No source code was matched in this passage. These are this study’s references.';
      if (!references.length) $('reader-source-status').textContent = 'This document has no linked bibliography entries.';
      for (const entry of entries) {
        const li = document.createElement('li'), button = document.createElement('button'); button.type = 'button';
        button.textContent = (entry.tag ? entry.tag + ' · ' : '') + entry.title;
        button.addEventListener('click',() => { showSource(entry); $('reader-source-detail').scrollIntoView({block:'nearest'}); });
        li.append(button); list.append(li);
      }
    }
    function openSources(trigger, item = selected || currentItem(), entry = null) {
      if (!item) return;
      passageItem = item; chosenSource = null; $('reader-viewer-title').textContent = 'Link & sources';
      const excerpt = S.readableText(item.node) || item.text;
      $('reader-passage-excerpt').textContent = excerpt.slice(0,600) + (excerpt.length > 600 ? '…' : '');
      $('reader-source-query').value = ''; $('reader-source-detail').hidden = true;
      renderSources(); if (entry) showSource(entry);
      openViewer(trigger);
    }
    $('reader-passage-tools').addEventListener('click',event => openSources(event.currentTarget));
    $('reader-source-query').addEventListener('input',renderSources);
    $('reader-copy-passage').addEventListener('click',() => {
      if (!passageItem) return;
      const canonical = new URL(pageURL);
      copy(S.passageURL(canonical.pathname,passageItem,'',version,canonical.origin));
    });
    $('reader-copy-citation').addEventListener('click',() => { if (chosenSource) copy(chosenSource.text + '\n' + chosenSource.url); });
    main.addEventListener('click',event => {
      const link = event.target.closest('a[href]');
      if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button) return;
      const url = safeURL(link.href,location.href); if (!url) return;
      const key = new URL(url); key.hash = ''; const entry = byURL.get(key.href); if (!entry) return;
      event.preventDefault(); openSources(link,passages.find(p => p.node.contains(link)) || currentItem(),{...entry,url});
    });
    const tags = [...byTag.keys()].filter(tag => byTag.get(tag)).sort((a,b) => b.length - a.length);
    if (tags.length) {
      const pattern = new RegExp('(^|[\\s(;,—–])(' + tags.map(escape).join('|') + ')(?=\\s*(?:[,;:]|§|pp?\\.|v\\.))','g');
      const walker = document.createTreeWalker(main,NodeFilter.SHOW_TEXT), texts = []; let node;
      while ((node = walker.nextNode())) if (!node.parentElement.closest('a,button,code,pre,h1,h2,h3,h4,.katex,[data-reader-reference],.study-toc')) texts.push(node);
      for (const text of texts) {
        const matches = [...text.textContent.matchAll(pattern)]; if (!matches.length) continue;
        const item = passages.find(p => p.node.contains(text)); if (!item) continue;
        const fragment = document.createDocumentFragment(); let offset = 0;
        for (const match of matches) {
          const start = match.index + match[1].length, end = start + match[2].length;
          fragment.append(document.createTextNode(text.textContent.slice(offset,start)));
          const button = document.createElement('button'); button.type = 'button'; button.className = 'reader-citation'; button.textContent = match[2];
          button.setAttribute('aria-label','Preview source ' + match[2]);
          button.addEventListener('click',() => openSources(button,item,byTag.get(match[2]))); fragment.append(button); offset = end;
        }
        fragment.append(document.createTextNode(text.textContent.slice(offset))); text.replaceWith(fragment);
      }
    }

    let scale = 1, baseWidth = 800, baseHeight = 600;
    const stage = $('reader-visual-stage'), canvas = $('reader-visual-canvas'), content = $('reader-visual-content');
    function zoom(value) {
      scale = Math.max(0.1,Math.min(4,value));
      content.style.transform = `scale(${scale})`; canvas.style.width = baseWidth * scale + 'px'; canvas.style.height = baseHeight * scale + 'px';
      $('reader-zoom-level').textContent = Math.round(scale * 100) + '%';
      $('reader-zoom-out').disabled = scale <= 0.1; $('reader-zoom-in').disabled = scale >= 4;
    }
    $('reader-zoom-in').addEventListener('click',() => zoom(scale * 1.25));
    $('reader-zoom-out').addEventListener('click',() => zoom(scale / 1.25));
    $('reader-zoom-fit').addEventListener('click',() => zoom(Math.min(1,(stage.clientWidth - 16) / baseWidth)));
    $('reader-zoom-reset').addEventListener('click',() => zoom(1));
    let serial = 0;
    function visual(original, trigger, label) {
      passageItem = passages.find(p => p.node === original || p.node.contains(original)) || currentItem();
      const target = original.matches('.mermaid') ? original.querySelector('svg') : original;
      if (!target) { message('This diagram is still loading. Try opening it again in a moment.'); return; }
      const clone = target.cloneNode(true), renamed = new Map(), prefix = 'reader-view-' + (++serial) + '-';
      for (const node of [clone,...clone.querySelectorAll('[id]')]) if (node.id) { renamed.set(node.id,prefix + node.id); node.id = prefix + node.id; }
      for (const node of [clone,...clone.querySelectorAll('*')]) {
        if (node.matches('style')) {
          node.textContent = node.textContent.replace(/#([\w-]+)/g,(all,id) => renamed.has(id) ? '#' + renamed.get(id) : all);
        }
        for (const attribute of [...node.attributes]) {
          let value = attribute.value.replace(/url\(#([^)]+)\)/g,(all,id) => renamed.has(id) ? `url(#${renamed.get(id)})` : all);
          if (['href','xlink:href'].includes(attribute.name) && value.startsWith('#') && renamed.has(value.slice(1))) value = '#' + renamed.get(value.slice(1));
          if (['aria-labelledby','aria-describedby'].includes(attribute.name)) value = value.split(' ').map(id => renamed.get(id) || id).join(' ');
          if (value !== attribute.value) node.setAttribute(attribute.name,value);
        }
        if (node.matches('a')) { node.setAttribute('target','_blank'); node.setAttribute('rel','noopener noreferrer'); }
        if (node.matches('button.term-tip')) node.replaceWith(document.createTextNode(node.textContent));
      }
      content.replaceChildren(clone); $('reader-viewer-title').textContent = label;
      openViewer(trigger,true);
      baseWidth = original.matches('table') ? Math.max(800,original.scrollWidth) : target.naturalWidth || target.viewBox?.baseVal?.width || target.getBoundingClientRect().width || 800;
      baseWidth = Math.min(6000,Math.max(300,baseWidth)); content.style.width = baseWidth + 'px';
      clone.style.maxWidth = 'none'; clone.style.width = '100%'; clone.style.height = 'auto'; content.style.transform = 'none';
      baseHeight = content.getBoundingClientRect().height;
      zoom(original.matches('table') ? 1 : Math.min(1,(stage.clientWidth - 16) / baseWidth));
      if (clone.matches('img') && !clone.complete) clone.addEventListener('load',() => {
        if (clone.parentElement !== content) return;
        baseHeight = content.offsetHeight; zoom(scale);
      },{once:true});
    }
    let figure = 0, table = 0;
    for (const node of main.querySelectorAll('table,.mermaid,p > img')) {
      if (node.closest('.study-toc')) continue;
      const isTable = node.matches('table'), label = isTable ? `Table ${++table}` : node.getAttribute('alt') || `Diagram ${++figure}`;
      const button = document.createElement('button'); button.type = 'button'; button.className = 'reader-enlarge reader-chrome';
      button.textContent = isTable ? 'Enlarge table' : 'Enlarge figure'; button.setAttribute('aria-label',button.textContent + ': ' + label);
      button.addEventListener('click',() => visual(node,button,label));
      const holder = node.closest('.study-table-scroll') || (node.matches('img') ? node.parentElement : node);
      holder.insertAdjacentElement('afterend',button);
    }
    measure();
    const params = new URLSearchParams(location.search), query = params.get('find');
    if (query) {
      input.value = query.slice(0,200); find();
      let anchor; try { anchor = decodeURIComponent(location.hash.slice(1)); } catch (_) { anchor = ''; }
      active = results.findIndex(result => result.passage.id === anchor);
      if (active >= 0) paintHit(results[active].passage);
      resultPosition();
    }
    if (params.get('pv') && !version.startsWith(params.get('pv'))) message('This study has changed since the link was created. Check the passage and its sources.');
    if (location.hash.startsWith('#reader-p-')) {
      let id; try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { id = ''; }
      if (id && !passages.some(p => p.id === id)) {
        const section = headings.find(h => h.id === params.get('section'));
        requestAnimationFrame(() => {
          if (section) go(placeFor(section),{focus:false,history:false});
          message(section ? 'That passage has changed. Opened its original section.' : 'That passage is no longer available. Use Contents or Find to locate it.',true);
        });
      }
    }
  };
})();

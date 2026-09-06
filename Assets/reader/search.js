/* Literal passage search, shared by the reader and the public collection page. */
(() => {
  'use strict';
  function fold(text) {
    return String(text).normalize('NFD').replace(/[\u0300-\u036f]/g,'').normalize('NFC')
      .toLowerCase().replace(/[‘’]/g,"'").replace(/[‐‑–—]/g,'-');
  }
  function normalized(text) {
    let value = '', offsets = [];
    for (let i = 0; i < text.length;) {
      const character = String.fromCodePoint(text.codePointAt(i)), end = i + character.length;
      const folded = fold(character);
      if (!folded && offsets.length) offsets[offsets.length - 1][1] = end;
      for (let part of folded) {
        if (/\s/u.test(part)) part = ' ';
        if (part === ' ' && value.endsWith(' ')) { offsets[offsets.length - 1][1] = end; continue; }
        value += part;
        for (let j = 0; j < part.length; j++) offsets.push([i,end]);
      }
      i = end;
    }
    return { value, offsets };
  }
  function terms(query) {
    if (query.length > 200) throw new Error('Use up to 200 characters.');
    if ((query.match(/"/g) || []).length % 2) throw new Error('Close the quotation marks around your phrase.');
    return [...new Set((query.match(/"[^"]+"|[^\s"]+/g) || []).map(word =>
      normalized(word.replace(/^"|"$/g,'')).value.trim()).filter(Boolean))];
  }
  const word = character => Boolean(character && /[\p{L}\p{N}\p{M}_]/u.test(character));
  function locations(text, term) {
    const found = [];
    if (!term) return found;
    for (let from = 0; from < text.length;) {
      const start = text.indexOf(term,from); if (start < 0) break;
      const end = start + term.length;
      if ((!word(term[0]) || !word(text[start - 1])) && (!word(term.at(-1)) || !word(text[end]))) found.push([start,end]);
      from = end;
    }
    return found;
  }
  function match(text, queryTerms) {
    if (!queryTerms.length) return [];
    const quick = fold(text).replace(/\s+/g,' ');
    if (queryTerms.some(term => !locations(quick,term).length)) return [];
    const normal = normalized(text), hits = queryTerms.map(term => locations(normal.value,term));
    if (hits.some(items => !items.length)) return [];
    const ranges = hits.flat().map(([start,end]) => [normal.offsets[start][0],normal.offsets[end - 1][1]]).sort((a,b) => a[0] - b[0]);
    return ranges.reduce((all, range) => {
      const last = all.at(-1);
      if (last && range[0] <= last[1]) last[1] = Math.max(last[1],range[1]); else all.push(range);
      return all;
    },[]);
  }
  function search(passages, queryTerms) {
    return passages.flatMap(passage => {
      const hits = match(passage.text,queryTerms);
      return hits.length ? [{ passage,hits }] : [];
    });
  }
  function excerpt(text, hits, size = 240) {
    const start = Math.max(0,(hits[0]?.[0] || 0) - 70), end = Math.min(text.length,start + size);
    return (start ? '…' : '') + text.slice(start,end) + (end < text.length ? '…' : '');
  }
  function passageURL(documentPath, passage, query = '', version = '', base = 'https://analyticmadhyasthdarshan.org') {
    const url = new URL(documentPath,base);
    if (url.origin !== new URL(base).origin || !/^\/(Studies|Applications)\/[^?#]+\.html$/.test(url.pathname)) throw new Error('Invalid study URL');
    url.search = '';
    if (query) url.searchParams.set('find',query.slice(0,200));
    if (passage.heading) url.searchParams.set('section',passage.heading);
    if (version) url.searchParams.set('pv',version.slice(0,16));
    url.hash = passage.id;
    return url.href;
  }
  const Core = { fold,normalized,terms,locations,match,search,excerpt,passageURL };
  if (typeof module !== 'undefined' && module.exports) module.exports = Core;
  if (typeof document === 'undefined') return;
  window.AMDSearch = Core;
  Core.readableText = node => {
    if (node.querySelector('.katex')) {
      node = node.cloneNode(true);
      node.querySelectorAll('.katex-html,annotation').forEach(duplicate => duplicate.remove());
    }
    return node.textContent.replace(/\s+/g,' ').trim().normalize('NFC');
  };
  Core.markText = (container,text,queryTerms) => {
    const ranges = queryTerms.flatMap(term => match(text,[term])).sort((a,b) => a[0] - b[0])
      .reduce((all,range) => {
        const last = all.at(-1);
        if (last && range[0] <= last[1]) last[1] = Math.max(last[1],range[1]); else all.push(range);
        return all;
      },[]);
    let offset = 0;
    for (const [start,end] of ranges) {
      container.append(document.createTextNode(text.slice(offset,start)));
      const mark = document.createElement('mark'); mark.textContent = text.slice(start,end); container.append(mark); offset = end;
    }
    container.append(document.createTextNode(text.slice(offset)));
  };

  const panel = document.getElementById('collection-search');
  if (!panel) return;
  const $ = id => document.getElementById(id);
  const form = panel.querySelector('form'), status = panel.querySelector('.search-status');
  const list = panel.querySelector('.search-results'), more = panel.querySelector('.search-more');
  const input = $('collection-query'), fields = ['document','kind','status','language'];
  let manifest, catalogRequest, matches = [], displayed = 0, request, run = 0, activeTerms = [], activeQuery = '';
  const cache = new Map();
  async function json(url, limit, signal) {
    const safe = new URL(url,location.href);
    if (safe.origin !== location.origin || !safe.pathname.startsWith('/Studies/search-data/')) throw new Error('Invalid index URL');
    const response = await fetch(safe,{ signal });
    if (!response.ok) throw new Error('Document index could not load');
    if (Number(response.headers.get('content-length')) > limit) throw new Error('Index is too large');
    const text = await response.text(); if (text.length > limit) throw new Error('Index is too large');
    return JSON.parse(text);
  }
  async function catalog() {
    if (manifest) return manifest;
    if (catalogRequest) return catalogRequest;
    catalogRequest = loadCatalog().finally(() => { catalogRequest = null; });
    return catalogRequest;
  }
  async function loadCatalog() {
    const data = await json(panel.dataset.manifest,200000);
    if (data.schema !== 1 || !Array.isArray(data.documents) || data.documents.length > 2000) throw new Error('Invalid search catalog');
    for (const doc of data.documents) {
      if (!/^[a-f0-9]{16}$/.test(doc.key) || !/^study-[a-f0-9]{16}\.json\?v=[a-f0-9]{16}$/.test(doc.index)) throw new Error('Invalid document index');
      passageURL(doc.url,{id:'test'},'',doc.version,location.origin);
    }
    manifest = data.documents;
    for (const doc of manifest) {
      const option = document.createElement('option'); option.value = doc.key; option.textContent = doc.title;
      $('search-document').append(option);
    }
    for (const language of [...new Set(manifest.map(doc => doc.language))].sort()) {
      const option = document.createElement('option'); option.value = language;
      option.textContent = language === 'en' ? 'English' : language === 'hi' ? 'Hindi' : language;
      $('search-language').append(option);
    }
    return manifest;
  }
  function displayNext() {
    const next = matches.slice(displayed,displayed + 20);
    for (const {doc,passage,hits} of next) {
      const li = document.createElement('li'), link = document.createElement('a'), description = document.createElement('p');
      link.href = passageURL(doc.url,passage,activeQuery,doc.version,location.origin);
      link.textContent = doc.title + ' · ' + passage.section;
      const metadata = document.createElement('p'); metadata.className = 'search-help';
      metadata.textContent = doc.kind === 'companion' ? 'Companion note' : (doc.status === 'released' ? 'Released study' : 'Draft study');
      Core.markText(description,excerpt(passage.text,hits),activeTerms);
      li.append(link,metadata,description); list.append(li);
    }
    displayed += next.length; more.hidden = displayed >= matches.length;
  }
  async function perform(remember = true) {
    const thisRun = ++run; request?.abort(); request = new AbortController();
    panel.removeAttribute('aria-busy');
    list.replaceChildren(); more.hidden = true; matches = []; displayed = 0;
    activeQuery = input.value;
    let queryTerms;
    try { queryTerms = terms(activeQuery); } catch (error) { status.textContent = error.message; return; }
    if (!queryTerms.length) { status.textContent = 'Enter a word or phrase to begin.'; return; }
    activeTerms = queryTerms; panel.setAttribute('aria-busy','true'); status.textContent = 'Searching selected documents…';
    try {
      const documents = await catalog(); if (thisRun !== run) return;
      const filtered = documents.filter(doc => fields.every(field => !$('search-' + field).value ||
        (field === 'document' ? doc.key : doc[field]) === $('search-' + field).value));
      if (remember) {
        const url = new URL(location.href); url.search = ''; url.searchParams.set('q',activeQuery);
        for (const field of fields) if ($('search-' + field).value) url.searchParams.set(field,$('search-' + field).value);
        history.replaceState(null,'',url);
      }
      let cursor = 0, failed = 0; const collected = [];
      const signal = request.signal;
      await Promise.all(Array.from({length:Math.min(4,filtered.length)},async () => {
        while (cursor < filtered.length && !signal.aborted) {
          const doc = filtered[cursor++];
          try {
            let data = cache.get(doc.index);
            if (!data) {
              data = await json(new URL(doc.index,new URL(panel.dataset.manifest,location.href)),5000000,signal);
              if (data.schema !== 1 || data.version !== doc.version || !Array.isArray(data.passages) || data.passages.length > 20000
                  || data.passages.some(p => typeof p.id !== 'string' || p.id.length > 400 || typeof p.text !== 'string' || p.text.length > 200000)) throw new Error('Stale document index');
              cache.set(doc.index,data);
            }
            for (const hit of search(data.passages,queryTerms)) collected.push({doc,...hit});
          } catch (error) { if (signal.aborted) throw error; failed++; }
          // Cached broad queries must still yield to typing, painting and cancellation.
          await new Promise(resolve => setTimeout(resolve,0));
        }
      }));
      if (thisRun !== run) return;
      matches = collected.sort((a,b) => a.doc.title.localeCompare(b.doc.title));
      status.textContent = `${matches.length} matching passage${matches.length === 1 ? '' : 's'} in ${filtered.length - failed} searched document${filtered.length - failed === 1 ? '' : 's'}.` +
        (failed ? ` ${failed} document${failed === 1 ? '' : 's'} could not load. Search again to retry.` : !matches.length ? ' Try fewer words or a different spelling.' : '');
      displayNext();
    } catch (error) {
      if (thisRun === run) status.textContent = 'Search could not load. Check your connection and search again.';
    } finally { if (thisRun === run) panel.removeAttribute('aria-busy'); }
  }
  let interacted = false;
  form.addEventListener('input',() => { interacted = true; });
  form.addEventListener('submit',event => { interacted = true; event.preventDefault(); perform(); });
  more.addEventListener('click',displayNext);
  for (const field of fields) $('search-' + field).addEventListener('change',() => { interacted = true; if (input.value.trim()) perform(); });
  const params = new URLSearchParams(location.search); input.value = (params.get('q') || '').slice(0,200);
  for (const field of fields) if (field !== 'document' && params.has(field)) $('search-' + field).value = params.get(field);
  catalog().then(() => {
    if (interacted) return;
    if (params.has('document')) $('search-document').value = params.get('document');
    if (input.value) perform(false);
  }).catch(() => { status.textContent = 'The search catalog could not load. Submit your search to retry.'; });
})();

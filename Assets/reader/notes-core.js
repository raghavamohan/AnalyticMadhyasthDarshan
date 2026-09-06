/* Portable annotation records and transactional, device-local storage. */
(() => {
  'use strict';
  const COLORS = ['yellow','green','blue','rose'];
  const LIMIT = 2000, PER_DOCUMENT = 200;
  const text = (value,max) => typeof value === 'string' && value.length <= max;
  const identifier = value => typeof value === 'string' && /^[a-zA-Z0-9_-]{8,80}$/.test(value);
  const documentPath = value => typeof value === 'string' && /^\/(Studies|Applications)\/[A-Za-z0-9-]+\/[A-Za-z0-9._-]+\.html$/.test(value);
  function valid(note) {
    return Boolean(note && identifier(note.id) && identifier(note.revision) && documentPath(note.document)
      && text(note.title,250) && /^[a-f0-9]{64}$/.test(note.version) && COLORS.includes(note.color)
      && text(note.quote,6000) && note.quote.trim() && text(note.note,12000)
      && text(note.created,40) && Number.isFinite(Date.parse(note.created))
      && text(note.updated,40) && Number.isFinite(Date.parse(note.updated))
      && Array.isArray(note.anchors) && note.anchors.length > 0 && note.anchors.length <= 20
      && note.anchors.every(a => a && text(a.id,400) && a.id && text(a.heading,400)
        && text(a.quote,6000) && a.quote && text(a.prefix,40) && text(a.suffix,40)
        && Number.isInteger(a.start) && a.start >= 0 && Number.isInteger(a.end) && a.end > a.start && a.end <= 200000)
      && note.anchors.reduce((n,a) => n + a.quote.length,0) <= 6000);
  }
  function record(raw) {
    if (!valid(raw)) throw new Error('This backup contains an invalid note. Nothing was imported.');
    const {id,revision,document,title,version,color,quote,note,created,updated} = raw;
    return {id,revision,document,title,version,color,quote,note,created,updated,
      anchors:raw.anchors.map(({id,heading,quote,prefix,suffix,start,end}) => ({id,heading,quote,prefix,suffix,start,end}))};
  }
  function limits(notes) {
    if (notes.length > LIMIT) throw new Error(`Keep up to ${LIMIT} notes on this device. Export older notes first.`);
    const counts = new Map();
    for (const n of notes) counts.set(n.document,(counts.get(n.document) || 0) + 1);
    if ([...counts.values()].some(n => n > PER_DOCUMENT)) throw new Error(`Keep up to ${PER_DOCUMENT} notes per document. Export older notes first.`);
    if (new TextEncoder().encode(JSON.stringify(notes,null,2)).byteLength > 8000000) throw new Error('Your notes exceed the 8 MB storage limit. Export and remove older notes first.');
  }
  function backup(notes) { return JSON.stringify({format:'amd-study-notes',schema:1,notes:notes.map(record)},null,2) + '\n'; }
  function parseBackup(value) {
    if (value.length > 10000000) throw new Error('Choose a backup smaller than 10 MB.');
    let data;
    try { data = JSON.parse(value); } catch (_) { throw new Error('Choose a valid JSON notes backup.'); }
    if (data?.format !== 'amd-study-notes' || data.schema !== 1 || !Array.isArray(data.notes)) throw new Error('This notes backup format is not supported.');
    const notes = data.notes.map(record); limits(notes);
    if (new Set(notes.map(n => n.id)).size !== notes.length) throw new Error('This backup contains repeated note identifiers. Nothing was imported.');
    return notes;
  }
  function link(note, origin = 'https://analyticmadhyasthdarshan.org') {
    const url = new URL(note.document,origin), anchor = note.anchors[0];
    url.hash = anchor.id; url.searchParams.set('pv',note.version.slice(0,16));
    if (anchor.heading) url.searchParams.set('section',anchor.heading);
    return url.href;
  }
  function markdown(notes) {
    return '# Study notes\n\nPrivate notes exported from this device. Source versions and quoted passages are retained.\n\n' + notes.map(n =>
      `## ${n.title.replace(/[\r\n]/g,' ')}\n\nSource: <${link(n)}>\n\nVersion: ${n.version}\n\nCreated: ${n.created}\nUpdated: ${n.updated}\nHighlight: ${n.color}\n\n` +
      n.quote.split('\n').map(line => '> ' + line).join('\n') + '\n\n' + n.note + '\n').join('\n');
  }
  function resolve(anchor, passages) {
    const matches = (passage, contextual) => {
      const result = [], source = passage.text;
      for (let from = 0; from < source.length;) {
        const start = source.indexOf(anchor.quote,from); if (start < 0) break;
        const end = start + anchor.quote.length;
        if (!contextual || ((!anchor.prefix || source.slice(Math.max(0,start - anchor.prefix.length),start) === anchor.prefix)
            && (!anchor.suffix || source.slice(end,end + anchor.suffix.length) === anchor.suffix))) result.push({passage,start,end});
        from = start + 1;
      }
      return result;
    };
    const original = passages.find(p => p.id === anchor.id);
    if (original) {
      const found = matches(original,false);
      if (found.length === 1) return found[0];
      const contextual = matches(original,true);
      if (contextual.length === 1) return contextual[0];
    }
    const found = passages.filter(p => p.heading === anchor.heading).flatMap(p => matches(p,true));
    return found.length === 1 ? found[0] : null;
  }
  function makeAnchor(passage,start,end) {
    return {id:passage.id,heading:passage.heading,quote:passage.text.slice(start,end),start,end,
      prefix:passage.text.slice(Math.max(0,start - 40),start),suffix:passage.text.slice(end,end + 40)};
  }
  const Core = {COLORS,LIMIT,PER_DOCUMENT,valid,record,documentPath,limits,backup,parseBackup,link,markdown,resolve,makeAnchor};
  if (typeof module !== 'undefined' && module.exports) module.exports = Core;
  if (typeof window === 'undefined') return;
  window.AMDNotes = Core;

  Core.openStore = async () => {
    const db = await new Promise((resolve,reject) => {
      let settled = false;
      const fail = error => { if (!settled) { settled = true; clearTimeout(timer); reject(error); } };
      const timer = setTimeout(() => fail(new Error('Device notes storage did not open.')),8000);
      const request = indexedDB.open('amd-study-notes',1);
      request.onupgradeneeded = () => request.result.createObjectStore('notes',{keyPath:'id'});
      request.onsuccess = () => { if (settled) { request.result.close(); return; } settled = true; clearTimeout(timer); resolve(request.result); };
      request.onerror = () => fail(request.error);
      request.onblocked = () => fail(new Error('Close other study tabs and retry opening your notes.'));
    });
    db.onversionchange = () => db.close();
    function transaction(update) {
      return new Promise((resolve,reject) => {
        const tx = db.transaction('notes',update ? 'readwrite' : 'readonly'), store = tx.objectStore('notes');
        let result, failure;
        const get = store.getAll(undefined,LIMIT + 1);
        get.onsuccess = () => {
          try {
            const notes = get.result.map(record); limits(notes);
            result = update ? update(notes,store) : notes;
          } catch (error) { failure = error; tx.abort(); }
        };
        tx.oncomplete = () => resolve(result);
        tx.onabort = tx.onerror = () => reject(failure || tx.error || new Error('Notes could not be saved.'));
      });
    }
    return {
      all:() => transaction(),
      put:(note,expected = null) => transaction((notes,store) => {
        const value = record(note), old = notes.find(n => n.id === value.id);
        if ((old?.revision || null) !== expected) throw new Error('This note changed in another tab. Your text is still here; reload the saved note before editing it again.');
        limits([...notes.filter(n => n.id !== value.id),value]); store.put(value); return value;
      }),
      remove:(id,expected) => transaction((notes,store) => {
        const old = notes.find(n => n.id === id);
        if (old && old.revision !== expected) throw new Error('This note changed in another tab. Review its latest text before deleting.');
        store.delete(id);
      }),
      restore:incoming => transaction((notes,store) => {
        const known = new Map(notes.map(n => [n.id,n])); let added = 0, skipped = 0;
        for (const raw of incoming) {
          let n = record(raw);
          if (known.has(n.id)) {
            if (JSON.stringify(known.get(n.id)) === JSON.stringify(n)) { skipped++; continue; }
            n = {...n,id:crypto.randomUUID(),revision:crypto.randomUUID()};
          }
          known.set(n.id,n); store.put(n); added++;
        }
        limits([...known.values()]); return {added,skipped};
      })
    };
  };
})();

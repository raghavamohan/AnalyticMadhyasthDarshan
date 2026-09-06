/* Contributor drafts stay in this browser. No credentials are stored here. */
(function (root) {
  'use strict';
  const MAX = 100;
  function key(context) {
    return JSON.stringify(['v1', context.account.toLowerCase(), context.kind,
      context.mode || '', context.slug || '', context.artifact || '', context.target || '', context.file || '', context.pr || '']);
  }
  function validate(data) {
    if (!data || typeof data !== 'object' || JSON.stringify(data).length > 18000000)
      throw new Error('This draft exceeds the browser draft limit. Download your source before leaving.');
    for (const name of ['title','category','desc','summary','fam','content','author','proposal','fileName']) {
      if (data[name] != null && (typeof data[name] !== 'string' || data[name].length > 2100000)) throw new Error('This draft has an invalid text field. Nothing was imported.');
    }
    if (data.source && (typeof data.source.content !== 'string' || data.source.content.length > 2100000 || !/^[a-f0-9]{40,64}$/.test(data.source.sha || ''))) throw new Error('This draft has an invalid source version. Nothing was imported.');
    if (data.operation && (!/^[0-9a-f-]{36}$/i.test(data.operation.id || '') || !['/api/propose','/api/submit','/api/revise'].includes(data.operation.path))) throw new Error('This draft has an invalid submission receipt. Nothing was imported.');
    if (data.presentation && (typeof data.presentation.contentBase64 !== 'string' || data.presentation.contentBase64.length > 14000000 || !/^[A-Za-z0-9+/]*={0,2}$/.test(data.presentation.contentBase64) || !/^[A-Za-z0-9-]+\.pptx$/i.test(data.presentation.fileName || ''))) throw new Error('This draft has an invalid presentation. Nothing was imported.');
    return data;
  }
  function open(name = 'amd-contributor-drafts') {
    return new Promise((resolve, reject) => {
      let done = false;
      const fail = error => { if (!done) { done = true; clearTimeout(timer); reject(error); } };
      const timer = setTimeout(() => fail(new Error('Browser draft storage did not open. Download a backup before leaving.')), 8000);
      const request = indexedDB.open(name, 1);
      request.onupgradeneeded = () => {
        request.result.createObjectStore('drafts', {keyPath:'key'});
        request.result.createObjectStore('metadata', {keyPath:'key'});
      };
      request.onerror = () => fail(request.error);
      request.onblocked = () => fail(new Error('Close other contribution tabs and retry saving.'));
      request.onsuccess = () => {
        const db = request.result;
        if (done) { db.close(); return; }
        done = true; clearTimeout(timer);
        db.onversionchange = () => db.close();
        function transact(write, context, action) {
          return new Promise((yes,no) => {
            const tx = db.transaction(['drafts','metadata'],write ? 'readwrite' : 'readonly');
            const drafts = tx.objectStore('drafts'), metadata = tx.objectStore('metadata');
            let result, error;
            const get = metadata.getAll(undefined,MAX + 1);
            const fail = err => { error=err; tx.abort(); };
            get.onsuccess = () => {
              const run = old => { try { result = action(get.result,old,drafts,metadata); } catch(err) {fail(err);} };
              if (context) { const current = drafts.get(key(context)); current.onsuccess = () => run(current.result || null); }
              else run(null);
            };
            tx.oncomplete = () => yes(result);
            tx.onabort = tx.onerror = () => no(error || tx.error || new Error('Draft save failed. Download a backup before leaving.'));
          });
        }
        resolve({
          all:account => transact(false,null,rows => rows.filter(r => r.context.account.toLowerCase() === account.toLowerCase())),
          get:context => transact(false,context,(_,old) => old),
          put:(context,data,expected=null,checkpoint=false) => transact(true,context,(rows,old,drafts,metadata) => {
            validate(data);
            const id=key(context);
            if ((old?.revision || null) !== expected) throw new Error('Another tab changed this draft. Download your current work, then recover the saved version.');
            if (!old && rows.length >= MAX) throw new Error('This browser has 100 drafts. Download and remove older drafts first.');
            const now=new Date().toISOString();
            const previous=checkpoint && old ? {data:old.data,saved:old.saved} : old?.previous || null;
            const record={key:id,context,data,revision:crypto.randomUUID(),saved:now,previous};
            const bytes=new TextEncoder().encode(JSON.stringify(record)).byteLength;
            if (rows.filter(r => r.key !== id).reduce((sum,r) => sum+r.bytes,0)+bytes > 64000000)
              throw new Error('Contributor drafts exceed 64 MB. Download and remove older drafts before saving more.');
            drafts.put(record); metadata.put({key:id,context,saved:now,bytes,data:{title:typeof data.title === 'string' ? data.title : ''},pending:Boolean(data.operation)});
            return record;
          }),
          remove:(context,expected) => transact(true,context,(_,old,drafts,metadata) => {
            if (old && old.revision !== expected) throw new Error('This draft changed in another tab. Refresh the saved drafts first.');
            drafts.delete(key(context)); metadata.delete(key(context));
          }),
          clear:account => transact(true,null,(rows,_,drafts,metadata) => {
            const selected=rows.filter(r => r.context.account.toLowerCase() === account.toLowerCase());
            if (selected.some(r => r.pending)) throw new Error('Check pending submission results before removing their saved receipts.');
            for (const row of selected) {drafts.delete(row.key);metadata.delete(row.key);}
          }),
          close:() => db.close(),
        });
      };
    });
  }
  const api = {key, open, validate};
  if (typeof module !== 'undefined') module.exports = api;
  root.AMDContributorDrafts = api;
})(typeof window === 'undefined' ? globalThis : window);

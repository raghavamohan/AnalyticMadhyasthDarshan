/* Opt-in offline readers. No API, authenticated response or background caching. */
importScripts('/Assets/reader/offline-policy.js');
const P = self.AMDOfflinePolicy, origin = self.location.origin, jobs = new Map();
let entryCache;
self.addEventListener('activate',event => event.waitUntil(self.clients.claim()));
async function entries(fresh = false) {
  if (entryCache && !fresh) return entryCache;
  entryCache = (async () => {
  const cache = await caches.open(P.REGISTRY), keys = await cache.keys(), result = [];
  for (const key of keys) {
    try { const item = await (await cache.match(key)).json();
      if (P.record(item) && item.resources.every(url => typeof url === 'string' && P.resource(url,item.path,origin))) result.push(item);
    } catch (_) { /* Do not serve incomplete metadata. */ }
  }
  return result;
  })();
  try { return await entryCache; } catch (error) { entryCache = null; throw error; }
}
async function bounded(response,limit) {
  const reader = response.body.getReader(), chunks = []; let length = 0;
  try {
    for (;;) { const {done,value} = await reader.read(); if (done) break; length += value.byteLength;
      if (length > limit) throw new Error('A reading file exceeds its expected size. Your previous saved copy is retained.'); chunks.push(value);
    }
  } catch (error) { await reader.cancel().catch(() => {}); throw error; }
  const result = new Uint8Array(length); let offset = 0;
  for (const chunk of chunks) { result.set(chunk,offset); offset += chunk.byteLength; }
  return result;
}
async function save(path,port) {
  if (!P.documentPath(path)) throw new Error('Only a published study or companion can be saved.');
  const response = await fetch('/Studies/offline-manifest.json',{credentials:'omit',cache:'no-store'});
  if (!response.ok || response.redirected) throw new Error('The offline catalog could not load. Reconnect and retry.');
  const raw = new TextDecoder().decode(await bounded(response,2000000));
  const manifest = JSON.parse(raw);
  if (manifest.schema !== 1 || !Array.isArray(manifest.documents) || manifest.documents.length > 2000) throw new Error('Offline catalog is invalid.');
  const item = manifest.documents.find(doc => doc.path === path); if (!item) throw new Error('This document is not available for offline saving.');
  P.bundle(item,origin);
  const current = await entries(true), old = current.find(doc => doc.path === path), registry = await caches.open(P.REGISTRY);
  if (!old && current.length >= 30) throw new Error('Keep up to 30 offline documents. Remove an older saved copy first.');
  // A browser shutdown can interrupt staging. Reclaim only our unreferenced bundles.
  const live = new Set(current.map(doc => doc.cache));
  for (const name of await caches.keys()) if (new RegExp('^' + P.PREFIX + '[a-f0-9-]{36}$').test(name) && !live.has(name)) await caches.delete(name);
  const name = P.PREFIX + crypto.randomUUID(), cache = await caches.open(name);
  let bytes = 0, committed = false;
  try {
    for (const [index,asset] of item.resources.entries()) {
      port?.postMessage({progress:`Saving ${index + 1} of ${item.resources.length} files…`});
      const response = await fetch(asset.url,{credentials:'omit',cache:'no-store'});
      if (!response.ok || response.status !== 200 || response.redirected || response.type === 'opaque'
          || /private|no-store/i.test(response.headers.get('cache-control') || '')) throw new Error('A public reading file could not be saved. Retry when connected.');
      const content = await bounded(response,asset.bytes);
      const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256',content))].map(b => b.toString(16).padStart(2,'0')).join('');
      if (content.byteLength !== asset.bytes || hash !== asset.sha256) throw new Error('The site is being updated or a file is incomplete. Refresh the study and try again. Your previous saved copy is retained.');
      bytes += content.byteLength;
      const headers = new Headers(response.headers); headers.delete('content-encoding'); headers.delete('content-length');
      await cache.put(new URL(asset.url,origin),new Response(content,{status:200,headers}));
    }
    const record = {path:item.path,title:item.title,version:item.version,savedAt:new Date().toISOString(),bytes,cache:name,resources:item.resources.map(r => r.url)};
    await registry.put(new URL(P.key(path),origin),new Response(JSON.stringify(record),{headers:{'Content-Type':'application/json'}}));
    committed = true;
    entryCache = null;
    if (old) await caches.delete(old.cache).catch(() => {});
    return record;
  } catch (error) { if (!committed) await caches.delete(name); throw error; }
}
async function remove(path) {
  const item = (await entries(true)).find(doc => doc.path === path);
  if (!item) return;
  const registry = await caches.open(P.REGISTRY);
  await registry.delete(new URL(P.key(path),origin)); entryCache = null; await caches.delete(item.cache);
}
self.addEventListener('message',event => {
  const port = event.ports[0], data = event.data;
  if (!port || !event.source?.url || new URL(event.source.url).origin !== origin || !data) return;
  event.waitUntil((async () => {
    try {
      if (data.type === 'LIST') { port.postMessage({result:await entries(true)}); return; }
      if (!['SAVE','REMOVE'].includes(data.type) || !P.documentPath(data.path)) throw new Error('Invalid offline action.');
      // Serialise every mutation, including concurrent tabs, to protect quotas and replacements.
      const previous = jobs.get('write') || Promise.resolve();
      const job = previous.catch(() => {}).then(() => data.type === 'SAVE' ? save(data.path,port) : remove(data.path));
      jobs.set('write',job);
      let result;
      try { result = await job; } finally { if (jobs.get('write') === job) jobs.delete('write'); }
      port.postMessage({result:result || null});
    } catch (error) { port.postMessage({error:error.message || 'Offline saving failed. The previous copy is retained.'}); }
  })());
});
async function cached(request,event) {
  const url = new URL(request.url), all = await entries();
  let path = url.pathname;
  if (!P.navigation(request.url,origin)) {
    const client = event.clientId && await self.clients.get(event.clientId);
    path = client ? new URL(client.url).pathname : '';
  }
  const ordered = all.slice().sort((a,b) => Number(b.path === path) - Number(a.path === path));
  for (const item of ordered) {
    if (request.mode === 'navigate' && item.path !== path && path !== '/Studies/notebook.html') continue;
    if (!P.resource(request.mode === 'navigate' ? new URL(path,origin).href : request.url,item.path,origin)) continue;
    if (!await caches.has(item.cache)) continue;
    const cache = await caches.open(item.cache), key = request.mode === 'navigate' ? new URL(path,origin) : request;
    const hit = await cache.match(key); if (!hit) continue;
    if (request.mode !== 'navigate') return hit;
    const html = (await hit.text()).replace('<html ','<html data-offline-copy="" '), headers = new Headers(hit.headers);
    headers.delete('content-length'); headers.delete('content-encoding');
    return new Response(html,{status:200,headers});
  }
  return null;
}
self.addEventListener('fetch',event => {
  const request = event.request, url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== origin) return;
  const navigate = request.mode === 'navigate';
  if (navigate ? !P.navigation(request.url,origin) : !/^\/Assets\/(reader|Mermaid|KaTeX\/fonts|Icons)\//.test(url.pathname)
      && !/^\/(Studies|Applications)\/[A-Za-z0-9-]+\/[A-Za-z0-9._-]+\.(svg|png|jpg|jpeg|webp)$/.test(url.pathname)) return;
  event.respondWith((async () => {
    // Immutable, content-versioned assets are safe to reuse; document HTML stays network-first.
    const hit = await cached(request,event);
    if (!hit) {
      try { return await fetch(request); }
      catch (error) {
        if (!navigate) throw error;
        return new Response('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Study not saved</title><h1>This study is not saved offline</h1><p>Reconnect to open it, or choose a saved study.</p><p><a href="/Studies/notebook.html">My notes &amp; saved studies</a></p></html>',{status:503,headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}});
      }
    }
    if (!navigate && /^[a-f0-9]{16}$/.test(url.searchParams.get('v') || '')) return hit;
    const abort = new AbortController(), timer = setTimeout(() => abort.abort(),4000);
    try { return await fetch(request,{signal:abort.signal}); }
    catch (_) {
      return hit;
    } finally { clearTimeout(timer); }
  })());
});

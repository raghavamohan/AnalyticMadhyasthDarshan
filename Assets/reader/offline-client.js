/* Register the narrowly scoped worker only after an explicit offline-save action. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id), registryName = 'amd-reader-offline-v1-registry';
  async function registration(create = false) {
    if (!isSecureContext || !('serviceWorker' in navigator) || !('caches' in window)) throw new Error('Offline saving needs HTTPS and browser storage support.');
    const existing = await navigator.serviceWorker.getRegistration('/');
    if (existing && !existing.active?.scriptURL.endsWith('/reader-sw.js') && !existing.installing?.scriptURL.endsWith('/reader-sw.js')) throw new Error('Another offline application controls this site. Offline saving is unavailable here.');
    if (!create) return existing;
    const reg = await navigator.serviceWorker.register('/reader-sw.js',{scope:'/',updateViaCache:'none'});
    await Promise.race([navigator.serviceWorker.ready,new Promise((_,reject) => setTimeout(() => reject(new Error('Offline setup is still starting. Try Save again.')),20000))]);
    return reg;
  }
  async function list() {
    if (!('caches' in window) || !await caches.has(registryName)) return [];
    const cache = await caches.open(registryName), entries = [];
    for (const key of await cache.keys()) { try { const item = await (await cache.match(key)).json(); if (window.AMDNotes.documentPath(item.path) && typeof item.savedAt === 'string'
      && Number.isFinite(Date.parse(item.savedAt)) && typeof item.title === 'string' && /^[a-f0-9]{64}$/.test(item.version)
      && Number.isInteger(item.bytes) && item.bytes > 0 && item.bytes <= 20000000 && /^amd-reader-offline-v1-[a-f0-9-]{36}$/.test(item.cache)) {
      const keys = await caches.has(item.cache) ? new Set((await (await caches.open(item.cache)).keys()).map(r => r.url)) : new Set();
      item.available = Array.isArray(item.resources) && item.resources.length > 0 && item.resources.every(url => keys.has(new URL(url,location.origin).href)); entries.push(item);
    } } catch (_) { /* An incomplete record is never advertised as available. */ } }
    return entries;
  }
  async function action(type,path,progress) {
    const reg = await registration(type === 'SAVE'); if (!reg?.active) throw new Error('Reconnect and open offline tools before changing saved copies.');
    return new Promise((resolve,reject) => {
      const channel = new MessageChannel();
      const timer = setTimeout(() => { channel.port1.close(); reject(new Error('Saving is taking longer than expected. Recheck saved copies before retrying.')); },180000);
      channel.port1.onmessage = event => {
        if (event.data?.progress) { progress?.(event.data.progress); return; }
        clearTimeout(timer); channel.port1.close(); event.data?.error ? reject(new Error(event.data.error)) : resolve(event.data.result);
      };
      reg.active.postMessage({type,path},[channel.port2]);
    });
  }
  function description(item) {
    return `${item.available === false ? 'Copy incomplete or removed by the browser.' : 'Saved'} ${new Date(item.savedAt).toLocaleString()} · ${(item.bytes / 1048576).toFixed(1)} MB · version ${item.version.slice(0,8)}.`;
  }
  let wired = false;
  async function reader(path) {
    const status = $('offline-status');
    async function check() {
      const item = (await list()).find(n => n.path === path), current = document.querySelector('meta[name="amd-source-version"]')?.content;
      status.textContent = item ? description(item) + (item.version !== current ? ' This open study has a different version. Save again to update the copy.' : '') : 'This document is not saved offline.';
      $('offline-remove').hidden = !item; $('offline-save').textContent = item ? 'Update offline copy' : 'Save for offline reading';
    }
    if (!wired) {
      wired = true;
      $('offline-save').addEventListener('click',async () => {
        $('offline-save').disabled = $('offline-remove').disabled = true;
        try { status.textContent = 'Preparing offline reading…'; await action('SAVE',path,text => { status.textContent = text; }); await check(); }
        catch (error) { status.textContent = error.message; }
        finally { $('offline-save').disabled = $('offline-remove').disabled = false; }
      });
      $('offline-remove').addEventListener('click',async () => {
        try { await action('REMOVE',path); await check(); status.textContent = 'Saved study copy removed. Your notes and bookmarks are retained.'; }
        catch (error) { status.textContent = error.message; }
      });
    }
    try { await check(); } catch (_) { status.textContent = 'Browser storage is unavailable. Offline copies could not be checked.'; }
  }
  async function library() {
    const status = $('offline-library-status'), root = $('offline-library'); root.replaceChildren();
    try {
      const items = await list(); status.textContent = items.length ? `${items.length} saved documents. Open one using its title.` : 'No offline studies yet. In a study, open Display → Offline reading to save it.';
      for (const item of items) {
        const li = document.createElement('li'), link = document.createElement('a'), details = document.createElement('p'), remove = document.createElement('button');
        link.href = item.path; link.textContent = item.title; details.textContent = description(item); remove.type = 'button'; remove.textContent = 'Remove saved copy';
        remove.addEventListener('click',async () => { try { remove.disabled = true; await action('REMOVE',item.path); await library(); } catch (error) { status.textContent = error.message; remove.disabled = false; } });
        li.append(link,details,remove); root.append(li);
      }
    } catch (_) { status.textContent = 'Saved copies could not be read. Browser storage may be unavailable.'; }
  }
  window.AMDOffline = {reader,library,list,action};
})();

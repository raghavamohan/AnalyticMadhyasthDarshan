/* The service worker may save only explicit public reader bundles. */
(() => {
  'use strict';
  const PREFIX = 'amd-reader-offline-v1-', REGISTRY = PREFIX + 'registry';
  const documentPath = value => typeof value === 'string' && /^\/(Studies|Applications)\/[A-Za-z0-9-]+\/[A-Za-z0-9._-]+\.html$/.test(value);
  const key = path => '/__amd_offline__/' + encodeURIComponent(path);
  function record(item) {
    return item && documentPath(item.path) && typeof item.title === 'string' && item.title.length <= 250
      && /^[a-f0-9]{64}$/.test(item.version) && typeof item.savedAt === 'string' && Number.isFinite(Date.parse(item.savedAt))
      && Number.isInteger(item.bytes) && item.bytes > 0 && item.bytes <= 20000000
      && typeof item.cache === 'string' && new RegExp('^' + PREFIX + '[a-f0-9-]{36}$').test(item.cache)
      && Array.isArray(item.resources) && item.resources.length > 0 && item.resources.length <= 150;
  }
  function resource(value,document,origin) {
    const url = new URL(value,origin), base = new URL(origin);
    if (url.origin !== base.origin || url.hash || url.username || url.password || [...url.searchParams.keys()].some(k => k !== 'v')) return false;
    const path = url.pathname, parent = document.slice(0,document.lastIndexOf('/') + 1);
    return path === document || path === '/Studies/notebook.html'
      || /^\/Assets\/reader\/[a-z-]+\.(js|css)$/.test(path)
      || /^\/Assets\/Mermaid\/mermaid\.min\.js$/.test(path)
      || /^\/Assets\/KaTeX\/fonts\/[A-Za-z0-9_-]+\.woff2$/.test(path)
      || /^\/Assets\/Icons\/[A-Za-z0-9_.-]+\.(svg|png|ico)$/.test(path)
      || (path.startsWith(parent) && /^[A-Za-z0-9_.-]+\.(svg|png|jpg|jpeg|webp)$/.test(path.slice(parent.length)));
  }
  function bundle(value,origin) {
    if (!value || !documentPath(value.path) || typeof value.title !== 'string' || value.title.length > 250
        || !/^[a-f0-9]{64}$/.test(value.version) || !Array.isArray(value.resources) || !value.resources.length || value.resources.length > 150) throw new Error('Invalid offline document bundle.');
    if (value.resources.some(r => !r || typeof r.url !== 'string' || !resource(r.url,value.path,origin)
      || !/^[a-f0-9]{64}$/.test(r.sha256) || !Number.isInteger(r.bytes) || r.bytes <= 0 || r.bytes > 8000000)) throw new Error('Unsafe or oversized offline resource.');
    if (value.resources.reduce((sum,r) => sum + r.bytes,0) > 20000000 || new Set(value.resources.map(r => r.url)).size !== value.resources.length
        || !value.resources.some(r => r.url === value.path) || !value.resources.some(r => r.url === '/Studies/notebook.html')) throw new Error('Incomplete offline document bundle.');
    return value;
  }
  function navigation(url,origin) {
    const parsed = new URL(url,origin);
    return parsed.origin === new URL(origin).origin && ![...parsed.searchParams.keys()].some(k => !['find','section','pv','v'].includes(k))
      && (documentPath(parsed.pathname) || parsed.pathname === '/Studies/notebook.html');
  }
  const Core = {PREFIX,REGISTRY,documentPath,key,resource,bundle,navigation,record};
  if (typeof module !== 'undefined' && module.exports) module.exports = Core;
  if (typeof self !== 'undefined') self.AMDOfflinePolicy = Core;
})();

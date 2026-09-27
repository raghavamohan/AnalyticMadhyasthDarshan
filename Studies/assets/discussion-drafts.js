/* Browser-local discussion drafts. Ownership here is a recovery boundary,
 * never server authorization. No emails, cookies or sign-in tokens are stored. */
(function (root) {
  'use strict';
  function create(storage, slug) {
    const prefix = 'amd-discussion-draft-v1:' + JSON.stringify(slug) + ':';
    const revisions = new Map();
    const key = (owner, parent = '') => prefix + JSON.stringify([owner, parent]);
    function get(owner, parent = '') {
      const id = key(owner, parent), raw = storage.getItem(id);
      const row = raw ? JSON.parse(raw) : null;
      if (row && (row.owner !== owner || row.parent !== parent || typeof row.body !== 'string' || row.body.length > 8192))
        throw new Error('This browser draft cannot be read. Download your text before leaving.');
      revisions.set(id, row?.revision || null);
      return row;
    }
    function put(owner, parent, body) {
      if (!owner || typeof body !== 'string' || body.length > 8192) throw new Error('Invalid discussion draft.');
      const id = key(owner, parent), raw = storage.getItem(id), row = raw ? JSON.parse(raw) : null;
      if ((row?.revision || null) !== (revisions.get(id) || null))
        throw new Error('Another tab changed this draft. Download your text before reloading.');
      if (!body) { storage.removeItem(id); revisions.set(id, null); return; }
      if (row?.body === body) return;
      const next = {owner, parent, body, revision:crypto.randomUUID(), saved:Date.now()};
      storage.setItem(id, JSON.stringify(next)); revisions.set(id, next.revision);
    }
    function list(owner) {
      const rows = [];
      for (let i = 0; i < storage.length; i++) {
        const id = storage.key(i);
        if (!id?.startsWith(prefix)) continue;
        const context = JSON.parse(id.slice(prefix.length));
        if (context[0] === owner) {
          const row = JSON.parse(storage.getItem(id));
          if (row && row.owner === owner && typeof row.body === 'string' && row.body.length <= 8192) {
            if (!revisions.has(id)) revisions.set(id, row.revision || null);
            rows.push(row);
          }
        }
      }
      return rows.sort((a, b) => b.saved - a.saved);
    }
    return {get, put, list};
  }
  root.AMDDiscussionDrafts = {create};
  if (typeof module !== 'undefined') module.exports = {create};
})(typeof window === 'undefined' ? globalThis : window);

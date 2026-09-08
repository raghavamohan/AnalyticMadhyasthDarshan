(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.AMDContributorActionOperations = api;
})(typeof self !== 'undefined' ? self : globalThis, function () {
  'use strict';

  const PREFIX = 'amd-contributor-action-v1:';
  const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const SLUG = /^[A-Za-z0-9-]{1,60}$/;
  const PATHS = new Set(['/api/status-change', '/api/delete-artifact']);

  function accountName(value) {
    const account = String(value || '').trim().toLowerCase();
    if (!/^[a-z0-9-]{1,39}$/.test(account)) throw new Error('The signed-in GitHub account is invalid. Refresh sign-in before continuing.');
    return account;
  }

  function key(account) {
    return PREFIX + accountName(account);
  }

  function cleanPayload(path, value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('The saved action receipt has an invalid request.');
    if ('turnstileToken' in value || 'operationId' in value) throw new Error('The saved action receipt contains transient credentials.');
    const slug = String(value.slug || '').trim();
    if (!SLUG.test(slug)) throw new Error('The saved action receipt has an invalid study slug.');
    if (path === '/api/status-change') {
      const targetStatus = String(value.targetStatus || '').trim().toLowerCase();
      if (!['draft', 'released'].includes(targetStatus)) throw new Error('The saved status-change receipt has an invalid target status.');
      const reason = String(value.reason || '');
      if (reason.length > 2000) throw new Error('The saved status-change reason is too long.');
      return {slug, targetStatus, reason};
    }
    const artifactType = String(value.artifactType || '').trim().toLowerCase();
    if (!['study', 'note', 'presentation'].includes(artifactType)) throw new Error('The saved deletion receipt has an invalid artifact type.');
    const fileName = String(value.fileName || '').trim();
    if (fileName.length > 240 || (artifactType !== 'study' && !fileName)) throw new Error('The saved deletion receipt has an invalid filename.');
    return {slug, artifactType, fileName};
  }

  function validate(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('The saved dashboard action receipt is invalid.');
    if (!UUID_V4.test(value.id)) throw new Error('The saved dashboard action receipt has an invalid identifier.');
    if (!PATHS.has(value.path)) throw new Error('The saved dashboard action receipt has an invalid route.');
    const created = String(value.created || '');
    if (!created || Number.isNaN(Date.parse(created))) throw new Error('The saved dashboard action receipt has an invalid timestamp.');
    if (value.blockedBy != null && !UUID_V4.test(value.blockedBy)) throw new Error('The saved dashboard action receipt has an invalid blocking identifier.');
    const state = value.state == null ? null : String(value.state);
    if (state && !['notStarted', 'inProgress', 'uncertain'].includes(state)) throw new Error('The saved dashboard action receipt has an invalid state.');
    return {
      id: value.id,
      path: value.path,
      payload: cleanPayload(value.path, value.payload),
      created,
      retryAllowed: Boolean(value.retryAllowed),
      ...(value.blockedBy ? {blockedBy: value.blockedBy} : {}),
      ...(state ? {state} : {}),
    };
  }

  function create(storage) {
    if (!storage || typeof storage.getItem !== 'function' || typeof storage.setItem !== 'function' || typeof storage.removeItem !== 'function') {
      throw new Error('Browser receipt storage is unavailable. No action was sent.');
    }
    return {
      load(account) {
        const raw = storage.getItem(key(account));
        if (!raw) return null;
        try { return validate(JSON.parse(raw)); }
        catch (error) { throw new Error('The saved dashboard action receipt could not be read. Preserve this browser profile and ask a maintainer for help. ' + error.message); }
      },
      save(account, operation) {
        const checked = validate(operation);
        storage.setItem(key(account), JSON.stringify(checked));
        return checked;
      },
      clear(account) {
        storage.removeItem(key(account));
      },
    };
  }

  return {key, validate, create};
});

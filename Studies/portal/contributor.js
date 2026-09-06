/* Form integration. Context changes and writes run in order; async source
 * results must also match the context and editor text they started with. */
function renderContributorFeedback(item) {
  const stage = item.stage;
  let next = stage === 'accepted' ? 'You: submit the first draft from this workspace.'
    : stage === 'changes_requested' ? 'You: address the review below, then send a revision.'
    : item.checks?.state === 'failure' ? 'You: open the failed check, correct the reported problem and update the pull request. Ask a maintainer if the failure is infrastructure-related.'
    : ['approved','preparing'].includes(stage) ? 'Automation: preparing the study workspace. Refresh to check progress.'
    : stage === 'pending' ? 'Maintainer: review the proposal. You can add context on the GitHub issue.'
    : stage === 'pr-open' ? (item.checks?.state === 'pending' ? 'Automation: checks are running. Maintainer review follows; no resubmission is needed.' : 'Maintainer: review and merge the pull request. You can follow the conversation on GitHub.')
    : stage === 'merged' ? 'Publication follows the merge. Check the study link; its Draft or Released status is shown separately.'
    : 'Open the GitHub conversation for the decision and any suggested next steps.';
  let result = '<div class="contributor-feedback"><p><strong>Next action:</strong> ' + escapeHtml(next) + '</p>';
  for (const review of (item.feedback || []).slice(0,5)) {
    result += '<details open><summary>Review from @' + escapeHtml(review.reviewer) + '</summary><pre>' + escapeHtml(review.body || 'See the inline review comments on GitHub.') + '</pre><a target="_blank" rel="noopener" href="' + escapeHtml(safeGitHubUrl(review.url)) + '">Open review and inline comments</a></details>';
  }
  for (const check of (item.checks?.details || []).slice(0,8)) {
    result += '<details><summary>' + escapeHtml(check.name + ' — ' + check.conclusion) + '</summary><pre>' + escapeHtml([check.title,check.summary].filter(Boolean).join('\n') || 'Open the check for its error details.') + '</pre><a target="_blank" rel="noopener" href="' + escapeHtml(safeGitHubUrl(check.url)) + '">Open failed check</a></details>';
  }
  return result + '</div>';
}

const contributor = (() => {
  'use strict';
  const el = id => document.getElementById(id);
  const states = {submit:{}, propose:{}};
  let account = '', storePromise, queue = Promise.resolve(), timer;
  let epoch = 0;
  const store = () => storePromise || (storePromise = AMDContributorDrafts.open().catch(error => { storePromise = null; throw error; }));
  const serial = action => { const next = queue.then(action); queue = next.catch(() => {}); return next; };
  const status = (kind, message) => { el(kind + '-draft-status').textContent = message; };
  const context = kind => kind === 'propose' ? {account, kind, target:el('p-draft-id').value || 'new'} : {
    account, kind, mode:el('s-mode').value, slug:el('s-slug').value.trim(), artifact:selectedArtifactType(),
    target:el('s-target').value, pr:el('s-pr').value,
    file:el('s-target').value === '__new__' ? states.submit.fileName ?? new URLSearchParams(location.search).get('file') ?? '' : '',
  };
  function capture(kind) {
    if (kind === 'propose') return {title:el('p-title').value, category:el('p-category').value,
      desc:el('p-desc').value, summary:el('p-summary').value, fam:el('p-fam').value,
      formal:el('p-formal').checked, operation:states.propose.operation || null};
    return {content:el('s-content').value, author:el('s-author').value, proposal:states.submit.proposal ?? el('s-proposal').value,
      fileName:states.submit.fileName || '', presentation:uploadedPresentation,
      source:states.submit.source || null, operation:states.submit.operation || null};
  }
  function apply(kind, data = {}) {
    if (kind === 'propose') {
      for (const field of ['title','category','desc','summary']) el('p-' + field).value = data[field] || '';
      el('p-fam').value = data.fam || 'New to the texts'; el('p-formal').checked = Boolean(data.formal);
      resetProposeConfirm(); updateSlugPreview();
    } else {
      el('s-content').value = data.content || ''; el('s-author').value = data.author || '';
      el('s-diff').hidden = true;
      el('s-load-source-status').textContent = ''; el('s-load-source-status').style.display = 'none';
      if (data.proposal) setProposalValue(data.proposal);
      states.submit.proposal = data.proposal || el('s-proposal').value;
      el('s-file').value = ''; uploadedPresentation = data.presentation || null;
      states.submit.source = data.source || null;
      states.submit.fileName = data.fileName || (states.submit.context ? states.submit.context.file || '' : new URLSearchParams(location.search).get('file') || '');
      revisionLoadedForPr = data.source && el('s-mode').value === 'revise' ? el('s-pr').value : null;
      setFileStatus(uploadedPresentation ? `Recovered ${uploadedPresentation.fileName}; ready to submit.` : data.fileName ? `Recovered ${data.fileName} in the editor.` : '');
      setEditorMode('write'); applyAuthorDefault(); updateSubmitAvailability();
    }
    states[kind].operation = data.operation || null;
    paintOperation(kind);
  }
  function meaningful(kind, data) {
    return kind === 'propose' ? Boolean(data.title || data.desc || data.summary || data.operation)
      : Boolean(data.content || data.presentation || data.operation);
  }
  async function save(kind, checkpoint = false) {
    const state = states[kind];
    if (!state.context || !account) return;
    const data = capture(kind), signature = JSON.stringify(data);
    if (!meaningful(kind, data) && !state.record) { state.dirty = false; return; }
    if (signature === state.signature && !checkpoint) { state.dirty = false; return; }
    status(kind, 'Saving in this browser…');
    try {
      const record = await (await store()).put(state.context, data, state.record?.revision || null, checkpoint || state.firstEdit);
      state.record = record; state.signature = signature; state.firstEdit = false;
      state.dirty = JSON.stringify(capture(kind)) !== signature;
      status(kind, state.dirty ? 'Unsaved changes…' : 'Saved in this browser at ' + new Date(record.saved).toLocaleTimeString());
    } catch (error) { state.dirty = true; status(kind, error.message); throw error; }
  }
  function schedule(kind) {
    if (!account || !states[kind].context) return;
    states[kind].dirty = true; status(kind, 'Unsaved changes…');
    if (kind === 'submit') el('s-diff').hidden = true;
    clearTimeout(timer);
    timer = setTimeout(() => serial(async () => { await save('submit'); await save('propose'); }).catch(() => {}), 400);
  }
  async function restore(kind) {
    const state = states[kind], ctx = context(kind);
    state.context = ctx; state.record = null; state.firstEdit = true; state.dirty = false;
    apply(kind);
    const emptySignature = JSON.stringify(capture(kind));
    try {
      const record = await (await store()).get(ctx);
      state.record = record;
      if (JSON.stringify(capture(kind)) !== emptySignature) {
        state.dirty = true;
        status(kind, 'Your new text is kept. Use Recovery options to load the saved draft, or Save now to keep this version with a recovery copy.');
        return;
      }
      if (record) apply(kind, record.data);
      state.signature = JSON.stringify(capture(kind));
      status(kind, record ? 'Recovered browser draft saved ' + new Date(record.saved).toLocaleString() : 'Drafts save in this browser as you write.');
    } catch (error) { status(kind, error.message); }
  }
  function restoreContext(ctx) {
    if (ctx.kind === 'propose') { el('p-draft-id').value = ctx.target || 'new'; return; }
    configureSubmitView(ctx.mode);
    el('s-slug').value = ctx.slug; el('s-artifact').value = ctx.artifact; el('s-pr').value = ctx.pr;
    updateArtifactUi(); refreshMappedArtifactControls(); el('s-target').value = ctx.target;
    states.submit.fileName = ctx.file || '';
  }
  async function change(kind = 'submit', action) {
    const wanted = context(kind);
    return serial(async () => {
      const state = states[kind];
      try { await save(kind, true); }
      catch (error) { if (state.context) restoreContext(state.context); return false; }
      epoch++;
      if (action) action(); else restoreContext(wanted);
      await restore(kind);
      syncUrl();
      return true;
    });
  }
  function syncUrl() {
    const url = new URL(location.href);
    if (el('submit-tab').classList.contains('active')) {
      const ctx = context('submit');
      url.search = new URLSearchParams({tab:'submit', mode:ctx.mode, slug:ctx.slug, artifact:ctx.artifact, target:ctx.target, pr:ctx.pr}).toString();
      if (ctx.file) url.searchParams.set('file',ctx.file);
      if (el('s-proposal').value) url.searchParams.set('proposal', el('s-proposal').value);
    } else if (el('propose-tab').classList.contains('active')) {
      url.search = new URLSearchParams({tab:'propose', draft:el('p-draft-id').value}).toString();
    }
    history.replaceState(null, '', url.pathname + url.search);
  }
  function ticket() { return {epoch, account, key:AMDContributorDrafts.key(context('submit')), content:el('s-content').value}; }
  function matches(t) { return t.epoch === epoch && t.account === account && t.key === AMDContributorDrafts.key(context('submit')) && t.content === el('s-content').value; }
  function source(data) { states.submit.source = {content:data.content, sha:data.sourceSha}; }
  function download(kind) {
    const data = {format:'amd-contributor-draft', schema:1, context:states[kind].context || context(kind), data:capture(kind)};
    const blob = new Blob([JSON.stringify(data, null, 2) + '\n'], {type:'application/json'});
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = (data.context.slug || 'proposal') + '-draft.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function listDrafts() {
    const list = el('saved-draft-list'); list.replaceChildren();
    if (!account) return;
    try {
      const rows = await (await store()).all(account);
      for (const row of rows.sort((a,b) => b.saved.localeCompare(a.saved))) {
        const li = document.createElement('li'), open = document.createElement('button');
        open.type = 'button'; open.className = 'auth-btn';
        open.textContent = [row.context.slug || row.data.title || (row.context.kind === 'submit' ? 'Untitled draft' : 'Untitled proposal'), row.context.artifact, row.context.target === '__new__' ? row.context.file || 'New file' : row.context.target === 'new' ? '' : row.context.target, row.context.pr ? 'PR #' + row.context.pr : '', new Date(row.saved).toLocaleString()].filter(Boolean).join(' · ');
        open.onclick = async () => {
          if (await change(row.context.kind, () => restoreContext(row.context))) {
            switchTab(row.context.kind === 'propose' ? 'propose' : 'submit', false); syncUrl();
          }
        };
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'auth-btn'; remove.textContent = 'Remove';
      remove.setAttribute('aria-label','Remove draft ' + (row.context.slug || row.data.title || 'Untitled proposal'));
      remove.onclick = () => serial(async () => {
        if (!confirm('Remove this browser draft? Download a backup first if you need it.')) return;
        const db = await store(), latest = await db.get(row.context);
        if (latest?.data.operation) throw new Error('Check the submission result before removing its receipt.');
        await db.remove(row.context,latest?.revision);
        if (states[row.context.kind].context && AMDContributorDrafts.key(states[row.context.kind].context) === row.key) await restore(row.context.kind);
        await listDrafts();
      }).catch(error => { list.textContent = error.message; });
      li.append(open, ' ', remove); list.append(li);
      }
      if (!rows.length) list.textContent = 'No saved contributor drafts for this account.';
    } catch (error) { list.textContent = error.message; }
  }
  function paintOperation(kind) {
    const operation = states[kind].operation;
    el(kind + '-check-result').hidden = !operation;
    el(kind + '-operation-status').textContent = operation
      ? 'A submission receipt is saved. Check its result before sending again. Receipt: ' + operation.id : '';
  }
  async function begin(kind, path, payload) {
    if (account !== currentUser?.login?.toLowerCase()) throw new Error('Refresh sign-in before submitting. Your draft remains here.');
    if (states[kind].operation && !states[kind].operation.retryAllowed) throw new Error('Check the previous submission result before submitting again.');
    const id = states[kind].operation?.id || crypto.randomUUID();
    states[kind].operation = {id, path};
    states[kind].dirty = true;
    try { await serial(() => save(kind, true)); }
    catch (error) { states[kind].operation = null; throw error; }
    paintOperation(kind);
    return {...payload, operationId:id, ...(states.submit.source && kind === 'submit' ? {sourceSha:states.submit.source.sha} : {})};
  }
  async function complete(kind, data, certain = true) {
    if (!certain) {
      if (data?.operationId && states[kind].operation && data.operationId !== states[kind].operation.id) {
        states[kind].operation.blockedBy = data.operationId;
        await serial(() => save(kind));
      }
      paintOperation(kind); return;
    }
    const previous = states[kind].operation;
    states[kind].operation = null;
    try { await serial(() => save(kind, true)); }
    catch (error) { states[kind].operation = previous; paintOperation(kind); throw error; }
    paintOperation(kind);
    if (data?.success) status(kind, 'Submitted. A recovery copy remains in this browser.');
  }
  async function checkResult(kind) {
    const op = states[kind].operation, identity = account;
    if (!op) return;
    el(kind + '-operation-status').textContent = 'Checking the saved submission receipt…';
    try {
      const response = await apiFetch('/api/operation?id=' + encodeURIComponent(op.blockedBy || op.id));
      const data = await response.json();
      if (account !== identity || states[kind].operation?.id !== op.id) return;
      if (data.uncertain) {
        el(kind + '-operation-status').textContent = (data.error || 'The submission is still being checked.') + ' Receipt: ' + op.id;
        return;
      }
      if (data.notStarted) {
        states[kind].operation.retryAllowed = true;
        await serial(() => save(kind));
        el(kind + '-operation-status').textContent = 'The server has not recorded this attempt. Submit unchanged content to retry with the same receipt; a delayed first request cannot create a second copy.';
        return;
      }
      if (data.success || data.completed) {
        await complete(kind, data);
        showAlert(kind, data.success ? 'success' : 'info', data.success
          ? (op.blockedBy ? 'The earlier submission is confirmed. This draft has not been sent. ' : 'Submission confirmed. ') + '<a href="' + escapeHtml(safeGitHubUrl(data.url)) + '" target="_blank" rel="noopener">Open on GitHub</a>. ' + escapeHtml(data.warning || '')
          : escapeHtml(data.error || 'The server did not start this submission. You can submit when ready.'));
        dashboardCache = null;
      } else throw new Error(data.error || 'Could not check the submission.');
    } catch (error) { el(kind + '-operation-status').textContent = error.message + ' Your receipt is still saved.'; }
  }
  function compare() {
    const source = states.submit.source;
    const box = el('s-diff'); box.replaceChildren(); box.hidden = false;
    if (!source) { box.textContent = 'Load the current source before comparing. Your draft will be kept as a recovery copy.'; return; }
    const before = source.content.split('\n'), after = el('s-content').value.split('\n');
    let start = 0, left = before.length, right = after.length;
    while (start < left && start < right && before[start] === after[start]) start++;
    while (left > start && right > start && before[left-1] === after[right-1]) { left--; right--; }
    if (start === left && start === right) { box.textContent = 'No changes from the loaded source.'; return; }
    const summary = document.createElement('p');
    summary.textContent = `Changed region starts at line ${start + 1}: ${left - start} original lines, ${right - start} draft lines. Unchanged lines outside this region are omitted.`;
    box.append(summary);
    for (const [label, text] of [['Loaded source', before.slice(start,left).join('\n')], ['Your draft', after.slice(start,right).join('\n')]]) {
      const heading = document.createElement('h3'), pre = document.createElement('pre');
      heading.textContent = label; pre.textContent = text.length > 40000 ? text.slice(0,40000) + '\n[Display shortened. Download the draft for the full source.]' : text || '[No lines]';
      box.append(heading, pre);
    }
  }
  for (const kind of ['submit','propose']) {
    el(kind + '-save-now').onclick = () => serial(() => save(kind)).catch(() => {});
    el(kind + '-download-draft').onclick = () => download(kind);
    el(kind + '-check-result').onclick = () => checkResult(kind);
    el(kind + '-recover-draft').onclick = () => serial(async () => {
      const record = await (await store()).get(states[kind].context);
      if (!record) { status(kind, 'No saved draft to recover.'); return; }
      if (!confirm('Recover the saved draft? Download your current text first if you want to keep it.')) return;
      states[kind].record = record; apply(kind, record.data); states[kind].dirty = false;
      states[kind].signature = JSON.stringify(capture(kind)); status(kind, 'Recovered the latest saved draft.');
    }).catch(error => status(kind, error.message));
    el(kind + '-recover-previous').onclick = () => serial(async () => {
      const old = states[kind].record?.previous || (kind === 'submit' && states.submit.source ? {data:{...capture(kind),content:states.submit.source.content},saved:states[kind].record?.saved} : null);
      if (!old) { status(kind, 'No earlier recovery copy exists yet.'); return; }
      if (states[kind].operation) throw new Error('Check the submission result before recovering an earlier copy.');
      const baseline = states.submit.source;
      await save(kind, true); apply(kind, {...old.data, source:baseline || old.data.source, operation:null}); states[kind].dirty = true;
      await save(kind); status(kind, 'Recovered the earlier copy from ' + new Date(old.saved).toLocaleString());
    }).catch(error => status(kind, error.message));
  }
  el('saved-drafts-refresh').onclick = listDrafts;
  el('clear-account-drafts').onclick = () => serial(async () => {
    if (!account || !confirm('Remove all contributor drafts for @' + account + ' from this browser? Download any backups you need first.')) return;
    if (Object.values(states).some(s => s.operation)) throw new Error('Check pending submission results before clearing their receipts.');
    await (await store()).clear(account);
    for (const kind of ['submit','propose']) { await restore(kind); status(kind, 'Contributor drafts removed from this browser.'); }
    await listDrafts();
  }).catch(error => { el('saved-draft-list').textContent = error.message; });
  el('s-compare').onclick = compare;
  el('recover-legacy-draft').onclick = async () => {
    try {
      const submit = JSON.parse(localStorage.getItem('amd-submit-draft') || 'null');
      const proposal = JSON.parse(localStorage.getItem('amd-propose-draft') || 'null');
      if (!submit && !proposal) return;
      if (!confirm('Older drafts were not assigned to an account. Recover them for @' + account + ' only if they belong to you. Current drafts will be kept as recovery copies.')) return;
      for (const [kind,data,key] of [['submit',submit,'amd-submit-draft'],['propose',proposal,'amd-propose-draft']]) {
        if (!data) continue;
        AMDContributorDrafts.validate(data);
        if (kind === 'submit' && !/^[A-Za-z0-9-]*$/.test(data.slug || '')) throw new Error('The older draft has an invalid study slug.');
        if (!await change(kind, () => {
          if (kind === 'submit') restoreContext({kind,mode:data.isNew === false ? 'update' : 'new',slug:data.slug || '',artifact:'study',target:'',pr:''});
          else el('p-draft-id').value = crypto.randomUUID();
        })) return;
        if (states[kind].operation) throw new Error('Check the saved submission receipt first.');
        await serial(async () => { await save(kind,true); apply(kind,data); states[kind].dirty=true; await save(kind); });
        localStorage.removeItem(key);
      }
      el('recover-legacy-draft').hidden=true; await listDrafts();
    } catch(error) { el('saved-draft-list').textContent=error.message; }
  };
  el('p-new-draft').onclick = () => change('propose', () => { el('p-draft-id').value = crypto.randomUUID(); }).then(syncUrl);
  el('draft-import').onchange = async event => {
    const file = event.target.files?.[0]; if (!file || !account) return;
    try {
      if (file.size > 18000000) throw new Error('Choose a contributor backup smaller than 18 MB.');
      const value = JSON.parse(await file.text());
      if (value.format !== 'amd-contributor-draft' || value.schema !== 1 || !['submit','propose'].includes(value.context?.kind)) throw new Error('Choose a contributor draft JSON backup.');
      if (value.context.account?.toLowerCase() !== account) throw new Error('Sign in to the account named in this backup before importing it.');
      const ctx = value.context;
      for (const field of ['mode','slug','artifact','target','file','pr']) if (typeof ctx[field] !== 'undefined' && (typeof ctx[field] !== 'string' || ctx[field].length > 240)) throw new Error('The backup has an invalid draft context.');
      if (ctx.kind === 'submit' && (!['new','update','revise'].includes(ctx.mode) || !['study','note','presentation'].includes(ctx.artifact) || !/^[A-Za-z0-9-]*$/.test(ctx.slug))) throw new Error('The backup has an invalid study context.');
      AMDContributorDrafts.validate(value.data);
      if (!confirm('Restore this backup into its draft workspace? The current saved version will be kept as a recovery copy.')) return;
      if (!await change(ctx.kind, () => restoreContext(ctx))) return;
      if (states[ctx.kind].operation) throw new Error('Check the pending submission result before importing over this draft.');
      await serial(async () => { await save(ctx.kind,true); apply(ctx.kind, value.data); states[ctx.kind].dirty = true; await save(ctx.kind); });
      switchTab(ctx.kind, false); syncUrl();
    } catch (error) { el('saved-draft-list').textContent = error.message; }
    event.target.value = '';
  };
  addEventListener('beforeunload', event => {
    if (Object.values(states).some(s => s.dirty)) { event.preventDefault(); event.returnValue = ''; }
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) serial(async () => { await save('submit'); await save('propose'); }).catch(() => {});
  });
  return {schedule, change, source, ticket, matches, begin, complete, compare,
    async prepareFile(name) {
      if (el('s-target').value !== '__new__' || states.submit.context?.file === name) return true;
      if (!await change('submit',() => { states.submit.fileName = name; })) return false;
      await serial(() => save('submit',true));
      return true;
    },
    setProposal(value) { if (states.submit.proposal !== String(value)) { states.submit.proposal = String(value); schedule('submit'); } },
    get fileName() { return states.submit.fileName; },
    set fileName(value) { states.submit.fileName = value; },
    get sourceSha() { return states.submit.source?.sha; },
    get pending() { return Boolean(states.submit.operation); },
    checkpoint: () => serial(() => save('submit', true)),
    flush: () => serial(async () => { await save('submit'); await save('propose'); syncUrl(); }),
    async auth(user, options = {}) {
      const next = (user?.login || '').toLowerCase(); if (next === account) return;
      await serial(async () => {
        if (account && !options.discardUnsaved) { await save('submit'); await save('propose'); }
        account = next; epoch++;
        for (const kind of ['submit','propose']) { states[kind] = {}; apply(kind); }
        el('browser-drafts').hidden = !account;
        if (account) {
          await restore('submit'); await restore('propose'); await listDrafts();
          try { el('recover-legacy-draft').hidden = !localStorage.getItem('amd-submit-draft') && !localStorage.getItem('amd-propose-draft'); } catch (_) {}
        }
      });
    },
  };
})();

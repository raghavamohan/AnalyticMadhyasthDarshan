/* A durable receipt is committed before any GitHub write. Uncertain writes are
 * never retried automatically: GitHub and Cloudflare cannot share a transaction. */
export const operationId = value => typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
export const operationPaths = new Set([
  '/api/propose',
  '/api/submit',
  '/api/revise',
  '/api/status-change',
  '/api/delete-artifact',
]);

export function operationLabel(path, data = {}) {
  if (path === '/api/propose') return 'study-proposal';
  if (path === '/api/revise') return 'new-study';
  if (path === '/api/status-change') return 'status-change';
  if (path === '/api/delete-artifact') return 'study-update';
  return data.isNew ? 'new-study' : 'study-update';
}

export function operationBranchName(path, data, id) {
  const slug = String(data?.slug || '').trim().slice(0, 60);
  if (!slug || !operationId(id)) return null;
  if (path === '/api/submit') return `submission-${slug}-${id}`;
  if (path === '/api/status-change') return `status-${slug}-${id}`;
  if (path === '/api/delete-artifact') return `deletion-${slug}-${id}`;
  return null;
}

export async function digestPayload(path, data) {
  const {turnstileToken, operationId: ignored, ...payload} = data;
  const stable = Object.fromEntries(Object.entries(payload).sort(([a], [b]) => a.localeCompare(b)));
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(path + JSON.stringify(stable)))), b => b.toString(16).padStart(2, '0')).join('');
}

export function operationResource(receipt) {
  if (receipt?.response) {
    return {
      ...receipt.response,
      operationId: receipt.id,
      state: 'complete',
      completed: true,
      retryAllowed: false,
      result: receipt.response,
    };
  }
  if (receipt?.phase === 'started') {
    return {
      success: false,
      operationId: receipt.id,
      state: 'inProgress',
      inProgress: true,
      retryAllowed: false,
      error: 'This operation is still being processed. Check its result before sending another request.',
    };
  }
  return {
    success: false,
    operationId: receipt?.id,
    state: 'uncertain',
    uncertain: true,
    retryAllowed: false,
    ...(receipt?.recoveryBranch ? {recoveryBranch: receipt.recoveryBranch} : {}),
    error: 'This operation is being checked. Check its result; do not send a second copy.',
  };
}

export function receiptResponse(receipt) {
  const resource = operationResource(receipt);
  return new Response(JSON.stringify(resource), {
    status: receipt?.response ? receipt.status : 409,
    headers: {'Content-Type':'application/json'},
  });
}

export async function claimOperation(storage, id, fingerprint, path) {
  return storage.transaction(async tx => {
    const known = await tx.get('op:' + id);
    if (known) {
      if (known.fingerprint !== fingerprint) return {response:Response.json({success:false, state:'uncertain', uncertain:true, retryAllowed:false, operationId:id, error:'This operation receipt belongs to different content. Check its result before starting another operation.'}, {status:409})};
      return {response:receiptResponse(known)};
    }
    const active = await tx.get('active');
    if (active) return {response:Response.json({success:false, state:'uncertain', uncertain:true, retryAllowed:false, operationId:active,
      error:'An earlier operation still needs a result check. Resolve it before sending another.'}, {status:409})};
    const window = Math.floor(Date.now() / 3600000), budget = await tx.get('budget');
    if (budget?.window === window && budget.count >= 30) return {response:Response.json({success:false,
      error:'This account has made 30 submission attempts this hour. Your draft is safe; try again next hour.'}, {status:429})};
    await tx.put('budget',{window,count:budget?.window === window ? budget.count + 1 : 1});
    const receipt = {id, fingerprint, path, phase:'started', created:new Date().toISOString()};
    await tx.put('op:' + id, receipt);
    await tx.put('active', id);
    return {receipt};
  });
}

export async function finishOperation(storage, receipt, response, wrote) {
  const body = await response.clone().json();
  if (wrote && !response.ok) {
    const unknown = {...receipt, phase:'uncertain'};
    await storage.put('op:' + receipt.id, unknown);
    return receiptResponse(unknown);
  }
  const completed = {...receipt, phase:'complete', status:response.status, response:body};
  await storage.transaction(async tx => {
    await tx.put('op:' + receipt.id, completed);
    if (await tx.get('active') === receipt.id) await tx.delete('active');
  });
  const headers = new Headers(response.headers);
  headers.delete('Content-Length');
  headers.set('Content-Type', 'application/json');
  return new Response(JSON.stringify(operationResource(completed)), {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

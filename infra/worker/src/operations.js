/* A durable receipt is committed before any GitHub write. Uncertain writes are
 * never retried automatically: GitHub and Cloudflare cannot share a transaction. */
export const operationId = value => typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
export const operationPaths = new Set(['/api/propose', '/api/submit', '/api/revise']);

export async function digestPayload(path, data) {
  const {turnstileToken, operationId: ignored, ...payload} = data;
  const stable = Object.fromEntries(Object.entries(payload).sort(([a], [b]) => a.localeCompare(b)));
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(path + JSON.stringify(stable)))), b => b.toString(16).padStart(2, '0')).join('');
}

export function receiptResponse(receipt) {
  if (receipt?.response) return new Response(JSON.stringify(receipt.response), {status:receipt.status, headers:{'Content-Type':'application/json'}});
  return Response.json({success:false, uncertain:true, operationId:receipt?.id,
    error:'This submission is being checked. Use Check submission result; do not submit a second copy.'}, {status:409});
}

export async function claimOperation(storage, id, fingerprint, path) {
  return storage.transaction(async tx => {
    const known = await tx.get('op:' + id);
    if (known) {
      if (known.fingerprint !== fingerprint) return {response:Response.json({success:false, uncertain:true, operationId:id, error:'This submission receipt belongs to different content. Check its result before starting another submission.'}, {status:409})};
      return {response:receiptResponse(known)};
    }
    const active = await tx.get('active');
    if (active) return {response:Response.json({success:false, uncertain:true, operationId:active,
      error:'An earlier submission still needs a result check. Resolve it before sending another.'}, {status:409})};
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
  await storage.transaction(async tx => {
    await tx.put('op:' + receipt.id, {...receipt, phase:'complete', status:response.status, response:body});
    if (await tx.get('active') === receipt.id) await tx.delete('active');
  });
  return response;
}

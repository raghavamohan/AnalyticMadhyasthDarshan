// D1 outbox + Resend idempotency. Never retry outside the provider's 24-hour window.
const encoder = new TextEncoder();
async function key(env) {
  if (!env.SESSION_SECRET) throw new Error('Discussion signing is not configured.');
  return crypto.subtle.importKey('raw', encoder.encode(env.SESSION_SECRET), {name:'HMAC',hash:'SHA-256'}, false, ['sign','verify']);
}
export async function unsubscribeToken(env, userId, epoch) {
  const payload = JSON.stringify([userId, epoch]);
  const encoded = btoa(payload).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  const signature = await crypto.subtle.sign('HMAC', await key(env), encoder.encode('discussion-unsubscribe:' + encoded));
  return encoded + '.' + Array.from(new Uint8Array(signature), b=>b.toString(16).padStart(2,'0')).join('');
}
export async function decodeUnsubscribe(env, token) {
  if (typeof token !== 'string' || token.length > 512) return null;
  try {
    const [payload, signature, extra] = token.split('.');
    if (extra || !/^[a-f0-9]{64}$/.test(signature || '')) return null;
    const bytes = Uint8Array.from(signature.match(/../g), value=>parseInt(value,16));
    if (!await crypto.subtle.verify('HMAC', await key(env), bytes, encoder.encode('discussion-unsubscribe:' + payload))) return null;
    const data = JSON.parse(atob(payload.replace(/-/g,'+').replace(/_/g,'/')));
    return Array.isArray(data) && data.length === 2 && data.every(value=>typeof value === 'string') ? data : null;
  } catch { return null; }
}
export async function getPreferences(db, userId) {
  const row = await db.prepare('SELECT reply_email FROM discussion_preferences WHERE user_id = ?').bind(userId).first();
  return {replyEmail: row?.reply_email === 1};
}
export async function setPreferences(db, userId, enabled) {
  const epoch = crypto.randomUUID();
  await db.prepare(`INSERT INTO discussion_preferences (user_id, reply_email, epoch) VALUES (?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET reply_email = excluded.reply_email, epoch = excluded.epoch
    WHERE discussion_preferences.reply_email != excluded.reply_email`)
    .bind(userId, enabled ? 1 : 0, epoch).run();
  return {replyEmail:enabled};
}
export async function unsubscribe(db, env, token) {
  const identity = await decodeUnsubscribe(env, token);
  if (!identity) return false;
  // A link from an older enrollment cannot disable a later explicit opt-in.
  await db.prepare('UPDATE discussion_preferences SET reply_email = 0 WHERE user_id = ? AND epoch = ?').bind(...identity).run();
  return true;
}
export function replyEmail(env, row, token) {
  const origin = env.SITE_ORIGIN || 'https://analyticmadhyasthdarshan.org';
  const link = `${origin}/Studies/${encodeURIComponent(row.thread_slug)}/discussion.html#c-${encodeURIComponent(row.comment_id)}`;
  const stop = `${origin}/api/discuss-auth/unsubscribe#token=${encodeURIComponent(token)}`;
  // No comment bodies in email: a later-hidden comment is not replicated in an inbox.
  return {from:env.EMAIL_FROM || 'Discussions <discussions@analyticmadhyasthdarshan.org>',to:[row.email],
    subject:'A reply to your Analytic Madhyasth Darshan comment',
    text:`Someone replied to your comment.\n\nRead the reply: ${link}\n\nYou opted in to direct-reply emails. Disable reply emails: ${stop}`};
}
export async function deliverReplies(env, now = Date.now()) {
  if (!env.DB || !env.RESEND_API_KEY) return;
  const db = env.DB;
  // A provider request might have succeeded despite a lost response. Leave old
  // uncertain attempts for inspection instead of risking a duplicate after expiry.
  await db.prepare(`UPDATE reply_outbox SET state = 'uncertain', payload = NULL
    WHERE state = 'pending' AND first_attempt IS NOT NULL AND first_attempt < ?`).bind(now - 23*60*60*1000).run();
  const {results} = await db.prepare(`SELECT comment_id FROM reply_outbox
    WHERE state = 'pending' AND next_at <= ? AND lease_until < ? ORDER BY created_at LIMIT 10`).bind(now,now).all();
  for (const candidate of results || []) {
    const lease = crypto.randomUUID();
    const claimed = await db.prepare(`UPDATE reply_outbox SET lease = ?, lease_until = ?, attempts = attempts + 1,
      first_attempt = COALESCE(first_attempt, ?) WHERE comment_id = ? AND state = 'pending' AND lease_until < ?
      RETURNING *`).bind(lease,now+120000,now,candidate.comment_id,now).first();
    if (!claimed) continue;
    const context = await db.prepare(`SELECT o.comment_id, c.thread_slug, u.email, p.epoch
      FROM reply_outbox o JOIN comments c ON c.id = o.comment_id
      JOIN comments parent ON parent.id = c.parent_id JOIN users u ON u.id = o.recipient_id
      JOIN discussion_preferences p ON p.user_id = o.recipient_id
      WHERE o.comment_id = ? AND p.reply_email = 1 AND p.epoch = o.epoch
      AND c.status = 'visible' AND parent.status = 'visible'`).bind(claimed.comment_id).first();
    if (!context) {
      await db.prepare("UPDATE reply_outbox SET state = 'cancelled', payload = NULL WHERE comment_id = ? AND lease = ?").bind(claimed.comment_id,lease).run();
      continue;
    }
    try {
      // Persist the exact provider payload before the first request: retries with
      // this key must never change recipient, links or unsubscribe enrollment.
      const payload = claimed.payload || JSON.stringify(replyEmail(env, context, await unsubscribeToken(env, claimed.recipient_id, claimed.epoch)));
      if (!claimed.payload) await db.prepare('UPDATE reply_outbox SET payload = ? WHERE comment_id = ? AND lease = ?').bind(payload,claimed.comment_id,lease).run();
      const response = await fetch('https://api.resend.com/emails', {method:'POST',headers:{
        Authorization:`Bearer ${env.RESEND_API_KEY}`,'Content-Type':'application/json','Idempotency-Key':'discussion-reply/'+claimed.comment_id},
        body:payload,signal:AbortSignal.timeout(15000)});
      const result = await response.json().catch(()=>({}));
      if (!response.ok || !result.id) throw new Error('Provider did not confirm delivery.');
      await db.prepare("UPDATE reply_outbox SET state = 'sent', sent_at = ?, provider_id = ?, payload = NULL WHERE comment_id = ? AND lease = ?").bind(now,result.id,claimed.comment_id,lease).run();
    } catch {
      await db.prepare('UPDATE reply_outbox SET next_at = ?, lease_until = 0 WHERE comment_id = ? AND lease = ?')
        .bind(now+Math.min(3600000,60000*2**Math.min(claimed.attempts,6)),claimed.comment_id,lease).run();
      // No recipient, content, token or provider response enters logs.
      console.warn('Discussion reply mail retry scheduled.');
    }
  }
  // Keep operational payloads bounded. Uncertain rows remain for inspection.
  await db.prepare("DELETE FROM reply_outbox WHERE state IN ('sent','cancelled') AND created_at < ?").bind(now-30*86400000).run();
  await db.prepare("DELETE FROM reply_outbox WHERE state = 'uncertain' AND created_at < ?").bind(now-90*86400000).run();
  await db.prepare("DELETE FROM discussion_reports WHERE state = 'resolved' AND resolved_at < ?").bind(now-90*86400000).run();
}

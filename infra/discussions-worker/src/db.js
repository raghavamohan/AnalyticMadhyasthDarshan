export function nowMs() {
  return Date.now();
}

export async function ensureThread(db, slug, title) {
  const existing = await db.prepare('SELECT slug FROM threads WHERE slug = ?').bind(slug).first();
  if (existing) return;
  await db.prepare(
    'INSERT INTO threads (slug, title, created_at) VALUES (?, ?, ?)',
  ).bind(slug, title, nowMs()).run();
}

export async function findOrCreateUser(db, email, displayName) {
  const normalizedEmail = email.trim().toLowerCase();
  const existing = await db.prepare(
    'SELECT id, email, display_name FROM users WHERE email = ?',
  ).bind(normalizedEmail).first();
  if (existing) {
    if (displayName && existing.display_name !== displayName) {
      await db.prepare(
        'UPDATE users SET display_name = ? WHERE id = ?',
      ).bind(displayName.trim(), existing.id).run();
      return { id: existing.id, email: existing.email, displayName: displayName.trim() };
    }
    return {
      id: existing.id,
      email: existing.email,
      displayName: existing.display_name,
    };
  }
  const id = crypto.randomUUID();
  await db.prepare(
    'INSERT INTO users (id, email, display_name, created_at) VALUES (?, ?, ?, ?)',
  ).bind(id, normalizedEmail, displayName.trim(), nowMs()).run();
  return { id, email: normalizedEmail, displayName: displayName.trim() };
}

export async function storeMagicToken(db, { token, email, displayName, expiresAt }) {
  await db.prepare(
    'INSERT INTO magic_tokens (token, email, display_name, expires_at) VALUES (?, ?, ?, ?)',
  ).bind(token, email.trim().toLowerCase(), displayName.trim(), expiresAt).run();
}

export async function consumeMagicToken(db, token) {
  const row = await db.prepare(
    'SELECT token, email, display_name, expires_at, used_at FROM magic_tokens WHERE token = ?',
  ).bind(token).first();
  if (!row) return null;
  if (row.used_at) return null;
  if (row.expires_at < nowMs()) return null;
  await db.prepare(
    'UPDATE magic_tokens SET used_at = ? WHERE token = ?',
  ).bind(nowMs(), token).run();
  return {
    email: row.email,
    displayName: row.display_name,
  };
}

export async function listComments(db, slug, { limit = 50, offset = 0 } = {}) {
  const { results } = await db.prepare(`
    SELECT
      c.id,
      c.thread_slug,
      c.parent_id,
      c.body,
      c.status,
      c.created_at,
      c.updated_at,
      c.user_id,
      u.display_name AS author_name
    FROM comments c
    JOIN users u ON u.id = c.user_id
    WHERE c.thread_slug = ? AND c.status = 'visible'
    ORDER BY c.created_at ASC
    LIMIT ? OFFSET ?
  `).bind(slug, limit, offset).all();
  return results || [];
}

export async function insertComment(db, {
  id,
  threadSlug,
  parentId,
  userId,
  body,
}) {
  const ts = nowMs();
  await db.prepare(`
    INSERT INTO comments (id, thread_slug, parent_id, user_id, body, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, 'visible', ?, ?)
  `).bind(id, threadSlug, parentId || null, userId, body, ts, ts).run();
}

export async function getComment(db, commentId, threadSlug) {
  return db.prepare(`
    SELECT id, thread_slug, user_id, status
    FROM comments
    WHERE id = ? AND thread_slug = ?
  `).bind(commentId, threadSlug).first();
}

export async function listThreadStats(db) {
  const { results } = await db.prepare(`
    SELECT
      thread_slug AS slug,
      COUNT(*) AS count,
      MAX(created_at) AS latest_at
    FROM comments
    WHERE status = 'visible'
    GROUP BY thread_slug
  `).all();
  return results || [];
}

export async function hideComment(db, commentId) {
  await db.prepare(
    "UPDATE comments SET status = 'hidden', updated_at = ? WHERE id = ? AND status = 'visible'",
  ).bind(nowMs(), commentId).run();
}

export async function countRecentMagicTokens(db, email, sinceMs) {
  const row = await db.prepare(
    'SELECT COUNT(*) AS count FROM magic_tokens WHERE email = ? AND expires_at > ?',
  ).bind(email.trim().toLowerCase(), sinceMs).first();
  return Number(row?.count || 0);
}

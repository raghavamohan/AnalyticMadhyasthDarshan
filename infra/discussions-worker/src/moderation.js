export async function reportComment(db, userId, commentId, slug, reason, now = Date.now()) {
  const row = await db.prepare(`INSERT INTO discussion_reports (id, comment_id, reporter_id, reason, created_at)
    SELECT ?, c.id, ?, ?, ? FROM comments c WHERE c.id = ? AND c.thread_slug = ? AND c.status = 'visible'
    AND c.user_id != ? AND (SELECT COUNT(*) FROM discussion_reports WHERE reporter_id = ? AND created_at > ?) < 10
    ON CONFLICT(comment_id, reporter_id) DO NOTHING RETURNING id`)
    .bind(crypto.randomUUID(),userId,reason,now,commentId,slug,userId,userId,now-3600000).first();
  if (row) return 'created';
  const existing = await db.prepare('SELECT id FROM discussion_reports WHERE comment_id = ? AND reporter_id = ?').bind(commentId,userId).first();
  return existing ? 'duplicate' : 'limited';
}
export async function listReports(db, limit = 50, offset = 0) {
  const {results} = await db.prepare(`SELECT r.id, r.comment_id AS commentId, r.reason, r.created_at AS createdAt,
    c.thread_slug AS slug, c.body, c.status, c.updated_at AS sourceUpdatedAt, u.display_name AS authorName
    FROM discussion_reports r JOIN comments c ON c.id = r.comment_id JOIN users u ON u.id = c.user_id
    WHERE r.state = 'open' ORDER BY r.created_at, r.id LIMIT ? OFFSET ?`).bind(limit,offset).all();
  const count = await db.prepare("SELECT COUNT(*) AS count FROM discussion_reports WHERE state = 'open'").first();
  return {reports:results || [],total:Number(count?.count || 0)};
}
export async function resolveReport(db, reportId, adminId) {
  const result = await db.prepare("UPDATE discussion_reports SET state = 'resolved', resolved_at = ?, resolved_by = ? WHERE id = ? AND state = 'open'")
    .bind(Date.now(),adminId,reportId).run();
  return result.meta?.changes === 1;
}

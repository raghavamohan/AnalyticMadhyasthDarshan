-- Reply mail is explicitly opt-in. No existing user is enrolled.
CREATE TABLE IF NOT EXISTS discussion_preferences (
  user_id TEXT PRIMARY KEY REFERENCES users(id),
  reply_email INTEGER NOT NULL DEFAULT 0 CHECK (reply_email IN (0, 1)),
  epoch TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reply_outbox (
  comment_id TEXT PRIMARY KEY REFERENCES comments(id),
  recipient_id TEXT NOT NULL REFERENCES users(id),
  epoch TEXT NOT NULL,
  payload TEXT,
  state TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  next_at INTEGER NOT NULL,
  first_attempt INTEGER,
  lease TEXT,
  lease_until INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL,
  sent_at INTEGER,
  provider_id TEXT
);
CREATE INDEX IF NOT EXISTS reply_outbox_due ON reply_outbox(state, next_at, lease_until);
CREATE TABLE IF NOT EXISTS discussion_reports (
  id TEXT PRIMARY KEY,
  comment_id TEXT NOT NULL REFERENCES comments(id),
  reporter_id TEXT NOT NULL REFERENCES users(id),
  reason TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open', 'resolved')),
  created_at INTEGER NOT NULL,
  resolved_at INTEGER,
  resolved_by TEXT,
  UNIQUE(comment_id, reporter_id)
);
CREATE INDEX IF NOT EXISTS discussion_reports_open ON discussion_reports(state, created_at);
CREATE INDEX IF NOT EXISTS discussion_reports_quota ON discussion_reports(reporter_id, created_at);

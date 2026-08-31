-- D1 (SQLite) schema, ported column-for-column from the Postgres SQLModel tables.
--
-- Type mapping:
--   VARCHAR(n)  -> TEXT     SQLite ignores length; app-side truncation still applies.
--   SERIAL      -> INTEGER PRIMARY KEY AUTOINCREMENT
--   BOOLEAN     -> INTEGER  SQLite has no BOOLEAN: 0/1.
--   TIMESTAMP   -> TEXT     ISO-8601 UTC strings. SQLite has no native datetime type;
--                           ISO-8601 sorts lexicographically so ORDER BY still works.
--   ENUM        -> TEXT + CHECK (SQLite has no ENUM type).
--
-- Load-bearing constraints (relied on by app/services/substack_sync.py):
--   story.source_url  UNIQUE — the sync's idempotency key.
--   story.slug        UNIQUE — /essays/{slug} lookup.

CREATE TABLE IF NOT EXISTS user (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  email            TEXT NOT NULL,
  hashed_password  TEXT NOT NULL,
  full_name        TEXT,
  is_author        INTEGER NOT NULL DEFAULT 0,
  is_active        INTEGER NOT NULL DEFAULT 1,
  created_at       TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_user_email     ON user(email);
CREATE INDEX        IF NOT EXISTS ix_user_is_author ON user(is_author);

CREATE TABLE IF NOT EXISTS story (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  title             TEXT NOT NULL,
  slug              TEXT,
  canonical_url     TEXT,
  source_url        TEXT,
  content_hash      TEXT,
  content_source    TEXT CHECK (content_source IN ('api','rss') OR content_source IS NULL),
  meta_description  TEXT,
  content           TEXT NOT NULL,
  excerpt           TEXT,
  cover_image_url   TEXT,
  status            TEXT NOT NULL DEFAULT 'draft'
                      CHECK (status IN ('draft','published','archived')),
  author_notes      TEXT,
  content_warning   TEXT,
  view_count        INTEGER NOT NULL DEFAULT 0,
  read_time_minutes INTEGER,
  author_id         INTEGER NOT NULL REFERENCES user(id),
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL,
  published_at      TEXT,
  search_vector     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_story_slug         ON story(slug);
CREATE UNIQUE INDEX IF NOT EXISTS ix_story_source_url   ON story(source_url);
CREATE INDEX        IF NOT EXISTS ix_story_author_id    ON story(author_id);
CREATE INDEX        IF NOT EXISTS ix_story_published_at ON story(published_at);
CREATE INDEX        IF NOT EXISTS ix_story_status       ON story(status);

CREATE TABLE IF NOT EXISTS lead_capture (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  email              TEXT NOT NULL,
  source             TEXT NOT NULL,
  utm_source         TEXT,
  utm_medium         TEXT,
  utm_campaign       TEXT,
  utm_content        TEXT,
  utm_term           TEXT,
  referrer_url       TEXT,
  magnet_requested   INTEGER NOT NULL DEFAULT 0,
  confirmation_token TEXT NOT NULL,
  confirmed_at       TEXT,
  unsubscribed_at    TEXT,
  sequence_step      INTEGER NOT NULL DEFAULT 0,
  next_send_at       TEXT,
  created_at         TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_lead_capture_email              ON lead_capture(email);
CREATE UNIQUE INDEX IF NOT EXISTS ix_lead_capture_confirmation_token ON lead_capture(confirmation_token);
CREATE INDEX        IF NOT EXISTS ix_lead_capture_next_send_at       ON lead_capture(next_send_at);

CREATE TABLE IF NOT EXISTS lead_event (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  lead_id      INTEGER NOT NULL REFERENCES lead_capture(id),
  event_type   TEXT NOT NULL,
  sg_event_id  TEXT NOT NULL,
  payload_json TEXT,
  occurred_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_lead_event_lead_id     ON lead_event(lead_id);
CREATE INDEX IF NOT EXISTS ix_lead_event_event_type  ON lead_event(event_type);
CREATE INDEX IF NOT EXISTS ix_lead_event_occurred_at ON lead_event(occurred_at);

-- Parents who want to hear when PDF downloads open.
CREATE TABLE waitlist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  child_age TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

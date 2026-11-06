-- One row per free-preview download, so we can see which levels parents look at.
CREATE TABLE preview_downloads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL,
  country TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX preview_downloads_level ON preview_downloads (level);

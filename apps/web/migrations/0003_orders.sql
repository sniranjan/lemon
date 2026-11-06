-- Paid orders for whole-level PDFs (Stripe Checkout). One row per completed checkout session.
-- `token` is the secret in the customer's download link (/orders/<token>).
CREATE TABLE orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL UNIQUE,
  token TEXT NOT NULL UNIQUE,
  level TEXT NOT NULL,
  email TEXT,
  amount_cents INTEGER NOT NULL,
  currency TEXT NOT NULL,
  downloads INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX orders_email ON orders (email);

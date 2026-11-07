-- Gifts the buyer passes on themselves ("I'll give it myself", worker/gift.ts), and every name optional.
-- A self-share gift has no recipient_email and no deliver_on (the cron never sends it); an emailed gift has
-- both. buyer_name and recipient_name may be empty too (the card then says "a gift for you", no "from").
-- SQLite can't drop NOT NULL in place, so the table is rebuilt: create, copy every row (ids kept, so
-- AUTOINCREMENT carries on), drop, rename, recreate the index. No BEGIN/COMMIT: D1 runs each migration in a
-- transaction of its own. No other table references gifts, and it has no triggers or views.
CREATE TABLE gifts_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  session_id TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL CHECK (kind IN ('all', 'credit')),
  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
  balance_cents INTEGER NOT NULL CHECK (balance_cents >= 0),
  currency TEXT NOT NULL DEFAULT 'usd',
  buyer_name TEXT,
  buyer_email TEXT,
  recipient_name TEXT,
  recipient_email TEXT,
  child_name TEXT,
  message TEXT,
  deliver_on TEXT,
  delivered_at TEXT,
  resent_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  CHECK ((recipient_email IS NULL) = (deliver_on IS NULL))
);

INSERT INTO gifts_new (id, code, session_id, kind, amount_cents, balance_cents, currency, buyer_name, buyer_email,
  recipient_name, recipient_email, child_name, message, deliver_on, delivered_at, resent_at, created_at)
SELECT id, code, session_id, kind, amount_cents, balance_cents, currency, buyer_name, buyer_email,
  recipient_name, recipient_email, child_name, message, deliver_on, delivered_at, resent_at, created_at
FROM gifts;

DROP TABLE gifts;
ALTER TABLE gifts_new RENAME TO gifts;

-- Emailed gifts still waiting to go out (self-share gifts keep delivered_at empty forever, so they're left out).
CREATE INDEX gifts_due ON gifts (deliver_on) WHERE delivered_at IS NULL AND deliver_on IS NOT NULL;

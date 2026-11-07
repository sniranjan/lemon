-- Gifts: one parent buys paperlessons for another family (worker/gift.ts).
-- A gift is created by the Stripe webhook once the buyer has paid. `code` is the secret printed on the gift
-- card and emailed to the recipient (XXXX-XXXX-XXXX). Codes never expire.
--   kind 'all'    = every level; redeemed once into an order for all 13 levels (balance goes to 0)
--   kind 'credit' = a dollar amount; spent across any number of orders until the balance is used up
-- deliver_on is a UTC date (YYYY-MM-DD); the daily cron emails the recipient once it is due.
-- Only the child's first name is stored.
CREATE TABLE gifts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  session_id TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL CHECK (kind IN ('all', 'credit')),
  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
  balance_cents INTEGER NOT NULL CHECK (balance_cents >= 0),
  currency TEXT NOT NULL DEFAULT 'usd',
  buyer_name TEXT NOT NULL,
  buyer_email TEXT,
  recipient_name TEXT NOT NULL,
  recipient_email TEXT NOT NULL,
  child_name TEXT,
  message TEXT,
  deliver_on TEXT NOT NULL,
  delivered_at TEXT,
  resent_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX gifts_due ON gifts (deliver_on) WHERE delivered_at IS NULL;

-- Every order paid (fully or partly) with a gift. order_session is orders.session_id: a Stripe session for
-- "pay the rest", or a synthetic id for orders the gift covered in full (no Stripe). UNIQUE keeps webhook
-- retries from taking the balance twice.
CREATE TABLE gift_redemptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL,
  order_session TEXT NOT NULL UNIQUE,
  cents_used INTEGER NOT NULL CHECK (cents_used >= 0),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX gift_redemptions_code ON gift_redemptions (code);

-- While a "pay the rest" checkout is open, the part of the balance it will use is held here, so a second
-- tab can't spend the same dollars. Holds lapse on their own (expires_at) and are removed once paid.
CREATE TABLE gift_holds (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL,
  cents INTEGER NOT NULL,
  session_id TEXT,
  expires_at TEXT NOT NULL
);
CREATE INDEX gift_holds_code ON gift_holds (code);

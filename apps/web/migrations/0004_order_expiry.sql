-- Download links expire 7 days after purchase (set on insert; extend by hand with an UPDATE if a buyer
-- genuinely needs their files again).
ALTER TABLE orders ADD COLUMN expires_at TEXT;
UPDATE orders SET expires_at = datetime(created_at, '+7 days') WHERE expires_at IS NULL;

-- Bundles: one order can cover several levels. `levels` is a comma list of slugs in ladder order
-- (a single-level order has just its own slug); `kind` is level | two | all.
ALTER TABLE orders ADD COLUMN levels TEXT;
ALTER TABLE orders ADD COLUMN kind TEXT NOT NULL DEFAULT 'level';
UPDATE orders SET levels = level WHERE levels IS NULL;

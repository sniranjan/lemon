// Selling whole levels as PDFs: Stripe Checkout (hosted page) → order row in D1 → download page.
//
// What's for sale is whatever is in R2: a level is buyable once `levels/<slug>/` holds its PDFs
// (uploaded from the generator's booklets) AND its Stripe price exists (lookup key `level_<slug>`,
// created by scripts/stripe-setup.mjs; change prices in the Stripe dashboard by moving the lookup key
// to a new price). Checkout stays off until the Stripe secrets are set:
//   npx wrangler secret put STRIPE_SECRET_KEY
//   npx wrangler secret put STRIPE_WEBHOOK_SECRET
import { Hono } from "hono";
import ladder from "../src/data/ladder.json";
import { createCheckoutSession, getCheckoutSession, newToken, pricesByLookupKey, verifyWebhook, type CheckoutSession } from "./stripe";

export type ShopEnv = {
  DB: D1Database;
  FILES: R2Bucket;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
};

const LEVELS = new Map(ladder.map((l) => [l.slug, l]));
const TOKEN = /^[A-Za-z0-9_-]{20,64}$/;
const FILE = /^[a-z0-9][a-z0-9.-]{0,80}\.pdf$/;
const SESSION = /^cs_[A-Za-z0-9_]{10,200}$/;

const shop = new Hono<{ Bindings: ShopEnv }>();

const checkoutOn = (env: ShopEnv) => Boolean(env.STRIPE_SECRET_KEY);

type LevelPrice = { id: string; cents: number; currency: string };
let priceCache: { at: number; bySlug: Map<string, LevelPrice> } | null = null;

/** Each level's Stripe price (lookup key `level_<slug>`), cached for 5 minutes per isolate. */
async function levelPrices(env: ShopEnv): Promise<Map<string, LevelPrice>> {
  if (!env.STRIPE_SECRET_KEY) return new Map();
  if (priceCache && Date.now() - priceCache.at < 300_000) return priceCache.bySlug;
  try {
    const prices = await pricesByLookupKey(env.STRIPE_SECRET_KEY, [...LEVELS.keys()].map((s) => `level_${s}`));
    const bySlug = new Map<string, LevelPrice>();
    for (const p of prices) {
      if (p.lookup_key?.startsWith("level_") && p.unit_amount != null) {
        bySlug.set(p.lookup_key.slice("level_".length), { id: p.id, cents: p.unit_amount, currency: p.currency });
      }
    }
    priceCache = { at: Date.now(), bySlug };
  } catch (e) {
    console.error(e);
    if (!priceCache) return new Map();
  }
  return priceCache!.bySlug;
}

/** Slugs with whole-level PDFs in R2. */
async function levelsForSale(files: R2Bucket): Promise<string[]> {
  const listed = await files.list({ prefix: "levels/", delimiter: "/" });
  return listed.delimitedPrefixes.map((p) => p.slice("levels/".length, -1)).filter((s) => LEVELS.has(s));
}

async function levelFiles(files: R2Bucket, slug: string) {
  const listed = await files.list({ prefix: `levels/${slug}/` });
  return listed.objects
    .map((o) => ({ name: o.key.slice(`levels/${slug}/`.length), size: o.size }))
    .filter((f) => FILE.test(f.name))
    .sort((a, b) => rank(a.name) - rank(b.name) || a.name.localeCompare(b.name));
}

/** Reading, then math, then pencil; each subject's level book before its answer key. */
function rank(name: string): number {
  const subject = ["reading", "math", "pencil"].findIndex((s) => name.includes(s));
  return (subject < 0 ? 3 : subject) * 2 + (name.includes("answers") ? 1 : 0);
}

/** What the library needs in one request: previews, what's buyable, and each level's price. */
shop.get("/api/catalog", async (c) => {
  const [previewList, withFiles, prices] = await Promise.all([
    c.env.FILES.list({ prefix: "previews/" }),
    levelsForSale(c.env.FILES),
    levelPrices(c.env),
  ]);
  const previews = previewList.objects
    .map((o) => o.key.slice("previews/".length))
    .filter((k) => k.endsWith(".pdf"))
    .map((k) => k.slice(0, -4));
  const forSale = checkoutOn(c.env) ? withFiles.filter((s) => prices.has(s)) : [];
  return c.json(
    {
      previews,
      forSale,
      prices: Object.fromEntries(forSale.map((s) => [s, { cents: prices.get(s)!.cents, currency: prices.get(s)!.currency }])),
    },
    200,
    { "cache-control": "public, max-age=60" },
  );
});

shop.post("/api/checkout", async (c) => {
  if (!checkoutOn(c.env)) return c.json({ ok: false, error: "Checkout isn't open yet." }, 503);
  const body = await c.req.json<{ level?: string }>().catch(() => ({}) as { level?: string });
  const level = LEVELS.get(String(body.level ?? ""));
  const levelPrice = level && (await levelPrices(c.env)).get(level.slug);
  if (!level || !levelPrice || !(await levelFiles(c.env.FILES, level.slug)).length) {
    return c.json({ ok: false, error: "That level isn't for sale yet." }, 404);
  }
  const origin = new URL(c.req.url).origin;
  try {
    const session = await createCheckoutSession(c.env.STRIPE_SECRET_KEY!, {
      mode: "payment",
      line_items: [{ price: levelPrice.id, quantity: 1 }],
      allow_promotion_codes: true,
      metadata: { level: level.slug },
      payment_intent_data: { metadata: { level: level.slug } },
      success_url: `${origin}/thanks?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/#library`,
    });
    return c.json({ ok: true, url: session.url });
  } catch (e) {
    console.error(e);
    return c.json({ ok: false, error: "Couldn't start checkout. Please try again." }, 502);
  }
});

/** Store a paid session as an order (idempotent) and return its download token. */
async function recordOrder(db: D1Database, s: CheckoutSession): Promise<string | null> {
  const level = s.metadata?.level;
  // "no_payment_required" = a 100%-off promotion code, which is still a real order.
  if (s.payment_status === "unpaid" || s.status !== "complete" || !level || !LEVELS.has(level)) return null;
  await db
    .prepare(
      "INSERT INTO orders (session_id, token, level, email, amount_cents, currency) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(session_id) DO NOTHING",
    )
    .bind(s.id, newToken(), level, s.customer_details?.email?.toLowerCase() ?? null, s.amount_total ?? 0, s.currency ?? "")
    .run();
  const row = await db.prepare("SELECT token FROM orders WHERE session_id = ?").bind(s.id).first<{ token: string }>();
  return row?.token ?? null;
}

shop.post("/api/stripe/webhook", async (c) => {
  const secret = c.env.STRIPE_WEBHOOK_SECRET;
  if (!secret) return c.json({ ok: false }, 503);
  const raw = await c.req.text();
  if (!(await verifyWebhook(raw, c.req.header("stripe-signature") ?? null, secret))) {
    return c.json({ ok: false, error: "bad signature" }, 400);
  }
  const event = JSON.parse(raw) as { type: string; data: { object: CheckoutSession } };
  if (event.type === "checkout.session.completed" || event.type === "checkout.session.async_payment_succeeded") {
    await recordOrder(c.env.DB, event.data.object);
  }
  return c.json({ received: true });
});

/** The thanks page asks for its token. If the webhook hasn't landed yet, ask Stripe directly. */
shop.get("/api/orders/session/:sid", async (c) => {
  const sid = c.req.param("sid");
  if (!SESSION.test(sid)) return c.json({ ok: false, error: "Not found" }, 404);
  const row = await c.env.DB.prepare("SELECT token FROM orders WHERE session_id = ?").bind(sid).first<{ token: string }>();
  if (row) return c.json({ ok: true, token: row.token });
  if (!checkoutOn(c.env)) return c.json({ ok: false, error: "Not found" }, 404);
  try {
    const token = await recordOrder(c.env.DB, await getCheckoutSession(c.env.STRIPE_SECRET_KEY!, sid));
    if (token) return c.json({ ok: true, token });
    return c.json({ ok: false, pending: true, error: "We're still confirming your payment." }, 202);
  } catch {
    return c.json({ ok: false, error: "Not found" }, 404);
  }
});

type OrderRow = { level: string; email: string | null; created_at: string };

async function orderFor(db: D1Database, token: string) {
  if (!TOKEN.test(token)) return null;
  return db.prepare("SELECT level, email, created_at FROM orders WHERE token = ?").bind(token).first<OrderRow>();
}

shop.get("/api/orders/:token", async (c) => {
  const token = c.req.param("token");
  const order = await orderFor(c.env.DB, token);
  if (!order) return c.json({ ok: false, error: "We couldn't find that order." }, 404);
  const level = LEVELS.get(order.level)!;
  const files = await levelFiles(c.env.FILES, order.level);
  return c.json(
    {
      ok: true,
      level: { slug: level.slug, name: level.name, title: level.title, age: level.age },
      email: order.email,
      purchasedAt: order.created_at,
      files: files.map((f) => ({ ...f, url: `/api/orders/${token}/files/${f.name}` })),
    },
    200,
    { "cache-control": "private, no-store" },
  );
});

shop.get("/api/orders/:token/files/:file", async (c) => {
  const { token, file } = c.req.param();
  const order = await orderFor(c.env.DB, token);
  if (!order || !FILE.test(file)) return c.json({ ok: false, error: "Not found" }, 404);
  const obj = await c.env.FILES.get(`levels/${order.level}/${file}`);
  if (!obj) return c.json({ ok: false, error: "Not found" }, 404);
  c.executionCtx.waitUntil(c.env.DB.prepare("UPDATE orders SET downloads = downloads + 1 WHERE token = ?").bind(token).run());
  return new Response(obj.body, {
    headers: {
      "content-type": "application/pdf",
      "content-disposition": `attachment; filename="paperlessons-${file}"`,
      "cache-control": "private, no-store",
      etag: obj.httpEtag,
    },
  });
});

export default shop;

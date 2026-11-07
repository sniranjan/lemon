// Selling whole levels as PDFs: Stripe Checkout (hosted page) → order row in D1 → download page.
//
// What's for sale is whatever is in R2: a level is buyable once `levels/<slug>/` holds its PDFs
// (uploaded from the generator's booklets) AND its Stripe price exists (lookup key `level_<slug>`,
// created by scripts/stripe-setup.mjs; change prices in the Stripe dashboard by moving the lookup key
// to a new price). Bundles use lookup keys `bundle_two` (a level plus the next one) and `bundle_all` (every
// level). Checkout stays off until the Stripe secrets are set:
//   npx wrangler secret put STRIPE_SECRET_KEY
//   npx wrangler secret put STRIPE_WEBHOOK_SECRET
import { Hono } from "hono";
import ladder from "../src/data/ladder.json";
import { sendOrderEmail } from "./email";
import { createCheckoutSession, getCheckoutSession, newToken, pricesByLookupKey, verifyWebhook, type CheckoutSession } from "./stripe";

export type ShopEnv = {
  DB: D1Database;
  FILES: R2Bucket;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  EMAIL?: SendEmail;
};

const LEVELS = new Map(ladder.map((l) => [l.slug, l]));
const ORDER = ladder.map((l) => l.slug);
type Kind = "level" | "two" | "all";
const BUNDLE_KEYS: Record<Exclude<Kind, "level">, string> = { two: "bundle_two", all: "bundle_all" };
const TOKEN = /^[A-Za-z0-9_-]{20,64}$/;
const FILE = /^[a-z0-9][a-z0-9.-]{0,80}\.pdf$/;
const SESSION = /^cs_[A-Za-z0-9_]{10,200}$/;

const shop = new Hono<{ Bindings: ShopEnv }>();

const checkoutOn = (env: ShopEnv) => Boolean(env.STRIPE_SECRET_KEY);

type LevelPrice = { id: string; cents: number; currency: string };
type Prices = { bySlug: Map<string, LevelPrice>; bundles: Map<string, LevelPrice> };
let priceCache: { at: number; prices: Prices } | null = null;
const NO_PRICES: Prices = { bySlug: new Map(), bundles: new Map() };

/** Level prices (lookup key `level_<slug>`) and bundle prices, cached for 5 minutes per isolate. */
async function allPrices(env: ShopEnv): Promise<Prices> {
  if (!env.STRIPE_SECRET_KEY) return NO_PRICES;
  if (priceCache && Date.now() - priceCache.at < 300_000) return priceCache.prices;
  try {
    const keys = [...ORDER.map((s) => `level_${s}`), ...Object.values(BUNDLE_KEYS)];
    const found = await pricesByLookupKey(env.STRIPE_SECRET_KEY, keys);
    const prices: Prices = { bySlug: new Map(), bundles: new Map() };
    for (const p of found) {
      if (p.unit_amount == null || !p.lookup_key) continue;
      const price = { id: p.id, cents: p.unit_amount, currency: p.currency };
      if (p.lookup_key.startsWith("level_")) prices.bySlug.set(p.lookup_key.slice("level_".length), price);
      else prices.bundles.set(p.lookup_key, price);
    }
    priceCache = { at: Date.now(), prices };
  } catch (e) {
    console.error(e);
    if (!priceCache) return NO_PRICES;
  }
  return priceCache!.prices;
}

const levelPrices = async (env: ShopEnv) => (await allPrices(env)).bySlug;

/** The level after `slug` on the ladder, if it is also for sale. */
function nextFor(slug: string, forSale: string[]): string | undefined {
  const next = ORDER[ORDER.indexOf(slug) + 1];
  return next && forSale.includes(next) ? next : undefined;
}

/** "Chicks", "Chicks and Ducklings", "All 13 levels". */
function orderName(kind: Kind, slugs: string[]): string {
  if (kind === "all") return `All ${slugs.length} levels`;
  return slugs.map((s) => LEVELS.get(s)!.name).join(" and ");
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
  const [previewList, withFiles, all] = await Promise.all([
    c.env.FILES.list({ prefix: "previews/" }),
    levelsForSale(c.env.FILES),
    allPrices(c.env),
  ]);
  const prices = all.bySlug;
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
      // bundles: "two" = a level plus the next one on the ladder (`next` says which); "all" = every level for sale
      bundles: Object.fromEntries(
        (["two", "all"] as const)
          .map((k) => [k, all.bundles.get(BUNDLE_KEYS[k])] as const)
          .filter(([, p]) => p && forSale.length > 1)
          .map(([k, p]) => [k, { cents: p!.cents, currency: p!.currency, levels: k === "all" ? forSale.length : 2 }]),
      ),
      next: Object.fromEntries(forSale.map((s) => [s, nextFor(s, forSale)]).filter(([, n]) => n)),
    },
    200,
    { "cache-control": "public, max-age=60" },
  );
});

shop.post("/api/checkout", async (c) => {
  if (!checkoutOn(c.env)) return c.json({ ok: false, error: "Checkout isn't open yet." }, 503);
  const body = await c.req.json<{ level?: string; bundle?: string }>().catch(() => ({}) as { level?: string; bundle?: string });
  const kind: Kind = body.bundle === "two" || body.bundle === "all" ? body.bundle : "level";
  const [prices, withFiles] = await Promise.all([allPrices(c.env), levelsForSale(c.env.FILES)]);
  const forSale = withFiles.filter((s) => prices.bySlug.has(s)).sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b));
  let slugs: string[] = [];
  if (kind === "all") slugs = forSale;
  else {
    const slug = String(body.level ?? "");
    if (forSale.includes(slug)) slugs = kind === "two" ? [slug, nextFor(slug, forSale)].filter(Boolean) as string[] : [slug];
  }
  const price = kind === "level" ? prices.bySlug.get(slugs[0] ?? "") : prices.bundles.get(BUNDLE_KEYS[kind]);
  if (!price || !slugs.length || (kind === "two" && slugs.length !== 2) || (kind === "all" && slugs.length < 2)) {
    return c.json({ ok: false, error: kind === "level" ? "That level isn't for sale yet." : "That bundle isn't available." }, 404);
  }
  const origin = new URL(c.req.url).origin;
  const metadata = { level: slugs[0], levels: slugs.join(","), kind };
  try {
    const session = await createCheckoutSession(c.env.STRIPE_SECRET_KEY!, {
      mode: "payment",
      line_items: [{ price: price.id, quantity: 1 }],
      allow_promotion_codes: true,
      metadata,
      payment_intent_data: { metadata, description: `paperlessons: ${orderName(kind, slugs)}` },
      success_url: `${origin}/thanks?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/#library`,
    });
    return c.json({ ok: true, url: session.url });
  } catch (e) {
    console.error(e);
    return c.json({ ok: false, error: "Couldn't start checkout. Please try again." }, 502);
  }
});

/**
 * Store a paid session as an order (idempotent) and return its download token. The first time an order is
 * stored, the buyer gets an email with the download link, which expires 7 days after purchase.
 */
async function recordOrder(env: ShopEnv, s: CheckoutSession, origin: string): Promise<string | null> {
  // "no_payment_required" = a 100%-off promotion code, which is still a real order.
  if (s.payment_status === "unpaid" || s.status !== "complete") return null;
  const slugs = (s.metadata?.levels ?? s.metadata?.level ?? "").split(",").filter((x) => LEVELS.has(x));
  const kind: Kind = s.metadata?.kind === "two" || s.metadata?.kind === "all" ? s.metadata.kind : "level";
  if (!slugs.length) return null;
  const email = s.customer_details?.email?.toLowerCase() ?? null;
  const inserted = await env.DB.prepare(
    "INSERT INTO orders (session_id, token, level, levels, kind, email, amount_cents, currency, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+7 days')) ON CONFLICT(session_id) DO NOTHING",
  )
    .bind(s.id, newToken(), slugs[0], slugs.join(","), kind, email, s.amount_total ?? 0, s.currency ?? "")
    .run();
  const row = await env.DB.prepare("SELECT token, expires_at FROM orders WHERE session_id = ?")
    .bind(s.id)
    .first<{ token: string; expires_at: string }>();
  if (row && email && inserted.meta.changes > 0) {
    const single = slugs.length === 1 ? LEVELS.get(slugs[0])! : null;
    await sendOrderEmail(env.EMAIL, {
      to: email,
      levelName: orderName(kind, slugs),
      levelTitle: single ? single.title : kind === "all" ? "every level, ages 3 to 12" : "two levels in a row",
      url: `${origin}/orders/${row.token}`,
      expiresAt: row.expires_at,
    });
  }
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
    await recordOrder(c.env, event.data.object, new URL(c.req.url).origin);
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
    const token = await recordOrder(c.env, await getCheckoutSession(c.env.STRIPE_SECRET_KEY!, sid), new URL(c.req.url).origin);
    if (token) return c.json({ ok: true, token });
    return c.json({ ok: false, pending: true, error: "We're still confirming your payment." }, 202);
  } catch {
    return c.json({ ok: false, error: "Not found" }, 404);
  }
});

type OrderRow = {
  level: string;
  levels: string | null;
  kind: string | null;
  email: string | null;
  created_at: string;
  expires_at: string | null;
  expired: number;
};

const orderLevels = (o: OrderRow) => (o.levels ?? o.level).split(",").filter((x) => LEVELS.has(x));

async function orderFor(db: D1Database, token: string) {
  if (!TOKEN.test(token)) return null;
  return db
    .prepare(
      "SELECT level, levels, kind, email, created_at, expires_at, (expires_at IS NOT NULL AND expires_at <= datetime('now')) AS expired FROM orders WHERE token = ?",
    )
    .bind(token)
    .first<OrderRow>();
}

const EXPIRED = { ok: false, expired: true, error: "This download link has expired." } as const;

shop.get("/api/orders/:token", async (c) => {
  const token = c.req.param("token");
  const order = await orderFor(c.env.DB, token);
  if (!order) return c.json({ ok: false, error: "We couldn't find that order." }, 404);
  if (order.expired) return c.json(EXPIRED, 410, { "cache-control": "private, no-store" });
  const slugs = orderLevels(order);
  const groups = await Promise.all(
    slugs.map(async (slug) => {
      const l = LEVELS.get(slug)!;
      const files = await levelFiles(c.env.FILES, slug);
      return {
        slug,
        name: l.name,
        title: l.title,
        age: l.age,
        files: files.map((f) => ({ ...f, url: `/api/orders/${token}/files/${f.name}` })),
      };
    }),
  );
  const first = groups[0];
  return c.json(
    {
      ok: true,
      kind: order.kind ?? "level",
      name: orderName((order.kind as Kind) ?? "level", slugs),
      level: { slug: first.slug, name: first.name, title: first.title, age: first.age },
      levels: groups,
      email: order.email,
      purchasedAt: order.created_at,
      expiresAt: order.expires_at,
      files: groups.flatMap((g) => g.files),
    },
    200,
    { "cache-control": "private, no-store" },
  );
});

shop.get("/api/orders/:token/files/:file", async (c) => {
  const { token, file } = c.req.param();
  const order = await orderFor(c.env.DB, token);
  if (!order || !FILE.test(file)) return c.json({ ok: false, error: "Not found" }, 404);
  if (order.expired) return c.json(EXPIRED, 410);
  // Book files are named <slug>-<subject>-level….pdf, so the prefix says which of the order's levels it belongs to.
  const slug = orderLevels(order).find((l) => file.startsWith(`${l}-`));
  if (!slug) return c.json({ ok: false, error: "Not found" }, 404);
  const obj = await c.env.FILES.get(`levels/${slug}/${file}`);
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

// Selling whole levels as PDFs: Stripe Checkout (hosted page) → order row in D1 → download page.
//
// What's for sale and prices: worker/catalog.ts. Gifts (buying for another family, redeeming a code): worker/gift.ts.
// Checkout stays off until the Stripe secrets are set:
//   npx wrangler secret put STRIPE_SECRET_KEY
//   npx wrangler secret put STRIPE_WEBHOOK_SECRET
import { Hono } from "hono";
import {
  BUNDLE_KEYS,
  LEVELS,
  allPrices,
  buyableLevels,
  checkoutOn,
  levelFiles,
  levelsForSale,
  nextFor,
  orderName,
  orderTitle,
  parseKind,
  FILE,
  type Kind,
  type ShopEnv,
} from "./catalog";
import { sendOrderEmail } from "./email";
import { applyGiftPayment, giftCatalog, isGiftPurchase, recordGift } from "./gift";
import { createCheckoutSession, getCheckoutSession, newToken, verifyWebhook, type CheckoutSession } from "./stripe";

export type { ShopEnv } from "./catalog";

const TOKEN = /^[A-Za-z0-9_-]{20,64}$/;
const SESSION = /^cs_[A-Za-z0-9_]{10,200}$/;

const shop = new Hono<{ Bindings: ShopEnv }>();

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
      gifts: giftCatalog(c.env, all),
    },
    200,
    { "cache-control": "public, max-age=60" },
  );
});

shop.post("/api/checkout", async (c) => {
  if (!checkoutOn(c.env)) return c.json({ ok: false, error: "Checkout isn't open yet." }, 503);
  const body = await c.req.json<{ level?: string; bundle?: string }>().catch(() => ({}) as { level?: string; bundle?: string });
  const kind: Kind = body.bundle === "two" || body.bundle === "all" ? body.bundle : "level";
  const { prices, forSale } = await buyableLevels(c.env);
  let slugs: string[] = [];
  if (kind === "all") slugs = forSale;
  else {
    const slug = String(body.level ?? "");
    if (forSale.includes(slug)) slugs = kind === "two" ? [slug, nextFor(slug, forSale)].filter(Boolean) as string[] : [slug];
  }
  const price = kind === "level" ? prices.bySlug.get(slugs[0] ?? "") : prices.bundles.get(BUNDLE_KEYS[kind as "two" | "all"]);
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
export async function recordOrder(env: ShopEnv, s: CheckoutSession, origin: string): Promise<string | null> {
  // "no_payment_required" = a 100%-off promotion code, which is still a real order.
  if (s.payment_status === "unpaid" || s.status !== "complete") return null;
  const slugs = (s.metadata?.levels ?? s.metadata?.level ?? "").split(",").filter((x) => LEVELS.has(x));
  const kind = parseKind(s.metadata?.kind);
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
    await sendOrderEmail(env.EMAIL, {
      to: email,
      levelName: orderName(kind, slugs),
      levelTitle: orderTitle(kind, slugs),
      url: `${origin}/orders/${row.token}`,
      expiresAt: row.expires_at,
      gift: Boolean(s.metadata?.gift_code),
    });
  }
  return row?.token ?? null;
}

/**
 * A paid session, from the webhook or from a return page that got there first. Every step is idempotent
 * (keyed on the session id), so both paths can run, in any order, any number of times.
 */
async function handlePaidSession(env: ShopEnv, s: CheckoutSession, origin: string) {
  if (isGiftPurchase(s)) return { gift: await recordGift(env, s, origin) };
  const token = await recordOrder(env, s, origin);
  if (token) await applyGiftPayment(env, s);
  return { token };
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
    await handlePaidSession(c.env, event.data.object, new URL(c.req.url).origin);
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
    const { token } = await handlePaidSession(c.env, await getCheckoutSession(c.env.STRIPE_SECRET_KEY!, sid), new URL(c.req.url).origin);
    if (token) return c.json({ ok: true, token });
    return c.json({ ok: false, pending: true, error: "We're still confirming your payment." }, 202);
  } catch {
    return c.json({ ok: false, error: "Not found" }, 404);
  }
});

/** A gift buyer's return page asks for the gift code (same fallback as orders). */
shop.get("/api/gift/session/:sid", async (c) => {
  const sid = c.req.param("sid");
  if (!SESSION.test(sid)) return c.json({ ok: false, error: "Not found" }, 404);
  const row = await c.env.DB.prepare("SELECT code FROM gifts WHERE session_id = ?").bind(sid).first<{ code: string }>();
  if (row) return c.json({ ok: true, code: row.code });
  if (!checkoutOn(c.env)) return c.json({ ok: false, error: "Not found" }, 404);
  try {
    const { gift } = await handlePaidSession(c.env, await getCheckoutSession(c.env.STRIPE_SECRET_KEY!, sid), new URL(c.req.url).origin);
    if (gift) return c.json({ ok: true, code: gift });
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
      name: orderName(parseKind(order.kind ?? undefined), slugs),
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

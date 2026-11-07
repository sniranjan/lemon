// Gifts: one parent buys paperlessons for another family (GitHub issue #1).
//
// Buying:   gift form on our site → POST /api/gift/checkout (validates everything; the details travel in the
//           Checkout Session's metadata, since Managed Payments rejects custom_text) → Stripe → webhook creates
//           the `gifts` row (recordGift) and emails the buyer a receipt + printable card. Never download links.
// Delivery: on deliver_on (a UTC date) the recipient gets the message and a redeem link. "Today" is sent from
//           the webhook straight away; later dates by the daily cron (deliverDueGifts, wrangler triggers.crons).
// Redeeming (/redeem): an every-level gift becomes one order for all 13 levels, once. A gift amount pays for
//           a cart of levels: covered in full → the order is made here, no Stripe; otherwise Stripe charges the
//           rest with a one-off amount_off coupon. The balance is only taken once that payment succeeds
//           (applyGiftPayment, from the webhook), and a hold stops two open checkouts spending the same dollars.
// Either way the family gets the usual order: the 7-day download link (worker/shop.ts).
// Codes never expire. All sales are final.
import { Hono } from "hono";
import { planPayment, quoteCart } from "../src/lib/cart";
import {
  BUNDLE_KEYS,
  ORDER,
  buyableLevels,
  checkoutOn,
  nextFor,
  orderName,
  orderTitle,
  parseKind,
  type Prices,
  type ShopEnv,
} from "./catalog";
import { sendGiftBuyerEmail, sendGiftRecipientEmail, sendOrderEmail } from "./email";
import { createCheckoutSession, createCoupon, newToken, type CheckoutSession } from "./stripe";

/** Links in emails sent by the cron (which has no request to take an origin from). */
export const SITE = "https://paperlessons.com";

export const GIFT_PRESETS = [1900, 2900, 5000];
export const CUSTOM_MIN = 1000;
export const CUSTOM_MAX = 25000;
export const MESSAGE_MAX = 300;
export const NAME_MAX = 60;
export const CHILD_MAX = 30;
export const DAYS_AHEAD = 90;
const CURRENCY = "usd";

// ---------------------------------------------------------------------------------------------------------
// Dates, codes, validation (pure)

/** Today's date in UTC, YYYY-MM-DD. */
export const todayUTC = (now = new Date()) => now.toISOString().slice(0, 10);

export function addDays(iso: string, days: number): string {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

// No 0/O, 1/I/L: easy to read off a printed card and type back in.
const ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";

/** XXXX-XXXX-XXXX from a 31-letter alphabet (about 59 bits). */
export function newGiftCode(): string {
  const out: string[] = [];
  while (out.length < 12) {
    for (const b of crypto.getRandomValues(new Uint8Array(16))) {
      if (b < 248 && out.length < 12) out.push(ALPHABET[b % 31]); // 248 = 31 × 8: no bias
    }
  }
  return `${out.slice(0, 4).join("")}-${out.slice(4, 8).join("")}-${out.slice(8).join("")}`;
}

/** What someone typed ("abcd efgh jkmn", "ABCD-EFGH-JKMN") → the stored form, or null if it can't be a code. */
export function normalizeCode(input: string): string | null {
  const raw = input.toUpperCase().replace(/[^A-Z0-9]/g, "");
  if (raw.length !== 12 || [...raw].some((ch) => !ALPHABET.includes(ch))) return null;
  return `${raw.slice(0, 4)}-${raw.slice(4, 8)}-${raw.slice(8)}`;
}

/** One line of plain text: no control characters (they could break an email Subject), spaces squeezed. */
function line(v: unknown, max: number): string {
  return String(v ?? "")
    .normalize("NFC")
    .replace(/[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/gu, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, max + 1);
}

/** The message: line breaks kept (at most one blank line in a row), other control characters dropped. */
function messageText(v: unknown): string {
  return String(v ?? "")
    .normalize("NFC")
    .replace(/\r\n?/g, "\n")
    .replace(/[^\P{Cc}\n]|[\p{Cf}\p{Zl}\p{Zp}]/gu, "")
    .split("\n")
    .map((l) => l.replace(/[ \t]+/g, " ").trim())
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

const EMAIL = /^[^\s@"<>(),;:]+@[^\s@"<>(),;:]+\.[a-z]{2,}$/i;
const CHILD = /^\p{L}[\p{L}\p{M}'’-]*$/u;
const DATE = /^\d{4}-\d{2}-\d{2}$/;

export function validEmail(v: unknown): string | null {
  const e = line(v, 254).toLowerCase();
  return e.length <= 254 && EMAIL.test(e) ? e : null;
}

export type GiftForm = {
  kind: "all" | "credit";
  amountCents: number;
  buyerName: string;
  recipientName: string;
  recipientEmail: string;
  childName: string | null;
  message: string | null;
  deliverOn: string;
};

type Invalid = { ok: false; field: string; error: string };

/**
 * Check a gift form. `today` is the UTC date. The delivery date may be one day before it (the buyer's "today"
 * west of UTC) up to 90 days out (+1 for time zones east of UTC). `allCents` is the every-level price, or null
 * when it isn't for sale.
 */
export function validateGift(body: unknown, today: string, allCents: number | null): { ok: true; gift: GiftForm } | Invalid {
  const b = (body && typeof body === "object" ? body : {}) as Record<string, unknown>;
  const bad = (field: string, error: string): Invalid => ({ ok: false, field, error });

  let kind: GiftForm["kind"];
  let amountCents: number;
  if (b.kind === "all") {
    if (!allCents) return bad("kind", "The every-level gift isn't available right now.");
    kind = "all";
    amountCents = allCents;
  } else if (b.kind === "credit") {
    kind = "credit";
    amountCents = Number(b.amountCents);
    const preset = GIFT_PRESETS.includes(amountCents);
    const custom = Number.isInteger(amountCents) && amountCents % 100 === 0 && amountCents >= CUSTOM_MIN && amountCents <= CUSTOM_MAX;
    if (!preset && !custom) return bad("amountCents", "Pick an amount, or type a whole-dollar amount from $10 to $250.");
  } else return bad("kind", "Pick a gift.");

  const buyerName = line(b.buyerName, NAME_MAX);
  if (!buyerName) return bad("buyerName", "Please add your name, so they know who it's from.");
  if (buyerName.length > NAME_MAX) return bad("buyerName", `Your name can be up to ${NAME_MAX} characters.`);

  const recipientName = line(b.recipientName, NAME_MAX);
  if (!recipientName) return bad("recipientName", "Who is the gift for?");
  if (recipientName.length > NAME_MAX) return bad("recipientName", `Their name can be up to ${NAME_MAX} characters.`);

  const recipientEmail = validEmail(b.recipientEmail);
  if (!recipientEmail) return bad("recipientEmail", "Please check their email address.");

  const child = line(b.childName, CHILD_MAX);
  if (child.length > CHILD_MAX) return bad("childName", `The child's first name can be up to ${CHILD_MAX} characters.`);
  if (child && !CHILD.test(child)) return bad("childName", "Just the child's first name, please (one word).");

  const message = messageText(b.message);
  if ([...message].length > MESSAGE_MAX) return bad("message", `The message can be up to ${MESSAGE_MAX} characters.`);

  const deliverOn = String(b.deliverOn ?? "");
  if (!DATE.test(deliverOn) || Number.isNaN(Date.parse(`${deliverOn}T00:00:00Z`)) || addDays(deliverOn, 0) !== deliverOn) {
    return bad("deliverOn", "Please pick a delivery date.");
  }
  if (deliverOn < addDays(today, -1) || deliverOn > addDays(today, DAYS_AHEAD + 1)) {
    return bad("deliverOn", `Pick a delivery date from today to ${DAYS_AHEAD} days from now.`);
  }

  return {
    ok: true,
    gift: { kind, amountCents, buyerName, recipientName, recipientEmail, childName: child || null, message: message || null, deliverOn },
  };
}

export const dollars = (cents: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: cents % 100 ? 2 : 0 }).format(cents / 100);

/** "every level, ages 3 to 12" / "$50 to spend on any level". */
const giftWhat = (kind: string, amountCents: number) => (kind === "all" ? "every level, ages 3 to 12" : `${dollars(amountCents)} to spend on any level`);

/** What the site shows about gifts (in /api/catalog). */
export function giftCatalog(env: ShopEnv, prices: Prices) {
  const all = prices.bundles.get(BUNDLE_KEYS.all);
  return {
    open: checkoutOn(env),
    allCents: all && all.currency === CURRENCY ? all.cents : null,
    presets: GIFT_PRESETS,
    min: CUSTOM_MIN,
    max: CUSTOM_MAX,
  };
}

// ---------------------------------------------------------------------------------------------------------
// Buying a gift: Stripe → webhook

export const isGiftPurchase = (s: CheckoutSession) => s.metadata?.gift === "buy";

type GiftRow = {
  code: string;
  kind: "all" | "credit";
  amount_cents: number;
  balance_cents: number;
  currency: string;
  buyer_name: string;
  buyer_email: string | null;
  recipient_name: string;
  recipient_email: string;
  child_name: string | null;
  message: string | null;
  deliver_on: string;
  delivered_at: string | null;
  resent_at: string | null;
  created_at: string;
};

const giftByCode = (db: D1Database, code: string) => db.prepare("SELECT * FROM gifts WHERE code = ?").bind(code).first<GiftRow>();

/**
 * Store a paid gift purchase (idempotent: keyed on the session id) and return its code. The first time, the
 * buyer gets the receipt + gift card email. A gift due today (or earlier) is delivered right away.
 */
export async function recordGift(env: ShopEnv, s: CheckoutSession, origin: string, today = todayUTC()): Promise<string | null> {
  // Only a real payment makes a gift (promotion codes are off for gifts, so "no_payment_required" never should).
  if (!isGiftPurchase(s) || s.status !== "complete" || s.payment_status !== "paid") return null;
  const m = s.metadata!;
  const kind = m.gift_kind === "all" ? "all" : "credit";
  const cents = Number(m.gift_cents);
  if (!Number.isInteger(cents) || cents <= 0 || !m.recipient_email || !m.deliver_on) {
    console.error("gift session with bad metadata", s.id);
    return null;
  }
  const buyerEmail = s.customer_details?.email?.toLowerCase() ?? null;
  let inserted = false;
  for (let attempt = 0; attempt < 4 && !inserted; attempt++) {
    try {
      const r = await env.DB.prepare(
        `INSERT INTO gifts (code, session_id, kind, amount_cents, balance_cents, currency, buyer_name, buyer_email,
           recipient_name, recipient_email, child_name, message, deliver_on)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(session_id) DO NOTHING`,
      )
        .bind(
          newGiftCode(),
          s.id,
          kind,
          cents,
          cents,
          CURRENCY,
          m.buyer_name || "A friend",
          buyerEmail,
          m.recipient_name || "you",
          m.recipient_email,
          m.child_name || null,
          m.message || null,
          m.deliver_on,
        )
        .run();
      inserted = r.meta.changes > 0;
      break; // stored now, or already stored by an earlier call
    } catch (e) {
      // A clash on the random code (UNIQUE): try another one.
      if (!String(e).includes("UNIQUE") || attempt === 3) throw e;
    }
  }
  const row = await env.DB.prepare("SELECT * FROM gifts WHERE session_id = ?").bind(s.id).first<GiftRow>();
  if (!row) return null;
  const sendNow = row.deliver_on <= today;
  if (inserted && buyerEmail) {
    await sendGiftBuyerEmail(env.EMAIL, {
      ...giftEmailFields(row),
      to: buyerEmail,
      amount: dollars(row.amount_cents),
      cardUrl: `${origin}/gift/card/${row.code}`,
      deliverOn: row.deliver_on,
      sentNow: sendNow,
    });
  }
  if (sendNow && !row.delivered_at) await deliverGift(env, row.code, origin);
  return row.code;
}

const giftEmailFields = (g: GiftRow) => ({
  code: g.code,
  what: giftWhat(g.kind, g.amount_cents),
  buyerName: g.buyer_name,
  recipientName: g.recipient_name,
  childName: g.child_name,
  message: g.message,
});

/**
 * Email the recipient, once. The row is claimed first (delivered_at set only if still empty), so a webhook
 * retry and the cron can't both send; if the send fails the claim is undone and tomorrow's cron tries again.
 */
export async function deliverGift(env: ShopEnv, code: string, origin = SITE): Promise<boolean> {
  const claim = await env.DB.prepare("UPDATE gifts SET delivered_at = datetime('now') WHERE code = ? AND delivered_at IS NULL")
    .bind(code)
    .run();
  if (claim.meta.changes !== 1) return false;
  const g = await giftByCode(env.DB, code);
  const sent =
    g != null &&
    (await sendGiftRecipientEmail(env.EMAIL, { ...giftEmailFields(g), to: g.recipient_email, redeemUrl: `${origin}/redeem?code=${g.code}` }));
  if (!sent) await env.DB.prepare("UPDATE gifts SET delivered_at = NULL WHERE code = ?").bind(code).run();
  return sent;
}

/** The daily cron: every gift due on or before `today` (UTC) that hasn't gone out yet. */
export async function deliverDueGifts(env: ShopEnv, today = todayUTC(), origin = SITE): Promise<number> {
  const due = await env.DB.prepare("SELECT code FROM gifts WHERE delivered_at IS NULL AND deliver_on <= ? ORDER BY id LIMIT 500")
    .bind(today)
    .all<{ code: string }>();
  let sent = 0;
  for (const { code } of due.results) if (await deliverGift(env, code, origin)) sent++;
  if (due.results.length) console.log(`gifts: delivered ${sent} of ${due.results.length} due`);
  return sent;
}

// ---------------------------------------------------------------------------------------------------------
// Paying with a gift balance: after "pay the rest" succeeds

const ACTIVE_HOLDS = "COALESCE((SELECT SUM(cents) FROM gift_holds WHERE code = gifts.code AND expires_at > datetime('now')), 0)";

/**
 * Take the gift balance a paid "pay the rest" session used (metadata gift_code + gift_cents, our own number:
 * never amount_total, which may include tax). One transaction, keyed on the session id, so webhook retries
 * and the thanks page can both call it. Never throws on a short balance (Stripe would retry forever).
 */
export async function applyGiftPayment(env: ShopEnv, s: CheckoutSession): Promise<void> {
  const code = s.metadata?.gift_code;
  if (!code || s.status !== "complete" || s.payment_status === "unpaid") return;
  const used = Number(s.metadata?.gift_cents);
  if (!Number.isInteger(used) || used < 0) return;
  const before = await env.DB.prepare("SELECT balance_cents FROM gifts WHERE code = ?").bind(code).first<{ balance_cents: number }>();
  const [taken] = await env.DB.batch([
    env.DB.prepare(
      "UPDATE gifts SET balance_cents = MAX(0, balance_cents - ?) WHERE code = ? AND NOT EXISTS (SELECT 1 FROM gift_redemptions WHERE order_session = ?)",
    ).bind(used, code, s.id),
    env.DB.prepare("INSERT INTO gift_redemptions (code, order_session, cents_used) VALUES (?, ?, ?) ON CONFLICT(order_session) DO NOTHING").bind(
      code,
      s.id,
      used,
    ),
    env.DB.prepare("DELETE FROM gift_holds WHERE id = ? OR session_id = ?").bind(s.metadata?.gift_hold ?? "", s.id),
  ]);
  if (taken.meta.changes && before && before.balance_cents < used) {
    console.error(`gift ${code}: session ${s.id} used ${used} but only ${before.balance_cents} was left`);
  }
}

// ---------------------------------------------------------------------------------------------------------
// Routes

const gift = new Hono<{ Bindings: ShopEnv }>();
const PRIVATE = { "cache-control": "private, no-store" };

gift.post("/api/gift/checkout", async (c) => {
  if (!checkoutOn(c.env)) return c.json({ ok: false, error: "Gifts aren't open yet." }, 503);
  const body = await c.req.json().catch(() => null);
  const { prices } = await buyableLevels(c.env);
  const v = validateGift(body, todayUTC(), giftCatalog(c.env, prices).allCents);
  if (!v.ok) return c.json(v, 400);
  const g = v.gift;
  const origin = new URL(c.req.url).origin;
  const name = g.kind === "all" ? "Paper Lessons gift: every level" : `Paper Lessons gift: ${dollars(g.amountCents)}`;
  // Metadata values are at most 500 characters; every field here is capped well below that.
  const metadata: Record<string, string | undefined> = {
    gift: "buy",
    gift_kind: g.kind,
    gift_cents: String(g.amountCents),
    buyer_name: g.buyerName,
    recipient_name: g.recipientName,
    recipient_email: g.recipientEmail,
    child_name: g.childName ?? undefined,
    message: g.message ?? undefined,
    deliver_on: g.deliverOn,
  };
  try {
    const session = await createCheckoutSession(c.env.STRIPE_SECRET_KEY!, {
      mode: "payment",
      line_items: [
        {
          quantity: 1,
          price_data: {
            currency: CURRENCY,
            unit_amount: g.amountCents,
            product_data: {
              name,
              description:
                g.kind === "all"
                  ? `For ${g.recipientName}: all 13 levels of printable reading and math pages, ages 3 to 12. Code never expires.`
                  : `For ${g.recipientName}: ${dollars(g.amountCents)} to spend on any level. Code never expires.`,
            },
          },
        },
      ],
      // No promotion codes on gifts: a 100%-off code would mint free gift balance.
      metadata,
      payment_intent_data: { metadata: { gift: "buy", gift_kind: g.kind }, description: `paperlessons: ${name}` },
      success_url: `${origin}/gift/thanks?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/gift`,
    });
    return c.json({ ok: true, url: session.url });
  } catch (e) {
    console.error(e);
    return c.json({ ok: false, error: "Couldn't start checkout. Please try again." }, 502);
  }
});

/** The redeem page and the printable card. No email addresses, no order tokens. */
gift.get("/api/gift/:code", async (c) => {
  const code = normalizeCode(c.req.param("code"));
  const g = code ? await giftByCode(c.env.DB, code) : null;
  if (!g) return c.json({ ok: false, error: "We couldn't find that gift code. Check the letters and try again." }, 404);
  const [held, orders] = await Promise.all([
    c.env.DB.prepare(`SELECT ${ACTIVE_HOLDS} AS held FROM gifts WHERE code = ?`).bind(g.code).first<{ held: number }>(),
    c.env.DB.prepare(
      `SELECT o.kind, o.level, o.levels, o.created_at, o.expires_at, (o.expires_at <= datetime('now')) AS expired, r.cents_used
       FROM gift_redemptions r JOIN orders o ON o.session_id = r.order_session WHERE r.code = ? ORDER BY r.id`,
    )
      .bind(g.code)
      .all<{ kind: string; level: string; levels: string | null; created_at: string; expires_at: string; expired: number; cents_used: number }>(),
  ]);
  return c.json(
    {
      ok: true,
      code: g.code,
      kind: g.kind,
      amountCents: g.amount_cents,
      balanceCents: Math.max(0, g.balance_cents - (held?.held ?? 0)),
      currency: g.currency,
      buyerName: g.buyer_name,
      recipientName: g.recipient_name,
      childName: g.child_name,
      message: g.message,
      deliverOn: g.deliver_on,
      delivered: Boolean(g.delivered_at),
      redeemed: g.kind === "all" && orders.results.length > 0,
      orders: orders.results.map((o) => {
        const slugs = (o.levels ?? o.level).split(",");
        return { name: orderName(parseKind(o.kind), slugs), createdAt: o.created_at, expiresAt: o.expires_at, expired: Boolean(o.expired), centsUsed: o.cents_used };
      }),
    },
    200,
    PRIVATE,
  );
});

type OrderMade = { token: string; email: string; expires_at: string; kind: string; levels: string };

async function emailOrder(env: ShopEnv, o: OrderMade, origin: string) {
  const slugs = o.levels.split(",");
  const kind = parseKind(o.kind);
  return sendOrderEmail(env.EMAIL, {
    to: o.email,
    levelName: orderName(kind, slugs),
    levelTitle: orderTitle(kind, slugs),
    url: `${origin}/orders/${o.token}`,
    expiresAt: o.expires_at,
    gift: true,
  });
}

const orderBySession = (db: D1Database, sid: string) =>
  db.prepare("SELECT token, email, expires_at, kind, levels FROM orders WHERE session_id = ?").bind(sid).first<OrderMade>();

/**
 * Every-level gift → one order for all 13 levels, once. The order's session id is fixed per code, so the
 * UNIQUE constraint on orders.session_id makes a second redemption (even a simultaneous one) impossible.
 */
gift.post("/api/gift/:code/redeem", async (c) => {
  const code = normalizeCode(c.req.param("code"));
  const g = code ? await giftByCode(c.env.DB, code) : null;
  if (!g) return c.json({ ok: false, error: "We couldn't find that gift code." }, 404);
  if (g.kind !== "all") return c.json({ ok: false, error: "This gift is an amount to spend: pick the levels you'd like." }, 400);
  const body = await c.req.json<{ email?: string }>().catch(() => ({}) as { email?: string });
  const email = validEmail(body.email);
  if (!email) return c.json({ ok: false, field: "email", error: "Please check your email address: we send your download link there." }, 400);
  const sid = `gift-all-${g.code}`;
  const [made] = await c.env.DB.batch([
    c.env.DB.prepare(
      `INSERT INTO orders (session_id, token, level, levels, kind, email, amount_cents, currency, expires_at)
       SELECT ?, ?, ?, ?, 'all', ?, 0, currency, datetime('now', '+7 days') FROM gifts WHERE code = ? AND kind = 'all' AND balance_cents > 0
       ON CONFLICT(session_id) DO NOTHING`,
    ).bind(sid, newToken(), ORDER[0], ORDER.join(","), email, g.code),
    c.env.DB.prepare(
      `INSERT INTO gift_redemptions (code, order_session, cents_used)
       SELECT code, ?, balance_cents FROM gifts WHERE code = ? AND balance_cents > 0 AND EXISTS (SELECT 1 FROM orders WHERE session_id = ?)
       ON CONFLICT(order_session) DO NOTHING`,
    ).bind(sid, g.code, sid),
    c.env.DB.prepare("UPDATE gifts SET balance_cents = 0 WHERE code = ? AND EXISTS (SELECT 1 FROM gift_redemptions WHERE order_session = ?)").bind(
      g.code,
      sid,
    ),
  ]);
  if (made.meta.changes !== 1) {
    return c.json({ ok: false, redeemed: true, error: "This gift has already been opened. Use “Resend my files” below if you need the link again." }, 409);
  }
  const order = (await orderBySession(c.env.DB, sid))!;
  await emailOrder(c.env, order, new URL(c.req.url).origin);
  return c.json({ ok: true, token: order.token });
});

/**
 * Gift amount → a cart of levels. Covered in full: the order is made here (no Stripe). Otherwise Stripe
 * Checkout for the rest, with the balance used as a one-off amount_off coupon; the balance is taken in the
 * webhook once that payment succeeds.
 */
gift.post("/api/gift/:code/checkout", async (c) => {
  const code = normalizeCode(c.req.param("code"));
  const g = code ? await giftByCode(c.env.DB, code) : null;
  if (!g) return c.json({ ok: false, error: "We couldn't find that gift code." }, 404);
  if (g.kind !== "credit") return c.json({ ok: false, error: "This gift is every level: open it with one click." }, 400);
  if (!checkoutOn(c.env)) return c.json({ ok: false, error: "The shop isn't open yet." }, 503);
  const body = await c.req.json<{ levels?: unknown; email?: string }>().catch(() => ({}) as { levels?: unknown; email?: string });
  const email = validEmail(body.email);
  if (!email) return c.json({ ok: false, field: "email", error: "Please check your email address: we send your download link there." }, 400);
  const picked = Array.isArray(body.levels) ? body.levels.map(String).slice(0, 20) : [];
  const { prices, forSale } = await buyableLevels(c.env);
  const all = prices.bundles.get(BUNDLE_KEYS.all);
  const two = prices.bundles.get(BUNDLE_KEYS.two);
  const quote = quoteCart(picked, {
    forSale,
    prices: Object.fromEntries([...prices.bySlug].map(([s, p]) => [s, { cents: p.cents }])),
    bundles: { all: all && { cents: all.cents }, two: two && { cents: two.cents } },
    next: Object.fromEntries(forSale.map((s) => [s, nextFor(s, forSale)]).filter(([, n]) => n)) as Record<string, string>,
  });
  if (!quote) return c.json({ ok: false, error: "Pick at least one level that's for sale." }, 400);
  const held = await c.env.DB.prepare(`SELECT balance_cents - ${ACTIVE_HOLDS} AS available FROM gifts WHERE code = ?`)
    .bind(g.code)
    .first<{ available: number }>();
  const available = Math.max(0, held?.available ?? 0);
  if (available <= 0) return c.json({ ok: false, error: "This gift's balance is all used up." }, 409);
  const { use, rest } = planPayment(quote.cents, available);
  const origin = new URL(c.req.url).origin;

  if (rest === 0) {
    // The gift covers it: one transaction takes the balance (only if it's still there) and makes the order.
    const sid = `gift_${newToken()}`;
    const [taken] = await c.env.DB.batch([
      c.env.DB.prepare(
        `INSERT INTO gift_redemptions (code, order_session, cents_used)
         SELECT code, ?, ? FROM gifts WHERE code = ? AND kind = 'credit' AND balance_cents - ${ACTIVE_HOLDS} >= ?`,
      ).bind(sid, use, g.code, use),
      c.env.DB.prepare("UPDATE gifts SET balance_cents = balance_cents - ? WHERE code = ? AND EXISTS (SELECT 1 FROM gift_redemptions WHERE order_session = ?)").bind(
        use,
        g.code,
        sid,
      ),
      c.env.DB.prepare(
        `INSERT INTO orders (session_id, token, level, levels, kind, email, amount_cents, currency, expires_at)
         SELECT ?, ?, ?, ?, ?, ?, 0, ?, datetime('now', '+7 days') WHERE EXISTS (SELECT 1 FROM gift_redemptions WHERE order_session = ?)`,
      ).bind(sid, newToken(), quote.slugs[0], quote.slugs.join(","), quote.kind, email, g.currency, sid),
    ]);
    if (taken.meta.changes !== 1) return c.json({ ok: false, error: "Your balance just changed. Please try again." }, 409);
    const order = (await orderBySession(c.env.DB, sid))!;
    await emailOrder(c.env, order, origin);
    return c.json({ ok: true, token: order.token, paid: 0 });
  }

  // Pay the rest. Hold the part of the balance this checkout will use, so another tab can't spend it too.
  const holdId = newToken();
  const hold = await c.env.DB.prepare(
    `INSERT INTO gift_holds (id, code, cents, expires_at)
     SELECT ?, code, ?, datetime('now', '+40 minutes') FROM gifts WHERE code = ? AND balance_cents - ${ACTIVE_HOLDS} >= ?`,
  )
    .bind(holdId, use, g.code, use)
    .run();
  if (hold.meta.changes !== 1) return c.json({ ok: false, error: "Your balance just changed. Please try again." }, 409);

  const lineItems =
    quote.kind === "all" ? [{ price: all!.id, quantity: 1 }]
    : quote.kind === "two" ? [{ price: two!.id, quantity: 1 }]
    : quote.slugs.map((s) => ({ price: prices.bySlug.get(s)!.id, quantity: 1 }));
  const metadata = {
    level: quote.slugs[0],
    levels: quote.slugs.join(","),
    kind: quote.kind,
    gift_code: g.code,
    gift_cents: String(use),
    gift_hold: holdId,
  };
  try {
    const key = c.env.STRIPE_SECRET_KEY!;
    const coupon = use > 0
      ? await createCoupon(key, { amount_off: use, currency: g.currency, duration: "once", max_redemptions: 1, name: "Gift balance" }, `gift-coupon-${holdId}`)
      : null;
    const session = await createCheckoutSession(
      key,
      {
        mode: "payment",
        line_items: lineItems,
        ...(coupon ? { discounts: [{ coupon: coupon.id }] } : {}), // (Stripe won't take allow_promotion_codes with discounts)
        customer_email: email,
        metadata,
        payment_intent_data: { metadata, description: `paperlessons: ${orderName(quote.kind, quote.slugs)} (gift)` },
        expires_at: Math.floor(Date.now() / 1000) + 31 * 60, // the hold lasts 40 minutes, a little longer
        success_url: `${origin}/thanks?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${origin}/redeem?code=${g.code}`,
      },
      `gift-session-${holdId}`,
    );
    await c.env.DB.prepare("UPDATE gift_holds SET session_id = ? WHERE id = ?").bind(session.id, holdId).run();
    return c.json({ ok: true, url: session.url, paid: rest });
  } catch (e) {
    console.error(e);
    await c.env.DB.prepare("DELETE FROM gift_holds WHERE id = ?").bind(holdId).run();
    return c.json({ ok: false, error: "Couldn't start checkout. Please try again." }, 502);
  }
});

/**
 * "Resend my files": email the download link again for this code's orders that haven't expired, to the
 * address each order was made with. It never extends the 7 days. At most once every 2 minutes per code.
 */
gift.post("/api/gift/:code/resend", async (c) => {
  const code = normalizeCode(c.req.param("code"));
  const g = code ? await giftByCode(c.env.DB, code) : null;
  if (!g) return c.json({ ok: false, error: "We couldn't find that gift code." }, 404);
  const live = await c.env.DB.prepare(
    `SELECT o.token, o.email, o.expires_at, o.kind, COALESCE(o.levels, o.level) AS levels
     FROM gift_redemptions r JOIN orders o ON o.session_id = r.order_session
     WHERE r.code = ? AND o.email IS NOT NULL AND o.expires_at > datetime('now') ORDER BY r.id`,
  )
    .bind(g.code)
    .all<OrderMade>();
  if (!live.results.length) {
    return c.json({ ok: false, error: "There's nothing to resend: download links last 7 days after you open a gift, and these have expired." }, 410);
  }
  const claim = await c.env.DB.prepare(
    "UPDATE gifts SET resent_at = datetime('now') WHERE code = ? AND (resent_at IS NULL OR resent_at <= datetime('now', '-2 minutes'))",
  )
    .bind(g.code)
    .run();
  if (claim.meta.changes !== 1) return c.json({ ok: false, error: "We just sent it. Check your inbox (and the spam folder)." }, 429);
  const origin = new URL(c.req.url).origin;
  let sent = 0;
  for (const o of live.results) if (await emailOrder(c.env, o, origin)) sent++;
  return c.json({ ok: true, sent });
});

export default gift;

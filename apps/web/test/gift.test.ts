import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ladder from "../src/data/ladder.json";
import { planPayment, quoteCart } from "../src/lib/cart";
import { resetPriceCache } from "../worker/catalog";
import { addDays, deliverDueGifts, newGiftCode, normalizeCode, todayUTC, validateGift } from "../worker/gift";
import { app } from "../worker/index";
import { ALL_CENTS, LEVEL_CENTS, TWO_CENTS, ctx, makeEnv, sign, stubStripe, type StripeCall } from "./env";

const SLUGS = ladder.map((l) => l.slug);
const TODAY = todayUTC();

let t: ReturnType<typeof makeEnv>;
let stripe: ReturnType<typeof stubStripe>;

beforeEach(() => {
  resetPriceCache();
  t = makeEnv(SLUGS);
  stripe = stubStripe();
});
afterEach(() => vi.unstubAllGlobals());

const req = (path: string, init?: RequestInit) => app.request(`https://paperlessons.test${path}`, init, t.env, ctx);
const post = (path: string, body: unknown) => req(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });

/** `metadata[x]=y` form fields of a Stripe call → { x: y }. */
function metadataOf(call: StripeCall): Record<string, string> {
  return Object.fromEntries([...call.body.entries()].filter(([k]) => /^metadata\[\w+\]$/.test(k)).map(([k, v]) => [k.slice(9, -1), v]));
}

function paidSession(id: string, metadata: Record<string, string>, extra: Record<string, unknown> = {}) {
  return { id, url: null, status: "complete", payment_status: "paid", amount_total: 0, currency: "usd", customer_details: { email: "Buyer@Example.com" }, metadata, ...extra };
}

async function webhook(session: unknown, type = "checkout.session.completed") {
  const body = JSON.stringify({ type, data: { object: session } });
  return req("/api/stripe/webhook", { method: "POST", headers: { "stripe-signature": await sign(body) }, body });
}

const FORM = {
  kind: "all",
  buyerName: "Priya",
  recipientName: "Sam Lee",
  recipientEmail: "sam@example.com",
  childName: "Maya",
  message: "Happy birthday, Maya!\nLove, Priya",
  deliverOn: TODAY,
};

/** Buy a gift through the real routes: form → Checkout Session → signed webhook. Returns its code. */
async function buyGift(form: Record<string, unknown> = FORM) {
  const r = await post("/api/gift/checkout", form);
  expect(r.status).toBe(200);
  const call = stripe.calls.filter((c) => c.path === "/v1/checkout/sessions").at(-1)!;
  const id = `cs_test_gift${stripe.calls.length.toString().padStart(8, "0")}`;
  const session = paidSession(id, metadataOf(call), { amount_total: Number(call.body.get("line_items[0][price_data][unit_amount]")) });
  expect((await webhook(session)).status).toBe(200);
  const row = t.db.prepare("SELECT code FROM gifts WHERE session_id = ?").get(id) as { code: string };
  return { code: row.code, session };
}

const gift = (code: string) => t.db.prepare("SELECT * FROM gifts WHERE code = ?").get(code) as Record<string, unknown>;
const count = (sql: string, ...p: string[]) => Number((t.db.prepare(sql).get(...p) as { n: number }).n);

describe("gift form validation", () => {
  const ok = (over: Record<string, unknown>) => validateGift({ ...FORM, ...over }, TODAY, ALL_CENTS);

  it("accepts the every-level gift at the every-level price", () => {
    const v = ok({});
    expect(v.ok && v.gift).toMatchObject({ kind: "all", amountCents: ALL_CENTS, childName: "Maya", recipientEmail: "sam@example.com" });
  });

  it("accepts the preset amounts and whole-dollar custom amounts from $10 to $250", () => {
    for (const cents of [1900, 2900, 5000, 1000, 7500, 25000]) expect(ok({ kind: "credit", amountCents: cents }).ok).toBe(true);
    for (const cents of [900, 25100, 1050, 0, -1900, "lots", null]) expect(ok({ kind: "credit", amountCents: cents }).ok).toBe(false);
  });

  it("refuses the every-level gift when its price isn't available", () => {
    expect(validateGift(FORM, TODAY, null)).toMatchObject({ ok: false, field: "kind" });
  });

  it("needs both names and a real recipient email", () => {
    expect(ok({ buyerName: "  " })).toMatchObject({ ok: false, field: "buyerName" });
    expect(ok({ recipientName: "" })).toMatchObject({ ok: false, field: "recipientName" });
    expect(ok({ recipientEmail: "sam@" })).toMatchObject({ ok: false, field: "recipientEmail" });
    expect(ok({ buyerName: "x".repeat(61) })).toMatchObject({ ok: false, field: "buyerName" });
  });

  it("keeps names to one clean line (they go into the email Subject)", () => {
    const v = ok({ buyerName: "Priya\r\nBcc: evil@example.com", recipientName: "Sam\u0000 Lee" });
    expect(v.ok && v.gift.buyerName).toBe("Priya Bcc: evil@example.com");
    expect(v.ok && v.gift.recipientName).toBe("Sam Lee");
  });

  it("stores only a child's first name, and it's optional", () => {
    expect(ok({ childName: "Maya Lee" })).toMatchObject({ ok: false, field: "childName" });
    expect(ok({ childName: "" }).ok && (ok({ childName: "" }) as { gift: { childName: unknown } }).gift.childName).toBeNull();
    expect(ok({ childName: "Anne-Marie" }).ok).toBe(true);
  });

  it("caps the message at 300 characters", () => {
    expect(ok({ message: "a".repeat(300) }).ok).toBe(true);
    expect(ok({ message: "a".repeat(301) })).toMatchObject({ ok: false, field: "message" });
  });

  it("delivers today up to 90 days out (one day of slack for time zones)", () => {
    expect(ok({ deliverOn: addDays(TODAY, -1) }).ok).toBe(true); // already "tomorrow" in UTC for the buyer
    expect(ok({ deliverOn: addDays(TODAY, 90) }).ok).toBe(true);
    expect(ok({ deliverOn: addDays(TODAY, -2) })).toMatchObject({ ok: false, field: "deliverOn" });
    expect(ok({ deliverOn: addDays(TODAY, 92) })).toMatchObject({ ok: false, field: "deliverOn" });
    expect(ok({ deliverOn: "2026-02-30" })).toMatchObject({ ok: false, field: "deliverOn" });
  });

  it("makes readable codes and reads them back however they're typed", () => {
    const code = newGiftCode();
    expect(code).toMatch(/^[A-HJKMNP-Z2-9]{4}-[A-HJKMNP-Z2-9]{4}-[A-HJKMNP-Z2-9]{4}$/);
    expect(normalizeCode(code.toLowerCase().replace(/-/g, " "))).toBe(code);
    expect(normalizeCode("ABCD-EFGH-JK0N")).toBeNull(); // 0 is never used
    expect(normalizeCode("short")).toBeNull();
  });
});

describe("POST /api/gift/checkout", () => {
  it("rejects a bad form with the field to fix, without calling Stripe for a session", async () => {
    const r = await post("/api/gift/checkout", { ...FORM, recipientEmail: "nope" });
    expect(r.status).toBe(400);
    expect(await r.json()).toMatchObject({ ok: false, field: "recipientEmail" });
    expect(stripe.calls.some((c) => c.path === "/v1/checkout/sessions")).toBe(false);
  });

  it("starts Checkout with an inline price, the details in metadata, and no promotion codes", async () => {
    const r = await post("/api/gift/checkout", { ...FORM, kind: "credit", amountCents: 5000 });
    expect(await r.json()).toMatchObject({ ok: true, url: expect.stringContaining("checkout.stripe.test") });
    const call = stripe.calls.find((c) => c.path === "/v1/checkout/sessions")!;
    expect(call.body.get("line_items[0][price_data][unit_amount]")).toBe("5000");
    expect(call.body.get("line_items[0][price_data][currency]")).toBe("usd");
    expect(call.body.has("allow_promotion_codes")).toBe(false);
    expect(call.body.has("custom_text[submit][message]")).toBe(false);
    expect(call.body.get("success_url")).toBe("https://paperlessons.test/gift/thanks?session_id={CHECKOUT_SESSION_ID}");
    expect(metadataOf(call)).toEqual({
      gift: "buy",
      gift_kind: "credit",
      gift_cents: "5000",
      buyer_name: "Priya",
      recipient_name: "Sam Lee",
      recipient_email: "sam@example.com",
      child_name: "Maya",
      message: "Happy birthday, Maya!\nLove, Priya",
      deliver_on: TODAY,
    });
  });

  it("charges the every-level price from Stripe for the every-level gift", async () => {
    await post("/api/gift/checkout", FORM);
    const call = stripe.calls.find((c) => c.path === "/v1/checkout/sessions")!;
    expect(call.body.get("line_items[0][price_data][unit_amount]")).toBe(String(ALL_CENTS));
  });

  it("is closed while checkout is off", async () => {
    t.env.STRIPE_SECRET_KEY = undefined;
    expect((await post("/api/gift/checkout", FORM)).status).toBe(503);
  });
});

describe("webhook: creating the gift", () => {
  it("creates the gift once, emails the buyer a card (no download links), and delivers 'today' right away", async () => {
    const { code, session } = await buyGift();
    expect(gift(code)).toMatchObject({ kind: "all", amount_cents: ALL_CENTS, balance_cents: ALL_CENTS, buyer_email: "buyer@example.com", child_name: "Maya" });
    expect(gift(code).delivered_at).not.toBeNull();

    const [buyer, recipient] = t.mail.sent;
    expect(t.mail.sent).toHaveLength(2);
    expect(buyer.to).toBe("buyer@example.com");
    expect(buyer.text).toContain(code);
    expect(buyer.text).toContain(`/gift/card/${code}`);
    expect(buyer.text + buyer.html).not.toContain("/orders/");

    expect(recipient.to).toBe("sam@example.com");
    expect(recipient.from).toEqual({ name: "Paper Lessons", email: "hello@paperlessons.com" });
    expect(recipient.subject).toBe("Priya sent you a gift from Paper Lessons");
    expect(recipient.text).toContain("Happy birthday, Maya!");
    expect(recipient.text).toContain(`/redeem?code=${code}`);
    expect(recipient.html).toContain("Happy birthday, Maya!<br>Love, Priya");

    // Stripe repeats webhooks: nothing new happens.
    await webhook(session);
    await webhook(session, "checkout.session.async_payment_succeeded");
    expect(count("SELECT COUNT(*) AS n FROM gifts")).toBe(1);
    expect(t.mail.sent).toHaveLength(2);
  });

  it("the buyer's return page gets the code even before the webhook, and the webhook then adds nothing", async () => {
    await post("/api/gift/checkout", { ...FORM, deliverOn: addDays(TODAY, 10) });
    const call = stripe.calls.find((c) => c.path === "/v1/checkout/sessions")!;
    const session = paidSession("cs_test_thanksfirst01", metadataOf(call));
    stripe.sessions[session.id] = session;
    const r = await req(`/api/gift/session/${session.id}`);
    const { code } = (await r.json()) as { code: string };
    expect(code).toMatch(/^\w{4}-\w{4}-\w{4}$/);
    await webhook(session);
    expect(count("SELECT COUNT(*) AS n FROM gifts")).toBe(1);
    expect(t.mail.sent).toHaveLength(1); // buyer only: delivery is in 10 days
  });

  it("ignores unpaid sessions, and bad signatures are refused", async () => {
    await post("/api/gift/checkout", FORM);
    const meta = metadataOf(stripe.calls.find((c) => c.path === "/v1/checkout/sessions")!);
    await webhook(paidSession("cs_test_unpaid000001", meta, { payment_status: "unpaid" }));
    expect(count("SELECT COUNT(*) AS n FROM gifts")).toBe(0);
    const body = JSON.stringify({ type: "checkout.session.completed", data: { object: paidSession("cs_test_forged000001", meta) } });
    const r = await req("/api/stripe/webhook", { method: "POST", headers: { "stripe-signature": await sign(body, "whsec_wrong") }, body });
    expect(r.status).toBe(400);
    expect(count("SELECT COUNT(*) AS n FROM gifts")).toBe(0);
  });

  it("the public gift lookup shows no email addresses or order tokens", async () => {
    const { code } = await buyGift();
    const text = await (await req(`/api/gift/${code.toLowerCase()}`)).text();
    expect(JSON.parse(text)).toMatchObject({ ok: true, code, kind: "all", recipientName: "Sam Lee", buyerName: "Priya", redeemed: false });
    expect(text).not.toMatch(/@example\.com/);
    expect((await req("/api/gift/AAAA-BBBB-CCCC")).status).toBe(404);
  });
});

describe("delivery scheduling (cron)", () => {
  it("emails the recipient on the delivery date, once", async () => {
    const on = addDays(TODAY, 5);
    const { code } = await buyGift({ ...FORM, deliverOn: on });
    expect(t.mail.sent.map((m) => m.to)).toEqual(["buyer@example.com"]);
    expect(gift(code).delivered_at).toBeNull();

    expect(await deliverDueGifts(t.env, addDays(on, -1))).toBe(0);
    expect(await deliverDueGifts(t.env, on)).toBe(1);
    expect(t.mail.sent.at(-1)!.to).toBe("sam@example.com");
    expect(gift(code).delivered_at).not.toBeNull();
    expect(await deliverDueGifts(t.env, addDays(on, 1))).toBe(0);
    expect(t.mail.sent).toHaveLength(2);
  });

  it("tries again the next day if sending failed", async () => {
    const on = addDays(TODAY, 3);
    const { code } = await buyGift({ ...FORM, deliverOn: on });
    t.mail.failNext();
    expect(await deliverDueGifts(t.env, on)).toBe(0);
    expect(gift(code).delivered_at).toBeNull();
    expect(await deliverDueGifts(t.env, addDays(on, 1))).toBe(1);
    expect(gift(code).delivered_at).not.toBeNull();
  });

  it("the Worker's scheduled handler delivers what's due today", async () => {
    await buyGift({ ...FORM, deliverOn: addDays(TODAY, 30) });
    t.db.prepare("UPDATE gifts SET deliver_on = ?").run(TODAY);
    const { default: worker } = await import("../worker/index");
    const waits: Promise<unknown>[] = [];
    await worker.scheduled!({} as ScheduledController, t.env as never, { ...ctx, waitUntil: (p: Promise<unknown>) => waits.push(p) } as never);
    await Promise.all(waits);
    expect(t.mail.sent.at(-1)!.to).toBe("sam@example.com");
  });
});

describe("cart and pay-the-rest math", () => {
  const P = {
    forSale: SLUGS,
    prices: Object.fromEntries(SLUGS.map((s) => [s, { cents: LEVEL_CENTS }])),
    bundles: { two: { cents: TWO_CENTS }, all: { cents: ALL_CENTS } },
    next: Object.fromEntries(SLUGS.slice(0, -1).map((s, i) => [s, SLUGS[i + 1]])),
  };

  it("prices one level, a pack of two in a row, any pick, and every level", () => {
    expect(quoteCart(["chicks"], P)).toEqual({ kind: "level", slugs: ["chicks"], cents: LEVEL_CENTS });
    expect(quoteCart(["ducklings", "chicks"], P)).toEqual({ kind: "two", slugs: ["chicks", "ducklings"], cents: TWO_CENTS });
    expect(quoteCart(["chicks", "bunnies"], P)).toMatchObject({ kind: "pick", cents: 2 * LEVEL_CENTS });
    expect(quoteCart(SLUGS.slice(0, 3), P)).toMatchObject({ kind: "pick", cents: 3 * LEVEL_CENTS });
    // six levels would cost more than every level: they get every level for the every-level price
    expect(quoteCart(SLUGS.slice(0, 6), P)).toEqual({ kind: "all", slugs: SLUGS, cents: ALL_CENTS });
    expect(quoteCart([], P)).toBeNull();
    expect(quoteCart(["unicorns"], P)).toBeNull();
  });

  it("uses the balance up to the total, never leaving less than Stripe's 50-cent minimum to pay", () => {
    expect(planPayment(1900, 5000)).toEqual({ use: 1900, rest: 0 });
    expect(planPayment(2900, 1000)).toEqual({ use: 1000, rest: 1900 });
    expect(planPayment(1900, 1880)).toEqual({ use: 1850, rest: 50 });
    expect(planPayment(1900, 0)).toEqual({ use: 0, rest: 1900 });
    expect(planPayment(30, 10)).toEqual({ use: 0, rest: 30 });
  });
});

describe("spending a gift amount", () => {
  async function creditGift(cents = 5000) {
    const { code } = await buyGift({ ...FORM, kind: "credit", amountCents: cents });
    t.mail.sent.length = 0;
    return code;
  }
  const sessionsMade = () => stripe.calls.filter((c) => c.path === "/v1/checkout/sessions").length;

  it("a $0 order skips Stripe: the balance pays, the order and its 7-day link are made at once", async () => {
    const code = await creditGift(5000);
    const before = sessionsMade();
    const r = await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "Sam@Example.com" });
    const d = (await r.json()) as { ok: boolean; token: string; paid: number };
    expect(d).toMatchObject({ ok: true, paid: 0 });
    expect(sessionsMade()).toBe(before);
    expect(stripe.calls.some((c) => c.path === "/v1/coupons")).toBe(false);
    expect(gift(code).balance_cents).toBe(5000 - LEVEL_CENTS);
    const order = t.db.prepare("SELECT * FROM orders WHERE token = ?").get(d.token) as Record<string, unknown>;
    expect(order).toMatchObject({ levels: "chicks", kind: "level", email: "sam@example.com", amount_cents: 0 });
    expect(String(order.expires_at) > String(order.created_at)).toBe(true);
    expect(t.mail.sent[0].text).toContain(`/orders/${d.token}`);
    expect((await req(`/api/orders/${d.token}`)).status).toBe(200);
    expect(count("SELECT COUNT(*) AS n FROM gift_redemptions WHERE code = ?", code)).toBe(1);
  });

  it("pay the rest: a one-off coupon for the balance, taken only when the webhook says it's paid, once", async () => {
    const code = await creditGift(1900);
    // spend $10 of it first, leaving $9
    t.db.prepare("UPDATE gifts SET balance_cents = 900 WHERE code = ?").run(code);
    const r = await post(`/api/gift/${code}/checkout`, { levels: ["chicks", "ducklings"], email: "sam@example.com" });
    expect(await r.json()).toMatchObject({ ok: true, paid: TWO_CENTS - 900 });

    const coupon = stripe.calls.find((c) => c.path === "/v1/coupons")!;
    expect(coupon.body.get("amount_off")).toBe("900");
    expect(coupon.body.get("duration")).toBe("once");
    expect(coupon.body.get("max_redemptions")).toBe("1");
    const call = stripe.calls.filter((c) => c.path === "/v1/checkout/sessions").at(-1)!;
    expect(call.body.get("discounts[0][coupon]")).toMatch(/^coupon_/);
    expect(call.body.has("allow_promotion_codes")).toBe(false);
    expect(call.body.get("line_items[0][price]")).toBe("price_bundle_two");
    const meta = metadataOf(call);
    expect(meta).toMatchObject({ gift_code: code, gift_cents: "900", kind: "two", levels: "chicks,ducklings" });

    // Not paid yet: the balance is still there, but held (another tab can't spend it).
    expect(gift(code).balance_cents).toBe(900);
    expect(((await (await req(`/api/gift/${code}`)).json()) as { balanceCents: number }).balanceCents).toBe(0);
    expect((await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "sam@example.com" })).status).toBe(409);

    // Tax may be added on top: the balance taken is our own number, not amount_total.
    const session = paidSession("cs_test_paytherest01", meta, { amount_total: 2150, customer_details: { email: "sam@example.com" } });
    await webhook(session);
    expect(gift(code).balance_cents).toBe(0);
    expect(count("SELECT COUNT(*) AS n FROM gift_holds")).toBe(0);
    expect(t.db.prepare("SELECT levels, kind FROM orders WHERE session_id = ?").get(session.id)).toEqual({ levels: "chicks,ducklings", kind: "two" });

    await webhook(session);
    await webhook(session, "checkout.session.async_payment_succeeded");
    expect(count("SELECT COUNT(*) AS n FROM gift_redemptions WHERE order_session = ?", session.id)).toBe(1);
    expect(count("SELECT COUNT(*) AS n FROM orders WHERE session_id = ?", session.id)).toBe(1);
  });

  it("leaves what wasn't used on the code (50-cent minimum), and webhook replays don't touch it", async () => {
    const code = await creditGift(1900);
    t.db.prepare("UPDATE gifts SET balance_cents = 1880 WHERE code = ?").run(code);
    expect(await (await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "sam@example.com" })).json()).toMatchObject({ paid: 50 });
    const meta = metadataOf(stripe.calls.filter((c) => c.path === "/v1/checkout/sessions").at(-1)!);
    expect(meta.gift_cents).toBe("1850");
    const session = paidSession("cs_test_fiftycents01", meta);
    for (let i = 0; i < 3; i++) await webhook(session);
    expect(gift(code).balance_cents).toBe(30);
    expect(((await (await req(`/api/gift/${code}`)).json()) as { balanceCents: number }).balanceCents).toBe(30);
  });

  it("the thanks page can land first: the balance is still taken exactly once", async () => {
    const code = await creditGift(1000);
    await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "sam@example.com" });
    const meta = metadataOf(stripe.calls.filter((c) => c.path === "/v1/checkout/sessions").at(-1)!);
    const session = paidSession("cs_test_thanksorder1", meta);
    stripe.sessions[session.id] = session;
    expect(await (await req(`/api/orders/session/${session.id}`)).json()).toMatchObject({ ok: true });
    expect(gift(code).balance_cents).toBe(0);
    await webhook(session);
    expect(gift(code).balance_cents).toBe(0);
    expect(count("SELECT COUNT(*) AS n FROM gift_redemptions")).toBe(1);
  });

  it("an abandoned checkout leaves the balance alone, and its hold lapses", async () => {
    const code = await creditGift(1000);
    await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "sam@example.com" });
    t.db.prepare("UPDATE gift_holds SET expires_at = datetime('now', '-1 minute')").run();
    expect(gift(code).balance_cents).toBe(1000);
    expect(((await (await req(`/api/gift/${code}`)).json()) as { balanceCents: number }).balanceCents).toBe(1000);
  });

  it("a gift used up can't pay again", async () => {
    const code = await creditGift(1900);
    await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "sam@example.com" });
    const r = await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "sam@example.com" });
    expect(r.status).toBe(409);
  });

  it("checks the cart and the email", async () => {
    const code = await creditGift();
    expect((await post(`/api/gift/${code}/checkout`, { levels: [], email: "sam@example.com" })).status).toBe(400);
    expect((await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "" })).status).toBe(400);
    expect((await post(`/api/gift/${code}/redeem`, { email: "sam@example.com" })).status).toBe(400); // that's for every-level gifts
  });
});

describe("every-level gift", () => {
  it("one click makes one order for all 13 levels, and only once", async () => {
    const { code } = await buyGift();
    t.mail.sent.length = 0;
    const r = await post(`/api/gift/${code}/redeem`, { email: "sam@example.com" });
    const d = (await r.json()) as { ok: boolean; token: string };
    expect(d.ok).toBe(true);
    const order = t.db.prepare("SELECT levels, kind, email FROM orders WHERE token = ?").get(d.token) as { levels: string; kind: string };
    expect(order).toEqual({ levels: SLUGS.join(","), kind: "all", email: "sam@example.com" });
    expect(SLUGS).toHaveLength(13);
    expect(gift(code).balance_cents).toBe(0);
    expect(t.mail.sent).toHaveLength(1);
    expect(t.mail.sent[0].subject).toBe("Your All 13 levels pages are ready to download");
    expect(stripe.calls.filter((c) => c.method === "POST")).toHaveLength(1); // only the gift purchase itself

    const again = await post(`/api/gift/${code}/redeem`, { email: "someone@example.com" });
    expect(again.status).toBe(409);
    expect(await again.json()).toMatchObject({ redeemed: true });
    expect(count("SELECT COUNT(*) AS n FROM orders")).toBe(1);
    expect(((await (await req(`/api/gift/${code}`)).json()) as { redeemed: boolean }).redeemed).toBe(true);
    expect((await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "sam@example.com" })).status).toBe(400);
  });

  it("two clicks at the same moment still make one order", async () => {
    const { code } = await buyGift();
    const results = await Promise.all([1, 2, 3].map(() => post(`/api/gift/${code}/redeem`, { email: "sam@example.com" })));
    expect(results.map((r) => r.status).sort()).toEqual([200, 409, 409]);
    expect(count("SELECT COUNT(*) AS n FROM orders")).toBe(1);
    expect(count("SELECT COUNT(*) AS n FROM gift_redemptions")).toBe(1);
  });

  it("'Resend my files' re-sends a live link (not too often) and never extends it", async () => {
    const { code } = await buyGift();
    expect((await post(`/api/gift/${code}/resend`, {})).status).toBe(410); // nothing opened yet
    const { token } = (await (await post(`/api/gift/${code}/redeem`, { email: "sam@example.com" })).json()) as { token: string };
    const expires = (t.db.prepare("SELECT expires_at FROM orders").get() as { expires_at: string }).expires_at;
    t.mail.sent.length = 0;
    expect(await (await post(`/api/gift/${code}/resend`, {})).json()).toEqual({ ok: true, sent: 1 });
    expect(t.mail.sent[0].to).toBe("sam@example.com");
    expect(t.mail.sent[0].text).toContain(`/orders/${token}`);
    expect((await post(`/api/gift/${code}/resend`, {})).status).toBe(429);
    expect((t.db.prepare("SELECT expires_at FROM orders").get() as { expires_at: string }).expires_at).toBe(expires);

    t.db.prepare("UPDATE orders SET expires_at = datetime('now', '-1 minute')").run();
    t.db.prepare("UPDATE gifts SET resent_at = NULL").run();
    expect((await post(`/api/gift/${code}/resend`, {})).status).toBe(410);
  });
});

describe("existing shop", () => {
  it("still sells a level with promotion codes allowed", async () => {
    const r = await post("/api/checkout", { level: "chicks" });
    expect(await r.json()).toMatchObject({ ok: true });
    const call = stripe.calls.find((c) => c.path === "/v1/checkout/sessions")!;
    expect(call.body.get("allow_promotion_codes")).toBe("true");
    expect(call.body.get("line_items[0][price]")).toBe("price_level_chicks");
  });

  it("the catalog says whether gifts are open and what every level costs", async () => {
    const d = (await (await req("/api/catalog")).json()) as { gifts: { open: boolean; allCents: number } };
    expect(d.gifts).toMatchObject({ open: true, allCents: ALL_CENTS });
  });
});

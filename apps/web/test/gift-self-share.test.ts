// "I'll give it myself" gifts (no recipient email, no date), every name optional, and migration 0007.
import { DatabaseSync } from "node:sqlite";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ladder from "../src/data/ladder.json";
import { resetPriceCache } from "../worker/catalog";
import { addDays, deliverDueGifts, deliverGift, todayUTC, validateGift } from "../worker/gift";
import { app } from "../worker/index";
import { ALL_CENTS, ctx, makeEnv, migrate, sign, stubStripe, type StripeCall } from "./env";

const TODAY = todayUTC();
let t: ReturnType<typeof makeEnv>;
let stripe: ReturnType<typeof stubStripe>;

beforeEach(() => {
  resetPriceCache();
  t = makeEnv(ladder.map((l) => l.slug));
  stripe = stubStripe();
});
afterEach(() => vi.unstubAllGlobals());

const req = (path: string, init?: RequestInit) => app.request(`https://paperlessons.test${path}`, init, t.env, ctx);
const post = (path: string, body: unknown) => req(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
const metadataOf = (call: StripeCall): Record<string, string> =>
  Object.fromEntries([...call.body.entries()].filter(([k]) => /^metadata\[\w+\]$/.test(k)).map(([k, v]) => [k.slice(9, -1), v]));
const sessionCalls = () => stripe.calls.filter((c) => c.path === "/v1/checkout/sessions");
const paidSession = (id: string, metadata: Record<string, string>, extra: Record<string, unknown> = {}) => ({
  id, url: null, status: "complete", payment_status: "paid", amount_total: 0, currency: "usd", customer_details: { email: "Buyer@Example.com" }, metadata, ...extra,
});
async function webhook(session: unknown) {
  const body = JSON.stringify({ type: "checkout.session.completed", data: { object: session } });
  return req("/api/stripe/webhook", { method: "POST", headers: { "stripe-signature": await sign(body) }, body });
}
let n = 0;
async function buyGift(form: Record<string, unknown>) {
  expect((await post("/api/gift/checkout", form)).status).toBe(200);
  const id = `cs_test_self${String(++n).padStart(8, "0")}`;
  expect((await webhook(paidSession(id, metadataOf(sessionCalls().at(-1)!)))).status).toBe(200);
  return (t.db.prepare("SELECT code FROM gifts WHERE session_id = ?").get(id) as { code: string }).code;
}
const gift = (code: string) => t.db.prepare("SELECT * FROM gifts WHERE code = ?").get(code) as Record<string, unknown>;
const noJunk = (s: string) => expect(s).not.toMatch(/\b(null|undefined)\b/);

const SELF = { kind: "all", delivery: "self", buyerName: "Priya", recipientName: "Sam Lee", childName: "Maya", message: "Happy birthday, Maya!" };
const EMPTY = { kind: "credit", amountCents: 2900, delivery: "self" };

describe("validation", () => {
  const v = (body: Record<string, unknown>) => validateGift(body, TODAY, ALL_CENTS);

  it("self-share needs no recipient email and no date, and drops any left over from switching modes", () => {
    expect(v(SELF)).toMatchObject({ ok: true, gift: { delivery: "self", recipientEmail: null, deliverOn: null, recipientName: "Sam Lee" } });
    expect(v({ ...SELF, recipientEmail: "not an email", deliverOn: "nope" })).toMatchObject({ ok: true, gift: { recipientEmail: null, deliverOn: null } });
  });

  it("works with nothing personal at all", () => {
    expect(v(EMPTY)).toEqual({
      ok: true,
      gift: { kind: "credit", amountCents: 2900, delivery: "self", buyerName: null, recipientName: null, recipientEmail: null, childName: null, message: null, deliverOn: null },
    });
  });

  it("email mode still needs the email and a date (names optional); a form with no mode is an emailed one", () => {
    expect(v({ ...SELF, delivery: "email" })).toMatchObject({ ok: false, field: "recipientEmail" });
    expect(v({ ...SELF, delivery: "email", recipientEmail: "sam@example.com" })).toMatchObject({ ok: false, field: "deliverOn" });
    expect(v({ ...EMPTY, delivery: "email", recipientEmail: "sam@example.com", deliverOn: TODAY })).toMatchObject({
      ok: true,
      gift: { delivery: "email", buyerName: null, recipientName: null, recipientEmail: "sam@example.com", deliverOn: TODAY },
    });
    const { delivery: _, ...noMode } = SELF;
    expect(v(noMode)).toMatchObject({ ok: false, field: "recipientEmail" });
    expect(v({ ...SELF, delivery: "pigeon" })).toMatchObject({ ok: false, field: "delivery" });
  });

  it("the checkout carries no recipient email or date (that is the mode) and no empty fields", async () => {
    await post("/api/gift/checkout", EMPTY);
    const call = sessionCalls()[0];
    expect(metadataOf(call)).toEqual({ gift: "buy", gift_kind: "credit", gift_cents: "2900" });
    expect(call.body.get("line_items[0][price_data][product_data][description]")).toBe("$29 to spend on any level. Code never expires.");
    await post("/api/gift/checkout", SELF);
    expect(sessionCalls()[1].body.get("line_items[0][price_data][product_data][description]")).toMatch(/^For Sam Lee: all 13 levels/);
  });
});

describe("webhook, cron and emails", () => {
  it("creates a self-share gift with no delivery: only the buyer is emailed, with the code, card link and a message to forward", async () => {
    const code = await buyGift(SELF);
    expect(gift(code)).toMatchObject({ recipient_email: null, deliver_on: null, delivered_at: null, recipient_name: "Sam Lee", buyer_email: "buyer@example.com" });
    expect(t.mail.sent).toHaveLength(1);
    const [buyer] = t.mail.sent;
    expect(buyer.to).toBe("buyer@example.com");
    expect(buyer.subject).toBe("Your gift for Sam Lee is ready to share");
    const card = `https://paperlessons.test/gift/card/${code}`;
    for (const body of [buyer.text, buyer.html]) {
      expect(body).toContain(code);
      expect(body).toContain(card);
      expect(body).toContain("I got you and Maya a little gift: every level of Paper Lessons");
      expect(body).toContain(`Open it at ${card} (gift code ${code})`);
      expect(body).not.toContain("/orders/");
    }
    expect(buyer.text).toContain("- Priya");
    expect(buyer.text).not.toContain("We'll email");
    noJunk(buyer.text + buyer.html);
    expect(await (await req(`/api/gift/${code}`)).json()).toMatchObject({ delivery: "self", deliverOn: null, delivered: false });
  });

  it("the cron and deliverGift skip it, on any day", async () => {
    const code = await buyGift(SELF);
    expect(await deliverDueGifts(t.env, TODAY)).toBe(0);
    expect(await deliverDueGifts(t.env, addDays(TODAY, 400))).toBe(0);
    expect(await deliverGift(t.env, code)).toBe(false);
    expect(gift(code).delivered_at).toBeNull();
    expect(t.mail.sent).toHaveLength(1);
  });

  it("an all-empty gift works everywhere: row, card data, buyer email, spending it", async () => {
    const code = await buyGift(EMPTY);
    expect(gift(code)).toMatchObject({ buyer_name: null, recipient_name: null, child_name: null, message: null, recipient_email: null, deliver_on: null });
    expect(await (await req(`/api/gift/${code}`)).json()).toMatchObject({
      ok: true, code, kind: "credit", amountCents: 2900, buyerName: null, recipientName: null, childName: null, message: null, delivery: "self",
    });
    const [buyer] = t.mail.sent;
    expect(buyer.subject).toBe("Your gift is ready to share");
    expect(buyer.text).toContain("Thank you! You gave a gift of $29 to spend on any level ($29).");
    expect(buyer.text).toContain("I got you a little gift: $29 to spend on Paper Lessons");
    expect(buyer.text).toMatch(/so open it whenever you're ready\.$/m); // no "- name" signature
    noJunk(buyer.text + buyer.html);
    expect(await (await post(`/api/gift/${code}/checkout`, { levels: ["chicks"], email: "sam@example.com" })).json()).toMatchObject({ ok: true, paid: 0 });
  });

  it("an emailed gift with no names uses friendly fallbacks", async () => {
    const code = await buyGift({ kind: "all", delivery: "email", recipientEmail: "sam@example.com", deliverOn: TODAY });
    const [buyer, recipient] = t.mail.sent;
    expect(buyer.subject).toBe("Your gift is ready");
    expect(buyer.text).toContain("We've just emailed them");
    expect(buyer.text).toContain(`/gift/card/${code}`);
    expect(recipient.to).toBe("sam@example.com");
    expect(recipient.subject).toBe("You've been sent a gift from Paper Lessons");
    expect(recipient.text.startsWith("Hi there,")).toBe(true);
    expect(recipient.text).toContain("Here's a gift for you: every level");
    noJunk(buyer.text + buyer.html + recipient.text + recipient.html);
  });

  it("an emailed gift for later: the buyer email gives the date and the share kit too", async () => {
    const on = addDays(TODAY, 5);
    const code = await buyGift({ ...SELF, delivery: "email", recipientEmail: "sam@example.com", deliverOn: on });
    expect(t.mail.sent).toHaveLength(1);
    const [buyer] = t.mail.sent;
    expect(buyer.text).toContain("We'll email Sam Lee your message");
    expect(buyer.text).toContain("Ready to forward:");
    expect(buyer.text).toContain(`/gift/card/${code}`);
    expect(await (await req(`/api/gift/${code}`)).json()).toMatchObject({ delivery: "email", deliverOn: on, delivered: false });
    expect(await deliverDueGifts(t.env, on)).toBe(1);
  });

  it("refuses metadata with only one of recipient email and date", async () => {
    expect((await webhook(paidSession("cs_test_halfmeta0001", { gift: "buy", gift_kind: "all", gift_cents: String(ALL_CENTS), deliver_on: TODAY }))).status).toBe(200);
    expect(t.db.prepare("SELECT COUNT(*) AS n FROM gifts").get()).toEqual({ n: 0 });
  });

  it("falls back to customer_email for the buyer's address", async () => {
    await post("/api/gift/checkout", EMPTY);
    await webhook(paidSession("cs_test_custemail001", metadataOf(sessionCalls()[0]), { customer_details: { email: null }, customer_email: "Other@Example.com" }));
    expect(t.mail.sent.map((m) => m.to)).toEqual(["other@example.com"]);
  });
});

describe("migration 0007", () => {
  it("rebuilds gifts with nullable delivery and names, keeping every row, id and the due index", () => {
    const db = new DatabaseSync(":memory:");
    migrate(db, { to: "0006" });
    const ins = db.prepare(
      `INSERT INTO gifts (code, session_id, kind, amount_cents, balance_cents, currency, buyer_name, buyer_email, recipient_name, recipient_email,
         child_name, message, deliver_on, delivered_at, resent_at, created_at) VALUES (?, ?, ?, ?, ?, 'usd', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    );
    ins.run("AAAA-BBBB-CCCC", "cs_1", "all", 9900, 0, "Priya", "p@example.com", "Sam", "sam@example.com", "Maya", "Hi!\nLove", "2026-11-01", "2026-11-01 14:00:00", "2026-11-02 09:00:00", "2026-10-30 10:00:00");
    ins.run("DDDD-EEEE-FFFF", "cs_2", "credit", 5000, 3100, "Ana", null, "Lee", "lee@example.com", null, null, "2026-12-24", null, null, "2026-10-31 10:00:00");
    db.exec("DELETE FROM gifts WHERE code = 'AAAA-BBBB-CCCC'"); // a gap in the ids, which must survive
    ins.run("AAAA-BBBB-CCCC", "cs_1", "all", 9900, 0, "Priya", "p@example.com", "Sam", "sam@example.com", "Maya", "Hi!\nLove", "2026-11-01", "2026-11-01 14:00:00", "2026-11-02 09:00:00", "2026-10-30 10:00:00");
    const before = db.prepare("SELECT * FROM gifts ORDER BY id").all();
    expect(before.map((r) => r.id)).toEqual([2, 3]);
    const seq = (db.prepare("SELECT seq FROM sqlite_sequence WHERE name = 'gifts'").get() as { seq: number }).seq;

    migrate(db, { from: "0007" });
    expect(db.prepare("SELECT * FROM gifts ORDER BY id").all()).toEqual(before);
    expect(db.prepare("SELECT sql FROM sqlite_master WHERE type = 'index' AND name = 'gifts_due'").get()).toMatchObject({ sql: expect.stringContaining("deliver_on IS NOT NULL") });
    expect(db.prepare("SELECT name FROM sqlite_master WHERE name = 'gifts_new'").get()).toBeUndefined();
    const cols = Object.fromEntries((db.prepare("PRAGMA table_info(gifts)").all() as { name: string; notnull: number }[]).map((c) => [c.name, c.notnull]));
    expect(cols).toMatchObject({ recipient_email: 0, deliver_on: 0, buyer_name: 0, recipient_name: 0, code: 1, session_id: 1, kind: 1, amount_cents: 1 });

    // a self-share row goes in, ids carry on past the old ones (even deleted ones), half a delivery is refused
    const r = db.prepare("INSERT INTO gifts (code, session_id, kind, amount_cents, balance_cents) VALUES ('GGGG-HHHH-JJJJ', 'cs_3', 'credit', 2900, 2900)").run();
    expect(Number(r.lastInsertRowid)).toBe(seq + 1);
    expect(() =>
      db.prepare("INSERT INTO gifts (code, session_id, kind, amount_cents, balance_cents, deliver_on) VALUES ('KKKK-MMMM-NNNN', 'cs_4', 'all', 9900, 9900, '2026-12-01')").run(),
    ).toThrow(/CHECK/);
    expect(() => db.prepare("INSERT INTO gifts (code, session_id, kind, amount_cents, balance_cents) VALUES ('AAAA-BBBB-CCCC', 'cs_5', 'all', 9900, 9900)").run()).toThrow(/UNIQUE/);
  });
});

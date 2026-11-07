// The gift card PDF (worker/giftCard.ts), its route, the buyer's email with the PDF attached, older checkouts and
// rows from when we emailed gifts on a chosen day, and migration 0007.
import { DatabaseSync } from "node:sqlite";
import { getDocument } from "pdfjs-dist/legacy/build/pdf.mjs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ladder from "../src/data/ladder.json";
import { resetPriceCache } from "../worker/catalog";
import { LAYOUT, NOTE, cardDocument, giftCardPdf, layoutCard, type CardGift } from "../worker/giftCard";
import { app } from "../worker/index";
import { ALL_CENTS, ctx, makeEnv, migrate, sign, stubStripe, type StripeCall } from "./env";

/** Every piece of text in a PDF, page by page, whitespace squeezed (pdf.js splits letter-spaced runs). */
async function pdfText(bytes: Uint8Array) {
  const doc = await getDocument({ data: bytes.slice(), disableFontFace: true, useSystemFonts: false, isEvalSupported: false }).promise;
  const pages: { text: string; width: number; height: number }[] = [];
  for (let i = 1; i <= doc.numPages; i++) {
    const page = await doc.getPage(i);
    const [, , width, height] = page.view;
    const content = await page.getTextContent();
    const text = content.items.map((it) => ("str" in it ? it.str : "")).join(" ").replace(/\s+/g, " ");
    pages.push({ text, width, height });
  }
  await doc.destroy();
  return pages;
}
const squeeze = (s: string) => s.replace(/\s+/g, "");

const NORMAL: CardGift = {
  kind: "all",
  amountCents: ALL_CENTS,
  code: "HAPY-BDAY-MAYA",
  childName: "Maya",
  buyerName: "Priya",
  message: "Happy birthday, Maya! A little something for rainy afternoons.",
};
const EMPTY: CardGift = { kind: "credit", amountCents: 2900, code: "ABCD-EFGH-JKMN", childName: null, buyerName: null, message: null };
const MSG300 = (
  "Happy birthday! We hope these pages bring lots of quiet mornings, giggles over counting games and proud moments reading the first words aloud. " +
  "Take it slow, a few pages a day, and keep the ones you love on the fridge. We can't wait to hear what you learn next. Lots of love from all of us!!!"
).slice(0, 300);
const LONGEST: CardGift = { kind: "credit", amountCents: 25000, code: "WWWW-WWWW-WWWW", childName: "W".repeat(30), buyerName: "W".repeat(60), message: MSG300 };

describe("giftCardPdf", () => {
  it("is one US Letter page with the names, the message, the gift and the code", async () => {
    const [page, ...more] = await pdfText(await giftCardPdf(NORMAL));
    expect(more).toHaveLength(0);
    expect([page.width, page.height]).toEqual([612, 792]);
    for (const s of ["a gift for", "Maya", "from Priya", "Happy birthday, Maya!", "rainy afternoons.", "Every level, ages 3 to 12", "paperlessons.com/redeem"]) {
      expect(page.text).toContain(s);
    }
    expect(squeeze(page.text)).toContain("HAPY-BDAY-MAYA");
    expect(squeeze(page.text)).toContain("YOURGIFTCODE");
    expect(page.text).not.toContain(NOTE.slice(0, 20));
  });

  it("is deterministic: the same gift gives the same bytes", async () => {
    const [a, b] = [await giftCardPdf(NORMAL), await giftCardPdf(NORMAL)];
    expect(Buffer.from(a).equals(Buffer.from(b))).toBe(true);
    expect(Buffer.from(a).equals(Buffer.from(await giftCardPdf({ ...NORMAL, code: "HAPY-BDAY-MAYB" })))).toBe(false);
  });

  it("with nothing personal: a gift for you, our little note, no from line", async () => {
    const [page] = await pdfText(await giftCardPdf(EMPTY));
    expect(page.text).toContain("a gift for");
    expect(page.text).toMatch(/ you \$29 /); // the name line, then the gift line
    expect(page.text).toContain("little lessons, one page at a time");
    expect(page.text).toContain("$29 to spend on any level");
    expect(page.text.replace("from first words", "")).not.toMatch(/\bfrom\b/);
    expect(squeeze(page.text)).toContain("ABCD-EFGH-JKMN");
  });

  it("keeps every letter of names with ligature pairs (fi, ff, fl)", async () => {
    const [page] = await pdfText(await giftCardPdf({ ...NORMAL, childName: "Raffi", buyerName: "Effie Flynn", message: "Fifty fluffy office waffles" }));
    expect(page.text).toContain("Raffi");
    expect(page.text).toContain("from Effie Flynn");
    expect(page.text).toContain("Fifty fluffy office waffles");
  });

  it("leaves out characters the card fonts can't draw instead of failing; accented Latin letters stay", async () => {
    const [page] = await pdfText(await giftCardPdf({ ...NORMAL, childName: "Zoë", buyerName: "Łucja 🎁", message: "Happy birthday! 🎂🎉 Love, 美咲" }));
    expect(page.text).toContain("Zoë");
    expect(page.text).toContain("from Łucja");
    expect(page.text).toContain("Happy birthday!");
    expect(page.text).toContain("Love,");
    const [cjk] = await pdfText(await giftCardPdf({ ...EMPTY, childName: "美咲" }));
    expect(cjk.text).toMatch(/ you \$29 /);
  });

  it("the longest names and a 300-character message fit on the page", async () => {
    const bytes = await giftCardPdf(LONGEST);
    const [page, ...more] = await pdfText(bytes);
    expect(more).toHaveLength(0);
    expect(squeeze(page.text)).toContain("W".repeat(30)); // two lines, every letter
    expect(page.text).toContain("from WWWW");
    expect(squeeze(page.text)).toContain(squeeze(MSG300)); // the whole message, nothing cut
    expect(squeeze(page.text)).toContain("WWWW-WWWW-WWWW");
  });
});

describe("layoutCard: nothing overflows", () => {
  const cases: [string, CardGift][] = [
    ["normal", NORMAL],
    ["empty", EMPTY],
    ["longest", LONGEST],
    ["300 letters, no spaces", { ...LONGEST, message: "W".repeat(300) }],
    ["150 short lines", { ...LONGEST, message: "a\n".repeat(150).trim() }],
    ["long name, no message", { ...EMPTY, childName: "W".repeat(30), buyerName: "W".repeat(60) }],
  ];
  it.each(cases)("%s", async (_, g) => {
    const { fonts } = await cardDocument();
    const card = layoutCard(g, fonts);
    expect(card.topEnd).toBeLessThanOrEqual(LAYOUT.topLimit);
    for (const l of card.lines) {
      expect(l.x).toBeGreaterThanOrEqual(LAYOUT.left);
      expect(l.x + l.width).toBeLessThanOrEqual(LAYOUT.left + LAYOUT.width + 0.01);
      expect(l.size).toBeGreaterThanOrEqual(11);
    }
    if (card.box) expect(card.box.x + card.box.width).toBeLessThanOrEqual(LAYOUT.left + LAYOUT.width);
    // The top part (name, from, message) stays above the gift line; the code sits inside its box.
    const code = card.lines.at(-1)!;
    expect(code.text).toBe(g.code);
    expect(code.top).toBeGreaterThan(LAYOUT.codeBox.top);
    expect(code.top + code.lineHeight).toBeLessThan(LAYOUT.codeBox.bottom);
    for (const l of card.lines.filter((l) => l.top < LAYOUT.whatTop)) expect(l.top + l.lineHeight).toBeLessThanOrEqual(LAYOUT.topLimit + 0.01);
  });

  it("a short message keeps the big type; 300 characters wrap smaller but whole", async () => {
    const { fonts } = await cardDocument();
    const short = layoutCard(NORMAL, fonts).lines.filter((l) => l.inBox);
    expect(short[0].size).toBe(20.8);
    const long = layoutCard(LONGEST, fonts).lines.filter((l) => l.inBox);
    expect(long.map((l) => l.text).join(" ")).toBe(MSG300);
    const lines = layoutCard({ ...LONGEST, message: "a\n".repeat(150).trim() }, fonts).lines.filter((l) => l.inBox);
    expect(lines.at(-1)!.text.endsWith("…")).toBe(true); // too many lines: cut, never over the edge
  });
});

// ---------------------------------------------------------------------------------------------------------
// Through the Worker

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
  const id = `cs_test_card${String(++n).padStart(8, "0")}`;
  expect((await webhook(paidSession(id, metadataOf(sessionCalls().at(-1)!)))).status).toBe(200);
  return (t.db.prepare("SELECT code FROM gifts WHERE session_id = ?").get(id) as { code: string }).code;
}
const gift = (code: string) => t.db.prepare("SELECT * FROM gifts WHERE code = ?").get(code) as Record<string, unknown>;
const noJunk = (s: string) => expect(s).not.toMatch(/\b(null|undefined)\b/);

describe("the buyer's email", () => {
  it("is one email with the gift card PDF attached, the code and where to open it", async () => {
    const code = await buyGift({ kind: "all", childName: "Maya", message: "Happy birthday!", buyerName: "Priya" });
    expect(t.mail.sent).toHaveLength(1);
    const [m] = t.mail.sent;
    expect(m.attachments).toHaveLength(1);
    const [a] = m.attachments!;
    expect(a).toMatchObject({ disposition: "attachment", filename: `paper-lessons-gift-card-${code}.pdf`, type: "application/pdf" });
    expect(Buffer.from(a.content.slice(0, 5)).toString()).toBe("%PDF-");
    const [page] = await pdfText(a.content);
    expect(squeeze(page.text)).toContain(code);
    expect(page.text).toContain("from Priya");
    expect(m.text).toContain(`Gift code: ${code}`);
    expect(m.text).toContain("paperlessons.com/redeem");
    noJunk(m.text + m.html);
  });

  it("with nothing personal it still reads naturally", async () => {
    const code = await buyGift({ kind: "credit", amountCents: 2900 });
    const [m] = t.mail.sent;
    expect(m.subject).toBe("Your gift card is ready");
    expect(m.text).toContain("Thank you! You gave a gift of $29 to spend on any level ($29).");
    expect(m.text).toContain(code);
    noJunk(m.text + m.html);
  });

  it("falls back to customer_email for the buyer's address", async () => {
    await post("/api/gift/checkout", { kind: "credit", amountCents: 2900 });
    await webhook(paidSession("cs_test_custemail001", metadataOf(sessionCalls()[0]), { customer_details: { email: null }, customer_email: "Other@Example.com" }));
    expect(t.mail.sent.map((m) => m.to)).toEqual(["other@example.com"]);
  });
});

describe("GET /api/gift/:code/card.pdf", () => {
  it("downloads the card, private and never cached by anyone else", async () => {
    const code = await buyGift({ kind: "all", childName: "Maya" });
    const r = await req(`/api/gift/${code.toLowerCase()}/card.pdf`);
    expect(r.status).toBe(200);
    expect(r.headers.get("content-type")).toBe("application/pdf");
    expect(r.headers.get("cache-control")).toBe("private, no-store");
    expect(r.headers.get("content-disposition")).toBe(`attachment; filename="paper-lessons-gift-card-${code}.pdf"`);
    const bytes = new Uint8Array(await r.arrayBuffer());
    expect(Buffer.from(bytes).equals(Buffer.from(t.mail.sent[0].attachments![0].content))).toBe(true); // the same file as the email
  });

  it("is a 404 for a code that doesn't exist or can't be one", async () => {
    expect((await req("/api/gift/AAAA-BBBB-CCCC/card.pdf")).status).toBe(404);
    expect((await req("/api/gift/nope/card.pdf")).status).toBe(404);
  });
});

describe("older checkouts and gifts", () => {
  it("a checkout started on the old form is recorded without the recipient's email or a date, and nobody else is emailed", async () => {
    const meta = { gift: "buy", gift_kind: "all", gift_cents: String(ALL_CENTS), buyer_name: "Priya", recipient_name: "Sam", recipient_email: "sam@example.com", deliver_on: "2026-11-01", message: "Hi!" };
    expect((await webhook(paidSession("cs_test_oldform00001", meta))).status).toBe(200);
    const row = t.db.prepare("SELECT * FROM gifts WHERE session_id = 'cs_test_oldform00001'").get() as Record<string, unknown>;
    expect(row).toMatchObject({ recipient_email: null, deliver_on: null, delivered_at: null, child_name: "Sam", buyer_name: "Priya" });
    expect(t.mail.sent.map((m) => m.to)).toEqual(["buyer@example.com"]);
  });

  it("a gift stored with a grown-up's name and no child's name shows that name on the card", async () => {
    t.db.prepare(
      `INSERT INTO gifts (code, session_id, kind, amount_cents, balance_cents, recipient_name, recipient_email, deliver_on, delivered_at)
       VALUES ('QRST-UVWX-YZ23', 'cs_old', 'credit', 5000, 5000, 'Sam Lee', 'sam@example.com', '2026-11-01', '2026-11-01 14:00:00')`,
    ).run();
    const [page] = await pdfText(new Uint8Array(await (await req("/api/gift/QRST-UVWX-YZ23/card.pdf")).arrayBuffer()));
    expect(page.text).toContain("Sam Lee");
    expect(await (await req("/api/gift/QRST-UVWX-YZ23")).json()).toMatchObject({ recipientName: "Sam Lee", childName: null });
    expect(gift("QRST-UVWX-YZ23").recipient_email).toBe("sam@example.com"); // untouched, never used
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

    // a gift with no delivery goes in, ids carry on past the old ones (even deleted ones), half a delivery is refused
    const r = db.prepare("INSERT INTO gifts (code, session_id, kind, amount_cents, balance_cents) VALUES ('GGGG-HHHH-JJJJ', 'cs_3', 'credit', 2900, 2900)").run();
    expect(Number(r.lastInsertRowid)).toBe(seq + 1);
    expect(() =>
      db.prepare("INSERT INTO gifts (code, session_id, kind, amount_cents, balance_cents, deliver_on) VALUES ('KKKK-MMMM-NNNN', 'cs_4', 'all', 9900, 9900, '2026-12-01')").run(),
    ).toThrow(/CHECK/);
    expect(() => db.prepare("INSERT INTO gifts (code, session_id, kind, amount_cents, balance_cents) VALUES ('AAAA-BBBB-CCCC', 'cs_5', 'all', 9900, 9900)").run()).toThrow(/UNIQUE/);
  });
});

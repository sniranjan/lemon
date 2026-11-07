// If the gift card PDF can't be made, the buyer still gets their receipt and code (with a link to the card).
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import ladder from "../src/data/ladder.json";
import { resetPriceCache } from "../worker/catalog";
import { app } from "../worker/index";
import { ctx, makeEnv, sign, stubStripe } from "./env";

vi.mock("../worker/giftCard", async (load) => ({
  ...(await load<typeof import("../worker/giftCard")>()),
  giftCardPdf: async () => {
    throw new Error("no card today");
  },
}));

let t: ReturnType<typeof makeEnv>;
beforeEach(() => {
  resetPriceCache();
  t = makeEnv(ladder.map((l) => l.slug));
  stubStripe();
  vi.spyOn(console, "error").mockImplementation(() => {});
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

it("emails the receipt without the attachment, with the card link instead", async () => {
  const session = {
    id: "cs_test_nocard000001", url: null, status: "complete", payment_status: "paid", amount_total: 2900, currency: "usd",
    customer_details: { email: "buyer@example.com" }, metadata: { gift: "buy", gift_kind: "credit", gift_cents: "2900", child_name: "Maya" },
  };
  const body = JSON.stringify({ type: "checkout.session.completed", data: { object: session } });
  const r = await app.request("https://paperlessons.test/api/stripe/webhook", { method: "POST", headers: { "stripe-signature": await sign(body) }, body }, t.env, ctx);
  expect(r.status).toBe(200);
  const { code } = t.db.prepare("SELECT code FROM gifts").get() as { code: string };
  expect(t.mail.sent).toHaveLength(1);
  const [m] = t.mail.sent;
  expect(m.attachments).toBeUndefined();
  expect(m.text).toContain(`https://paperlessons.test/api/gift/${code}/card.pdf`);
  expect(m.html).toContain("Download the gift card (PDF)");
  expect(m.text).toContain(`Gift code: ${code}`);
});

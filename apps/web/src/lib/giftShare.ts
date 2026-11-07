// Gift wording shared by the Worker (emails) and the site (share page, gift card), so the buyer's email and the
// share page offer exactly the same ready-to-paste message. Every name is optional: a gift bought with no names
// at all still reads naturally ("a gift for you", no "from" line).

export const dollars = (cents: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: cents % 100 ? 2 : 0 }).format(cents / 100);

/** "every level, ages 3 to 12" / "$50 to spend on any level". */
export const giftWhat = (kind: string, amountCents: number) =>
  kind === "all" ? "every level, ages 3 to 12" : `${dollars(amountCents)} to spend on any level`;

/** Who the card is for: the child's first name leads, then the grown-up's name; null means "you". */
export const giftFor = (g: { childName?: string | null; recipientName?: string | null }) => g.childName || g.recipientName || null;

/** The card link and the redeem link for a code. */
export const cardUrl = (origin: string, code: string) => `${origin}/gift/card/${code}`;

/**
 * The ready-to-paste message the buyer sends however they like (WhatsApp, Messages, email):
 * "I got you a little gift: every level of Paper Lessons … Open it at <card link> (gift code …)."
 */
export function shareText(g: { kind: string; amountCents: number; childName?: string | null; buyerName?: string | null; code: string; url: string }) {
  const who = g.childName ? `you and ${g.childName}` : "you";
  const what =
    g.kind === "all"
      ? "every level of Paper Lessons, printable reading and math pages for kids 3 to 12"
      : `${dollars(g.amountCents)} to spend on Paper Lessons, printable reading and math pages for kids 3 to 12`;
  const sign = g.buyerName ? ` - ${g.buyerName}` : "";
  return `I got ${who} a little gift: ${what}. Open it at ${g.url} (gift code ${g.code}). It never expires, so open it whenever you're ready.${sign}`;
}

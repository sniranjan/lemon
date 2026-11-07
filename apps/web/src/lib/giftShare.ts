// Gift wording shared by the Worker (the buyer's email, the gift card PDF) and the site (thanks page, gift card).
// Every name is optional: a gift bought with no names at all still reads naturally ("a gift for you", no "from").

export const dollars = (cents: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: cents % 100 ? 2 : 0 }).format(cents / 100);

/** "every level, ages 3 to 12" / "$50 to spend on any level". */
export const giftWhat = (kind: string, amountCents: number) =>
  kind === "all" ? "every level, ages 3 to 12" : `${dollars(amountCents)} to spend on any level`;

/**
 * Who the card is for: the child's first name; null means "you". Older gifts may have a grown-up's name
 * (recipientName) and no child's name: that name stands in.
 */
export const giftFor = (g: { childName?: string | null; recipientName?: string | null }) => g.childName || g.recipientName || null;

/** The gift card PDF for a code (the code is the secret). */
export const cardPdfUrl = (code: string) => `/api/gift/${encodeURIComponent(code)}/card.pdf`;

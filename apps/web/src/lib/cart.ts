// Pricing a cart of levels, shared by the redeem page and the Worker (worker/gift.ts), so the total a family
// sees is the total they're charged. Pure functions, no imports.

export type CartPrices = {
  forSale: string[]; // buyable level slugs, in ladder order
  prices: Record<string, { cents: number }>; // per level
  bundles: { two?: { cents: number }; all?: { cents: number } };
  next: Record<string, string>; // slug → the next level on the ladder (if for sale)
};

export type CartQuote = {
  kind: "level" | "two" | "all" | "pick";
  slugs: string[]; // what the order will cover, in ladder order
  cents: number;
};

/**
 * The best price for the picked levels:
 * - every level for sale, or a pick that would cost at least the every-level price → every level at that price
 * - a level and the next one → the two-level pack price (when cheaper)
 * - otherwise the sum of the levels.
 * Returns null when nothing (or something not for sale) is picked.
 */
export function quoteCart(picked: string[], p: CartPrices): CartQuote | null {
  const want = new Set(picked);
  if (!want.size || [...want].some((s) => !p.forSale.includes(s) || !p.prices[s])) return null;
  const slugs = p.forSale.filter((s) => want.has(s));
  const sum = slugs.reduce((t, s) => t + p.prices[s].cents, 0);
  const all = p.bundles.all;
  if (all && p.forSale.length > 1 && (slugs.length === p.forSale.length || sum >= all.cents)) {
    return { kind: "all", slugs: [...p.forSale], cents: all.cents };
  }
  const two = p.bundles.two;
  if (two && slugs.length === 2 && p.next[slugs[0]] === slugs[1] && two.cents < sum) {
    return { kind: "two", slugs, cents: two.cents };
  }
  return { kind: slugs.length === 1 ? "level" : "pick", slugs, cents: sum };
}

/** Stripe won't charge less than 50 cents, so a remainder is never between 1 and 49 cents. */
export const MIN_CHARGE = 50;

/**
 * How much of a gift balance goes toward `total` and what's left to pay by card. The balance is used up to
 * the total; if that would leave a remainder Stripe can't charge, a little less of the balance is used.
 */
export function planPayment(total: number, balance: number): { use: number; rest: number } {
  let use = Math.max(0, Math.min(balance, total));
  let rest = total - use;
  if (rest > 0 && rest < MIN_CHARGE) {
    use = Math.max(0, total - MIN_CHARGE);
    rest = total - use;
  }
  return { use, rest };
}

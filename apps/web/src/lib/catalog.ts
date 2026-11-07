import { useEffect, useState } from "react";

export type Catalog = {
  previews: string[];   // level slugs with a free preview PDF
  forSale: string[];    // level slugs that can be bought right now (empty while checkout is off)
  prices: Record<string, { cents: number; currency: string }>;   // from Stripe, per level
  // "two" = a level plus the next one (next[slug] says which); "all" = every level for sale
  bundles: Partial<Record<"two" | "all", { cents: number; currency: string; levels: number }>>;
  next: Record<string, string>;
  // gifts are open once checkout is; allCents = the every-level gift's price (null if not on sale)
  gifts?: { open: boolean; allCents: number | null; presets: number[]; min: number; max: number };
};

const EMPTY: Catalog = { previews: [], forSale: [], prices: {}, bundles: {}, next: {} };

/** What the library shows: previews, buyable levels and the price, asked once from the Worker. */
export function useCatalog(): Catalog {
  const [catalog, setCatalog] = useState<Catalog>(EMPTY);
  useEffect(() => {
    fetch("/api/catalog")
      .then((r) => (r.ok ? (r.json() as Promise<Catalog>) : EMPTY))
      .then((c) => setCatalog({ ...EMPTY, ...c }))
      .catch(() => {});
  }, []);
  return catalog;
}

export function formatPrice(cents: number, currency: string): string {
  const whole = cents % 100 === 0;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency.toUpperCase(),
    minimumFractionDigits: whole ? 0 : 2,
  }).format(cents / 100);
}

/** Start Stripe Checkout for one level; resolves to an error message if it couldn't. */
export async function startCheckout(level: string | null, bundle?: "two" | "all"): Promise<string | null> {
  try {
    const r = await fetch("/api/checkout", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ level, bundle }),
    });
    const d = (await r.json()) as { ok: boolean; url?: string; error?: string };
    if (d.ok && d.url) {
      window.location.assign(d.url);
      return null;
    }
    return d.error ?? "Couldn't start checkout.";
  } catch {
    return "Couldn't reach the shop. Check your connection and try again.";
  }
}

// ---------------------------------------------------------------------------------------------------------
// Gifts (worker/gift.ts)

export type GiftInfo = {
  ok: true;
  code: string;
  kind: "all" | "credit";
  amountCents: number;
  balanceCents: number;
  heldCents: number; // part of the balance an open checkout will use (a new checkout closes that one)
  currency: string;
  buyerName: string | null;
  recipientName: string | null; // older gifts only (a grown-up's name; the card falls back to it)
  childName: string | null;
  message: string | null;
  redeemed: boolean;
  orders: { name: string; createdAt: string; expiresAt: string; expired: boolean; centsUsed: number }[];
};

export type ApiResult = { ok: boolean; error?: string; field?: string; url?: string; token?: string; redeemed?: boolean };

const OFFLINE = "Couldn't reach the shop. Check your connection and try again.";

/** POST JSON to the Worker; network trouble comes back as an ordinary error. */
export async function postJson(path: string, body: unknown): Promise<ApiResult> {
  try {
    const r = await fetch(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    return (await r.json()) as ApiResult;
  } catch {
    return { ok: false, error: OFFLINE };
  }
}

export async function getGift(code: string): Promise<GiftInfo | { ok: false; error: string }> {
  try {
    const r = await fetch(`/api/gift/${encodeURIComponent(code)}`);
    return (await r.json()) as GiftInfo | { ok: false; error: string };
  } catch {
    return { ok: false, error: OFFLINE };
  }
}

/** "2026-11-20" or "2026-11-13 14:41:14" (UTC, from D1) → "November 20, 2026". */
export function longDate(s: string): string {
  const iso = s.length === 10 ? `${s}T12:00:00Z` : `${s.replace(" ", "T")}Z`;
  return new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeZone: "UTC" }).format(new Date(iso));
}

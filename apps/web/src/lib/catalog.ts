import { useEffect, useState } from "react";

export type Catalog = {
  previews: string[];   // level slugs with a free preview PDF
  forSale: string[];    // level slugs that can be bought right now (empty while checkout is off)
  prices: Record<string, { cents: number; currency: string }>;   // from Stripe, per level
  // "two" = a level plus the next one (next[slug] says which); "all" = every level for sale
  bundles: Partial<Record<"two" | "all", { cents: number; currency: string; levels: number }>>;
  next: Record<string, string>;
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

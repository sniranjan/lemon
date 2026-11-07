// What's for sale and what it costs, shared by the shop (worker/shop.ts) and gifts (worker/gift.ts).
//
// What's for sale is whatever is in R2: a level is buyable once `levels/<slug>/` holds its PDFs AND its
// Stripe price exists (lookup key `level_<slug>`). Bundles use lookup keys `bundle_two` (a level plus the
// next one) and `bundle_all` (every level).
import ladder from "../src/data/ladder.json";
import { pricesByLookupKey } from "./stripe";

export type ShopEnv = {
  DB: D1Database;
  FILES: R2Bucket;
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  EMAIL?: SendEmail;
};

export const LEVELS = new Map(ladder.map((l) => [l.slug, l]));
/** Every level slug in ladder order (Chicks first). */
export const ORDER = ladder.map((l) => l.slug);
/** level = one level · two = a level and the next · all = every level · pick = any other set (gift carts). */
export type Kind = "level" | "two" | "all" | "pick";
export const BUNDLE_KEYS = { two: "bundle_two", all: "bundle_all" } as const;
export const FILE = /^[a-z0-9][a-z0-9.-]{0,80}\.pdf$/;

export const checkoutOn = (env: ShopEnv) => Boolean(env.STRIPE_SECRET_KEY);

export type LevelPrice = { id: string; cents: number; currency: string };
export type Prices = { bySlug: Map<string, LevelPrice>; bundles: Map<string, LevelPrice> };
let priceCache: { at: number; prices: Prices } | null = null;
const NO_PRICES: Prices = { bySlug: new Map(), bundles: new Map() };

/** Tests only: forget cached prices. */
export function resetPriceCache() {
  priceCache = null;
}

/** Level prices (lookup key `level_<slug>`) and bundle prices, cached for 5 minutes per isolate. */
export async function allPrices(env: ShopEnv): Promise<Prices> {
  if (!env.STRIPE_SECRET_KEY) return NO_PRICES;
  if (priceCache && Date.now() - priceCache.at < 300_000) return priceCache.prices;
  try {
    const keys = [...ORDER.map((s) => `level_${s}`), ...Object.values(BUNDLE_KEYS)];
    const found = await pricesByLookupKey(env.STRIPE_SECRET_KEY, keys);
    const prices: Prices = { bySlug: new Map(), bundles: new Map() };
    for (const p of found) {
      if (p.unit_amount == null || !p.lookup_key) continue;
      const price = { id: p.id, cents: p.unit_amount, currency: p.currency };
      if (p.lookup_key.startsWith("level_")) prices.bySlug.set(p.lookup_key.slice("level_".length), price);
      else prices.bundles.set(p.lookup_key, price);
    }
    priceCache = { at: Date.now(), prices };
  } catch (e) {
    console.error(e);
    if (!priceCache) return NO_PRICES;
  }
  return priceCache!.prices;
}

/** The level after `slug` on the ladder, if it is also for sale. */
export function nextFor(slug: string, forSale: string[]): string | undefined {
  const next = ORDER[ORDER.indexOf(slug) + 1];
  return next && forSale.includes(next) ? next : undefined;
}

/** "Chicks", "Chicks and Ducklings", "Chicks, Ducklings and Bunnies", "All 13 levels". */
export function orderName(kind: Kind, slugs: string[]): string {
  if (kind === "all") return `All ${slugs.length} levels`;
  const names = slugs.map((s) => LEVELS.get(s)!.name);
  return names.length > 2 ? `${names.slice(0, -1).join(", ")} and ${names.at(-1)}` : names.join(" and ");
}

/** The short description after the name in order emails. */
export function orderTitle(kind: Kind, slugs: string[]): string {
  if (slugs.length === 1) return LEVELS.get(slugs[0])!.title;
  if (kind === "all") return "every level, ages 3 to 12";
  if (kind === "two") return "two levels in a row";
  return `${slugs.length} levels`;
}

/** Slugs with whole-level PDFs in R2. */
export async function levelsForSale(files: R2Bucket): Promise<string[]> {
  const listed = await files.list({ prefix: "levels/", delimiter: "/" });
  return listed.delimitedPrefixes.map((p) => p.slice("levels/".length, -1)).filter((s) => LEVELS.has(s));
}

/** Levels that can be bought right now (files in R2 and a Stripe price), in ladder order. */
export async function buyableLevels(env: ShopEnv): Promise<{ prices: Prices; forSale: string[] }> {
  const [prices, withFiles] = await Promise.all([allPrices(env), levelsForSale(env.FILES)]);
  const forSale = checkoutOn(env)
    ? withFiles.filter((s) => prices.bySlug.has(s)).sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b))
    : [];
  return { prices, forSale };
}

export async function levelFiles(files: R2Bucket, slug: string) {
  const listed = await files.list({ prefix: `levels/${slug}/` });
  return listed.objects
    .map((o) => ({ name: o.key.slice(`levels/${slug}/`.length), size: o.size }))
    .filter((f) => FILE.test(f.name))
    .sort((a, b) => rank(a.name) - rank(b.name) || a.name.localeCompare(b.name));
}

/** Reading, then math, then pencil; each subject's level book before its answer key. */
function rank(name: string): number {
  const subject = ["reading", "math", "pencil"].findIndex((s) => name.includes(s));
  return (subject < 0 ? 3 : subject) * 2 + (name.includes("answers") ? 1 : 0);
}

export function parseKind(k: string | undefined): Kind {
  return k === "two" || k === "all" || k === "pick" ? k : "level";
}

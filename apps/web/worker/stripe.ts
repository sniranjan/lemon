// Minimal Stripe client for Workers: plain fetch + WebCrypto, no SDK.
// Only what checkout needs: create a Checkout Session (and a one-off coupon), read one back, and verify
// webhook signatures.

const API = "https://api.stripe.com/v1";

export type CheckoutSession = {
  id: string;
  url: string | null;
  payment_status: "paid" | "unpaid" | "no_payment_required";
  status: "open" | "complete" | "expired";
  amount_total: number | null;
  currency: string | null;
  customer_details: { email: string | null } | null;
  metadata: Record<string, string> | null;
};

/** Stripe's form encoding: nested objects and arrays as a[b][0][c]=v. */
function form(params: Record<string, unknown>, prefix = "", out = new URLSearchParams()): URLSearchParams {
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    const key = prefix ? `${prefix}[${k}]` : k;
    if (Array.isArray(v)) v.forEach((item, i) => form({ [i]: item }, key, out));
    else if (typeof v === "object") form(v as Record<string, unknown>, key, out);
    else out.append(key, String(v));
  }
  return out;
}

async function call<T>(key: string, method: "GET" | "POST", path: string, params?: Record<string, unknown>, idempotencyKey?: string): Promise<T> {
  const headers: Record<string, string> = { authorization: `Bearer ${key}` };
  if (idempotencyKey) headers["idempotency-key"] = idempotencyKey;
  let body: string | undefined;
  if (params) {
    headers["content-type"] = "application/x-www-form-urlencoded";
    body = form(params).toString();
  }
  const res = await fetch(`${API}${path}`, { method, headers, body });
  const data = (await res.json()) as T & { error?: { message?: string } };
  if (!res.ok) throw new Error(`stripe ${method} ${path}: ${res.status} ${data.error?.message ?? ""}`);
  return data;
}

export type Price = { id: string; lookup_key: string | null; unit_amount: number | null; currency: string };

/** Active prices by lookup key (Stripe allows 10 keys per request). */
export async function pricesByLookupKey(key: string, lookupKeys: string[]): Promise<Price[]> {
  const out: Price[] = [];
  for (let i = 0; i < lookupKeys.length; i += 10) {
    const q = form({ active: true, limit: 100, lookup_keys: lookupKeys.slice(i, i + 10) }).toString();
    out.push(...(await call<{ data: Price[] }>(key, "GET", `/prices?${q}`)).data);
  }
  return out;
}

export function createCheckoutSession(key: string, params: Record<string, unknown>, idempotencyKey?: string) {
  return call<CheckoutSession>(key, "POST", "/checkout/sessions", params, idempotencyKey);
}

/** A one-off coupon (used once) for "pay the rest" with a gift balance. */
export function createCoupon(key: string, params: Record<string, unknown>, idempotencyKey?: string) {
  return call<{ id: string }>(key, "POST", "/coupons", params, idempotencyKey);
}

export function getCheckoutSession(key: string, id: string) {
  return call<CheckoutSession>(key, "GET", `/checkout/sessions/${encodeURIComponent(id)}`);
}

const enc = new TextEncoder();

function hex(buf: ArrayBuffer): string {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/**
 * Verify a `Stripe-Signature` header (t=…,v1=…) against the raw body, as Stripe documents:
 * HMAC-SHA256 of `${t}.${body}` with the endpoint secret, and a timestamp within `toleranceSec`.
 */
export async function verifyWebhook(body: string, header: string | null, secret: string, toleranceSec = 300, now = Date.now()): Promise<boolean> {
  if (!header) return false;
  const parts = header.split(",").map((p) => p.split("=") as [string, string]);
  const t = parts.find(([k]) => k === "t")?.[1];
  const sigs = parts.filter(([k]) => k === "v1").map(([, v]) => v);
  if (!t || !sigs.length || !/^\d+$/.test(t)) return false;
  if (Math.abs(now / 1000 - Number(t)) > toleranceSec) return false;
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const expected = hex(await crypto.subtle.sign("HMAC", key, enc.encode(`${t}.${body}`)));
  return sigs.some((s) => safeEqual(s, expected));
}

/** Random URL-safe secret for download links. */
export function newToken(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(24));
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

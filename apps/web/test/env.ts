// Test doubles for the Worker's bindings. D1 = node:sqlite with every migration applied (batch is one
// transaction, as on D1), R2 = an in-memory map, EMAIL = a recorder, Stripe = a fetch stub that throws on any
// URL it doesn't know, so a test can never reach a real API.
import { readdirSync, readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { vi } from "vitest";
import type { ShopEnv } from "../worker/catalog";

const MIGRATIONS = fileURLToPath(new URL("../migrations", import.meta.url));

type Row = Record<string, unknown>;
const plain = (r: unknown) => (r ? { ...(r as Row) } : null);

export function makeD1() {
  const db = new DatabaseSync(":memory:");
  for (const f of readdirSync(MIGRATIONS).filter((f) => f.endsWith(".sql")).sort()) {
    db.exec(readFileSync(path.join(MIGRATIONS, f), "utf8"));
  }
  class Stmt {
    constructor(readonly sql: string, readonly params: unknown[] = []) {}
    bind(...params: unknown[]) {
      if (params.some((p) => p === undefined)) throw new Error("D1_TYPE_ERROR: undefined bind value");
      return new Stmt(this.sql, params);
    }
    runSync() {
      const r = db.prepare(this.sql).run(...(this.params as never[]));
      return { success: true, results: [], meta: { changes: Number(r.changes), last_row_id: Number(r.lastInsertRowid) } };
    }
    async run() {
      return this.runSync();
    }
    async first<T>(col?: string) {
      const r = plain(db.prepare(this.sql).get(...(this.params as never[])));
      return (r && col ? r[col] : r) as T | null;
    }
    async all<T>() {
      return { success: true, meta: {}, results: db.prepare(this.sql).all(...(this.params as never[])).map(plain) as T[] };
    }
  }
  const d1 = {
    prepare: (sql: string) => new Stmt(sql),
    async batch(stmts: Stmt[]) {
      db.exec("BEGIN");
      try {
        const out = stmts.map((s) => s.runSync());
        db.exec("COMMIT");
        return out;
      } catch (e) {
        db.exec("ROLLBACK");
        throw e;
      }
    },
  };
  return { d1: d1 as unknown as D1Database, db };
}

export function makeR2(keys: string[]) {
  const store = new Map(keys.map((k) => [k, `pdf:${k}`]));
  const r2 = {
    async list({ prefix = "", delimiter }: { prefix?: string; delimiter?: string } = {}) {
      const hits = [...store.keys()].filter((k) => k.startsWith(prefix));
      if (!delimiter) return { objects: hits.map((key) => ({ key, size: 1000 })), delimitedPrefixes: [] };
      const prefixes = new Set<string>();
      const objects: { key: string; size: number }[] = [];
      for (const k of hits) {
        const rest = k.slice(prefix.length);
        const i = rest.indexOf(delimiter);
        if (i >= 0) prefixes.add(prefix + rest.slice(0, i + 1));
        else objects.push({ key: k, size: 1000 });
      }
      return { objects, delimitedPrefixes: [...prefixes] };
    },
    async get(key: string) {
      const v = store.get(key);
      return v ? { body: v, httpEtag: '"x"' } : null;
    },
  };
  return r2 as unknown as R2Bucket;
}

export type Sent = { from: { name: string; email: string }; to: string; subject: string; text: string; html: string };

export function makeMailer() {
  const sent: Sent[] = [];
  let failNext = 0;
  const mailer = {
    async send(m: Sent) {
      if (failNext > 0) {
        failNext--;
        throw new Error("mail down");
      }
      sent.push(m);
    },
  };
  return { mailer: mailer as unknown as SendEmail, sent, failNext: (n = 1) => (failNext = n) };
}

/** Stripe prices: $19 per level, $29 two-level pack, $99 every level. */
export const LEVEL_CENTS = 1900;
export const TWO_CENTS = 2900;
export const ALL_CENTS = 9900;

export type StripeCall = { method: string; path: string; body: URLSearchParams; idempotencyKey: string | null };

/** Stubs global fetch for api.stripe.com. Anything else, or an unknown Stripe path, throws. */
export function stubStripe(sessions: Record<string, unknown> = {}) {
  const calls: StripeCall[] = [];
  let n = 0;
  const fetchStub = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input));
    if (url.hostname !== "api.stripe.com") throw new Error(`test tried to reach ${url.hostname}`);
    const method = init?.method ?? "GET";
    const headers = new Headers(init?.headers);
    if (headers.get("authorization") !== "Bearer sk_test_fake") throw new Error("test used a real-looking key");
    const body = new URLSearchParams(typeof init?.body === "string" ? init.body : "");
    calls.push({ method, path: url.pathname, body, idempotencyKey: headers.get("idempotency-key") });
    const json = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json" } });
    if (method === "GET" && url.pathname === "/v1/prices") {
      const keys = url.searchParams.getAll("lookup_keys[]").concat([...url.searchParams.entries()].filter(([k]) => /^lookup_keys\[\d+\]$/.test(k)).map(([, v]) => v));
      const data = keys.map((k) => ({
        id: `price_${k}`,
        lookup_key: k,
        currency: "usd",
        unit_amount: k === "bundle_all" ? ALL_CENTS : k === "bundle_two" ? TWO_CENTS : LEVEL_CENTS,
      }));
      return json({ data });
    }
    if (method === "POST" && url.pathname === "/v1/checkout/sessions") {
      const id = `cs_test_${String(++n).padStart(12, "0")}`;
      return json({ id, url: `https://checkout.stripe.test/${id}` });
    }
    if (method === "POST" && url.pathname === "/v1/coupons") return json({ id: `coupon_${++n}` });
    const m = url.pathname.match(/^\/v1\/checkout\/sessions\/(cs_[\w]+)$/);
    if (method === "GET" && m) return sessions[m[1]] ? json(sessions[m[1]]) : json({ error: { message: "No such session" } }, 404);
    throw new Error(`unexpected Stripe call ${method} ${url.pathname}`);
  });
  vi.stubGlobal("fetch", fetchStub);
  return { calls, sessions };
}

/** Every level for sale (PDFs in R2 for each slug). */
export function makeEnv(slugs: string[]) {
  const { d1, db } = makeD1();
  const mail = makeMailer();
  const env: ShopEnv = {
    DB: d1,
    FILES: makeR2(slugs.flatMap((s) => [`levels/${s}/${s}-reading-level.pdf`, `levels/${s}/${s}-math-level.pdf`])),
    STRIPE_SECRET_KEY: "sk_test_fake",
    STRIPE_WEBHOOK_SECRET: "whsec_test",
    EMAIL: mail.mailer,
  };
  return { env, db, mail };
}

export const ctx = { waitUntil() {}, passThroughOnException() {}, props: {} } as unknown as ExecutionContext;

/** A Stripe-Signature header for `body`, the way Stripe signs webhooks. */
export async function sign(body: string, secret = "whsec_test", t = Math.floor(Date.now() / 1000)) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${t}.${body}`));
  return `t=${t},v1=${[...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("")}`;
}

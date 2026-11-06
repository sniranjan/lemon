#!/usr/bin/env node
// One-time (and re-runnable) Stripe setup for paperlessons.com. Never prints the secret key.
//
//   node scripts/stripe-setup.mjs              # dry run: shows what it would create
//   node scripts/stripe-setup.mjs --apply      # creates products, prices, webhook; sets Worker secrets
//
// Options: --price 1900 (cents, for prices it creates; existing prices are left alone)
//          --url https://paperlessons.com      (site address for the webhook)
//
// The key is read from STRIPE_SECRET_KEY or from ~/.config/paperlessons/stripe.env
// (a line `STRIPE_SECRET_KEY=sk_live_…`; keep that file chmod 600, outside the repo).
//
// What it does, idempotently:
//  - one Product per ladder level, id `level_<slug>`, with metadata.level = slug
//  - one Price per level with lookup key `level_<slug>` (the Worker finds prices by that key; to change a
//    price later, create a new price in the dashboard and move the lookup key to it)
//  - a webhook endpoint <url>/api/stripe/webhook for checkout.session.completed / async_payment_succeeded,
//    and pipes its signing secret straight into `wrangler secret put STRIPE_WEBHOOK_SECRET`
//  - `wrangler secret put STRIPE_SECRET_KEY` with the same key
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const args = process.argv.slice(2);
const apply = args.includes("--apply");
const opt = (name, fallback) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : fallback;
};
const PRICE = Number(opt("--price", "1900"));
const SITE = opt("--url", "https://paperlessons.com").replace(/\/$/, "");
const WEBHOOK_URL = `${SITE}/api/stripe/webhook`;
const EVENTS = ["checkout.session.completed", "checkout.session.async_payment_succeeded"];

function readKey() {
  if (process.env.STRIPE_SECRET_KEY) return process.env.STRIPE_SECRET_KEY.trim();
  const file = `${homedir()}/.config/paperlessons/stripe.env`;
  if (existsSync(file)) {
    // `STRIPE_SECRET_KEY=sk_…` or just the key on its own line
    const m = readFileSync(file, "utf8").match(/^(?:STRIPE_SECRET_KEY\s*=\s*)?["']?((?:sk|rk)_(?:live|test)_\w+)/m);
    if (m) return m[1];
  }
  throw new Error("No key: set STRIPE_SECRET_KEY or create ~/.config/paperlessons/stripe.env");
}

const KEY = readKey();
if (!/^(sk|rk)_(live|test)_/.test(KEY)) throw new Error("That doesn't look like a Stripe secret or restricted key");
const LIVE = /_live_/.test(KEY);

function form(params, prefix = "", out = new URLSearchParams()) {
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    const key = prefix ? `${prefix}[${k}]` : k;
    if (Array.isArray(v)) v.forEach((item, i) => form({ [i]: item }, key, out));
    else if (typeof v === "object") form(v, key, out);
    else out.append(key, String(v));
  }
  return out;
}

async function stripe(method, path, params) {
  const url = `https://api.stripe.com/v1${path}${method === "GET" && params ? `?${form(params)}` : ""}`;
  const res = await fetch(url, {
    method,
    headers: {
      authorization: `Bearer ${KEY}`,
      ...(method === "POST" ? { "content-type": "application/x-www-form-urlencoded" } : {}),
    },
    body: method === "POST" && params ? form(params).toString() : undefined,
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = String(data.error?.message ?? "").replaceAll(KEY, `${KEY.slice(0, 8)}…`); // Stripe echoes bad keys
    const err = new Error(`${method} ${path}: ${res.status} ${msg}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

function putSecret(name, value) {
  execFileSync("npx", ["wrangler", "secret", "put", name], {
    cwd: fileURLToPath(new URL("..", import.meta.url)),
    input: value,
    stdio: ["pipe", "inherit", "inherit"],
  });
}

const ladder = parse(readFileSync(new URL("../../../syllabus/ladder.yaml", import.meta.url), "utf8"));
const account = await stripe("GET", "/account").catch(() => ({ id: "(restricted key: account name not readable)" }));
console.log(
  `Stripe account: ${account.settings?.dashboard?.display_name ?? account.business_profile?.name ?? account.id}` +
    ` (${account.id}, ${LIVE ? "LIVE" : "test"} mode)${apply ? "" : "  [dry run: add --apply to make changes]"}\n`,
);

for (const level of ladder) {
  const id = `level_${level.slug}`;
  let product = null;
  try {
    product = await stripe("GET", `/products/${id}`);
  } catch (e) {
    if (e.status !== 404) throw e;
  }
  if (!product) {
    console.log(`+ product ${id}: ${level.public_name}`);
    if (apply) {
      product = await stripe("POST", "/products", {
        id,
        name: `${level.public_name}: the whole level (printable PDF)`,
        description: `${level.public_title}. Reading and math, age ${level.age}. Printable PDF pages plus answer keys.`,
        metadata: { level: level.slug },
        tax_code: "txcd_10302000", // e-books / digital publications (only used if Stripe Tax is on)
      });
    }
  }
  const prices = await stripe("GET", "/prices", { lookup_keys: [id], active: true });
  if (prices.data.length) {
    const p = prices.data[0];
    console.log(`  price ${id}: ${(p.unit_amount / 100).toFixed(2)} ${p.currency.toUpperCase()} (exists)`);
  } else {
    console.log(`+ price ${id}: ${(PRICE / 100).toFixed(2)} USD`);
    if (apply) {
      await stripe("POST", "/prices", {
        product: id,
        unit_amount: PRICE,
        currency: "usd",
        lookup_key: id,
        metadata: { level: level.slug },
      });
    }
  }
}

const hooks = await stripe("GET", "/webhook_endpoints", { limit: 100 });
const hook = hooks.data.find((h) => h.url === WEBHOOK_URL);
if (hook) {
  console.log(`\n  webhook ${WEBHOOK_URL} (exists: ${hook.id}). Its secret can't be read back; to reset it, delete`);
  console.log("  the endpoint in the dashboard and re-run with --apply.");
} else {
  console.log(`\n+ webhook ${WEBHOOK_URL} → ${EVENTS.join(", ")}`);
  if (apply) {
    const created = await stripe("POST", "/webhook_endpoints", {
      url: WEBHOOK_URL,
      enabled_events: EVENTS,
      description: "paperlessons.com: record paid orders",
    });
    putSecret("STRIPE_WEBHOOK_SECRET", created.secret);
    console.log("  → STRIPE_WEBHOOK_SECRET set on the Worker");
  }
}

if (apply) {
  putSecret("STRIPE_SECRET_KEY", KEY);
  console.log("  → STRIPE_SECRET_KEY set on the Worker");
}

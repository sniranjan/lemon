import { Hono } from "hono";
import shop, { type ShopEnv } from "./shop";
import gift from "./gift";

type Env = ShopEnv & { ASSETS: Fetcher };

const app = new Hono<{ Bindings: Env }>();

// www → apex, so there is one canonical address to remember.
app.use("*", async (c, next) => {
  const url = new URL(c.req.url);
  if (url.hostname === "www.paperlessons.com") {
    url.hostname = "paperlessons.com";
    return c.redirect(url.toString(), 301);
  }
  await next();
});

app.get("/api/health", (c) => c.json({ ok: true }));

// Short, clean links for profiles and posts that land with campaign tags (shows up in Google Analytics).
const SHORT_LINKS: Record<string, string> = {
  "/ig": "/?utm_source=instagram&utm_medium=bio",
};
for (const [path, target] of Object.entries(SHORT_LINKS)) {
  app.get(path, (c) => c.redirect(target, 302));
}

// Free previews live in R2 as previews/<level-slug>.pdf (uploaded separately, one per level).
const SLUG = /^[a-z][a-z0-9-]{1,40}$/;

app.get("/api/previews", async (c) => {
  const listed = await c.env.FILES.list({ prefix: "previews/" });
  const previews = listed.objects
    .map((o) => o.key.slice("previews/".length))
    .filter((k) => k.endsWith(".pdf"))
    .map((k) => k.slice(0, -4));
  return c.json({ previews }, 200, { "cache-control": "public, max-age=300" });
});

app.get("/api/previews/:slug", async (c) => {
  const slug = c.req.param("slug").replace(/\.pdf$/, "");
  if (!SLUG.test(slug)) return c.json({ ok: false, error: "Not found" }, 404);
  const obj = await c.env.FILES.get(`previews/${slug}.pdf`);
  if (!obj) return c.json({ ok: false, error: "This preview isn't ready yet." }, 404);
  const country = (c.req.raw.cf?.country as string | undefined) ?? null;
  c.executionCtx.waitUntil(
    c.env.DB.prepare("INSERT INTO preview_downloads (level, country) VALUES (?, ?)").bind(slug, country).run(),
  );
  return new Response(obj.body, {
    headers: {
      "content-type": "application/pdf",
      "content-disposition": `attachment; filename="paperlessons-${slug}-preview.pdf"`,
      "cache-control": "public, max-age=300",
      etag: obj.httpEtag,
    },
  });
});

// Images and reel videos for social posts (scripts/marketing/ig_publish.py uploads them to R2 as
// social/<hash>.jpg or .mp4). Instagram's API only takes media by public URL, so it fetches them from here.
// Names are content hashes, so the files never change and can be cached forever.
const SOCIAL_MEDIA = /^[a-f0-9]{16}\.(jpg|mp4)$/;

app.get("/media/social/:name", async (c) => {
  const name = c.req.param("name");
  if (!SOCIAL_MEDIA.test(name)) return c.notFound();
  const obj = await c.env.FILES.get(`social/${name}`);
  if (!obj) return c.notFound();
  return new Response(obj.body, {
    headers: {
      "content-type": name.endsWith(".mp4") ? "video/mp4" : "image/jpeg",
      "content-length": String(obj.size),
      "cache-control": "public, max-age=31536000, immutable",
      etag: obj.httpEtag,
    },
  });
});

// Checkout, orders and downloads (worker/shop.ts).
app.route("/", shop);
// Gifts: buying one, the gift card, redeeming a code (worker/gift.ts).
app.route("/", gift);

app.all("/api/*", (c) => c.json({ ok: false, error: "Not found" }, 404));

// Everything else is the React app (static assets).
// Visitors where analytics need opt-in consent (GDPR / UK GDPR / Swiss FADP): EU, EEA, UK, Switzerland.
const CONSENT_COUNTRIES = new Set(
  ("AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE " + "IS LI NO GB CH").split(" "),
);

/**
 * Everything else is the React app (static assets). Pages get a flag in <head> telling the inline Google
 * tag loader and the cookie banner whether this visitor must opt in first. `?region=eu` forces it (testing).
 */
app.all("*", async (c) => {
  const res = await c.env.ASSETS.fetch(c.req.raw);
  if (!res.headers.get("content-type")?.includes("text/html")) return res;
  const country = (c.req.raw.cf?.country as string | undefined) ?? "";
  const needsConsent = CONSENT_COUNTRIES.has(country) || new URL(c.req.url).searchParams.get("region") === "eu";
  const page = new HTMLRewriter()
    .on("head", {
      element(head) {
        head.prepend(`<script>window.__PL_CONSENT_REQUIRED=${needsConsent};</script>`, { html: true });
      },
    })
    .transform(res);
  const headers = new Headers(page.headers);
  headers.set("cache-control", "private, no-cache");
  headers.delete("etag");
  return new Response(page.body, { status: page.status, headers });
});

export { app };

export default {
  fetch: app.fetch,
} satisfies ExportedHandler<Env>;

import { Hono } from "hono";

type Env = { DB: D1Database; FILES: R2Bucket; ASSETS: Fetcher };

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

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const AGES = new Set(["2", "3", "4", "5", "6", "7+"]);

app.post("/api/waitlist", async (c) => {
  const body = await c.req.json<{ email?: string; childAge?: string }>().catch(() => ({}) as never);
  const email = String(body?.email ?? "").trim().toLowerCase();
  const age = AGES.has(String(body?.childAge)) ? String(body.childAge) : null;
  if (!EMAIL.test(email) || email.length > 254) {
    return c.json({ ok: false, error: "Please enter a valid email address." }, 400);
  }
  await c.env.DB.prepare(
    "INSERT INTO waitlist (email, child_age) VALUES (?, ?) ON CONFLICT(email) DO UPDATE SET child_age = COALESCE(excluded.child_age, child_age)",
  )
    .bind(email, age)
    .run();
  return c.json({ ok: true });
});

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
      "cache-control": "public, max-age=3600",
      etag: obj.httpEtag,
    },
  });
});

app.all("/api/*", (c) => c.json({ ok: false, error: "Not found" }, 404));

// Everything else is the React app (static assets).
app.all("*", (c) => c.env.ASSETS.fetch(c.req.raw));

export default app;

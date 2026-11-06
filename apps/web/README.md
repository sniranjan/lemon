# paperlessons.com (web)

The public site. One Cloudflare Worker: a Hono API plus a React/Vite single-page app served as static assets.

- **Stack:** Workers, D1 (`paperlessons`), R2 (`paperlessons-files`), React 19, Tailwind v4, shadcn/ui.
- **Live:** https://paperlessons.com (custom domain; `www` 301-redirects to the apex).

## Commands (run from this folder, or `npm run web:dev` / `npm run web:deploy` from the repo root)

```bash
npm install                 # once, at the repo root
npm run db:migrate:local    # once, creates the local D1 tables
npm run dev                 # local site + Worker + local D1/R2 (http://localhost:5173)
npm run deploy              # build, apply D1 migrations remotely, deploy
```

`npm run dev` / `build` first copy the worksheet pictures from `../../assets/pictures` into
`public/pictures` (git-ignored), so the site and the sheets share one set of pictures.

## API

| Route | What it does |
|---|---|
| `GET /api/health` | `{ ok: true }` |
| `POST /api/waitlist` | `{ email, childAge? }` → row in D1 `waitlist` (upsert on email) |
| `GET /api/previews` | slugs that have a free preview PDF in R2 |
| `GET /api/previews/:slug` | streams `previews/<slug>.pdf` from R2, logs a row in `preview_downloads` |
| `GET /api/catalog` | `{ previews, forSale, priceCents, currency }` for the library (forSale is empty while checkout is off) |
| `POST /api/checkout` | `{ level }` → Stripe Checkout Session URL |
| `POST /api/stripe/webhook` | Stripe `checkout.session.completed` → row in D1 `orders` (signature checked) |
| `GET /api/orders/session/:sid` | thanks page → order token (asks Stripe directly if the webhook hasn't landed) |
| `GET /api/orders/:token` | the order and its files; `GET /api/orders/:token/files/:file` downloads one |

## Free previews

One PDF per level in R2 at `previews/<level-slug>.pdf` (slugs in `src/data/levels.ts`:
`chicks`, `ducklings`, `bunnies`, ... `lions`). A level's "Free preview" button lights up automatically once its
file exists:

```bash
npx wrangler r2 object put paperlessons-files/previews/chicks.pdf --file chicks.pdf \
  --content-type application/pdf --remote
```

Preview PDFs must not show internal level codes or anything referencing other programs (see the root CLAUDE.md §15).

## Selling levels (Stripe Checkout)

- **What's for sale = what's in R2.** A level gets a "Buy" button once `levels/<slug>/` holds its PDFs
  (from the generator's booklets, e.g. `chicks-reading-level.pdf`, `chicks-math-level.pdf`,
  `chicks-pencil-level.pdf` and the `-answers.pdf` keys):
  ```bash
  npx wrangler r2 object put paperlessons-files/levels/chicks/chicks-reading-level.pdf \
    --file ../../out/english/7A/chicks-reading-level.pdf --content-type application/pdf --remote
  ```
- **Price:** `LEVEL_PRICE_CENTS` / `CURRENCY` in `wrangler.jsonc` (one price for every level for now).
- **Turning checkout on** (it stays off until the secret key exists):
  ```bash
  npx wrangler secret put STRIPE_SECRET_KEY        # sk_live_… (or sk_test_… to try it)
  npx wrangler secret put STRIPE_WEBHOOK_SECRET    # whsec_… from the webhook endpoint below
  ```
  In the Stripe dashboard add a webhook endpoint `https://paperlessons.com/api/stripe/webhook` with
  events `checkout.session.completed` and `checkout.session.async_payment_succeeded`, and turn on
  email receipts.
- **Flow:** Buy → Stripe's hosted checkout → `/thanks?session_id=…` → `/orders/<token>`, a private page
  with the download links (bookmarkable; the token is the only key). Orders are in D1 `orders`.
- **Local testing:** put test values in `.dev.vars` (git-ignored); `stripe listen --forward-to
  localhost:5173/api/stripe/webhook` prints a webhook secret for local use.

## Data

```bash
npx wrangler d1 execute paperlessons --remote --command "select * from waitlist order by id desc limit 20"
npx wrangler d1 execute paperlessons --remote --command "select level, email, amount_cents, downloads, created_at from orders order by id desc limit 20"
```

New tables go in `migrations/NNNN_name.sql`; `npm run deploy` applies them.

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
| `GET /api/previews` | slugs that have a free preview PDF in R2 |
| `GET /api/previews/:slug` | streams `previews/<slug>.pdf` from R2, logs a row in `preview_downloads` |
| `GET /api/catalog` | `{ previews, forSale, prices }` for the library (a level is for sale once its PDFs are in R2 and its Stripe price exists) |
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
- **Products and prices live in Stripe.** One product per level (`level_<slug>`) with a price whose lookup
  key is `level_<slug>`; the site reads prices from Stripe. To change a price, add a new price to the
  product in the dashboard and move the lookup key to it (tick "transfer lookup key").
- **Bundles:** `bundle_two` ($29, a level plus the next one on the ladder) and `bundle_all` ($99, every level
  for sale), products + prices by lookup key, created by the setup script. One order can cover several levels
  (`orders.levels` comma list, `orders.kind` level | two | all); the order page groups files by level.
- **Setup (once, re-runnable):** put the key in `~/.config/paperlessons/stripe.env` as
  `STRIPE_SECRET_KEY=sk_live_…` (chmod 600, outside the repo), then:
  ```bash
  node scripts/stripe-setup.mjs            # dry run: shows the account and what it would create
  node scripts/stripe-setup.mjs --apply    # products, prices, webhook endpoint, and both Worker secrets
  ```
  The webhook signing secret goes straight from Stripe into `wrangler secret put`; nothing is printed.
  Turn on email receipts in the Stripe dashboard (Settings → Customer emails).
- **Flow:** Buy → Stripe's hosted checkout → `/thanks?session_id=…` → `/orders/<token>`, a private page
  with the download links. The same link is emailed to the buyer once (worker/email.ts, Cloudflare
  `send_email` from hello@paperlessons.com). **Links expire 7 days after purchase** (`orders.expires_at`);
  after that the page says the link has expired. To give a buyer more time:
  `npx wrangler d1 execute paperlessons --remote --command "UPDATE orders SET expires_at = datetime('now','+7 days') WHERE email = '…'"`
- **Local testing:** put test values in `.dev.vars` (git-ignored); `stripe listen --forward-to
  localhost:5173/api/stripe/webhook` prints a webhook secret for local use.

## Session replay

OpenReplay (self-hosted at `replay.cloudhut.io`), started in `src/lib/replay.ts`, on paperlessons.com only.
Nothing is masked on purpose (text, inputs, network payloads), so replays show anything typed on the
site and order-page URLs, which contain download tokens.

## Data

```bash
npx wrangler d1 execute paperlessons --remote --command "select level, email, amount_cents, downloads, created_at from orders order by id desc limit 20"
```

New tables go in `migrations/NNNN_name.sql`; `npm run deploy` applies them.

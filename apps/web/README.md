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
npm run typecheck           # TypeScript, site + Worker + tests
npm test                    # Worker unit tests (vitest; D1 = node:sqlite with the migrations, Stripe stubbed)
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
| `POST /api/gift/checkout` | gift form (kind, amount; optional child's first name, message and the buyer's name) → validated → Stripe Checkout URL |
| `GET /api/gift/session/:sid` | gift thanks page → gift code (asks Stripe directly if the webhook hasn't landed) |
| `GET /api/gift/:code` | a gift for the redeem page and the gift card: kind, balance, names, message, orders (no emails or tokens) |
| `GET /api/gift/:code/card.pdf` | the gift card PDF (one Letter page, `worker/giftCard.ts`); the code is the secret; `private, no-store` |
| `POST /api/gift/:code/redeem` | every-level gift + `{ email }` → one order for all 13 levels, once |
| `POST /api/gift/:code/checkout` | gift amount + `{ levels, email }` → order with no Stripe if the balance covers it, else Checkout for the rest |
| `POST /api/gift/:code/resend` | emails the still-valid download links of this code's orders again (at most every 2 minutes) |

Pages: `/gift` (form), `/gift/thanks` (the buyer's page: card preview, "Download gift card (PDF)", the code), `/gift/card/:code` (the card on screen with "Open your gift" and the PDF download), `/redeem?code=…` or `/redeem#CODE`. These pages show a code, so analytics never start on them (`onGiftCodePage` in `src/lib/consent.ts` and the check in `index.html`).

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

## Gifts (worker/gift.ts)

- **Two kinds:** every level (the `bundle_all` price, $99) or a gift amount ($19 / $29 / $50, or $10–$250 in
  whole dollars). Gift details travel in the Checkout Session's metadata (Managed Payments rejects `custom_text`);
  the price is inline `price_data`; promotion codes are off for gifts.
- **The form:** pick a gift, then the child's first name, a message (up to 300 characters) and the buyer's name,
  all optional. We never ask for or contact the other family: the buyer prints the card or sends it on.
- **Webhook** (`metadata.gift = buy`) → row in `gifts` with a code like `HAPY-BDAY-MAYA` (no 0/O/1/I/L). The buyer
  (the email Stripe Checkout collects, `customer_details.email`) gets one email, From "Paper Lessons": the receipt,
  the code, paperlessons.com/redeem and the **gift card PDF attached** (the `send_email` builder's `attachments`).
  Never download links. If the PDF fails, the email still goes out with a link to `/api/gift/:code/card.pdf`.
- **The card PDF** (`worker/giftCard.ts`): a fixed background (logo, paper circles, code box, mascots) drawn once
  with Chromium, plus pdf-lib drawing the child's name ("you" without one), "from …" if given, the message on a
  cream card (or our little note), the gift line and the code, with Fredoka / Nunito / Gochi Hand (SIL OFL,
  latin + latin-ext). Text is measured and shrinks or wraps to fit; characters the fonts lack (emoji, other
  scripts) are left out. Same gift, same bytes. pdf-lib and the fonts sit in a lazily imported chunk (~820 KB
  gzip), so other requests don't load them. To change the design: edit `scripts/gift-card/render_background.py`
  and `LAYOUT` in `worker/giftCard.ts`, then `uv run python apps/web/scripts/gift-card/render_background.py`
  and `node apps/web/scripts/gift-card/bundle.mjs` (fonts: `python3 apps/web/scripts/gift-card/build_fonts.py`);
  `npx tsx scripts/gift-card/sample.ts <dir>` writes sample cards.
- **Older gifts** (from when we could email the other family on a chosen day) may have `recipient_name`,
  `recipient_email`, `deliver_on` and `delivered_at`: those columns stay but are no longer written or used,
  except `recipient_name` as the card's name when there's no child's name. There is no cron any more
  (`triggers.crons` is `[]`, which removes the old schedule on deploy).
- **Redeeming:** an every-level gift becomes one order for all 13 levels (order `session_id = gift-all-<code>`, so
  only once). A gift amount pays for a cart (`src/lib/cart.ts`, shared with the redeem page): covered in full →
  the order is made with no Stripe; otherwise Checkout with a one-off `amount_off` coupon for the balance used.
  The balance is taken only when the webhook says it's paid (`gift_redemptions`, keyed on the session, so retries
  are harmless); `gift_holds` reserves the balance while a checkout is open (up to 40 minutes), and starting a
  new checkout for the code first expires its earlier open sessions, so backing out of Stripe never locks it.
- Codes never expire. Orders opened with a gift get the usual 7-day download link.

```bash
npx wrangler d1 execute paperlessons --remote --command "select code, kind, amount_cents, balance_cents, child_name, created_at from gifts order by id desc limit 20"
```

## Session replay

OpenReplay (self-hosted at `replay.cloudhut.io`), started in `src/lib/replay.ts`, on paperlessons.com only.
Nothing is masked on purpose (text, inputs, network payloads), so replays show anything typed on the
site and order-page URLs, which contain download tokens.

## Data

```bash
npx wrangler d1 execute paperlessons --remote --command "select level, email, amount_cents, downloads, created_at from orders order by id desc limit 20"
```

New tables go in `migrations/NNNN_name.sql`; `npm run deploy` applies them.

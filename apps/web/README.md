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

## Free previews

One PDF per level in R2 at `previews/<level-slug>.pdf` (slugs in `src/data/levels.ts`:
`chicks`, `ducklings`, `bunnies`, ... `lions`). A level's "Free preview" button lights up automatically once its
file exists:

```bash
npx wrangler r2 object put paperlessons-files/previews/chicks.pdf --file chicks.pdf \
  --content-type application/pdf --remote
```

Preview PDFs must not show internal level codes or anything referencing other programs (see the root CLAUDE.md §15).

## Data

```bash
npx wrangler d1 execute paperlessons --remote --command "select * from waitlist order by id desc limit 20"
```

New tables go in `migrations/NNNN_name.sql`; `npm run deploy` applies them.

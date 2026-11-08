# Pinterest: paperlessons.com

Pins for printable reading and math, ages 3 to 12. Everything here is ours to post. The rules are the same as
for Instagram (see `marketing/instagram/README.md`):
- Use public level names only (Chicks … Whales). Never internal codes, and never other programs' names.
- Use American spelling.
- Say "about two grades ahead of school" and "a few pages a day". Don't promise results.
- No children's faces, and no prices on images (pins live for years).
- Use real pages from the free preview PDFs.

```
boards.yaml           the boards (key → name + description); pins name a board by key
pins/batch-NN.yaml    a batch of pin specs (format: top of scripts/marketing/pin_make.py)
pins/batch-NN/        rendered pins, 1000×1500 PNG (2:3), one per pin id
pins/batch-NN-contact.png   every pin at feed size (~236px wide), to check they read when small
pins/manifest.json    what pin_publish.py posts, in order (written by pin_make.py)
boards.json           board ids per environment, saved by --boards (not secret)
pinned.jsonl          one line per published pin: id, environment, pin id, image URL (never post twice)
```

## Make pins

```bash
uv run python scripts/marketing/pin_make.py marketing/pinterest/pins/batch-01.yaml --check   # specs only
uv run python scripts/marketing/pin_make.py marketing/pinterest/pins/batch-01.yaml           # render + manifest
uv run python scripts/marketing/pin_make.py marketing/pinterest/pins/batch-01.yaml --only foxes-math
```

Before rendering you need:
- the preview PDFs in `out/previews/<slug>.pdf` (`uv run ws preview --subject … --level …`)
- `npm run sync` in `apps/web`, for the ladder and mascots
- `pdftoppm`

Every title, description, alt text and piece of image text is checked against `content/banned.yaml`, plus
these extra rules:
- no prices
- no "free printable"
- no "boost", "master" or "guarantee"
- no "Common Core"

The renderer also fails when a headline runs past 2 lines or when a page overlaps the header or footer. Open the
contact sheet and a few full-size pins before publishing.

**Writing a pin.** The title is ≤ 100 characters with the search words first, for example
"Times Tables Worksheets | Grade 3 Multiplication and Division Printables". The description is ≤ 500 characters
and covers:
- skill
- grade
- age the level is made for
- "printable"
- "homeschool"
- level name
- "free preview on the site"

The alt text says what is on the image. The headline is 2–4 words. Use 1–2 real pages; never the preview
cover (page 1) or the closing page.

**Links.**
- Level and skill pins go to `https://paperlessons.com/?utm_source=pinterest&utm_medium=pin&utm_campaign=<level
  or skill>&utm_content=<pin id>#library`. That is the library section. The site has no per-level anchor yet.
- Gift pins go to `https://paperlessons.com/gift?utm_…`.

## Boards

| key | board | levels |
|---|---|---|
| preschool | Preschool Printables (Ages 3–4) | Chicks, Ducklings, first words, counting, pencil lines |
| k1 | Kindergarten & Grade 1 Worksheets | Bunnies, Kittens, Puppies, phonics |
| grade23 | Grade 2–3 Worksheets | Cubs, Foxes, times tables |
| upper_reading | Upper Elementary Reading | Owls, Otters reading, reading comprehension |
| upper_math | Upper Elementary Math | Owls, Otters math, fractions |
| middle | Middle School Reading & Math | Pandas, Penguins, Lions, Whales |
| gifts | Gift Ideas for Kids | gift card pins (link to /gift) |

Create them once with `--boards --create`. It creates the boards that are missing, as PUBLIC, and saves their ids.

## Getting a token

1. **The app is pending approval.** Nothing can be posted yet. Use `--dry-run`, which needs no token.
2. **Trial access.** Once Pinterest grants trial access, the app may only call the **sandbox**
   (api-sandbox.pinterest.com).
   - Generate a sandbox token in the developer portal: My apps → the app → "Generate token".
   - Choose the scopes `boards:read`, `boards:write`, `pins:read`, `pins:write` and `user_accounts:read`.
   - Put it in the repo-root `.env`, which is git-ignored:
     ```
     PINTEREST_SANDBOX_TOKEN=pina_...
     ```
   - Run every command with `PINTEREST_SANDBOX=1` in front. Sandbox boards and pins are separate from the
     real account and nobody sees them. Use the sandbox to prove the flow end to end:
     `PINTEREST_SANDBOX=1 … --check`, then `--boards --create`, then `--limit 1`.
3. **Standard access.** After review, Pinterest grants standard access.
   - Make a production token with the same scopes (OAuth flow or the portal's token generator).
   - Save it as `PINTEREST_ACCESS_TOKEN=pina_...` in `.env`.
   - Run without `PINTEREST_SANDBOX`.
4. **Refreshing.** Access tokens expire after about 30 days. If you have the app id, secret and a refresh token in
   `.env` (`PINTEREST_APP_ID`, `PINTEREST_APP_SECRET`, `PINTEREST_REFRESH_TOKEN`), `--refresh` gets a new token
   and rewrites the token line in `.env`. It uses POST /v5/oauth/token with grant_type=refresh_token and Basic
   app auth. Otherwise generate a new token in the portal. The scripts never print tokens.

## Publishing

```bash
uv run python scripts/marketing/pin_publish.py --dry-run --limit 3     # exactly what would be sent; no network
uv run python scripts/marketing/pin_publish.py --check                 # GET /v5/user_account
uv run python scripts/marketing/pin_publish.py --boards [--create]
uv run python scripts/marketing/pin_publish.py --limit 3               # the next 3 pins not yet pinned
uv run python scripts/marketing/pin_publish.py --only gift-every-level
```

Each pin is published in three steps:
1. The PNG is converted to a JPEG and uploaded to R2 as `paperlessons-files/social/<hash>.jpg` with wrangler.
   This is the same helper `ig_publish.py` uses.
2. The image is served at `https://paperlessons.com/media/social/<hash>.jpg`.
3. The script calls `POST /v5/pins` with `board_id`, `title`, `description`, `link`, `alt_text` and
   `media_source {source_type: image_url, url}`.

Results go to `pinned.jsonl`, keyed by (pin id, environment). A pin already there is skipped unless `--force`
is given. Sandbox pins never block real ones.

**Cadence.**
- Post about 3 pins a day (`--limit 3`), every day, rather than a big batch at once. Pinterest rewards
  steady, fresh pins.
- The manifest order mixes levels and boards, so a few a day spreads across boards.
- Make the next batch (`batch-02.yaml`) when about a week of pins is left. Use new pages, new headlines and the
  same links.
- Seasonal pins (gifts in November–December, back to school in July–August) go up 30–45 days before the season.

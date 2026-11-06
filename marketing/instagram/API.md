# Posting to Instagram from the repo

How we post to **@paper.lessons**, read comments and messages, and reply to them, through Meta's Graph API
instead of the phone app. Two scripts do the work:

| Script | What it does |
|---|---|
| `scripts/marketing/ig_post.py` | **Makes** a post: `post.yaml` → `post.png` (or `slide-N.png`) + `caption.md`, in the house style, with text checks |
| `scripts/marketing/ig_publish.py` | **Publishes** a post folder or a story; lists comments and DMs; replies |

Every publish is logged in `posted.jsonl` (this folder), so nothing goes up twice by accident.

---

## 1. Every time: refresh the token (1 minute)

The token is short-lived (an hour or two) and we chose not to keep a long-lived one. Before posting or
replying:

1. Open [developers.facebook.com](https://developers.facebook.com) → **My Apps → Postman** → **Use cases →
   Manage messaging & content on Instagram → Customize → API setup with Unified login**.
2. Step **2. Generate access tokens** → **Generate token** next to `paper.lessons`.
3. Paste it into the repo-root `.env` after `IG_ACCESS_TOKEN=` (replace the old one). Never paste it in chat
   or commit it; `.env` is git-ignored.
4. Check it: `uv run python scripts/marketing/ig_publish.py --check` → shows `@paper.lessons`, posts, and the
   publishing quota (100 a day).

An expired token fails with `(the token has expired or is wrong: regenerate it ...)`.

## 2. Posting something new (the usual flow)

Post when something a parent would care about ships: a new level is ready, a new free preview, a level goes on
sale, a new kind of page, a site feature (e.g. a new page on paperlessons.com). Not for internal changes.

```bash
# 1. Scaffold a dated folder with a post.yaml template
uv run python scripts/marketing/ig_post.py new 2026-11-20-bunnies-is-here

# 2. Fill in marketing/instagram/posts/2026-11-20-bunnies-is-here/post.yaml
#    (headline, subline, real pages, mascots, caption, tags, alt text)

# 3. Render: writes post.png / slide-N.png + caption.md and checks all text
uv run python scripts/marketing/ig_post.py render marketing/instagram/posts/2026-11-20-bunnies-is-here

# 4. LOOK at the images (they must read well as a small grid tile), then dry-run
uv run python scripts/marketing/ig_publish.py marketing/instagram/posts/2026-11-20-bunnies-is-here --dry-run

# 5. Refresh the token (§1), then publish
uv run python scripts/marketing/ig_publish.py marketing/instagram/posts/2026-11-20-bunnies-is-here

# 6. Commit the folder and posted.jsonl
```

### `post.yaml` (one layout, `announce`, that adapts)

```yaml
background: cream            # cream | sun | coral | teal | sky | grape | leaf
headline: "New: Cubs Reading"
subline: "picture puzzles, kinds of words, read aloud"   # handwritten line
chip: "Grade 2 work, age 5"  # optional pill
pages:                       # 0–3 real pages from out/previews/<level>.pdf
  - {level: cubs, page: 1}
  - {level: cubs, page: 2}
  - {level: cubs, page: 3}
mascots: [cubs]              # 0–3 level slugs (chicks … whales); or pictures: [apple, duck] from assets/pictures
sticker: "Try it free"
sticker_sub: "link in bio ↑"
slides:                      # optional: more slides with the same keys → a carousel (max 10)
  - background: sky
    headline: "Read aloud"
    subline: "a short story, then three questions"
    pages: [{level: cubs, page: 4}]
caption: |
  Cubs Reading is ready 🐻 ...
  Free previews at the link in bio.
tags: "#printableworksheets #kidsworksheets ... #paperlessons"   # 8–15 hashtags
alt: >-
  Slide 1: ...

  Slide 2: ...                # one paragraph per slide starting "Slide N:" → each carousel image gets its own alt text
```

With pages, mascots peek over the pages; with only mascots/pictures they sit in big round discs; with neither,
the logo fills the space. Real pages need `uv run ws preview --subject … --level …` to have built
`out/previews/<slug>.pdf`. For a different look, add a layout in `ig_post.py` (the launch set's one-off
layouts are in `instagram_launch.py`).

### Stories

A story is one 1080×1920 image, no caption; it disappears after 24 hours (save it to a Highlight in the app):

```bash
uv run python scripts/marketing/ig_publish.py marketing/instagram/stories/highlights/levels.png --story
```

## 3. Comments and messages

```bash
uv run python scripts/marketing/ig_publish.py --inbox                 # comments on the last 12 posts + DMs
uv run python scripts/marketing/ig_publish.py --reply-comment 1789... "Thank you! Chicks is a great start at 3."
uv run python scripts/marketing/ig_publish.py --hide-comment 1789...  # spam or rude
uv run python scripts/marketing/ig_publish.py --reply-dm 9876... "Hi! ..."
```

- **Replies are public (comments) or go to a real parent (DMs): draft them, show the user, then send.**
  Warm, short, no promises of results, public level names only, never ask for a child's details.
- **DMs:** Meta only lets us reply within **24 hours** of the person's last message, and never message first.
  For the inbox to show anything, turn on, in the Instagram app: **Settings → Messages and story replies →
  Message controls → Connected tools → Allow access to messages**.
- DM replies are untested so far (no messages yet). If `--reply-dm` fails, our setup may need a Facebook Page
  linked to the account (see §5).

## 4. What the API can't do (do these in the app)

Highlights (create or add to), pinning posts, editing the bio or profile picture, music or stickers on stories,
editing a caption after posting, scheduling for later (we post when it's time instead).

## 5. How it's set up (for when something breaks)

- **Meta app "Postman"** (id `2181250069269397`, owned by our business portfolio), use case *Manage messaging &
  content on Instagram*. New apps get **"API setup with Unified login"**; the older "Instagram login" setup isn't
  offered any more. The *Instagram Tester* role only takes Facebook developer accounts, not an Instagram
  handle; we didn't need it.
- **Token:** a Facebook-style token (starts `EAA`). It only works on **graph.facebook.com**
  (graph.instagram.com rejects it). `/me` and `/me/accounts` come back empty because there's no Facebook Page,
  so we call the account directly by its Instagram user id, `IG_USER_ID=17841466730265977` in `.env`.
- **Permissions:** `instagram_basic`, `instagram_content_publish`, `instagram_manage_comments`,
  `instagram_manage_messages` (+ `instagram_manage_insights`). Untick `ads_management` / `ads_read` when
  generating; we don't need them.
- **Images:** the API only takes media by public URL. `ig_publish.py` converts PNG → JPEG (`sips`), uploads it to
  R2 (`paperlessons-files/social/<hash>.jpg`, via wrangler, needs `npx wrangler login`), and the site serves it
  at `https://paperlessons.com/media/social/<hash>.jpg` (`apps/web/worker/index.ts`).
- **Cloudflare's bot filter** returns 403 to Python's default user agent, so the script sends
  `paperlessons-publisher/1.0`.
- **Limits:** 100 API posts per 24 hours; carousels up to 10 images; caption ≤ 2,200 characters, ≤ 30 hashtags
  (we use 8–15).
- **If the account can't be found** or DMs need a Page: create a "Paper Lessons" Facebook Page, link
  @paper.lessons to it (Page settings → Linked accounts), regenerate the token with `pages_show_list` and
  `pages_read_engagement` too.

# Feed posts

## Set 2: the fresh grid (current)

Built 2026-11-06 to replace the launch set once the user has deleted the old posts in the app (see "Retired"
below). Nine posts = three full grid rows, framed around the whole ladder: 13 levels, ages 3 to 12, reading +
math about two grades ahead of school, a free preview for every level. No partial counts, no "coming soon".
Preview: `set2-grid-preview.png` (profile view, each tile cropped to 3:4).

**Post in this order, oldest first** (the profile shows the newest top-left, so 09 ends up top-left):

| # | Folder | Shows | Background | Made by | Status |
|---|---|---|---|---|---|
| 1 | `set2-01-hello/` | logo, "Little lessons, one page at a time", ages 3–12, three real pages | cream | launch script | ready |
| 2 | `set2-02-thirteen-levels/` | carousel: all 13 mascots on the climb, then 4 slides of level cards (age, grade work, "Free preview") | sky | launch script | ready |
| 3 | `set2-03-ages-3-4/` | carousel: band cover + Chicks, Ducklings, Bunnies, Kittens (3 real pages each) | cream | ig_post | ready |
| 4 | `set2-04-ages-5-6/` | carousel: band cover + Puppies, Cubs, Foxes | grape | ig_post | ready |
| 5 | `set2-05-ages-7-8/` | carousel: band cover + Owls, Otters | cream | ig_post | ready |
| 6 | `set2-06-ages-9-12/` | carousel: 4 mascot badges + Pandas, Penguins, Lions, Whales | coral | ig_post | ready |
| 7 | `set2-07-two-grades-ahead/` | "Age 6? Grade 3 work." ladder: ages 3/6/9/12 → grade work | cream | launch script | ready |
| 8 | `set2-08-how-it-works/` | three steps: pick a level, get the whole level (one PDF), a little every day | sun | launch script | ready |
| 9 | `set2-09-try-free/` | "Try any level free", preview covers fanned, link in bio | cream | ig_post | ready |

Grid (newest top-left), a checkerboard of cream and color:

```
09 Try any level free (cream)  08 How it works (sun)     07 Two grades ahead (cream)
06 Ages 9 to 12 (coral)        05 Ages 7 & 8 (cream)     04 Ages 5 & 6 (grape)
03 Ages 3 & 4 (cream)          02 Thirteen levels (sky)  01 Hello (cream)
```

**Pinning:** pinned posts jump to the front of the grid, which would break the checkerboard above, so pin
nothing while set 2 is the whole grid (09 is top-left anyway). Once newer posts push the set down, pin
02 Thirteen levels and 09 Try any level free (and 01 Hello if wanted) in the app (API.md §4).

**Rendering:**
- 01, 02, 07, 08 and the grid preview: `uv run python scripts/marketing/instagram_launch.py set2`.
- 03–06 and 09: `uv run python scripts/marketing/ig_post.py render marketing/instagram/posts/set2-NN-…`.
- Needs `out/previews/<slug>.pdf` for every level used (copy from the main checkout) and the synced site data
  (`node apps/web/scripts/sync-pictures.mjs && node apps/web/scripts/sync-ladder.mjs`). In a worktree, also
  symlink the main checkout's `node_modules` (or `npm install`): the renders load Nunito from
  `node_modules/@fontsource/nunito`.
- All nine are rendered (2026-11-06, all 13 levels on sale). Sublines and captions were checked against the
  real preview pages and the current level titles; when a level's preview or title changes, re-check the page
  numbers in its `post.yaml` (preview page 1 is the cover, the last page is the closing page), re-render, look at
  every slide, then re-run `instagram_launch.py set2` for the grid preview.
- Publish only after the user has deleted the old launch posts in the app (the API can't delete with our setup).

**Posting plan:**
- Day 1: 01 Hello, then 02 Thirteen levels about an hour later (the profile is never one lonely post).
- Then one post a day, morning 7–8 am Eastern (or evening 8–9 pm): 03, 04, 05, 06, 07, 08, 09.
  Don't reorder (the checkerboard depends on it).
- Share each post to stories the same day.
- After the set: 3 feed posts a week (e.g. Mon / Wed / Sat): real pages from one level per post
  (`ig_post.py`, one level's 3 best pages), new site features, and short parent tips. Post when something a
  parent would care about ships; one feed post a day at most.
- Comments and DMs: run `ig_publish.py --inbox` daily; draft replies and get the user's OK before sending.

## Retired: launch set (01–06)

Retired 2026-11-06: the catalog moved on (the launch posts say only Chicks and Ducklings are ready, and the
level cards say "coming soon"). The user is deleting the published ones (01 Hello, 02 Meet the levels,
03 A real page) in the app; 04–06 were never published and won't be. Files kept for history; don't post them.
Their renders come from `uv run python scripts/marketing/instagram_launch.py` (no argument), which also
rewrites the highlight covers in `../stories/highlights/`.


Rendered by `uv run python scripts/marketing/instagram_launch.py` (re-runnable, byte-identical output).
Edit the layouts and captions in that script, not the PNGs or `caption.md` files, then re-run it.

The launch set uses `NN-slug/` folders (posting order) instead of the `YYYY-MM-DD-name/` scheme in
`../README.md`, because the dates aren't fixed yet. Later posts use dated folders made with `ig_post.py` (see `../API.md`) and are published with `ig_publish.py`;
`../posted.jsonl` records what's up.

| # | Folder | Images | Background |
|---|---|---|---|
| 1 | `01-hello/` | `post.png` | cream |
| 2 | `02-meet-the-levels/` | carousel, `slide-1.png` … `slide-5.png` | sky (cover), cream |
| 3 | `03-a-real-page/` | `post.png` | cream |
| 4 | `04-how-it-works/` | `post.png` | sun |
| 5 | `05-two-grades-ahead/` | `post.png` | cream |
| 6 | `06-free-previews/` | `post.png` | coral |

Each folder has `caption.md` with the caption, hashtags and alt text. Paste the alt text under
Advanced settings → Accessibility → Write alt text (for the carousel, one per slide is fine).

### Posting order and grid

Post them **in number order, 01 first**. The profile shows the newest post top-left, so the grid ends up as:

```
06 Free previews (coral)   05 Two grades ahead (cream)   04 How it works (sun)
03 A real page (cream)     02 Meet the levels (sky)      01 Hello (cream)
```

Colored and cream tiles alternate like a checkerboard, and "Try it free" lands in the top-left spot.
See `grid-preview.png` (it crops each post to 3:4 the way the profile grid does; all important
content stays inside that crop).

Once all six are up, pin **01 Hello** and **02 Meet the levels** (and optionally 06) so new visitors see
who we are first.

### Cadence and times

- **Launch week:** 01 and 02 on day 1 (02 about an hour after 01, so the profile is never one lonely post),
  then one post every other day: 03 day 3, 04 day 5, 05 day 7, 06 day 9.
- **After that:** 3 feed posts a week (for example Mon / Wed / Sat), with stories in between.
- **Times (US parents, use the viewer's time zone; start with Eastern):** weekday mornings 7–8 am
  (before school drop-off), or evenings 8–9 pm (after bedtime). Weekends 8–10 am.
  Check Insights → Audience after two weeks and move to whatever hours the followers actually use.
- Share each new post to stories the same day, and add it to the matching highlight
  (`../stories/highlights/`: Free previews, Levels, How it works, Real pages).

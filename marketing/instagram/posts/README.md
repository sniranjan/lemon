# Feed posts: launch set

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

## Posting order and grid

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

## Cadence and times

- **Launch week:** 01 and 02 on day 1 (02 about an hour after 01, so the profile is never one lonely post),
  then one post every other day: 03 day 3, 04 day 5, 05 day 7, 06 day 9.
- **After that:** 3 feed posts a week (for example Mon / Wed / Sat), with stories in between.
- **Times (US parents, use the viewer's time zone; start with Eastern):** weekday mornings 7–8 am
  (before school drop-off), or evenings 8–9 pm (after bedtime). Weekends 8–10 am.
  Check Insights → Audience after two weeks and move to whatever hours the followers actually use.
- Share each new post to stories the same day, and add it to the matching highlight
  (`../stories/highlights/`: Free previews, Levels, How it works, Real pages).

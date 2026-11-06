# Instagram: @paper.lessons

Marketing material for https://www.instagram.com/paper.lessons/. Everything here is ours to post.

```
profile/     profile picture (1080×1080) and the bio
posts/       feed posts, one folder per post: posts/YYYY-MM-DD-short-name/ (images + caption.md)
stories/     stories (1080×1920)
reels/       reel covers (1080×1920) and scripts
templates/   reusable layouts
```

## Sizes
| Format | Size | Notes |
|---|---|---|
| Profile picture | 1080×1080 | shown as a small circle: keep everything inside the middle ~80% |
| Feed post | 1080×1350 (4:5) | the tallest Instagram allows; also fine: 1080×1080 |
| Story / reel | 1080×1920 (9:16) | keep text out of the top 250px and bottom 300px (app UI covers them) |

## Brand (same as the site and the PDFs)
- **Logo:** `assets/brand/` (regenerate with `uv run python scripts/brand/export.py`). Don't redraw or restyle it.
- **Fonts:** "paper" and headings: Fredoka Bold. Handwritten accents ("lessons", little notes): Gochi Hand.
  Body text: Nunito. Font files: `assets/fonts/brand/` (Fredoka, Gochi Hand) and `@fontsource/nunito`.
- **Colors:** ink `#1f2a44` · cream `#fff8ec` · sun `#ffc83d` · coral `#ff6b5e` · teal `#10a99a` ·
  sky `#4d96ff` · grape `#9b5de5` · leaf `#5cc46b`. Thick ink outlines, rounded corners, flat colors.
- **Pictures:** reuse the worksheet pictures (`assets/pictures/`) and level mascots (`apps/web/public/brand/`).
- **Real sheets:** real pages make the best posts. Free previews live in `out/previews/<level>.pdf`
  (`uv run ws preview <level>`).

## Rules
- Never mention, compare to, or hint at other learning programs by name. Levels are animals
  (Chicks, Ducklings, …), never codes.
- Say "ages 3 to 12", "about two grades ahead of school", "a few pages a day". Don't promise results.
- No children's faces or names unless a parent has given written permission; prefer hands, pencils and pages.
- American spelling. Link in bio: https://paperlessons.com

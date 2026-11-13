# Instagram reels (Remotion)

1080 × 1920, 30 fps, no sound (add a trending sound in the Instagram app when posting).

```bash
uv run python scripts/marketing/reel_assets.py      # fonts, mascots, levels.json, preview pages → public/ (git-ignored)
cd apps/reels && npx remotion studio                # preview and tweak
npx remotion render Quiz out/Quiz.mp4               # Ladder | Quiz | Stack
```

Finished reels and captions live in `marketing/instagram/reels/<NN-name>/` (reel.mp4 + caption.md).
Keep text between y 200 and 1500 and 90px from the sides: Instagram's buttons and caption cover the rest.
Same rules as every post: public level names only, no prices, no children's faces, no promises of results.

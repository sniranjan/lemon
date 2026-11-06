# Status — where we are (updated 2026-11-06)

Read `CLAUDE.md` first (it is the spec), then this file. Branch: `feature/worksheets`.

## Done
- **Milestones 1–3** (CLAUDE.md §13): package, models, syllabus YAML for EN 7A, MA 6A and pencil ZI;
  all 10 sheet types with templates; `ws verify` (content, plan and layout checks, contact sheets);
  PDF booklets with cover, progress log and answer keys.
- **Math 5A (Ducklings math)**: `syllabus/math/5A.yaml`, 200 pages, sections A–E with `standards:`.
  `number_read` gained `show: ten_frames | rods` (11–30 as ten-frames, 51–100 as tens bars);
  new `number_sequence` (tracks with gaps to say aloud). All 200 pages verify with 0 errors.
- **Pencil ZII (Ducklings pencil warm-ups, 100 pages)**: `syllabus/pencil/ZII.yaml`, using an extended
  `line_path` sheet type. A Shape to Shape 1–30 · B Story Paths 31–60 (picture pairs from
  `content/pencil/line_stories.yaml`) · C Zigzag Paths 61–80 · D Twists and Turns 81–100 (steps,
  bumps, S-curves). Lanes go from 52 to 32 px. Verify samples each lane, so it never turns back and
  stays clear of the page edges and of other lanes. ZI output is unchanged.
- **Word bank: 160 of ~200 words** in `content/vocab/english.yaml` (file order = introduction order,
  2 new words per page), all with original pictures in `assets/pictures/` and licence entries.
  | Batch | Words | 7A pages | Approved | Commit |
  |---|---|---|---|---|
  | 1 | 1–40 | 1–20 | 2026-11-03 | fa361bd |
  | 2 | 41–80 (incl. 6 color words, drawn as crayons) | 21–40 | 2026-11-03 | 1ba6f36 |
  | 3 | 81–120 (incl. 8 action words) | 41–60 | 2026-11-05 | baf79f9 |
  | 4 | 121–160 (hose for glasses; brown/black crayons; 40 pictures, `draw_7A_batch4.py`) | 61–80 | 2026-11-06 | this branch |

  Ducklings Reading (EN 6A) words, `level: 6A`, one new word a page (target 80):
  | Batch | Words | 6A pages | Approved | Commit |
  |---|---|---|---|---|
  | 6A-1 | 40 (12 actions, 5 body, 3 clothes, 5 toys, 5 home, big/little/hot/cold, 6 animals); 36 pictures (`draw_batch4.py`) | 71–100, 141–150 | 2026-11-06 | this branch |
  | 6A-2 | 40, draft `syllabus/drafts/6A-words-batch2.md` | 151–190 | waiting | |
- Generated so far (in `out/`, git-ignored; rebuild with `ws generate`): EN 7A pages 1–80 and
  101–200, EN 6A pages 1–150 and 191–200, plus samples of MA 6A and ZI.
- `ws verify` (after batch 4, English only): 340 sheets, **0 errors**, 5 expected warnings (color-word
  pages in 7A and 6A; the word bank covers 80 of 100 7A new-word pages and 40 of 80 6A ones, so
  review/story sheets will change as words are added).
- `uv run pytest`: 149 tests pass.

- **Ducklings reading (EN 6A)** (2026-11-06): `syllabus/english/6A.yaml` (A Word Hunt 1–30, B Little
  Phrases 31–100, C Say a Sentence 101–200); new sheet types `phrase_card` and `sentence_recite`; frames,
  picture colors and who-can-do-what in `content/phrases/english.yaml`; planner `plan_phrases`
  (and `review_from_levels` for 6A-A).
  Word batch 1 (2026-11-06): pages 1–150 and 191–200 build (160 of 200; verify 0 errors, 3 expected
  warnings). big/little/hot/cold use the `sizes` / `temperatures` tables and a `describe` sentence group;
  Word Hunt takes the least-seen Chicks words first; animal action sentences show the animal only.
  Pages 151–190 wait for batch 2. The live free preview (pages 3, 33, 103, 131) is now stale for
  pages 3, 103 and 131: rebuild it with `ws preview` and re-upload when the user says so.

## Next steps
1. **Batch 5** (words 161–200, 7A pages 81–100): draft a table and wait for the user's OK; avoid every
   Ducklings word (`syllabus/drafts/6A-words-batch*.md`). That completes 7A-A's word bank. Plural words go
   in `plural:` in `content/phrases/english.yaml` (stories and phrases then avoid "... is ...").
3. Then generate all of EN 7A, MA 6A, ZI; `ws verify` must pass; build booklets with `ws render --pdf`.
4. `ws vocab stats` is a stub (exits 2); implement it when needed.
5. **6A word batch 2**: draft in `syllabus/drafts/6A-words-batch2.md`. Wait for the user's OK; then add
   words with `level: 6A`, draw pictures (new `draw_batch5.py`), and add `can_do` / `picture_colors` /
   `sizes` / `temperatures` / `plural` entries in `content/phrases/english.yaml` so each new word fits a
   sentence frame (the planner errors if it doesn't).

## Open questions for the user
- What should a 7A repeat (`--variant 2`) change? Today it keeps the same words and strip and only
  changes the parent tip.

## Decisions to keep (from the user)
- American spelling everywhere a child or parent reads; English only (no home language).
- Design in color but keep everything readable in black and white; picture fills 50–75% gray
  lightness (crayon color words exempt, `kind: color_swatch`).
- Claude draws all pictures (OpenMoji only if genuinely hard, with attribution).
- New story-frame categories so far: family, body, nature, colors, actions
  (`content/stories/english.yaml`). Words that read as "some" carry `mass: true`.
- Ideas for later batches: more verbs/actions, opposites-friendly nouns; keep words ≤ 7 letters.

## Picture workflow
- `scripts/pictures/draw_batchN.py <out_dir>` wrote each batch's SVGs. They are a record only:
  the SVGs in `assets/pictures/` are the source of truth, so **don't re-run old batch scripts**
  (later fixes may be overwritten). Copy the helpers into a new `draw_batch4.py` for batch 4.
- `scripts/pictures/zoom.py out.png name …` renders chosen pictures large for a close look.

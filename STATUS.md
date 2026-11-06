# Status — where we are (updated 2026-11-05)

Read `CLAUDE.md` first (it is the spec), then this file. Branch: `feature/worksheets`.

## Done
- **Milestones 1–3** (CLAUDE.md §13): package, models, syllabus YAML for EN 7A, MA 6A and pencil ZI;
  all 10 sheet types with templates; `ws verify` (content, plan and layout checks, contact sheets);
  PDF booklets with cover, progress log and answer keys.
- **Word bank: 120 of ~200 words** in `content/vocab/english.yaml` (file order = introduction order,
  2 new words per page), all with original pictures in `assets/pictures/` and licence entries.
  | Batch | Words | 7A pages | Approved | Commit |
  |---|---|---|---|---|
  | 1 | 1–40 | 1–20 | 2026-11-03 | fa361bd |
  | 2 | 41–80 (incl. 6 color words, drawn as crayons) | 21–40 | 2026-11-03 | 1ba6f36 |
  | 3 | 81–120 (incl. 8 action words) | 41–60 | 2026-11-05 | baf79f9 |
- Generated so far (in `out/`, git-ignored; rebuild with `ws generate`): EN 7A pages 1–60,
  101–112, 141–150, plus samples of MA 6A and ZI.
- `ws verify`: 382 sheets, **0 errors**, 2 expected warnings (color-word pages; the word bank
  covers 60 of 100 new-word pages, so 7A-B/C sheets will change as words are added).
- `uv run pytest`: 99 tests pass.

- **Ducklings reading (EN 6A)** (2026-11-06): `syllabus/english/6A.yaml` (A Word Hunt 1–30, B Little
  Phrases 31–100, C Say a Sentence 101–200); new sheet types `phrase_card` and `sentence_recite`; frames,
  picture colors and who-can-do-what in `content/phrases/english.yaml`; planner `plan_phrases`
  (and `review_from_levels` for 6A-A). Built from the 120 approved words only: pages 1–70,
  101–140, 191–200 (verify 0 errors, 3 expected warnings). 80 new-word pages (71–100, 141–190) wait for
  approved 6A words.

## Next steps
1. **Batch 4** (words 121–160, 7A pages 61–80): draft a table (word, category, sentence) and
   **wait for the user's OK before drawing**. After drawing, run `ws pictures sheet`, look at
   `out/pictures/contact.png`, fix weak pictures, then send the contact sheet and the 7A review sheet.
2. Batch 5 (words 161–200, pages 81–100). That completes 7A-A's word bank.
3. Then generate all of EN 7A, MA 6A, ZI; `ws verify` must pass; build booklets with `ws render --pdf`.
4. `ws vocab stats` is a stub (exits 2); implement it when needed.
5. **6A word batch 1**: draft in `syllabus/drafts/6A-words-batch1.md` (40 words, 80-word target, open
   questions). Wait for the user's OK; then add words with `level: 6A`, draw pictures, and add `can_do`/slot
   entries in `content/phrases/english.yaml` so each new word fits a frame (the planner errors if it doesn't).

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

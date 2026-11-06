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
- **Word bank: Chicks complete, 200 words** in `content/vocab/english.yaml` (file order = introduction order,
  2 new words per page), all with original pictures in `assets/pictures/` and licence entries.
  | Batch | Words | 7A pages | Approved | Commit |
  |---|---|---|---|---|
  | 1 | 1–40 | 1–20 | 2026-11-03 | fa361bd |
  | 2 | 41–80 (incl. 6 color words, drawn as crayons) | 21–40 | 2026-11-03 | 1ba6f36 |
  | 3 | 81–120 (incl. 8 action words) | 41–60 | 2026-11-05 | baf79f9 |
  | 4 | 121–160 (hose for glasses; brown/black crayons; 40 pictures, `draw_7A_batch4.py`) | 61–80 | 2026-11-06 | merged |
  | 5 | 161–200, the last Chicks batch (gray crayon; popcorn/honey `mass`; 40 pictures + neck and pour redrawn, `draw_7A_batch5.py`) | 81–100 | 2026-11-06 | this branch |

  Ducklings Reading (EN 6A) words, `level: 6A`, one new word a page (target 80):
  | Batch | Words | 6A pages | Approved | Commit |
  |---|---|---|---|---|
  | 6A-1 | 40 (12 actions, 5 body, 3 clothes, 5 toys, 5 home, big/little/hot/cold, 6 animals); 36 pictures (`draw_batch4.py`) | 71–100, 141–150 | 2026-11-06 | this branch |
  | 6A-2 | 40 (8 animals, 6 actions incl. "push" for "laugh", 6 food, 3 toys, 5 home, 4 clothes, 5 nature, toe, thumb, family); 40 pictures (`draw_batch5.py`) | 151–190 | 2026-11-06 | merged |

  **Rule (user, 2026-11-06):** the 80 Ducklings words must not be reused as new words in Chicks batches 4–5.
- **Chicks Reading (EN 7A) is complete: 200/200 pages** (2026-11-06). Verify checks the full exposure rules
  (every Chicks word seen ≥ 3 times) with 0 errors; booklets: one per section plus `chicks-reading-level.pdf`
  (202 pages = cover + 200 + log); no answers PDF (Chicks Reading has no answer keys). Ducklings Reading was
  regenerated (it reviews Chicks words). The live free previews are stale for Chicks page 101 and Ducklings
  pages 3, 33, 103, 131: rebuild with `ws preview` and re-upload when the user says so.
- Generated so far (in `out/`, git-ignored; rebuild with `ws generate`): **EN 7A all 200 pages**;
  **EN 6A (Ducklings Reading) all 200 pages**; MA 5A, ZII all; samples of MA 6A and ZI.
- `ws verify`: 0 errors after Chicks batch 5 (regenerate 7A and 6A first; the only expected warnings are
  the color-word pages of Chicks and Ducklings Reading).
- `uv run pytest`: 238 passed (2026-11-06, with Kittens Reading).

- **Ducklings reading (EN 6A)** (2026-11-06): `syllabus/english/6A.yaml` (A Word Hunt 1–30, B Little
  Phrases 31–100, C Say a Sentence 101–200); new sheet types `phrase_card` and `sentence_recite`; frames,
  picture colors and who-can-do-what in `content/phrases/english.yaml`; planner `plan_phrases`
  (and `review_from_levels` for 6A-A).
  Word batch 1 (2026-11-06): pages 1–150 and 191–200 build (160 of 200; verify 0 errors, 3 expected
  warnings). big/little/hot/cold use the `sizes` / `temperatures` tables and a `describe` sentence group;
  Word Hunt takes the least-seen Chicks words first; animal action sentences show the animal only.
  Word batch 2 (2026-11-06): **Ducklings Reading is complete, 200/200 pages**; verify 0 errors, 2 expected
  warnings (color-word pages; Chicks word bank incomplete); every new word seen ≥ 3 times (checked on the
  full level). Booklets: one per section plus `ducklings-reading-level.pdf` (202 pages = cover + 200 + log).
  The live free preview (pages 3, 33, 103, 131) is now stale for
  pages 3, 103 and 131: rebuild it with `ws preview` and re-upload when the user says so.

- **Kittens Reading (EN 4A) is complete: 200/200 pages** (2026-11-06). `syllabus/english/4A.yaml`: A Letter Teams
  1–100 (ten 10-page units: double letters, sh, ch/tch, th/wh, ck, l-, r-, s-blends, teams at the end, word
  families; each unit = 3 parts: familiar words 1–3, one new word a page 4–8, write the team 9–10), B Rhyme Time
  101–140 (pairs, pick of 2, pick of 3, odd one out), C Trace a Sentence 141–200 (6A frames + `more_can` /
  `more_daily`). New sheet types `letter_team`, `rhyme_match`, `sentence_trace`; planner `ws/phonics.py`
  (new words chosen by team, not bank order); hand-checked teams and rhymes in `content/phonics/english.yaml`.
  50 new words (target 50; chart ~225), batches `4A-words-batch1.md` (40) and `batch2.md` (10), approved by the
  orchestrator under the user's delegation; pictures `scripts/pictures/draw_4A_batch1.py`. bat/pan/wig/bug were
  given to Bunnies Reading (replaced by can, jug, rake, crow): once Bunnies words merge, add them to the 4A rhyme
  groups and families (-at, -an, -ig, -ug). Verify 0 errors (1 warning: color-word pages 151–160); booklets:
  three section PDFs + `kittens-reading-level.pdf` (202 pages) + answers for Rhyme Time.

## Next steps
1. Chicks word bank: done (batch 5, 2026-11-06). New words in later levels: plural words go in `plural:` in
   `content/phrases/english.yaml` (stories and phrases then avoid "... is ...").
2. Sentence-sense fixes: done (2026-11-06). Hand-checked `eatable`, `ownable`, `the_only` lists in
   `content/phrases/english.yaml`; story "my"/"I have" frames only for ownable words; `frames_by_word` for
   wash/ride; `tests/test_sentence_sense.py` scans every Chicks + Ducklings sentence. New words in later
   batches must be added to `ownable` / `eatable` by hand when they fit.
3. EN 7A: done. Then generate all of MA 6A, ZI; `ws verify` must pass; build booklets with `ws render --pdf`.
4. `ws vocab stats` is a stub (exits 2); implement it when needed.
5. Ducklings Reading is done (200/200). The live free preview may now differ from the rebuilt pages:
   rebuild with `ws preview` and re-upload only when the user says so.

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
  (later fixes may be overwritten). Chicks batches are `draw_7A_batchN.py`, Ducklings ones
  `draw_batchN.py`; copy the helpers from `draw_7A_batch5.py` (it merges both sets) into a new script.
- `scripts/pictures/zoom.py out.png name …` renders chosen pictures large for a close look.

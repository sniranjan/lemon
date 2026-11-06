# Status — where we are (updated 2026-11-06)

Read `CLAUDE.md` first (it is the spec), then this file. Branch: `feature/worksheets`.

## Done
- **Milestones 1–3** (CLAUDE.md §13): package, models, syllabus YAML for EN 7A, MA 6A and pencil ZI;
  all 10 sheet types with templates; `ws verify` (content, plan and layout checks, contact sheets);
  PDF booklets with cover, progress log and answer keys.
- **Math 4A (Bunnies Math)** (2026-11-06): `syllabus/math/4A.yaml`, 200 pages, A Tracing Numbers to 10 1–40 ·
  B Writing Numbers to 10 41–100 · C Writing Numbers to 20 101–120 · D Writing Numbers to 30 121–140 ·
  E Writing Numbers to 50 141–200, with `standards:`. New sheet types `number_trace` and `number_write`
  (`copy` / `fill`); child text ≥ 28px enforced for this strand (`min_child_px("4A", "math")`). All 200 pages
  verify with 0 errors; booklets `bunnies-math-level.pdf` (202 pages) + `-answers.pdf` (pages 41–200).
- **Math 5A (Ducklings math)**: `syllabus/math/5A.yaml`, 200 pages, sections A–E with `standards:`.
  `number_read` gained `show: ten_frames | rods` (11–30 as ten-frames, 51–100 as tens bars);
  new `number_sequence` (tracks with gaps to say aloud). All 200 pages verify with 0 errors.
- **Math 3A (Kittens math, 200 pages)** (2026-11-06): `syllabus/math/3A.yaml`, sections A What Comes Next to 100
  (1–60) · B What Comes Next to 120 (61–70) · C Plus One (71–130) · D Plus Two (131–160) · E Plus Three
  (161–180) · F Plus One, Two or Three (181–200), with `standards:` and per-section SCT. New sheet types
  `next_number` and `add_facts` (general: `op`, `addend`/`second`, `min_first`/`max_first`, `new_from`,
  `rows`, `bridge`; C shows "n → box" above "n + 1 = box"). `max_first` follows CLAUDE.md §5 (sums up to the
  chart's number: "up to 14+2" = `max_first: 12`). All 200 pages verify with 0 errors; booklets per
  section + `kittens-math-level.pdf` (202 pages) and `-answers.pdf` files. The Kittens free preview waits
  for Kittens Reading.
- **Puppies Math (M1, our own level, 200 pages)** (2026-11-06): `syllabus/math/M1.yaml`, adding and taking-away
  facts within 20 (1.OA.4–8, 2.OA.2): A Adding Warm-Up 1–10 · B Adding 4 and 5 11–40 · C Adding 6 and 7 41–70 ·
  D Adding 8, 9 and 10 71–100 · E Adding Mix 101–110 · F Taking Away 1, 2, 3 111–130 · G Taking Away 4, 5, 6 131–150 ·
  H Taking Away 7 to 10 151–170 · I Add or Take Away 171–180 · J Missing Numbers and Families 181–200.
  New sheet type `fact_drill` (layouts horizontal / vertical / bridge number tracks / fact-family houses), tests in
  `tests/test_math_M1.py`. All 200 pages verify with 0 errors; booklets per section + `puppies-math-level.pdf`
  (202 pages) and `-answers.pdf` files. Free preview (pages 1, 61, 111, 191) built with Puppies Reading (`ws preview puppies`; not uploaded yet).
  Kept separate from Kittens' `add_facts` on purpose; reconcile when the branches merge.
- **Puppies Reading (EN 3A, 200 pages)** (2026-11-06): `syllabus/english/3A.yaml`, A Word Patterns 1–70 (7 parts:
  letter pairs, magic e, ai/ay, ee/ea, oa/ow/igh, bossy r, ou/ow/oi/oy/oo) · B Word Endings 71–110 (plurals, -ing, -ed,
  take it off) · C Clap the Parts 111–140 (compound, closed, count 1–3) · D Copy a Sentence 141–200 (3–8 words, asking
  sentences in part 3), with `standards:` (RF.1.3a–f, RF.2.3a–d, L.1.4c, RF.1.1a, L.1.1a/j, L.1.2b/d, L.2.2d).
  New sheet types `pattern_words`, `word_endings`, `syllable_split`, `sentence_copy`; planner `plan_spelling`
  (rule `known_levels: [7A, 6A]` pins the review pool, so other strands' words never change these pages);
  hand-checked tables in `content/phonics/english.yaml`. 70 new words (one a page in A; batches 3A-1 40 words and
  3A-2 30 words, `syllabus/drafts/3A-words-batch*.md`, approved under user delegation), 70 pictures
  (`draw_3A_batch1.py`, `draw_3A_batch2.py`). After Kittens Reading merged, 10 words it owns (shark, wheel, beach,
  couch, tooth, shower, snake, tray, crow, jar) were swapped for shampoo, teacher, chimney, chest, thread, shed, lake,
  spray, mower, guitar (batch 3A-3, `draw_3A_batch3.py`); the Puppies tables follow Kittens' in the shared
  `content/phonics/english.yaml`, and the Puppies code is `ws/spelling.py` (Kittens' is `ws/phonics.py`). Verify 0 errors, every word seen ≥ 3 times; booklets per section +
  `puppies-reading-level.pdf` (202 pages) and `-answers.pdf` (A–C). Free preview pages 3, 85, 113, 143.
- **Foxes Math (M3, our own level, grade 3 work, 200 pages)** (2026-11-06): `syllabus/math/M3.yaml`:
  A Big Adding & Taking Away 1–30 (3.NBT.2) · B Times Tables 2, 5, 10 31–60 · C Times Tables 3 and 4 61–90 ·
  D Times Tables 6 to 9 91–140 (3.OA.1/4/5/7) · E Sharing Facts 141–170 (3.OA.2/4/6/7) · F Fractions on a Line
  171–190 (3.NF.1–2; denominators 2, 3, 4, 6, 8 only) · G Story Problems 191–200 (3.OA.3, 3.OA.8). New sheet types
  `fraction_line`, `story_problem` (33 frames in `content/math/story_problems.yaml`, copy in test fixtures); Cubs'
  `column_arithmetic` serves section A too (new optional rules `regroup_counts`, `across_zero`, `title`, 9 a page;
  Cubs output unchanged); `fact_drill` gained × and ÷ (`skip`, `arrays`, `pairs`, × ÷ `families`) with Puppies output
  byte-identical. Tests in `tests/test_math_M3.py`. All 200 pages verify with 0 errors and 0 warnings; booklets per
  section + `foxes-math-level.pdf` (202 pages) and `foxes-math-level-answers.pdf` (10 pages). Child text stays
  ≥ 28px (the 20px floor wasn't needed). Free preview pages 1, 31, 141, 171 wait for Foxes Reading.
- **Otters Math (M5, our own level, grade 5 work, 200 pages)** (2026-11-06): `syllabus/math/M5.yaml`:
  A Long Division 1–40 (5.NBT.6: divide by tens, 2-digit divisors, 2-digit answers, 4-digit dividends) ·
  B Unlike Fractions 41–90 (5.NF.1: related denominators, then unrelated, then mixed numbers) · C Fractions Times
  Fractions 91–120 (5.NF.4: whole × fraction, area model, fraction × fraction) · D Decimals in Columns 121–160
  (5.NBT.3–4, 5.NBT.7: place value page, then add/take away with points lined up) · E Decimals Times and Shared
  161–190 (5.NBT.2, 5.NBT.7) · F Parentheses and Volume 191–200 (5.OA.1, 5.MD.3–5; pages alternate). Section A reuses Owls'
  `division_house` (new optional rule `divisor_multiple_of`; Owls output unchanged). New sheet types `fraction_ops`, `decimal_place_value`,
  `decimal_column`, `decimal_ops`, `order_of_operations`, `box_volume`; exact helpers in `ws/sheet_types/_exact.py`
  (items store ints / canonical decimal strings; `Fraction` and `Decimal` only for computing). Tests in
  `tests/test_math_M5.py`. All 200 pages verify with 0 errors and 0 warnings; booklets per section +
  `otters-math-level.pdf` (202 pages) and `otters-math-level-answers.pdf` (12 pages). Answers with a remainder read
  "36 R 12" (R5 alone is a banned internal code). Free preview pages 21, 61, 131, 192 wait for Otters Reading.
- **Owls Math (M4, our own level, grade 4 work for age 7, 200 pages)** (2026-11-06): `syllabus/math/M4.yaml`:
  A Warm-up 1–20 (4-digit adding and taking away, 4.NBT.4) · B Multiply by One Digit 21–60 (in parts, then 2-, 3-,
  4-digit × 1 digit with carry boxes) · C Two-by-Two 61–100 (× tens, then 2-digit × 2-digit in two lines; the line-two
  0 printed in parts 2–3, written by the child in part 4) (4.NBT.5) · D Long Division 101–150 (division house; even,
  remainders, first digit too small, 0 inside the answer, 4-digit two a page) (4.NBT.6) · E Factors and Multiples 151–170
  (factor pairs, count in multiples, circle multiples, prime or composite) (4.OA.4) · F Fraction Friends 171–200 (fraction
  bars, equivalent fractions incl. tenths → hundredths, like-denominator adding and taking away within one whole)
  (4.NF.1, 4.NF.3, 4.NF.3a). New sheet types `long_multiplication`, `division_house`, `factor_pairs`, `fraction_bars`;
  `column_arithmetic` puts 4-digit problems 2 a row (Cubs/Foxes output unchanged). Tests `tests/test_math_M4.py`.
  All 200 pages verify with 0 errors and 0 warnings; booklets per section + `owls-math-level.pdf` (202 pages) and
  `owls-math-level-answers.pdf` (14 pages). Child text ≥ 28px. Free preview pages 21, 71, 121, 171 wait for Owls Reading.
  ≥ 28px (the 20px floor wasn't needed). Free preview pages 1, 31, 141, 171: with Foxes Reading built, `ws preview foxes` now builds `out/previews/foxes.pdf` locally (10 pages; not uploaded).
- **Foxes Reading (R3, our own level, grade 3 reading, 200 pages)** (2026-11-06): `syllabus/english/R3.yaml`:
  A Why They Did It 1–50 (RL.3.3) · B Word Builders 51–90 (un-, re-, -ful, -less, then compound words; L.3.4b,
  RF.3.3a; compounds are the L.2.4d on-ramp) · C Fables and Their Lessons 91–130 (RL.3.2) · D Why Did They? 131–170
  (RL.3.3) · E Say It in a Sentence 171–200 (RL.3.1, L.3.1i; part 1 prints sentence starters). 80 original passages
  (`content/passages/R3/`, 2 pages each, 120–150 words, Flesch-Kincaid 2.5–4.5 by `ws/readability.py`; 6 fables
  retell classic public-domain ideas in our words) and 66 word builders (`content/wordparts/R3.yaml`); drafts
  `syllabus/drafts/R3-passages.md`, `R3-words.md` are generated by `scripts/r3_drafts.py` (approved by the
  orchestrator under the user's delegation). New sheet types `passage_questions`, `word_builder`,
  `full_sentence_answer` (planner `passages` in `ws/passages.py`); child text 20px (`min_child_px` for R levels);
  answers PDF lists one line per answer (level rule `answers: by_line`). All 200 pages verify with 0 errors and
  0 warnings; booklets per section + `foxes-reading-level.pdf` (202 pages) + answers. `daily_pages: 2` (ours).
- **Pandas Reading (R6, our own level, grade 6 reading for age 9, 200 pages)** (2026-11-06): `syllabus/english/R6.yaml`:
  A Central Idea 1–50 (RI.6.2, objective summaries) · B Reading Between the Lines 51–100 (inference with cited
  evidence, RL.6.1 / RI.6.1) · C Why Was It Written? 101–140 (purpose and point of view, RI.6.6, RL.6.6, RI.6.8) ·
  D How It's Built 141–170 (cause/effect, compare/contrast, problem/solution; how a paragraph fits, RI.6.5) ·
  E Short Written Answers 171–200 (two 3–4-sentence answers with a quote, W.6.9, W.6.1). 52 original passages
  (`content/passages/R6/`, 305–354 words, Flesch-Kincaid 5.5–7.5; 37 nonfiction, 15 stories), each read on one
  or two two-page spreads. New sheet type `passage_spread` (`ws/spreads.py`): page 1 the passage (numbered
  paragraphs; a Letter page holds ~300 words at the 20px floor, so the end continues at the top of page 2, split at a
  sentence), page 2 the questions: `mc` (A–D), `quote` (exact text choices), `write`, `paragraph` (sample + rubric in
  the key), `organizer` (Cause / Effect boxes). Planner: `plan_passages` with rule `spread: true` (Foxes unchanged).
  Draft record `syllabus/drafts/R6-passages.md` from `scripts/r6_drafts.py` (approved by the orchestrator under the
  user's delegation). Verify 0 errors, 0 warnings; booklets per section + `pandas-reading-level.pdf` (202 pages) and
  `pandas-reading-level-answers.pdf` (29 pages; level rule `answers_height`). Preview pages 1–2 and 171–172 (two whole spreads); `ws preview pandas` builds `out/previews/pandas.pdf` (10 pages, with Pandas Math; not uploaded).
- **Lions Math (M8, our own level, grade 8 work for age 11, 200 pages)** (2026-11-06): `syllabus/math/M8.yaml`:
  A Exponents and Square Roots 1–30 (8.EE.1–2, 8.NS.2) · B Very Big and Very Small 31–50 (8.EE.3–4) · C Multi-Step
  Equations 51–100 (8.EE.7a–b) · D Lines and Slope 101–150 (8.EE.5–6, 8.F.1–4) · E Two Equations at Once 151–180
  (8.EE.8a–c) · F Right Triangles 181–200 (8.G.6–8). New sheet types `power_root`, `sci_notation`, `pythagorean`;
  multi-step equations are `equation_solve` `mode: multi_step`, lines and systems are `coordinate_grid` `mode: lines` /
  `systems` (Pandas output byte-identical; a `template_for(sheet)` hook in the registry picks the mode's template).
  Exact helpers `ws/sheet_types/_algebra.py` + `templates/_lions_algebra.html.j2` (tokens, stacked fractions, SVG grid);
  system story frames `content/math/systems.yaml` (copy in test fixtures). Letters a, m, r never used (2a, m8, r5
  would read as codes). Child text ≥ 20px (`min_child_px`). Tests `tests/test_math_M8.py`. All 200 pages verify with
  0 errors and 0 warnings; booklets per section + `lions-math-level.pdf` (202 pages) and
  `lions-math-level-answers.pdf` (16 pages); no internal codes in PDF text. Free preview pages 11, 61, 131, 181 wait
  for Lions Reading.
- **Pandas Math (M6, our own level, grade 6 work for age 9, 200 pages)** (2026-11-06): `syllabus/math/M6.yaml`:
  A Dividing Fractions 1–30 (6.NS.1) · B Ratios and Rates 31–70 (6.RP.1, 6.RP.2, 6.RP.3a/b/d) · C Percents 71–100
  (6.RP.3c) · D Below Zero 101–130 (6.NS.5–8) · E Letters for Numbers 131–170 (6.EE.1, 6.EE.2a/c) · F One-Step
  Equations 171–200 (6.EE.5, 6.EE.7); codes checked on thecorestandards.org. Dividing fractions extends Otters'
  `fraction_ops` (`op: div`, layouts `model` with fraction bars and `list`; Otters output byte-identical). New sheet types `ratio_table`, `rational_story` (frames in `content/math/rational_stories.yaml`, contexts in `ratios.yaml`; copies in
  test fixtures), `percent_problem`, `signed_numbers`, `coordinate_grid`, `expression_eval`, `equation_solve`, sharing
  exact-number helpers in `ws/sheet_types/_rational.py` (Fraction parse/format/evaluate, `pretty` printing; Jinja
  filters `frac_parts`, `minus`, `pretty`). Grade 6 only: no adding/taking away negatives, all equation numbers
  nonnegative. Child text ≥ 22px (`min_child_px` M6). Tests in `tests/test_math_M6.py` (18 goldens). All 200 pages verify with
  0 errors and 0 warnings; booklets per section + `pandas-math-level.pdf` (202 pages) and
  `pandas-math-level-answers.pdf` (14 pages). Free preview pages 11, 51, 121, 171 wait for Pandas Reading.
- **Penguins Math (M7, our own level, grade 7 work for age 10, 200 pages)** (2026-11-06): `syllabus/math/M7.yaml`:
  A Adding and Subtracting Negatives 1–40 (7.NS.1a–d) · B Multiplying and Dividing Negatives 41–70 (7.NS.2a–c) ·
  C All Kinds of Numbers 71–100 (7.NS.1d, 2c, 2d, 3) · D Proportions and Percent Change 101–140 (7.RP.1, 2a–c, 3) ·
  E Tidy Expressions 141–170 (7.EE.1–2) · F Two-Step Equations and Inequalities 171–200 (7.EE.3, 4a, 4b); 10-page parts
  (`source: ours`). No new sheet types: modes of the Pandas types, Pandas/Otters output byte-identical:
  `signed_numbers` `layout: operations` (`_signed_ops.py`), `rational_story` with 68 new frames (tags signed_story,
  fraction_rate, percent_change, money_percent, two_step_story, inequality_story; `signed`, percent, step ranges,
  floor/ceil), `ratio_table` `mode: proportional` (`_proportional.py`), `expression_eval` `task: tidy` (`_tidy.py`),
  `equation_solve` `mode: two_step` (`_two_step.py`, inequalities graphed on a number line). Exact numbers and a tiny
  linear-expression type in `ws/sheet_types/_linear.py`; `SheetType.template_for(sheet)` lets a mode use its own
  template. Child text ≥ 20px (`min_child_px("M7")`). Tests `tests/test_math_M7.py`. All 200 pages verify with 0 errors,
  0 warnings; booklets per section + `penguins-math-level.pdf` (202 pages) and `penguins-math-level-answers.pdf`
  (15 pages). Preview pages 1, 45, 121, 191 (wait for Penguins Reading).
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
  **EN 6A (Ducklings Reading) all 200 pages**; MA 5A, MA 4A, MA 3A, MA M1, **MA M2 (Cubs Math)**, **MA M3 (Foxes Math)**, **MA M4 (Owls Math)**, **MA M5 (Otters Math)**, **MA M6 (Pandas Math)**, **MA M7 (Penguins Math)**, **MA M8 (Lions Math)**, **EN 5A (Bunnies Reading)**, **EN 4A (Kittens Reading)**, **EN 2A (Cubs Reading)**, ZII all; samples of MA 6A and ZI.
- `ws verify`: 0 errors (regenerate a level after content changes; expected warnings: color-word pages).
- `uv run pytest`: see the latest merge commit.
- **Cubs Reading (EN 2A) is complete: 200/200 pages** (2026-11-06). `syllabus/english/2A.yaml`, with `standards:`:
  A Picture Puzzles 1–60 (missing letters, then little crosswords) · B Kinds of Words 61–150 (naming / doing /
  describing words: pick, sort, fill in) · C Read Aloud 151–200 (25 original passages of 43–60 words, each read on
  two pages with different questions). New sheet types `word_puzzle`, `word_sort`, `read_aloud`; planner
  `ws/reading.py` (`plan_reading`, picked up by rules `puzzle` / `word_kinds` / `passage_words`); hand-checked word
  kinds, fill-in sentences and puzzle words in `content/grammar/english.yaml`; passages in
  `content/passages/english.yaml`. Word batch 2A-1 (40 words: 16 naming, 12 doing, 12 describing; one new a page on
  61–100; drafts `syllabus/drafts/2A-words-batch1.md`, `2A-passages.md`, approved under user delegation) and 28
  pictures (`draw_2A_batch1.py`). Verify 0 errors, 0 warnings; every new word seen ≥ 3 times; booklets
  `cubs-reading-level.pdf` (202 pages) + `-answers.pdf` and one pair per section. Preview pages 5, 45, 95, 155: the
  Cubs free preview waits for Cubs Math (M2). Tests: `tests/test_english_2A.py`; the sentence scan covers Cubs text.

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

- **Cubs Math (math M2, our own level)** (2026-11-06): `syllabus/math/M2.yaml`, 200 pages, sections A–H
  (Tens and Ones 1–20 · Hundreds, Tens and Ones 21–50 · Counting by 5s, 10s and 100s 51–70 · Adding Ones 71–90 ·
  Adding Two-Digit Numbers 91–130 · Taking Away Two-Digit Numbers 131–170 · Big Number Adding and Taking Away
  171–190 · Story Problems 191–200), standards 1.NBT.2 (on-ramp), 2.NBT.1–7, 2.OA.1. New sheet types
  `place_value`, `skip_count`, `column_arithmetic`, `math_story` (frames in `content/math/stories.yaml`).
  All 200 pages verify with 0 errors; booklets: one per section plus `cubs-math-level.pdf` (202 pages) and
  answers PDFs (`cubs-math-level-answers.pdf`, 10 pages). `ws preview` for Cubs needs Cubs Reading first.
- **Bunnies Reading (EN 5A)** (2026-11-06): `syllabus/english/5A.yaml`: A Letter Trails 1–70 (letters in
  stroke order: l i t · c o a d g · r n m h b p · u y v w x k z · e s f j q, 2 pages each + group reviews),
  B Sound Pieces 71–150 (short a/e/i/o/u, rhyming families, then one new word a page), C Letter Pairs
  151–160 (capital + small, a–z, then b/d/p), D Word Trails 161–200. New sheet types `letter_trace`,
  `sound_parts`, `word_trace`; dotted letters come from our own single-stroke trace font (`ws/trace_font.py`);
  planner `plan_letters` (rule `planner: letters`) with the hand-checked lists in `content/sounds/english.yaml`.
  Word batch 5A-1 (23 words: queen, quilt, zipper + 20 short-vowel words; approved 2026-11-06 by the
  orchestrator under the user's delegation; `draw_5A_batch1.py`, which also redraws **hat** as a straw sun hat
  so it no longer looks like a cap): **Bunnies Reading is complete, 200/200 pages**, verify 0 errors and 0 warnings,
  every new word seen at least 3 times. Optional words in the draft (igloo, otter, ox, vest, vase, yarn) are not approved.
  `ws generate` now skips pages that still wait for words (with a note) for `--pages` and `--count` too.
  Booklets: one per section plus `bunnies-reading-level.pdf` (202 pages = cover + 200 + log).
  The hat redraw changes how Chicks and Ducklings pages with "hat" look: rebuild their booklets and the live previews when convenient.
- **Kittens Reading (EN 4A) is complete: 200/200 pages** (2026-11-06). `syllabus/english/4A.yaml`: A Letter Teams
  1–100 (ten 10-page units: double letters, sh, ch/tch, th/wh, ck, l-, r-, s-blends, teams at the end, word
  families; each unit = 3 parts: familiar words 1–3, one new word a page 4–8, write the team 9–10), B Rhyme Time
  101–140 (pairs, pick of 2, pick of 3, odd one out), C Trace a Sentence 141–200 (6A frames + `more_can` /
  `more_daily`). New sheet types `letter_team`, `rhyme_match`, `sentence_trace`; planner `ws/phonics.py`
  (new words chosen by team, not bank order); hand-checked teams and rhymes in `content/phonics/english.yaml`.
  50 new words (target 50; chart ~225), batches `4A-words-batch1.md` (40) and `batch2.md` (10), approved by the
  orchestrator under the user's delegation; pictures `scripts/pictures/draw_4A_batch1.py`. bat/pan/wig/bug were
  given to Bunnies Reading (replaced by can, jug, rake, crow); after the merge "can" became "man" (so "can"
  is only the verb) and the Bunnies words joined the families and rhyme groups (-at, -an, -ig, -ug, -ap, -un,
  new -et, -op, -en, -in). Trace a Sentence: `level_word_first` makes each page's first sentence use a Kittens
  word (ship, pretzel, swan) when one fits. Verify 0 errors (1 warning: color-word pages); booklets:
  three section PDFs + `kittens-reading-level.pdf` (202 pages) + answers for Rhyme Time.

- **Whales Math (M9, our own level, grade 9 / Algebra 1 work for age 12, 200 pages)** (2026-11-06):
  `syllabus/math/M9.yaml`: A Powers and Roots 1–30 (exponent rules, rational exponents, simplifying radicals;
  N-RN.A.1–2, part 1 also 8.EE.1 as an on-ramp) · B Lines and Inequalities 31–70 (write y = mx + b from tables,
  points and situations; graph lines; solve and graph one-variable inequalities; graph two-variable inequalities
  with shading; A-CED.A.2, F-LE.A.2, F-IF.B.6, F-IF.C.7a, A-REI.D.10, A-REI.B.3, A-REI.D.12) · C Polynomial
  Operations 71–110 (add/subtract, distribute, FOIL rows, box method; A-APR.A.1) · D Factoring 111–150 (GCF,
  x² + bx + c, leading 2/3/5, difference of squares; A-SSE.A.2, A-SSE.B.3a) · E Solving Quadratics 151–200
  (factoring, square roots, the formula with rational then radical answers, choose a method + area story;
  A-REI.B.4b). Standards checked on thecorestandards.org (written `N-RN.A.1` for the site's `HSN.RN.A.1`).
  Exact algebra kit `ws/algebra.py` (Poly with a small ASCII parser, Mono with rational exponents, radicals,
  quadratic roots (p ± q√d)/s checked in Q(√d)); new sheet types `exponent_rules`, `slope_intercept`,
  `inequality_line`, `polynomial_ops`, `polynomial_factoring`, `quadratic_solve`; graphing lines and inequalities
  extends Pandas' `coordinate_grid` (rule `graphs`, `ws/sheet_types/_slope_lines.py`; Pandas output byte-identical).
  Situations in `content/math/algebra_stories.yaml` (copy in test fixtures). Variables are never `a` and the
  general quadratic formula is never printed (digit + a would read as an internal code). Tests
  `tests/test_math_M9.py` (19 goldens). Verify 0 errors, 0 warnings; booklets per section + `whales-math-level.pdf`
  (202 pages) and `whales-math-level-answers.pdf` (27 pages). Preview pages 1, 41, 121, 181 wait for Whales Reading.

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
- Foxes Reading: is 2 passage pages a day right for age 6 (the default elsewhere is 5)? Should the 4 sections of
  passages be read in order, or interleaved with Word Builders? (Today: in order.)
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

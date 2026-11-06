# CLAUDE.md — Home Worksheet Generator ("our Kumon-style programme")

## 1. What this project is

A small command-line tool that **generates, verifies and prints daily practice worksheets** for a
young child (starting age 3–4), following the *structure and progression* of the Kumon English
and Math syllabus (levels, page ranges, skill sequence) but with **entirely our own sheets**:
our words, our sentences, our pictures, our layout.

The child works through the levels at his own pace: about 5 pages a day, with a grown-up
beside him for the early levels. The tool's job is to make it cheap to produce the *next* batch
of good sheets on demand, for example:

> "Generate 20 more English 7A section A sheets"
> "Make all of Math 6A"
> "Add a new sheet type for 6A Simple Phrases"

### Goals (in priority order)
1. **Correct and age-appropriate.** Every sheet must pass automated verification before it
   is considered done (see §8). A sheet with a wrong count, a missing picture or overflowing
   text is a bug.
2. **Extensible by data, not code.** Adding a level, section, word list or sheet type should
   mostly mean editing YAML, plus at most one small template or generator.
3. **Deterministic.** The same command + seed always produces byte-identical output.
4. **Printable.** US Letter, black-and-white friendly, large type, one sheet = one page.
5. **Repetition built in.** Words and numbers recur on purpose; the generator tracks exposure.

### Non-goals (cut on purpose)
- No web app, accounts, database or progress-tracking UI. A printable progress log page is enough.
- No copying of Kumon material. See §2.
- No AI image generation at build time. Pictures are static SVG files in the repo (§6).

---

## 2. Hard rules (never break these)

- **Never reproduce Kumon worksheets, wording, illustrations, sheet codes, logos or the word
  "Kumon" on any output.** We follow the published *syllabus structure* only (level names,
  page ranges, section topics, aims). All content is original.
- Sheet IDs use our own scheme: `EN-7A-A-001`, `MA-6A-B-014`, `ZI-A-003`.
- Content must suit ages 3–12 (topics fit the level's age band): no scary, violent or brand-name content; everyday
  objects, animals, food, family, home, nature, transport.
- **American spelling and words for all text a child or parent sees** (color, mom, diaper,
  coloring). Code, file names, YAML keys and sheet type names may keep British spelling
  (e.g. `colouring`).
- Every picture in `assets/pictures/` must have a recorded source and licence in
  `assets/pictures/LICENSES.yaml` (either "original" or an open licence such as CC-BY with attribution).
- Never mark a task done unless `ws verify` passes on everything that was generated.

---

## 3. Tech stack

- Python 3.11+, run with `uv` (or a plain venv).
- `pydantic` for schemas, `PyYAML` for content, `Jinja2` for HTML templates.
- `playwright` (Chromium) to render HTML → PDF and to run layout checks.
- `pypdf` to merge per-sheet PDFs into booklets (with fixed metadata, so output is byte-identical).
- `pytest` for tests.
- CLI entry point: `ws` (via `[project.scripts]` in `pyproject.toml`), built with `typer`.

---

## 4. Repository layout

```
lemon/                           # repo root
  CLAUDE.md
  pyproject.toml
  syllabus/                      # WHAT to teach (structure), one file per subject+level
    pencil/ZI.yaml ZII.yaml
    english/7A.yaml 6A.yaml 5A.yaml 4A.yaml 3A.yaml 2A.yaml
    math/6A.yaml 5A.yaml 4A.yaml 3A.yaml 2A.yaml     # math starts at 6A
  content/                       # the raw material (our own)
    vocab/english.yaml           # word bank: word, picture, category, level, sentences
    phrases/english.yaml         # 6A+ phrases and sentence frames
    stories/english.yaml         # short word stories / passages
    math/objects.yaml            # countable objects for math sheets (→ pictures)
  assets/
    pictures/<slug>.svg          # one picture per word/object
    pictures/LICENSES.yaml
    fonts/                       # Andika (OFL), self-hosted
  ws/                            # the package
    cli.py
    models.py                    # pydantic models for syllabus, content, Sheet
    registry.py                  # sheet-type registry (plugin pattern, §7)
    sheet_types/                 # one module per sheet type: generate() + template name
    templates/                   # Jinja2: base.html.j2 + one partial per sheet type
    render.py                    # HTML → PDF, booklet assembly
    verify/                      # content checks + layout checks
    exposure.py                  # tracks how often each word/number has appeared
  out/                           # generated output (git-ignored)
    english/7A/A/EN-7A-A-001.html …
    english/7A/chicks-reading-pages-001-020.pdf   # buyer-facing files use public names (§15)
    previews/chicks.pdf                           # free preview PDFs (ws preview)
    manifest.jsonl               # one line per generated sheet (id, seed, items, checks)
  tests/
```

---

## 5. Core concepts and data model

**Subject → Level → Section → Sheet type → Sheet**

- **Level**: e.g. English `7A`. It has aims, a target vocabulary size, a daily page target and
  an optional SCT (standard completion time per page).
- **Section**: a contiguous page range in a level with one learning focus, e.g. 7A pages
  1–100 "Familiar Words". Each section gets a **letter code (A, B, C…) in page order**, so
  "7A type A" means section A of 7A.
- **Sheet type**: a reusable layout + generator (e.g. `word_picture_pair`,
  `count_and_say`). One section uses one or more sheet types; one sheet type can serve
  many sections and levels.
- **Sheet**: one generated page with a stable ID, its seed, its items and a parent tip.

### `syllabus/english/7A.yaml` (example; all levels follow this shape)
```yaml
subject: english
level: 7A
title: Repeating familiar words
aims:
  - Repeat familiar words and everyday expressions while looking at them
  - Introduce ~200 words, each seen at least 3 times
pages: 200
daily_pages: 5
sct_minutes_per_page: null
vocab_target: 200
sections:
  - code: A
    name: Familiar Words
    pages: [1, 100]
    sheet_types: [word_picture_pair, word_picture_sentence]   # pages cycle through this list
    rules:
      new_words_per_sheet: 2
      max_word_length: 7
      say_it_again: { count: 2, sheets_back: [3, 10] }   # small review strip; omitted on pages 1–3
    parts:   # a part can narrow the sheet types: pairs only until the routine is familiar
      - { part: 1, pages: [1, 20],   sheet_types: [word_picture_pair] }
      - { part: 2, pages: [21, 100], sheet_types: [word_picture_pair, word_picture_sentence] }
  - code: B
    name: Familiar Words Review
    pages: [101, 140]
    sheet_types: [review_grid_4]
    rules: { review_from_sections: [A] }
  - code: C
    name: Word Stories
    pages: [141, 200]
    sheet_types: [word_story]
    rules: { sentences_per_story: [2, 4], only_known_words: true }
```

### `syllabus/math/3A.yaml` (excerpt — sections can carry 10-page `parts`)
```yaml
subject: math
level: 3A
pages: 200
sections:
  - code: C
    name: Adding 1
    pages: [71, 130]
    sheet_types: [add_facts]
    sct_minutes_per_page: [1, 2]
    parts:
      - { part: 1, pages: [71, 80],   rules: { addend: 1, max_first: 11 } }    # up to 12+1
      - { part: 2, pages: [81, 90],   rules: { addend: 1, max_first: 17 } }    # up to 18+1
      - { part: 3, pages: [91, 100],  rules: { addend: 1, max_first: 23 } }
      - { part: 4, pages: [101, 110], rules: { addend: 1, max_first: 29 } }
      - { part: 5, pages: [111, 120], rules: { addend: 1, max_first: 59 } }
      - { part: 6, pages: [121, 130], rules: { addend: 1, max_first: 999 } }   # up to 1000+1
```
Rules merge **level → section → part**, later ones winning. A part may also set its own
`sheet_types`. When a section or part lists several sheet types, pages cycle through the
list in order (list a type twice to weight it). `--part N` selects one part; otherwise pages
map to parts by page number. Values we chose ourselves (not from the published chart) carry
`source: ours`.

**Sheet IDs** number pages *within the section*: 7A page 101 is `EN-7A-B-001`. Pencil sheets
drop the subject prefix (`ZI-A-003`). Variants after the first add a suffix (`EN-7A-A-001-v2`).
**Seeds** are the first 8 bytes of `sha256("subject|level|section|page|variant")`, never Python's `hash()`.

**Planning is level-wide.** Before generating, the planner builds a schedule for the whole
level (which words are new on which page, which go in each "Say it again" strip, review grid
and story). Each page is then built from that plan, so `--pages 51-100` gives the same sheets
whether or not pages 1–50 exist yet.

### `content/vocab/english.yaml`
```yaml
- word: apple
  picture: apple            # → assets/pictures/apple.svg (must exist)
  category: food
  level: 7A                 # level that introduces it
  sentences: ["I like the red apple.", "The apple is sweet."]
  # optional: mass: true        → stories say "some" (milk, grapes, pants)
  # optional: needs_color: true → color words; verify warns and booklet covers ask for color printing
```

### Sheet (in-memory / manifest)
```
id, subject, level, section, sheet_type, page_number, seed,
title, parent_tip, items[], answer_key (if any), new_words[], review_words[]
```

---

## 6. Pictures (the real bottleneck)

7A alone needs ~200 pictured words. Pictures are therefore a first-class workstream.

- Style: simple flat illustration, **thick dark outline (3px at 100×100 viewBox)**, flat
  **mid-tone** fill, no text inside, no gradients, recognizable in grayscale.
- **Fill lightness**: the main fill (the most common color after the dark outline) must be
  **50–75% lightness in grayscale**, measured as `0.2126 R + 0.7152 G + 0.0722 B` (the CSS
  `grayscale()` weights). Pastels are too light and vanish in black and white.
  `ws pictures sheet` measures every picture on a real render and flags any outside the range.
- **Color words** (red, blue, ...) are pictured as crayons in true hues, marked
  `kind: color_swatch` in `LICENSES.yaml`; they are exempt from the lightness rule.
- Format: SVG, `viewBox="0 0 100 100"`, no `<style>`, no scripts, no embedded rasters.
- Sources, in order of preference: (1) original SVGs drawn by Claude Code in the house
  style; (2) open-licence sets (e.g. OpenMoji CC BY-SA 4.0), recorded in `LICENSES.yaml`.
- `ws pictures missing --subject english --level 7A` lists words with no SVG.
- `ws pictures draw <slug>…` is a *Claude Code task*, not code: draw the SVG, save it,
  add the licence entry, then run `ws pictures sheet` to make a contact sheet (PNG grid of
  all pictures) for a human to eyeball.
- Grow the word bank in batches (e.g. 40 words at a time) so pictures and words stay in sync.

---

## 7. Sheet types (plugin registry)

Each sheet type is a module in `ws/sheet_types/` registered with a decorator:

```python
@register("word_picture_pair")
class WordPicturePair(SheetType):
    template = "word_picture_pair.html.j2"
    def generate(self, ctx: GenContext) -> SheetContent: ...
    def verify(self, sheet: Sheet) -> list[Issue]: ...   # type-specific checks
```

`GenContext` gives the generator the level/section rules, a seeded RNG, the content banks
and the exposure tracker. **Adding a sheet type = one module + one template partial + one
test.** Nothing else in the code should change.

### Initial catalogue (build these first; add more as levels are reached)

| Sheet type | Used in | What the child does |
|---|---|---|
| `word_picture_pair` | EN 7A-A | 2 big picture+word cards (the 2 new words), says each word back; "Say it again" strip |
| `word_picture_sentence` | EN 7A-A | 2 cards of picture + word + short sentence read aloud together; "Say it again" strip |
| `review_grid_4` | EN 7A-B, 6A-A | 4 known pictures+words; "find it" game |
| `word_story` | EN 7A-C | 1 picture, 2–4 short sentences using known words |
| `phrase_card` | EN 6A-B | 3 cards of picture(s) + 2–3 word phrase ("a red apple", "mom and dad"), built from frames in `content/phrases/english.yaml` |
| `sentence_recite` | EN 6A-C | 2 blocks (3 on new-word pages) of picture(s) + one sentence ("The dog can run."), each with 3 circles to color, one per recitation |
| `letter_trace` | EN 5A-A/C | One letter (big copies + practice rows) with two picture words that start with its sound; or review rows of 3 letters (with capitals in 5A-C) |
| `sound_parts` | EN 5A-B | 3 cards: picture + short-vowel word split into onset + rime boxes ("c" "at"), then the whole word; rhyme pages show one family |
| `word_trace` | EN 5A-D | 3 pictures, each with its word (solid) and the same word dotted to trace |
| `colouring` | ZI-A | Simple outline shape to colour inside |
| `line_path` | ZI-B/C, ZII-A…D | Draw from a start dot along a lane to what's at the end. ZI: straight, then curved lanes to a small picture. ZII-A: from a shape to the same shape. ZII-B: story pairs, picture to picture ("the bee goes to the flower", `content/pencil/line_stories.yaml`). ZII-C: zigzags. ZII-D: right-angle steps, square bumps (left→right lanes only) and S-curves. Lines always run left→right or top→bottom and never turn back; no arrows or text for the child; lanes narrow across the level and lines get longer across each part |
| `count_and_say` | MA 6A-A/B | Rows of N pictures + big numeral + number word; count aloud while pointing |
| `count_and_point` | MA 6A-B/C | Rows of N pictures + 3 numeral choices to point at |
| `number_read` | MA 6A-C, 5A-A/E | 4 numeral cards to read aloud, each with a picture of how many: object pictures (6A, `show: pictures`), ten-frames (5A-A up to 30, `show: ten_frames`) or tens bars + ones squares (5A-E, 51–100, `show: rods`) |
| `dots_to_number` | MA 6A-D | Dot patterns up to 10 with their numerals |
| `number_sequence` | MA 5A-B/C/D | 4 tracks of 10 consecutive numerals with `gaps` empty boxes to say aloud (first box always shown, gaps never side by side); answer key = the gap numbers |
| `number_trace` | MA 4A-A | Rows of one number: a solid model with that many dots, then 3 large dotted numerals to trace (Andika glyphs filled with a dot pattern; verify checks the glyphs exist in the font). No answer key |
| `number_write` | MA 4A-B…E | `mode: copy`: a dotted run to trace, then empty boxes to write the same numbers; `mode: fill`: tracks of 10 (two rows of five) with empty boxes to write the missing numbers. Answer key = numbers written |
| `next_number` | MA 3A-A/B | "Write the number that comes next": two columns of `n → box` (`order: run` or `mixed`; `max` is the largest answer) |
| `add_facts` | MA 3A-C…F, 2A | Two columns of `a + b = box` facts within the part's range (`op`, `addend`/`second` one number or a list, `min_first`/`max_first`, `new_from`, `rows`); answer key generated, one answer per box. `bridge: N` (+1 only) shows `n → box` above `n + 1 = box`; reusable for subtraction (`op: "-"`) |
| `fact_drill` | MA M1 (Puppies math, ours) | + and − facts within 20 (`ops`, `amounts`, `first`, `turnarounds`, `blanks`: answer or missing middle number) in four layouts cycled per part: `horizontal` (12), `vertical` (12 column facts), `bridge` (4 count-on/count-back number tracks + 6 facts, amounts ≤ 3), `families` (3 number houses × 4 facts). Facts numbered small for grown-ups; answer key in that order. Verify recomputes every answer, keeps operands in the part's range, sums ≤ 20, no negatives, every amount and sign on the page, ≤ 1 zero answer |
| `fact_drill` (× ÷) | MA M3 B–E (Foxes math, ours) | Same type with `ops: ["*"]` / `["/"]` (facts within 100; `amounts` = the tables, `first` = the other factor, or the answer for ÷, so sharing always comes out even). Extra layouts: `skip` (count-by track b…10b with 4 gaps + 8 facts of that table), `arrays` (4 dot arrays: a rows of b), `pairs` (6 rows "☐ × b = c" next to "c ÷ b = ☐"), and `families` as × ÷ houses. Verify recomputes every fact, the track, array sizes and pairs |
| `place_value` | MA M2-A/B | `mode: blocks` (tens bars / hundred squares → "☐ hundreds ☐ tens ☐ ones = ☐"), `expanded` (parts, units, number names), `compare` (<, >, =) |
| `skip_count` | MA M2-C | Tracks counting by 5s/10s/100s from a multiple of the step; first two boxes shown, gaps to write |
| `column_arithmetic` | MA M2-D…H | Vertical 2-/3-digit add/take away (or 3 addends); dashed carry/borrow boxes only on regrouping parts; verify recomputes answers and regrouping per part (`regroup: none/all/mixed`, `max_regroups`). Foxes (MA M3-A) adds `problems: 9` (3 × 3, compact), `regroup_counts` (exact number of trading columns each problem may have; every count on every page) and `across_zero` (at least N take-aways trading through a 0 in the tens, 402 − 168) |
| `math_story` | MA M2-H | Tiny story problems from `content/math/stories.yaml` with a picture and "☐ ◯ ☐ = ☐" to fill |
| `pattern_words` | EN 3A-A (Puppies Reading) | Pattern bank on top (sh ch th wh / a_e i_e … / ai ay …), 4 cards: picture + word with the pattern's letters as boxes to fill (the whole word is shown too on the first `show_word_pages` of a part). New word first; review words from `known_levels` + earlier 3A words with the same pattern family (`content/phonics/english.yaml`). Verify: the pattern really occurs at the gaps. Answer key = the words |
| `word_endings` | EN 3A-B | `add`: "jump + ing = ☐" (plurals show the picture twice), `take_off`: "jumping − ing = ☐". Forms from the hand-checked `endings` table; verify re-derives each from the spelling rules (es, drop e, double) unless listed under `irregular` |
| `syllable_split` | EN 3A-C | Picture + word; `boxes`: one box per clap to write each syllable, `count`: circle 1, 2 or 3 claps. Splits from the hand-checked `syllables` table (join back into the word, a vowel in each) |
| `sentence_copy` | EN 3A-D | 2 cards: picture + a sentence (the word's own `sentences:`) + 2 handwriting rows. Verify: known words, sight words and their regular endings only; part's length and end marks (`.` / `?`); sentence-sense scan in `tests/test_sentence_sense.py` |
| `letter_team` | EN 4A-A | 4 picture words with their letter team highlighted (sh, bl, -at); trace the team in gray or write it in boxes. Teams and words from the hand-checked `content/phonics/english.yaml`; new words go to the page whose team they carry |
| `rhyme_match` | EN 4A-B | 4 rows from hand-checked rhyme groups: read a rhyming pair, pick the picture that rhymes, or find the odd one out (wrong choices never share the vowel sound); answer key |
| `sentence_trace` | EN 4A-C | Picture + a sentence of known words (the 6A frames and truth rules), read, then traced in gray on writing lines (two lines when long) |
| `fraction_line` | MA M3 F | 5 number lines 0–1 cut into 2, 3, 4, 6, 8 parts (one of each a page); tasks `name` (write the dotted fraction), `mark` (draw a dot), `fill` (write missing tick labels); `unit_only` in part 1. Only whole numbers stored; verify checks ticks, marks and answers |
| `story_problem` | MA M3 G | 3 short stories a page from `content/math/story_problems.yaml` (33 frames: equal groups, sharing, two-step); one times, one sharing and one two-step story a page. Verify refills each frame from the stored numbers, recomputes the answer and the true-to-life checks |
| `fraction_ops` | MA M5 B–C | 8 stacked-fraction problems (`op` add/sub/mul/mixed; `relation` multiple/other for unlike denominators; `mixed_numbers`; `whole_times`; `simplify_min`) or `layout: area` (4 unit squares cut and shaded by both fractions). Answers in simplest form, over 1 as mixed numbers; verify recomputes with `Fraction` |
| `decimal_place_value` | MA M5 D part 1 | 4 compare pairs (<, >, = incl. 9.2 vs 9.20), 3 rounding lines (whole, tenths, hundredths), 3 "the 8 is worth" lines |
| `decimal_column` | MA M5 D | 6 column problems with the points lined up and ragged places (3.5 over 12.47), take-aways from whole numbers; `answer_point: false` leaves the point to the child. Verify recomputes with `Decimal` |
| `decimal_ops` | MA M5 E | 10 horizontal × ÷ facts by kind: by 10/100/1000, decimal and whole number, decimal by decimal; division must come out exactly (checked with `Fraction`) |
| `order_of_operations` | MA M5 F | 10 expressions with parentheses/brackets (8) and plain times-before-plus lines (2); every step whole and above 0; grouping always changes the answer |
| `box_volume` | MA M5 F | 4 drawn boxes: unit cubes to count, labeled l × w × h, base area × height, two boxes side by side to add (5.MD.5c) |
| `column_arithmetic` (4-digit) | MA M4-A (Owls math, ours) | Same type with four-digit numbers (`max_answer: 9999`, `regroup_counts: [1, 2, 3]`, `across_zero` on taking away); 4+ digit columns put 2 problems a row in the compact size |
| `long_multiplication` | MA M4 B–C | `layout: expanded` (one line per place of a 2-digit number × 1 digit, then add) · `carry` (one answer line, carry boxes over the top number; every problem carries; `tens_only` for 23 × 40) · `partials` (2-digit × 2-digit: × ones, × tens ending in 0, then add; `zero_shown` prints that 0; a line always carries). Lines right-aligned in `cols` columns; verify recomputes the lines, columns, carry boxes and answers |
| `division_house` | MA M4 D, M5 A | Long division house, divisor range from the rules (1 digit in Owls, 2 digits in Otters; optional `divisor_multiple_of` for dividing by tens): answer boxes over the dividend digits from the first that holds the divisor (`start`), "R" box on remainder parts, squared work space under the digits. Rules `remainder: none/all/mixed`, `small_first`, `zero_in_quotient`, `problems` (4; 2 for four digits). Verify: q × d + r = dividend, r < d, alignment, counts per page |
| `factor_pairs` | MA M4 E | Stacked cards: `pairs` (every factor pair of n, one ☐ × ☐ slot per pair; numbers rotate by page so neighbors differ), `multiples` (count in 3s…9s), `circle` (circle the 3–4 multiples among 8), `prime` (3 numbers: circle prime or composite). All within 1–100; verify recomputes pairs, multiples and primes |
| `fraction_bars` | MA M4 F | `bars` (two equal bars, b and n·b parts, write the equivalent top), `times` / `divide` (a/b = ☐/d, missing top or bottom), `add` / `sub` with like denominators (first `bars` problems drawn as one bar: shaded, striped, crossed out; sums ≤ 1 whole). Denominators 2, 3, 4, 5, 6, 8, 10, 12 (100 only from tenths); verify cross-multiplies every pair |
| `fraction_ops` (÷) | MA M6 A (Pandas math, ours) | Same type with `op: div`: `layout: model` (5 rows: whole or fraction ÷ unit fraction with fraction bars to count on; whole answers) or `list` (8 problems, `dividend`/`divisor` kinds proper / mixed / whole / unit cycling, answers in simplest form). Keep-change-flip appears only in parent tips. Otters output unchanged; verify recomputes every quotient and bar |
| `ratio_table` | MA M6 B | Ratio tables from `content/math/ratios.yaml` contexts: `start` (sentence + first column = the simplest ratio, ×1…×5, 3 a page) or any-column tables (one full column, write the simplest ratio, 4 a page). Verify checks every column against the base ratio |
| `rational_story` | MA M6 A, B, C, F | 3 word problems a page from `content/math/rational_stories.yaml` (tags: fraction_divide, unit_rate, speed, unit_price, convert, percent_of, percent_whole, equation); exact Fraction answers in whole, fraction, decimal or money style; equation frames add an "Equation:" line. Verify refills and recomputes each frame |
| `percent_problem` | MA M6 C | `grids` (6 hundred grids: ☐ out of 100 = ☐%) or `facts` (12: p% of w, p% of ☐ = part, ☐% of w = part; whole numbers only). Verify recomputes p × w ÷ 100 exactly |
| `signed_numbers` | MA M6 D | Number lines −10…10 (`name`, `mark`, `opposite`) or facts (`context` situations, `opposite`, `compare` <>, `abs`, `order`), halves allowed. No adding or taking away negatives (that is grade 7) |
| `coordinate_grid` | MA M6 D | Drawn SVG grid −6…6: 4 points to read (one per quadrant), 4 to plot (one on an axis), 2 distances between points sharing a coordinate. Points store pixel positions; verify checks them against their coordinates |
| `expression_eval` | MA M6 E | `power` (whole-number exponents, order of operations), `write` (phrase → expression), `substitute` (if n = 5, 3n + 4), `formula` (A = lw, P = 2l + 2w, d = rt, two-letter expressions). Expressions stored in Python form and printed by `_rational.pretty`; never the letter `a` |
| `equation_solve` | MA M6 F | x + p = q, p + x = q, px = q with nonnegative whole, decimal (tenths/hundredths) or fraction numbers; "x = ☐". Verify solves each again with Fraction |
| `power_root` | MA M8 A (Lions math, ours) | 8 problems: `power`, `square_root`, `cube_root` (index-3 root), exponent rules `product` / `quotient` / `power_of_power` (write as one power, b^☐; number or letter bases), `zero_negative` (2^−3 = 1/8), `rule_value`, `solve_square` (x² = 49 → ±7), `solve_cube`, `between` (√40 between ☐ and ☐). Only numbers stored; verify recomputes with Fraction and checks bases, exponents and roots per part |
| `sci_notation` | MA M8 B | `to_sci` (3,200,000,000 → ☐ × 10^☐), `to_standard`, `multiply`, `divide`, `times_bigger` (how many times bigger). Coefficients 1 ≤ c < 10 with ≤ 3 significant digits, exponents per part; exact Decimal arithmetic, answers re-tidied (24 × 10^5 → 2.4 × 10^6) |
| `equation_solve` (`mode: multi_step`) | MA M8 C | 6 equations a page with room to work (`ws/sheet_types/_multi_step.py`, template `equation_solve_multi_step.html.j2`): forms `two_step`, `like_terms`, `both_sides`, `distribute`, `distribute_like`, `distribute_right`, `distribute_both`, `fraction_coef` (¾x − 7 = x − 6); `fraction_solutions` (answers like −10/3) and `special` (one no-solution and one every-number equation, 8.EE.7a). Built backwards from the answer; stored as terms + printed tokens; verify re-prints and re-solves exactly. Pandas pages unchanged |
| `coordinate_grid` (`mode: lines`) | MA M8 D | `ws/sheet_types/_slope_lines.py`: slope from `points` / `table` / a drawn line (`read_slope`), `read_mb`, `write_graph`, `draw_line` (empty grid; key names 2 points), `from_points`, `from_table`, `compare` (equation vs. table: greater rate of change, 8.F.2), `is_function` (x/y table, yes/no pairs, 8.F.1). Pages cycle through `mixes`; 4 graphs, 6 or 8 text items a page. Lines store exact grid-edge ends; verify recomputes them, checks dots and table rows lie on y = mx + b and ≥ 3 grid points |
| `coordinate_grid` (`mode: systems`) | MA M8 E | `ws/sheet_types/_systems.py`: `graph_read` (two lines drawn, solid + dashed), `graph_draw`, `substitution`, `elimination`, `inspect` (no solution / same line), `story` (frames in `content/math/systems.yaml`, 8.EE.8c). Whole-number answers; verify re-prints both equations, checks the unique (or none/all) solution and every drawn line |
| `pythagorean` | MA M8 F | Right triangles drawn from their legs (square corner marked, "?" on the unknown): `hypotenuse`, `leg`, `is_right` (yes/no pairs, the converse), `distance` between grid points. `triples: true` → whole answers (3-4-5 … multiples); false → √n ≈ one decimal (exact half-up rounding). Legs at most 3.5 : 1 so triangles stay readable |
| `coordinate_grid` (`graphs`) | MA M9 B (Whales math, ours) | Same type with rule `graphs: 4`: four small −6…6 grids, each a line (`signs: ["="]`) or linear inequality (< ≤ > ≥) to graph, slopes from `slopes` (incl. ½, ⅔, 3/2), whole intercepts; standard form (2x + y < 4) from `standard_form_from`. Answer: dashed/solid line through two points, shade above/below. Pandas output unchanged (`ws/sheet_types/_slope_lines.py`) |
| `exponent_rules` | MA M9 A | 8 expressions to simplify: whole/zero/negative exponents (positive-exponent answers), rational exponents (8^(2/3), root ↔ power), simplifying √ and ∛ (letters positive). Exact `Mono`/`root_parts` in `ws/algebra.py` plus a float cross-check |
| `slope_intercept` | MA M9 B | Write y = mx + b: 2 tables, 2 pairs of points, 1 situation (`content/math/algebra_stories.yaml`, letters from the frame, never `a`). Verify recomputes every table value and point |
| `inequality_line` | MA M9 B | 5 one-variable inequalities (two-step, negative coefficient, x on both sides, distribute) + an empty number line −10…10; answer x ≤ s with open/closed dot and side. Verify collects to Px + Q and flips for P < 0 |
| `polynomial_ops` | MA M9 C | Add/subtract/distribute/FOIL in `rows` (5) or the `box` method (4; 2×2 or 2×3 boxes labeled with the factors' terms). Problems stored as ASCII, multiplied out exactly by `ws/algebra.parse` |
| `polynomial_factoring` | MA M9 D | 8 polynomials to factor completely: GCF, x² + bx + c, leading 2/3/5, difference of squares (incl. two letters), GCF first. Canonical answer order; verify multiplies back and checks nothing factors further |
| `quadratic_solve` | MA M9 E | Factoring / square roots (8 a page), the formula (4 a page with boxes for the three numbers and b² − 4ac; the general formula is never printed), mixed with an area story. Exact roots (p ± q√d)/s, checked in Q(√d) |
| `word_puzzle` | EN 2A-A (Cubs Reading) | Picture clues → letters: `puzzle: missing` (4 pictures, word in letter boxes, `blanks` empty: a number or `all_but_first`; `blank_letters: vowels` never a silent final e) or `puzzle: crossword` (2 two-word crosswords crossing at a shared letter, arrow clues; `given` squares). Words from the hand-checked `puzzle_words` (content/grammar/english.yaml), least used first; answer key = the words |
| `word_sort` | EN 2A-B (Cubs Reading) | Naming / doing / describing words from the hand-checked `kinds` lists (disjoint; color words left out). `word_kinds: pick` (circle the `target` word in rows of 3) · `sort` (check one kind per word, even across kinds) · `fill` (sentence with a blank + 2 choices, only one of the right kind; sentences hand-written in `fill`). A new word gets a word card (picture, word, its bank sentence); tips per layout (`word_sort_pick` …) |
| `read_aloud` | EN 2A-C (Cubs Reading) | An original passage (content/passages/english.yaml, file order) read on `passage_reads` pages in a row, with `questions_per_sheet` who/what/where/when/why/how questions, 3 choices to circle; grown-up box with word count and time. Verify: `passage_words` and `max_sentence_words` per part, answers word for word in the passage, featured `words` appear |
| `passage_questions` | EN R3-A/C/D (Foxes Reading, ours) | An original 120–150-word passage (`content/passages/R3/<section>.yaml`) + 3 questions: 2 circle-A/B/C (options shuffled by seed) + 1 written on 2 lines. A passage serves 2 pages ("Read the story again" on the second). Verify: word count, Flesch-Kincaid grade 2.5–4.5 (`ws/readability.py`), US spelling, every question's `evidence` quote is in the text, key matches |
| `word_builder` | EN R3-B | 4 words to build (un + kind, care + ful, star + fish with pictures), circle the meaning of 2 (wrong choices: the other word part's meaning and another word's), pick the word that fits 2 sentences (built word vs its hand-checked foil). List: `content/wordparts/R3.yaml` |
| `full_sentence_answer` | EN R3-E | A 120–140-word passage + 3 questions answered in full sentences on lines; part 1 prints each answer's first words (`starter`); sample answers in the key |

**Counting pictures** (`count_*`, `number_read`): up to 5 in one row; 6–10 as two rows of
five (ten-frame style), since ten 72px pictures don't fit one row. Checks count the
pictures in the item, not in one row.

**Numbers past 10** (MA 5A): never draw more than 10 object pictures. Numbers 11–30 are shown
as ten-frames (one full frame per ten + a partly filled frame for the ones, K.NBT.1); 51–100
(5A-E) as bars of ten squares + single squares, since eight or nine ten-frames don't fit a card.
Sequence sheets (5A-B/C/D) use numerals only. A part's `new` may be a list (5A-A adds two
numbers per part); every page shows all of them.

**Line paths**: the start is a dot; the end is a small picture on a white disc centered on
the lane's end. Lane ends never touch the page edge. One direction per sheet (cycling
through the part's `directions`). With `start_marker: shape` or `picture` (ZII-A/B), the start
shape or picture sits on its own disc and the dot is on the lane just past that disc. Path kinds:
`straight`, `arc`, `wave`, `mixed_curves` (ZI); `zigzag` (`turns`), `steps`, `bumps`, `s_curve`
(`bends`), and `mixed` with a `kinds` list (ZII). Verify samples the whole lane: x must never
decrease on left→right lanes (y on top→bottom lanes), so zigzags and corners can move up or down
but never back, and top→bottom lanes have no flat leftward strokes. It also checks that every lane and disc stays clear of the page edge and of
the other lanes on the sheet.

**Phrases and sentences** (`phrase_card`, `sentence_recite`): every phrase must be true to its
pictures, using hand-checked tables in `content/phrases/english.yaml`: `picture_colors` (the color a
picture is drawn in), `sizes` (nouns that really are big / little; the noun's picture is then drawn
large or small, item field `picture_size`), `temperatures` (things that really are hot / cold) and
`can_do` (which animals can do an action), `child_cannot` (no "I can read" for a 3-year-old) and
`people_can` (only these people do it: "Mom can read."). Describing words (big, little, hot, cold) have no picture
of their own (`picture` left out in the word bank). An animal doing an action ("The mouse can eat.")
shows the animal only, since the action pictures show a child; a person doing it shows both. A
page's new word is used in one of its phrases, and its picture is shown there. Word Hunt grids
(6A-A, `review_from_levels`) take the previous level's words seen least in that level's plan first.

**"Say it again" strip** (every 7A-A sheet, both types): a small strip at the bottom of the
page with 2 small pictures and their words, taken from words introduced 3–10 sheets earlier.
The main cards stay at 2 new words. Pages 1–3 have no strip, because no word is old enough yet.

**Letters and sounds (EN 5A)**: one planner (`rules: { planner: letters }`, `ws/plan.py plan_letters`) picks
each page's letter, rime or words from the hand-checked lists in `content/sounds/english.yaml` (words by
first sound, onset + rime splits). Pages the word bank can't fill yet are listed by verify as warnings.

Later levels (4A–2A English, 3A–2A Math) need more types. Add them when the child is about
one level away. Don't build them early.

---

## 8. Verification (`ws verify`) — must pass before done

Run on any set of generated sheets (default: everything in the latest manifest entries).
Each check returns `Issue(sheet_id, severity, message)`. Any `error` → non-zero exit.
Checks run per **(level, variant)**, so a `--variant 2` repeat is never a "duplicate" of variant 1.

- **Stale check**: every sheet is rebuilt from its recorded seed and compared; a mismatch means
  code or content changed since it was generated ("stale: regenerate it").
- **Plan-based exposure**: the exposure rules are checked on the level plan, which always covers
  the whole level, so verify passes on a partly generated level. Real exposure counts from the
  manifest are checked too once every page of the level exists. While the word bank doesn't
  cover all of 7A-A, verify warns (7A-B/C sheets will change as words are added).
- A sheet type forced with `--sheet-type` is a warning, not an error.
- **Color words**: sheets showing a `needs_color` word are listed in one warning per level
  ("print these in color"); booklet covers name those pages. Everything else must still read
  in black and white.
- Banned words live in `content/banned.yaml` (matched case-insensitively, whole words) and are
  checked on every sheet's text and on booklet covers, logs and answer pages.

**Content checks (all types)**
- Schema valid; sheet ID unique; page number inside the section's range.
- Every referenced picture file exists, is valid SVG, has a licence entry.
- Vocabulary is allowed: every word appears in the bank with `level ≤ current level`, and
  "new" words are introduced only in sections that allow new words.
- No duplicate sheet (same items in same order) within a level.
- Text limits: word length, sentence length and words per sheet are within the section rules.
- Parent tip present, ≤ 220 characters.
- Banned-content list check (brands, "Kumon", violence words).

**Type-specific checks (examples)**
- `count_*`: number of pictures in a row == stated answer; answer within section range;
  distractors distinct, in range and ≠ answer; the answer's position is not always the same.
- `add_facts`: every answer recomputed and matches the answer key; the added number and the
  largest first number stay inside the **part's** range (e.g. 3A-C part 2 → `n + 1` with n ≤ 17).
- `number_sequence` / `next_number`: gaps and answers are consistent with the sequence and
  inside the section's number limit.
- `word_story`: `only_known_words` holds (every token is a known word or one of the
  `allowed_words` in `content/stories/english.yaml`, e.g. *the, a, is, I, my*). Stories are
  built from sentence frames with a slot (`"I see {a} {w}."`), so the planner can aim them
  at the words seen least.
- `word_picture_sentence`: the sentence is read *to* the child, so it is exempt from the
  known-words check; it must contain the card's word and stay within the section's `max_sentence_words` (6 in 7A).
- `phrase_card` / `sentence_recite`: every token is known (or in `allowed_words`); the phrase
  re-renders from its frame; colors, sizes, temperatures and animal actions match the tables;
  the pictures and `picture_size` are the ones the phrase calls for; new words are used and pictured.
- `letter_trace` / `word_trace`: letters requested exist in the trace font (`ws/trace_font.py`, our own
  single-stroke dotted a–z in Andika's shapes; Andika only has outlines) and the solid letters in Andika's cmap.
- `letter_team`: the word is on the team's hand-checked list and the team sits at its place (start/end/any). `rhyme_match`: rhymes come from the hand-checked groups; wrong choices have a different vowel; the answer is not always in the same place.

**Exposure checks (per section / level run)**
- Words are "new" exactly once in the level.
- Every 7A word appears ≥ 3 times across the level (new + "Say it again" strip + review
  grid + stories). The strip has only ~194 slots, and words introduced on the last pages of
  7A-A never reach it, so the planner must give 7A-B grid slots and 7A-C story words to the
  words the strip served least.
- Every strip word was introduced 3–10 sheets before the sheet it appears on.

**Layout checks (Playwright, after render)**
- Each sheet renders to exactly **one** Letter page (816×1056 CSS px); nothing overflows
  (`scrollHeight ≤ clientHeight` for the page root and every card).
- Minimum font sizes: child-facing text ≥ 28px (7A–5A, math 4A and pencil levels), ≥ 20px (other 4A+); parent tip ≥ 16px.
  Parent-facing parts of a template carry `data-audience="parent"` (header, tip, footer, strip
  label); every other piece of text on the page counts as child-facing.
- Each sheet prints (Chromium PDF) to exactly one 612×792pt page.
- All images loaded (no broken `<img>`).
- Output a **contact sheet PNG** (thumbnails of every generated page) to
  `out/<subject>/<level>/review.png`, plus one per section (`review-<section>.png`); more than
  10 pages use quarter-size thumbnails. Claude Code must look at this image before reporting done.

---

## 9. CLI

```bash
# Generate: by section ("type A"), by page range, or whole level
ws generate --subject english --level 7A --section A --count 20      # next 20 unused pages of 7A-A
ws generate --subject english --level 7A --pages 1-50
ws generate --subject math    --level 6A --all
ws generate --subject math    --level 3A --section C --part 2 --count 10   # Adding 1, up to 18+1
ws generate --subject english --level 7A --section A --count 10 --sheet-type word_picture_sentence
ws generate ... --seed 42            # default seed = hash(subject, level, section, page)
ws generate ... --variant 2          # alternative version of the same pages (for repeats)

# Verify and render
ws verify [--subject english --level 7A]
ws render --subject english --level 7A --pdf     # one booklet PDF per section + whole level

# Content helpers
ws pictures missing --subject english --level 7A
ws pictures sheet                                # contact sheet of all pictures
ws preview --subject english --level 7A          # free preview PDF → out/previews/<slug>.pdf (§15)
ws vocab stats --level 7A                        # words in bank vs. target, exposure counts
ws syllabus show english 7A                      # print sections, page ranges, sheet types
```

**"Next unused pages"**: the manifest records which page numbers of each section exist
(per variant), so `--count 20` continues where the last run stopped. Running it again after
the end of the section's range errors clearly ("7A-A is complete: pages 1–100").

**Booklet PDF** = cover page (child's name field, level, page range, sections, and the mastery
note from §12 for grown-ups) + the sheets in order + a final **progress log** page (date, pages,
minutes, notes). No answer keys in the child's booklet. Answer keys go in a separate `-answers.pdf`.
Names use public names (§15): one per section from the pages present, numbered by level page
(`chicks-reading-pages-001-020.pdf`), and one for the whole level (`chicks-reading-level.pdf`,
`chicks-math-level.pdf`); variants add `-vN`. Gaps in a section are a warning.

---

## 10. Visual spec (match the existing sample sheets)

- Page: US Letter 816×1056 px, padding 48/56/40 px, white background.
- Font: **Andika** (designed for early readers, single-storey "a"), bold for headings.
- Header: small caps line `CHICKS · READING` (public level name · public subject), sheet title (34px bold), pill with the page number **within the level** (`Chicks · 101`, so progress
  reads 1–200 in one line),
  and `Name ____ Date ____ Time ____` on the right, then a 3px rule in the subject colour.
- Subject colours: English teal `#0B7A75` (tint `#E6F4F3`), Math orange `#B4410C`
  (tint `#FDEDE3`), Pencil skills purple `#6B4FBB` (tint `#EFEBFA`). Must print legibly in grayscale.
- Parent tip box under the header, tinted background, 2px solid border in the subject color
  (so it still shows in black and white), 17px. Tips come from `content/tips/<subject>.yaml`
  per sheet type; a section or part can override them with `rules: { tips: { <sheet_type>: [...] } }`.
- The body fills the height left between header/tip and strip/footer; no floating, centered
  blocks. 7A word cards are stacked one per row (picture ~280px left, word 96px bold right, lowercase).
- Ligatures are off (`font-variant-ligatures: none`) so early readers see every letter.
- Cards: 3px near-black border, 28px radius. Pictures 200–250px in 7A English, 72px
  per item in counting rows.
- Footer: 12px grey public reference (`Chicks · Reading · page 101`, plus `· version N`). Internal sheet IDs
  (`EN-7A-B-001`) stay in the manifest and work files. No branding on sheets.

---

## 11. Syllabus to encode (our version of the structure)

Page ranges are for a 200-page level unless noted. Section letters follow page order.

### Pencil skills (subject `pencil`, shared by English and Math, from the math chart)
No SCT. Do ZI alongside the first English/Math level; it must be finished before EN 5A
and MA 4A, which start tracing.
| Level | Sections (code: name, pages) | Notes |
|---|---|---|
| ZI (100p) | A Coloring 1–20 · B Straight Lines 21–50 · C Curved Lines 51–100 | Coloring 1–2, Straight Lines 1–3, Curved Lines 1–5 (10 pages each) |
| ZII (100p) | A Shapes & Pictures 1–30 · B Shapes & Pictures (Stories) 31–60 · C Back & Forth 61–80 · D Corners & Curves 81–100 | e.g. "draw a line from the circle to the star" |

### English (from the syllabus chart)
| Level | Sections (code: name, pages) | Aims / notes |
|---|---|---|
| 7A | A Familiar Words 1–100 · B Familiar Words Review 101–140 · C Word Stories 141–200 | Repeat familiar words; ~200 words (our choice: fewer words, learned well), each seen ≥ 3 times |
| 6A | A Vocabulary Review 1–30 · B Simple Phrases 31–100 · C Familiar Sentence Structures 101–200 | Recite words/phrases/sentences; +210 words |
| 5A | A Letter Tracing 1–70 · B Sound Parts 71–150 · C Letter Review 151–160 · D Word Tracing 161–200 | Read short sentences; initial consonants, short vowels; trace a–z; +113 words |
| 4A | A Familiar Letter Combinations 1–100 · B Rhyming Skills 101–140 · C Sentence Tracing 141–200 | Double consonants, clusters, phonograms; SCT 1–2 min/page; +225 words |
| 3A | A Spelling Patterns 1–70 · B Take the Tail 71–110 · C Syllables 111–140 · D Sentence Copying 141–200 | r-controlled vowels, digraphs, diphthongs, long vowels; SCT 1–2 (last section 1.5–2.5); +181 words |
| 2A | A Word Puzzle 1–60 · B Function of Words 61–150 · C Oral Reading 151–200 | Nouns, verbs, adjectives; read ~50-word passages in ~1 min; SCT 1–2 |

### Math (from the official math chart; 6A is the first math level, there is NO math 7A)
Each section is split into 10-page **parts** in the chart; encode them as `parts:` with their
own number range so generators know exactly which numbers/facts a page may use. SCT is
not used in 6A–5A. 4A and 3A pages 1–60 are 0.5–2 min/page; 3A from page 61 and all of 2A
are 1–2 min/page.

| Level | Section (code: name, pages) | Parts / number range |
|---|---|---|
| 6A Counting | A Counting up to 5, 1–30 | 3 parts: up to 3 / 4 / 5 (`source: ours`) |
| | B Counting up to 10, 31–100 | 7 parts: up to 6 / 7 / 8 / 9 / 10 (`count_and_say`), then 2 mixed up to 10 (`count_and_point`) |
| | C Number Reading up to 10, 101–150 | 5 parts: 1–4 / 1–6 / 1–8 / 1–10 / mixed 1–10 (read numerals with pictures) |
| | D Number of Dots up to 10, 151–200 | 5 parts: 1–5 / 1–7 / 1–9 / 1–10 / mixed 1–10 (dot patterns ↔ numeral) |
| 5A Reading Numbers | A Number Reading up to 30, 1–100 | 10 parts |
| | B Sequence of Numbers up to 30, 101–130 | 3 parts |
| | C Sequence of Numbers up to 40, 131–160 | 3 parts |
| | D Sequence of Numbers up to 50, 161–190 | 3 parts |
| | E Large Numbers, 191–200 | numbers beyond 50, reading only |
| 4A Writing Numbers | A Number Tracing, 1–40 | 4 parts |
| | B Number Writing up to 10, 41–100 | 6 parts |
| | C Number Writing up to 20, 101–120 | 2 parts |
| | D Number Writing up to 30, 121–140 | 2 parts |
| | E Numbers up to 50, 141–200 | 6 parts |
| 3A Adding (+1 to +3) | A Numbers up to 100, 1–60 | 6 parts ("write the number that comes next") |
| | B Numbers up to 120, 61–70 | 1 part |
| | C Adding 1, 71–130 | parts up to 12+1, 18+1, 24+1, 30+1, 60+1, 1000+1 |
| | D Adding 2, 131–160 | parts up to 14+2, 18+2, 32+2 |
| | E Adding 3, 161–180 | parts up to 14+3, 21+3 |
| | F Adding up to 3, 181–200 | mixed +1/+2/+3 |
| 2A Adding up to 10 | A Review up to 3A, 1–10 | |
| | B Adding 4, 11–30 | up to 12+4, 16+4 |
| | C Adding 5, 31–50 | up to 12+5, 15+5 |
| | D Adding up to 5, 51–70 | mixed |
| | E Adding 6, 71–90 | up to 12+6, 14+6 |
| | F Adding 7, 91–110 | up to 11+7, 13+7 |
| | G Adding up to 7, 111–130 | mixed |
| | H Adding 8, 131–150 | up to 11+8, 12+8 |
| | I Adding 9, 151–160 | up to 12+9 |
| | J Adding 9 and 10, 161–170 | up to 12+9 and 15+10 |
| | K Adding up to 10, 171–200 | mixed |
| **M1 (ours)** Puppies: Adding and Subtracting to 20 | A Adding 1–3 review 1–10 · B Adding 4, 5 11–40 · C Adding 6, 7 41–70 · D Adding 8, 9, 10 71–100 · E Adding within 20 101–110 · F Subtracting 1–3 111–130 · G Subtracting 4–6 131–150 · H Subtracting 7–10 151–170 · I + and − within 20 171–180 · J Missing numbers 181–190, fact families 191–200 | Replaces 2A for Puppies (grade 1–2: 1.OA.4–8, 2.OA.2); sheet type `fact_drill`; 10-page parts with ranges in `syllabus/math/M1.yaml` (`source: ours`); SCT 1–2 min/page (ours) |
| **M3 (ours)** Foxes: Big Adding, Times Tables, Sharing, Fractions | A Big Adding & Taking Away 1–30 · B Times Tables 2, 5, 10 31–60 · C Times Tables 3 and 4 61–90 · D Times Tables 6 to 9 91–140 · E Sharing Facts 141–170 · F Fractions on a Line 171–190 · G Story Problems 191–200 | Grade 3 work for age 6 (3.NBT.2, 3.OA.1–8, 3.NF.1–2); sheet types `column_arithmetic`, `fact_drill` (× ÷), `fraction_line`, `story_problem`; 10-page parts in `syllabus/math/M3.yaml` (`source: ours`); SCT 2–4 min/page (ours); child text kept at ≥ 28px |
| **M4 (ours)** Owls: Big Multiplying, Long Division, Factors, Fraction Friends | A Warm-up 1–20 · B Multiply by One Digit 21–60 · C Two-by-Two 61–100 · D Long Division 101–150 · E Factors and Multiples 151–170 · F Fraction Friends 171–200 | Grade 4 work for age 7 (4.NBT.4–6, 4.OA.4, 4.NF.1, 4.NF.3); sheet types `column_arithmetic`, `long_multiplication`, `division_house`, `factor_pairs`, `fraction_bars`; 10-page parts in `syllabus/math/M4.yaml` (`source: ours`); SCT 3–6 min/page (ours); child text ≥ 28px |
| **M5 (ours)** Otters: Long Division, Fractions, Decimals, Parentheses and Volume | A Long Division 1–40 · B Unlike Fractions 41–90 · C Fractions Times Fractions 91–120 · D Decimals in Columns 121–160 · E Decimals Times and Shared 161–190 · F Parentheses and Volume 191–200 | Grade 5 work for age 8 (5.NBT.2–4, 5.NBT.6–7, 5.NF.1, 5.NF.4, 5.OA.1, 5.MD.3–5); sheet types `division_house` (2-digit divisors), `fraction_ops`, `decimal_place_value`, `decimal_column`, `decimal_ops`, `order_of_operations`, `box_volume`; 10-page parts in `syllabus/math/M5.yaml` (`source: ours`); SCT 3–6 min/page (ours); child text ≥ 28px |
| **M6 (ours)** Pandas: Dividing Fractions, Ratios, Percents, Below Zero, Expressions, Equations | A Dividing Fractions 1–30 · B Ratios and Rates 31–70 · C Percents 71–100 · D Below Zero 101–130 · E Letters for Numbers 131–170 · F One-Step Equations 171–200 | Grade 6 work for age 9 (6.NS.1, 6.RP.1–3, 6.NS.5–8, 6.EE.1–2, 6.EE.5, 6.EE.7); sheet types `fraction_ops` (÷), `ratio_table`, `rational_story`, `percent_problem`, `signed_numbers`, `coordinate_grid`, `expression_eval`, `equation_solve`; 10-page parts in `syllabus/math/M6.yaml` (`source: ours`); SCT 3–6 min/page (ours); child text ≥ 22px |
| **M8 (ours)** Lions: Exponents, Scientific Notation, Equations, Lines, Systems, Right Triangles | A Exponents and Square Roots 1–30 · B Very Big and Very Small 31–50 · C Multi-Step Equations 51–100 · D Lines and Slope 101–150 · E Two Equations at Once 151–180 · F Right Triangles 181–200 | Grade 8 work for age 11 (8.EE.1–8, 8.F.1–4, 8.G.6–8, 8.NS.2); sheet types `power_root`, `sci_notation`, `equation_solve` (multi_step), `coordinate_grid` (lines, systems), `pythagorean`; 10-page parts in `syllabus/math/M8.yaml` (`source: ours`); SCT 4–8 min/page (ours); child text ≥ 20px |
| **M9 (ours)** Whales: Exponents, Lines, Polynomials, Factoring and Quadratics (Algebra 1) | A Powers and Roots 1–30 · B Lines and Inequalities 31–70 · C Polynomial Operations 71–110 · D Factoring 111–150 · E Solving Quadratics 151–200 | Grade 9 work for age 12 (N-RN.A.1–2, A-CED.A.1–2, F-LE.A.2, F-IF.B.6, F-IF.C.7a, A-REI.B.3, A-REI.D.10, A-REI.D.12, A-APR.A.1, A-SSE.A.1a, A-SSE.A.2, A-SSE.B.3a, A-REI.B.4b; high-school codes written without "HS"); sheet types `exponent_rules`, `slope_intercept`, `coordinate_grid` (graphs), `inequality_line`, `polynomial_ops`, `polynomial_factoring`, `quadratic_solve` on the exact kit `ws/algebra.py`; 10-page parts in `syllabus/math/M9.yaml` (`source: ours`); SCT 6–12 min/page (ours); child text ≥ 28px |

**M2 (Cubs math, our own level, `source: ours`, 200p):** A Tens and Ones 1–20 · B Hundreds, Tens and Ones 21–50 ·
C Skip Counting 51–70 · D Adding Ones 71–90 · E Adding Tens and Ones 91–130 (incl. three addends) · F Taking Away
131–170 · G Three-Digit Adding and Taking Away 171–190 · H Story Problems and Review 191–200. Covers 2.NBT.1–7 and
2.OA.1 so Foxes can open with 3-digit regrouping. See `syllabus/math/M2.yaml`.

Bridging pattern used throughout 3A: "3 → ☐" (next number) is shown above "3 + 1 = ☐", so
the child sees that +1 means "the next number". Reproduce the *idea* with our own layout.

---

## 12. Pedagogy rules the generator must respect

- **5 pages a day** is the default unit. Booklets are printed in batches of 10 pages.
- **Spiral repetition**: each 7A word is new exactly once and seen ≥ 3 times within the
  level (new card, "Say it again" strip, review grid, stories). Sections
  marked "Review" draw only from already-introduced items.
- **Small steps**: no section jumps more than one new idea per sheet (e.g. one new number
  per counting sheet, two new words per word sheet).
- **Mastery gate (printed in the parent guide, not enforced in code)**: move on when the
  child finishes 3 sheets in a row within the SCT (or ~5 min for 7A–5A) without prompting;
  otherwise repeat with `--variant N`.
- Parent tips are short, concrete and warm ("Touch each star and count together").
  No pressure language.

---

## 13. Build order (first milestones)

1. Scaffold package, models, syllabus YAML for EN 7A + MA 6A + pencil ZI, CLI skeleton.
2. Sheet types `word_picture_pair`, `word_picture_sentence`, `review_grid_4`, `word_story`, `count_and_say`,
   `count_and_point`, `number_read`, `dots_to_number`, `colouring`, `line_path`, plus templates.
3. Verification (content + layout + contact sheet) and render-to-PDF booklet.
4. Seed word bank: 60 words + pictures for 7A-A pages 1–30; prove the pipeline end to end.
5. Grow the word bank to ~200 words in batches of 40 (show each batch as a table of
   word, category and sentence and wait for an OK before drawing; show the contact sheet after), then generate all of EN 7A, MA 6A, ZI.
6. Only then: 6A sheet types and content.

## 14. Definition of done for any request
- Requested sheets generated, IDs continue the existing sequence.
- `ws verify` passes with zero errors. Warnings are listed in the reply.
- PDF booklet rendered; contact sheet viewed and nothing looks wrong.
- `pytest` passes. New sheet types have at least one golden-output test (fixed seed).
- Reply to the user: what was generated (IDs and page range), where the PDF is, any warnings.

## 15. Website: paperlessons.com (`apps/web/`)

The sheets are sold at **paperlessons.com**: PDF downloads first, printed sets shipped later, an iPad
app much later. This repo is a monorepo: the generator stays at the root (Python), apps live in
`apps/` (npm workspaces). See `apps/web/README.md` for commands.

- **Stack (keep it simple):** one Cloudflare Worker (Hono API + React/Vite SPA as static assets),
  D1 for data, R2 for files (PDFs). Tailwind v4 + shadcn/ui, bright kid-friendly palette.
- **Nothing public references Kumon**: no name, no comparisons, no level codes.
- **The public ladder is `syllabus/ladder.yaml`** (single source of truth; the site copies it at build time):
  13 levels for ages 3 to 12, Chicks → Ducklings → Bunnies → Kittens → Puppies → Cubs → Foxes → Owls →
  Otters → Pandas → Penguins → Lions → Whales. **Every level = one reading strand + one math strand**
  (reading 7A + math 6A, reading 6A + math 5A, …; from Puppies' math on, our own codes M1, M2, R3–R9,
  M3–M9, all in the internal-code ban list); Chicks and Ducklings also carry pencil warm-ups
  (ZI, ZII). Public subjects are "Reading", "Math" and "Pencil skills". Each internal level belongs to
  exactly one public level; `load_level` fills in its public name from the ladder.
- **Content runs two school grades ahead, by definition:** school grade = age on Sept 1 − 5 (preschool at
  3 = −2, Pre-K at 4 = −1); each level has one on-pace `age` and `content_grade` = school grade + 2
  (Cubs age 5 → grade 2, Foxes 6 → 3 … Whales 12 → 9). Ages 3–5 have two levels a year; the second one
  reaches the target. Every syllabus section carries `standards:` (Common Core codes it teaches; Chicks is
  Pre-K work, which has no Common Core codes, so its sections may leave it empty), checked
  against `content_grade`, and reading passages get a readability floor. The audit and the plan for
  Foxes → Whales are in `syllabus/PLAN-upper-levels.md`.
  Public section names must also be our own. Internal codes (7A, sheet IDs like `EN-7A-A-001`) may
  stay inside the generator, but anything a buyer sees (sheet headers, page pills, footers, PDF names,
  covers) must use public names before it is sold or offered as a preview.
- **Public names live in the syllabus YAML:** `public_name`, `public_title`, `slug`, `preview_pages` per level and
  `public_name` per section (all required). `ws/public.py` builds labels and file names from them.
  Internal level codes are in `content/banned.yaml`, so verify and the booklet/preview builders fail if
  one ever reaches printed text.
- **Free previews:** `ws preview --subject … --level …` regenerates the level's `preview_pages` and builds
  `out/previews/<slug>.pdf` (preview cover + pages + closing page). Upload to R2 at `previews/<slug>.pdf`
  (see `apps/web/README.md`); the site picks them up automatically.
- **Logo:** "paper" (Fredoka, bold, ink) + "lessons" (Gochi Hand, coral) next to a smiling folded-corner
  sheet. Keep it this simple.

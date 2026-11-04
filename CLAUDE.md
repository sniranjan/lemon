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
- Content must suit a 3–6 year old: no scary, violent or brand-name content; everyday
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
    english/7A/EN-7A-A-001-020.pdf
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
| `phrase_card` | EN 6A-B | Picture + 2–3 word phrase ("a red ball") |
| `sentence_recite` | EN 6A-C | Picture + one sentence to recite 3 times |
| `letter_trace` | EN 5A-A/C | Two picture words + large dotted lower-case letters to trace |
| `sound_parts` | EN 5A-B | Word split into onset + rime with picture |
| `word_trace` | EN 5A-D | Dotted whole words to trace under pictures |
| `colouring` | ZI-A | Simple outline shape to colour inside |
| `line_path` | ZI-B/C, ZII-C/D | Draw from a start dot to a small picture to reach ("take the bee to the flower") along a straight/curved/zigzag lane. Lines always run left→right or top→bottom; no arrows or text for the child; lines get longer across each part |
| `count_and_say` | MA 6A-A/B | Rows of N pictures + big numeral + number word; count aloud while pointing |
| `count_and_point` | MA 6A-B/C | Rows of N pictures + 3 numeral choices to point at |
| `number_read` | MA 6A-C, 5A-A | Numerals (in jars/balloons/boxes) to read aloud, with matching pictures |
| `dots_to_number` | MA 6A-D | Dot patterns up to 10 with their numerals |
| `number_sequence` | MA 5A-B/C/D | Number line/track with a few gaps to say aloud |
| `number_trace` | MA 4A-A | Large dotted numerals to trace |
| `number_write` | MA 4A-B…E | Trace a row, then write the same numbers in empty circles |
| `next_number` | MA 3A-A/B | "Write the number that comes next" in boxes |
| `add_facts` | MA 3A-C…F, 2A | Vertical list of `a + b =` facts within the part's range; answer key generated |

**Counting pictures** (`count_*`, `number_read`): up to 5 in one row; 6–10 as two rows of
five (ten-frame style), since ten 72px pictures don't fit one row. Checks count the
pictures in the item, not in one row.

**Line paths**: the start is a dot; the end is a small picture on a white disc centered on
the lane's end. Lane ends never touch the page edge. One direction per sheet (cycling
through the part's `directions`).

**"Say it again" strip** (every 7A-A sheet, both types): a small strip at the bottom of the
page with 2 small pictures and their words, taken from words introduced 3–10 sheets earlier.
The main cards stay at 2 new words. Pages 1–3 have no strip, because no word is old enough yet.

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
- `letter_trace`: letters requested exist in the trace font.

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
- Minimum font sizes: child-facing text ≥ 28px (7A–5A and pencil levels), ≥ 20px (4A+); parent tip ≥ 16px.
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
ws vocab stats --level 7A                        # words in bank vs. target, exposure counts
ws syllabus show english 7A                      # print sections, page ranges, sheet types
```

**"Next unused pages"**: the manifest records which page numbers of each section exist
(per variant), so `--count 20` continues where the last run stopped. Running it again after
the end of the section's range errors clearly ("7A-A is complete: pages 1–100").

**Booklet PDF** = cover page (child's name field, level, page range, sections, and the mastery
note from §12 for grown-ups) + the sheets in order + a final **progress log** page (date, pages,
minutes, notes). No answer keys in the child's booklet. Answer keys go in a separate `-answers.pdf`.
Names: one per section from the pages present (`EN-7A-A-001-020.pdf`) and one for the whole
level (`EN-7A-level.pdf`, `ZI-level.pdf`); variants add `-vN`. Gaps in a section are a warning.

---

## 10. Visual spec (match the existing sample sheets)

- Page: US Letter 816×1056 px, padding 48/56/40 px, white background.
- Font: **Andika** (designed for early readers, single-storey "a"), bold for headings.
- Header: small caps line `LEVEL 7A · ENGLISH`, sheet title (34px bold), pill with the page number **within the level** (`7A · 101`, so progress
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
- Footer: 12px grey sheet ID (section-relative, e.g. `EN-7A-B-001`). No branding.

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

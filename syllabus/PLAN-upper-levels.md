# Plan: Foxes → Lions (grades 3–8 work, ages 6–12)

Status: **draft, waiting for approval.** Nothing below is built yet. Once approved, each level becomes
`syllabus/english/R<g>.yaml` + `syllabus/math/M<g>.yaml` and `ladder.yaml` points at them.

## Ground rules

- **Grade target:** each level matches the US standard for its `content_grade` (CLAUDE.md §15), so
  ages 6–7 get grade 3 work up to ages 11–12 getting grade 8 work.
- **200 pages per strand**, sections in page order, 10-page parts where the numbers step up (as in 3A/2A).
- **Our own internal codes:** `R3`…`R8` (reading) and `M3`…`M8` (math), named after the content grade.
  The current placeholders (`A`, `B` … `G`) can't go in the internal-code ban list, because banning "A"
  as a whole word would fail every sheet with the article "a". `R3`/`M3` are safe to ban. These levels
  also go beyond the original structure on purpose, so their codes should be ours.
- **Answer keys** for every sheet from Foxes on, in a separate `-answers.pdf` as today. Reading
  short answers get a sample answer.
- **Page fit:** child text stays ≥ 20px (§8). Passages up to ~350 words fit on one page with their
  questions. Longer texts (Pandas and up) use a two-page spread: a reading page, then a questions page.
- **Topics fit ages 6–12:** animals, nature, science, inventions, sports, history, everyday life.
  Nothing scary, violent or tied to a brand.

## Foxes: grade 3 work, ages 6–7

| Reading R3 | Pages | Math M3 | Pages |
|---|---|---|---|
| A Story Time: 120–150-word stories, who/what/where questions | 1–50 | A Big Adding & Taking Away: 3-digit, with regrouping | 1–30 |
| B Word Builders: un-, re-, -ful, -less; compound words | 51–90 | B Times Tables 2, 5, 10 (skip-counting bridge) | 31–60 |
| C First, Next, Last: put story events in order | 91–130 | C Times Tables 3 and 4 | 61–90 |
| D Why Did They?: feelings and reasons in a story | 131–170 | D Times Tables 6 to 9 | 91–140 |
| E Say It in a Sentence: answer in a full sentence | 171–200 | E Sharing Facts: division as the times tables backwards | 141–170 |
| | | F Fractions on a Line: unit fractions, ½ … ⅛ | 171–190 |
| | | G Story Problems: mixed × ÷ | 191–200 |

## Owls: grade 4 work, ages 7–8

| Reading R4 | Pages | Math M4 | Pages |
|---|---|---|---|
| A Chapter Stories: 250-word installments of a few longer stories | 1–60 | A Warm-up: 4-digit adding and subtracting | 1–20 |
| B Word Detective: meaning from context | 61–100 | B Multiply by One Digit: 2- to 4-digit numbers | 21–60 |
| C True Facts: nonfiction, headings, captions, diagrams | 101–140 | C Two-by-Two: 2-digit × 2-digit | 61–100 |
| D Two Texts: compare two short texts on one topic | 141–170 | D Long Division: 1-digit divisor, with remainders | 101–150 |
| E The Big Idea in One Sentence: first summaries | 171–200 | E Factors and Multiples | 151–170 |
| | | F Fraction Friends: equivalent fractions; adding with like denominators | 171–200 |

## Otters: grade 5 work, ages 8–9

| Reading R5 | Pages | Math M5 | Pages |
|---|---|---|---|
| A Finding Details: 300–350-word nonfiction | 1–50 | A Long Division: 2-digit divisors | 1–40 |
| B Clue Words: context clues, multiple meanings | 51–90 | B Unlike Fractions: add and subtract | 41–90 |
| C What's the Lesson?: theme in stories and fables | 91–130 | C Fractions Times Fractions | 91–120 |
| D Like a Picture: similes and metaphors | 131–160 | D Decimals: place value, add, subtract | 121–160 |
| E Paragraph Summaries | 161–200 | E Decimals: multiply and divide | 161–190 |
| | | F Order of Operations and Volume | 191–200 |

## Pandas: grade 6 work, ages 9–10

| Reading R6 | Pages | Math M6 | Pages |
|---|---|---|---|
| A Main Idea and Support | 1–50 | A Dividing Fractions | 1–30 |
| B Reading Between the Lines: inference | 51–100 | B Ratios and Rates: ratio tables, unit rates | 31–70 |
| C Why Was It Written?: purpose and point of view | 101–140 | C Percents: of a number, find the whole | 71–100 |
| D How It's Built: cause/effect, compare/contrast | 141–170 | D Below Zero: negative numbers, the coordinate plane | 101–130 |
| E Short Written Answers: 3–4 sentences with evidence | 171–200 | E Letters for Numbers: expressions, substituting | 131–170 |
| | | F One-Step Equations | 171–200 |

## Penguins: grade 7 work, ages 10–11

| Reading R7 | Pages | Math M7 | Pages |
|---|---|---|---|
| A Summaries in Your Own Words | 1–50 | A Adding and Subtracting Negatives | 1–40 |
| B Claim and Evidence: simple arguments | 51–100 | B Multiplying and Dividing Negatives | 41–70 |
| C Word Roots: common Greek and Latin roots | 101–130 | C All Kinds of Numbers: fraction/decimal ops with signs | 71–100 |
| D Poems and Pictures in Words | 131–160 | D Proportions and Percent Change | 101–140 |
| E One Topic, Two Ways: fiction vs. nonfiction | 161–200 | E Tidy Expressions: like terms, distributing | 141–170 |
| | | F Two-Step Equations and Inequalities | 171–200 |

## Lions: grade 8 work, ages 11–12

| Reading R8 | Pages | Math M8 | Pages |
|---|---|---|---|
| A Close Reading: short excerpts, word-level questions | 1–50 | A Exponents and Square Roots | 1–30 |
| B Weighing Arguments: evidence, bias, counterclaims | 51–100 | B Very Big and Very Small: scientific notation | 31–50 |
| C Growing Characters: theme and character across a longer story | 101–150 | C Multi-Step Equations | 51–100 |
| D Explain Why: evidence-based paragraph answers | 151–200 | D Lines and Slope: y = mx + b, graphing | 101–150 |
| | | E Two Equations at Once: simple systems | 151–180 |
| | | F Right Triangles: the Pythagorean theorem | 181–200 |

## New sheet types (built level by level, not all at once)

- **Reading:** `passage_questions` (multiple choice + short answer; most reading pages),
  `passage_spread` (two-page text + questions), `word_parts`, `story_order`, `written_response`.
- **Math:** most are one generalized `arithmetic_facts` (operator + operand ranges per part, answers
  recomputed by verify), plus `column_arithmetic`, `long_division`, `fraction_ops`, `decimal_ops`,
  `ratio_table`, `equation_solve`, `coordinate_graph`, `word_problem`.
- Math content is generated from rules with every answer recomputed, so it's cheap. Word problems come
  from ~40 sentence frames per level, with numbers filled in and checked.

## The real cost: reading passages

Every reading page needs original text. A passage can serve 2–3 pages (different question focus),
so each level needs about **70–90 original passages**, roughly **450 across the six levels**, growing
from ~130 words (Foxes) to ~600 words (Lions). Same workflow as the 7A word bank: write in batches of
~20, show them for approval, then generate. Each batch gets a reading-level check (sentence length,
word difficulty) so passages stay on their grade.

## Suggested order

Build one level at a time, bottom up: **Foxes first**. Ducklings → Cubs follow the existing structure
(no plan needed) and Ducklings is the quickest next free preview, so it can go in between.

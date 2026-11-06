# Ducklings reading (6A): word batch 2, draft for approval

**Status: approved 2026-11-06, with one change: "laugh" (#10) is replaced by "push"** (picture: a child
pushing the red toy wagon; "I can push." / "Dad can push."; people only, no animal pushes). All 40 words are
in `content/vocab/english.yaml` (`level: 6A`), drawn by `scripts/pictures/draw_batch5.py`, and used on
pages 151–190. Ducklings Reading now builds all 200 pages.

## Where things stand

| | Pages | Status |
|---|---|---|
| A Word Hunt | 1–30 | built (Chicks words, least seen first) |
| B Little Phrases | 31–100 | built (batch 1 words 1–30 on 71–100) |
| C Say a Sentence, parts 1–5 | 101–150 | built (batch 1 words 31–40 on 141–150) |
| C parts 6–9 (one new word a page) | 151–190 | built from this batch (2026-11-06) |
| C part 10 (review, no new words) | 191–200 | built (reviews these words) |

This batch completes the 80-word target. Every word lands on a Say a Sentence page, so it must fit a
sentence frame: "This is a ___." / "Here is my ___." / "Look at the ___." (things), "The ___ is red."
(colors), "The ___ can run." / "I can ___." (actions), "I eat a ___." / "I like to ___." / "I love my ___."
(my day), or "The ___ is big." / "The ___ is hot." (describing). Every word has 7 letters or fewer,
American spelling, and is something a 3-year-old knows. Phrases stay true: animals only do what they
can, colors match the picture, and only really hot or cold things are called hot or cold.

## Proposed words (40)

| # | Word | Category | Sentence it appears in | Picture needed |
|---|---|---|---|---|
| 1 | zebra | animals | The zebra can run. / I see a zebra. | zebra (stripes, mid-gray) |
| 2 | tiger | animals | The tiger can sleep. / The tiger is big. | friendly tiger |
| 3 | giraffe | animals | The giraffe can eat. / The giraffe is big. | giraffe with long neck |
| 4 | hen | animals | The hen can walk. / Look at the hen. | hen |
| 5 | ant | animals | The ant can crawl. / The ant is little. | ant |
| 6 | seal | animals | The seal can swim. | seal |
| 7 | penguin | animals | The penguin can swim. / The penguin can walk. | penguin |
| 8 | lamb | animals | The lamb can jump. / The lamb is little. | lamb |
| 9 | hug | actions | I can hug. / Mom can hug. | child hugging a teddy |
| 10 | push | actions | I can push. / Dad can push. | child pushing the red toy wagon (was "laugh", changed at approval) |
| 11 | throw | actions | I can throw. | child throwing a ball overhand |
| 12 | catch | actions | I can catch. | child catching a ball with both hands |
| 13 | crawl | actions | The ant can crawl. / I can crawl. | child crawling on hands and knees |
| 14 | splash | actions | The duck can splash. / I like to splash. | child splashing in a puddle |
| 15 | peach | food | I eat a peach. | peach |
| 16 | muffin | food | I eat a muffin. | muffin |
| 17 | toast | food | I eat some toast. | slice of toast |
| 18 | pancake | food | I eat a pancake. | pancake stack |
| 19 | yogurt | food | I eat some yogurt. | yogurt cup with spoon |
| 20 | peas | food | I eat peas. / I see green peas. | pea pod (green) |
| 21 | crayon | toys | Here is my crayon. / I like my red crayon. | one red crayon (not the color-word crayons: lying down, with a scribble) |
| 22 | wagon | toys | Here is my wagon. / The wagon is red. | red toy wagon |
| 23 | sled | toys | Here is my sled. / I see a big sled. | sled |
| 24 | blanket | home | Here is my blanket. | folded blanket |
| 25 | window | home | Look at the window. | window |
| 26 | oven | home | The oven is hot. | oven |
| 27 | pot | home | The pot is hot. | cooking pot with steam |
| 28 | fridge | home | The fridge is cold. | fridge |
| 29 | cap | clothes | Here is my cap. / I like my blue cap. | baseball cap (one color, no logo) |
| 30 | sweater | clothes | I like my green sweater. | sweater |
| 31 | pajamas | clothes | I like my blue pajamas. | pajamas (top + pants) |
| 32 | shorts | clothes | I like my red shorts. | shorts |
| 33 | sand | nature | Look at the sand. / This is some sand. | sand pile |
| 34 | shell | nature | I see a shell. / The shell is little. | seashell |
| 35 | grass | nature | The grass is green. | grass tuft |
| 36 | puddle | nature | Look at the puddle. | puddle |
| 37 | ice | nature | The ice is cold. | ice cubes |
| 38 | toe | body | Here is my toe. | foot with the big toe in focus |
| 39 | thumb | body | Here is my thumb. | thumbs-up hand |
| 40 | family | family | I love my family. | mom, dad and child together |

**Pictures:** 40 new pictures in the house style. Data to add with them (no new code): `can_do` for the
new animals and actions, `picture_colors` (wagon, crayon, cap, sweater, pajamas, shorts, peas, grass),
`sizes` (big: tiger, giraffe, zebra, sled; little: ant, lamb, shell, hen), `temperatures` (hot: oven,
pot; cold: ice, fridge). Plural words (peas, pajamas, shorts) go on the `plural` list, so they never
take "a" or "is".

**Questions for you**
1. Hot things: "The oven is hot." and "The pot is hot." teach a safety idea. OK, or keep hot to sun and soup?
2. Chicks still needs 80 more words (its batches 4–5). Should those avoid all of these 40, so each word
   is new in only one level? (The plan assumes yes.)
3. "laugh" and "throw"/"catch" are hard to show in one still picture. Keep them, or swap for "stand" and
   "push"?
4. "family" shows three people. OK as one picture, or would you rather have "aunt" / "uncle"?

**Answers (user, 2026-11-06)**
1. "The oven is hot." and "The pot is hot." are OK. Hot: sun, soup, oven, pot. Cold: snow, snowman, milk, juice, ice, fridge.
2. Yes: these 40 words must not be reused as new words in Chicks batches 4–5.
3. Keep throw and catch (the ball is clearly mid-air for throw and in both hands for catch). "laugh" becomes "push".
4. "family" is one picture of mom, dad and child together.

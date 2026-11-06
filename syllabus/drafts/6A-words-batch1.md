# Ducklings reading (6A): word batch 1, draft for approval

**Status: not approved.** Nothing below has been drawn, added to the word bank, or used on a sheet.
Every 6A sheet generated so far uses only the 120 approved 7A words.

## Where things stand

| | Pages | Uses | Status |
|---|---|---|---|
| A Word Hunt (find-it grids) | 1–30 | 7A words only | built (120 slots: every 7A word once) |
| B Little Phrases, parts 1–4 | 31–70 | 7A words only | built |
| B parts 5–7 (one new word a page) | 71–100 | **30 new words** | waiting for this batch |
| C Say a Sentence, parts 1–4 | 101–140 | 7A words only | built |
| C parts 5–9 (one new word a page) | 141–190 | **50 new words** | 10 from this batch, 40 in batch 2 |
| C part 10 (review, no new words) | 191–200 | all words | built today from 7A words; will be redone once the new words exist |

- **Today's 120 words cover 120 of the 200 pages** (1–70, 101–140, 191–200). They cover **0 of the 80 new-word
  pages**, by design: those pages exist to bring in new words.
- Pages 1–30 won't change as words are added. Pages 31–70 and 101–140 can still change a little when 7A
  batches 4–5 arrive, because the phrases pick the least-seen words.
- **Recommended vocabulary target: 80 new words** (two batches of 40), against about 210 on the published
  chart. 7A took the same approach: fewer words, learned well. One new word a page keeps to "one new
  idea per sheet". Each word is then seen at least 3 times (the planner checks this; tested with 80
  made-up words). Reaching 210 would mean 2–3 new words a page across all of B and C.

## Proposed words (40)

The first 30 must fit phrases that already exist: "I can ___", "my ___" (toys, clothes, home, body,
family), "___ and ___", or a color phrase. That is why the batch opens with actions and everyday
"my" things. The last 10 are for the first sentence pages (141–150). Every word has 7 letters or fewer,
American spelling.

| # | Word | Category | Phrase or sentence it appears in | Picture needed |
|---|---|---|---|---|
| 1 | hop | actions | I can hop / The bunny can hop. | child hopping |
| 2 | sing | actions | I can sing / Mom can sing. | child singing (music notes) |
| 3 | dance | actions | I can dance | child dancing |
| 4 | nap | actions | I can nap / The cat can nap. | child napping on a pillow |
| 5 | dig | actions | The dog can dig. / I can dig | child with spade |
| 6 | walk | actions | I can walk / Grandpa can walk | child walking |
| 7 | kick | actions | I can kick | child kicking |
| 8 | wave | actions | I can wave / Dad can wave | child waving |
| 9 | read | actions | I like to read. | child with open book |
| 10 | draw | actions | I like to draw. | child drawing |
| 11 | climb | actions | The monkey can climb. | child on a ladder |
| 12 | hide | actions | I can hide / The cat can hide. | child peeking behind a box |
| 13 | face | body | my face / I wash my face. | face |
| 14 | head | body | my head / Here is my head. | head |
| 15 | knee | body | my knee | bent knee |
| 16 | finger | body | my finger | pointing finger |
| 17 | tummy | body | my tummy | child's tummy |
| 18 | jacket | clothes | my jacket / my red jacket | jacket (one color) |
| 19 | mitten | clothes | my mitten / my blue mitten | mitten (one color) |
| 20 | skirt | clothes | my skirt / my pink skirt | skirt (one color) |
| 21 | teddy | toys | my teddy | teddy bear |
| 22 | bag | toys | my bag / my red bag | backpack (one color) |
| 23 | puzzle | toys | my puzzle | jigsaw piece |
| 24 | robot | toys | my robot | friendly toy robot |
| 25 | bucket | toys | my bucket | beach bucket |
| 26 | brush | home | my brush / brush and comb | hairbrush |
| 27 | comb | home | my comb | comb |
| 28 | fork | home | my fork / fork and spoon | fork |
| 29 | sofa | home | my sofa | sofa |
| 30 | box | home | my box / This is a box. | box |
| 31 | big | describing | a big dog / The dog is big. | none: the noun's picture, drawn large |
| 32 | little | describing | a little cat / The cat is little. | none: the noun's picture, drawn small |
| 33 | hot | describing | The sun is hot. / hot soup | none: only with things listed as hot |
| 34 | cold | describing | The snow is cold. / cold milk | none: only with things listed as cold |
| 35 | puppy | animals | This is a puppy. / The puppy can run. | puppy |
| 36 | kitten | animals | I see a kitten. / The kitten can sleep. | kitten |
| 37 | chick | animals | Look at the chick. | chick |
| 38 | whale | animals | The whale can swim. | friendly whale |
| 39 | crab | animals | I see a crab. | crab |
| 40 | snail | animals | Look at the snail. | snail |

**Pictures:** 34 new pictures in the house style (all except big, little, hot, cold). The describing
words need a little code: a picture-size option and a "hot/cold things" list, like the color list.

**Questions for you**
1. Is the 80-word target (instead of about 210) OK?
2. Is "and" OK as a new function word? It is the only word on the sheets so far that the child didn't
   meet in 7A. It appears in "mom and dad" phrases (pages 51–60).
3. big/little/hot/cold: OK to add now (with the small code change), or keep 6A to nouns and actions?
4. Pages 1–30 review the 7A words in word-bank order. Once 7A has all 200 words, the 80 newest come
   back only in B/C phrases, not in the grids. Should the grids favor the words 7A showed least?
5. "The mouse can eat." shows the mouse next to the action picture, which is a child eating. Is that
   OK, or should action sentences with an animal show the animal only?
6. Actions are limited to things people can really do, because "I can ___" and "Grandma can ___" accept
   any action. That is why "fly" isn't proposed.

## Phrase frames (B, `content/phrases/english.yaml`)

| Part | Pages | Frames | Examples |
|---|---|---|---|
| 1 Color phrases | 31–40 | `{a} {color} {colored}` | a red apple, a yellow sun, blue pants |
| 2 My things | 41–50 | `my {mine}`, `my {color} {colored_mine}` | my hat, my red drum |
| 3 Two together | 51–60 | `{x} and {y}` (20 fixed pairs) | mom and dad, cup and spoon |
| 4 I can | 61–70 | `I can {action}`, `{person} can {action}` | I can jump, grandma can swim |
| 5–7 (new words) | 71–100 | all of the above | |

## Sentence frames (C)

| Part | Pages | Frames | Examples |
|---|---|---|---|
| 1 This is | 101–110 | `This is {a} {thing}.` `I see {a} {thing}.` `Here is my {mine}.` `Look at the {thing}.` | This is a bear. |
| 2 Colors | 111–120 | `I see {a} {color} {colored}.` `The {colored} is {color}.` `I like my {color} {colored_mine}.` | The banana is yellow. |
| 3 Who can | 121–130 | `The {animal} can {action}.` `I can {action}.` `{person} can {action}.` | The dog can run. |
| 4 My day | 131–140 | `I like to {action}.` `I eat {a} {eatable}.` `I wash my {washable}.` `I love my {family}.` | I wash my hair. |
| 5–10 | 141–200 | all of the above, 3 sentences a page | |

Phrases are always true to their pictures:
- Color words go only with nouns whose picture is that color (a hand-checked list of 45 pictures).
- Animals do only actions they can do (no "The fish can run.").
- Plural nouns never take "a" or "is".

# Kittens Reading (4A): word batch 1, draft

**Status: approved by the orchestrator under user delegation, 2026-11-06** (the user asked the orchestrator
to self-review and approve this batch instead of waiting). All 40 words are in `content/vocab/english.yaml`
(`level: 4A`), drawn by `scripts/pictures/draw_4A_batch1.py`, and used on Letter Teams pages 4–8 of
units 1–8 (pages 4–8, 14–18, 24–28, 34–38, 44–48, 54–58, 64–68, 74–78). Batch 2 (10 words) is in
`4A-words-batch2.md`.

## Where things stand (before this batch)

| Section | Pages | Built from approved words | Needs new words |
|---|---|---|---|
| A Letter Teams | 1–100 | 50 (pages 1–3 and 9–10 of each 10-page unit) | 50 (pages 4–8 of each unit, one new word a page) |
| B Rhyme Time | 101–140 | 40 | 0 |
| C Trace a Sentence | 141–200 | 60 | 0 |
| **Total** | 200 | **150** | **50** |

Batch 1 fills units 1–8 (40 pages): 190 of 200. Batch 2 fills units 9–10: 200 of 200.

**Recommended vocabulary target: 50** (chart: ~225; as in Chicks and Ducklings, fewer words learned well).
Every Kittens word is new once, on a Letter Teams page, and the planner brings it back on the next pages of
its unit until it has been seen 3 times. Many also come back in Rhyme Time (new rhyme partners below) and in
Trace a Sentence ("This is a ship.", "I like to eat a pretzel.").

## Rules checked for every word
Age 4, a word a young child knows; concrete and drawable; at most 7 letters; American spelling; not
already in the word bank; the page's letter team really is in the word and makes its sound (checked by
ear, recorded in `content/phonics/english.yaml`); rhymes said aloud in General American English (no eye
rhymes, no accent-only rhymes); every sentence the frames can make passes the sentence-sense scan
(`tests/test_sentence_sense.py`). Kittens is grade 1 work: these are decodable words with digraphs and
blends (RF.1.3a, RF.1.2b).

## Words (40)

| # | Word | Category | How used (letter team; rhyme; sentence) | Picture needed |
|---|---|---|---|---|
| 1 | glass | home | ss (end), gl; rhymes with grass; "Here is my glass." | glass of water |
| 2 | wall | home | ll (end); rhymes with ball; "Look at the wall." | short brick wall |
| 3 | well | nature | ll (end); rhymes with bell, shell; "I see a well." | wishing well with roof and bucket |
| 4 | bull | animals | ll (end); "The bull can run." / "The bull is big." | friendly bull |
| 5 | grill | home | ll (end), gr; rhymes with hill; "Look at the grill." | backyard grill |
| 6 | ship | vehicles | sh; "I see a ship." | ship on waves |
| 7 | dish | home | sh; rhymes with fish; "Here is my dish." | dish (shallow bowl) |
| 8 | shark | animals | sh; "The shark can swim." / "The shark is big." | friendly shark |
| 9 | shelf | home | sh; "Look at the shelf." | shelf with books |
| 10 | shower | home | sh; "This is a shower." | shower head with water drops |
| 11 | bench | home | ch; "I see a bench." | park bench |
| 12 | watch | clothes | tch; "Here is my watch." | wristwatch (no brand) |
| 13 | couch | home | ch; "Look at the couch." | couch (American word for sofa) |
| 14 | beach | nature | ch; rhymes with peach; "I see a beach." | sand, sea, umbrella |
| 15 | cheek | body | ch; "Here is my cheek." (body words take "my", see note) | child's face, cheek marked |
| 16 | tooth | body | th; "Here is my tooth." | one tooth |
| 17 | path | nature | th; "Look at the path." | path between grass |
| 18 | moth | animals | th; "I see a moth." / "The moth is little." | moth |
| 19 | wheel | vehicles | wh; rhymes with seal; "Look at the wheel." | wheel |
| 20 | whisk | home | wh; "This is a whisk." | kitchen whisk |
| 21 | lock | home | ck; rhymes with sock, clock, rock; "I see a lock." | padlock |
| 22 | pocket | clothes | ck; rhymes with rocket; "Here is my pocket." | jeans pocket |
| 23 | chicken | animals | ck, ch; "The chicken can walk." | chicken |
| 24 | sticker | toys | ck, st; "Here is my sticker." | star sticker |
| 25 | cracker | food | ck, cr; "I eat a cracker." | square cracker |
| 26 | flag | toys | fl; rhymes with bag; "Here is my flag." | plain flag (no country) |
| 27 | glove | clothes | gl; "I like my green glove." | winter glove |
| 28 | plant | nature | pl, nt; rhymes with ant; "Look at the plant." | potted plant |
| 29 | glue | toys | gl; rhymes with shoe; "Here is my glue." | glue bottle (no brand) |
| 30 | slipper | clothes | sl; "Here is my slipper." | slipper |
| 31 | brick | home | br, ck; rhymes with chick, kick, stick; "I see a brick." | one brick |
| 32 | present | toys | pr, nt; "Here is my present." | wrapped gift with bow |
| 33 | pretzel | food | pr; "I eat a pretzel." | soft pretzel |
| 34 | tray | home | tr; "Look at the tray." | tray |
| 35 | trumpet | toys | tr; "Here is my trumpet." | toy trumpet |
| 36 | snake | animals | sn; rhymes with cake; "I see a snake." | friendly snake |
| 37 | sponge | home | sp; "This is a sponge." | sponge |
| 38 | swan | animals | sw; "The swan can swim." | swan |
| 39 | skate | toys | sk; rhymes with plate; "Here is my skate." | roller skate |
| 40 | stool | home | st; "Look at the stool." | step stool |

Row 15 note: "cheek" goes in the body category; the "I wash my ___" frame only takes hand, hair and face,
so it never makes "I wash my cheek."; body words are not in the `thing` slot, so it is "Here is my cheek."
(like "Here is my nose." in Ducklings Reading).

## Self-review (orchestrator delegation)
- All 40 are 7 letters or fewer, none in the bank (checked by script), American (couch, cracker, pretzel).
- Nothing scary: shark, snake and bull are drawn friendly; no brands on the watch, glue or flag.
- Rhymes added (hand-checked): ball/wall, grass/glass, bell/shell/well, hill/grill, fish/dish, peach/beach,
  seal/wheel, sock/clock/rock/lock, rocket/pocket, chick/kick/stick/brick, bag/flag, ant/plant, shoe/glue,
  cake/snake, plate/skate.
- Sentence lists updated by hand: `eatable` (cracker, pretzel), `ownable` (toys, clothes and home things he
  owns), `can_do` (bull, shark, chicken, snake, swan), `sizes` (bull, shark big; moth little).

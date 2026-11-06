# Chicks reading (7A): word batch 4, draft for approval

**Status: approved 2026-11-06**, with one change: **hose** replaces glasses (#20). Decisions: bubbles, rice,
noodles are `mass: true` (and plural); brown and black stay as crayon swatches; ride, roll, cook, pour kept;
chin and neck drawn as a face with the part lightly tinted. Drawn (`scripts/pictures/draw_7A_batch4.py`),
added to the word bank and used on pages 61–80.

## Where things stand

| | Pages | Status |
|---|---|---|
| A First Words (2 new words a page) | 1–60 | built (batches 1–3, 120 words) |
| A pages 61–80 | 61–80 | **waiting for this batch (40 words, words 121–160)** |
| A pages 81–100 | 81–100 | waiting for batch 5 (words 161–200) |
| B Find It grids | 101–140 | built; will change as words are added |
| C Tiny Stories | 141–200 | built; will change as words are added |

Each page 61–80 shows two of these words as big picture cards (picture + word, or picture + word + a short
sentence read aloud to the child). 3–10 pages later each word comes back in the small "Say it again" strip,
then again in the Find It grids and Tiny Stories, where the planner gives slots to the words the strip
served least, so every word is seen at least 3 times.

Rules followed: words a 3-year-old knows, concrete and easy to picture, 7 letters or fewer, American
spelling, nothing scary or branded. Card sentences have 6 words or fewer and contain the word. None of the
120 Chicks words or the 80 Ducklings words are reused. Pairs on one page are from different categories and
don't look alike.

## Proposed words (40)

| # | Word | Category | Sentence on its card | Picture needed |
|---|---|---|---|---|
| 1 | fox | animals | The fox has a fluffy tail. | orange fox, sitting, big tail |
| 2 | sink | home | Wash your hands at the sink. | bathroom sink with faucet |
| 3 | lemon | food | The lemon is sour. | whole lemon with a leaf |
| 4 | scooter | vehicles | I ride my scooter. | kick scooter, side view |
| 5 | drink | actions | I drink my milk. | child drinking from a cup |
| 6 | nest | nature | Eggs sit in the nest. | twig nest with 3 eggs |
| 7 | belt | clothes | Dad wears a belt. | belt with buckle, curled |
| 8 | koala | animals | The koala hugs the tree. | koala holding a trunk |
| 9 | rice | food (`mass: true`) | I eat rice with a spoon. | bowl of rice |
| 10 | rocket | vehicles | The rocket goes up, up! | toy-style rocket with flame |
| 11 | chin | body | Tap your chin. | child face, chin highlighted |
| 12 | puppet | toys | My puppet says hello. | sock/hand puppet with eyes |
| 13 | smile | actions | Show me a big smile. | smiling child face |
| 14 | broom | home | Sweep with the broom. | broom, upright |
| 15 | potato | food | Mom cooks a potato. | brown potato |
| 16 | parrot | animals | The parrot can talk. | parrot on a perch |
| 17 | bubbles | toys (`mass: true`) | I blow big bubbles. | bubble wand + 3 bubbles |
| 18 | deer | animals | The deer runs fast. | deer with small antlers |
| 19 | ride | actions | I ride my bike. | child riding a tricycle |
| 20 | ~~glasses~~ **hose** | home | We water flowers with the hose. | green coiled garden hose with nozzle |
| 21 | tomato | food | The tomato is red. | round tomato with stem |
| 22 | crib | home | The baby sleeps in a crib. | crib with bars |
| 23 | brown | colors (`needs_color`) | The bear is brown. | brown crayon (`kind: color_swatch`) |
| 24 | camel | animals | The camel has a hump. | camel, one hump, side view |
| 25 | pour | actions | I pour the milk. | child pouring milk from a jug into a cup |
| 26 | feather | nature | The feather is soft. | single feather |
| 27 | bib | clothes | The baby wears a bib. | bib with ties |
| 28 | cherry | food | A cherry is small. | two cherries on a stem |
| 29 | neck | body | I wash my neck. | child head and shoulders, neck shown |
| 30 | tent | toys | We sleep in a tent. | small camping tent |
| 31 | cook | actions | Dad and I cook. | child stirring a pot |
| 32 | acorn | nature | The squirrel has an acorn. | acorn with cap |
| 33 | noodles | food (`mass: true`) | I slurp my noodles. | bowl of noodles with fork |
| 34 | donkey | animals | The donkey says hee-haw. | gray donkey, long ears |
| 35 | black | colors (`needs_color`) | The cat is black. | black crayon (`kind: color_swatch`) |
| 36 | bathtub | home | I sit in the bathtub. | bathtub with bubbles on top |
| 37 | roll | actions | I roll the ball. | child rolling a ball on the floor |
| 38 | pumpkin | food | The pumpkin is big and orange. | round pumpkin with stem |
| 39 | hill | nature | We run up the hill. | green hill with a small tree |
| 40 | rug | home | The cat naps on the rug. | striped oval rug |

Pages: 61 = 1+2, 62 = 3+4, … 80 = 39+40.

Category mix: animals 6, food 7, home 5, actions 6, nature 4, clothes 3, toys 3, vehicles 2, body 2, colors 2.

## Notes

- **New pictures: 40** (none of these slugs exist in `assets/pictures/`). Two are crayon swatches
  (brown, black), exempt from the lightness rule. Watch the lightness rule on dark subjects: black is a
  swatch, but deer, donkey, potato and the brown things must still have a 50–75% main fill.
- **Story frames:** all words fit existing frames: actions use "I can {w}." / "I like to {w}.";
  body, nature and colors use their category frames; the rest use the default frames ("I see {a} {w}.",
  "Here is my {w}."). Mass words get "some" ("I have some rice."). No new frames needed.
- Card sentences use some words the child hasn't met yet (sour, slurp, squirrel, sweep); that is allowed
  because the card sentence is read *to* the child.

## Questions (with my recommendation)

1. **glasses** as `mass: true` gives "I see some glasses", which can read like drinking glasses. Without
   `mass` it gives "I see a glasses". Recommend: keep it with `mass: true` (like pants); swap for **hose** if you
   prefer (gloves is too close to the Ducklings word mitten).
2. **bubbles**: `mass: true` ("I see some bubbles") reads fine. Recommend yes.
3. **black**: a black crayon on a black-and-white page is fine, but the card word "black" next to a solid
   dark picture is heavy. Alternative: **white** (harder: white crayon on white paper) or **gray**.
   Recommend black.
4. **tent** filed under toys (there is no outdoors category). Alternative: nature. Recommend toys, so the
   nature frames ("I see the tent") don't apply oddly; either works.
5. **ride / push / roll / cook** in "I can {w}." stories read a little bare ("I can ride."). Recommend
   accept; they are short and true.
6. **chin / neck** pictures need a child face with the part pointed out, which is harder to read than an
   object. Recommend keep them (body words are core) and draw a small arrow-free highlight (tinted area).

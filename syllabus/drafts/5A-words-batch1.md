# Bunnies Reading (5A): word batch 1, draft for approval

**Status: draft, waiting for the user's OK.** Nothing here is drawn or in `content/vocab/english.yaml` yet.

## Where things stand

The 280 approved words (200 Chicks + 80 Ducklings) already build **165 of 200 pages**. Verify gives
0 errors and 5 warnings, all of them pages waiting for new words.

| Section (public name) | Pages | Built now | Waiting for |
|---|---|---|---|
| A Letter Trails | 1–70 | 66 | z (52–53: only "zebra"), q (66–67: no q word at all) |
| B Sound Pieces, parts 1–6 | 71–130 | 60 | — |
| B Sound Pieces, parts 7–8 (one new word a page) | 131–150 | 0 | 20 new short-vowel words |
| C Letter Pairs | 151–160 | 9 | q (156: p, q, r) |
| D Word Trails, parts 1–3 | 161–190 | 30 | — |
| D Word Trails, part 4 (traces this level's new words) | 191–200 | 0 | any of this batch |

**Rules for these words:** something a 4-year-old knows, concrete and drawable, at most 7 letters,
American spelling, not already in the bank. They are either letter words (they start with the letter's
usual sound) or **one-syllable short-vowel words that complete a rhyming family**, which is the K–1
decoding work this level is for (c-at, h-at, **b-at**). No sentences are printed in this level yet, so
none are needed. After approval, each word also goes into `content/sounds/english.yaml`: `letter_words`
for the q and z words, and `rimes` for the others.

Recommended vocabulary target: **23 words**, the 23 marked *needed*. The chart's +113 is far more than
this level's pages use. Letters and sounds are the point here, and "fewer words, learned well" is the
rule we chose. Each new word is new once and comes back at least twice more. This is checked by
`tests/test_bunnies_reading.py::test_new_words_fill_every_page`: with these words all 200 pages are
planned and every new word is seen 3 or more times. The 8 *optional* words would improve pages that are
already built (a true first-sound word for i, o, u, v and y). Those pages would change once they're added.

## Proposed words (31: 23 needed + 8 optional)

| # | Word | Category | How used | Picture needed | Unlocks |
|---|---|---|---|---|---|
| 1 | queen | people | trace word (q), letter pair Qq, word trace | smiling queen with a crown, head and shoulders | needed: pages 66–67, 156 |
| 2 | quilt | home | trace word (q), letter pair, word trace | folded patchwork quilt | needed: 66–67 |
| 3 | zipper | clothes | trace word (z), letter pair Zz, word trace | big zipper, half open | needed: 52–53 |
| 4 | bat | toys | sound part b + at (with cat, hat); word trace | toy baseball bat (not the animal) | needed: 131 |
| 5 | pen | home | sound part p + en (with hen); word trace | pen with its cap off | needed: 132 |
| 6 | pin | home | sound part p + in (with chin); word trace | safety pin, closed | needed: 133 |
| 7 | mop | home | sound part m + op (with hop); word trace | mop with a gray string head | needed: 134 |
| 8 | bug | animals | sound part b + ug (with rug, hug); word trace | friendly green beetle | needed: 135 |
| 9 | mat | home | sound part m + at; word trace | striped doormat | needed: 136 |
| 10 | net | toys | sound part n + et; word trace | butterfly net | needed: 137 |
| 11 | fin | animals | sound part f + in; word trace | a fish with its fin marked (hard to show, see note) | needed: 138 |
| 12 | top | toys | sound part t + op; word trace | spinning top toy | needed: 139 |
| 13 | mug | home | sound part m + ug; word trace | mug with a heart, no steam | needed: 140 |
| 14 | pan | home | sound part p + an (with van, fan); word trace | frying pan (empty) | needed: 141 |
| 15 | jet | vehicles | sound part j + et (with net); word trace | jet plane from the side (different from "plane") | needed: 142 |
| 16 | wig | toys | sound part w + ig (with pig, dig); word trace | curly dress-up wig | needed: 143 |
| 17 | log | nature | sound part l + og (with dog, frog); word trace | log with rings at the end | needed: 144 |
| 18 | nut | food | sound part n + ut; word trace | peanut in its shell | needed: 145 |
| 19 | map | toys | sound part m + ap (with cap, nap, clap); word trace | folded treasure map with a dotted path | needed: 146 |
| 20 | web | nature | sound part w + eb; word trace | spider web (no spider) | needed: 147 |
| 21 | lid | home | sound part l + id; word trace | pot lid with a knob | needed: 148 |
| 22 | jam | food | sound part j + am; word trace | jar of jam | needed: 149 |
| 23 | tub | home | sound part t + ub; word trace | small round wash tub | needed: 150 |
| 24 | igloo | home | trace word (i) | snow igloo | optional: i pages (now pig, fish) |
| 25 | insect | animals | trace word (i) | hard to show one picture for it, see note | optional: i pages |
| 26 | otter | animals | trace word (o) | otter floating on its back | optional: o pages (now octopus + dog) |
| 27 | ox | animals | trace word (o), sound part? (no onset: trace only) | ox with small horns | optional: o pages |
| 28 | uncle | family | trace word (u) | smiling man waving | optional: u pages (now sun, jump) |
| 29 | vest | clothes | trace word (v); sound part v + est (with nest) | puffy vest | optional: v pages (now van + oven) |
| 30 | vase | home | trace word (v) | vase with one flower | optional: v pages |
| 31 | yarn | toys | trace word (y) | ball of yarn | optional: y pages (now yawn, yogurt) |

Notes for the user:
- **fin (#11):** a fin alone is hard to picture clearly. A swap with an easy picture is **bun**
  (b + un, rhymes with sun and run): a round bread roll. I recommend **bun** instead of fin.
- **insect (#25):** "insect" is a whole category. We already have bee, ant and ladybug, so there's no
  single clear picture for it. I suggest dropping it unless you like it.
- **umbrella** would be the classic u word, but it has 8 letters (our limit is 7), so it's left out.
  "uncle" is the closest picturable u word, though a picture can't really show "uncle". Optional.
- New sound-piece words are introduced in this order (one a page, 131–150): the table order 4–23.
  Each one sits next to its rhyming mates.

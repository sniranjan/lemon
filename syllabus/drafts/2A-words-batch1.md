# Cubs Reading (english 2A): word batch 1 (40 words)

Status: **approved by the orchestrator under user delegation, 2026-11-06** (self-reviewed against the
rules below; the user delegated word-table approvals on 2026-11-06, see memory `autonomy-content.md`).

Cubs is age 5 with content grade 2 (ladder.yaml). Its section "Kinds of Words" teaches naming, doing and
describing words (L.2.1e, L.2.5a, L.1.1b, L.1.1f), so this batch is grammar words rather than phonics words:
16 two-syllable naming words (pictured), 12 doing words (pictured: a child doing it) and 12 describing words
(no picture, like big / little / hot / cold). One new word a page on Kinds of Words pages 61–100, in file order.

Checks made on the table:
- none is already in `content/vocab/english.yaml`; none is on the Bunnies/Kittens draft lists seen in the
  sibling worktrees (queen, quilt, zipper, bat, pen, pin, mop, bug, mat, net, bun, top, mug, pan, jet, wig,
  log, nut, map, web, lid, jam, tub, igloo, otter, ox, vest, vase, yarn; glass … stool incl. skate, plant,
  pocket, pretzel; ring, skunk, pond, stamp, jar);
- every word is a common everyday word for a 5-year-old; nothing scary, branded or unsafe;
- American spelling; every card sentence is true and passes the sentence-sense scan
  (`tests/test_sentence_sense.py`);
- word classes are unambiguous in a child's everyday use (no "brush", "swing", "paint": those are kept out of
  the hand-checked lists in `content/grammar/english.yaml`).

| # | Word | Kind | Category | Page | Card sentence (read together) |
|---|---|---|---|---|---|
| 1 | pencil | naming | home | 61 | I write my name with a pencil. |
| 2 | button | naming | clothes | 62 | My coat has a big button. |
| 3 | ribbon | naming | toys | 63 | She ties a ribbon in her hair. |
| 4 | helmet | naming | clothes | 64 | I wear a helmet on my bike. |
| 5 | magnet | naming | toys | 65 | The magnet sticks to the fridge. |
| 6 | candle | naming | home | 66 | There is a candle on the cake. |
| 7 | napkin | naming | home | 67 | I wipe my mouth with a napkin. |
| 8 | kettle | naming | home | 68 | The kettle whistles when the water is hot. |
| 9 | rabbit | naming | animals | 69 | The rabbit has long ears. |
| 10 | robin | naming | animals | 70 | A robin sings in the tree. |
| 11 | carry | doing | actions | 71 | I carry the box to my room. |
| 12 | bake | doing | actions | 72 | We bake cookies with Grandma. |
| 13 | sweep | doing | actions | 73 | I sweep the floor with a broom. |
| 14 | skip | doing | actions | 74 | I skip down the path to the park. |
| 15 | tiptoe | doing | actions | 75 | We tiptoe past the sleeping baby. |
| 16 | wiggle | doing | actions | 76 | I wiggle my toes. |
| 17 | giggle | doing | actions | 77 | We giggle at Dad's funny joke. |
| 18 | munch | doing | actions | 78 | I munch a crunchy apple. |
| 19 | sniff | doing | actions | 79 | I sniff the pretty flower. |
| 20 | stir | doing | actions | 80 | I stir the soup with a spoon. |
| 21 | soft | describing | describing | 81 | My pillow is soft. |
| 22 | fluffy | describing | describing | 82 | The lamb has fluffy wool. |
| 23 | tiny | describing | describing | 83 | An ant is tiny. |
| 24 | shiny | describing | describing | 84 | My new bike is shiny. |
| 25 | sticky | describing | describing | 85 | Honey is sticky. |
| 26 | noisy | describing | describing | 86 | The drum is noisy. |
| 27 | quiet | describing | describing | 87 | We are quiet when the baby sleeps. |
| 28 | muddy | describing | describing | 88 | My boots are muddy. |
| 29 | sleepy | describing | describing | 89 | The baby is sleepy. |
| 30 | hungry | describing | describing | 90 | I am hungry for lunch. |
| 31 | tulip | naming | nature | 91 | A red tulip grows in the garden. |
| 32 | scrub | doing | actions | 92 | I scrub my hands with soap. |
| 33 | pony | naming | animals | 93 | I ride a brown pony at the farm. |
| 34 | gentle | describing | describing | 94 | Be gentle with the kitten. |
| 35 | hamster | naming | animals | 95 | The hamster runs on its wheel. |
| 36 | listen | doing | actions | 96 | I listen to the birds sing. |
| 37 | sandwich | naming | food | 97 | Mom packs a sandwich for my lunch. |
| 38 | silly | describing | describing | 98 | Dad makes a silly face. |
| 39 | pebble | naming | nature | 99 | I find a smooth gray pebble. |
| 40 | lizard | naming | animals | 100 | A green lizard sits on a warm rock. |

Pictures to draw (28, house style, `scripts/pictures/draw_2A_batch1.py`): the 16 naming words, and the 12 doing
words as a child doing the action. Colors to match the sentences: tulip red, pony brown, lizard green,
pebble gray, robin with a red-orange chest.

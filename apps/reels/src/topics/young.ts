// Topic reels for the four youngest levels (Chicks, Ducklings, Bunnies, Kittens): 4 topics each, 5 questions.
// Every question comes from the section named above it; words, rhymes and sounds come from the
// hand-checked lists in content/ (vocab, phrases, sounds, phonics). Pencil skills are left out (not a quiz).
import type { TopicSpec } from "../challenges";

export const TOPICS_YOUNG: TopicSpec[] = [
  // ---------------------------------------------------------------- Chicks (age 3, Pre-K)
  // 7A-A Picture Words, pages 1–100: picture + word card, the child says the word back (7A word bank).
  {
    level: "chicks",
    topic: "Picture Words",
    seconds: 5,
    questions: [
      { prompt: "What is this?", pic: "ball", big: "?", answer: "ball" },
      { prompt: "What is this?", pic: "apple", big: "?", answer: "apple" },
      { prompt: "Say the word!", pic: "spoon", big: "?", answer: "spoon" },
      { prompt: "And this one?", pic: "turtle", big: "?", answer: "turtle" },
      { prompt: "Tricky one!", pic: "cactus", big: "?", answer: "cactus" },
    ],
  },
  // 7A-B Find It, pages 101–140: review grid of 4 known pictures, "find it" game.
  {
    level: "chicks",
    topic: "Find It",
    seconds: 5,
    questions: [
      { prompt: "Where is the cup?", choices: [{ pic: "dog" }, { pic: "cup" }, { pic: "tree" }, { pic: "car" }], correct: 1 },
      { prompt: "Where is the hat?", choices: [{ pic: "hat" }, { pic: "fish" }, { pic: "bed" }, { pic: "sun" }], correct: 0 },
      { prompt: "Where is the bus?", choices: [{ pic: "bike" }, { pic: "boat" }, { pic: "plane" }, { pic: "bus" }], correct: 3 },
      { prompt: "Where is the moon?", choices: [{ pic: "sun" }, { pic: "star" }, { pic: "moon" }, { pic: "cloud" }], correct: 2 },
      { prompt: "Where is the owl?", choices: [{ pic: "parrot" }, { pic: "owl" }, { pic: "duck" }, { pic: "bird" }], correct: 1 },
    ],
  },
  // 6A-A Counting to 5 (pages 1–30) and 6A-B Counting to 10 (pages 31–100): rows of N pictures, count aloud.
  {
    level: "chicks",
    topic: "Counting",
    seconds: 5,
    questions: [
      { prompt: "How many bees?", row: { pic: "bee", n: 2 }, big: "?", answer: "2" },
      { prompt: "How many stars?", row: { pic: "star", n: 3 }, big: "?", answer: "3" },
      { prompt: "How many fish?", row: { pic: "fish", n: 4 }, big: "?", answer: "4" },
      { prompt: "How many cookies?", row: { pic: "cookie", n: 5 }, big: "?", answer: "5" },
      { prompt: "How many balls?", row: { pic: "ball", n: 8 }, big: "?", answer: "8" },
    ],
  },
  // 6A-C Reading Numbers, pages 101–150: read numerals 1–10 aloud; point to the right numeral.
  {
    level: "chicks",
    topic: "Read the Numbers",
    seconds: 5,
    questions: [
      { prompt: "What number is this?", big: "3", answer: "three" },
      { prompt: "Which one is 2?", choices: [{ label: "2" }, { label: "5" }, { label: "7" }], correct: 0 },
      { prompt: "Can they read it?", big: "5", answer: "five" },
      { prompt: "Which one is 6?", choices: [{ label: "9" }, { label: "6" }, { label: "8" }], correct: 1, note: "6 and 9 look alike!" },
      { prompt: "Which one is 10?", choices: [{ label: "7" }, { label: "1" }, { label: "10" }], correct: 2 },
    ],
  },

  // ---------------------------------------------------------------- Ducklings (age 3, K)
  // 6A-B Little Phrases, pages 31–100: parts "Color phrases" (a red apple, colors from picture_colors)
  // and "Two together" (pairs: shoe and sock, table and chair).
  {
    level: "ducklings",
    topic: "Little Phrases",
    seconds: 5,
    questions: [
      { prompt: "Find a red one", choices: [{ pic: "ball" }, { pic: "frog" }, { pic: "apple" }, { pic: "banana" }], correct: 2, note: "a red apple" },
      { prompt: "Find a blue one", choices: [{ pic: "car" }, { pic: "sock" }, { pic: "tree" }, { pic: "duck" }], correct: 1, note: "a blue sock" },
      { prompt: "Shoe and…?", choices: [{ pic: "cup" }, { pic: "fish" }, { pic: "sock" }, { pic: "tree" }], correct: 2, note: "shoe and sock" },
      { prompt: "Table and…?", choices: [{ pic: "chair" }, { pic: "bus" }, { pic: "frog" }, { pic: "apple" }], correct: 0, note: "table and chair" },
      { prompt: "Find a green one", choices: [{ pic: "pig" }, { pic: "cup" }, { pic: "sun" }, { pic: "frog" }], correct: 3, note: "a green frog" },
    ],
  },
  // 6A-C Say a Sentence, pages 101–200: parts "This is", "Colors", "Who can" (can_do table) and
  // "describe" (temperatures: snow is cold).
  {
    level: "ducklings",
    topic: "Say a Sentence",
    seconds: 5,
    questions: [
      { prompt: "Finish the sentence", pic: "cat", big: "This is a ?", answer: "cat" },
      { prompt: "What color is it?", pic: "banana", big: "The banana is ?", answer: "yellow" },
      { prompt: "Who can hop?", choices: [{ pic: "cow" }, { pic: "car" }, { pic: "bunny" }, { pic: "fish" }], correct: 2, note: "The bunny can hop." },
      { prompt: "Hot or cold?", pic: "snow", big: "The snow is ?", answer: "cold" },
      { prompt: "Who can climb?", choices: [{ pic: "fish" }, { pic: "cow" }, { pic: "duck" }, { pic: "monkey" }], correct: 3, note: "The monkey can climb." },
    ],
  },
  // 5A-A Numbers to 30, pages 1–100: read numbers 11–30 (shown with ten-frames on the sheets).
  {
    level: "ducklings",
    topic: "Read the Numbers",
    seconds: 5,
    questions: [
      { prompt: "Read this number!", big: "4", answer: "four" },
      { prompt: "Read this number!", big: "7", answer: "seven" },
      { prompt: "Which one is 9?", choices: [{ label: "6" }, { label: "9" }], correct: 1, note: "6 and 9 look alike!" },
      { prompt: "Read this number!", big: "10", answer: "ten" },
      { prompt: "Can they read it?", big: "15", answer: "fifteen" },
    ],
  },
  // 5A-B/C/D Counting On to 30, 40 and 50, pages 101–190: number tracks with empty boxes to say aloud.
  {
    level: "ducklings",
    topic: "Counting On",
    seconds: 5,
    questions: [
      { prompt: "What comes next?", big: "1, 2, ?", answer: "3" },
      { prompt: "What comes next?", big: "4, 5, ?", answer: "6" },
      { prompt: "What's missing?", big: "6, ?, 8", answer: "7" },
      { prompt: "What comes next?", big: "8, 9, ?", answer: "10" },
      { prompt: "Past ten!", big: "11, 12, ?", answer: "13" },
    ],
  },

  // ---------------------------------------------------------------- Bunnies (age 4, K–1)
  // 5A-A Letter Trails, pages 1–70: each letter comes with two picture words that start with its sound
  // (content/sounds/english.yaml letter_words).
  {
    level: "bunnies",
    topic: "Letter Sounds",
    seconds: 5,
    questions: [
      { prompt: "Starts with m?", choices: [{ pic: "sun" }, { pic: "moon" }, { pic: "dog" }, { pic: "cup" }], correct: 1 },
      { prompt: "Starts with b?", choices: [{ pic: "fish" }, { pic: "hat" }, { pic: "cup" }, { pic: "bus" }], correct: 3 },
      { prompt: "Starts with t?", choices: [{ pic: "turtle" }, { pic: "pig" }, { pic: "moon" }, { pic: "egg" }], correct: 0 },
      { prompt: "Starts with p?", choices: [{ pic: "bear" }, { pic: "dog" }, { pic: "pig" }, { pic: "bus" }], correct: 2, note: "bear and bus start with b" },
      { prompt: "Starts with l?", choices: [{ pic: "rock" }, { pic: "lemon" }, { pic: "nest" }, { pic: "fox" }], correct: 1 },
    ],
  },
  // 5A-B Sound Pieces, pages 71–150: short-vowel words split into onset + rime ("s" "un"), then the
  // whole word (content/sounds/english.yaml rimes).
  {
    level: "bunnies",
    topic: "Sound Pieces",
    seconds: 5,
    questions: [
      { prompt: "Put the sounds together", big: "s + un = ?", answer: "sun" },
      { prompt: "Put the sounds together", big: "h + en = ?", answer: "hen" },
      { prompt: "Put the sounds together", big: "p + ig = ?", answer: "pig" },
      { prompt: "What's the end part?", pic: "rug", big: "r + ?", answer: "ug" },
      { prompt: "What's the first sound?", pic: "bed", big: "? + ed", answer: "b" },
    ],
  },
  // 5A-C Letter Pairs, pages 151–160: review rows of letters with their capitals.
  {
    level: "bunnies",
    topic: "Letter Pairs",
    seconds: 5,
    questions: [
      { prompt: "Its small letter?", big: "M", choices: [{ label: "n" }, { label: "m" }], correct: 1 },
      { prompt: "Its small letter?", big: "T", choices: [{ label: "t" }, { label: "f" }], correct: 0 },
      { prompt: "Its small letter?", big: "G", choices: [{ label: "q" }, { label: "g" }], correct: 1 },
      { prompt: "Its small letter?", big: "D", choices: [{ label: "d" }, { label: "b" }], correct: 0 },
      { prompt: "Its small letter?", big: "Q", choices: [{ label: "p" }, { label: "q" }], correct: 1 },
    ],
  },
  // 4A-B…E Writing Numbers to 10, 20, 30 and 50, pages 41–200: tracks with empty boxes to write the
  // missing numbers (fill mode).
  {
    level: "bunnies",
    topic: "Missing Numbers",
    seconds: 5,
    questions: [
      { prompt: "What's missing?", big: "2, 3, ?, 5", answer: "4" },
      { prompt: "What's missing?", big: "5, ?, 7", answer: "6" },
      { prompt: "What's missing?", big: "7, 8, ?, 10", answer: "9" },
      { prompt: "What's missing?", big: "12, ?, 14", answer: "13" },
      { prompt: "What's missing?", big: "19, ?, 21", answer: "20" },
    ],
  },

  // ---------------------------------------------------------------- Kittens (age 4, grade 1)
  // 4A-A Letter Teams, pages 1–100: sh, ch, th (parts 4–12), ck (13–15), r-blends (19–21)
  // (content/phonics/english.yaml letter_teams).
  {
    level: "kittens",
    topic: "Letter Teams",
    seconds: 5,
    questions: [
      { prompt: "Starts with sh?", choices: [{ pic: "sheep" }, { pic: "chair" }, { pic: "cat" }, { pic: "tree" }], correct: 0 },
      { prompt: "Starts with ch?", choices: [{ pic: "shoe" }, { pic: "thumb" }, { pic: "cherry" }, { pic: "dog" }], correct: 2 },
      { prompt: "Starts with th?", choices: [{ pic: "whale" }, { pic: "thumb" }, { pic: "sock" }, { pic: "chick" }], correct: 1 },
      { prompt: "Ends with ck?", choices: [{ pic: "ball" }, { pic: "fish" }, { pic: "sun" }, { pic: "sock" }], correct: 3 },
      { prompt: "Starts with fr?", choices: [{ pic: "flower" }, { pic: "frog" }, { pic: "drum" }, { pic: "tree" }], correct: 1, note: "flower is fl, drum is dr" },
    ],
  },
  // 4A-B Rhyme Time, pages 101–140: "Which one rhymes" (parts 2–3) and "Odd one out" (part 4), from the
  // hand-checked rhyme groups; wrong choices have a different vowel sound.
  {
    level: "kittens",
    topic: "Rhyme Time",
    seconds: 5,
    questions: [
      { prompt: "Rhymes with bug?", choices: [{ pic: "cat", label: "cat" }, { pic: "rug", label: "rug" }, { pic: "pig", label: "pig" }], correct: 1 },
      { prompt: "Rhymes with fox?", choices: [{ pic: "box", label: "box" }, { pic: "fish", label: "fish" }, { pic: "bus", label: "bus" }], correct: 0 },
      { prompt: "Rhymes with moon?", choices: [{ pic: "cake", label: "cake" }, { pic: "tree", label: "tree" }, { pic: "spoon", label: "spoon" }], correct: 2 },
      { prompt: "Odd one out?", choices: [{ pic: "coat", label: "coat" }, { pic: "sun", label: "sun" }, { pic: "goat", label: "goat" }], correct: 1, note: "coat and goat rhyme" },
      { prompt: "Odd one out?", choices: [{ pic: "fish", label: "fish" }, { pic: "snail", label: "snail" }, { pic: "whale", label: "whale" }], correct: 0, note: "snail and whale rhyme" },
    ],
  },
  // 3A-C Plus One (up to 60 + 1 by part 5), 3A-D Plus Two (up to 32 + 2), 3A-E Plus Three (up to 21 + 3).
  {
    level: "kittens",
    topic: "Adding 1, 2, 3",
    seconds: 5,
    questions: [
      { prompt: "Plus one!", big: "2 + 1 = ?", answer: "3" },
      { prompt: "Plus one!", big: "4 + 1 = ?", answer: "5" },
      { prompt: "Plus two!", big: "3 + 2 = ?", answer: "5" },
      { prompt: "Plus two!", big: "6 + 2 = ?", answer: "8" },
      { prompt: "Plus three!", big: "7 + 3 = ?", answer: "10" },
    ],
  },
  // 3A-A What Comes Next to 100 (pages 1–60) and 3A-B What Comes Next to 120 (pages 61–70).
  {
    level: "kittens",
    topic: "What Comes Next",
    seconds: 5,
    questions: [
      { prompt: "What comes next?", big: "5, 6, ?", answer: "7" },
      { prompt: "What comes next?", big: "9, 10, ?", answer: "11" },
      { prompt: "What comes next?", big: "14, 15, ?", answer: "16" },
      { prompt: "What comes next?", big: "19, 20, ?", answer: "21" },
      { prompt: "What comes next?", big: "99, ?", answer: "100" },
    ],
  },
];

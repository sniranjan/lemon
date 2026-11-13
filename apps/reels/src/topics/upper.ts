// Topic reels for Owls, Otters and Pandas: one syllabus section (or one skill inside it) per reel.
// Every answer is checked twice by hand; skills match syllabus/english/R4–R6.yaml and syllabus/math/M4–M6.yaml.
import type { TopicSpec } from "../challenges";

export const TOPICS_UPPER: TopicSpec[] = [
  // ---------------------------------------------------------------- Owls (age 7, grade 4 work)

  // M4-E Factors and Multiples (factor pairs, multiples, prime or composite; numbers 1–100)
  {
    level: "owls",
    topic: "Factors & primes",
    seconds: 4,
    questions: [
      { prompt: "Is 7 a factor of 42?", choices: [{ label: "yes" }, { label: "no" }], correct: 0, note: "6 × 7 = 42" },
      { prompt: "Find the factor pair", big: "48 = 6 × ?", answer: "8" },
      { prompt: "Which one is prime?", choices: [{ label: "21" }, { label: "23" }, { label: "27" }], correct: 1, note: "23 is only 1 × 23" },
      { prompt: "Which is NOT a multiple of 6?", choices: [{ label: "36" }, { label: "54" }, { label: "44" }], correct: 2, note: "6 × 7 = 42 and 6 × 8 = 48" },
      { prompt: "Is 91 a prime number?", choices: [{ label: "yes" }, { label: "no" }], correct: 1, note: "91 = 7 × 13" },
    ],
  },

  // M4-F Fraction Friends (equivalent fractions, adding and taking away like fractions)
  {
    level: "owls",
    topic: "Fraction friends",
    seconds: 4,
    questions: [
      { prompt: "Same amount", big: "1/3 = ?/6", answer: "2" },
      { prompt: "Same bottom number", big: "2/8 + 3/8 = ?", answer: "5/8" },
      { prompt: "Same amount", big: "3/4 = ?/12", answer: "9", note: "4 × 3 = 12, so 3 × 3 = 9" },
      { prompt: "The other way!", big: "6/8 = 3/?", answer: "4", note: "share top and bottom by 2" },
      { prompt: "Take away the tops", big: "7/10 − 4/10 = ?", answer: "3/10" },
    ],
  },

  // M4-B Multiply by One Digit · M4-C Two-by-Two
  {
    level: "owls",
    topic: "Multiplying",
    seconds: 4,
    questions: [
      { prompt: "In your head!", big: "40 × 6 = ?", answer: "240" },
      { prompt: "In your head!", big: "31 × 3 = ?", answer: "93", note: "30 × 3 + 1 × 3" },
      { prompt: "Quick!", big: "25 × 4 = ?", answer: "100" },
      { prompt: "Tens times tens", big: "20 × 30 = ?", answer: "600", note: "2 × 3 = 6, then two zeros" },
      { prompt: "Two-by-two!", big: "12 × 11 = ?", answer: "132", note: "12 × 10 + 12" },
    ],
  },

  // R4-B Word Detective (meaning from context: definition, example, restatement, opposite clues)
  {
    level: "owls",
    topic: "Word detective",
    seconds: 5,
    questions: [
      { prompt: "Famished, he ate it all. Famished?", choices: [{ label: "very hungry" }, { label: "very tired" }, { label: "very full" }], correct: 0, note: "clue: he ate it all" },
      { prompt: "Not dry but damp. Damp means…", choices: [{ label: "very dry" }, { label: "a bit wet" }, { label: "bright red" }], correct: 1, note: "clue: not dry (an opposite)" },
      { prompt: "A gigantic, or huge, ship. Gigantic?", choices: [{ label: "very fast" }, { label: "very old" }, { label: "very big" }], correct: 2, note: "clue: or huge" },
      { prompt: "Timid, not bold. Timid means…", choices: [{ label: "shy and afraid" }, { label: "loud and silly" }, { label: "very strong" }], correct: 0, note: "clue: not bold (an opposite)" },
      { prompt: "Citrus fruits, like lemons. Citrus?", choices: [{ label: "apples and pears" }, { label: "oranges and limes" }, { label: "nuts and seeds" }], correct: 1, note: "clue: like lemons (an example)" },
    ],
  },

  // ---------------------------------------------------------------- Otters (age 8, grade 5 work)

  // R5-D Like a Picture (similes, metaphors, idioms, personification, hyperbole; content/figurative/R5.yaml)
  {
    level: "otters",
    topic: "Like a picture",
    seconds: 5,
    questions: [
      { prompt: "\"It's a piece of cake\" means…", choices: [{ label: "it's very easy" }, { label: "it's a dessert" }, { label: "it's very hard" }], correct: 0, note: "an idiom" },
      { prompt: "\"Spill the beans\" means…", choices: [{ label: "make a mess" }, { label: "tell a secret" }, { label: "cook dinner" }], correct: 1, note: "an idiom" },
      { prompt: "\"As quiet as a mouse\" is a…", choices: [{ label: "simile" }, { label: "metaphor" }, { label: "idiom" }], correct: 0, note: "it compares with as" },
      { prompt: "\"I could eat a horse!\" means…", choices: [{ label: "I like horses" }, { label: "I'm very hungry" }, { label: "I ate a lot" }], correct: 1, note: "hyperbole: a huge exaggeration" },
      { prompt: "\"The wind grabbed my hat\" is…", choices: [{ label: "a simile" }, { label: "hyperbole" }, { label: "personification" }], correct: 2, note: "the wind acts like a person" },
    ],
  },

  // M5-B Unlike Fractions (parts 1–5: one bottom a multiple, then others; answers simplest, over 1 mixed)
  {
    level: "otters",
    topic: "Unlike fractions",
    seconds: 4,
    questions: [
      { prompt: "Make the bottoms match", big: "1/2 + 1/4 = ?", answer: "3/4", note: "2/4 + 1/4" },
      { prompt: "Simplest form!", big: "2/3 − 1/6 = ?", answer: "1/2", note: "4/6 − 1/6 = 3/6" },
      { prompt: "Find a common bottom", big: "1/3 + 1/4 = ?", answer: "7/12", note: "4/12 + 3/12" },
      { prompt: "Find a common bottom", big: "3/4 − 2/3 = ?", answer: "1/12", note: "9/12 − 8/12" },
      { prompt: "More than one whole!", big: "1/2 + 3/5 = ?", answer: "1 1/10", note: "5/10 + 6/10 = 11/10" },
    ],
  },

  // M5-D Decimals in Columns (place value, rounding, adding and taking away)
  {
    level: "otters",
    topic: "Decimals",
    seconds: 4,
    questions: [
      { prompt: "Which is bigger?", choices: [{ label: "3.09" }, { label: "3.9" }], correct: 1, note: "3.90 > 3.09" },
      { prompt: "Round to the tenth", big: "4.67 ≈ ?", answer: "4.7", note: "7 hundredths rounds up" },
      { prompt: "What is the 8 worth?", big: "3.182", answer: "0.08", note: "8 hundredths" },
      { prompt: "Line up the points", big: "2.5 + 1.75 = ?", answer: "4.25" },
      { prompt: "Think 10.00", big: "10 − 2.75 = ?", answer: "7.25" },
    ],
  },

  // M5-F Parentheses and Volume (order of operations)
  {
    level: "otters",
    topic: "Parentheses",
    seconds: 4,
    questions: [
      { prompt: "Times comes first!", big: "3 + 4 × 2 = ?", answer: "11" },
      { prompt: "Parentheses first!", big: "(3 + 4) × 2 = ?", answer: "14" },
      { prompt: "Share comes first!", big: "20 − 6 ÷ 2 = ?", answer: "17" },
      { prompt: "Parentheses first!", big: "(8 + 4) ÷ 3 = ?", answer: "4" },
      { prompt: "Careful!", big: "5 + 3 × 4 − 2", answer: "15", note: "5 + 12 − 2" },
    ],
  },

  // ---------------------------------------------------------------- Pandas (age 9, grade 6 work)

  // M6-C Percents (out of 100, percent of a number, finding the whole)
  {
    level: "pandas",
    topic: "Percents",
    seconds: 4,
    questions: [
      { prompt: "In your head!", big: "10% of 70 = ?", answer: "7" },
      { prompt: "Half of it!", big: "50% of 36 = ?", answer: "18" },
      { prompt: "In your head!", big: "20% of 45 = ?", answer: "9", note: "10% is 4.5, so 20% is 9" },
      { prompt: "Three quarters", big: "75% of 40 = ?", answer: "30", note: "25% is 10, so 75% is 30" },
      { prompt: "Find the whole!", big: "25% of ? = 9", answer: "36", note: "9 × 4 = 36" },
    ],
  },

  // M6-B Ratios and Rates (ratio tables, simplest ratio, unit rates, speed, converting units)
  {
    level: "pandas",
    topic: "Ratios & rates",
    seconds: 4,
    questions: [
      { prompt: "Same ratio", big: "3 : 5 = 6 : ?", answer: "10" },
      { prompt: "Simplest ratio", big: "16 : 20 = 4 : ?", answer: "5", note: "share both by 4" },
      { prompt: "12 laps in 4 minutes", big: "? laps a minute", answer: "3" },
      { prompt: "150 miles in 3 hours", big: "? miles an hour", answer: "50" },
      { prompt: "3 feet in every yard", big: "7 yards = ? ft", answer: "21" },
    ],
  },

  // M6-D Below Zero (negatives, compare, absolute value, coordinate plane; no operations with negatives)
  {
    level: "pandas",
    topic: "Below zero",
    seconds: 4,
    questions: [
      { prompt: "5 degrees below zero is…", choices: [{ label: "5" }, { label: "−5" }], correct: 1 },
      { prompt: "Which is bigger?", choices: [{ label: "|−3|" }, { label: "|2|" }], correct: 0, note: "−3 is farther from 0" },
      { prompt: "Which is bigger?", choices: [{ label: "−4.5" }, { label: "−4" }], correct: 1, note: "closer to zero is bigger" },
      { prompt: "Plot (−3, 2). From 0, go…", choices: [{ label: "left 3, up 2" }, { label: "right 3, up 2" }, { label: "left 3, down 2" }], correct: 0, note: "x first, then y" },
      { prompt: "From (1, 5) to (1, −3). How far?", big: "? units", answer: "8", note: "5 up + 3 down" },
    ],
  },

  // R6-C Why Was It Written? (author's purpose, opinion vs. evidence)
  {
    level: "pandas",
    topic: "Author's purpose",
    seconds: 5,
    questions: [
      { prompt: "A pancake recipe is written to…", choices: [{ label: "persuade" }, { label: "inform" }, { label: "entertain" }], correct: 1, note: "it tells you how" },
      { prompt: "A joke book is written to…", choices: [{ label: "entertain" }, { label: "inform" }, { label: "persuade" }], correct: 0 },
      { prompt: "\"You must visit this park!\" aims to…", choices: [{ label: "inform" }, { label: "entertain" }, { label: "persuade" }], correct: 2, note: "\"must\" pushes you to act" },
      { prompt: "Which one is an opinion?", choices: [{ label: "Bees make honey." }, { label: "Bees are the best!" }, { label: "Bees have 6 legs." }], correct: 1, note: "you can't check \"the best\"" },
      { prompt: "Which one is evidence?", choices: [{ label: "Recess must last!" }, { label: "Recess is great." }, { label: "8 in 10 kids agree" }], correct: 2, note: "a number from a survey backs it up" },
    ],
  },
];

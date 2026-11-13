import type { TopicSpec } from "../challenges";

// Topic reels for Puppies, Cubs and Foxes: 4 topics a level, 5 questions each.
export const TOPICS_MIDDLE: TopicSpec[] = [
  // ---------------------------------------------------------------- Puppies (age 5)
  // Puppies Reading, "Word Patterns": letter pairs, magic e, ai, oa, bossy r
  {
    level: "puppies",
    topic: "Word Patterns",
    seconds: 4,
    questions: [
      { prompt: "Which letters are missing?", pic: "ship", big: "? i p", answer: "sh" },
      { prompt: "Which letter is missing?", pic: "cake", big: "c ? k e", answer: "a", note: "magic e makes a say its name" },
      { prompt: "Which letters are missing?", pic: "rain", big: "r ? n", answer: "ai" },
      { prompt: "Which letters are missing?", pic: "boat", big: "b ? t", answer: "oa" },
      { prompt: "Which letters are missing?", pic: "star", big: "s t ?", answer: "ar", note: "bossy r: a + r says ar" },
    ],
  },
  // Puppies Reading, "Word Endings": plurals, ing, ed, take the ending off
  {
    level: "puppies",
    topic: "Word Endings",
    seconds: 4,
    questions: [
      { prompt: "Add the ending", big: "jump + ing = ?", answer: "jumping" },
      { prompt: "One fox, two…", pic: "fox", choices: [{ label: "foxs" }, { label: "foxes" }], correct: 1, note: "after x, add es" },
      { prompt: "Add the ending", big: "smile + ed = ?", answer: "smiled", note: "it ends in e, so just add d" },
      { prompt: "Add the ending", big: "sit + ing = ?", answer: "sitting", note: "short i: double the t" },
      { prompt: "Take the ending off", big: "hopped − ed = ?", answer: "hop", note: "take off ed and the extra p" },
    ],
  },
  // Puppies Math, "Adding Warm-Up" to "Adding 8, 9 and 10": sums within 20
  {
    level: "puppies",
    topic: "Adding to 20",
    seconds: 4,
    questions: [
      { prompt: "7 apples and 3 more", row: { pic: "apple", n: 7 }, big: "7 + 3 = ?", answer: "10" },
      { prompt: "Quick!", big: "5 + 9 = ?", answer: "14", note: "make a ten: 9 + 1 + 4" },
      { prompt: "Quick!", big: "6 + 7 = ?", answer: "13", note: "double 6 is 12, plus 1" },
      { prompt: "Quick!", big: "8 + 6 = ?", answer: "14", note: "make a ten: 8 + 2 + 4" },
      { prompt: "Quick!", big: "9 + 8 = ?", answer: "17", note: "make a ten: 9 + 1 + 7" },
    ],
  },
  // Puppies Math, "Taking Away 1, 2, 3" to "Taking Away 7 to 10": within 20, no negatives
  {
    level: "puppies",
    topic: "Taking Away",
    seconds: 4,
    questions: [
      { prompt: "9 cookies. Eat 3!", row: { pic: "cookie", n: 9 }, big: "9 − 3 = ?", answer: "6" },
      { prompt: "Quick!", big: "12 − 4 = ?", answer: "8", note: "12 − 2 − 2" },
      { prompt: "Quick!", big: "15 − 6 = ?", answer: "9", note: "15 − 5 − 1" },
      { prompt: "Quick!", big: "13 − 8 = ?", answer: "5", note: "count up: 8 + 5 = 13" },
      { prompt: "Quick!", big: "20 − 9 = ?", answer: "11", note: "20 − 10 + 1" },
    ],
  },

  // ---------------------------------------------------------------- Cubs (age 5)
  // Cubs Reading, "Picture Puzzles": middle sound, one letter, two letters missing
  {
    level: "cubs",
    topic: "Picture Puzzles",
    seconds: 4,
    questions: [
      { prompt: "What's missing?", pic: "bus", big: "b ? s", answer: "u" },
      { prompt: "What's missing?", pic: "frog", big: "f r ? g", answer: "o" },
      { prompt: "What's missing?", pic: "drum", big: "d r u ?", answer: "m" },
      { prompt: "What's missing?", pic: "lamp", big: "l a ? p", answer: "m" },
      { prompt: "Two letters missing!", pic: "snail", big: "s n ? l", answer: "ai" },
    ],
  },
  // Cubs Reading, "Kinds of Words": naming, doing and describing words
  {
    level: "cubs",
    topic: "Kinds of Words",
    seconds: 5,
    questions: [
      { prompt: "Which is a naming word?", choices: [{ label: "eat" }, { label: "apple" }, { label: "sleepy" }], correct: 1 },
      { prompt: "Which is a describing word?", choices: [{ label: "soft" }, { label: "sing" }, { label: "spoon" }], correct: 0 },
      { prompt: "Which is a doing word?", choices: [{ label: "muddy" }, { label: "bread" }, { label: "climb" }], correct: 2 },
      { prompt: "The ___ puppy naps.", choices: [{ label: "sit" }, { label: "tiny" }], correct: 1, note: "tiny is a describing word" },
      { prompt: "The frog can ___.", choices: [{ label: "hop" }, { label: "nest" }], correct: 0, note: "hop is a doing word" },
    ],
  },
  // Cubs Math, "Tens and Ones" and "Hundreds, Tens and Ones"
  {
    level: "cubs",
    topic: "Tens and Ones",
    seconds: 4,
    questions: [
      { prompt: "What number is this?", big: "6 tens 4 ones", answer: "64" },
      { prompt: "Quick!", big: "40 + 7 = ?", answer: "47" },
      { prompt: "3 hundreds, 5 tens, 2 ones", big: "300 + 50 + 2", answer: "352" },
      { prompt: "What is the 7 worth?", big: "375", answer: "7 tens = 70" },
      { prompt: "Which is bigger?", choices: [{ label: "609" }, { label: "690" }], correct: 1, note: "same hundreds; 9 tens beat 0 tens" },
    ],
  },
  // Cubs Math, "Adding Ones", "Adding Two-Digit Numbers", "Taking Away Two-Digit Numbers"
  {
    level: "cubs",
    topic: "Add and Take Away",
    seconds: 4,
    questions: [
      { prompt: "Ones first!", big: "34 + 25 = ?", answer: "59" },
      { prompt: "Carry the ten!", big: "56 + 7 = ?", answer: "63", note: "6 + 7 = 13: carry the ten" },
      { prompt: "Carry the ten!", big: "47 + 36 = ?", answer: "83" },
      { prompt: "Break a ten!", big: "52 − 8 = ?", answer: "44" },
      { prompt: "Break a ten!", big: "71 − 35 = ?", answer: "36", note: "71 − 30 = 41, 41 − 5 = 36" },
    ],
  },

  // ---------------------------------------------------------------- Foxes (age 6)
  // Foxes Math, "Times Tables 2, 5, 10" to "Times Tables 6 to 9" (within 10 × 10)
  {
    level: "foxes",
    topic: "Times Tables",
    seconds: 4,
    questions: [
      { prompt: "Quick!", big: "3 × 4 = ?", answer: "12" },
      { prompt: "Quick!", big: "5 × 6 = ?", answer: "30" },
      { prompt: "Quick!", big: "4 × 7 = ?", answer: "28", note: "double 2 × 7: 14 + 14" },
      { prompt: "Quick!", big: "6 × 8 = ?", answer: "48" },
      { prompt: "Quick!", big: "9 × 7 = ?", answer: "63", note: "10 × 7 − 7 = 63" },
    ],
  },
  // Foxes Math, "Sharing Facts": division as a missing factor, always even
  {
    level: "foxes",
    topic: "Sharing",
    seconds: 4,
    questions: [
      { prompt: "8 cookies, 2 friends. Each gets?", row: { pic: "cookie", n: 8 }, big: "8 ÷ 2 = ?", answer: "4" },
      { prompt: "Quick!", big: "15 ÷ 3 = ?", answer: "5", note: "3 × 5 = 15" },
      { prompt: "Quick!", big: "32 ÷ 4 = ?", answer: "8", note: "4 × 8 = 32" },
      { prompt: "Quick!", big: "42 ÷ 6 = ?", answer: "7", note: "6 × 7 = 42" },
      { prompt: "Quick!", big: "54 ÷ 9 = ?", answer: "6", note: "9 × 6 = 54" },
    ],
  },
  // Foxes Math, "Fractions on a Line": 0 to 1 cut into 2, 3, 4, 6 or 8 parts
  {
    level: "foxes",
    topic: "Fractions",
    seconds: 4,
    questions: [
      { prompt: "1 of 4 equal parts is…", choices: [{ label: "1/2" }, { label: "1/4" }, { label: "1/8" }], correct: 1 },
      { prompt: "Which is bigger?", choices: [{ label: "1/8" }, { label: "1/2" }], correct: 1, note: "fewer pieces means bigger pieces" },
      { prompt: "Which is bigger?", choices: [{ label: "2/3" }, { label: "1/3" }], correct: 0, note: "same size parts, and 2 > 1" },
      { prompt: "0 to 1 in 8 parts. 3 jumps!", big: "? / 8", answer: "3", note: "3 jumps of 1/8 is 3/8" },
      { prompt: "0 to 1 in 6 parts. What is at 1?", big: "? / 6", answer: "6", note: "6 sixths make 1 whole" },
    ],
  },
  // Foxes Reading, "Word Builders": un-, re-, -ful, -less and compound words
  {
    level: "foxes",
    topic: "Word Builders",
    seconds: 5,
    questions: [
      { prompt: "Build the word", big: "un + safe = ?", answer: "unsafe", note: "un- means not" },
      { prompt: "What does refill mean?", choices: [{ label: "not full" }, { label: "fill again" }, { label: "without fill" }], correct: 1 },
      { prompt: "Build the word", big: "help + ful = ?", answer: "helpful", note: "-ful means full of" },
      { prompt: "What does fearless mean?", choices: [{ label: "full of fear" }, { label: "fear again" }, { label: "without fear" }], correct: 2 },
      { prompt: "Two words in one", pic: "fish", big: "star + fish = ?", answer: "starfish" },
    ],
  },
];

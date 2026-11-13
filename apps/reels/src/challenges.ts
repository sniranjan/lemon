// Challenge reels, as data. Every answer must be right and every skill must match the level it names.
import type { ChallengeSpec } from "./Challenge";

export const CHALLENGES: ChallengeSpec[] = [
  {
    id: "HowFar",
    bg: "#ffc83d",
    hook: ["Age 4 to 11:", "how far can", "your kid get?"],
    hookSub: "ask them one by one · 3 seconds each 👀",
    seconds: 3,
    questions: [
      { tag: "Age 4", prompt: "Which one rhymes with cat?", choices: [{ pic: "dog", label: "dog" }, { pic: "hat", label: "hat" }, { pic: "sun", label: "sun" }], correct: 1, level: "kittens" },
      { tag: "Age 5", prompt: "Quick!", big: "8 + 7 = ?", answer: "15", note: "make a ten: 8 + 2 + 5", level: "puppies" },
      { tag: "Age 6", prompt: "Times tables", big: "6 × 7 = ?", answer: "42", level: "foxes" },
      { tag: "Age 7", prompt: "What does fragile mean?", choices: [{ label: "very heavy" }, { label: "easy to break" }, { label: "bright yellow" }], correct: 1, level: "owls" },
      { tag: "Age 8", prompt: "Which is bigger?", choices: [{ label: "0.5" }, { label: "0.45" }], correct: 0, note: "0.5 is 0.50: fifty hundredths", level: "otters" },
      { tag: "Age 9", prompt: "How many quarters in 3/4?", big: "3/4 ÷ 1/4 = ?", answer: "3", level: "pandas" },
      { tag: "Age 10", prompt: "Careful with the signs", big: "−3 × −4 = ?", answer: "12", note: "negative times negative is positive", level: "penguins" },
      { tag: "Age 11", prompt: "Solve it", big: "x² = 49, x = ?", answer: "±7", note: "7 × 7 = 49 and −7 × −7 = 49", level: "lions" },
    ],
    outro: ["Where did your", "kid get stuck?", "Comment the age 👇"],
  },
  {
    id: "WhichBigger",
    bg: "#cfe3ff",
    hook: ["Ask your kid:", "which is bigger?"],
    hookSub: "careful, they're tricky 👀",
    seconds: 4,
    questions: [
      { prompt: "Which is bigger?", choices: [{ label: "1/3" }, { label: "1/4" }], correct: 0, note: "fewer pieces means bigger pieces", level: "foxes" },
      { prompt: "Which is bigger?", choices: [{ label: "0.5" }, { label: "0.45" }], correct: 0, note: "0.5 = 0.50, and 50 > 45", level: "otters" },
      { prompt: "Which is bigger?", choices: [{ label: "3/4" }, { label: "2/3" }], correct: 0, note: "9/12 beats 8/12", level: "owls" },
      { prompt: "Which is bigger?", choices: [{ label: "−3" }, { label: "−7" }], correct: 0, note: "closer to zero is bigger", level: "pandas" },
      { prompt: "Which is bigger?", choices: [{ label: "2³" }, { label: "3²" }], correct: 1, note: "2³ = 8 and 3² = 9", level: "lions" },
    ],
    outro: ["How many did", "your kid get?", "Comment x/5 👇"],
  },
  {
    id: "WhatNext",
    bg: "#c9f0e3",
    hook: ["Ask your kid:", "what comes next?"],
    hookSub: "each one is harder 🧠",
    seconds: 4,
    questions: [
      { prompt: "What comes next?", big: "2, 4, 6, 8, ?", answer: "10", note: "count by 2s", level: "cubs" },
      { prompt: "What comes next?", big: "5, 10, 15, 20, ?", answer: "25", note: "count by 5s", level: "cubs" },
      { prompt: "What comes next?", big: "1, 2, 4, 8, ?", answer: "16", note: "double it each time", level: "foxes" },
      { prompt: "What comes next?", big: "1, 4, 9, 16, ?", answer: "25", note: "1×1, 2×2, 3×3, 4×4, 5×5", level: "owls" },
      { prompt: "What comes next?", big: "1, 1, 2, 3, 5, ?", answer: "8", note: "add the two before it: 3 + 5", level: "owls" },
    ],
    outro: ["Which one", "stumped them?", "Comment 1 to 5 👇"],
  },
  {
    id: "OddOneOut",
    bg: "#ffd9c9",
    hook: ["Ask your", "3-year-old:", "which one doesn't belong?"],
    hookSub: "point and say it together 👆",
    seconds: 5,
    questions: [
      { prompt: "Which one doesn't belong?", choices: [{ pic: "cat" }, { pic: "dog" }, { pic: "car" }, { pic: "cow" }], correct: 2, note: "the car is not an animal", level: "chicks" },
      { prompt: "Which one doesn't belong?", choices: [{ pic: "apple" }, { pic: "shoe" }, { pic: "banana" }, { pic: "grapes" }], correct: 1, note: "we can't eat a shoe!", level: "chicks" },
      { prompt: "Which one doesn't belong?", choices: [{ pic: "bus" }, { pic: "train" }, { pic: "car" }, { pic: "pig" }], correct: 3, note: "a pig doesn't take us places", level: "chicks" },
      { prompt: "Which one doesn't belong?", choices: [{ pic: "hat" }, { pic: "sock" }, { pic: "fish" }, { pic: "coat" }], correct: 2, note: "we don't wear a fish", level: "chicks" },
    ],
    outro: ["Did they get", "all four?", "Tell us below 👇"],
  },
];

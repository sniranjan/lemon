// Holiday "table challenge" reels: questions a family can try at the dinner table, one reel per age band.
// Same quiz template (hook-first); each answer names the level that teaches that skill ("Our Foxes level · age 6").
// Answers are checked by hand; captions ask families to try it at the table and comment who won (shares > likes).
import type { ChallengeSpec, Question } from "./Challenge";

type H = { id: string; band: string; seconds: number; questions: Question[] };

const AUTUMN = "#f7dcbc";
const holidayReel = (h: H): ChallengeSpec => ({
  id: `Holiday-${h.id}`,
  bg: AUTUMN,
  hook: ["Thanksgiving table quiz", h.band],
  hookSub: "",
  seconds: h.seconds,
  questions: h.questions,
  outro: ["Try it at the table!", "Who won?", "Comment 👇"],
  levelPrefix: "Our ",
  closing: { line: "Happy Thanksgiving\nfrom paper lessons 🧡", sub: "every kid learns at their own pace\nprintable worksheets, ages 3–12\npaperlessons.com" },
  music: "easy-lemon",
});

export const HOLIDAY: H[] = [
  { id: "thanksgiving-little", band: "for ages 3–5 🍂", seconds: 5, questions: [
    { tag: "Counting", prompt: "Count the corn!", row: { pic: "corn", n: 4 }, big: "?", answer: "4", level: "chicks" },
    { tag: "Find it", prompt: "Where is the pumpkin?", choices: [{ pic: "apple" }, { pic: "pumpkin" }, { pic: "potato" }], correct: 1, level: "chicks" },
    { tag: "Find it", prompt: "Where is the leaf?", choices: [{ pic: "feather" }, { pic: "acorn" }, { pic: "leaf" }], correct: 2, level: "chicks" },
    { tag: "Adding 1", prompt: "3 rolls, then 1 more", row: { pic: "roll", n: 3 }, big: "3 + 1 = ?", answer: "4", level: "bunnies" },
    { bonus: true, prompt: "Which one rhymes with corn?", choices: [{ label: "horn" }, { label: "pie" }, { label: "leaf" }], correct: 0, level: "kittens" },
  ] },
  { id: "thanksgiving-kids", band: "for ages 6–8 🦃", seconds: 6, questions: [
    { tag: "Taking away", prompt: "8 slices of pie. 3 get eaten.", big: "8 − 3 = ?", answer: "5", level: "puppies" },
    { tag: "Times tables", prompt: "12 guests, 2 rolls each", big: "12 × 2 = ?", answer: "24", level: "foxes" },
    { tag: "Fractions", prompt: "Who ate more pie?", choices: [{ label: "you: 1/4" }, { label: "cousin: 2/4" }], correct: 1, level: "foxes" },
    { tag: "Time", prompt: "Turkey goes in at 11:00 and cooks 4 hours. Ready at…", choices: [{ label: "2:00" }, { label: "3:00" }, { label: "4:00" }], correct: 1, level: "foxes" },
    { bonus: true, prompt: "Grateful means…", choices: [{ label: "full of thanks" }, { label: "very big" }, { label: "grumpy" }], correct: 0, level: "owls" },
  ] },
  { id: "thanksgiving-big-kids", band: "ages 9–12 vs grown-ups 🥧", seconds: 7, questions: [
    { tag: "Fractions", prompt: "Double ¾ cup of sugar", big: "2 × 3/4 = ?", answer: "1 1/2", level: "otters" },
    { tag: "Percents", prompt: "A $20 pie is 25% off. New price?", choices: [{ label: "$15" }, { label: "$5" }, { label: "$18" }], correct: 0, level: "pandas" },
    { tag: "Ratios", prompt: "2 cups of flour for 3 eggs. With 9 eggs?", big: "? cups", answer: "6", level: "pandas" },
    { tag: "Negative numbers", prompt: "Freezer −4°F, kitchen 36°F. How much warmer?", big: "36 − (−4) = ?", answer: "40", level: "penguins" },
    { bonus: true, prompt: "2 apple, 3 pumpkin, 5 pecan pies. Pick one. Chance it's pumpkin?", choices: [{ label: "3/10" }, { label: "1/3" }, { label: "3/5" }], correct: 0, level: "penguins" },
  ] },
];

export const HOLIDAY_REELS = HOLIDAY.map(holidayReel);

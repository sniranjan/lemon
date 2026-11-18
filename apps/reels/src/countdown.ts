// "Christmas countdown" reels, Dec 1–24: one puzzle a day, ages rotating from 3 to 12 so every parent gets
// their kid's day. Same hook-first quiz template with one question; the answer names the level that teaches
// it, and the closing card says "see you tomorrow for day N + 1" (a daily series is a reason to follow).
// Answers are checked by hand.
import type { ChallengeSpec, Question } from "./Challenge";

type Day = Omit<Question, "level" | "tag"> & { age: string; skill: string; level: string };

const RED = "#f8d6d2";
const GREEN = "#d2ecd7";

export const DAYS: Day[] = [
  /* 1 */ { age: "3", skill: "Counting", level: "chicks", prompt: "Count the stars!", row: { pic: "star", n: 3 }, big: "?", answer: "3" },
  /* 2 */ { age: "6", skill: "Times tables", level: "foxes", prompt: "6 boxes, 4 cookies in each", big: "6 × 4 = ?", answer: "24" },
  /* 3 */ { age: "4", skill: "Find it", level: "chicks", prompt: "Where is the snowman?", choices: [{ pic: "tree" }, { pic: "snowman" }, { pic: "bell" }], correct: 1 },
  /* 4 */ { age: "8", skill: "Fractions", level: "otters", prompt: "¾ of a roll of gift wrap, then ⅛ more", big: "3/4 + 1/8 = ?", answer: "7/8" },
  /* 5 */ { age: "5", skill: "Adding", level: "kittens", prompt: "5 bells, then 4 more", big: "5 + 4 = ?", answer: "9" },
  /* 6 */ { age: "7", skill: "Long division", level: "owls", prompt: "96 candy canes in 4 stockings", big: "96 ÷ 4 = ?", answer: "24" },
  /* 7 */ { age: "3", skill: "Find it", level: "chicks", prompt: "Where is the mitten?", choices: [{ pic: "sock" }, { pic: "mitten" }, { pic: "hat" }], correct: 1 },
  /* 8 */ { age: "9", skill: "Percents", level: "pandas", prompt: "A $40 sled is 30% off. New price?", choices: [{ label: "$28" }, { label: "$10" }, { label: "$12" }], correct: 0 },
  /* 9 */ { age: "6", skill: "Fractions", level: "foxes", prompt: "Which slice of pie is bigger?", choices: [{ label: "1/3" }, { label: "1/8" }], correct: 0 },
  /* 10 */ { age: "10", skill: "Negative numbers", level: "penguins", prompt: "It's −6°F. It warms up 10 degrees.", big: "−6 + 10 = ?", answer: "4" },
  /* 11 */ { age: "4", skill: "Patterns", level: "ducklings", prompt: "Star, tree, star, tree… what's next?", choices: [{ pic: "tree" }, { pic: "star" }], correct: 1 },
  /* 12 */ { age: "11", skill: "Square roots", level: "lions", prompt: "Quick!", big: "√144 = ?", answer: "12" },
  /* 13 */ { age: "5", skill: "Skip counting", level: "cubs", prompt: "Count by 5s", big: "5, 10, 15, ?", answer: "20" },
  /* 14 */ { age: "7", skill: "Word meaning", level: "owls", prompt: "Which word means very cold?", choices: [{ label: "freezing" }, { label: "toasty" }, { label: "gentle" }], correct: 0 },
  /* 15 */ { age: "8", skill: "Decimals", level: "otters", prompt: "Wrapping 2.5 hours a day for 4 days", big: "2.5 × 4 = ?", answer: "10" },
  /* 16 */ { age: "3", skill: "Counting", level: "chicks", prompt: "Count the presents!", row: { pic: "present", n: 4 }, big: "?", answer: "4" },
  /* 17 */ { age: "6", skill: "Times tables", level: "foxes", prompt: "8 reindeer, 4 legs each", big: "8 × 4 = ?", answer: "32" },
  /* 18 */ { age: "9", skill: "Ratios", level: "pandas", prompt: "3 cups of cocoa for 2 kids. For 6 kids?", big: "? cups", answer: "9" },
  /* 19 */ { age: "4", skill: "More or less", level: "bunnies", prompt: "Which plate has more cookies?", choices: [{ label: "🍪🍪🍪" }, { label: "🍪🍪🍪🍪🍪" }], correct: 1 },
  /* 20 */ { age: "12", skill: "Quadratics", level: "whales", prompt: "x² = 49. So x is…", choices: [{ label: "7 only" }, { label: "7 or −7" }, { label: "24.5" }], correct: 1 },
  /* 21 */ { age: "5", skill: "Rhymes", level: "kittens", prompt: "Which one rhymes with snow?", choices: [{ label: "go" }, { label: "sled" }, { label: "tree" }], correct: 0 },
  /* 22 */ { age: "7", skill: "Prime numbers", level: "owls", prompt: "Is 23 a prime number?", choices: [{ label: "yes" }, { label: "no" }], correct: 0 },
  /* 23 */ { age: "10", skill: "Percents", level: "penguins", prompt: "A $50 gift plus 8% tax", choices: [{ label: "$54" }, { label: "$58" }, { label: "$50.80" }], correct: 0 },
  /* 24 */ { age: "8+", skill: "Christmas Eve bonus", level: "owls", bonus: true, prompt: "All 12 days of the song: how many gifts in all?", choices: [{ label: "78" }, { label: "144" }, { label: "364" }], correct: 2 },
];

export const countdownReel = (d: Day, i: number): ChallengeSpec => {
  const n = i + 1;
  const { age, skill, level, ...q } = d;
  const small = !age.includes("+") && Number(age) <= 5;
  return {
    id: `Countdown-day-${String(n).padStart(2, "0")}`,
    bg: n % 2 ? RED : GREEN,
    hook: ["Christmas countdown", `Day ${n} of 24 🎄`],
    hookSub: "",
    seconds: small ? 5 : 7,
    questions: [{ ...q, tag: `Age ${age} · ${skill}`, level }],
    outro: n < 24 ? ["Did you get it?", "Comment your", "answer 👇"] : ["Merry Christmas!", "Comment your", "answer 👇"],
    levelPrefix: "Our ",
    closing: n < 24
      ? { line: "Every kid learns\nat their own pace", sub: `see you tomorrow for day ${n + 1} 🎁\npaperlessons.com` }
      : { line: "Merry Christmas\nfrom paper lessons 🎄", sub: "every kid learns at their own pace\npaperlessons.com" },
    music: "jingle-bells-calm",
  };
};

export const COUNTDOWN_REELS = DAYS.map(countdownReel);

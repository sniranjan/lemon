// One challenge reel per level: every question comes from that level's own sections, at that level's age.
// Answers are checked by hand; skills match the level's syllabus (syllabus/*, ladder in syllabus/ladder.yaml).
import type { ChallengeSpec, Question } from "./Challenge";
import { BY_SLUG } from "./brand";

// A light tint of the level color, so ink text reads on every background.
const tint = (hex: string, k = 0.62) => {
  const n = parseInt(hex.slice(1), 16);
  const mix = (c: number) => Math.round(c + (255 - c) * k);
  return `rgb(${mix(n >> 16)}, ${mix((n >> 8) & 255)}, ${mix(n & 255)})`;
};

type Q = Omit<Question, "level">;

const level = (slug: string, seconds: number, questions: Q[]): ChallengeSpec => {
  const lv = BY_SLUG[slug];
  return {
    id: `Level-${slug}`,
    bg: tint(lv.color),
    hook: ["Can your", `${lv.age}-year-old`, "do these?"],
    mascot: slug,
    hookSub: `${lv.name} level · ${lv.grade} work\n${seconds} seconds each 👀`,
    seconds,
    questions: questions.map((q) => ({ ...q, level: slug })),
    outro: ["How many did", "they get?", `Comment x/${questions.length} 👇`],
  };
};

export const CHALLENGES: ChallengeSpec[] = [
  level("chicks", 5, [
    { tag: "Find it", prompt: "Where is the pig?", choices: [{ pic: "cat" }, { pic: "train" }, { pic: "pig" }, { pic: "apple" }], correct: 2 },
    { tag: "Count", prompt: "How many ducks?", row: { pic: "duck", n: 3 }, big: "?", answer: "3" },
    { tag: "Find it", prompt: "Which one is a train?", choices: [{ pic: "car" }, { pic: "ship" }, { pic: "bus" }, { pic: "train" }], correct: 3 },
    { tag: "Count", prompt: "How many apples?", row: { pic: "apple", n: 5 }, big: "?", answer: "5" },
    { tag: "Find it", prompt: "Which one doesn't belong?", choices: [{ pic: "cat" }, { pic: "dog" }, { pic: "car" }, { pic: "cow" }], correct: 2, note: "the car is not an animal" },
  ]),
  level("ducklings", 5, [
    { tag: "Numbers", prompt: "What comes next?", big: "26, 27, 28, ?", answer: "29" },
    { tag: "Words", prompt: "Which one can fly?", choices: [{ pic: "dog" }, { pic: "pig" }, { pic: "bee" }, { pic: "cow" }], correct: 2, note: "The bee can fly." },
    { tag: "Numbers", prompt: "Can they read it?", big: "47", answer: "forty-seven" },
    { tag: "Numbers", prompt: "What's missing?", big: "5, 6, ?, 8", answer: "7" },
    { tag: "Numbers", prompt: "Count on!", big: "18, 19, ?", answer: "20" },
  ]),
  level("bunnies", 4, [
    { tag: "Sounds", prompt: "What sound does it start with?", pic: "sun", choices: [{ label: "b" }, { label: "s" }, { label: "m" }], correct: 1 },
    { tag: "Sounds", prompt: "Put the sounds together", big: "c + at = ?", answer: "cat" },
    { tag: "Letters", prompt: "Which one is a small b?", choices: [{ label: "d" }, { label: "b" }, { label: "p" }], correct: 1 },
    { tag: "Numbers", prompt: "What's missing?", big: "38, 39, ?, 41", answer: "40" },
    { tag: "Sounds", prompt: "What sound does it start with?", pic: "fish", choices: [{ label: "f" }, { label: "p" }, { label: "t" }], correct: 0 },
  ]),
  level("kittens", 4, [
    { tag: "Rhymes", prompt: "Which one rhymes with hat?", choices: [{ pic: "dog", label: "dog" }, { pic: "cat", label: "cat" }, { pic: "sun", label: "sun" }], correct: 1 },
    { tag: "Letter teams", prompt: "Which team starts ship?", pic: "ship", choices: [{ label: "sh" }, { label: "ch" }, { label: "th" }], correct: 0 },
    { tag: "Adding", prompt: "Quick!", big: "13 + 2 = ?", answer: "15" },
    { tag: "Adding", prompt: "Careful!", big: "99 + 1 = ?", answer: "100" },
    { tag: "Numbers", prompt: "What comes next?", big: "118, 119, ?", answer: "120" },
  ]),
  level("puppies", 4, [
    { tag: "Endings", prompt: "Add the ending", big: "run + ing = ?", answer: "running", note: "run doubles its n" },
    { tag: "Syllables", prompt: "How many claps in butterfly?", choices: [{ label: "2" }, { label: "3" }], correct: 1, note: "but · ter · fly" },
    { tag: "Adding", prompt: "Quick!", big: "8 + 7 = ?", answer: "15", note: "make a ten: 8 + 2 + 5" },
    { tag: "Taking away", prompt: "Quick!", big: "15 − 9 = ?", answer: "6" },
    { tag: "Missing numbers", prompt: "What's missing?", big: "? + 6 = 13", answer: "7" },
  ]),
  level("cubs", 4, [
    { tag: "Kinds of words", prompt: "Which is a doing word?", choices: [{ label: "chair" }, { label: "jump" }, { label: "green" }], correct: 1 },
    { tag: "Word puzzle", prompt: "What's missing?", pic: "kite", big: "k ? t e", answer: "i" },
    { tag: "Tens and ones", prompt: "How many tens in 47?", big: "47 = ? tens 7 ones", answer: "4" },
    { tag: "Skip counting", prompt: "Count by 5s", big: "35, 40, 45, ?", answer: "50" },
    { tag: "Adding", prompt: "Carry the ten!", big: "46 + 38 = ?", answer: "84" },
  ]),
  level("foxes", 4, [
    { tag: "Word parts", prompt: "What does unkind mean?", choices: [{ label: "very kind" }, { label: "not kind" }, { label: "kind again" }], correct: 1 },
    { tag: "Times tables", prompt: "Quick!", big: "7 × 8 = ?", answer: "56" },
    { tag: "Sharing", prompt: "24 shared by 4", big: "24 ÷ 4 = ?", answer: "6" },
    { tag: "Fractions", prompt: "Which is bigger?", choices: [{ label: "1/3" }, { label: "1/4" }], correct: 0, note: "fewer pieces means bigger pieces" },
    { tag: "Big taking away", prompt: "Through the zero!", big: "402 − 168 = ?", answer: "234" },
  ]),
  level("owls", 4, [
    { tag: "Word clues", prompt: "The vase is fragile. Fragile means…", choices: [{ label: "very heavy" }, { label: "easy to break" }, { label: "bright yellow" }], correct: 1 },
    { tag: "Multiplying", prompt: "In your head!", big: "23 × 4 = ?", answer: "92", note: "20 × 4 + 3 × 4" },
    { tag: "Division", prompt: "Quick!", big: "96 ÷ 8 = ?", answer: "12" },
    { tag: "Factors", prompt: "Is 51 a prime number?", choices: [{ label: "yes" }, { label: "no" }], correct: 1, note: "51 = 3 × 17" },
    { tag: "Fraction friends", prompt: "Same amount", big: "1/2 = ?/8", answer: "4" },
  ]),
  level("otters", 4, [
    { tag: "Figurative language", prompt: "\"It's raining cats and dogs\" means…", choices: [{ label: "raining very hard" }, { label: "pets outside" }, { label: "a little rain" }], correct: 0 },
    { tag: "Fractions", prompt: "Unlike fractions", big: "1/2 + 1/3 = ?", answer: "5/6", note: "3/6 + 2/6" },
    { tag: "Decimals", prompt: "Which is bigger?", choices: [{ label: "0.5" }, { label: "0.45" }], correct: 0, note: "0.5 = 0.50, and 50 > 45" },
    { tag: "Decimals", prompt: "Line up the points", big: "3.5 + 1.25 = ?", answer: "4.75" },
    { tag: "Volume", prompt: "A box 2 by 3 by 4. How many cubes?", big: "2 × 3 × 4 = ?", answer: "24" },
  ]),
  level("pandas", 4, [
    { tag: "Dividing fractions", prompt: "How many quarters in 3/4?", big: "3/4 ÷ 1/4 = ?", answer: "3" },
    { tag: "Percents", prompt: "In your head!", big: "25% of 80 = ?", answer: "20" },
    { tag: "Below zero", prompt: "Which is bigger?", choices: [{ label: "−3" }, { label: "−7" }], correct: 0, note: "closer to zero is bigger" },
    { tag: "Equations", prompt: "Solve it", big: "x + 7 = 15", answer: "x = 8" },
    { tag: "Ratios", prompt: "2 cats for every 3 dogs", big: "4 cats : ? dogs", answer: "6" },
  ]),
  level("penguins", 4, [
    { tag: "Negatives", prompt: "Careful with the signs", big: "−3 × −4 = ?", answer: "12" },
    { tag: "Negatives", prompt: "Quick!", big: "−5 + 8 = ?", answer: "3" },
    { tag: "Percent change", prompt: "50 goes up to 60. That's…", choices: [{ label: "10%" }, { label: "20%" }], correct: 1, note: "10 more out of 50 = 20%" },
    { tag: "Two-step equations", prompt: "Solve it", big: "2x + 3 = 11", answer: "x = 4" },
    { tag: "Expressions", prompt: "Tidy it up", big: "3x + 2x = ?", answer: "5x" },
  ]),
  level("lions", 4, [
    { tag: "Exponents", prompt: "Which is bigger?", choices: [{ label: "2³" }, { label: "3²" }], correct: 1, note: "2³ = 8 and 3² = 9" },
    { tag: "Square roots", prompt: "Solve it", big: "x² = 49", answer: "x = 7 or −7" },
    { tag: "Exponents", prompt: "Trick question?", big: "5⁰ = ?", answer: "1" },
    { tag: "Right triangles", prompt: "Legs 3 and 4. The long side?", big: "3² + 4² = ?²", answer: "5" },
    { tag: "Lines", prompt: "What's the slope?", big: "y = 2x + 1", answer: "slope 2" },
  ]),
  level("whales", 4, [
    { tag: "Exponent rules", prompt: "Simplify", big: "x² · x³ = ?", answer: "x⁵" },
    { tag: "Polynomials", prompt: "Multiply it out", big: "(x + 3)(x − 3)", answer: "x² − 9" },
    { tag: "Factoring", prompt: "Factor it", big: "x² + 5x + 6", answer: "(x + 2)(x + 3)" },
    { tag: "Roots", prompt: "Simplify", big: "√64 = ?", answer: "8" },
    { tag: "Exponent rules", prompt: "Trick question?", big: "2⁻¹ = ?", answer: "1/2" },
  ]),
];

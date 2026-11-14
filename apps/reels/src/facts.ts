// "What should a 3rd grader know by June?" reels: five real Common Core expectations for one school grade,
// each with one thing to try (timer, then the answer). The answer chip names our level that teaches that
// grade's work ("Our Foxes level · age 6"), so the two-grades-ahead point shows without a sales line.
// Every item names the standard it comes from (`code`, listed in the caption: Gochi Hand draws G like 6, so not on screen).
// Answers are checked by hand.
import type { ChallengeSpec, Question } from "./Challenge";
import { BY_SLUG } from "./brand";
import { tint } from "./challenges";

type F = Omit<Question, "level" | "note"> & { code: string };
export type FactSpec = { grade: string; who: string; level: string; items: F[] };

export const factReel = (f: FactSpec): ChallengeSpec => {
  const lv = BY_SLUG[f.level];
  return {
    id: `Facts-grade-${f.grade}`,
    bg: tint(lv.color),
    hook: ["What should", `a ${f.who}`, "know by June?"],
    topic: "Common Core",
    hookSub: "used in most US states\ntry each one with your kid 👀",
    seconds: 5,
    questions: f.items.map(({ code: _code, ...q }) => ({ ...q, level: f.level })),
    outro: ["How many did", "yours get?", `Comment x/${f.items.length} 👇`],
    levelPrefix: "Our ",
    closing: { line: "Every kid learns\nat their own pace", sub: "printable worksheets, ages 3–12\nstart at their level\npaperlessons.com" },
  };
};

export const FACTS: FactSpec[] = [
  { grade: "k", who: "kindergartner", level: "ducklings", items: [
    { tag: "Count to 100", prompt: "Count by tens", big: "10, 20, 30, ?", answer: "40", code: "K.CC.1" },
    { tag: "Make 10", prompt: "What makes 10?", big: "6 + ? = 10", answer: "4", code: "K.OA.4" },
    { tag: "Adding within 5", prompt: "Quick!", big: "4 + 1 = ?", answer: "5", code: "K.OA.5" },
    { tag: "Compare numbers", prompt: "Which is more?", choices: [{ label: "4" }, { label: "8" }], correct: 1, code: "K.CC.7" },
    { tag: "Rhymes", prompt: "Which one rhymes with cat?", choices: [{ label: "dog" }, { label: "hat" }, { label: "sun" }], correct: 1, code: "RF.K.2a" },
  ] },
  { grade: "1", who: "1st grader", level: "kittens", items: [
    { tag: "Adding within 20", prompt: "Quick!", big: "7 + 5 = ?", answer: "12", code: "1.OA.6" },
    { tag: "Facts within 10", prompt: "By heart!", big: "10 − 3 = ?", answer: "7", code: "1.OA.6" },
    { tag: "Count to 120", prompt: "Keep going", big: "118, 119, ?", answer: "120", code: "1.NBT.1" },
    { tag: "Tens and ones", prompt: "How many tens?", big: "34 = ? tens 4 ones", answer: "3", code: "1.NBT.2" },
    { tag: "Letter teams", prompt: "Which letter team starts ship?", choices: [{ label: "sh" }, { label: "ch" }, { label: "th" }], correct: 0, code: "RF.1.3a" },
  ] },
  { grade: "2", who: "2nd grader", level: "cubs", items: [
    { tag: "Sums by heart", prompt: "Every one-digit sum", big: "9 + 6 = ?", answer: "15", code: "2.OA.2" },
    { tag: "Skip counting", prompt: "Count by 100s", big: "300, 400, 500, ?", answer: "600", code: "2.NBT.2" },
    { tag: "Adding within 100", prompt: "Carry the ten!", big: "57 + 26 = ?", answer: "83", code: "2.NBT.5" },
    { tag: "Money", prompt: "2 quarters and 1 dime is…", choices: [{ label: "35¢" }, { label: "60¢" }, { label: "52¢" }], correct: 1, code: "2.MD.8" },
    { tag: "Telling time", prompt: "Five minutes after 3:00 is…", choices: [{ label: "3:05" }, { label: "3:50" }, { label: "5:03" }], correct: 0, code: "2.MD.7" },
  ] },
  { grade: "3", who: "3rd grader", level: "foxes", items: [
    { tag: "Times tables by heart", prompt: "Quick!", big: "6 × 9 = ?", answer: "54", code: "3.OA.7" },
    { tag: "Division facts", prompt: "Quick!", big: "63 ÷ 7 = ?", answer: "9", code: "3.OA.7" },
    { tag: "Fractions", prompt: "Which is bigger?", choices: [{ label: "1/3" }, { label: "1/6" }], correct: 0, code: "3.NF.3d" },
    { tag: "Taking away to 1000", prompt: "Through the zero!", big: "503 − 247 = ?", answer: "256", code: "3.NBT.2" },
    { tag: "Word parts", prompt: "What does unkind mean?", choices: [{ label: "very kind" }, { label: "not kind" }, { label: "kind again" }], correct: 1, code: "L.3.4b" },
  ] },
  { grade: "4", who: "4th grader", level: "owls", items: [
    { tag: "Two-by-two", prompt: "Multiply", big: "21 × 13 = ?", answer: "273", code: "4.NBT.5" },
    { tag: "Long division", prompt: "Divide", big: "252 ÷ 4 = ?", answer: "63", code: "4.NBT.6" },
    { tag: "Equal fractions", prompt: "Same amount", big: "3/4 = ?/12", answer: "9", code: "4.NF.1" },
    { tag: "Primes", prompt: "Is 57 a prime number?", choices: [{ label: "yes" }, { label: "no" }], correct: 1, code: "4.OA.4" },
    { tag: "Decimals", prompt: "As a fraction", big: "0.3 = ?/10", answer: "3", code: "4.NF.6" },
  ] },
  { grade: "5", who: "5th grader", level: "otters", items: [
    { tag: "Unlike fractions", prompt: "Add", big: "1/2 + 1/4 = ?", answer: "3/4", code: "5.NF.1" },
    { tag: "Fraction × fraction", prompt: "Multiply", big: "2/3 × 3/4 = ?", answer: "1/2", code: "5.NF.4" },
    { tag: "Decimals", prompt: "Line up the points", big: "2.5 + 1.75 = ?", answer: "4.25", code: "5.NBT.7" },
    { tag: "Volume", prompt: "A box 3 by 2 by 5. How many cubes?", big: "3 × 2 × 5 = ?", answer: "30", code: "5.MD.5" },
    { tag: "Parentheses", prompt: "Inside first", big: "3 × (2 + 5) = ?", answer: "21", code: "5.OA.1" },
  ] },
  { grade: "6", who: "6th grader", level: "pandas", items: [
    { tag: "Dividing fractions", prompt: "How many sixths in a half?", big: "1/2 ÷ 1/6 = ?", answer: "3", code: "6.NS.1" },
    { tag: "Percents", prompt: "In your head!", big: "30% of 50 = ?", answer: "15", code: "6.RP.3c" },
    { tag: "Below zero", prompt: "Which is bigger?", choices: [{ label: "−2" }, { label: "−9" }], correct: 0, code: "6.NS.7" },
    { tag: "Equations", prompt: "Solve it", big: "x + 9 = 20", answer: "x = 11", code: "6.EE.7" },
    { tag: "Ratios", prompt: "Same ratio", big: "3 : 5 = 9 : ?", answer: "15", code: "6.RP.3" },
  ] },
  { grade: "7", who: "7th grader", level: "penguins", items: [
    { tag: "Negatives", prompt: "Careful with the signs", big: "−6 × 3 = ?", answer: "−18", code: "7.NS.2" },
    { tag: "Negatives", prompt: "Quick!", big: "−4 + 10 = ?", answer: "6", code: "7.NS.1" },
    { tag: "Percent change", prompt: "40 goes up to 50. That's…", choices: [{ label: "10%" }, { label: "25%" }], correct: 1, code: "7.RP.3" },
    { tag: "Two-step equations", prompt: "Solve it", big: "3x − 5 = 16", answer: "x = 7", code: "7.EE.4a" },
    { tag: "Expressions", prompt: "Tidy it up", big: "4x + x = ?", answer: "5x", code: "7.EE.1" },
  ] },
  { grade: "8", who: "8th grader", level: "lions", items: [
    { tag: "Exponents", prompt: "Trick question?", big: "7⁰ = ?", answer: "1", code: "8.EE.1" },
    { tag: "Square roots", prompt: "Solve it", big: "x² = 64", answer: "x = 8 or −8", code: "8.EE.2" },
    { tag: "Right triangles", prompt: "Legs 6 and 8. The long side?", big: "6² + 8² = ?²", answer: "10", code: "8.G.7" },
    { tag: "Lines", prompt: "What's the slope?", big: "y = 3x − 2", answer: "slope 3", code: "8.F.3" },
    { tag: "Roots", prompt: "Quick!", big: "√121 = ?", answer: "11", code: "8.EE.2" },
  ] },
];

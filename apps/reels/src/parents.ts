// "Your 4th grader's homework. Can YOU still do it?" reels, aimed at parents (grades 3–6, kids aged 8–11).
// Middle-school reels reached teens taking the quiz themselves; this series is meant for parents: everyday homework
// they help with, too easy to hold a teen. Same quiz template as facts.ts (5 Common Core items); the answer chip
// names our level that teaches it, often years younger. Answers are checked by hand.
import type { ChallengeSpec } from "./Challenge";
import { BY_SLUG } from "./brand";
import { tint } from "./challenges";
import type { FactSpec } from "./facts";

export const parentReel = (f: FactSpec): ChallengeSpec => {
  const lv = BY_SLUG[f.level];
  return {
    id: `Parents-grade-${f.grade}`,
    bg: tint(lv.color),
    hook: [`Your ${f.who}'s ${f.grade.endsWith("g") ? "grammar" : "homework"}`, "Can YOU still do it?"],
    topic: "Grown-ups",
    hookSub: "",
    seconds: 5,
    questions: f.items.map(({ code: _code, ...q }) => ({ ...q, level: f.level })),
    outro: ["Be honest:", "how many did", "YOU get? 👇"],
    levelPrefix: "Our ",
    closing: { line: "Homework without\nthe battle", sub: "every kid, their own pace\nprintable worksheets, ages 3–12\npaperlessons.com" },
  };
};

export const PARENTS: FactSpec[] = [
  { grade: "3", who: "3rd grader", level: "foxes", items: [
    { tag: "Times tables", prompt: "The one everyone forgets", big: "7 × 8 = ?", answer: "56", code: "3.OA.7" },
    { tag: "Fractions", prompt: "Which piece is bigger?", choices: [{ label: "1/2" }, { label: "1/3" }], correct: 0, code: "3.NF.3d" },
    { tag: "Area", prompt: "A rug 4 feet by 6 feet", big: "area = ?", answer: "24 sq ft", code: "3.MD.7" },
    { tag: "Sharing", prompt: "Quick!", big: "72 ÷ 8 = ?", answer: "9", code: "3.OA.7" },
    { tag: "Rounding", prompt: "Round to the nearest 10", big: "347 → ?", answer: "350", code: "3.NBT.1" },
  ] },
  { grade: "4", who: "4th grader", level: "owls", items: [
    { tag: "Multiplying", prompt: "No calculator!", big: "24 × 13 = ?", answer: "312", code: "4.NBT.5" },
    { tag: "Long division", prompt: "Remember how?", big: "156 ÷ 4 = ?", answer: "39", code: "4.NBT.6" },
    { tag: "Equal fractions", prompt: "Fill the box", big: "3/4 = ?/8", answer: "6", code: "4.NF.1" },
    { tag: "Factors", prompt: "How many factors does 12 have?", choices: [{ label: "4" }, { label: "6" }, { label: "5" }], correct: 1, code: "4.OA.4" },
    { tag: "Decimals", prompt: "Which is bigger?", choices: [{ label: "2.5" }, { label: "2.45" }], correct: 0, code: "4.NF.7" },
  ] },
  { grade: "5", who: "5th grader", level: "otters", items: [
    { tag: "Fractions", prompt: "Unlike bottoms!", big: "2/3 + 1/4 = ?", answer: "11/12", code: "5.NF.1" },
    { tag: "Decimals", prompt: "Careful…", big: "0.4 × 0.5 = ?", answer: "0.2", code: "5.NBT.7" },
    { tag: "Order of operations", prompt: "The internet fights about these", big: "3 + 4 × 2 = ?", answer: "11", code: "5.OA.1" },
    { tag: "Volume", prompt: "A box 2 × 3 × 4 cm", big: "volume = ?", answer: "24 cm³", code: "5.MD.5" },
    { tag: "Dividing fractions", prompt: "Half a pizza shared by 4", big: "1/2 ÷ 4 = ?", answer: "1/8", code: "5.NF.7" },
  ] },
  { grade: "6", who: "6th grader", level: "pandas", items: [
    { tag: "Dividing fractions", prompt: "Keep, change, flip?", big: "3/4 ÷ 1/8 = ?", answer: "6", code: "6.NS.1" },
    { tag: "Percents", prompt: "A 15% tip on $80", big: "$?", answer: "$12", code: "6.RP.3c" },
    { tag: "Absolute value", prompt: "Quick!", big: "|−7| = ?", answer: "7", code: "6.NS.7c" },
    { tag: "Expressions", prompt: "Multiply it out", big: "2(x + 3) = ?", answer: "2x + 6", code: "6.EE.3" },
    { tag: "Equations", prompt: "Solve it", big: "x/4 = 9", answer: "x = 36", code: "6.EE.7" },
  ] },
  { grade: "2", who: "2nd grader", level: "cubs", items: [
    { tag: "Shapes", prompt: "How many sides does a hexagon have?", big: "? sides", answer: "6", code: "2.G.1" },
    { tag: "Money", prompt: "2 quarters, 2 dimes and 1 nickel", choices: [{ label: "75¢" }, { label: "65¢" }, { label: "80¢" }], correct: 0, code: "2.MD.8" },
    { tag: "Even or odd", prompt: "Is 47 even or odd?", choices: [{ label: "even" }, { label: "odd" }], correct: 1, code: "2.OA.3" },
    { tag: "Compare numbers", prompt: "Which is bigger?", choices: [{ label: "509" }, { label: "590" }], correct: 1, code: "2.NBT.4" },
    { tag: "Telling time", prompt: "Quarter past 7 is…", choices: [{ label: "7:15" }, { label: "7:25" }, { label: "7:45" }], correct: 0, code: "2.MD.7" },
  ] },
  { grade: "3b", who: "3rd grader", level: "foxes", items: [
    { tag: "Times tables", prompt: "Another one people forget", big: "6 × 9 = ?", answer: "54", code: "3.OA.7" },
    { tag: "Fractions", prompt: "Which is bigger?", choices: [{ label: "3/4" }, { label: "3/8" }], correct: 0, code: "3.NF.3d" },
    { tag: "Perimeter", prompt: "A garden 5 feet by 3 feet. Fence all the way around?", big: "? feet", answer: "16", code: "3.MD.8" },
    { tag: "Elapsed time", prompt: "Practice starts at 4:45 and lasts 30 minutes. It ends at…", choices: [{ label: "5:15" }, { label: "5:05" }, { label: "4:75" }], correct: 0, code: "3.MD.1" },
    { tag: "Rounding", prompt: "Round to the nearest hundred", big: "652 → ?", answer: "700", code: "3.NBT.1" },
  ] },
  { grade: "4g", who: "4th grader", level: "owls", items: [
    { tag: "Confused words", prompt: "___ going to the park.", choices: [{ label: "Their" }, { label: "There" }, { label: "They're" }], correct: 2, code: "L.4.1g" },
    { tag: "Confused words", prompt: "The dog wagged ___ tail.", choices: [{ label: "its" }, { label: "it's" }], correct: 0, code: "L.4.1g" },
    { tag: "Irregular plurals", prompt: "One mouse, two…", choices: [{ label: "mouses" }, { label: "mice" }, { label: "mices" }], correct: 1, code: "L.2.1b" },
    { tag: "Complete sentences", prompt: "Which one is a complete sentence?", choices: [{ label: "Ran to the store." }, { label: "Mia ran to the store." }, { label: "To the store with Mia." }], correct: 1, code: "L.4.1f" },
    { tag: "Irregular verbs", prompt: "Yesterday I ___ in the lake.", choices: [{ label: "swimmed" }, { label: "swam" }, { label: "swum" }], correct: 1, code: "L.2.1d" },
  ] },
];

export const PARENT_REELS = PARENTS.map(parentReel);

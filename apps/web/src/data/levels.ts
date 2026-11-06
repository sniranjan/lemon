// Public level ladder for the site. Names, titles, ages, subjects and "ready" come from the generator's
// syllabus/ladder.yaml (copied to ladder.json at build time by scripts/sync-ladder.mjs), so the site and
// the PDFs always agree. This file only adds how each level looks on the site.
import ladder from "./ladder.json";

export type Subject = "reading" | "math" | "pencil";

export type Preview =
  | { kind: "words"; words: { word: string; picture: string }[] }
  | { kind: "path"; from: string; to: string }
  | { kind: "count"; picture: string; n: number }
  | { kind: "phrase"; phrase: string; picture: string }
  | { kind: "trace"; letter: string; word: string; picture: string }
  | { kind: "write"; numbers: number[] }
  | { kind: "facts"; subject: Subject; lines: string[]; bridge?: string }
  | { kind: "read"; lines: string[]; picture?: string };

type Look = {
  mascot: string;
  color: "sun" | "coral" | "teal" | "sky" | "grape" | "leaf";
  blurb: string;
  preview: Preview;
};

export type Level = Look & {
  slug: string;
  name: string;
  title: string;
  age: number;           // the one age a child on pace does this level
  grade: string;          // US school grade the work matches, e.g. "3", "K–1", "Pre-K"
  subjects: Subject[];
  status: "ready" | "soon";
};

export const SUBJECT_LABEL: Record<Subject, string> = {
  reading: "Reading",
  math: "Math",
  pencil: "Pencil",
};

/** Which subject a mini-sheet shows (its header label). */
export function previewSubject(p: Preview): Subject {
  switch (p.kind) {
    case "words":
    case "phrase":
    case "trace":
    case "read":
      return "reading";
    case "path":
      return "pencil";
    case "facts":
      return p.subject;
    default:
      return "math";
  }
}

const LOOK: Record<string, Look> = {
  chicks: {
    mascot: "/brand/chick.svg",
    color: "sun",
    blurb: "Big picture words to say together, counting to 10, and first crayon lines.",
    preview: { kind: "words", words: [{ word: "apple", picture: "apple" }, { word: "duck", picture: "duck" }] },
  },
  ducklings: {
    mascot: "/pictures/duck.svg",
    color: "sky",
    blurb: "Short phrases to say out loud, numbers up to 50, and steadier pencil lines.",
    preview: { kind: "phrase", phrase: "a red ball", picture: "ball" },
  },
  bunnies: {
    mascot: "/pictures/bunny.svg",
    color: "coral",
    blurb: "Tracing every letter, first sounds in words, and writing numbers all by themselves.",
    preview: { kind: "trace", letter: "b", word: "ball", picture: "ball" },
  },
  kittens: {
    mascot: "/pictures/cat.svg",
    color: "grape",
    blurb: "Letter teams like sh and ch, rhymes, and adding 1, 2 and 3 by finding the next number.",
    preview: { kind: "facts", subject: "math", bridge: "3 →", lines: ["3 + 1 =", "7 + 1 =", "5 + 2 =", "6 + 3 ="] },
  },
  puppies: {
    mascot: "/pictures/dog.svg",
    color: "sun",
    blurb: "Spelling patterns and copying sentences, plus adding and subtracting all the way to 20.",
    preview: { kind: "facts", subject: "math", lines: ["8 + 7 =", "13 − 6 =", "9 + 9 =", "17 − 8 ="] },
  },
  cubs: {
    mascot: "/pictures/bear.svg",
    color: "teal",
    blurb: "Reading passages aloud with expression, plus two-digit adding and subtracting.",
    preview: { kind: "read", lines: ["I see a big bear.", "The bear can swim.", "I like the bear."], picture: "bear" },
  },
  foxes: {
    mascot: "/brand/fox.svg",
    color: "coral",
    blurb: "Fables and what makes characters tick, plus learning the times tables by heart.",
    preview: { kind: "facts", subject: "math", lines: ["3 × 4 =", "6 × 7 =", "8 × 9 =", "7 × 8 ="] },
  },
  owls: {
    mascot: "/pictures/owl.svg",
    color: "grape",
    blurb: "First chapter books, plus long multiplication and long division.",
    preview: { kind: "facts", subject: "math", lines: ["23 × 14 =", "156 ÷ 6 =", "48 × 25 =", "912 ÷ 8 ="] },
  },
  otters: {
    mascot: "/brand/otter.svg",
    color: "sky",
    blurb: "Finding the details in a paragraph, and working with fractions and decimals.",
    preview: { kind: "facts", subject: "math", lines: ["½ + ¼ =", "0.3 + 0.45 =", "¾ − ⅓ =", "2.5 × 4 ="] },
  },
  pandas: {
    mascot: "/brand/panda.svg",
    color: "leaf",
    blurb: "Central ideas and reading between the lines, plus ratios, percents and fraction math.",
    preview: { kind: "facts", subject: "math", lines: ["3 : 5 = 12 : ?", "⅔ × ¾ =", "1½ ÷ ⅜ =", "40% of 75 ="] },
  },
  penguins: {
    mascot: "/brand/penguin.svg",
    color: "teal",
    blurb: "Weighing claims and evidence, plus negative numbers, percent change and two-step equations.",
    preview: { kind: "facts", subject: "math", lines: ["−4 + 9 =", "−3 × −6 =", "3x + 5 = 20", "x = ?"] },
  },
  lions: {
    mascot: "/pictures/lion.svg",
    color: "sun",
    blurb: "Reading closely and explaining why, plus linear equations and exponents.",
    preview: { kind: "facts", subject: "math", lines: ["2x + 3 = 11", "x = ?", "3² + 4² =", "5(x − 2) = 15"] },
  },
  whales: {
    mascot: "/brand/whale.svg",
    color: "sky",
    blurb: "How authors make their choices, plus polynomials, factoring and first quadratics.",
    preview: { kind: "facts", subject: "math", lines: ["(x + 3)(x − 2) =", "x² + 5x + 6 = 0", "2³ · 2⁴ =", "x = ?"] },
  },
};

/** "Grade 3 work", "K–1 work", "Pre-K work". */
export function gradeLabel(grade: string): string {
  return /^\d/.test(grade) ? `Grade ${grade} work` : `${grade} work`;
}

export const LEVELS: Level[] = ladder.map((r) => {
  const look = LOOK[r.slug];
  if (!look) throw new Error(`no site look for level ${r.slug}; add it to src/data/levels.ts`);
  return {
    ...look,
    slug: r.slug,
    name: r.name,
    title: r.title,
    age: r.age,
    grade: r.grade,
    subjects: r.subjects as Subject[],
    status: r.ready ? "ready" : "soon",
  };
});

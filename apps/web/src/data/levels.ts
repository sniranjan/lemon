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
  ages: string;
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
    blurb: "Letter teams like sh and ch, rhyming words, and adding 1, 2 and 3 by finding the next number.",
    preview: { kind: "facts", subject: "math", bridge: "3 →", lines: ["3 + 1 =", "7 + 1 =", "5 + 2 =", "6 + 3 ="] },
  },
  puppies: {
    mascot: "/pictures/dog.svg",
    color: "sun",
    blurb: "Spelling patterns, longer words and sentence copying, and adding all the way to 10.",
    preview: { kind: "facts", subject: "math", lines: ["7 + 5 =", "9 + 4 =", "6 + 6 =", "8 + 7 ="] },
  },
  cubs: {
    mascot: "/pictures/bear.svg",
    color: "teal",
    blurb: "Reading short passages aloud with expression, and adding bigger numbers in their heads.",
    preview: { kind: "read", lines: ["I see a big bear.", "The bear can swim.", "I like the bear."], picture: "bear" },
  },
  foxes: {
    mascot: "/brand/fox.svg",
    color: "coral",
    blurb: "Building sentences and reading little stories, plus subtraction and two-digit adding.",
    preview: { kind: "facts", subject: "math", lines: ["12 − 5 =", "15 − 8 =", "34 + 27 =", "50 − 16 ="] },
  },
  owls: {
    mascot: "/pictures/owl.svg",
    color: "grape",
    blurb: "Short stories with questions to answer, and the times tables up to multiplying bigger numbers.",
    preview: { kind: "facts", subject: "math", lines: ["3 × 4 =", "6 × 7 =", "8 × 9 =", "23 × 3 ="] },
  },
  otters: {
    mascot: "/brand/otter.svg",
    color: "sky",
    blurb: "Reading paragraphs and finding the details, plus long division with remainders.",
    preview: { kind: "facts", subject: "math", lines: ["84 ÷ 4 =", "96 ÷ 8 =", "125 ÷ 5 =", "100 ÷ 7 ="] },
  },
  pandas: {
    mascot: "/brand/panda.svg",
    color: "leaf",
    blurb: "Finding the main idea of a passage, and adding, subtracting and comparing fractions.",
    preview: { kind: "facts", subject: "math", lines: ["½ + ¼ =", "¾ − ⅓ =", "⅖ + ⅖ =", "1 − ⅝ ="] },
  },
  penguins: {
    mascot: "/brand/penguin.svg",
    color: "teal",
    blurb: "Summarizing what they read in their own words, and working with decimals and percents.",
    preview: { kind: "facts", subject: "math", lines: ["0.6 × 5 =", "2.5 + 1.75 =", "4.2 ÷ 0.7 =", "10% of 80 ="] },
  },
  lions: {
    mascot: "/pictures/lion.svg",
    color: "sun",
    blurb: "Reading closely and explaining why, plus negative numbers and first algebra.",
    preview: { kind: "facts", subject: "math", lines: ["2x + 3 = 11", "x = ?", "−4 + 9 =", "3(x − 2) = 12"] },
  },
};

export const LEVELS: Level[] = ladder.map((r) => {
  const look = LOOK[r.slug];
  if (!look) throw new Error(`no site look for level ${r.slug}; add it to src/data/levels.ts`);
  return {
    ...look,
    slug: r.slug,
    name: r.name,
    title: r.title,
    ages: r.ages,
    subjects: r.subjects as Subject[],
    status: r.ready ? "ready" : "soon",
  };
});

// Public level ladder. Internal generator codes stay inside the generator and never appear on the site.
export type Subject = "reading" | "numbers" | "pencil";

export type Level = {
  slug: string;            // URL + R2 key: previews/<slug>.pdf
  name: string;
  mascot: string;          // picture path
  color: "sun" | "coral" | "teal" | "sky" | "grape" | "leaf";
  ages: string;
  subjects: Subject[];
  blurb: string;
  skills: string[];
  status: "ready" | "soon";
  preview: Preview;
};

export type Preview =
  | { kind: "words"; words: { word: string; picture: string }[] }
  | { kind: "path"; from: string; to: string }
  | { kind: "count"; picture: string; n: number }
  | { kind: "phrase"; phrase: string; picture: string }
  | { kind: "trace"; letter: string; word: string; picture: string }
  | { kind: "write"; numbers: number[] }
  | { kind: "add"; facts: [number, number][] }
  | { kind: "read"; lines: string[]; picture: string };

export const SUBJECT_LABEL: Record<Subject, string> = {
  reading: "Reading",
  numbers: "Numbers",
  pencil: "Pencil skills",
};

export const LEVELS: Level[] = [
  {
    slug: "tadpoles",
    name: "Tadpoles",
    mascot: "/brand/tadpole.svg",
    color: "leaf",
    ages: "3–4",
    subjects: ["pencil"],
    blurb: "First crayon and pencil play: coloring inside big shapes, then lines from a dot to a picture.",
    skills: ["Coloring", "Straight lines", "Curvy lines"],
    status: "ready",
    preview: { kind: "path", from: "bee", to: "flower" },
  },
  {
    slug: "chicks",
    name: "Chicks",
    mascot: "/brand/chick.svg",
    color: "sun",
    ages: "3–4",
    subjects: ["reading"],
    blurb: "Big pictures and everyday words to say together. Every word comes back again and again.",
    skills: ["Picture words", "Say it again", "Tiny stories"],
    status: "ready",
    preview: { kind: "words", words: [{ word: "apple", picture: "apple" }, { word: "duck", picture: "duck" }] },
  },
  {
    slug: "ducklings",
    name: "Ducklings",
    mascot: "/pictures/duck.svg",
    color: "sky",
    ages: "4–5",
    subjects: ["numbers", "reading"],
    blurb: "Counting up to 10 while pointing, reading numbers, and saying short phrases out loud.",
    skills: ["Counting to 10", "Reading numbers", "Little phrases"],
    status: "ready",
    preview: { kind: "count", picture: "star", n: 4 },
  },
  {
    slug: "froglets",
    name: "Froglets",
    mascot: "/pictures/frog.svg",
    color: "teal",
    ages: "4–5",
    subjects: ["pencil"],
    blurb: "Steadier pencil control: shapes, back-and-forth lines, corners and curves.",
    skills: ["Shapes", "Back and forth", "Corners and curves"],
    status: "soon",
    preview: { kind: "path", from: "bunny", to: "carrot" },
  },
  {
    slug: "bunnies",
    name: "Bunnies",
    mascot: "/pictures/bunny.svg",
    color: "coral",
    ages: "4–5",
    subjects: ["reading", "numbers"],
    blurb: "Tracing letters a to z, first sounds in words, and reading numbers up to 50.",
    skills: ["Letter tracing", "First sounds", "Numbers to 50"],
    status: "soon",
    preview: { kind: "trace", letter: "b", word: "ball", picture: "ball" },
  },
  {
    slug: "kittens",
    name: "Kittens",
    mascot: "/pictures/cat.svg",
    color: "grape",
    ages: "5–6",
    subjects: ["reading", "numbers"],
    blurb: "Writing numbers by themselves, letter teams like sh and ch, and rhyming words.",
    skills: ["Writing numbers", "Letter teams", "Rhymes"],
    status: "soon",
    preview: { kind: "write", numbers: [1, 2, 3, 4, 5] },
  },
  {
    slug: "puppies",
    name: "Puppies",
    mascot: "/pictures/dog.svg",
    color: "sun",
    ages: "5–6",
    subjects: ["reading", "numbers"],
    blurb: "Adding 1, 2 and 3 by finding the next number. Longer words and sentence copying.",
    skills: ["Next number", "Adding 1 to 3", "Copying sentences"],
    status: "soon",
    preview: { kind: "add", facts: [[3, 1], [7, 1], [5, 2], [6, 3]] },
  },
  {
    slug: "cubs",
    name: "Cubs",
    mascot: "/pictures/bear.svg",
    color: "teal",
    ages: "6+",
    subjects: ["reading", "numbers"],
    blurb: "Adding up to 10 and reading short passages aloud, smoothly and with expression.",
    skills: ["Adding to 10", "Word puzzles", "Reading aloud"],
    status: "soon",
    preview: { kind: "read", lines: ["I see a big bear.", "The bear can swim.", "I like the bear."], picture: "bear" },
  },
];

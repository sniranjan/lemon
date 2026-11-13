import type { TopicSpec } from "../challenges";

// Topic reels for Penguins (grade 7 work), Lions (grade 8) and Whales (grade 9).
export const TOPICS_TEEN: TopicSpec[] = [
  // ---------- Penguins ----------
  // M7-A Adding and Subtracting Negatives (incl. distance |a − b|)
  {
    level: "penguins",
    topic: "Negative numbers",
    seconds: 4,
    questions: [
      { prompt: "Quick!", big: "−4 + 9 = ?", answer: "5" },
      { prompt: "Below zero we go", big: "3 − 8 = ?", answer: "−5" },
      { prompt: "Careful with the signs", big: "−6 − 5 = ?", answer: "−11" },
      { prompt: "Minus a negative…", big: "−2 − (−7) = ?", answer: "5", note: "taking away −7 is adding 7" },
      { prompt: "How far apart?", big: "|−3 − 5| = ?", answer: "8", note: "from −3 to 5 is 8 steps" },
    ],
  },
  // M7-B Multiplying and Dividing Negatives
  {
    level: "penguins",
    topic: "Multiply negatives",
    seconds: 4,
    questions: [
      { prompt: "Quick!", big: "−6 × 3 = ?", answer: "−18" },
      { prompt: "Negative times negative", big: "−5 × (−4) = ?", answer: "20" },
      { prompt: "Share it out", big: "−36 ÷ 9 = ?", answer: "−4" },
      { prompt: "Two negatives…", big: "−42 ÷ (−7) = ?", answer: "6" },
      { prompt: "Three at once!", big: "−2 × 3 × (−5)", answer: "30", note: "two negatives make a positive" },
    ],
  },
  // M7-F Two-Step Equations and Inequalities
  {
    level: "penguins",
    topic: "Two-step equations",
    seconds: 4,
    questions: [
      { prompt: "Solve it", big: "3x + 4 = 19", answer: "x = 5" },
      { prompt: "Solve it", big: "2x − 7 = 9", answer: "x = 8" },
      { prompt: "Undo it step by step", big: "5(x − 2) = 15", answer: "x = 5", note: "x − 2 = 3" },
      { prompt: "Watch the sign!", big: "−4x + 1 = 13", answer: "x = −3", note: "−4x = 12" },
      { prompt: "Solve the inequality", big: "−2x + 1 > 9", answer: "x < −4", note: "dividing by −2 flips the sign" },
    ],
  },
  // R7-C Word Roots (content/wordroots/R7.yaml)
  {
    level: "penguins",
    topic: "Word roots",
    seconds: 5,
    questions: [
      { prompt: "The root “therm” means…", choices: [{ label: "heat" }, { label: "water" }, { label: "sound" }], correct: 0, note: "thermometer: a heat meter" },
      { prompt: "The root “chron” means…", choices: [{ label: "light" }, { label: "time" }, { label: "look" }], correct: 1, note: "chronological: in time order" },
      { prompt: "The root “aud” means…", choices: [{ label: "carry" }, { label: "speak" }, { label: "hear" }], correct: 2, note: "audience: the people who hear" },
      { prompt: "Find the root and its meaning", big: "spectator", answer: "spect = look", note: "a spectator looks on" },
      { prompt: "A pedestrian gets around on…", choices: [{ label: "wheels" }, { label: "foot" }, { label: "wings" }], correct: 1, note: "Latin ped = foot" },
    ],
  },

  // ---------- Lions ----------
  // M8-A Exponents and Square Roots (incl. cube roots, negative exponents, exponent rules)
  {
    level: "lions",
    topic: "Exponents",
    seconds: 4,
    questions: [
      { prompt: "In your head!", big: "2⁵ = ?", answer: "32" },
      { prompt: "Square root", big: "√144 = ?", answer: "12" },
      { prompt: "Cube root", big: "∛64 = ?", answer: "4", note: "4 × 4 × 4 = 64" },
      { prompt: "Write as one power", big: "3⁴ × 3² = ?", answer: "3⁶", note: "same base: add the exponents" },
      { prompt: "Negative exponent", big: "2⁻³ = ?", answer: "1/8", note: "1 over 2³" },
    ],
  },
  // M8-B Very Big and Very Small (scientific notation)
  {
    level: "lions",
    topic: "Powers of ten",
    seconds: 5,
    questions: [
      { prompt: "Scientific notation?", big: "4,000,000", answer: "4 × 10⁶" },
      { prompt: "Write it out", big: "3 × 10⁴ = ?", answer: "30,000" },
      { prompt: "Scientific notation?", big: "0.005", answer: "5 × 10⁻³" },
      { prompt: "10⁸ is how many times 10⁵?", choices: [{ label: "100" }, { label: "1,000" }], correct: 1, note: "10⁸ ÷ 10⁵ = 10³" },
      { prompt: "Tidy it: first part under 10", big: "52 × 10⁴", answer: "5.2 × 10⁵" },
    ],
  },
  // M8-F Right Triangles (Pythagorean theorem, converse, distance)
  {
    level: "lions",
    topic: "Right triangles",
    seconds: 5,
    questions: [
      { prompt: "Legs 6 and 8. Long side?", big: "c = ?", answer: "10", note: "36 + 64 = 100" },
      { prompt: "Legs 5 and 12. Long side?", big: "c = ?", answer: "13", note: "25 + 144 = 169" },
      { prompt: "Long side 15, one leg 9. Other leg?", big: "b = ?", answer: "12", note: "225 − 81 = 144" },
      { prompt: "Sides 4, 5, 6: a right triangle?", choices: [{ label: "Yes" }, { label: "No" }], correct: 1, note: "16 + 25 = 41, not 36" },
      { prompt: "Distance from (1, 2) to (7, 10)?", big: "d = ?", answer: "10", note: "across 6, up 8" },
    ],
  },
  // R8-A Close Reading (figurative language, connotation, allusion: L.8.5a, L.8.5c, RL.8.4)
  {
    level: "lions",
    topic: "Figures of speech",
    seconds: 5,
    questions: [
      { prompt: "“Her voice was velvet.” is a…", choices: [{ label: "simile" }, { label: "metaphor" }, { label: "pun" }], correct: 1, note: "a comparison without like or as" },
      { prompt: "“The wind howled all night.”", choices: [{ label: "personification" }, { label: "hyperbole" }, { label: "simile" }], correct: 0, note: "wind can't really howl" },
      { prompt: "Which word sounds kindest?", choices: [{ label: "stingy" }, { label: "cheap" }, { label: "thrifty" }], correct: 2, note: "same idea, kinder connotation" },
      { prompt: "In the rain: “What a lovely day!”", choices: [{ label: "verbal irony" }, { label: "hyperbole" }, { label: "simile" }], correct: 0, note: "says the opposite of what's meant" },
      { prompt: "“He has the Midas touch.”", choices: [{ label: "hyperbole" }, { label: "allusion" }, { label: "pun" }], correct: 1, note: "points to the myth of King Midas" },
    ],
  },

  // ---------- Whales ----------
  // M9-A Powers and Roots (rational exponents, radicals, negative exponents)
  {
    level: "whales",
    topic: "Powers and roots",
    seconds: 5,
    questions: [
      { prompt: "x to the ½ power is…", choices: [{ label: "√x" }, { label: "x²" }, { label: "2x" }], correct: 0 },
      { prompt: "Simplify", big: "√50", answer: "5√2", note: "√50 = √25 × √2" },
      { prompt: "Simplify", big: "x⁻³ · x⁵ = ?", answer: "x²", note: "add the exponents: −3 + 5" },
      { prompt: "Simplify", big: "(2x³)² = ?", answer: "4x⁶" },
      { prompt: "8 to the 2/3 power is…", choices: [{ label: "16/3" }, { label: "4" }, { label: "2" }], correct: 1, note: "cube root of 8 is 2, and 2² = 4" },
    ],
  },
  // M9-D Factoring
  {
    level: "whales",
    topic: "Factoring",
    seconds: 5,
    questions: [
      { prompt: "Factor it", big: "x² + 7x + 12", answer: "(x + 3)(x + 4)" },
      { prompt: "Factor it", big: "x² − 25", answer: "(x + 5)(x − 5)" },
      { prompt: "Factor it", big: "x² − 2x − 15", answer: "(x + 3)(x − 5)" },
      { prompt: "Factor completely", big: "3x² − 12", answer: "3(x + 2)(x − 2)", note: "take out the 3 first" },
      { prompt: "Factor it", big: "2x² + 7x + 3", answer: "(2x + 1)(x + 3)" },
    ],
  },
  // M9-E Solving Quadratics (square roots, factoring, the formula's b² − 4ac)
  {
    level: "whales",
    topic: "Solving quadratics",
    seconds: 5,
    questions: [
      { prompt: "Solve it", big: "x² = 36", answer: "x = 6 or −6" },
      { prompt: "Solve it", big: "x(x − 4) = 0", answer: "x = 0 or 4" },
      { prompt: "Solve it", big: "x² − 5x + 6 = 0", answer: "x = 2 or 3", note: "(x − 2)(x − 3) = 0" },
      { prompt: "Solve it", big: "(x + 1)² = 9", answer: "x = 2 or −4", note: "x + 1 = 3 or −3" },
      { prompt: "Find b² − 4ac", big: "x² + 4x − 5 = 0", answer: "36", note: "16 − 4(1)(−5) = 36" },
    ],
  },
  // R9-C The Art of Persuasion (rhetoric and weak reasoning: RI.9-10.6, RI.9-10.8)
  {
    level: "whales",
    topic: "Persuasion",
    seconds: 5,
    questions: [
      { prompt: "“Everyone has one. Get one too!”", choices: [{ label: "bandwagon" }, { label: "analogy" }, { label: "anecdote" }], correct: 0, note: "popular doesn't mean right" },
      { prompt: "“We try. We learn. We grow.”", choices: [{ label: "analogy" }, { label: "repetition" }, { label: "bandwagon" }], correct: 1, note: "a repeat makes it stick" },
      { prompt: "“Two were sour, so all apples are.”", choices: [{ label: "bandwagon" }, { label: "no weak spot" }, { label: "too few examples" }], correct: 2, note: "a hasty generalization" },
      { prompt: "“Picture a puppy, cold and alone…”", choices: [{ label: "appeal to emotion" }, { label: "facts and numbers" }, { label: "expert opinion" }], correct: 0, note: "it works on our feelings" },
      { prompt: "“A school is like a garden…”", choices: [{ label: "anecdote" }, { label: "bandwagon" }, { label: "analogy" }], correct: 2, note: "compares two things to explain one" },
    ],
  },
];

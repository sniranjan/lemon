// The public level ladder lives in the generator (repo root syllabus/ladder.yaml). Copy it into the
// site at build time, so the site and the PDFs always agree on level names, ages and subjects.
// A level is "ready" when every one of its strands has a syllabus file (i.e. the generator can make it).
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { parse } from "yaml";

const here = path.dirname(fileURLToPath(import.meta.url));
const syllabus = path.resolve(here, "../../../syllabus");
const rungs = parse(readFileSync(path.join(syllabus, "ladder.yaml"), "utf8"));
const SUBJECT = { english: "reading", math: "math", pencil: "pencil" };

const ladder = rungs.map((r) => ({
  slug: r.slug,
  name: r.public_name,
  title: r.public_title,
  ages: String(r.ages),
  subjects: Object.keys(r.strands).map((s) => SUBJECT[s]),
  ready: Object.entries(r.strands).every(([s, code]) => existsSync(path.join(syllabus, s, `${code}.yaml`))),
}));

const out = path.resolve(here, "../src/data/ladder.json");
mkdirSync(path.dirname(out), { recursive: true });
writeFileSync(out, JSON.stringify(ladder, null, 2) + "\n");
console.log(`synced ${ladder.length} levels (${ladder.filter((l) => l.ready).length} ready)`);

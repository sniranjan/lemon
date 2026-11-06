// The site reuses the worksheet pictures (repo root assets/pictures) so there is one source of truth.
import { cpSync, mkdirSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const src = path.resolve(here, "../../../assets/pictures");
const dest = path.resolve(here, "../public/pictures");
mkdirSync(dest, { recursive: true });
const svgs = readdirSync(src).filter((f) => f.endsWith(".svg"));
for (const f of svgs) cpSync(path.join(src, f), path.join(dest, f));
console.log(`synced ${svgs.length} pictures`);

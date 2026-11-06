"""Check the Otters Reading content and write its draft record (the YAML is the source of truth):
syllabus/drafts/R5-passages.md and syllabus/drafts/R5-figurative.md.

    uv run python scripts/r5_drafts.py            # check everything, write the drafts
    uv run python scripts/r5_drafts.py --check B  # only check section B (prints problems, writes nothing)
    uv run python scripts/r5_drafts.py --check A --file work.yaml --start 27   # a work file of A passages

Checks per passage: words, Flesch-Kincaid grade, title length, question and choice lengths, evidence
found in the text (and in the paragraph a question names), bold words found, question counts, American
spelling, banned words; section D also checks every bold phrase against content/figurative/R5.yaml.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from ws.passages import Passage, find_phrase, passage_problems, section_passages  # noqa: E402
from ws.readability import stats  # noqa: E402
from ws.sheet_types.figurative_language import KINDS, figure_problems, figures  # noqa: E402
from ws.syllabus import load_level, resolve_page  # noqa: E402
from ws.verify import banned_words  # noqa: E402

APPROVAL = ("Approved by the orchestrator under the user's delegation, 2026-11-06 "
            "(\"Take sensible call on the word table, keep the age and our requirement of 2 levels up and "
            "keep going\").")
LEVEL = "R5"


def passage_text(p) -> str:
    return " ".join([p.title, p.text, p.moral or ""] + [t for s in p.pages for q in s.questions
                                                        for t in [q.ask, q.sample or "", *(q.choices or [])]])


def check_section(level, code: str, path: str | None = None, start: int | None = None) -> tuple[list[str], list[tuple]]:
    """(problems, [(passage, first page, stats)]) for one section (or a work file of its passages,
    the first one landing on page `start`)."""
    sec = level.section(code)
    page = start or sec.pages[0]
    probs, rows = [], []
    if path:
        ps = [Passage.model_validate(d) for d in yaml.safe_load(Path(path).read_text()) or []]
    else:
        ps = section_passages(LEVEL, code)
    for p in ps:
        rules = resolve_page(level, page).rules
        st = stats(p.text)
        probs += passage_problems(p, rules, code)
        probs += [f"passage {p.id}: banned word {w!r}" for w in banned_words(passage_text(p))]
        if code == "D":
            probs += figure_problems(p, LEVEL, rules.get("kinds", list(KINDS)))
        if rules.get("paragraphs") and len(p.paragraphs) != rules["paragraphs"]:
            probs.append(f"passage {p.id}: {len(p.paragraphs)} paragraphs (needs {rules['paragraphs']})")
        if rules.get("marks"):
            lo, hi = rules["marks"]
            for k, s in enumerate(p.pages, start=1):
                if not lo <= len(s.words) <= hi:
                    probs.append(f"passage {p.id}: set {k} has {len(s.words)} bold words (needs {lo}–{hi})")
                asks = " ".join(q.ask for q in s.questions)
                probs += [f"passage {p.id}: bold {w!r} isn't asked about in set {k}" for w in s.words
                          if not find_phrase(w, asks)]
        rows.append((p, page, st))
        page += rules.get("pages_per_passage", 2)
    need = sec.pages[1] - sec.pages[0] + 1
    have = page - sec.pages[0]
    if have != need and not path:
        probs.append(f"section {code}: passages cover {have} of {need} pages")
    ids = [p.id for p in ps]
    if len(set(ids)) != len(ids):
        probs.append(f"section {code}: duplicate passage ids")
    return probs, rows


def main() -> int:
    level = load_level("english", LEVEL)
    only = sys.argv[sys.argv.index("--check") + 1] if "--check" in sys.argv else None
    if "--file" in sys.argv:   # a work file: --file PATH --check A [--start 27]
        start = int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else None
        probs, rows = check_section(level, only, sys.argv[sys.argv.index("--file") + 1], start)
        for m in probs:
            print(m)
        for p, page, st in rows:
            print(f"  {p.id}: page {page}, {st['words']} words, FK {st['fk']}")
        print(f"{len(rows)} passages, {len(probs)} problems")
        return 1 if probs else 0
    codes = [only] if only else [s.code for s in level.sections]
    total, fks = 0, []
    lines = ["# Otters Reading passages (draft record)", "", APPROVAL, "",
             "Generated from `content/passages/R5/*.yaml` by `scripts/r5_drafts.py`; edit the YAML, not this file.",
             "Self-review: original articles and stories (fables marked *classic* retell a public-domain idea in our",
             "own words); nonfiction uses well-established facts only, no living people or brands; warm topics;",
             "American spelling; every question answerable from the text (each has an evidence quote that verify",
             "finds in the passage, in the paragraph the question names); Flesch-Kincaid grade 4.5–6.5.", ""]
    for code in codes:
        sec = level.section(code)
        probs, rows = check_section(level, code)
        total += len(probs)
        for m in probs:
            print(m)
        lines += [f"## {code} {sec.public_name} (pages {sec.pages[0]}–{sec.pages[1]}): {len(rows)} passages", ""]
        for p, page, st in rows:
            fks.append(st["fk"])
            n = resolve_page(level, page).rules.get("pages_per_passage", 2)
            lines += [f"### {p.title} (`{p.id}`, pages {page}–{page + n - 1}; {st['words']} words, FK {st['fk']})", ""]
            for i, para in enumerate(p.paragraphs, start=1):   # numbered as on the sheets (A, C, E)
                lines += [f"({i}) {para}" if code in "ACE" else para, ""]
            if p.moral:
                lines += [f"*Theme:* {p.moral}", ""]
            for k, s in enumerate(p.pages, start=1):
                bold = f" — bold: {', '.join(s.words)}" if s.words else ""
                lines.append(f"Question set {k} ({s.focus}){bold}:")
                for n_, q in enumerate(s.questions, start=1):
                    if q.choices:
                        lines.append(f"{n_}. {q.ask} — **{q.choices[0]}** / {q.choices[1]} / {q.choices[2]}")
                    else:
                        lines.append(f"{n_}. {q.ask} — sample: {q.sample}")
                lines.append("")
    if fks:
        print(f"{len(fks)} passages, FK {min(fks)}–{max(fks)}, {total} problems")
    if only:
        return 1 if total else 0
    (ROOT / "syllabus" / "drafts" / "R5-passages.md").write_text("\n".join(lines))
    fl = ["# Otters Reading figurative language (draft record)", "", APPROVAL, "",
          "Generated from `content/figurative/R5.yaml` by `scripts/r5_drafts.py`. Each phrase, its kind and its",
          "meaning checked by hand; verify makes every bold phrase in section D come from this list, and every",
          "\"what does it mean?\" / \"what kind?\" question answer with the listed meaning / kind.", "",
          "| Phrase | Kind | Meaning |", "|---|---|---|"]
    for f in figures(LEVEL).values():
        fl.append(f"| {f.phrase} | {f.kind} | {f.meaning} |")
        for w in banned_words(f.phrase + " " + f.meaning):
            print(f"figurative {f.phrase!r}: banned word {w!r}")
            total += 1
    (ROOT / "syllabus" / "drafts" / "R5-figurative.md").write_text("\n".join(fl) + "\n")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())

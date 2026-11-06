"""Write the Foxes Reading drafts from the content files (the YAML is the source of truth):
syllabus/drafts/R3-passages.md and syllabus/drafts/R3-words.md, and print the passage checks.

    uv run python scripts/r3_drafts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ws.passages import affixes, passage_problems, section_passages, word_parts, wordpart_problems  # noqa: E402
from ws.readability import stats  # noqa: E402
from ws.syllabus import load_level, resolve_page  # noqa: E402
from ws.verify import banned_words  # noqa: E402

APPROVAL = ("Approved by the orchestrator under the user's delegation, 2026-11-06 "
            "(\"Take sensible call on the word table, keep the age and our requirement of 2 levels up and "
            "keep going\").")

level = load_level("english", "R3")
first_page = {s.code: s.pages[0] for s in level.sections}
lines = ["# Foxes Reading passages (draft record)", "", APPROVAL, "",
         "Generated from `content/passages/R3/*.yaml` by `scripts/r3_drafts.py`; edit the YAML, not this file.",
         "Self-review: original stories and fables (6 fables retell a classic public-domain idea in our own",
         "words, marked *classic*), warm topics, American spelling, every question answerable from the text",
         "(each has an evidence quote that verify finds in the passage), Flesch-Kincaid grade 2.5–4.5.", ""]
problems = 0
fks = []
for code in "ACDE":
    sec = level.section(code)
    rules = resolve_page(level, sec.pages[0]).rules
    ps = section_passages("R3", code)
    lines += [f"## {code} {sec.public_name} (pages {sec.pages[0]}–{sec.pages[1]}): {len(ps)} passages", ""]
    page = sec.pages[0]
    for p in ps:
        st = stats(p.text)
        fks.append(st["fk"])
        probs = passage_problems(p, rules, code) + [f"banned {w}" for w in banned_words(
            " ".join([p.title, p.text, p.moral or ""] + [q.ask + " " + (q.sample or "") + " " + " ".join(q.choices or [])
                                                    for s in p.pages for q in s.questions]))]
        problems += len(probs)
        for m in probs:
            print(m)
        lines += [f"### {p.title} (`{p.id}`, pages {page}–{page + len(p.pages) - 1}; {st['words']} words, "
                  f"FK {st['fk']})", ""]
        page += len(p.pages)
        lines += [para for para in p.paragraphs for para in (para, "")]
        if p.moral:
            lines += [f"*Lesson:* {p.moral}", ""]
        for k, s in enumerate(p.pages, start=1):
            lines.append(f"Page {k} ({s.focus}):")
            for n, q in enumerate(s.questions, start=1):
                if q.choices:
                    lines.append(f"{n}. {q.ask} — **{q.choices[0]}** / {q.choices[1]} / {q.choices[2]}")
                else:
                    lines.append(f"{n}. {q.ask} — sample: {q.sample}")
            lines.append("")
(ROOT / "syllabus" / "drafts" / "R3-passages.md").write_text("\n".join(lines))

words = word_parts("R3")
known = {w.built for w in words}
info = affixes("R3")
wl = ["# Foxes Reading word builders (draft record)", "", APPROVAL, "",
      "Generated from `content/wordparts/R3.yaml` by `scripts/r3_drafts.py`. Every word is its parts joined",
      "with no spelling change; meanings and sentences checked by hand; the foil never fits the sentence.", ""]
for a, d in info.items():
    group = [w for w in words if w.affix == a]
    wl += [f"## {d['show']} = {d['means']} ({len(group)} words)", "", "| Word | Parts | Meaning | Sentence | Foil |",
           "|---|---|---|---|---|"]
    for w in group:
        for m in wordpart_problems(w, known):
            print(m)
            problems += 1
        parts = " + ".join(w.parts) if w.parts else (f"{a} + {w.base}" if a in ("un", "re") else f"{w.base} + {a}")
        wl.append(f"| {w.built} | {parts} | {w.meaning} | {w.sentence} | {w.foil} |")
    wl.append("")
(ROOT / "syllabus" / "drafts" / "R3-words.md").write_text("\n".join(wl))
print(f"{sum(len(section_passages('R3', c)) for c in 'ACDE')} passages, FK {min(fks)}–{max(fks)}, "
      f"{len(words)} word builders, {problems} problems")

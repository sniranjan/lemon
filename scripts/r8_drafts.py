"""Write the Lions Reading draft records from the content files (the YAML is the source of truth):
syllabus/drafts/R8-passages.md (sections A, B, D) and syllabus/drafts/R8-story.md (section C, the
story in installments), and print every passage check.

    uv run python scripts/r8_drafts.py            # all sections
    uv run python scripts/r8_drafts.py B          # check one section (still writes the full drafts)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ws.readability import stats  # noqa: E402
from ws.spreads import page_units, section_spreads, spill_units, split_text, spread_problems  # noqa: E402
from ws.syllabus import load_level, resolve_page  # noqa: E402
from ws.verify import banned_words  # noqa: E402

APPROVAL = ("Approved by the orchestrator under the user's delegation, 2026-11-06 "
            "(\"Take sensible call on the word table, keep the age and our requirement of 2 levels up and "
            "keep going\").")
REVIEW = [
    "Self-review: every text is original (characters, places and arguments are ours; nonfiction uses",
    "well-established facts only); no living people, brands, politics, religion or medical advice; arguments",
    "are about school and community life and the set argues both sides of several topics; warm, nothing",
    "scary; American spelling; every question is answerable from the text (each has an evidence quote that",
    "verify finds in the passage; quote choices and quotes inside sample answers are copied from the text);",
    "Flesch-Kincaid grade 7.5–9.5 on every text. Allusions are to well-known myths and tales only.",
]

only = sys.argv[1:] or list("ABCD")
level = load_level("english", "R8")
docs = {
    "R8-passages.md": ["# Lions Reading passages (draft record)", "", APPROVAL, "",
                       "Generated from `content/passages/R8/{A,B,D}.yaml` by `scripts/r8_drafts.py`; edit the YAML, "
                       "not this file.", *REVIEW, ""],
    "R8-story.md": ["# Lions Reading story: The Tower Clock (draft record)", "", APPROVAL, "",
                    "Generated from `content/passages/R8/C.yaml` by `scripts/r8_drafts.py`; edit the YAML, not this "
                    "file.", *REVIEW, ""],
}
problems = 0
fks: list[float] = []
counts: list[int] = []
for code in "ABCD":
    lines = docs["R8-story.md" if code == "C" else "R8-passages.md"]
    sec = level.section(code)
    ps = section_spreads("R8", code)
    spreads = sum(len(p.pages) for p in ps)
    need = (sec.pages[1] - sec.pages[0] + 1) // 2
    if code in only and spreads != need:
        print(f"section {code}: {spreads} question sets, needs {need} (one per two-page spread)")
        problems += 1
    lines += [f"## {code} {sec.public_name} (pages {sec.pages[0]}–{sec.pages[1]}): {len(ps)} passages, "
              f"{spreads} spreads", ""]
    page = sec.pages[0]
    for p in ps:
        rules = resolve_page(level, page).rules
        st = stats(p.text)
        fks.append(st["fk"])
        counts.append(st["words"])
        texts = [p.title, p.text, p.story or ""] + [t for s in p.pages for t in [s.look_for or ""] + [
            t for q in s.questions for t in [q.ask, q.sample or "", q.rubric or "", *(q.choices or []),
                                              *(q.samples or []), *(q.heads or [])]]]
        probs = spread_problems(p, rules) + [f"passage {p.id}: banned word {w!r}" for w in banned_words(" ".join(texts))]
        if code in only:
            problems += len(probs)
            for m in probs:
                print(m)
        first, rest = split_text(p.paragraphs)
        units = [round(page_units(s.questions) + spill_units(p.paragraphs)) for s in p.pages]
        name = f"Part {p.part}: {p.title}" if p.part else p.title
        lines += [f"### {name} (`{p.id}`, {p.genre}, pages {page}–{page + 2 * len(p.pages) - 1}; "
                  f"{st['words']} words, FK {st['fk']}; {len(rest)} paragraph(s) end on the questions page; "
                  f"questions page {'/'.join(map(str, units))} of {rules.get('page_units')} units)", ""]
        page += 2 * len(p.pages)
        lines += [x for n, para in enumerate(p.paragraphs, start=1) for x in (f"{n}. {para}", "")]
        for k, s in enumerate(p.pages, start=1):
            lines.append(f"Set {k} ({s.focus})" + (f", second reading: *{s.look_for}*" if s.look_for else "") + ":")
            for n, q in enumerate(s.questions, start=1):
                if q.kind in ("mc", "quote"):
                    lines.append(f"{n}. [{q.kind}] {q.ask} — **{q.choices[0]}** / " + " / ".join(q.choices[1:]))
                elif q.kind == "organizer":
                    lines.append(f"{n}. [organizer] {q.ask} — " + "; ".join(f"{h}: {v}" for h, v in zip(q.heads, q.samples)))
                else:
                    lines.append(f"{n}. [{q.kind}] {q.ask} — sample: {q.sample}"
                                 + (f" *Full answer:* {q.rubric}" if q.rubric else ""))
            lines.append("")
for name, lines in docs.items():
    (ROOT / "syllabus" / "drafts" / name).write_text("\n".join(lines))
if fks:
    print(f"{len(fks)} passages, {min(counts)}–{max(counts)} words, FK {min(fks)}–{max(fks)}, {problems} problems")
else:
    print("no passages yet")

"""Write the Pandas Reading draft record from the content files (the YAML is the source of truth):
syllabus/drafts/R6-passages.md, and print every passage check.

    uv run python scripts/r6_drafts.py            # all sections
    uv run python scripts/r6_drafts.py B          # check one section (still writes the full draft)
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

only = sys.argv[1:] or list("ABCDE")
level = load_level("english", "R6")
lines = ["# Pandas Reading passages (draft record)", "", APPROVAL, "",
         "Generated from `content/passages/R6/*.yaml` by `scripts/r6_drafts.py`; edit the YAML, not this file.",
         "Self-review: original articles and stories; nonfiction uses well-established facts only (no living",
         "people, brands, politics, medical or legal advice); warm topics; American spelling; every question",
         "answerable from the text (each has an evidence quote that verify finds in the passage; quote choices",
         "and quotes inside sample answers are copied from the text); Flesch-Kincaid grade 5.5–7.5.", ""]
problems = 0
fks: list[float] = []
counts: list[int] = []
for code in "ABCDE":
    sec = level.section(code)
    rules = resolve_page(level, sec.pages[0]).rules
    ps = section_spreads("R6", code)
    spreads = sum(len(p.pages) for p in ps)
    need = (sec.pages[1] - sec.pages[0] + 1) // 2
    if code in only and spreads != need:
        print(f"section {code}: {spreads} question sets, needs {need} (one per two-page spread)")
        problems += 1
    lines += [f"## {code} {sec.public_name} (pages {sec.pages[0]}–{sec.pages[1]}): {len(ps)} passages, "
              f"{spreads} spreads", ""]
    page = sec.pages[0]
    for p in ps:
        st = stats(p.text)
        fks.append(st["fk"])
        counts.append(st["words"])
        texts = [p.title, p.text] + [t for s in p.pages for t in [s.look_for or ""] + [
            t for q in s.questions for t in [q.ask, q.sample or "", q.rubric or "", *(q.choices or []),
                                              *(q.samples or []), *(q.heads or [])]]]
        probs = spread_problems(p, rules) + [f"passage {p.id}: banned word {w!r}" for w in banned_words(" ".join(texts))]
        if code in only:
            problems += len(probs)
            for m in probs:
                print(m)
        first, rest = split_text(p.paragraphs)
        units = [round(page_units(s.questions) + spill_units(p.paragraphs)) for s in p.pages]
        lines += [f"### {p.title} (`{p.id}`, {p.genre}, pages {page}–{page + 2 * len(p.pages) - 1}; "
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
(ROOT / "syllabus" / "drafts" / "R6-passages.md").write_text("\n".join(lines))
if fks:
    print(f"{len(fks)} passages, {min(counts)}–{max(counts)} words, FK {min(fks)}–{max(fks)}, {problems} problems")
else:
    print("no passages yet")

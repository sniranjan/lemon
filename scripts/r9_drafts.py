"""Write the Whales Reading draft record from the content files (the YAML is the source of truth):
syllabus/drafts/R9-passages.md. Checks: `uv run python scripts/r9_check.py` (and `ws verify`).

    uv run python scripts/r9_drafts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ws.readability import stats  # noqa: E402
from ws.spreads import section_spreads, split_text  # noqa: E402
from ws.syllabus import load_level  # noqa: E402

APPROVAL = ("Approved by the orchestrator under the user's delegation, 2026-11-06 "
            "(\"Take sensible call on the word table, keep the age and our requirement of 2 levels up and "
            "keep going\").")

level = load_level("english", "R9")
lines = ["# Whales Reading passages (draft record)", "", APPROVAL, "",
         "Generated from `content/passages/R9/*.yaml` by `scripts/r9_drafts.py`; edit the YAML, not this file.",
         "Self-review: original stories, speeches, essays and letters written for this book; arguments are",
         "kid-relevant and non-political, with no living people, brands, politics, religion or medical advice;",
         "nothing scary or violent; American spelling; every question answerable from the text (each has an",
         "evidence quote that verify finds in the passage; quote choices and quotes inside sample answers are",
         "copied from the text); Flesch-Kincaid grade 8.5–10.5. Each rhetoric text has one deliberate weak",
         "spot in its reasoning for the reader to find (RI.9-10.8).", ""]
fks: list[float] = []
counts: list[int] = []
for sec in level.sections:
    ps = section_spreads("R9", sec.code)
    spreads = sum(len(p.pages) for p in ps)
    lines += [f"## {sec.code} {sec.public_name} (pages {sec.pages[0]}–{sec.pages[1]}): {len(ps)} passages, "
              f"{spreads} spreads", ""]
    page = sec.pages[0]
    for p in ps:
        st = stats(p.text)
        fks.append(st["fk"])
        counts.append(st["words"])
        _, rest = split_text(p.paragraphs)
        lines += [f"### {p.title} (`{p.id}`, {p.genre}, pages {page}–{page + 2 * len(p.pages) - 1}; "
                  f"{st['words']} words, FK {st['fk']}; {len(rest)} paragraph(s) end on the questions page)", ""]
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
(ROOT / "syllabus" / "drafts" / "R9-passages.md").write_text("\n".join(lines))
print(f"{len(fks)} passages, {min(counts)}–{max(counts)} words, FK {min(fks)}–{max(fks)}" if fks else "no passages yet")

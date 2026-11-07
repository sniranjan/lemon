"""Penguins Reading drafts: check the content files and write the draft record (the YAML is the source
of truth): syllabus/drafts/R7-passages.md and syllabus/drafts/R7-roots.md.

    uv run python scripts/r7_drafts.py                    # check everything, write both drafts
    uv run python scripts/r7_drafts.py --check A file.yaml  # check one file as section A (writes nothing)

A check prints each passage's words, Flesch-Kincaid grade and questions-page units, then any problem
(content rules from ws/spreads.py, banned words, British spellings, duplicate ids or titles).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ws import content  # noqa: E402
from ws.readability import stats  # noqa: E402
from ws.roots import explain_problems, explained_on, level_roots, root_problems  # noqa: E402
from ws.spreads import SpreadPassage, page_units, passage_spill_units, section_spreads, spread_problems  # noqa: E402
from ws.syllabus import load_level, resolve_page  # noqa: E402
from ws.verify import banned_words  # noqa: E402

APPROVAL = ("Approved by the orchestrator under the user's delegation, 2026-11-06 "
            "(\"Take sensible call on the word table, keep the age and our requirement of 2 levels up and "
            "keep going, don't wait for my inputs\").")
LEVEL = load_level("english", "R7")


def all_strings(p: SpreadPassage) -> str:
    out = [p.title, p.full_text, *[x for t in p.texts or [] for x in (t.title, t.kind)]]
    for s in p.pages:
        out.append(s.look_for or "")
        for q in s.questions:
            out += [q.ask, q.sample or "", q.rubric or "", *(q.choices or []), *(q.samples or []), *(q.heads or [])]
    return " ".join(out)


def measure(p: SpreadPassage) -> str:
    if p.genre == "poem":
        return f"{len(p.poem_lines)} lines"
    texts = [t.text for t in p.texts] if p.texts else [p.text]
    return ", ".join(f"{stats(t)['words']} words FK {stats(t)['fk']}" for t in texts)


def check(code: str, ps: list[SpreadPassage]) -> list[str]:
    sec = LEVEL.section(code)
    rules = resolve_page(LEVEL, sec.pages[0]).rules
    out = []
    for p in ps:
        units = round(page_units(p.pages[0].questions) + passage_spill_units(p))
        print(f"{p.id}: {measure(p)}; questions page {units} units")
        probs = spread_problems(p, rules) + [f"passage {p.id}: banned word {w!r}" for w in banned_words(all_strings(p))]
        for m in probs:
            print("   ", m)
        out += probs
    for attr in ("id", "title"):
        vals = [getattr(p, attr) for p in ps]
        out += [f"duplicate {attr} {v!r}" for v in sorted({v for v in vals if vals.count(v) > 1})]
    return out


if len(sys.argv) == 4 and sys.argv[1] == "--check":
    code, path = sys.argv[2], Path(sys.argv[3])
    ps = [SpreadPassage.model_validate(d) for d in yaml.safe_load(path.read_text()) or []]
    probs = check(code, ps)
    print(f"{len(ps)} passages, {len(probs)} problems")
    sys.exit(1 if probs else 0)

content.clear_caches()
problems = 0
lines = ["# Penguins Reading passages and poems (draft record)", "", APPROVAL, "",
         "Generated from `content/passages/R7/*.yaml` by `scripts/r7_drafts.py`; edit the YAML, not this file.",
         "Self-review: original articles, arguments, poems and stories; nonfiction and history use well-established",
         "facts only (no living people, brands, politics, religion, medical or legal advice, wars or disasters);",
         "warm topics for a 10-year-old; American spelling; every question answerable from the text (each has an",
         "evidence quote that verify finds in the text; quote choices and quotes inside sample answers are copied",
         "from it); prose at Flesch-Kincaid grade 6.5–8.5 (poems exempt); every written answer has a rubric.", ""]
fks: list[float] = []
for code in "ABDE":
    sec = LEVEL.section(code)
    ps = section_spreads("R7", code)
    print(f"--- section {code}: {len(ps)} passages")
    problems += len(check(code, ps))
    lines += [f"## {code} {sec.public_name} (pages {sec.pages[0]}–{sec.pages[1]}, {len(ps)} passages)", ""]
    for i, p in enumerate(ps):
        page = sec.pages[0] + 2 * i
        lines += [f"### {p.title} (`{p.id}`, pages {page}–{page + 1}; {measure(p)})", ""]
        if p.texts:
            for n, t in enumerate(p.texts, start=1):
                lines += [f"**Text {n}: {t.title}** ({t.kind})", ""] + [para for para in t.paragraphs for para in (para, "")]
        elif p.genre == "poem":
            lines += ["\n".join(f"{line}  " for line in st) + "\n" for st in p.stanzas]
        else:
            lines += [para for para in p.paragraphs for para in (para, "")]
        for s in p.pages:
            lines.append(f"*Questions ({s.focus}):*")
            lines.append("")
            for n, q in enumerate(s.questions, start=1):
                if q.choices:
                    lines.append(f"{n}. {q.ask} — **{q.choices[0]}** / " + " / ".join(q.choices[1:]))
                else:
                    lines.append(f"{n}. {q.ask} — sample: {q.sample} *Rubric:* {q.rubric}")
            lines.append("")
        if p.genre != "poem":
            fks += [stats(t)["fk"] for t in ([x.text for x in p.texts] if p.texts else [p.text])]
lines.insert(4, f"Flesch-Kincaid range of the prose: {min(fks)}–{max(fks)}." if fks else "")
(ROOT / "syllabus" / "drafts" / "R7-passages.md").write_text("\n".join(lines) + "\n")

roots = level_roots("R7")
rl = ["# Penguins Reading word roots (draft record)", "", APPROVAL, "",
      "Generated from `content/wordroots/R7.yaml` by `scripts/r7_drafts.py`; edit the YAML, not this file.",
      "Self-review: grade 7 roots (L.7.4b), each word's origin checked by hand against standard etymologies; Latin and",
      "Greek roots that share a meaning are paired on purpose (ped/pod, rupt/fract); sentences use the word in a",
      "plain, everyday context; explain words are not on their page.", "",
      "| # | Root | Origin | Meaning | Words (example; matched; review) | Explain |", "|---|---|---|---|---|---|"]
for i, r in enumerate(roots, start=1):
    probs = root_problems(r)
    for m in probs:
        print("   ", m)
    problems += len(probs)
    ex = f"{r.explain.word} ({explained_on('R7', r.root)} page)" if r.explain else "—"
    rl.append(f"| {i} | {r.root} | {r.origin} | {r.meaning} | {', '.join(w.word for w in r.words)} | {ex} |")
for m in explain_problems("R7"):
    print("   ", m)
    problems += 1
(ROOT / "syllabus" / "drafts" / "R7-roots.md").write_text("\n".join(rl) + "\n")
print(f"{problems} problems; FK {min(fks) if fks else '-'}–{max(fks) if fks else '-'}")
sys.exit(1 if problems else 0)

"""Check the Owls Reading reads and (with --write) write the draft record from the content files
(the YAML is the source of truth): syllabus/drafts/R4-reads.md.

    uv run python scripts/r4_drafts.py            # check every section, print problems and stats
    uv run python scripts/r4_drafts.py B          # check one section
    uv run python scripts/r4_drafts.py --write    # also write the draft record
    uv run python scripts/r4_drafts.py A --file=path/to/more.yaml   # check reads in another file by A's rules
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from ws.longreads import LongRead, read_problems, section_reads  # noqa: E402
from ws.readability import stats  # noqa: E402
from ws.syllabus import load_level, resolve_page  # noqa: E402
from ws.verify import banned_words  # noqa: E402

APPROVAL = ("Approved by the orchestrator under the user's delegation, 2026-11-06 "
            "(\"Take sensible call on the word table, keep the age and our requirement of 2 levels up and "
            "keep going\").")

args = [a for a in sys.argv[1:] if not a.startswith("--")]
write = "--write" in sys.argv
other = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--file=")), None)
codes = args or list("ABCDE")
level = load_level("english", "R4")
lines = ["# Owls Reading reads (draft record)", "", APPROVAL, "",
         "Generated from `content/passages/R4/*.yaml` by `scripts/r4_drafts.py`; edit the YAML, not this file.",
         "Self-review: original stories and articles, warm topics, simple well-established facts, American",
         "spelling, every question answerable from the text (each has an evidence quote that verify finds in",
         "the read), Flesch-Kincaid grade 3.5–5.5 on the body text.", ""]
problems = 0
fks: list[float] = []
for code in codes:
    sec = level.section(code)
    rules = resolve_page(level, sec.pages[0]).rules
    reads = ([LongRead.model_validate(d) for d in yaml.safe_load(Path(other).read_text())] if other
             else section_reads("R4", code))
    per = 2 if rules.get("spread") else 1
    pages = sum(per if rules.get("spread") else len(p.pages) for p in reads)
    need = sec.pages[1] - sec.pages[0] + 1
    print(f"{code} {sec.public_name}: {len(reads)} reads, {pages}/{need} pages")
    lines += [f"## {code} {sec.public_name} (pages {sec.pages[0]}–{sec.pages[1]}): {len(reads)} reads", ""]
    page = sec.pages[0]
    for p in reads:
        rules_p = resolve_page(level, min(page, sec.pages[1])).rules
        texts = p.all_strings() + [t for s in p.pages for q in s.questions
                                   for t in [q.ask, q.sample or "", q.starter or "", *(q.choices or [])]]
        probs = read_problems(p, rules_p) + [f"read {p.id}: banned word {w!r}" for w in banned_words(" ".join(texts))]
        problems += len(probs)
        for m in probs:
            print("  " + m)
        sts = [stats(b) for b in p.body_texts]
        fks += [s["fk"] for s in sts]
        n = per if rules.get("spread") else len(p.pages)
        info = "; ".join(f"{s['words']} words, FK {s['fk']}" for s in sts)
        print(f"  {p.id}: pages {page}–{page + n - 1}; {info}")
        head = f"{p.story}, chapter {p.chapter}: " if p.story else ""
        lines += [f"### {head}{p.title} (`{p.id}`, pages {page}–{page + n - 1}; {info})", ""]
        page += n
        for t in p.texts or []:
            lines += [f"**{t.title}** ({t.kind})", ""] + [x for para in t.text.strip().split("\n\n")
                                                          for x in (" ".join(para.split()), "")]
        for b in p.blocks:
            lines += [f"**{b['h']}**" if "h" in b else b["p"], ""]
        if p.figure:
            f = p.figure
            body = " → ".join(f.items) if f.items else " / ".join(" | ".join(r) for r in f.rows)
            lines += [f"*Figure ({f.kind}): {f.title}.* {body}. *Caption:* {f.caption}", ""]
        for k, s in enumerate(p.pages, start=1):
            bold = f"; bold: {', '.join(s.targets)}" if s.targets else ""
            lines.append(f"Questions{f' (page {k})' if len(p.pages) > 1 else ''} ({s.focus}{bold}):")
            for i, q in enumerate(s.questions, start=1):
                if q.choices:
                    lines.append(f"{i}. {q.ask} — **{q.choices[0]}** / {q.choices[1]} / {q.choices[2]}")
                else:
                    lines.append(f"{i}. {q.ask} — sample: {q.sample}")
            lines.append("")
    if pages != need:
        print(f"  section {code} fills {pages} of {need} pages")
        problems += 1
if write:
    (ROOT / "syllabus" / "drafts" / "R4-reads.md").write_text("\n".join(lines))
print(f"FK {min(fks, default=0)}–{max(fks, default=0)}, {problems} problems")

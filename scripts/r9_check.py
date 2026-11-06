"""Check Whales Reading passages before they are generated: `uv run python scripts/r9_check.py [A B C D]`.

For each passage in content/passages/R9/<section>.yaml: the schema, ws.spreads.spread_problems with the
rules of the pages each question set lands on (level → section → part), the section D paragraph rules
(sentence count, quotes, rubric parts), banned words, and a stats line (words, FK, what spills onto the
questions page). Exit 1 on any problem.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ws.readability import fk_grade, sentences, words  # noqa: E402
from ws.spreads import SpreadPassage, page_units, spill_units, split_text, spread_problems  # noqa: E402
from ws.verify import banned_words  # noqa: E402

_QUOTED = re.compile(r"[\"“]([^\"”]+)[\"”]")


def merged_rules(level: dict, section: dict, page: int) -> dict:
    rules = {**level.get("rules", {}), **section.get("rules", {})}
    for part in section.get("parts", []):
        lo, hi = part["pages"]
        if lo <= page <= hi:
            rules.update(part.get("rules", {}))
    return rules


def main(codes: list[str]) -> int:
    level = yaml.safe_load((ROOT / "syllabus/english/R9.yaml").read_text())
    bad = 0
    for sec in level["sections"]:
        if codes and sec["code"] not in codes:
            continue
        path = ROOT / "content/passages/R9" / f"{sec['code']}.yaml"
        if not path.exists():
            print(f"{sec['code']}: no file yet")
            continue
        raw = yaml.safe_load(path.read_text()) or []
        page = sec["pages"][0]
        fks = []
        for d in raw:
            try:
                p = SpreadPassage.model_validate(d)
            except Exception as e:  # noqa: BLE001
                print(f"  SCHEMA {d.get('id')}: {e}")
                bad += 1
                continue
            probs: list[str] = []
            for k, s in enumerate(p.pages):
                rules = merged_rules(level, sec, page)
                # spread_problems checks set counts and second-reading prompts: run it on the real passage
                # with this page's rules, keeping messages about this set only
                for m in spread_problems(p, rules):
                    if "paragraph_sentences" in rules and "paragraph sample has" in m:
                        continue   # section D's own sentence range is checked below
                    if f"set {k + 1}:" in m or " set " not in m:
                        probs.append(m)
                for q in s.questions:
                    if q.kind == "paragraph" and "paragraph_sentences" in rules:
                        lo, hi = rules["paragraph_sentences"]
                        n = len(sentences(q.sample))
                        if not lo <= n <= hi:
                            probs.append(f"set {k + 1}: paragraph sample has {n} sentences (needs {lo}–{hi})")
                        nq = len(_QUOTED.findall(q.sample))
                        if nq < rules.get("paragraph_quotes", 1):
                            probs.append(f"set {k + 1}: paragraph sample quotes {nq} times (needs {rules['paragraph_quotes']})")
                    if q.kind == "paragraph" and "rubric_parts" in rules:
                        for part in rules["rubric_parts"]:
                            if f"{part}:" not in q.rubric:
                                probs.append(f"set {k + 1}: rubric needs '{part}:'")
                page += 2
            text = " ".join([p.title, p.text] + [t for s in p.pages for t in [s.look_for or ""] + [
                t for q in s.questions for t in [q.ask, q.sample or "", q.rubric or "", *(q.choices or []),
                                                  *(q.samples or []), *(q.heads or [])]]])
            for w in banned_words(text):
                probs.append(f"banned word {w!r}")
            probs = list(dict.fromkeys(probs))
            fk = fk_grade(p.text)
            fks.append(fk)
            _, rest = split_text(p.paragraphs)
            units = [round(page_units(s.questions) + spill_units(p.paragraphs)) for s in p.pages]
            print(f"{p.id:34} {len(words(p.text)):4}w FK {fk:5}  spill {len(' '.join(r['text'] for r in rest).split()):3}w"
                  f"  units {units}  {'OK' if not probs else 'PROBLEMS'}")
            for m in probs:
                print("    -", m)
            bad += bool(probs)
        if fks:
            print(f"{sec['code']}: {len(raw)} passages, {sum(len(x['pages']) for x in raw)} spreads "
                  f"(needs {(sec['pages'][1] - sec['pages'][0] + 1) // 2}), FK {min(fks)}–{max(fks)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

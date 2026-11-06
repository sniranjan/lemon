"""MA 3A-C…F, 2A (and later levels): a list of `a + b = box` facts; answer key generated.

Written generally so later levels can reuse it (subtraction, bigger numbers). Rules (merged
level → section → part):
- `op`: "+" (default) or "-".
- `addend` (or the generic `second`): the second number, one number or a list of numbers.
- `min_first` (default 1), `max_first`: the first number's range (the part's range, CLAUDE.md §8).
  For "-", facts with a negative answer are skipped.
- `new_from` (optional): about half the facts start at or above it (the part's new numbers).
- `rows`: rows per column (default 5); facts are shown in two columns, read top to bottom.
- `bridge` (even, "+1" only): that many facts also show "n → box" above "n + 1 = box", so the
  child sees that adding 1 is the next number. A bridged fact takes two rows; they come first
  in each column.

The answer key has one answer per box, top to bottom, left column first (a bridged fact gives
two: the next number and the sum, which are equal).
"""

from __future__ import annotations

import math
import operator

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

OPS = {"+": operator.add, "-": operator.sub}
OP_WORDS = {"+": "Add", "-": "Take away"}


def fact_shape(rules: dict) -> dict:
    """Normalize a part's rules (shared by generate and verify)."""
    op = rules.get("op", "+")
    if op not in OPS:
        raise ValueError(f"add_facts: unknown op {op!r}")
    second = rules.get("second", rules.get("addend"))
    if second is None:
        raise ValueError("add_facts: the part needs `addend` (or `second`)")
    seconds = [second] if isinstance(second, int) else list(second)
    lo, hi = rules.get("min_first", 1), rules["max_first"]
    rows, bridge = rules.get("rows", 5), rules.get("bridge", 0)
    if bridge % 2 or bridge > rows:
        raise ValueError(f"add_facts: bridge must be even and fit {rows} rows per column, got {bridge}")
    if bridge and (op != "+" or seconds != [1]):
        raise ValueError("add_facts: bridge is only for +1 facts")
    per_col = bridge // 2 + (rows - bridge)
    facts = [(a, b) for a in range(lo, hi + 1) for b in seconds if OPS[op](a, b) >= 0]
    new_from = rules.get("new_from")
    new_pool = [f for f in facts if new_from is not None and f[0] >= new_from]
    count = 2 * per_col
    return {"op": op, "seconds": seconds, "lo": lo, "hi": hi, "rows": rows, "bridge": bridge,
            "per_col": per_col, "count": count, "facts": facts, "new_from": new_from,
            "need_new": min(math.ceil(count / 2), len(new_pool)), "new_pool": new_pool}


def answers_for(items: list[dict]) -> list[int]:
    out = []
    for i in items:
        if i.get("bridge"):
            out.append(i["a"] + 1)
        out.append(OPS[i["op"]](i["a"], i["b"]))
    return out


@register("add_facts")
class AddFacts(SheetType):
    template = "add_facts.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        s = fact_shape(ctx.rules)
        count, need = s["count"], s["need_new"]
        old_pool = [f for f in s["facts"] if f not in s["new_pool"]]
        take_old = min(count - need, len(old_pool))
        need = count - take_old
        if need > len(s["new_pool"]):
            raise ValueError(f"add_facts: only {len(s['facts'])} facts in this part, need {count}")
        facts = ctx.rng.sample(s["new_pool"], need) + ctx.rng.sample(old_pool, take_old)
        ctx.rng.shuffle(facts)
        items = []
        for col in (facts[:s["per_col"]], facts[s["per_col"]:]):
            for k, (a, b) in enumerate(col):
                items.append({"kind": "fact", "a": a, "op": s["op"], "b": b, "bridge": k < s["bridge"] // 2})
        seconds = s["seconds"]
        what = str(seconds[0]) if len(seconds) == 1 else ", ".join(map(str, seconds[:-1])) + f" or {seconds[-1]}"
        return SheetContent(title=f"{OP_WORDS[s['op']]} {what}", parent_tip=ctx.tip(self.name),
                            items=items, answer_key=answers_for(items))

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        s = fact_shape(resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules)
        items, issues = sheet.items, []
        if len(items) != s["count"]:
            issues.append(error(sheet, f"{len(items)} facts; the part asks for {s['count']}"))
        for i in items:
            a, b, op = i["a"], i["b"], i["op"]
            if op != s["op"]:
                issues.append(error(sheet, f"fact {a} {op} {b}: this part uses {s['op']}"))
                continue
            if b not in s["seconds"]:
                issues.append(error(sheet, f"fact {a} {op} {b}: the second number must be one of {s['seconds']}"))
            if not s["lo"] <= a <= s["hi"]:
                issues.append(error(sheet, f"fact {a} {op} {b}: first number outside this part's range {s['lo']}–{s['hi']}"))
            if OPS[op](a, b) < 0:
                issues.append(error(sheet, f"fact {a} {op} {b} has a negative answer"))
        pairs = [(i["a"], i["b"]) for i in items]
        if len(set(pairs)) != len(pairs):
            issues.append(error(sheet, "the same fact appears twice"))
        per_col = s["per_col"]
        for col in (items[:per_col], items[per_col:]):
            flags = [bool(i.get("bridge")) for i in col]
            want = [k < s["bridge"] // 2 for k in range(len(col))]
            if flags != want:
                issues.append(error(sheet, f"bridged facts {flags} should be the first {s['bridge'] // 2} of each column"))
        if any(i.get("bridge") and (i["op"] != "+" or i["b"] != 1) for i in items):
            issues.append(error(sheet, "a bridged fact must be n + 1"))
        if any(i["op"] not in OPS for i in items):
            return issues
        if sheet.answer_key != answers_for(items):
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the facts {answers_for(items)}"))
        if s["new_from"] is not None and sum(i["a"] >= s["new_from"] for i in items) < s["need_new"]:
            issues.append(error(sheet, f"fewer than {s['need_new']} facts use the part's new numbers (from {s['new_from']})"))
        return issues

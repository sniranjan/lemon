"""Ratio tables (Pandas math, 6.RP.1 and 6.RP.3a): two rows that grow by the same multiplier.

Each table has a context from content/math/ratios.yaml (row labels and a sentence), a simplest
ratio `base` [a, b] (a and b share no factor) and the column multipliers `mults`; column k holds
a × mults[k] and b × mults[k]. Rules (merged level → section → part):
- `tables`: tables a page (default 4). `columns`: columns a table (default 5).
- `base`: [lo, hi] for each number of the simplest ratio (the two are never equal).
- `start`: true: the first column is the simplest ratio (multiplier 1), shown in full, the
  sentence names it, and the multipliers are 1, 2, 3… in order. false: the multipliers are
  sorted picks from `multipliers` [lo, hi]; one column (never the first) is shown in full and the
  child also writes the simplest ratio.
- `max_value`: no number in a table above it.
- `title`: the sheet title.
`mode: proportional` (Penguins math, 7.RP.2): is the table proportional, k, y = kx; see _proportional.py.
Every other column has exactly one empty cell (top or bottom). Answers per table: the empty
cells left to right, then the simplest ratio "a:b" when the child writes it.
"""

from __future__ import annotations

from math import gcd

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from . import _proportional
from ._common import error, page_rules

TABLES = 4
COLUMNS = 5
MAX_TRIES = 2000


def contexts() -> dict[str, dict]:
    from ..content import math_frames

    return {c["id"]: c for c in math_frames("ratios")}


def sentence(ctx: dict, a: int, b: int) -> str:
    top = ctx["top"][0 if a == 1 else 1]
    bottom = ctx["bottom"][0 if b == 1 else 1]
    return ctx["text"].format(a=a, b=b, top=top, bottom=bottom)


def answers_for(t: dict) -> list[str]:
    rows = (t["top"], t["bottom"])
    out = [str(rows[r][c]) for c, r in sorted((c, r) for r, c in t["blanks"])]
    if t["ask_simplest"]:
        out.append(f"{t['base'][0]}:{t['base'][1]}")
    return out


@register("ratio_table")
class RatioTable(SheetType):
    template = "ratio_table.html.j2"

    def template_for(self, sheet: Sheet) -> str:
        return _proportional.TEMPLATE if sheet.items and sheet.items[0].get("kind") == "proportion" else self.template

    def generate(self, ctx: GenContext) -> SheetContent:
        if _proportional.is_proportional_mode(ctx.rules):
            return _proportional.generate(ctx, self.name)
        r = ctx.rules
        count, cols = r.get("tables", TABLES), r.get("columns", COLUMNS)
        lo, hi = r["base"]
        start = r["start"]
        pool = list(contexts().values())
        chosen = ctx.rng.sample(pool, count)
        items, bases = [], set()
        for n, c in enumerate(chosen, 1):
            for _ in range(MAX_TRIES):
                a, b = ctx.rng.randint(lo, hi), ctx.rng.randint(lo, hi)
                if a == b or gcd(a, b) != 1 or (a, b) in bases:
                    continue
                if start:
                    mults = list(range(1, cols + 1))
                else:
                    mlo, mhi = r["multipliers"]
                    mults = sorted(ctx.rng.sample(range(mlo, mhi + 1), cols))
                if max(a, b) * mults[-1] <= r["max_value"]:
                    break
            else:
                raise ValueError(f"ratio_table: no ratio fits {r}")
            bases.add((a, b))
            full = 0 if start else ctx.rng.randrange(1, cols)
            blanks = [[ctx.rng.randrange(2), k] for k in range(cols) if k != full]
            items.append({
                "kind": "table", "n": n, "context": c["id"],
                "text": sentence(c, a, b) if start else None,
                "top_label": c["top"][1], "bottom_label": c["bottom"][1],
                "base": [a, b], "mults": mults,
                "top": [a * m for m in mults], "bottom": [b * m for m in mults],
                "blanks": blanks, "ask_simplest": not start,
            })
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[x for t in items for x in answers_for(t)])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        if _proportional.is_proportional_mode(r):
            return _proportional.verify(sheet, r)
        count, cols = r.get("tables", TABLES), r.get("columns", COLUMNS)
        known = contexts()
        issues: list[Issue] = []
        items = sheet.items
        if len(items) != count:
            issues.append(error(sheet, f"{len(items)} tables; this part has {count}"))
        if [t.get("n") for t in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "tables are not numbered 1, 2, 3… in order"))
        if len({t.get("context") for t in items}) != len(items) or len({tuple(t["base"]) for t in items}) != len(items):
            issues.append(error(sheet, "two tables share a context or a ratio"))
        for t in items:
            label = f"table {t.get('n')}"
            c = known.get(t.get("context"))
            if c is None:
                issues.append(error(sheet, f"{label}: context {t.get('context')!r} doesn't exist"))
                continue
            a, b = t["base"]
            lo, hi = r["base"]
            if not (lo <= a <= hi and lo <= b <= hi) or a == b or gcd(a, b) != 1:
                issues.append(error(sheet, f"{label}: {a}:{b} isn't a simplest ratio in {lo}–{hi}"))
            mults = t["mults"]
            if len(mults) != cols or mults != sorted(set(mults)):
                issues.append(error(sheet, f"{label}: multipliers {mults} must be {cols} different, in order"))
            if r["start"] and mults != list(range(1, cols + 1)):
                issues.append(error(sheet, f"{label}: a first table grows 1, 2, 3…, not {mults}"))
            if not r["start"] and not all(r["multipliers"][0] <= m <= r["multipliers"][1] for m in mults):
                issues.append(error(sheet, f"{label}: multipliers {mults} are outside {r['multipliers']}"))
            if t["top"] != [a * m for m in mults] or t["bottom"] != [b * m for m in mults]:
                issues.append(error(sheet, f"{label}: a column isn't {a}:{b} times its multiplier"))
            if max(t["top"] + t["bottom"]) > r["max_value"]:
                issues.append(error(sheet, f"{label}: a number is above {r['max_value']}"))
            if (t["top_label"], t["bottom_label"]) != (c["top"][1], c["bottom"][1]):
                issues.append(error(sheet, f"{label}: row labels don't match the context"))
            expected_text = sentence(c, a, b) if r["start"] else None
            if t.get("text") != expected_text:
                issues.append(error(sheet, f"{label}: the sentence should be {expected_text!r}"))
            cols_blank = sorted(k for _, k in t["blanks"])
            full = [k for k in range(cols) if k not in cols_blank]
            if (len(full) != 1 or len(cols_blank) != cols - 1 or not all(row in (0, 1) for row, _ in t["blanks"])
                    or (r["start"] and full != [0]) or (not r["start"] and full == [0])):
                issues.append(error(sheet, f"{label}: one column is shown in full and every other column has "
                                           f"one empty cell"))
            if t["ask_simplest"] == r["start"]:
                issues.append(error(sheet, f"{label}: the simplest-ratio box belongs on tables without a first column"))
        expected = [x for t in items for x in answers_for(t)]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the tables {expected}"))
        return issues

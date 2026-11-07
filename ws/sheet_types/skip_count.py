"""Cubs math (M2-C): skip-counting tracks (by 5s, 10s or 100s) with empty boxes to write in.

Rules (merged level → section → part):
- `steps`: the steps used on this part, e.g. [5, 10]; tracks take turns, so each step turns up.
- `min`, `max`: every number on a track stays inside this range.
- `length`: boxes per track (default 8). `rows`: tracks per sheet (default 4).
- `gaps`: empty boxes per track. The first two boxes always show (so the step can be seen),
  and two empty boxes are never side by side.
Tracks start on a multiple of their step (5, 10, 15 … / 230, 240 … / 100, 200 …).
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules

SHOWN_AT_START = 2


def _gap_positions(ctx: GenContext, length: int, gaps: int) -> list[int]:
    for _ in range(1000):
        picked = sorted(ctx.rng.sample(range(SHOWN_AT_START, length), gaps))
        if all(b - a > 1 for a, b in zip(picked, picked[1:])):
            return picked
    raise ValueError(f"skip_count: can't place {gaps} separate gaps in {length} boxes")


def starts(step: int, lo: int, hi: int, length: int) -> list[int]:
    first = -(-lo // step) * step
    return [s for s in range(first, hi + 1, step) if s + step * (length - 1) <= hi]


@register("skip_count")
class SkipCount(SheetType):
    template = "skip_count.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        steps, lo, hi = r["steps"], r["min"], r["max"]
        length, rows, gaps = r.get("length", 8), r.get("rows", 4), r["gaps"]
        offset = rng.randrange(len(steps))
        items, used = [], set()
        for k in range(rows):
            step = steps[(k + offset) % len(steps)]
            options = [s for s in starts(step, lo, hi, length) if (step, s) not in used]
            if not options:
                raise ValueError(f"skip_count: no more tracks by {step} of {length} inside {lo}–{hi}")
            s = rng.choice(options)
            used.add((step, s))
            items.append({"kind": "skip", "step": step, "cells": [s + step * i for i in range(length)],
                          "gaps": _gap_positions(ctx, length, gaps)})
        answers = [i["cells"][g] for i in items for g in i["gaps"]]
        names = " and ".join(f"{s}s" for s in steps)
        return SheetContent(title=f"Count by {names}", parent_tip=ctx.tip(self.name), items=items,
                            answer_key=answers)

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        steps, lo, hi = r["steps"], r["min"], r["max"]
        length, gaps = r.get("length", 8), r["gaps"]
        issues, answers = [], []
        if len(sheet.items) != r.get("rows", 4):
            issues.append(error(sheet, f"{len(sheet.items)} tracks; the part asks for {r.get('rows', 4)}"))
        for i in sheet.items:
            step, cells, g = i["step"], i["cells"], i["gaps"]
            if step not in steps:
                issues.append(error(sheet, f"counting by {step}; this part counts by {steps}"))
            if len(cells) != length:
                issues.append(error(sheet, f"track has {len(cells)} boxes, expected {length}"))
            if cells != [cells[0] + step * k for k in range(len(cells))] or cells[0] % step:
                issues.append(error(sheet, f"track {cells} doesn't count by {step} from a multiple of {step}"))
            if cells[0] < lo or cells[-1] > hi:
                issues.append(error(sheet, f"track {cells[0]}–{cells[-1]} is outside this part's range {lo}–{hi}"))
            if len(g) != gaps or g != sorted(set(g)):
                issues.append(error(sheet, f"track from {cells[0]} has gaps {g}; expected {gaps} distinct"))
            if any(not SHOWN_AT_START <= p < len(cells) for p in g):
                issues.append(error(sheet, f"gap position out of range (the first two boxes must show): {g}"))
            elif any(b - a < 2 for a, b in zip(g, g[1:])):
                issues.append(error(sheet, f"two empty boxes side by side: {g}"))
            else:
                answers += [cells[p] for p in g]
        if len(sheet.items) >= len(steps) and {i["step"] for i in sheet.items} != set(steps):
            issues.append(error(sheet, f"every step in {steps} should have a track"))
        if sheet.answer_key != answers:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the gaps {answers}"))
        return issues

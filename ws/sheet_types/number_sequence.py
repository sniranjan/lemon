"""MA 5A-B/C/D: number tracks of consecutive numbers with a few empty boxes to say aloud.

Rules (merged level → section → part):
- `min`, `max`: the part's number limit; every number on a track stays inside it.
- `length`: boxes per track (default 10). `rows`: tracks per sheet (default 4).
- `gaps`: empty boxes per track. The first box is always shown (the child's starting point)
  and two empty boxes are never side by side, so each gap can be found from its neighbors.
- `new_from` (optional): at least one track reaches a number ≥ this, so the part's new
  numbers turn up on every page.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules


def _gap_positions(ctx: GenContext, length: int, gaps: int) -> list[int]:
    for _ in range(1000):
        picked = sorted(ctx.rng.sample(range(1, length), gaps))
        if all(b - a > 1 for a, b in zip(picked, picked[1:])):
            return picked
    raise ValueError(f"can't place {gaps} separate gaps in {length} boxes")


@register("number_sequence")
class NumberSequence(SheetType):
    template = "number_sequence.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        lo, hi, length, rows, gaps = r["min"], r["max"], r.get("length", 10), r.get("rows", 4), r["gaps"]
        starts_ok = list(range(lo, hi - length + 2))
        if len(starts_ok) < rows:
            raise ValueError(f"number_sequence: {lo}–{hi} is too small for {rows} tracks of {length}")
        new_from = r.get("new_from")
        reaching = [s for s in starts_ok if new_from is not None and s + length - 1 >= new_from]
        if new_from is not None and not reaching:
            raise ValueError(f"number_sequence: no track of {length} inside {lo}–{hi} reaches {new_from}")
        while True:
            starts = sorted(ctx.rng.sample(starts_ok, rows))
            if new_from is None or any(s in reaching for s in starts):
                break
        items = []
        for s in starts:
            cells = list(range(s, s + length))
            items.append({"kind": "track", "cells": cells, "gaps": _gap_positions(ctx, length, gaps)})
        answers = [i["cells"][g] for i in items for g in i["gaps"]]
        return SheetContent(title="Missing numbers", parent_tip=ctx.tip(self.name), items=items,
                            answer_key=answers)

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        lo, hi, length, gaps = r["min"], r["max"], r.get("length", 10), r["gaps"]
        issues = []
        if len(sheet.items) != r.get("rows", 4):
            issues.append(error(sheet, f"{len(sheet.items)} tracks; the part asks for {r.get('rows', 4)}"))
        answers = []
        for i in sheet.items:
            cells, g = i["cells"], i["gaps"]
            if len(cells) != length:
                issues.append(error(sheet, f"track has {len(cells)} boxes, expected {length}"))
            if cells != list(range(cells[0], cells[0] + len(cells))):
                issues.append(error(sheet, f"track {cells} is not counting up by ones"))
            if cells[0] < lo or cells[-1] > hi:
                issues.append(error(sheet, f"track {cells[0]}–{cells[-1]} is outside this part's range {lo}–{hi}"))
            if len(g) != gaps or len(set(g)) != len(g) or g != sorted(g):
                issues.append(error(sheet, f"track starting {cells[0]} has gaps {g}; expected {gaps} distinct"))
            if any(not 1 <= p < len(cells) for p in g):
                issues.append(error(sheet, f"gap position out of range (first box must show): {g}"))
            elif any(b - a < 2 for a, b in zip(g, g[1:])):
                issues.append(error(sheet, f"two empty boxes side by side: {g}"))
            else:
                answers += [cells[p] for p in g]
        if sheet.answer_key != answers:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the gaps {answers}"))
        new_from = r.get("new_from")
        if new_from is not None and not any(i["cells"][-1] >= new_from for i in sheet.items):
            issues.append(error(sheet, f"no track reaches the part's new numbers (from {new_from})"))
        return issues

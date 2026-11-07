"""MA 4A-B…E: writing numbers.

Two modes (`rules.mode`):
- `copy`: `blocks` (default 3) runs of `run` consecutive numbers. Each block is a row of dotted
  numerals to trace, then a row of empty boxes to write the same numbers in. The answer key
  is the numbers written.
- `fill`: `blocks` (default 3) tracks of `length` consecutive numbers (default 10, shown as two
  rows of five) with `gaps` empty boxes to write the missing numbers in. The first box is
  always printed and three empty boxes never come one after another, so every gap can be
  worked out from a printed neighbor. The answer key is the missing numbers, in order.

Common rules: `min`, `max` (every number stays inside them) and optional `new_from`
(at least one block reaches a number ≥ this, so the part's new numbers turn up on every page).
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules
from .number_trace import check_range

MODES = ("copy", "fill")
TITLES = {"copy": "Trace, then write", "fill": "Missing numbers"}


def _starts(lo: int, hi: int, length: int, new_from: int | None) -> tuple[list[int], list[int]]:
    ok = list(range(lo, hi - length + 2))
    reaching = [s for s in ok if new_from is not None and s + length - 1 >= new_from]
    return ok, reaching


def _gaps(ctx: GenContext, length: int, gaps: int) -> list[int]:
    for _ in range(1000):
        picked = sorted(ctx.rng.sample(range(1, length), gaps))
        if not any(b == a + 1 and c == b + 1 for a, b, c in zip(picked, picked[1:], picked[2:])):
            return picked
    raise ValueError(f"number_write: can't place {gaps} gaps in {length} boxes")


@register("number_write")
class NumberWrite(SheetType):
    template = "number_write.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        mode = r.get("mode", "copy")
        if mode not in MODES:
            raise ValueError(f"number_write: unknown mode {mode!r} (use one of {', '.join(MODES)})")
        lo, hi, blocks, new_from = r["min"], r["max"], r.get("blocks", 3), r.get("new_from")
        length = r["run"] if mode == "copy" else r.get("length", 10)
        ok, reaching = _starts(lo, hi, length, new_from)
        if not ok or (new_from is not None and not reaching):
            raise ValueError(f"number_write: no run of {length} inside {lo}–{hi} reaching {new_from}")
        # tracks may repeat when the range holds only one (1–10); copy runs are all different
        distinct = mode == "copy" and len(ok) >= blocks
        for _ in range(1000):
            starts = ctx.rng.sample(ok, blocks) if distinct else [ctx.rng.choice(ok) for _ in range(blocks)]
            if new_from is None or any(s in reaching for s in starts):
                break
        items, answers = [], []
        for s in starts:
            cells = list(range(s, s + length))
            if mode == "copy":
                items.append({"kind": "copy", "numbers": cells})
                answers += cells
            else:
                gaps = _gaps(ctx, length, r["gaps"])
                items.append({"kind": "track", "cells": cells, "gaps": gaps})
                answers += [cells[g] for g in gaps]
        return SheetContent(title=TITLES[mode], parent_tip=ctx.tip(f"{self.name}_{mode}"),
                            items=items, answer_key=answers)

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        mode, lo, hi = r.get("mode", "copy"), r["min"], r["max"]
        length = r["run"] if mode == "copy" else r.get("length", 10)
        kind = "copy" if mode == "copy" else "track"
        issues = []
        if len(sheet.items) != r.get("blocks", 3):
            issues.append(error(sheet, f"{len(sheet.items)} blocks; the part asks for {r.get('blocks', 3)}"))
        answers, numbers = [], []
        for i in sheet.items:
            if i["kind"] != kind:
                issues.append(error(sheet, f"a {i['kind']} block on a {mode} page"))
                continue
            cells = i["numbers"] if kind == "copy" else i["cells"]
            numbers += cells
            if len(cells) != length:
                issues.append(error(sheet, f"block has {len(cells)} numbers, expected {length}"))
            if cells != list(range(cells[0], cells[0] + len(cells))):
                issues.append(error(sheet, f"block {cells} is not counting up by ones"))
            if kind == "copy":
                answers += cells
                continue
            g = i["gaps"]
            if len(g) != r["gaps"] or g != sorted(set(g)):
                issues.append(error(sheet, f"track starting {cells[0]} has gaps {g}; expected {r['gaps']} distinct"))
            elif any(not 1 <= p < len(cells) for p in g):
                issues.append(error(sheet, f"gap position out of range (the first box must show): {g}"))
            elif any(b == a + 1 and c == b + 1 for a, b, c in zip(g, g[1:], g[2:])):
                issues.append(error(sheet, f"three empty boxes one after another: {g}"))
            else:
                answers += [cells[p] for p in g]
        issues += check_range(sheet, numbers, lo, hi)
        if sheet.answer_key != answers:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the numbers to write {answers}"))
        new_from = r.get("new_from")
        if new_from is not None and numbers and max(numbers) < new_from:
            issues.append(error(sheet, f"no block reaches the part's new numbers (from {new_from})"))
        return issues

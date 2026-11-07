"""MA 3A-A/B: "write the number that comes next": a number, an arrow and an empty box.

Rules (merged level → section → part):
- `min`, `max`: the part's number limit. `max` is the largest *answer*, so the numbers shown
  run from `min` to `max − 1`.
- `count`: numbers per sheet (default 10, shown as two columns).
- `order`: `run` (each column counts up by ones, an easier start) or `mixed` (shuffled).
- `new_from` (optional): at least half the answers are ≥ this, so the part's new numbers turn
  up on every page (fewer only if the part has fewer new numbers than that).
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules


def _need_new(rules: dict, count: int) -> int:
    """How many answers must be ≥ new_from on one sheet."""
    new_from = rules.get("new_from")
    if new_from is None:
        return 0
    new_pool = max(0, rules["max"] - max(new_from, rules["min"] + 1) + 1)
    return min(count // 2, new_pool)


def _runs(ctx: GenContext, lo: int, hi: int, count: int, new_from: int | None) -> list[int]:
    """Two columns, each a run of consecutive numbers; the second reaches the new numbers."""
    half = count // 2
    starts = list(range(lo, hi - half + 2))
    if len(starts) < 2:
        raise ValueError(f"next_number: {lo}–{hi} is too small for two runs of {half}")
    for _ in range(1000):
        a, b = sorted(ctx.rng.sample(starts, 2))
        if b - a < half:
            continue   # runs overlap
        if new_from is not None and b + 1 < new_from:
            continue   # second column's answers must all be new numbers
        return list(range(a, a + half)) + list(range(b, b + half))
    raise ValueError(f"next_number: can't place two runs of {half} in {lo}–{hi} reaching {new_from}")


@register("next_number")
class NextNumber(SheetType):
    template = "next_number.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        lo, hi, count = r["min"], r["max"] - 1, r.get("count", 10)   # hi = largest number shown
        new_from = r.get("new_from")
        if r.get("order", "mixed") == "run":
            shown = _runs(ctx, lo, hi, count, new_from)
        else:
            need = _need_new(r, count)
            new_pool = [n for n in range(lo, hi + 1) if new_from is not None and n + 1 >= new_from]
            old_pool = [n for n in range(lo, hi + 1) if n not in new_pool]
            take_old = min(count - need, len(old_pool))
            if need + take_old < count:
                need = count - take_old
            shown = ctx.rng.sample(new_pool, need) + ctx.rng.sample(old_pool, take_old)
            ctx.rng.shuffle(shown)
        items = [{"kind": "next", "n": n} for n in shown]
        return SheetContent(title="What comes next?", parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[n + 1 for n in shown])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        lo, top, count = r["min"], r["max"], r.get("count", 10)
        shown = [i["n"] for i in sheet.items]
        answers = [n + 1 for n in shown]
        issues = []
        if len(shown) != count:
            issues.append(error(sheet, f"{len(shown)} numbers; the part asks for {count}"))
        if len(set(shown)) != len(shown):
            issues.append(error(sheet, f"a number is shown twice: {shown}"))
        if any(n < lo or n + 1 > top for n in shown):
            issues.append(error(sheet, f"numbers {shown} go outside this part's range {lo}–{top}"))
        if sheet.answer_key != answers:
            issues.append(error(sheet, f"answer key {sheet.answer_key} isn't the next numbers {answers}"))
        if r.get("order", "mixed") == "run":
            half = count // 2
            for col in (shown[:half], shown[half:]):
                if col and col != list(range(col[0], col[0] + len(col))):
                    issues.append(error(sheet, f"column {col} should count up by ones"))
        need = _need_new(r, count)
        if sum(a >= r.get("new_from", 0) for a in answers) < need:
            issues.append(error(sheet, f"fewer than {need} answers reach the part's new numbers (from {r['new_from']})"))
        return issues

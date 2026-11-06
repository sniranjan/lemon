"""Long multiplication in columns (Owls math, 4.NBT.5): up to four digits times one digit, then two-digit
times two-digit.

Rules (merged level → section → part):
- `a`: [lo, hi] for the top number; `b`: [lo, hi] for the number it is multiplied by.
- `tens_only`: b is a whole number of tens (20, 30 … 90): the warm-up for the second line of a two-by-two.
- `layout`:
  - `expanded`: one-digit b; one line for each place of a (47 × 6 → 42 and 240), then the sum.
  - `carry`: the answer on one line, with carry boxes over the top number (every problem carries).
  - `partials`: two-digit b; line one = a × the ones digit, line two = a × the tens (ends in 0), then the sum;
    at least one line carries.
- `zero_shown` (partials): the 0 that ends line two is printed for the child.
- `problems`: problems a page (4 → 2 × 2; 6 → 2 a row in 3 rows). `title`: the sheet title.

Each item stores whole numbers only (a, b, the partial lines, the columns that get a carry box), so
verify recomputes everything. Every line is right-aligned in `cols` digit columns (the widest answer the
part allows). Partial lines get exactly one box per digit; the answer line gets `cols` boxes.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

LAYOUTS = ("expanded", "carry", "partials")
MAX_TRIES = 20000


def digit(n: int, col: int) -> int:
    return n // 10 ** col % 10


def width(n: int) -> int:
    return len(str(n))


def partials(layout: str, a: int, b: int) -> list[int]:
    """The lines a child writes before the answer (none for `carry`)."""
    if layout == "expanded":
        return [digit(a, k) * 10 ** k * b for k in range(width(a))]
    if layout == "partials":
        return [a * digit(b, 0), a * digit(b, 1) * 10]
    return []


def carries(a: int, m: int) -> list[int]:
    """Carry out of each column of a when a is multiplied by the one digit m (right to left)."""
    out, carry = [], 0
    for k in range(width(a)):
        carry = (digit(a, k) * m + carry) // 10
        out.append(carry)
    return out


def carry_cols(layout: str, a: int) -> list[int]:
    """Columns (0 = ones) that get a carry box: over each digit of a except the ones (carry, partials)."""
    return [] if layout == "expanded" else list(range(1, width(a)))


def columns(rules: dict) -> int:
    return width(rules["a"][1] * rules["b"][1])


def multiplier(layout: str, b: int) -> int:
    """The one digit a carry runs on: b itself, or b's tens digit when b is a whole number of tens."""
    return b if b < 10 else b // 10


def problem_ok(r: dict, a: int, b: int) -> str | None:
    lo, hi = r["a"]
    if not lo <= a <= hi:
        return f"top number {a} is outside {lo}–{hi}"
    lo, hi = r["b"]
    if not lo <= b <= hi:
        return f"{b} is outside {lo}–{hi}"
    layout = r["layout"]
    if r.get("tens_only") and b % 10:
        return f"{b} isn't a whole number of tens"
    if layout == "expanded":
        if b > 9:
            return "the expanded layout multiplies by one digit"
        if 0 in [digit(a, k) for k in range(width(a))]:
            return f"{a} has a 0 digit, so one of its lines would be 0"
    if layout == "partials":
        if not 10 <= b <= 99 or digit(b, 0) == 0:
            return f"{b}: a two-by-two needs a two-digit number without a 0 in the ones"
        if not any(c for d in (digit(b, 0), digit(b, 1)) for c in carries(a, d)[:-1]):
            return f"{a} × {b} has no carry on either line"
    if layout == "carry":
        if b > 9 and not r.get("tens_only"):
            return "the carry layout multiplies by one digit (or a whole number of tens)"
        if not any(carries(a, multiplier(layout, b))[:-1]):
            return f"{a} × {b} has no carry"
    if width(a * b) > columns(r):
        return f"{a} × {b} doesn't fit {columns(r)} columns"
    return None


@register("long_multiplication")
class LongMultiplication(SheetType):
    template = "long_multiplication.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        layout = r["layout"]
        if layout not in LAYOUTS:
            raise ValueError(f"long_multiplication: unknown layout {layout!r} (use one of {', '.join(LAYOUTS)})")
        cols, items, seen = columns(r), [], set()
        for _ in range(r.get("problems", 4)):
            for _ in range(MAX_TRIES):
                a = rng.randint(*r["a"])
                b = rng.randrange(r["b"][0], r["b"][1] + 1, 10) if r.get("tens_only") else rng.randint(*r["b"])
                if (a, b) not in seen and problem_ok(r, a, b) is None:
                    break
            else:
                raise ValueError(f"long_multiplication: can't find a problem with these rules: {r}")
            seen.add((a, b))
            items.append({"kind": "times", "layout": layout, "a": a, "b": b, "cols": cols,
                          "partials": partials(layout, a, b), "carry_cols": carry_cols(layout, a),
                          "zero_shown": bool(r.get("zero_shown")) and layout == "partials"})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer_text(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        n = r.get("problems", 4)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} problems; the part asks for {n}"))
        seen = set()
        for i in sheet.items:
            a, b, label = i["a"], i["b"], f"{i['a']} × {i['b']}"
            if i["layout"] != r["layout"]:
                issues.append(error(sheet, f"{label}: layout {i['layout']} on a {r['layout']} page"))
            why = problem_ok(r, a, b)
            if why:
                issues.append(error(sheet, f"{label}: {why}"))
            if i["partials"] != partials(r["layout"], a, b):
                issues.append(error(sheet, f"{label}: lines {i['partials']} should be {partials(r['layout'], a, b)}"))
            elif sum(i["partials"] or [a * b]) != a * b:
                issues.append(error(sheet, f"{label}: the lines don't add up to {a * b}"))
            if i["cols"] != columns(r) or any(width(x) > i["cols"] for x in [a, b, a * b, *i["partials"]]):
                issues.append(error(sheet, f"{label}: digits must line up in {columns(r)} columns"))
            if i["carry_cols"] != carry_cols(r["layout"], a):
                issues.append(error(sheet, f"{label}: carry boxes belong over the digits of {a} after the ones"))
            if i["zero_shown"] != (bool(r.get("zero_shown")) and r["layout"] == "partials"):
                issues.append(error(sheet, f"{label}: the printed 0 on line two must follow the part's zero_shown"))
            if (a, b) in seen:
                issues.append(error(sheet, f"{label} appears twice"))
            seen.add((a, b))
        expected = [answer_text(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues


def answer_text(item: dict) -> str:
    total = item["a"] * item["b"]
    lines = item["partials"]
    return f"{total} ({' + '.join(map(str, lines))})" if lines else str(total)

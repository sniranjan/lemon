"""Scientific notation (Lions math, 8.EE.3–4): very big and very small numbers.

A number in scientific notation is stored as `coef` (a decimal string, 1 ≤ coef < 10, at most
`digits[1]` significant digits) and `exp` (a whole number). Tasks (rules `tasks`, cycled):
- `to_sci`: a number in standard form (3,200,000,000 or 0.000405); the child writes coef × 10^exp.
- `to_standard`: coef × 10^exp; the child writes the number out.
- `multiply`, `divide`: two numbers in scientific notation; the answer in scientific notation
  (front numbers multiplied or divided, powers added or taken away, then tidied to 1 ≤ coef < 10).
- `times_bigger`: how many times bigger the first number is than the second (an exact quotient).
`exponents`: the range for every power of ten on the page (and the answer's). Standard-form
numbers use powers 2 or more away from 0 so they look big or small. Decimal arithmetic is exact.
"""

from __future__ import annotations

from decimal import Decimal

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._algebra import MINUS
from ._common import error

PROBLEMS = 8
OPS = ("multiply", "divide", "times_bigger")


def value(coef: str, exp: int) -> Decimal:
    return Decimal(coef).scaleb(exp)


def normal(v: Decimal) -> tuple[str, int]:
    """A positive Decimal as (coef, exp) with 1 ≤ coef < 10, no trailing zeros."""
    exp = v.adjusted()
    coef = v.scaleb(-exp).normalize()
    return format(coef, "f"), exp


def sig_digits(coef: str) -> int:
    return len(coef.replace(".", "").lstrip("0"))


def standard(coef: str, exp: int) -> str:
    """The number written out: 3,200,000,000 or 0.000405."""
    v = value(coef, exp).normalize()
    if v == v.to_integral_value():
        return f"{int(v):,}"
    return format(v, "f")


def sci(coef: str, exp: int) -> str:
    return f"{coef} × 10^{str(exp).replace('-', MINUS)}"


def result(i: dict) -> tuple[str, int]:
    a = value(i["coef"], i["exp"])
    if i["task"] == "to_sci" or i["task"] == "to_standard":
        return i["coef"], i["exp"]
    b = value(i["coef2"], i["exp2"])
    return normal(a * b if i["task"] == "multiply" else a / b)


def answer(i: dict) -> str:
    if i["task"] == "to_standard":
        return standard(i["coef"], i["exp"])
    return sci(*result(i))


def _coef(rng, digits: tuple[int, int]) -> str:
    n = rng.randint(*digits)
    first = rng.randint(1, 9)
    rest = "".join(str(rng.randint(0, 9)) for _ in range(n - 1)).rstrip("0")
    return f"{first}.{rest}" if rest else str(first)


def _item(ctx: GenContext, task: str) -> dict:
    r, rng = ctx.rules, ctx.rng
    elo, ehi = r["exponents"]
    digits = tuple(r["digits"])
    if task in ("to_sci", "to_standard"):
        while True:
            exp = rng.randint(elo, ehi)
            if abs(exp) >= 2:
                coef = _coef(rng, digits)
                item = {"task": task, "coef": coef, "exp": exp}
                return {**item, "standard": standard(coef, exp)} if task == "to_sci" else item
    for _ in range(1000):
        if task == "multiply":
            c1, c2 = _coef(rng, (1, 2)), _coef(rng, (1, 2))
            e1, e2 = rng.randint(elo, ehi), rng.randint(elo, ehi)
        elif task == "divide":   # build from the answer so the quotient is exact
            q, e2 = _coef(rng, (1, 2)), rng.randint(elo, ehi)
            c2 = _coef(rng, (1, 1))
            c1, e1 = normal(value(q, rng.randint(elo, ehi)) * value(c2, e2))
        else:   # times_bigger: whole-number quotient, the first number much bigger
            k, c2 = rng.randint(2, 9), rng.randint(1, 4)
            e2 = rng.randint(2, ehi - 2)
            c1, e1 = normal(value(str(c2), e2) * k * Decimal(10) ** rng.randint(2, 6))
            c2 = str(c2)
        item = {"task": task, "coef": c1, "exp": e1, "coef2": c2, "exp2": e2}
        coef, exp = result(item)
        if 0 not in (e1, e2) and (all(elo <= e <= ehi for e in (e1, e2, exp)) and sig_digits(c1) <= digits[1]
                and sig_digits(coef) <= digits[1]):
            return item
    raise ValueError(f"sci_notation: no {task} problem fits {r['exponents']}")


@register("sci_notation")
class SciNotation(SheetType):
    template = "sci_notation.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        n = r.get("problems", PROBLEMS)
        items: list[dict] = []
        for k in range(n):
            task = r["tasks"][k % len(r["tasks"])]
            for _ in range(200):
                item = _item(ctx, task)
                if all(item != {kk: v for kk, v in i.items() if kk != "n"} for i in items):
                    break
            items.append({"n": k + 1, **item})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        n = r.get("problems", PROBLEMS)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} problems; this part has {n}"))
        if [i["task"] for i in sheet.items] != [r["tasks"][k % len(r["tasks"])] for k in range(len(sheet.items))]:
            issues.append(error(sheet, "tasks don't follow the part's list"))
        elo, ehi = r["exponents"]
        for i in sheet.items:
            label = f"problem {i.get('n')} ({i['task']})"
            pairs = [(i["coef"], i["exp"])] + ([(i["coef2"], i["exp2"])] if i["task"] in OPS else [])
            for c, e in pairs:
                if not (Decimal(1) <= Decimal(c) < 10 and normal(Decimal(c))[0] == c):
                    issues.append(error(sheet, f"{label}: {c} isn't a tidy number from 1 to just under 10"))
                if not elo <= e <= ehi or (e == 0 and i["task"] in OPS):
                    issues.append(error(sheet, f"{label}: power {e} is outside {elo}–{ehi}"))
            if i["task"] == "to_sci" and i.get("standard") != standard(i["coef"], i["exp"]):
                issues.append(error(sheet, f"{label}: printed number {i.get('standard')} isn't {sci(i['coef'], i['exp'])}"))
            if sig_digits(i["coef"]) > r["digits"][1]:
                issues.append(error(sheet, f"{label}: {i['coef']} has too many digits"))
            if i["task"] in ("to_sci", "to_standard") and abs(i["exp"]) < 2:
                issues.append(error(sheet, f"{label}: power {i['exp']} doesn't make a big or small number"))
            coef, exp = result(i)
            if not (Decimal(1) <= Decimal(coef) < 10 and elo <= exp <= ehi):
                issues.append(error(sheet, f"{label}: answer {sci(coef, exp)} isn't tidy or is out of range"))
            if i["task"] in OPS:
                a, b = value(i["coef"], i["exp"]), value(i["coef2"], i["exp2"])
                exact = a * b if i["task"] == "multiply" else a / b
                if value(coef, exp) != exact:
                    issues.append(error(sheet, f"{label}: the answer isn't exact"))
                if i["task"] == "times_bigger" and (exact != exact.to_integral_value() or exact < 100):
                    issues.append(error(sheet, f"{label}: {exact} should be a whole number, 100 or more"))
        expected = [answer(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues

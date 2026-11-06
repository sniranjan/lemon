"""Dividing fractions (Pandas math, 6.NS.1): "how many 1/8s fit in 3/4?", then fraction ÷ fraction.

Rules (merged level → section → part):
- `layout`: `model` (each problem has a fraction bar to count on; divisors are unit fractions and
  every answer is whole) or `facts` (rows of problems, answers in simplest form).
- `problems`: problems a page (default 5 for `model`, 10 for `facts`).
- `dividend`, `divisor`: kinds the problems cycle through: `whole` (3), `proper` (3/4),
  `mixed` (2 1/2), `unit` (1/5, divisor only).
- `max_den`: largest denominator in a problem. `max_whole`: largest whole number / whole part.
- `max_answer_den` (facts): the answer's denominator stays at or below this (default 12).
- `max_answer` (facts): the answer stays at or below this (default 20).
- `title`: the sheet title.

Items store the numbers as strings ("3/4", "2 1/2", "3"); verify recomputes every answer with
Fraction and, for a model, the bar (how many bars, pieces per bar, shaded pieces).
Answers in the key are in simplest form, mixed numbers above 1 ("2 1/3").
"""

from __future__ import annotations

from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from ._rational import fmt, parse

DENS = (2, 3, 4, 5, 6, 8, 10, 12)
MAX_TRIES = 5000


def kind_of(x: Fraction) -> str:
    if x.denominator == 1:
        return "whole"
    if x < 1:
        return "unit" if x.numerator == 1 else "proper"
    return "mixed"


def _pick(rng, kind: str, max_den: int, max_whole: int) -> Fraction:
    dens = [d for d in DENS if d <= max_den]
    if kind == "whole":
        return Fraction(rng.randint(1, max_whole))
    d = rng.choice(dens)
    if kind == "unit":
        return Fraction(1, d)
    n = rng.randint(1, d - 1)
    x = Fraction(n, d)
    if kind == "proper":
        return x
    return rng.randint(1, max_whole) + x


def model_bar(a: Fraction, b: Fraction) -> dict:
    """Whole bars, each cut into pieces the size of b; the dividend's pieces are shaded."""
    pieces = b.denominator
    shaded = a * pieces
    return {"bars": -(-a.numerator // a.denominator), "pieces": pieces, "shaded": int(shaded)}


def _model_ok(a: Fraction, b: Fraction) -> bool:
    return b.numerator == 1 and (a / b).denominator == 1 and a / b >= 2 and (a * b.denominator).denominator == 1


@register("fraction_divide")
class FractionDivide(SheetType):
    template = "fraction_divide.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        layout = r["layout"]
        count = r.get("problems", 5 if layout == "model" else 10)
        max_den, max_whole = r["max_den"], r["max_whole"]
        items, seen = [], set()
        for n in range(1, count + 1):
            ka = r["dividend"][(n - 1) % len(r["dividend"])]
            kb = r["divisor"][(n - 1) % len(r["divisor"])]
            for _ in range(MAX_TRIES):
                a = _pick(ctx.rng, ka, max_den, max_whole)
                b = _pick(ctx.rng, kb, max_den, max_whole)
                if (a, b) in seen or kind_of(a) != ka or kind_of(b) != kb:
                    continue
                if self._fits(a, b, r):
                    break
            else:
                raise ValueError(f"fraction_divide: no {ka} ÷ {kb} problem fits the rules {r}")
            seen.add((a, b))
            item = {"kind": "divide", "n": n, "a": fmt(a), "b": fmt(b), "answer": fmt(a / b)}
            if layout == "model":
                item["bar"] = model_bar(a, b)
            items.append(item)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["answer"] for i in items])

    @staticmethod
    def _fits(a: Fraction, b: Fraction, r: dict) -> bool:
        if r["layout"] == "model":
            return _model_ok(a, b) and model_bar(a, b)["bars"] * b.denominator <= r.get("max_pieces", 24)
        q = a / b
        return q != 1 and q.denominator <= r.get("max_answer_den", 12) and q <= r.get("max_answer", 20)

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        layout = r["layout"]
        count = r.get("problems", 5 if layout == "model" else 10)
        issues: list[Issue] = []
        items = sheet.items
        if len(items) != count:
            issues.append(error(sheet, f"{len(items)} problems; this part has {count}"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
        pairs = set()
        for idx, i in enumerate(items):
            label = f"problem {i.get('n')} ({i.get('a')} ÷ {i.get('b')})"
            try:
                a, b = parse(i["a"]), parse(i["b"])
            except (KeyError, ValueError, ZeroDivisionError):
                issues.append(error(sheet, f"{label}: numbers aren't readable"))
                continue
            if fmt(a) != i["a"] or fmt(b) != i["b"]:
                issues.append(error(sheet, f"{label}: numbers aren't written in simplest form"))
            if b == 0 or a <= 0:
                issues.append(error(sheet, f"{label}: numbers must be above 0"))
                continue
            if i.get("answer") != fmt(a / b):
                issues.append(error(sheet, f"{label}: answer {i.get('answer')} is wrong, it's {fmt(a / b)}"))
            ka = r["dividend"][idx % len(r["dividend"])]
            kb = r["divisor"][idx % len(r["divisor"])]
            if kind_of(a) != ka or kind_of(b) != kb:
                issues.append(error(sheet, f"{label}: should be {ka} ÷ {kb}"))
            if max(a.denominator, b.denominator) > r["max_den"] or max(int(a), int(b)) > r["max_whole"]:
                issues.append(error(sheet, f"{label}: numbers are bigger than this part allows"))
            if (a, b) in pairs:
                issues.append(error(sheet, f"{label}: the same problem is on the page twice"))
            pairs.add((a, b))
            if not self._fits(a, b, r):
                issues.append(error(sheet, f"{label}: doesn't fit this part's rules (answer {fmt(a / b)})"))
            if layout == "model" and i.get("bar") != model_bar(a, b):
                issues.append(error(sheet, f"{label}: the bar should be {model_bar(a, b)}"))
            if layout != "model" and "bar" in i:
                issues.append(error(sheet, f"{label}: only model pages have bars"))
        if sheet.answer_key != [i.get("answer") for i in items]:
            issues.append(error(sheet, "answer key doesn't match the problems"))
        return issues

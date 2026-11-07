"""Multiplying and dividing decimals (Otters math, 5.NBT.2 and 5.NBT.7): one fact a line.

Each item is `a × b = ☐` or `a ÷ b = ☐` with exact decimals. `kinds` (rules) picks what a page
mixes, half and half:
- `times_power` / `divide_power`: by 10, 100 or 1000; numbers to thousandths.
- `times_whole` / `divide_whole`: a decimal (tenths or hundredths, under 20) and a whole number 2–9;
  sharing answers come out exactly, to hundredths.
- `times_decimal` / `divide_decimal`: both numbers decimals (tenths, or a tenth and hundredths),
  answers to hundredths; dividing answers are whole numbers 2–12 or tenths.
Rules: `kinds`, `problems` (default 10), `title`. Answers are canonical decimals ("340", "4.56").
Verify recomputes every answer with Decimal and checks each number fits its kind.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules
from ._exact import dec, dec_str, from_hundredths, places

PROBLEMS = 10
MAX_TRIES = 5000
POWERS = (10, 100, 1000)
KINDS = ("times_power", "divide_power", "times_whole", "divide_whole", "times_decimal", "divide_decimal")


def answer(item: dict) -> Decimal:
    a, b = dec(item["a"]), dec(item["b"])
    if item["op"] == "×":
        return a * b
    q = Fraction(a) / Fraction(b)   # exact; a decimal only if the bottom is made of 2s and 5s
    d = q.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    if d != 1:
        raise ValueError(f"{item['a']} ÷ {item['b']} doesn't come out exactly")
    with localcontext() as c:
        c.prec = 60
        return Decimal(q.numerator) / Decimal(q.denominator)   # exact: a terminating decimal


def kind_ok(item: dict) -> str | None:
    k, a, b = item["kind"], dec(item["a"]), dec(item["b"])
    if k not in KINDS:
        return f"unknown kind {k!r}"
    if item["op"] != ("×" if k.startswith("times") else "÷"):
        return f"sign {item['op']} doesn't fit {k}"
    ans = answer(item)
    if not 0 < ans:
        return "answer isn't more than 0"
    if k.endswith("power"):
        if b not in POWERS:
            return f"{item['b']} isn't 10, 100 or 1000"
        if places(item["a"]) > 3 or places(dec_str(ans)) > 3 or ans > 99999:
            return "numbers here go to thousandths and stay under 100000"
        if places(item["a"]) == 0 and a % 10 == 0:
            return f"{item['a']} ends in 0: pick a number that shows the digits moving"
    elif k.endswith("whole"):
        if b != b.to_integral_value() or not 2 <= b <= 9:
            return f"{item['b']} isn't a whole number 2–9"
        x = a if k.startswith("times") else ans
        if not 1 <= places(dec_str(x)) <= 2 or not 0 < x < 20:
            return f"{dec_str(x)} should be a decimal under 20, in tenths or hundredths"
        if places(dec_str(ans)) > 2 or places(item["a"]) > 2:
            return "answers here go to hundredths"
    else:
        if places(item["b"]) < 1 or places(item["a"]) > 2 or places(item["b"]) > 2:
            return "both numbers here are decimals to hundredths"
        if places(dec_str(ans)) > 2:
            return f"answer {dec_str(ans)} goes past hundredths"
        if k == "times_decimal" and places(item["a"]) + places(item["b"]) > 2:
            return "times facts here are tenths times tenths"
        if k == "divide_decimal" and (places(dec_str(ans)) > 1 or ans > 12 or ans < Decimal("0.2")):
            return f"answer {dec_str(ans)} should be a whole number to 12 or tenths"
    return None


def _make(rng, kind: str) -> dict:
    if kind == "times_power":
        p = rng.choice([1, 2, 3])
        a = from_hundredths(rng.randint(1, 9999), p)
        return {"op": "×", "a": dec_str(a), "b": str(rng.choice(POWERS))}
    if kind == "divide_power":
        p = rng.choice([0, 1, 1, 2])
        a = from_hundredths(rng.randint(11, 9999), p)
        return {"op": "÷", "a": dec_str(a), "b": str(rng.choice(POWERS))}
    if kind == "times_whole":
        a = from_hundredths(rng.randint(11, 1999), rng.choice([1, 2]))
        return {"op": "×", "a": dec_str(a), "b": str(rng.randint(2, 9))}
    if kind == "divide_whole":
        q = from_hundredths(rng.randint(11, 1999), rng.choice([1, 2]))
        w = rng.randint(2, 9)
        return {"op": "÷", "a": dec_str(q * w), "b": str(w)}
    if kind == "times_decimal":
        return {"op": "×", "a": dec_str(from_hundredths(rng.randint(2, 99), 1)),
                "b": dec_str(from_hundredths(rng.randint(2, 9), 1))}
    # divide_decimal
    d = from_hundredths(rng.randint(2, 15), 1)
    q = Decimal(rng.randint(2, 12)) if rng.random() < 0.6 else from_hundredths(rng.randint(2, 99), 1)
    return {"op": "÷", "a": dec_str(q * d), "b": dec_str(d)}


@register("decimal_ops")
class DecimalOps(SheetType):
    template = "decimal_ops.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        n = r.get("problems", PROBLEMS)
        kinds = [r["kinds"][k % len(r["kinds"])] for k in range(n)]
        rng.shuffle(kinds)
        items, seen = [], set()
        for kind in kinds:
            for _ in range(MAX_TRIES):
                item = {"kind": kind, **_make(rng, kind)}
                key = (item["op"], item["a"], item["b"])
                try:
                    ok = kind_ok(item) is None
                except (ValueError, ArithmeticError):
                    ok = False
                if ok and key not in seen:
                    break
            else:
                raise ValueError(f"decimal_ops: can't find a {kind} fact")
            seen.add(key)
            items.append(item)
        for k, item in enumerate(items, 1):
            item["n"] = k
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[dec_str(answer(i)) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        issues: list[Issue] = []
        n = r.get("problems", PROBLEMS)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} facts; the part asks for {n}"))
        if [i.get("n") for i in sheet.items] != list(range(1, len(sheet.items) + 1)):
            issues.append(error(sheet, "facts are not numbered 1, 2, 3… in order"))
        seen = set()
        for i in sheet.items:
            try:
                why = kind_ok(i)
            except (ValueError, ArithmeticError) as e:
                why = str(e)
            if i["kind"] not in r["kinds"]:
                why = f"{i['kind']} isn't used in this part"
            if why:
                issues.append(error(sheet, f"{i['a']} {i['op']} {i['b']}: {why}"))
            key = (i["op"], i["a"], i["b"])
            if key in seen:
                issues.append(error(sheet, f"{i['a']} {i['op']} {i['b']} appears twice"))
            seen.add(key)
        if len(sheet.items) >= len(r["kinds"]) and {i["kind"] for i in sheet.items} != set(r["kinds"]):
            issues.append(error(sheet, f"a page needs each of {r['kinds']}"))
        try:
            expected = [dec_str(answer(i)) for i in sheet.items]
        except (ValueError, ArithmeticError) as e:
            return issues + [error(sheet, f"can't work out the answers: {e}")]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the facts {expected}"))
        return issues

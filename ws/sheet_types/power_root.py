"""Powers, exponent rules and roots (Lions math, 8.EE.1–2, 8.NS.2).

`problems` items a page (default 8), tasks cycling through the part's `tasks` list:
- `power`: base^exp = box (exp 2–5, |value| ≤ `max_value`; negative bases in brackets if `negative_bases`).
- `square_root`: √(k²) = box, k in `squares`. `cube_root`: ∛(k³) = box, k in `cubes` (−k too if `negative_bases`).
- `product` b^p · b^q, `quotient` b^p ÷ b^q, `power_of_power` (b^p)^q: write as one power, b^box.
  Exponents in `exponents`; the base is a number in `bases` or the page's letter.
- `zero_negative`: b^0 or b^−e (e 1–3) as a number: 2^−3 = 1/8.
- `rule_value`: b^p · b^q with a small result, worked out as a number (2^5 · 2^−2 = 8).
- `solve_square`: x² = k² → x = k or x = −k. `solve_cube`: x³ = k³ → x = k.
- `between`: √n (n not a square) lies between two whole numbers.
Every item stores only numbers; the answer is recomputed exactly (Fraction) by verify.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._algebra import is_square, show
from ._common import error

PROBLEMS = 8
RULES = ("product", "quotient", "power_of_power")
BAD_LETTERS = {"a", "m", "r"}   # "2a", "m8", "r5" would read as internal codes


def result_exp(i: dict) -> int:
    p, e2 = i["exp"], i["exp2"]
    return {"product": p + e2, "quotient": p - e2, "power_of_power": p * e2, "rule_value": p + e2}[i["task"]]


def answer(i: dict) -> str:
    t = i["task"]
    if t == "power" or t == "zero_negative":
        return show(Fraction(i["base"]) ** i["exp"])
    if t == "square_root":
        return str(i["root"])
    if t == "cube_root":
        return show(i["root"])
    if t in RULES:
        base = i["base"] if isinstance(i["base"], str) else show(i["base"])
        return f"{base}^{show(result_exp(i))}"
    if t == "rule_value":
        return show(Fraction(i["base"]) ** result_exp(i))
    if t == "solve_square":
        return f"{i['letter']} = {i['root']} or {i['letter']} = {show(-i['root'])}"
    if t == "solve_cube":
        return f"{i['letter']} = {show(i['root'])}"
    if t == "between":
        lo = isqrt(i["value"])
        return f"{lo} and {lo + 1}"
    raise ValueError(f"unknown task {t!r}")


def _item(ctx: GenContext, task: str, letter: str) -> dict:
    r, rng = ctx.rules, ctx.rng
    blo, bhi = r["bases"]
    neg = r.get("negative_bases", False)
    item: dict = {"task": task}
    if task == "power":
        while True:
            b, e = rng.randint(blo, bhi), rng.randint(2, 5)
            if neg and rng.random() < 0.3:
                b = -b
            if abs(b) ** e <= r["max_value"]:
                item.update(base=b, exp=e)
                return item
    if task == "square_root":
        k = rng.randint(*r["squares"])
        item.update(root=k, value=k * k)
        return item
    if task == "cube_root":
        k = rng.randint(*r["cubes"])
        if neg and rng.random() < 0.4:
            k = -k
        item.update(root=k, value=k ** 3)
        return item
    if task in RULES:
        elo, ehi = r["exponents"]
        while True:
            p, e2 = rng.randint(elo, ehi), rng.randint(elo, ehi)
            if task == "power_of_power":
                e2 = rng.randint(2, 4)
            if p in (0, 1) or e2 in (0, 1):
                continue
            item.update(base=letter if rng.random() < 0.35 else rng.randint(blo, bhi), exp=p, exp2=e2)
            if elo <= result_exp(item) <= ehi * 2 and (task != "quotient" or p != e2):
                return item
    if task == "zero_negative":
        b = rng.randint(blo, min(bhi, 10))
        e = 0 if rng.random() < 0.25 else -rng.randint(1, 3)
        while b ** -e > 256:
            e += 1
        item.update(base=b, exp=e)
        return item
    if task == "rule_value":
        while True:
            b = rng.randint(2, 5)
            p, e2 = rng.randint(2, 7), -rng.randint(1, 6)
            if rng.random() < 0.5:
                p, e2 = e2, p
            item.update(base=b, exp=p, exp2=e2)
            res = result_exp(item)
            if -2 <= res <= 4 and b ** abs(res) <= 200:
                return item
    if task == "solve_square":
        k = rng.randint(max(2, r["squares"][0]), r["squares"][1])
        item.update(letter=letter, root=k, value=k * k)
        return item
    if task == "solve_cube":
        k = rng.randint(max(2, r["cubes"][0]), r["cubes"][1])
        if neg and rng.random() < 0.4:
            k = -k
        item.update(letter=letter, root=k, value=k ** 3)
        return item
    if task == "between":
        while True:
            n = rng.randint(5, r["squares"][1] ** 2)
            if not is_square(n):
                item.update(value=n)
                return item
    raise ValueError(f"power_root: unknown task {task!r}")


def _key(i: dict) -> tuple:
    return tuple(sorted((k, str(v)) for k, v in i.items() if k != "n"))


@register("power_root")
class PowerRoot(SheetType):
    template = "power_root.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        n = r.get("problems", PROBLEMS)
        letter = ctx.rng.choice(r["letters"])
        items, seen = [], set()
        for k in range(n):
            task = r["tasks"][k % len(r["tasks"])]
            for _ in range(200):
                item = _item(ctx, task, letter)
                if _key(item) not in seen:
                    break
            seen.add(_key(item))
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
        want = [r["tasks"][k % len(r["tasks"])] for k in range(len(sheet.items))]
        if [i["task"] for i in sheet.items] != want:
            issues.append(error(sheet, f"tasks {[i['task'] for i in sheet.items]} don't follow the part's list"))
        if len({_key(i) for i in sheet.items}) != len(sheet.items):
            issues.append(error(sheet, "the same problem is on the page twice"))
        blo, bhi = r["bases"]
        neg = r.get("negative_bases", False)
        for i in sheet.items:
            t, label = i["task"], f"problem {i.get('n')} ({i['task']})"
            base = i.get("base")
            if isinstance(base, str):
                if t not in RULES or base in BAD_LETTERS or len(base) != 1:
                    issues.append(error(sheet, f"{label}: letter base {base!r} isn't allowed here"))
            elif base is not None and not (blo <= abs(base) <= bhi and (base > 0 or neg)):
                issues.append(error(sheet, f"{label}: base {base} is outside {blo}–{bhi}"))
            if t == "power" and not (2 <= i["exp"] <= 5 and abs(base) ** i["exp"] <= r["max_value"]):
                issues.append(error(sheet, f"{label}: {base}^{i['exp']} is too big to work out by hand"))
            if t in ("square_root", "solve_square") and not (
                    i["value"] == i["root"] ** 2 and r["squares"][0] <= i["root"] <= r["squares"][1]):
                issues.append(error(sheet, f"{label}: {i['value']} isn't the square of {i['root']} in range"))
            if t in ("cube_root", "solve_cube") and not (
                    i["value"] == i["root"] ** 3 and r["cubes"][0] <= abs(i["root"]) <= r["cubes"][1]
                    and (i["root"] > 0 or neg)):
                issues.append(error(sheet, f"{label}: {i['value']} isn't the cube of {i['root']} in range"))
            if t in RULES:
                elo, ehi = r["exponents"]
                if not (elo <= i["exp"] <= ehi and elo <= i["exp2"] <= ehi):
                    issues.append(error(sheet, f"{label}: exponents outside {elo}–{ehi}"))
            if t == "zero_negative" and not (-3 <= i["exp"] <= 0 and base ** -i["exp"] <= 256):
                issues.append(error(sheet, f"{label}: {base}^{i['exp']} should be a zero or small negative power"))
            if t == "between" and (is_square(i["value"]) or i["value"] > r["squares"][1] ** 2):
                issues.append(error(sheet, f"{label}: √{i['value']} should be a non-square up to {r['squares'][1] ** 2}"))
            if "letter" in i and i["letter"] in BAD_LETTERS:
                issues.append(error(sheet, f"{label}: letter {i['letter']!r} isn't allowed"))
        expected = [answer(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues

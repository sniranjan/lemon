"""Multi-step linear equations in one letter (Lions math, 8.EE.7a–b).

`problems` equations a page (default 6), each with room to work and an answer line. Each is
built backwards from its solution, so it always has the stated answer. Forms (rules `forms`,
cycled): `two_step` 4x − 7 = 21 · `like_terms` 3x + 5x − 4 = 28 · `both_sides` 7x + 3 = 2x + 28 ·
`distribute` 3(x − 4) = 15 · `distribute_like` 2(x + 5) + 3x = 35 · `distribute_right`
4(x − 2) = x + 13 · `distribute_both` 3(x + 2) = 2(x − 1) + 12 · `fraction_coef` ½x + 3 = x − 1.
Rules: `solutions` (range of whole-number answers), `max_number` (largest number printed),
`fraction_solutions` (that many answers per page are fractions like 5/2, from forms that allow it),
`special` (2: one equation with no solution and one true for every number; 8.EE.7a).
Equations are stored as two lists of terms (see _algebra.py) plus the printed tokens; verify
re-prints and re-solves them exactly.
"""

from __future__ import annotations

from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent
from ._algebra import equation_tokens, fstr, numbers_in, show, solve
from ._common import error, nonzero_draw, page_rules

PROBLEMS = 6
BAD_LETTERS = {"a", "m", "r"}
FRACTION_FORMS = {"both_sides", "distribute", "distribute_right", "distribute_both"}


def X(c) -> dict:
    return {"c": fstr(c), "v": "x"}


def N(c) -> dict:
    return {"c": fstr(c), "v": ""}


def B(k, inner: list[dict]) -> dict:
    return {"k": fstr(k), "in": inner}


def answer(i: dict) -> str:
    s = solve(i["left"], i["right"])
    if s == "none":
        return "no solution"
    if s == "all":
        return "every number"
    return f"{i['letter']} = {show(s)}"


def _inner(rng) -> list[dict]:
    return [X(1), N(nonzero_draw(rng, -9, 9))]


def _build(rng, form: str, x: Fraction, special: str | None = None) -> tuple[list, list] | None:
    """One equation of `form` whose solution is x (or with no / every solution)."""
    if special == "none" or special == "all":
        k, b = rng.randint(2, 6), nonzero_draw(rng, -8, 8)
        shift = 0 if special == "all" else nonzero_draw(rng, -5, 5)
        if rng.random() < 0.5:
            return [B(k, _inner_with(b))], [X(k), N(k * b + shift)]
        p = rng.randint(2, 6)
        q = rng.randint(1, 5)
        return [X(p), N(b), X(q)], [X(p + q), N(b + shift)]
    if form == "two_step":
        p, c = nonzero_draw(rng, -9, 9), nonzero_draw(rng, -20, 20)
        if abs(p) == 1:
            return None
        return [X(p), N(c)], [N(p * x + c)]
    if form == "like_terms":
        p, s, c = rng.randint(2, 9), nonzero_draw(rng, -6, 9), nonzero_draw(rng, -20, 20)
        if p + s in (0, 1):
            return None
        left = [X(p), N(c), X(s)] if rng.random() < 0.5 else [X(p), X(s), N(c)]
        return left, [N((p + s) * x + c)]
    if form == "both_sides":
        p, s, c = nonzero_draw(rng, -6, 9), nonzero_draw(rng, -6, 9), nonzero_draw(rng, -20, 20)
        if p == s or (x.denominator > 1 and (p - s) % x.denominator):
            return None
        return [X(p), N(c)], [X(s), N((p - s) * x + c)]
    if form == "distribute":
        k, b = nonzero_draw(rng, -6, 7), nonzero_draw(rng, -9, 9)
        if abs(k) == 1:
            return None
        return [B(k, _inner_with(b))], [N(k * (x + b))]
    if form == "distribute_like":
        k, b, s = rng.randint(2, 7), nonzero_draw(rng, -9, 9), nonzero_draw(rng, -5, 6)
        if k + s == 0:
            return None
        return [B(k, _inner_with(b)), X(s)], [N(k * (x + b) + s * x)]
    if form == "distribute_right":
        k, b, s = nonzero_draw(rng, -5, 7), nonzero_draw(rng, -9, 9), nonzero_draw(rng, -4, 6)
        if abs(k) == 1 or k == s:
            return None
        return [B(k, _inner_with(b))], [X(s), N(k * (x + b) - s * x)]
    if form == "distribute_both":
        k, j, b, e = rng.randint(2, 7), rng.randint(2, 6), nonzero_draw(rng, -9, 9), nonzero_draw(rng, -9, 9)
        if k == j:
            return None
        d = k * (x + b) - j * (x + e)
        right = [B(j, _inner_with(e))] + ([N(d)] if d else [])
        return [B(k, _inner_with(b))], right
    if form == "fraction_coef":
        den = rng.choice([2, 3, 4])
        p = rng.randint(1, den - 1) if den > 2 else 1
        if Fraction(p, den).denominator != den or x.denominator > 1 or x % den:
            return None
        s, c = rng.choice([0, 1, 2]), nonzero_draw(rng, -9, 9)
        right = ([X(s)] if s else []) + [N(Fraction(p, den) * x - s * x + c)]
        return [X(Fraction(p, den)), N(c)], right
    raise ValueError(f"multi_step_equation: unknown form {form!r}")


def _inner_with(b: int) -> list[dict]:
    return [X(1), N(b)]


def _ok(left, right, r: dict, form: str) -> bool:
    """Every printed number is a whole number from 1 to `max_number` in size (a fraction only in
    front of the letter, in `fraction_coef`)."""
    nums = numbers_in(left) + numbers_in(right)
    lead = Fraction(left[0]["c"]) if form == "fraction_coef" and "c" in left[0] else None
    whole = all(v.denominator == 1 or v == lead for v in nums)
    return whole and all(0 < abs(v) <= r["max_number"] for v in nums)


class MultiStep:
    """A mode of `equation_solve` (rules `mode`); equation_solve.py dispatches here."""

    name = "equation_solve"
    template = "equation_solve_multi_step.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        n = r.get("problems", PROBLEMS)
        letter = rng.choice(r["letters"])
        lo, hi = r["solutions"]
        forms = [r["forms"][k % len(r["forms"])] for k in range(n)]
        specials = [None] * n
        if r.get("special"):
            slots = rng.sample(range(n), 2)
            specials[slots[0]], specials[slots[1]] = "none", "all"
        fraction_slots: set[int] = set()
        if r.get("fraction_solutions"):
            ok = [k for k in range(n) if forms[k] in FRACTION_FORMS and not specials[k]]
            fraction_slots = set(rng.sample(ok, r["fraction_solutions"]))
        items = []
        for k in range(n):
            for _ in range(2000):
                if k in fraction_slots:
                    den = rng.choice([2, 3, 4, 5])
                    x = Fraction(rng.randint(lo, hi), den)
                    if x.denominator == 1:
                        continue
                else:
                    x = Fraction(rng.randint(lo, hi))
                    if x == 0:
                        continue
                eq = _build(rng, forms[k], x, specials[k])
                if eq and _ok(*eq, r, forms[k]) and all(eq != (i["left"], i["right"]) for i in items):
                    break
            else:
                raise ValueError(f"multi_step_equation: no {forms[k]} equation fits the rules")
            left, right = eq
            items.append({"n": k + 1, "form": forms[k], "special": specials[k], "letter": letter,
                          "left": left, "right": right, "tokens": equation_tokens(left, right, letter)})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        issues: list[Issue] = []
        n = r.get("problems", PROBLEMS)
        items = sheet.items
        if len(items) != n:
            issues.append(error(sheet, f"{len(items)} equations; this part has {n}"))
        if [i["form"] for i in items] != [r["forms"][k % len(r["forms"])] for k in range(len(items))]:
            issues.append(error(sheet, "equation forms don't follow the part's list"))
        lo, hi = r["solutions"]
        fractions = 0
        for i in items:
            label = f"equation {i.get('n')} ({i['form']})"
            if i["letter"] in BAD_LETTERS or i["letter"] not in r["letters"]:
                issues.append(error(sheet, f"{label}: letter {i['letter']!r} isn't allowed"))
            if i["tokens"] != equation_tokens(i["left"], i["right"], i["letter"]):
                issues.append(error(sheet, f"{label}: the printed equation doesn't match its terms"))
            if not _ok(i["left"], i["right"], r, i["form"]):
                issues.append(error(sheet, f"{label}: a number is 0, a fraction or bigger than {r['max_number']}"))
            s = solve(i["left"], i["right"])
            if i["special"]:
                if s != i["special"]:
                    issues.append(error(sheet, f"{label}: should have {i['special']} solutions, has {s}"))
            elif isinstance(s, str):
                issues.append(error(sheet, f"{label}: has {s} solutions but should have one"))
            else:
                if not lo <= s <= hi:
                    issues.append(error(sheet, f"{label}: answer {s} is outside {lo}–{hi}"))
                if s.denominator > 1:
                    fractions += 1
                    if s.denominator > 5:
                        issues.append(error(sheet, f"{label}: answer {s} isn't a simple fraction"))
            brackets = [t for side in (i["left"], i["right"]) for t in side if "k" in t]
            if i["form"].startswith("distribute") and not brackets and not i["special"]:
                issues.append(error(sheet, f"{label}: a bracket form without brackets"))
            if not i["form"].startswith("distribute") and brackets and not i["special"]:
                issues.append(error(sheet, f"{label}: brackets aren't part of this form"))
        if fractions != r.get("fraction_solutions", 0):
            issues.append(error(sheet, f"{fractions} fraction answers; this part has {r.get('fraction_solutions', 0)}"))
        specials = sorted(i["special"] for i in items if i["special"])
        if specials != (["all", "none"] if r.get("special") else []):
            issues.append(error(sheet, f"special equations {specials} don't match the part"))
        keys = [(str(i["left"]), str(i["right"])) for i in items]
        if len(set(keys)) != len(keys):
            issues.append(error(sheet, "the same equation is on the page twice"))
        expected = [answer(i) for i in items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the equations {expected}"))
        return issues

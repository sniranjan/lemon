"""One-step equations (Pandas math, 6.EE.5 and 6.EE.7): x + p = q, p + x = q and px = q, where
p, q and x are all nonnegative (whole numbers, then decimals and fractions).

Rules (merged level → section → part):
- `forms`: the equation shapes, cycling down the page: `add` (x + p = q), `add_left` (p + x = q),
  `times` (px = q).
- `numbers`: the kinds of numbers, cycling down the page: `whole`, `decimal` (tenths and
  hundredths), `fraction` (fractions and mixed numbers, denominators 2–12).
- `max_q`: the largest q (default 100). `problems`: equations a page (default 10).
- `title`: the sheet title.
Numbers are stored as text ("2.5", "3/4", "1 1/2"); verify solves every equation again exactly
(x = q − p or x = q ÷ p, with Fraction) and checks the kinds and ranges.
Lions math adds `mode: multi_step` (multi-step equations, 8.EE.7): see _multi_step.py.
"""

from __future__ import annotations

from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from ._multi_step import MultiStep
from ._rational import fmt, parse

PROBLEMS = 10
MAX_TRIES = 5000
DENS = (2, 3, 4, 5, 6, 8, 10, 12)
LETTERS = "xnyktp"


def style(kind: str) -> str:
    return "decimal" if kind == "decimal" else "fraction"


def kind_ok(x: Fraction, kind: str) -> bool:
    if kind == "whole":
        return x.denominator == 1
    if kind == "decimal":
        return (x * 100).denominator == 1     # tenths and hundredths only
    return x.denominator <= 12


def solve(form: str, p: Fraction, q: Fraction) -> Fraction:
    return q / p if form == "times" else q - p


def _number(rng, kind: str, lo: int, hi: int) -> Fraction:
    if kind == "whole":
        return Fraction(rng.randint(lo, hi))
    if kind == "decimal":
        places = rng.choice([1, 1, 2])
        return Fraction(rng.randint(lo * 10 ** places, hi * 10 ** places), 10 ** places)
    d = rng.choice(DENS)
    return Fraction(rng.randint(lo * d, hi * d), d)


def answer_text(i: dict) -> str:
    return f"{i['letter']} = {i['x']}"


def _mode(sheet: Sheet) -> str | None:
    from ..syllabus import load_level, resolve_page

    return resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules.get("mode")


MODES = {"multi_step": MultiStep}


@register("equation_solve")
class EquationSolve(SheetType):
    template = "equation_solve.html.j2"

    def template_for(self, sheet: Sheet) -> str:
        mode = MODES.get(_mode(sheet))
        return mode.template if mode else self.template

    def generate(self, ctx: GenContext) -> SheetContent:
        if ctx.rules.get("mode") in MODES:
            return MODES[ctx.rules["mode"]]().generate(ctx)
        r = ctx.rules
        rng = ctx.rng
        max_q = r.get("max_q", 100)
        items, seen = [], set()
        for n in range(1, r.get("problems", PROBLEMS) + 1):
            form = r["forms"][(n - 1) % len(r["forms"])]
            kind = r["numbers"][(n - 1) % len(r["numbers"])]
            for _ in range(MAX_TRIES):
                if form == "times":
                    if kind == "whole":
                        p, x = Fraction(rng.randint(2, 12)), Fraction(rng.randint(2, 15))
                    elif kind == "decimal":
                        p = Fraction(rng.choice([2, 3, 4, 5, 6, 8, 15, 25]), rng.choice([1, 10]))
                        x = _number(rng, "decimal", 1, 20)
                    else:
                        d = rng.choice(DENS)
                        p = Fraction(rng.randint(1, d - 1), d)
                        x = _number(rng, rng.choice(["whole", "fraction"]), 1, 12)
                else:
                    p = _number(rng, kind, 1, max_q // 2)
                    x = _number(rng, kind, 1, max_q // 2)
                q = p * x if form == "times" else p + x
                ok = (p > 0 and x > 0 and q <= max_q and p != 1 and x != q and kind_ok(q, kind)
                      and kind_ok(p, kind) and kind_ok(x, kind) and (kind == "whole" or not (p.denominator == q.denominator == x.denominator == 1)))
                if ok and (form, p, q) not in seen:
                    break
            else:
                raise ValueError(f"equation_solve: no {form} equation with {kind} numbers fits {r}")
            seen.add((form, p, q))
            s = style(kind)
            item = {"kind": "equation", "n": n, "form": form, "numbers": kind, "letter": rng.choice(LETTERS),
                    "p": fmt(p, s), "q": fmt(q, s), "x": fmt(x, s)}
            item["answer"] = answer_text(item)
            items.append(item)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["answer"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        if _mode(sheet) in MODES:
            return MODES[_mode(sheet)]().verify(sheet)
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        items = sheet.items
        issues: list[Issue] = []
        count = r.get("problems", PROBLEMS)
        if len(items) != count:
            issues.append(error(sheet, f"{len(items)} equations; this part has {count}"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "equations are not numbered 1, 2, 3… in order"))
        for idx, i in enumerate(items):
            label = f"equation {i.get('n')}"
            form = r["forms"][idx % len(r["forms"])]
            kind = r["numbers"][idx % len(r["numbers"])]
            if i.get("form") != form or i.get("numbers") != kind:
                issues.append(error(sheet, f"{label}: should be a {form} equation with {kind} numbers"))
                continue
            try:
                p, q, x = parse(i["p"]), parse(i["q"]), parse(i["x"])
            except (KeyError, ValueError, ZeroDivisionError):
                issues.append(error(sheet, f"{label}: numbers aren't readable"))
                continue
            s = style(kind)
            if [i["p"], i["q"], i["x"]] != [fmt(v, s) for v in (p, q, x)]:
                issues.append(error(sheet, f"{label}: numbers aren't written in simplest form"))
            if p <= 0 or x <= 0 or q <= 0:
                issues.append(error(sheet, f"{label}: p, q and the answer must all be above 0"))
                continue
            if solve(form, p, q) != x:
                issues.append(error(sheet, f"{label}: the answer is {fmt(solve(form, p, q), s)}, not {i['x']}"))
            if q > r.get("max_q", 100) or not all(kind_ok(v, kind) for v in (p, q, x)):
                issues.append(error(sheet, f"{label}: numbers are outside this part ({kind}, q up to {r.get('max_q', 100)})"))
            if i.get("letter") not in LETTERS:
                issues.append(error(sheet, f"{label}: letter {i.get('letter')!r} isn't used"))
            if i.get("answer") != answer_text(i):
                issues.append(error(sheet, f"{label}: answer should read {answer_text(i)!r}"))
        if len({(i.get("form"), i.get("p"), i.get("q")) for i in items}) != len(items):
            issues.append(error(sheet, "the same equation is on the page twice"))
        if sheet.answer_key != [i.get("answer") for i in items]:
            issues.append(error(sheet, "answer key doesn't match the equations"))
        return issues

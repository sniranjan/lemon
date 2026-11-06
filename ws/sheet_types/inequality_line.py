"""Solve and graph a linear inequality in one variable (Whales math, A-REI.B.3, A-CED.A.1).

Each item is an inequality in x (ASCII `lhs`, `sign`, `rhs`; ws/algebra.py) whose answer is x (sign) s for a
whole number s; the child solves it and shows it on a number line from −10 to 10 (open dot for < and >,
filled dot for ≤ and ≥, shading toward the answers). Verify reads the inequality again, collects it to
P·x + Q (sign) 0, solves it (turning the sign around when P is negative) and checks the stored answer,
the kind and the range.

Rules (merged level → section → part):
- `kinds` (cycled for `items`, default 5): two_step (px + q < c), two_step_negative (−px + q < c: the sign
  turns), both_sides (x on both sides, more on the left), both_sides_negative (more on the right: the
  sign turns), distribute (k(x + q) < c).
- `answer`: [lo, hi] for s (inside the drawn line).
"""

from __future__ import annotations

from fractions import Fraction

from ..algebra import Poly, parse
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

ITEMS = 5
SIGNS = ["<", "<=", ">", ">="]
FLIP = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}
SHOW = {"<": "<", ">": ">", "<=": "≤", ">=": "≥"}
LINE = 10   # the number line runs from −LINE to LINE


def solve(lhs: str, sign: str, rhs: str) -> tuple[str, Fraction, int]:
    """(sign, s, P): the answer x (sign) s and the x-coefficient P after collecting terms."""
    p = parse(lhs) - parse(rhs)
    coeffs = p.univariate("x")
    if len(coeffs) != 2 or coeffs[1] == 0:
        raise ValueError(f"{lhs} {sign} {rhs} isn't linear in x")
    Q, P = coeffs
    return (sign if P > 0 else FLIP[sign]), -Q / P, int(P)


def answer_text(sign: str, s) -> str:
    dot = "open" if sign in ("<", ">") else "closed"
    side = "right" if sign in (">", ">=") else "left"
    return f"x {SHOW[sign]} {str(s).replace('-', '−')} ({dot} dot, shade {side})"


def _nz(rng, lo, hi):
    return rng.choice([k for k in range(lo, hi + 1) if k])


def lin(p: int, q: int) -> str:
    return Poly({(("x", 1),): p, (): q}).text()


def choose(kind: str, rng, r: dict) -> dict:
    lo, hi = r.get("answer", [-9, 9])
    s = rng.randint(lo, hi)
    want = rng.choice(SIGNS)
    if kind in ("two_step", "two_step_negative"):
        p, q = rng.randint(2, 6), _nz(rng, -12, 12)
        if kind == "two_step_negative":
            p = -p
        sign = want if p > 0 else FLIP[want]
        return {"lhs": lin(p, q), "sign": sign, "rhs": str(p * s + q)}
    if kind in ("both_sides", "both_sides_negative"):
        p2 = rng.randint(1, 4)
        p1 = p2 + rng.randint(1, 4)
        if kind == "both_sides_negative":
            p1, p2 = p2, p1
        q2 = _nz(rng, -12, 12)
        q1 = (p2 - p1) * s + q2
        sign = want if p1 > p2 else FLIP[want]
        return {"lhs": lin(p1, q1), "sign": sign, "rhs": lin(p2, q2)}
    if kind == "distribute":
        k, q = rng.randint(2, 5), _nz(rng, -6, 6)
        return {"lhs": f"{k}({lin(1, q)})", "sign": want, "rhs": str(k * (s + q))}
    raise ValueError(f"unknown inequality_line kind {kind!r}")


@register("inequality_line")
class InequalityLine(SheetType):
    template = "inequality_line.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        items, seen = [], set()
        for n in range(1, r.get("items", ITEMS) + 1):
            kind = r["kinds"][(n - 1) % len(r["kinds"])]
            for _ in range(200):
                d = choose(kind, ctx.rng, r)
                key = (d["lhs"], d["rhs"])
                if key not in seen and d["lhs"] != "0":
                    break
            seen.add(key)
            sign, s, _ = solve(d["lhs"], d["sign"], d["rhs"])
            items.append({"n": n, "kind": kind, **d, "show": SHOW[d["sign"]], "answer": answer_text(sign, int(s))})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[f"{i['n']}) {i['answer']}" for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        lo, hi = r.get("answer", [-9, 9])
        if len(sheet.items) != r.get("items", ITEMS):
            issues.append(error(sheet, f"{len(sheet.items)} inequalities; this part has {r.get('items', ITEMS)}"))
        for k, i in enumerate(sheet.items):
            label = f"inequality {i.get('n')} ({i.get('kind')})"
            if i.get("n") != k + 1 or i["kind"] != r["kinds"][k % len(r["kinds"])]:
                issues.append(error(sheet, f"{label}: numbering or kind doesn't follow the part"))
            try:
                sign, s, P = solve(i["lhs"], i["sign"], i["rhs"])
            except ValueError as e:
                issues.append(error(sheet, f"{label}: {e}"))
                continue
            if s.denominator != 1 or not lo <= s <= hi or abs(s) >= LINE:
                issues.append(error(sheet, f"{label}: answer {s} isn't a whole number inside the number line"))
            elif i.get("answer") != answer_text(sign, int(s)) or i.get("show") != SHOW[i["sign"]]:
                issues.append(error(sheet, f"{label}: answer {i.get('answer')} should be {answer_text(sign, int(s))}"))
            flips = i["kind"] in ("two_step_negative", "both_sides_negative")
            if flips != (P < 0):
                issues.append(error(sheet, f"{label}: this kind {'turns' if flips else 'keeps'} the sign"))
        keys = [(i["lhs"], i["rhs"]) for i in sheet.items]
        if len(set(keys)) != len(keys):
            issues.append(error(sheet, "the same inequality is on the page twice"))
        if sheet.answer_key != [f"{i['n']}) {i['answer']}" for i in sheet.items]:
            issues.append(error(sheet, "answer key doesn't match the inequalities"))
        return issues

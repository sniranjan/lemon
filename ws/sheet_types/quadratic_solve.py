"""Solving quadratics (Whales math, A-REI.B.4b, A-SSE.B.3a, A-CED.A.1): by factoring, by square roots,
by the quadratic formula, then choosing a method.

The generator picks the answers first (whole numbers, fractions, or h ± √n), builds the equation from
them and stores it as ASCII (`lhs`, `rhs`, ws/algebra.py language) with its standard-form numbers
`coeffs` [A, B, C] (A·x² + B·x + C = 0). Verify reads the equation again, solves it exactly with the
formula (ws/algebra.quadratic_roots: simplified radicals, reduced fractions), checks every root in exact
Q(√d) arithmetic, and checks the canonical answer: 'x = −3 or x = 1/2', 'x = 4' (a double root),
'x = ±2√3', 'x = (3 ± √5)/2'. Rational parts must have rational roots and the radical part must not.

Rules (merged level → section → part):
- `method`: factor | square_root | formula | mixed (the layout: formula pages have boxes for the three
  numbers and the number under the root; others are an equation and an answer line).
- `kinds` (cycled for `items`): monic, rearrange, lead, double (factor); perfect, scaled, shifted, radical,
  shifted_radical (square roots); formula pages use `roots: rational | irrational`; mixed pages may also
  use formula_rational, formula_irrational and area (a rectangle story from content/math/algebra_stories.yaml,
  where only the positive root is a length).
- `root`: [lo, hi] for whole-number roots, shifts and the numerators of fraction roots; `leads`: leading
  numbers; `coeff`: [lo, hi] for B and C on irrational formula problems; `max_disc`: largest number under
  the root.
"""

from __future__ import annotations

import math
from fractions import Fraction

from ..algebra import Poly, parse, quadratic_roots, roots_text, squarefree
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._algebra_stories import algebra_stories, frame
from ._common import error

RATIONAL_KINDS = {"monic", "rearrange", "lead", "double", "perfect", "scaled", "shifted", "formula_rational", "area"}
IRRATIONAL_KINDS = {"radical", "shifted_radical", "formula_irrational"}


def _nz(rng, lo, hi):
    return rng.choice([k for k in range(lo, hi + 1) if k])


def _x(c: int, var: str = "x") -> Poly:
    return Poly({((var, 1),): 1, (): -c})


def standard(lhs: str, rhs: str, var: str) -> list[int]:
    """[A, B, C] of lhs − rhs = 0; A·var² + B·var + C."""
    p = parse(lhs) - parse(rhs)
    c = p.univariate(var)
    if len(c) != 3 or any(k.denominator != 1 for k in c):
        raise ValueError(f"{lhs} = {rhs} is not a quadratic with whole numbers")
    return [int(c[2]), int(c[1]), int(c[0])]


def item_count(r: dict) -> int:
    return r.get("items", 8)


def choose(kind: str, rng, r: dict) -> dict:
    lo, hi = r.get("root", [-9, 9])
    if kind == "formula":
        kind = "formula_rational" if r.get("roots") == "rational" else "formula_irrational"
    if kind in ("monic", "rearrange"):
        while True:
            p, q = _nz(rng, lo, hi), _nz(rng, lo, hi)
            poly = _x(p) * _x(q)
            if p != q and p + q != 0:
                break
        if kind == "monic":
            return {"lhs": poly.text(), "rhs": "0"}
        c = int(poly.coeff())
        return {"lhs": (poly - Poly.const(c)).text(), "rhs": str(-c)}
    if kind == "double":
        p = _nz(rng, lo, hi)
        return {"lhs": (_x(p) * _x(p)).text(), "rhs": "0"}
    if kind in ("lead", "formula_rational"):
        while True:
            j = rng.choice([k for k in r["leads"] if k > 1] or [2])
            if kind == "formula_rational" and rng.random() < 0.5:
                j1, j2 = j, 1
            else:
                j1, j2 = (j, 1) if kind == "lead" else (rng.choice(r["leads"]), 1)
            p, q = _nz(rng, lo, hi), _nz(rng, lo, hi)
            poly = Poly({(("x", 1),): j1, (): -p}) * Poly({(("x", 1),): j2, (): -q})
            if poly.content() == 1 and Fraction(p, j1) != Fraction(q, j2) and poly.coeff(("x", 1)) != 0:
                return {"lhs": poly.text(), "rhs": "0"}
    if kind == "perfect":
        return {"lhs": "x^2", "rhs": str(rng.randint(2, hi) ** 2)}
    if kind == "scaled":
        k, p = rng.randint(2, 5), rng.randint(2, min(hi, 7))
        return {"lhs": f"{k}x^2", "rhs": str(k * p * p)}
    if kind in ("shifted", "shifted_radical"):
        h = _nz(rng, -6, 6)
        rhs = rng.randint(1, 8) ** 2 if kind == "shifted" else rng.choice([n for n in range(2, 51) if math.isqrt(n) ** 2 != n])
        return {"lhs": f"({_x(h).text()})^2", "rhs": str(rhs)}
    if kind == "radical":
        return {"lhs": "x^2", "rhs": str(rng.choice([n for n in range(8, 99) if math.isqrt(n) ** 2 != n]))}
    if kind == "formula_irrational":
        clo, chi = r.get("coeff", [-9, 9])
        while True:
            A = rng.choice(r["leads"])
            B, C = rng.randint(clo, chi), _nz(rng, clo, chi)
            disc = B * B - 4 * A * C
            if 0 < disc <= r.get("max_disc", 200) and math.isqrt(disc) ** 2 != disc and math.gcd(math.gcd(A, B), C) == 1:
                return {"lhs": Poly({(("x", 2),): A, (("x", 1),): B, (): C}).text(), "rhs": "0"}
    if kind == "area":
        f = rng.choice(algebra_stories()["area"])
        w, more = rng.randint(*f["width"]), rng.randint(*f["more"])
        return {"lhs": f"w^2 + {more}w", "rhs": str(w * (w + more)), "var": "w",
                "story": {"id": f["id"], "more": more, "area": w * (w + more)}}
    raise ValueError(f"unknown quadratic_solve kind {kind!r}")


def story_text(story: dict) -> str:
    f = frame("area", story["id"])
    return f["text"].format(more=story["more"], area=story["area"])


def answer_for(item: dict) -> str:
    var = item.get("var", "x")
    A, B, C = item["coeffs"]
    roots = quadratic_roots(A, B, C)
    if item["kind"] == "area":
        unit = frame("area", item["story"]["id"])["unit"]
        pos = [r.rational() for r in roots if r.is_rational() and r.rational() > 0]
        return f"{var} = {pos[0]} {unit}" if len(pos) == 1 else "?"
    return roots_text(roots, var)


@register("quadratic_solve")
class QuadraticSolve(SheetType):
    template = "quadratic_solve.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        kinds = r.get("kinds", ["formula"])
        items, seen = [], set()
        for n in range(1, item_count(r) + 1):
            kind = kinds[(n - 1) % len(kinds)]
            for _ in range(300):
                d = choose(kind, ctx.rng, r)
                if d["lhs"] + d["rhs"] not in seen:
                    break
            seen.add(d["lhs"] + d["rhs"])
            var = d.pop("var", "x")
            item = {"n": n, "kind": kind, **d, "var": var, "coeffs": standard(d["lhs"], d["rhs"], var)}
            if "story" in item:
                item["text"] = story_text(item["story"])
            item["answer"] = answer_for(item)
            items.append(item)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name),
                            items=[{"method": r["method"], **i} for i in items],
                            answer_key=[f"{i['n']}) {i['answer']}" for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        kinds = r.get("kinds", ["formula"])
        if len(sheet.items) != item_count(r):
            issues.append(error(sheet, f"{len(sheet.items)} equations; this part has {item_count(r)}"))
        lo, hi = r.get("root", [-9, 9])
        for k, i in enumerate(sheet.items):
            label = f"equation {i.get('n')} ({i.get('kind')})"
            if i.get("n") != k + 1 or i.get("kind") != kinds[k % len(kinds)] or i.get("method") != r["method"]:
                issues.append(error(sheet, f"{label}: numbering, kind or method doesn't follow the part"))
            try:
                coeffs = standard(i["lhs"], i["rhs"], i["var"])
            except (ValueError, KeyError) as e:
                issues.append(error(sheet, f"{label}: {e}"))
                continue
            if coeffs != i["coeffs"]:
                issues.append(error(sheet, f"{label}: standard form {i['coeffs']} should be {coeffs}"))
            A, B, C = coeffs
            roots = quadratic_roots(A, B, C)
            if not roots or not all(x.satisfies(A, B, C) for x in roots):
                issues.append(error(sheet, f"{label}: no real roots that check"))
                continue
            if i["answer"] != answer_for(i) or "?" in i["answer"]:
                issues.append(error(sheet, f"{label}: answer {i['answer']!r} should be {answer_for(i)!r}"))
            kind = i["kind"] if i["kind"] != "formula" else ("formula_rational" if r.get("roots") == "rational" else "formula_irrational")
            rational = all(x.is_rational() for x in roots)
            if kind in RATIONAL_KINDS and not rational:
                issues.append(error(sheet, f"{label}: this kind needs whole-number or fraction answers"))
            if kind in IRRATIONAL_KINDS and rational:
                issues.append(error(sheet, f"{label}: this kind should have answers with a root"))
            if not rational and not all(squarefree(x.d) for x in roots):
                issues.append(error(sheet, f"{label}: the root isn't simplified"))
            if math.gcd(math.gcd(A, B), C) != 1 and kind not in ("scaled", "perfect", "radical", "area"):
                issues.append(error(sheet, f"{label}: A, B and C share a factor; divide it out first"))
            if kind in ("monic", "rearrange", "double", "lead") and rational:
                nums = [x.p for x in roots]
                if any(not lo <= v <= hi for v in nums) or (kind != "lead" and any(x.s != 1 for x in roots)):
                    issues.append(error(sheet, f"{label}: roots outside the part's numbers"))
                if kind != "lead" and A != 1:
                    issues.append(error(sheet, f"{label}: this kind has x² alone in front"))
                if kind == "lead" and A not in r["leads"]:
                    issues.append(error(sheet, f"{label}: leading number {A} isn't one of {r['leads']}"))
            if kind.startswith("formula") and A not in r["leads"]:
                issues.append(error(sheet, f"{label}: leading number {A} isn't one of {r['leads']}"))
            if kind == "formula_irrational" and B * B - 4 * A * C > r.get("max_disc", 200):
                issues.append(error(sheet, f"{label}: the number under the root is over {r.get('max_disc', 200)}"))
            if kind == "area":
                if i.get("text") != story_text(i["story"]) or i["lhs"] != f"w^2 + {i['story']['more']}w":
                    issues.append(error(sheet, f"{label}: the story and its equation don't match"))
        eqs = [i["lhs"] + "=" + i["rhs"] for i in sheet.items]
        if len(set(eqs)) != len(eqs):
            issues.append(error(sheet, "the same equation is on the page twice"))
        if sheet.answer_key != [f"{i['n']}) {i['answer']}" for i in sheet.items]:
            issues.append(error(sheet, "answer key doesn't match the equations"))
        return issues


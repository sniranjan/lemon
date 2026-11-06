"""Lines and linear inequalities on a grid (Whales math, F-IF.C.7a, A-REI.D.10, A-REI.D.12), used by the
`graphs` mode of coordinate_grid.

A graph item is y (sign) m·x + b with m = num/den in lowest terms (den > 0) and b whole: sign "=" draws a
line, "<" ">" a dashed boundary, "<=" ">=" a solid one. In standard form (`form: standard`) the same
inequality is printed as A·x + B·y (sign) C with whole A, B, C (B may be negative, which turns the sign
around when y is solved for). Equations are stored as ASCII for ws/algebra.html_expr: a fraction slope
is 'F(2|3)', drawn stacked. Every graph's two plotting points, (0, b) and (den, b + num), are inside
the grid, and the answer says how to draw it and which side to shade.
"""

from __future__ import annotations

import math
from fractions import Fraction

from ..models import Issue, Sheet
from ._common import error

R = 6
FLIP = {"<": ">", ">": "<", "<=": ">=", ">=": "<=", "=": "="}
ASCII_SIGN = {"=": "=", "<": "<", ">": ">", "<=": "≤", ">=": "≥"}


def slope_text(m: Fraction) -> str:
    """'2x', '-x', 'F(2|3)x', '-F(1|2)x' (the slope term)."""
    sign = "-" if m < 0 else ""
    a = abs(m)
    if a.denominator == 1:
        return sign + ("" if a == 1 else str(a.numerator)) + "x"
    return f"{sign}F({a.numerator}|{a.denominator})x"


def intercept_text(b: int) -> str:
    return "" if b == 0 else f" + {b}" if b > 0 else f" - {-b}"


def slope_form(m: Fraction, b: int, sign: str) -> str:
    return f"y {ASCII_SIGN[sign]} {slope_text(m)}{intercept_text(b)}"


def standard_form(A: int, B: int, C: int, sign: str) -> str:
    def term(c: int, v: str, first: bool) -> str:
        body = ("" if abs(c) == 1 else str(abs(c))) + v
        if first:
            return ("-" if c < 0 else "") + body
        return f" {'-' if c < 0 else '+'} {body}"
    return f"{term(A, 'x', True)}{term(B, 'y', False)} {ASCII_SIGN[sign]} {C}"


def solved(item: dict) -> tuple[Fraction, Fraction, str]:
    """(m, b, sign) of y (sign) m·x + b for a stored graph item."""
    if item["form"] == "standard":
        A, B, C = item["abc"]
        sign = item["sign"] if B > 0 else FLIP[item["sign"]]
        return Fraction(-A, B), Fraction(C, B), sign
    return Fraction(item["slope"]), Fraction(item["b"]), item["sign"]


def equation(item: dict) -> str:
    if item["form"] == "standard":
        return standard_form(*item["abc"], item["sign"])
    return slope_form(Fraction(item["slope"]), item["b"], item["sign"])


def fmt(n) -> str:
    return str(n).replace("-", "−")


def answer_for(item: dict) -> str:
    m, b, sign = solved(item)
    p2 = (m.denominator, b + m.numerator)
    pts = f"through (0, {fmt(b)}) and ({fmt(p2[0])}, {fmt(p2[1])})"
    if sign == "=":
        return f"{item['n']}) line {pts}"
    style = "dashed" if sign in ("<", ">") else "solid"
    side = "above" if sign in (">", ">=") else "below"
    return f"{item['n']}) {style} line {pts}; shade {side}"


def choose_graphs(rng, r: dict, progress: float) -> list[dict]:
    """`graphs` items: slopes from `slopes`, intercepts from `intercept`, signs from `signs`;
    from `standard_form_from` (part progress 0–1) on, every other item is in standard form."""
    lo, hi = r.get("intercept", [-4, 4])
    signs = list(r.get("signs", ["="]))
    rng.shuffle(signs)
    items, seen = [], set()
    n_items = r["graphs"]
    slopes = list(r["slopes"])
    rng.shuffle(slopes)
    for n in range(1, n_items + 1):
        sign = signs[(n - 1) % len(signs)]
        standard = progress >= r.get("standard_form_from", 2) and n % 2 == 0
        for k in range(len(slopes) * 4):
            m = Fraction(slopes[(n * 3 + k) % len(slopes)])
            b = rng.randint(lo, hi)
            if not -R <= b + m.numerator <= R or (str(m), b) in seen:
                continue
            item = {"kind": "graph", "n": n, "sign": sign}
            if standard:
                k_ = rng.choice([1, 1, 2, -1])
                B = m.denominator * k_
                A, C = -m.numerator * k_, b * B
                if math.gcd(math.gcd(A, B), C) != 1 or abs(C) > 24:
                    continue
                item.update({"form": "standard", "abc": [A, B, C], "sign": sign if B > 0 else FLIP[sign]})
            else:
                item.update({"form": "slope", "slope": str(m), "b": b})
            seen.add((str(m), b))
            break
        else:
            raise ValueError("no line fits the grid with these slopes and intercepts")
        item["eq"] = equation(item)
        item["answer"] = answer_for(item)
        items.append(item)
    return items


def verify_graphs(sheet: Sheet, r: dict) -> list[Issue]:
    issues: list[Issue] = []
    if len(sheet.items) != r["graphs"]:
        issues.append(error(sheet, f"{len(sheet.items)} graphs; this part has {r['graphs']}"))
    lo, hi = r.get("intercept", [-4, 4])
    pairs = []
    for k, i in enumerate(sheet.items, 1):
        label = f"graph {i.get('n')}"
        if i.get("n") != k or i.get("kind") != "graph":
            issues.append(error(sheet, f"{label}: not numbered in order"))
        if i["sign"] not in r.get("signs", ["="]):
            issues.append(error(sheet, f"{label}: sign {i['sign']} isn't used in this part"))
        if i["form"] == "slope" and Fraction(i["slope"]) != Fraction(i["slope"]).limit_denominator(12):
            issues.append(error(sheet, f"{label}: bad slope"))
        m, b, _ = solved(i)
        if b.denominator != 1 or not lo <= b <= hi:
            issues.append(error(sheet, f"{label}: y-intercept {b} isn't a whole number in {lo}…{hi}"))
        if str(m) not in [str(Fraction(s)) for s in r["slopes"]]:
            issues.append(error(sheet, f"{label}: slope {m} isn't one of the part's slopes"))
        if not -R <= b + m.numerator <= R or m.denominator > R:
            issues.append(error(sheet, f"{label}: the second point is off the grid"))
        if i["form"] == "standard":
            A, B, C = i["abc"]
            if B == 0 or math.gcd(math.gcd(A, B), C) != 1:
                issues.append(error(sheet, f"{label}: {A}, {B}, {C} isn't a reduced standard form"))
        if i.get("eq") != equation(i) or i.get("answer") != answer_for(i):
            issues.append(error(sheet, f"{label}: equation or answer doesn't match its numbers"))
        pairs.append((str(m), str(b)))
    if len(set(pairs)) != len(pairs):
        issues.append(error(sheet, "two graphs are the same line"))
    if sheet.answer_key != [i.get("answer") for i in sheet.items]:
        issues.append(error(sheet, "answer key doesn't match the graphs"))
    return issues

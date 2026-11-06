"""Two-step equations and inequalities (Penguins math, grade 7: 7.EE.4a and 7.EE.4b).

This is the `mode: two_step` of the `equation_solve` sheet type (Pandas math's one-step equations);
equation_solve hands these pages to `generate` / `verify` here and prints them with
equation_solve_two_step.html.j2. Rules (merged level → section → part):
- `forms`: equation shapes cycling down the page: `px+q=r` (−3x + 7 = 22), `p(x+q)=r`
  (4(x − 3) = −20), `x/p+q=r` (x/4 − 2 = 3).
- `inequality: true`: the shapes become px + q < r, ≤, > or ≥ (cycling); the child solves and graphs
  the answer on a number line from −10 to 10 (open dot for < and >, filled dot for ≤ and ≥).
  Every other inequality has a negative p, so the sign has to turn around.
- `solution_range`: [lo, hi] for the answer (or the boundary of an inequality); never 0.
- `coef_range`: [lo, hi] for p (never 0, 1 or −1; x/p uses p from 2 up). q is never 0.
- `max_r`: the largest size of r (default 100). `problems`: per page (default 8; 5 inequalities).
Letters are never `a`, so a printed term can't spell an internal level code. Every number is an
integer stored as text; verify recomputes the answer, the dot and the arrow exactly.
"""

from __future__ import annotations

from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent
from ._common import error
from ._linear import MINUS, show, tokens

TEMPLATE = "equation_solve_two_step.html.j2"
FORMS = ("px+q=r", "p(x+q)=r", "x/p+q=r")
SYMBOLS = ("<", "≥", ">", "≤")
FLIP = {"<": ">", ">": "<", "≤": "≥", "≥": "≤"}
LETTERS = "xnyktp"
Q_RANGE = (-20, 20)
MAX_TRIES = 5000


def is_two_step(rules: dict) -> bool:
    return rules.get("mode") == "two_step"


def count_for(r: dict) -> int:
    return r.get("problems", 5 if r.get("inequality") else 8)


def lhs_value(form: str, p: int, q: int, x: Fraction) -> Fraction:
    if form == "px+q=r":
        return p * x + q
    if form == "p(x+q)=r":
        return p * (x + q)
    return x / p + q


def _signed(q: int) -> str:
    return f"+ {q}" if q > 0 else f"{MINUS} {-q}"


def display(form: str, p: int, q: int, r: int, v: str, sym: str = "=") -> str:
    """The equation as printed, fractions as 'x/4' (stacked by the template)."""
    if form == "px+q=r":
        coef = "" if p == 1 else MINUS if p == -1 else show(p)
        left = f"{coef}{v} {_signed(q)}"
    elif form == "p(x+q)=r":
        left = f"{show(p)}({v} {_signed(q)})"
    else:
        left = f"{v}/{p} {_signed(q)}"
    return f"{left} {sym} {show(r)}"


def solution(form: str, p: int, q: int, r: int, sym: str = "=") -> tuple[Fraction, str]:
    """The answer x (or the boundary) and the solved sign: dividing or multiplying by a negative
    p turns an inequality around."""
    if form == "px+q=r":
        x = Fraction(r - q, p)
    elif form == "p(x+q)=r":
        x = Fraction(r, p) - q
    else:
        x = Fraction((r - q) * p)
    if sym != "=" and p < 0:
        sym = FLIP[sym]
    return x, sym


def answer_text(item: dict) -> str:
    v, x = item["letter"], show(item["x"])
    if not item.get("symbol"):
        return f"{v} = {x}"
    dot = "closed" if item["solved"] in ("≤", "≥") else "open"
    arrow = "right" if item["solved"] in (">", "≥") else "left"
    return f"{v} {item['solved']} {x} ({dot} dot at {x}, arrow {arrow})"


def _make(rng, r: dict, form: str, sym: str, negative: bool | None) -> dict | None:
    lo, hi = r["solution_range"]
    clo, chi = r["coef_range"]
    x = rng.randint(lo, hi)
    if x == 0:
        return None
    if form == "x/p+q=r":
        p = rng.randint(max(2, clo), chi)
        k = rng.randint(lo, hi)
        if k == 0:
            return None
        x = k * p                      # x/p comes out whole
    else:
        p = rng.randint(clo, chi)
    if p in (0, 1, -1) or (negative is not None and (p < 0) != negative):
        return None
    q = rng.randint(*Q_RANGE)
    if q == 0:
        return None
    rv = lhs_value(form, p, q, Fraction(x))
    if rv.denominator != 1 or abs(rv) > r.get("max_r", 100):
        return None
    return {"form": form, "p": p, "q": q, "r": int(rv), "x": x, "symbol": sym if sym != "=" else None}


def generate(ctx: GenContext, name: str) -> SheetContent:
    r = ctx.rules
    rng = ctx.rng
    ineq = bool(r.get("inequality"))
    items, seen = [], set()
    for n in range(1, count_for(r) + 1):
        form = r["forms"][(n - 1) % len(r["forms"])]
        sym = SYMBOLS[(n - 1) % len(SYMBOLS)] if ineq else "="
        negative = (n % 2 == 0) if ineq and form != "x/p+q=r" else None
        for _ in range(MAX_TRIES):
            e = _make(rng, r, form, sym, negative)
            if e and (form, e["p"], e["q"], e["r"]) not in seen:
                break
        else:
            raise ValueError(f"equation_solve: no two-step {form} fits {r}")
        seen.add((form, e["p"], e["q"], e["r"]))
        v = rng.choice(LETTERS)
        x, solved = solution(form, e["p"], e["q"], e["r"], sym)
        item = {"kind": "two_step", "n": n, "form": form, "letter": v,
                "p": str(e["p"]), "q": str(e["q"]), "r": str(e["r"]), "x": str(int(x)),
                "show": tokens(display(form, e["p"], e["q"], e["r"], v, sym))}
        if ineq:
            item.update(symbol=sym, solved=solved)
        item["answer"] = answer_text(item)
        items.append(item)
    return SheetContent(title=r["title"], parent_tip=ctx.tip(name), items=items,
                        answer_key=[i["answer"] for i in items])


def verify(sheet: Sheet, r: dict) -> list[Issue]:
    items = sheet.items
    issues: list[Issue] = []
    ineq = bool(r.get("inequality"))
    if len(items) != count_for(r):
        issues.append(error(sheet, f"{len(items)} problems; this part has {count_for(r)}"))
    if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
        issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
    lo, hi = r["solution_range"]
    clo, chi = r["coef_range"]
    for idx, i in enumerate(items):
        label = f"problem {i.get('n')}"
        form = r["forms"][idx % len(r["forms"])]
        sym = SYMBOLS[idx % len(SYMBOLS)] if ineq else "="
        if i.get("form") != form or i.get("symbol") != (sym if ineq else None):
            issues.append(error(sheet, f"{label}: should be {form} with {sym}"))
            continue
        p, q, rv = int(i["p"]), int(i["q"]), int(i["r"])
        x, solved = solution(form, p, q, rv, sym)
        if x.denominator != 1 or str(int(x)) != i["x"]:
            issues.append(error(sheet, f"{label}: the answer is {x}, not {i['x']}"))
            continue
        if lhs_value(form, p, q, x) != rv:
            issues.append(error(sheet, f"{label}: {i['x']} doesn't make the two sides equal"))
        if p in (0, 1, -1) or q == 0 or not clo <= p <= chi or (form == "x/p+q=r" and p < 2):
            issues.append(error(sheet, f"{label}: p = {p}, q = {q} make a trivial or out-of-range problem"))
        size = x / p if form == "x/p+q=r" else x
        if x == 0 or not lo <= size <= hi or abs(rv) > r.get("max_r", 100):
            issues.append(error(sheet, f"{label}: numbers are outside this part"))
        if ineq and not -10 < x < 10:
            issues.append(error(sheet, f"{label}: the boundary {x} doesn't fit the number line (−10 to 10)"))
        if ineq and i.get("solved") != solved:
            issues.append(error(sheet, f"{label}: solving gives {i['letter']} {solved} {x}, not {i.get('solved')}"))
        if ineq and form != "x/p+q=r" and (p < 0) != (idx % 2 == 1):
            issues.append(error(sheet, f"{label}: every other inequality needs a negative number times the letter"))
        if i.get("letter") not in LETTERS:
            issues.append(error(sheet, f"{label}: letter {i.get('letter')!r} isn't used"))
        if i.get("show") != tokens(display(form, p, q, rv, i["letter"], sym)):
            issues.append(error(sheet, f"{label}: printed problem doesn't match its numbers"))
        if i.get("answer") != answer_text(i):
            issues.append(error(sheet, f"{label}: answer should read {answer_text(i)!r}"))
    if len({(i.get("form"), i.get("p"), i.get("q"), i.get("r")) for i in items}) != len(items):
        issues.append(error(sheet, "the same problem is on the page twice"))
    if sheet.answer_key != [i.get("answer") for i in items]:
        issues.append(error(sheet, "answer key doesn't match the problems"))
    return issues

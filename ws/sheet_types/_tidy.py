"""Tidy expressions (Penguins math, grade 7: 7.EE.1 and 7.EE.2): collecting like terms, opening
brackets, factoring, fraction coefficients, and rewriting a + 0.05a as 1.05a.

This is the `task: tidy` mode of the `expression_eval` sheet type (Pandas math's letters for
numbers); expression_eval hands these pages to `generate` / `verify` here and prints them with
expression_eval_tidy.html.j2. Rules (merged level → section → part):
- `tidy_tasks`: what the problems ask, cycling down the page:
  `combine` (5x − 3 − 8x + 7; every other one has two letters), `expand` (−3(2x − 5)),
  `expand_combine` (4(x − 2) − 6x), `factor` (6x + 9 = 3(2x + 3), the biggest whole number out),
  `fractions` (1/2x + 3/4x − 2/3), `rewrite` (x + 0.15x = 1.15x).
- `coef_range`: [lo, hi] for whole-number coefficients (never 0). `problems`: per page (default 10).
Problems are stored as a tiny source ("-3*(2*x - 5)") read by _linear.lin(); the answer is the one
canonical form (_linear.fmt_lin: letters in order, then the number; x not 1x). Verify reads the
problem and the answer again and checks they are equal, that the answer is canonical, and for
factoring that the number outside is the greatest common factor. Letters are never `a`, so a
printed term can't spell an internal level code ("6a").
"""

from __future__ import annotations

import re
from fractions import Fraction
from math import gcd

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent
from ._common import error
from ._linear import MINUS, Lin, fmt, fmt_lin, lin, read_lin, tokens

TEMPLATE = "expression_eval_tidy.html.j2"
PROBLEMS = 10
LETTERS = "xnyktp"
PAIRS = (("x", "y"), ("n", "p"), ("k", "t"), ("p", "t"), ("n", "y"))
FRACTION_DENS = (2, 3, 4, 6, 8)
PERCENTS = (5, 10, 15, 20, 25, 30, 40, 50, 60, 75)
MAX_TRIES = 5000


def is_tidy(rules: dict) -> bool:
    return rules.get("task") == "tidy"


def pretty(src: str) -> str:
    """'-3*(2*x - 5) + 4*x' -> '−3(2x − 5) + 4x' (fractions stay 'n/d' for the template)."""
    return src.replace("*", "").replace("-", MINUS)


def _term(c, v: str = "") -> str:
    """A signed term for a source string: (3, 'x') -> '3*x'; (-1, 'x') -> '-x'; (Fraction(1, 2), 'x') -> '1/2*x'."""
    c = Fraction(c)
    sign = "-" if c < 0 else ""
    c = abs(c)
    if v:
        body = v if c == 1 else f"{fmt(c)}*{v}" if c.denominator == 1 else f"{c.numerator}/{c.denominator}*{v}"
    else:
        body = fmt(c) if c.denominator == 1 else f"{c.numerator}/{c.denominator}"
    return sign + body


def join(terms: list[str]) -> str:
    out = terms[0]
    for t in terms[1:]:
        out += f" - {t[1:]}" if t.startswith("-") else f" + {t}"
    return out


def style_for(task: str) -> str:
    return "decimal" if task == "rewrite" else "fraction"


def factor_answer(src: str) -> str | None:
    e = lin(src)
    nums = [c for _, c in e.coef] + [e.const]
    if any(c.denominator != 1 for c in nums) or len(e.coef) != 1:
        return None
    g = 0
    for c in nums:
        g = gcd(g, int(c))
    if g < 2:
        return None
    return f"{g}({fmt_lin(e.scale(Fraction(1, g)))})"


def answer_for(task: str, src: str) -> str:
    if task == "factor":
        return factor_answer(src) or ""
    return fmt_lin(lin(src), style_for(task))


def _nz(rng, lo: int, hi: int, avoid=(0,)) -> int:
    while True:
        k = rng.randint(lo, hi)
        if k not in avoid:
            return k


def _make(rng, task: str, n: int, r: dict) -> str | None:
    lo, hi = r["coef_range"]
    v = rng.choice(LETTERS)
    if task == "combine":
        if n % 2 == 0:
            v1, v2 = rng.choice(PAIRS)
            terms = [_term(_nz(rng, lo, hi), v1), _term(_nz(rng, lo, hi), v2),
                     _term(_nz(rng, lo, hi), v1), _term(_nz(rng, lo, hi), v2)]
        else:
            terms = [_term(_nz(rng, lo, hi), v), _term(_nz(rng, lo, hi)),
                     _term(_nz(rng, lo, hi), v), _term(_nz(rng, lo, hi))]
        rng.shuffle(terms)
        src = join(terms)
    elif task == "expand":
        k = _nz(rng, lo, hi, (0, 1))
        p, q = _nz(rng, 1, 9), _nz(rng, -9, 9)
        inner = join([_term(p, v), _term(q)])
        src = f"-({inner})" if k == -1 else f"{k}*({inner})"
    elif task == "expand_combine":
        k = _nz(rng, lo, hi, (0, 1, -1))
        p, q = _nz(rng, 1, 5), _nz(rng, -9, 9)
        m, c = _nz(rng, lo, hi), _nz(rng, -9, 9)
        src = join([f"{k}*({join([_term(p, v), _term(q)])})", _term(m, v), _term(c)])
    elif task == "factor":
        g = rng.randint(2, 9)
        p, q = rng.randint(1, 9), _nz(rng, -9, 9)
        if gcd(p, abs(q)) != 1:
            return None
        src = join([_term(g * p, v), _term(g * q)])
    elif task == "fractions":
        def frac():
            d = rng.choice(FRACTION_DENS)
            return Fraction(_nz(rng, -d * 2 + 1, d * 2 - 1), d)
        a, b, c = frac(), frac(), frac()
        if a.denominator == 1 or b.denominator == 1 or c.denominator == 1:
            return None
        terms = [_term(a, v), _term(b, v), _term(c)]
        src = join(terms)
    elif task == "rewrite":
        pct = rng.choice(PERCENTS)
        k = Fraction(pct, 100)
        src = f"{v} + {fmt(k, 'decimal')}*{v}" if rng.random() < 0.5 else f"{v} - {fmt(k, 'decimal')}*{v}"
    else:
        raise ValueError(f"unknown tidy task {task!r}")
    return src


def problem_ok(task: str, src: str) -> bool:
    e = lin(src)
    if any(c == 0 for _, c in e.coef) or not e.coef:
        return False
    if task == "combine" and len(lin(src).coef) == 0:
        return False
    if task == "combine" and pretty(src) == fmt_lin(e):
        return False   # already tidy
    if task == "fractions" and any(c.denominator > 24 for _, c in e.coef):
        return False
    return bool(answer_for(task, src))


def generate(ctx: GenContext, name: str) -> SheetContent:
    r = ctx.rules
    rng = ctx.rng
    items, seen = [], set()
    for n in range(1, r.get("problems", PROBLEMS) + 1):
        task = r["tidy_tasks"][(n - 1) % len(r["tidy_tasks"])]
        for _ in range(MAX_TRIES):
            src = _make(rng, task, n, r)
            if src and src not in seen and problem_ok(task, src):
                break
        else:
            raise ValueError(f"expression_eval: no tidy {task} problem fits {r}")
        seen.add(src)
        items.append({"kind": "tidy", "n": n, "task": task, "src": src, "show": tokens(pretty(src)),
                      "answer": answer_for(task, src)})
    return SheetContent(title=r["title"], parent_tip=ctx.tip(name), items=items,
                        answer_key=[i["answer"] for i in items])


_FACTOR = re.compile(r"^(\d+)\((.+)\)$")


def verify(sheet: Sheet, r: dict) -> list[Issue]:
    items = sheet.items
    issues: list[Issue] = []
    count = r.get("problems", PROBLEMS)
    if len(items) != count:
        issues.append(error(sheet, f"{len(items)} problems; this part has {count}"))
    if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
        issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
    lo, hi = r["coef_range"]
    for idx, i in enumerate(items):
        label = f"problem {i.get('n')}"
        task = r["tidy_tasks"][idx % len(r["tidy_tasks"])]
        if i.get("task") != task:
            issues.append(error(sheet, f"{label}: should be a {task} problem"))
            continue
        try:
            e = lin(i["src"])
        except (ValueError, SyntaxError) as ex:
            issues.append(error(sheet, f"{label}: can't read {i.get('src')!r}: {ex}"))
            continue
        letters = set(re.findall(r"[a-z]", i["src"]))
        if not letters <= set(LETTERS):
            issues.append(error(sheet, f"{label}: letters {sorted(letters)} aren't allowed (never 'a')"))
        whole = [int(m) for m in re.findall(r"\d+", i["src"]) if "/" not in i["src"] and "." not in i["src"]]
        if task in ("combine", "expand", "expand_combine") and any(w > max(abs(lo), hi, 9) for w in whole):
            issues.append(error(sheet, f"{label}: a number in {i['src']!r} is outside this part"))
        if not problem_ok(task, i["src"]):
            issues.append(error(sheet, f"{label}: {i['src']!r} isn't a good {task} problem"))
        if i.get("show") != tokens(pretty(i["src"])):
            issues.append(error(sheet, f"{label}: printed problem doesn't match its source"))
        ans = i.get("answer", "")
        if task == "factor":
            m = _FACTOR.match(ans)
            if not m:
                issues.append(error(sheet, f"{label}: {ans!r} isn't written as g(…)"))
                continue
            g, inner = int(m.group(1)), read_lin(m.group(2))
            if inner.scale(Fraction(g)) != e:
                issues.append(error(sheet, f"{label}: {ans} doesn't multiply back to the problem"))
            nums = [c for _, c in inner.coef] + [inner.const]
            if any(c.denominator != 1 for c in nums) or gcd(*[abs(int(c)) for c in nums]) != 1:
                issues.append(error(sheet, f"{label}: {g} isn't the greatest common factor"))
            if m.group(2) != fmt_lin(inner):
                issues.append(error(sheet, f"{label}: the inside of {ans} isn't in tidy form"))
        else:
            if ans != fmt_lin(e, style_for(task)):
                issues.append(error(sheet, f"{label}: the tidy form is {fmt_lin(e, style_for(task))}, not {ans}"))
            elif read_lin(ans) != e:
                issues.append(error(sheet, f"{label}: {ans} isn't equal to the problem"))
        if "-" in ans:
            issues.append(error(sheet, f"{label}: a hyphen in the answer (use {MINUS})"))
    if len({i.get("src") for i in items}) != len(items):
        issues.append(error(sheet, "the same problem is on the page twice"))
    if sheet.answer_key != [i.get("answer") for i in items]:
        issues.append(error(sheet, "answer key doesn't match the problems"))
    return issues


__all__ = ["Lin", "TEMPLATE", "generate", "is_tidy", "verify"]

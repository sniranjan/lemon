"""Fraction arithmetic with stacked fractions (Otters math): adding and taking away fractions with
unlike denominators, mixed numbers (5.NF.1) and multiplying by a fraction (5.NF.4).

Each item is one problem `a op b`, every operand `{"whole", "num", "den"}` (a whole number is
num 0, den 1). The child writes the answer in simplest form; more than 1 as a mixed number.
Rules (merged level → section → part):
- `op`: add | sub | mul | mixed (mixed: half adding, half taking away).
- `denominators`: the denominators a fraction may have. Operands are always in simplest form.
- `relation` (add/sub): multiple (one denominator goes into the other: 1/2 + 3/8), other (neither
  goes into the other: 3/4 + 1/6), any. The two denominators always differ (unlike fractions).
- `mixed_numbers`: operands are mixed numbers with wholes 1…`max_whole`; taking away never goes below 0.
- `max_answer` (optional): no answer above it.
- `whole_times` (mul): all (every problem is a whole number 2…`max_whole` times a fraction, either
  order) or a count of such problems; the rest are fraction times fraction.
- `simplify_min`: at least this many answers need simplifying after the usual working (common
  denominator for add/sub, top times top over bottom times bottom for mul).
- `layout`: list (default; 8 a page) or area (mul only: a unit square cut into columns by the first
  fraction's denominator and rows by the second's, both shaded, 4 a page).
- `problems`, `title`.

Dividing (Pandas math, 6.NS.1) is `op: div`, with its own rules (Otters pages never use them):
- `dividend`, `divisor`: kinds the problems cycle through, in order: `whole` (3), `proper` (3/4),
  `mixed` (2 1/2), `unit` (1/5, divisor only). `max_den`, `max_whole`: the largest denominator and whole.
- `layout`: list (as above) or model (5 rows: whole bars cut into pieces the size of a unit-fraction
  divisor, the dividend's pieces shaded, `bar` = {bars, pieces, shaded}; every answer is whole and at
  least 2, at most `max_pieces` pieces drawn). On a list, `max_answer_den` (default 12) and
  `max_answer` (default 20) keep answers friendly, and no answer is 1.
Keep-change-flip is in the parent tips only, never on the child's page.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd, lcm

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules
from ._exact import as_mixed, frac_str, is_simplest, operand, value

PROBLEMS = 8
MAX_TRIES = 20000
SIGN = {"add": "+", "sub": "−", "mul": "×", "div": "÷"}
DIV_DENS = (2, 3, 4, 5, 6, 8, 10, 12)


def answer(item: dict) -> Fraction:
    a, b = value(item["a"]), value(item["b"])
    return {"add": a + b, "sub": a - b, "mul": a * b, "div": a / b}[item["op"]]


# --- dividing (Pandas math) ------------------------------------------------------------------

def div_kind(x: Fraction) -> str:
    if x.denominator == 1:
        return "whole"
    if x < 1:
        return "unit" if x.numerator == 1 else "proper"
    return "mixed"


def model_bar(a: Fraction, b: Fraction) -> dict:
    """Whole bars, each cut into pieces the size of b; the dividend's pieces are shaded."""
    return {"bars": -(-a.numerator // a.denominator), "pieces": b.denominator, "shaded": int(a * b.denominator)}


def _div_pick(rng, kind: str, r: dict) -> Fraction:
    if kind == "whole":
        return Fraction(rng.randint(1, r["max_whole"]))
    d = rng.choice([d for d in DIV_DENS if d <= r["max_den"]])
    if kind == "unit":
        return Fraction(1, d)
    x = Fraction(rng.randint(1, d - 1), d)
    return x if kind == "proper" else rng.randint(1, r["max_whole"]) + x


def divide_ok(r: dict, a: Fraction, b: Fraction) -> bool:
    q = a / b
    if r.get("layout") == "model":
        return (b.numerator == 1 and q.denominator == 1 and q >= 2 and (a * b.denominator).denominator == 1
                and model_bar(a, b)["bars"] * b.denominator <= r.get("max_pieces", 24))
    return q != 1 and q.denominator <= r.get("max_answer_den", 12) and q <= r.get("max_answer", 20)


def _as_operand(x: Fraction) -> dict:
    return as_mixed(x)


def needs_simplify(item: dict) -> bool:
    """Does the usual working end in a fraction that still needs simplifying?"""
    a, b = item["a"], item["b"]
    if item["op"] == "mul":
        top = (a["whole"] * a["den"] + a["num"]) * (b["whole"] * b["den"] + b["num"])
        bottom = a["den"] * b["den"]
    else:
        bottom = lcm(a["den"], b["den"])
        sign = 1 if item["op"] == "add" else -1
        top = (a["num"] * (bottom // a["den"]) + sign * b["num"] * (bottom // b["den"])) % bottom   # after trading wholes
    return top != 0 and gcd(top, bottom) > 1


def related(d1: int, d2: int) -> bool:
    return d1 % d2 == 0 or d2 % d1 == 0


def _fraction(rng, dens) -> dict:
    while True:
        d = rng.choice(dens)
        n = rng.randint(1, d - 1)
        if gcd(n, d) == 1:
            return operand(0, n, d)


def _ops(r: dict, n: int, rng) -> list[str]:
    if r["op"] != "mixed":
        return [r["op"]] * n
    ops = ["add"] * ((n + 1) // 2) + ["sub"] * (n // 2)
    rng.shuffle(ops)
    return ops


def _wholes(r: dict, ops: list[str], rng) -> list[bool]:
    wt = r.get("whole_times", 0)
    if wt == "all":
        return [True] * len(ops)
    flags = [k < wt for k in range(len(ops))]
    rng.shuffle(flags)
    return flags


def problem_ok(r: dict, item: dict, whole: bool | None = None) -> str | None:
    op, a, b = item["op"], item["a"], item["b"]
    allowed = ("add", "sub") if r["op"] == "mixed" else (r["op"],)
    if op not in allowed:
        return f"{op} isn't used in this part"
    for o in (a, b):
        if not is_simplest(o) or o["whole"] < 0:
            return f"{o} isn't a whole number or a fraction in simplest form"
        if o["num"] and o["den"] not in r["denominators"]:
            return f"denominator {o['den']} isn't used here ({r['denominators']})"
    is_whole = [o["num"] == 0 for o in (a, b)]
    if op == "mul":
        wt = r.get("whole_times", 0)
        if sum(is_whole) > 1 or (any(is_whole) and (wt == 0)):
            return "whole number factor isn't used here"
        if wt == "all" and not any(is_whole):
            return "every problem here is a whole number times a fraction"
        if whole is not None and any(is_whole) != whole:
            return "whole number times fraction in the wrong place"
        for o in (a, b):
            if o["num"] == 0 and not 2 <= o["whole"] <= r.get("max_whole", 9):
                return f"whole number {o['whole']} is outside 2–{r.get('max_whole', 9)}"
            if o["num"] and o["whole"]:
                return "mixed numbers aren't multiplied here"
        if r.get("layout") == "area" and any(is_whole):
            return "an area model needs two fractions"
    else:
        if any(is_whole):
            return "both numbers need a fraction part"
        if a["den"] == b["den"]:
            return f"denominators are both {a['den']}; this part is about unlike fractions"
        rel = r.get("relation", "any")
        if rel == "multiple" and not related(a["den"], b["den"]):
            return f"neither {a['den']} nor {b['den']} goes into the other"
        if rel == "other" and related(a["den"], b["den"]):
            return f"{a['den']} and {b['den']}: one goes into the other"
        if r.get("mixed_numbers"):
            if not all(1 <= o["whole"] <= r.get("max_whole", 5) for o in (a, b)):
                return f"wholes must be 1–{r.get('max_whole', 5)}"
        elif a["whole"] or b["whole"]:
            return "mixed numbers aren't used in this part"
    ans = answer(item)
    if ans <= 0:
        return f"answer {ans} isn't more than 0"
    if "max_answer" in r and ans > Fraction(r["max_answer"]):
        return f"answer {frac_str(ans)} is more than {r['max_answer']}"
    return None


@register("fraction_ops")
class FractionOps(SheetType):
    template = "fraction_ops.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        if r["op"] == "div":
            return self._generate_divide(ctx)
        n = r.get("problems", PROBLEMS)
        ops = _ops(r, n, rng)
        wholes = _wholes(r, ops, rng)
        simplify = [k < r.get("simplify_min", 0) for k in range(n)]
        rng.shuffle(simplify)
        dens = list(r["denominators"])
        items, seen = [], set()
        for op, whole, simp in zip(ops, wholes, simplify):
            for _ in range(MAX_TRIES):
                a, b = _fraction(rng, dens), _fraction(rng, dens)
                if op == "mul" and whole:
                    w = operand(rng.randint(2, r.get("max_whole", 9)))
                    a, b = (w, b) if rng.random() < 0.5 else (a, w)
                if r.get("mixed_numbers"):
                    a["whole"], b["whole"] = (rng.randint(1, r.get("max_whole", 5)) for _ in range(2))
                if op == "sub" and value(a) < value(b):
                    a, b = b, a
                item = {"kind": "fraction", "layout": r.get("layout", "list"), "op": op, "sign": SIGN[op], "a": a, "b": b}
                key = (op, repr(a), repr(b))
                if key not in seen and problem_ok(r, item, whole if op == "mul" else None) is None \
                        and (not simp or needs_simplify(item)):
                    break
            else:
                raise ValueError(f"fraction_ops: can't find a {op} problem with these rules: {r}")
            seen.add(key)
            items.append(item)
        rng.shuffle(items)
        for k, item in enumerate(items, 1):
            item["n"] = k
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[frac_str(answer(i)) for i in items])

    def _generate_divide(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        layout = r.get("layout", "list")
        items, seen = [], set()
        for k in range(r.get("problems", PROBLEMS)):
            ka, kb = r["dividend"][k % len(r["dividend"])], r["divisor"][k % len(r["divisor"])]
            for _ in range(MAX_TRIES):
                a, b = _div_pick(rng, ka, r), _div_pick(rng, kb, r)
                if (a, b) not in seen and div_kind(a) == ka and div_kind(b) == kb and divide_ok(r, a, b):
                    break
            else:
                raise ValueError(f"fraction_ops: no {ka} ÷ {kb} problem fits {r}")
            seen.add((a, b))
            item = {"kind": "fraction", "layout": layout, "op": "div", "sign": SIGN["div"],
                    "a": _as_operand(a), "b": _as_operand(b), "n": k + 1}
            if layout == "model":
                item["bar"] = model_bar(a, b)
            items.append(item)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[frac_str(answer(i)) for i in items])

    def _verify_divide(self, sheet: Sheet, r: dict) -> list[Issue]:
        issues: list[Issue] = []
        items = sheet.items
        layout = r.get("layout", "list")
        if len(items) != r.get("problems", PROBLEMS):
            issues.append(error(sheet, f"{len(items)} problems; the part asks for {r.get('problems', PROBLEMS)}"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
        seen = set()
        for k, i in enumerate(items):
            label = f"problem {i.get('n')}"
            if i.get("op") != "div" or i.get("sign") != "÷" or i.get("layout") != layout:
                issues.append(error(sheet, f"{label}: should be a ÷ problem in the {layout} layout"))
                continue
            if not all(is_simplest(o) and o["whole"] >= 0 for o in (i["a"], i["b"])):
                issues.append(error(sheet, f"{label}: numbers aren't in simplest form"))
                continue
            a, b = value(i["a"]), value(i["b"])
            if a <= 0 or b <= 0:
                issues.append(error(sheet, f"{label}: numbers must be above 0"))
                continue
            ka, kb = r["dividend"][k % len(r["dividend"])], r["divisor"][k % len(r["divisor"])]
            if div_kind(a) != ka or div_kind(b) != kb:
                issues.append(error(sheet, f"{label}: should be {ka} ÷ {kb}"))
            if max(a.denominator, b.denominator) > r["max_den"] or max(int(a), int(b)) > r["max_whole"]:
                issues.append(error(sheet, f"{label}: numbers are bigger than this part allows"))
            if not divide_ok(r, a, b):
                issues.append(error(sheet, f"{label}: {frac_str(a)} ÷ {frac_str(b)} = {frac_str(a / b)} "
                                           f"doesn't fit this part"))
            if (a, b) in seen:
                issues.append(error(sheet, f"{label} appears twice"))
            seen.add((a, b))
            if layout == "model" and i.get("bar") != model_bar(a, b):
                issues.append(error(sheet, f"{label}: the bar should be {model_bar(a, b)}"))
            if layout != "model" and "bar" in i:
                issues.append(error(sheet, f"{label}: only model pages have bars"))
        try:
            expected = [frac_str(answer(i)) for i in items]
        except (ValueError, ZeroDivisionError, KeyError) as e:
            return issues + [error(sheet, f"can't work out the answers: {e}")]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        if r["op"] == "div":
            return self._verify_divide(sheet, r)
        issues: list[Issue] = []
        n = r.get("problems", PROBLEMS)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} problems; the part asks for {n}"))
        if [i.get("n") for i in sheet.items] != list(range(1, len(sheet.items) + 1)):
            issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
        seen = set()
        for i in sheet.items:
            label = f"problem {i.get('n')}"
            why = problem_ok(r, i)
            if why:
                issues.append(error(sheet, f"{label}: {why}"))
            if i.get("layout") != r.get("layout", "list"):
                issues.append(error(sheet, f"{label}: layout {i.get('layout')!r}; this part uses {r.get('layout', 'list')!r}"))
            if i.get("sign") != SIGN.get(i["op"]):
                issues.append(error(sheet, f"{label}: sign {i.get('sign')!r} doesn't match {i['op']}"))
            key = (i["op"], repr(i["a"]), repr(i["b"]))
            if key in seen:
                issues.append(error(sheet, f"{label} appears twice"))
            seen.add(key)
        ops = {i["op"] for i in sheet.items}
        if r["op"] == "mixed" and len(sheet.items) > 1 and ops != {"add", "sub"}:
            issues.append(error(sheet, "a mixed page needs both adding and taking away"))
        wt = r.get("whole_times", 0)
        if isinstance(wt, int) and wt and r["op"] == "mul":
            got = sum(any(o["num"] == 0 for o in (i["a"], i["b"])) for i in sheet.items)
            if got != wt:
                issues.append(error(sheet, f"{got} whole-number problems; this part has {wt}"))
        simp = sum(needs_simplify(i) for i in sheet.items)
        if simp < r.get("simplify_min", 0):
            issues.append(error(sheet, f"{simp} answers need simplifying; this part needs {r['simplify_min']}"))
        try:
            expected = [frac_str(answer(i)) for i in sheet.items]
        except (ValueError, ZeroDivisionError) as e:
            return issues + [error(sheet, f"can't work out the answers: {e}")]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues

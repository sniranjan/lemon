"""Exponent rules and radicals (Whales math, N-RN.A.1–2): simplify each expression.

Each item is one expression to simplify, stored as `data` (whole numbers and "p/q" strings only) plus
the ASCII the sheet shows (`q`, or `top`/`bottom` for a fraction bar) and the canonical `answer`
(ws/algebra.py markup: '12x^7', '3/x^4', 'x^(5/6)', '6R(2|2)' for 6√2). `build(kind, data)` is the one
place that turns data into what is shown and the answer; verify calls it again, checks every number is
inside the part's ranges, and checks each answer numerically against the data with plain floats.
Canonical answers: positive exponents only (negative ones move below the bar), roots simplified, letters
taken as positive.

Rules (merged level → section → part):
- `kinds`: the page's items in order (one per item); `items`: how many (default 8).
- `exp`: [lo, hi] whole exponents in part 1 kinds; `bases`, `dens`: the roots and the root index for
  rational exponents (8^(2/3): root 2, index 3); `outs`, `insides`: what comes out of a root and what
  stays in (√72: out 6, inside 2).
Kinds: product, quotient, power, power_product, zero_negative, product_negative, quotient_negative;
eval_rational, to_root, to_power, rational_product, rational_quotient, rational_power;
simplify_sqrt, simplify_cbrt, root_product, root_vars.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

from ..algebra import Mono, rational_power, root_parts
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules

ITEMS = 8
X, Y = 1.37, 0.81   # float check values (letters are positive)


def fs(f) -> str:
    f = F(f)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def mono(c=1, **exps) -> dict:
    """A stored monomial; exponents of 0 stay (the question may show x⁰)."""
    return {"c": fs(c), **{v: fs(F(e)) for v, e in sorted(exps.items())}}


def show(m: dict) -> str:
    """A monomial as written in the question: exponents as given, even 0 or negative."""
    c = F(m.get("c", "1"))
    body = ""
    for v in sorted(k for k in m if k != "c"):
        e = F(m[v])
        body += v + ("" if e == 1 else f"^{e.numerator}" if e.denominator == 1 else f"^({e.numerator}/{e.denominator})")
    if not body:
        return fs(c)
    return ("" if c == 1 else "-" if c == -1 else fs(c)) + body


def answer_mono(m: Mono) -> str:
    return m.text(positive=True)


def fval(m: dict) -> float:
    """Float value of a stored monomial at x = X, y = Y."""
    v = float(F(m.get("c", "1")))
    for k, e in m.items():
        if k != "c":
            v *= {"x": X, "y": Y}[k] ** float(F(e))
    return v


def mono_value(m: Mono) -> float:
    v = float(m.coeff)
    for k, e in m.exps:
        v *= {"x": X, "y": Y}[k] ** float(e)
    return v


def build(kind: str, d: dict) -> tuple[dict, str, float, float]:
    """(what the sheet shows, canonical answer, float of the question, float of the answer)."""
    if kind in ("product", "product_negative", "rational_product"):
        a, b = Mono.from_json(d["a"]), Mono.from_json(d["b"])
        ans = a * b
        return {"q": f"{show(d['a'])} * {show(d['b'])}"}, answer_mono(ans), fval(d["a"]) * fval(d["b"]), mono_value(ans)
    if kind in ("quotient", "quotient_negative", "rational_quotient"):
        a, b = Mono.from_json(d["a"]), Mono.from_json(d["b"])
        ans = a / b
        return {"top": show(d["a"]), "bottom": show(d["b"])}, answer_mono(ans), fval(d["a"]) / fval(d["b"]), mono_value(ans)
    if kind in ("power", "power_product", "rational_power"):
        a, n = Mono.from_json(d["a"]), F(d["n"])
        ans = a.power(n)
        inner = show(d["a"])
        n_txt = f"^{n.numerator}" if n.denominator == 1 else f"^({n.numerator}/{n.denominator})"
        return {"q": f"({inner}){n_txt}"}, answer_mono(ans), fval(d["a"]) ** float(n), mono_value(ans)
    if kind == "zero_negative":
        a = Mono.from_json(d["a"])
        return {"q": show(d["a"])}, answer_mono(a), fval(d["a"]), mono_value(a)
    if kind == "eval_rational":
        base, p = F(d["base"]), F(d["p"])
        val = rational_power(base, p)
        return ({"q": f"{d['base']}^({p.numerator}/{p.denominator})"}, fs(val),
                float(base) ** float(p), float(val))
    if kind == "to_root":
        p = F(d["p"])
        inside = "x" if p.numerator == 1 else f"x^{p.numerator}"
        return ({"q": f"x^({p.numerator}/{p.denominator})"}, f"R({p.denominator}|{inside})",
                X ** float(p), X ** (p.numerator / p.denominator))
    if kind == "to_power":
        n, e = d["index"], d["e"]
        p = F(e, n)
        inside = "x" if e == 1 else f"x^{e}"
        ans = Mono.make(1, {"x": p})
        return {"q": f"R({n}|{inside})"}, answer_mono(ans), (X ** e) ** (1 / n), mono_value(ans)
    if kind in ("simplify_sqrt", "simplify_cbrt"):
        n, k = d["index"], d["k"]
        out, inside = root_parts(n, k)
        return {"q": f"R({n}|{k})"}, f"{out}R({n}|{inside})", k ** (1 / n), out * inside ** (1 / n)
    if kind == "root_product":
        u, v = d["u"], d["v"]
        out, inside = root_parts(2, u * v)
        return {"q": f"R(2|{u}) * R(2|{v})"}, f"{out}R(2|{inside})", math.sqrt(u) * math.sqrt(v), out * math.sqrt(inside)
    if kind == "root_vars":
        k, e = d["k"], d["e"]
        out, inside = root_parts(2, k)
        xo, xi = e // 2, e % 2
        outside = f"{'' if out == 1 else out}{'x' if xo == 1 else f'x^{xo}' if xo else ''}"
        inner = f"{'' if inside == 1 and xi else inside}{'x' if xi else ''}"
        ans = f"{outside}R(2|{inner})" if inner != "1" else outside
        return ({"q": f"R(2|{k}x^{e})"}, ans, math.sqrt(k * X ** e),
                out * X ** xo * math.sqrt((inside if inner != '1' else 1) * (X if xi else 1)))
    raise ValueError(f"unknown exponent_rules kind {kind!r}")


# --- choosing the numbers ----------------------------------------------------------------------

def _coeff(rng, big: bool = True) -> int:
    return rng.choice([1, 1, 2, 3, 4, 5, 6] if big else [1, 2, 3])


def choose(kind: str, rng, r: dict) -> dict:
    lo, hi = r.get("exp", [1, 9])
    e = lambda a=lo, b=hi: rng.randint(a, b)
    if kind == "product":
        return {"a": mono(_coeff(rng), x=e()), "b": mono(_coeff(rng), x=e())}
    if kind == "quotient":
        c2, k = rng.choice([1, 2, 3, 4]), rng.choice([1, 2, 3, 5])
        top = e(lo + 1, hi)
        return {"a": mono(c2 * k, x=top), "b": mono(c2, x=e(lo, top - 1))}
    if kind == "power":
        n = rng.randint(2, 4)
        c = rng.choice([1, 2, 3]) if n <= 3 else rng.choice([1, 2])
        return {"a": mono(c, x=e(lo if c > 1 else max(lo, 2), min(hi, 6))), "n": str(n)}   # no bare (x)ⁿ
    if kind == "power_product":
        n = rng.randint(2, 3)
        return {"a": mono(rng.choice([1, 2, 3]), x=e(lo, 5), y=e(lo, 4)), "n": str(n)}
    if kind == "zero_negative":
        if rng.random() < 0.5:
            return {"a": mono(rng.randint(2, 9), x=0, y=e(lo, 5))}
        return {"a": mono(rng.randint(2, 9), x=-e(lo, 6))}
    if kind == "product_negative":
        a = e()
        return {"a": mono(_coeff(rng, False), x=a), "b": mono(_coeff(rng, False), x=-e(a + 1, hi + 2))}
    if kind == "quotient_negative":
        c, k = rng.choice([2, 3, 4]), rng.choice([2, 3])
        top = e(lo, hi - 2)
        return {"a": mono(c, x=top), "b": mono(c * k, x=e(top + 1, hi))}
    if kind == "eval_rational":
        root = rng.choice(r["bases"])
        dens = [n for n in r["dens"] if root ** n <= 625]
        n = rng.choice(dens)
        p = rng.choice([k for k in range(1, n + 2) if math.gcd(k, n) == 1])
        if root ** p > 125:
            p = 1
        sign = -1 if rng.random() < 0.3 else 1
        return {"base": root ** n, "p": fs(F(sign * p, n))}
    if kind == "to_root":
        n = rng.choice(r["dens"])
        p = rng.choice([k for k in range(1, 2 * n) if math.gcd(k, n) == 1])
        return {"p": fs(F(p, n))}
    if kind == "to_power":
        n = rng.choice(r["dens"])
        return {"index": n, "e": rng.choice([k for k in range(1, 2 * n + 2) if k % n])}
    if kind == "rational_product":
        n1, n2 = rng.sample(r["dens"], 2) if len(r["dens"]) > 1 else (r["dens"][0], r["dens"][0])
        return {"a": mono(1, x=fs(F(rng.randint(1, n1 - 1 or 1), n1))),
                "b": mono(1, x=fs(F(rng.randint(1, n2), n2)))}
    if kind == "rational_quotient":
        n = rng.choice(r["dens"])
        top = rng.randint(n + 1, 3 * n)
        bottom = rng.randint(1, top - 1)
        return {"a": mono(1, x=fs(F(top, n))), "b": mono(1, x=fs(F(bottom, n)))}
    if kind == "rational_power":
        n = rng.choice(r["dens"])
        k = rng.choice([k for k in range(1, n + 2) if k != n])
        m = rng.choice([2, 3, 4, 6])
        return {"a": mono(1, x=fs(F(k, n))), "n": str(m)}
    if kind == "simplify_sqrt":
        return {"index": 2, "k": rng.choice(r["outs"]) ** 2 * rng.choice(r["insides"])}
    if kind == "simplify_cbrt":
        out = rng.choice([o for o in r["outs"] if o <= 5])
        return {"index": 3, "k": out ** 3 * rng.choice([i for i in r["insides"] if i <= 7 and i != 4])}
    if kind == "root_product":
        while True:
            u, v = rng.sample([2, 3, 5, 6, 7, 10, 12, 14, 15, 18, 20, 21, 27, 30], 2)
            out, inside = root_parts(2, u * v)
            if out > 1 and inside > 1:
                return {"u": u, "v": v}
    if kind == "root_vars":
        return {"k": rng.choice([2, 3, 4, 5]) ** 2 * rng.choice(r["insides"]), "e": rng.randint(2, 7)}
    raise ValueError(f"unknown exponent_rules kind {kind!r}")


def _exponents(d: dict) -> list[F]:
    return [F(v) for key in ("a", "b") if key in d for k, v in d[key].items() if k != "c"]


@register("exponent_rules")
class ExponentRules(SheetType):
    template = "exponent_rules.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        kinds = r["kinds"][: r.get("items", ITEMS)]
        items, seen = [], set()
        for n, kind in enumerate(kinds, 1):
            for _ in range(200):
                d = choose(kind, ctx.rng, r)
                shown, answer, _, _ = build(kind, d)
                if str(shown) not in seen:
                    break
            seen.add(str(shown))
            items.append({"n": n, "kind": kind, "data": d, **shown, "answer": answer})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[f"{i['n']}) {pretty_answer(i['answer'])}" for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        issues: list[Issue] = []
        kinds = r["kinds"][: r.get("items", ITEMS)]
        if [i["kind"] for i in sheet.items] != kinds:
            issues.append(error(sheet, f"items {[i['kind'] for i in sheet.items]}; this part has {kinds}"))
        if [i["n"] for i in sheet.items] != list(range(1, len(sheet.items) + 1)):
            issues.append(error(sheet, "items are not numbered 1, 2, 3… in order"))
        shown_all = []
        for i in sheet.items:
            label = f"item {i['n']} ({i['kind']})"
            try:
                shown, answer, qv, av = build(i["kind"], i["data"])
            except (ValueError, KeyError, ZeroDivisionError, TypeError) as e:
                issues.append(error(sheet, f"{label}: can't be worked out: {e}"))
                continue
            if {k: i[k] for k in ("q", "top", "bottom") if k in i} != shown:
                issues.append(error(sheet, f"{label}: the question doesn't match its numbers"))
            if i["answer"] != answer:
                issues.append(error(sheet, f"{label}: answer {i['answer']!r}, worked out {answer!r}"))
            if not math.isclose(qv, av, rel_tol=1e-9):
                issues.append(error(sheet, f"{label}: answer {answer} is not equal to the question ({qv} vs {av})"))
            if "^-" in answer or "^0" in answer:
                issues.append(error(sheet, f"{label}: answer {answer} isn't in simplest form (positive exponents)"))
            issues += self._ranges(sheet, label, i["kind"], i["data"], r)
            shown_all.append(str(shown))
        if len(set(shown_all)) != len(shown_all):
            issues.append(error(sheet, "the same expression is on the page twice"))
        expected = [f"{i['n']}) {pretty_answer(i['answer'])}" for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, "answer key doesn't match the items"))
        return issues

    def _ranges(self, sheet, label, kind, d, r) -> list[Issue]:
        out = []
        if kind in ("product", "quotient", "power", "power_product", "zero_negative", "product_negative",
                    "quotient_negative"):
            lo, hi = r["exp"]
            for e in _exponents(d):
                if e.denominator != 1 or not (abs(e) == 0 or lo <= abs(e) <= hi + 2):
                    out.append(error(sheet, f"{label}: exponent {e} is outside {lo}–{hi}"))
            if "negative" not in kind and kind != "zero_negative" and any(e < 0 for e in _exponents(d)):
                out.append(error(sheet, f"{label}: negative exponents come later in the part"))
        if kind == "eval_rational":
            p = F(d["p"])
            if p.denominator not in r["dens"] or rational_power(F(d["base"]), F(1, p.denominator)) not in r["bases"]:
                out.append(error(sheet, f"{label}: {d['base']}^{d['p']} uses a root outside {r['bases']}"))
            if rational_power(F(d["base"]), p) is None or abs(rational_power(F(d["base"]), p)) > 125:
                out.append(error(sheet, f"{label}: {d['base']}^{d['p']} is not a small rational number"))
        if kind in ("to_root", "to_power") and int(d.get("index", F(d.get("p", "1/2")).denominator)) not in r["dens"]:
            out.append(error(sheet, f"{label}: root index outside {r['dens']}"))
        if kind in ("simplify_sqrt", "simplify_cbrt"):
            o, i = root_parts(d["index"], d["k"])
            if o not in r["outs"] or i not in r["insides"]:
                out.append(error(sheet, f"{label}: {d['k']} → {o}, {i} is outside the part's numbers"))
        if kind == "root_product":
            o, i = root_parts(2, d["u"] * d["v"])
            if o == 1 or i == 1:
                out.append(error(sheet, f"{label}: the product should simplify to a whole number times a root"))
        if kind == "root_vars" and (not 2 <= d["e"] <= 7 or root_parts(2, d["k"])[1] not in r["insides"]):
            out.append(error(sheet, f"{label}: {d['k']}x^{d['e']} is outside the part's numbers"))
        return out


def pretty_answer(s: str) -> str:
    from ..algebra import pretty
    return pretty(s)

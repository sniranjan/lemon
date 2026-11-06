"""Factoring (Whales math, A-SSE.A.2, A-SSE.B.3a): factor each polynomial completely.

The generator picks the factors and multiplies them out, so every problem factors over the integers.
Each item stores the expanded problem `q` ('6x^3 + 9x^2') and the canonical `answer` ('3x^2(2x + 3)'):
the greatest common factor first (a positive number times the lowest power of x), then the other factors,
those with the bigger leading number first, then by constant; a repeated factor is written squared.
Verify multiplies the answer out and checks it equals the problem, that the outside factor is the whole
GCF, that no factor in brackets can be factored further (no common factor, no x² term with a square
discriminant), and that the numbers stay inside the part's ranges.

Rules (merged level → section → part):
- `kinds`: cycled for the page's `items` (default 8): gcf2, gcf3 (GCF times a binomial or trinomial),
  monic ((x + p)(x + q)), lead ((jx + p)(kx + q) with jk in `leads`), monic_gcf, lead_gcf (a number
  times those), squares (x² − p²), squares_lead (j²x² − p²), squares_two (j²x² − k²y²), squares_gcf.
- `root`: [lo, hi] for p and q; `leads`: leading numbers for the `lead` kinds.
"""

from __future__ import annotations

import math
import re

from ..algebra import Poly, parse, pretty
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

ITEMS = 8
_SPLIT = re.compile(r"^([^()]*)((?:\([^()]*\)(?:\^\d)?)+)$")
_GROUP = re.compile(r"\(([^()]*)\)(?:\^(\d))?")


def lin(j: int, p: int, v: str = "x", w: str | None = None) -> Poly:
    """jx + p, or jx + py when w is given."""
    second = Poly({((w, 1),): p}) if w else Poly.const(p)
    return Poly({((v, 1),): j}) + second


def _key(f: Poly):
    lead = f.terms[f._order()[0]]
    const = f.terms.get((), 0) + sum(c for m, c in f.terms.items() if m and m[0][0] != "x")
    return (-f.degree(), -lead, const)


def canonical(gcf: Poly, factors: list[Poly]) -> str:
    """'3x^2(2x + 3)', '(x - 3)(x + 5)', '2(x + 1)^2', '(3x - 2y)(3x + 2y)'."""
    counts: dict[str, int] = {}
    order: list[Poly] = []
    for f in sorted(factors, key=_key):
        t = f.text()
        if t not in counts:
            order.append(f)
        counts[t] = counts.get(t, 0) + 1
    body = "".join(f"({f.text()})" + (f"^{counts[f.text()]}" if counts[f.text()] > 1 else "") for f in order)
    g = gcf.text()
    return ("" if g == "1" else g) + body


def split(answer: str) -> tuple[Poly, list[Poly]]:
    """'3x^2(2x + 3)' → (3x², [2x + 3]); repeated factors are listed again."""
    m = _SPLIT.match(answer)
    if not m:
        raise ValueError(f"{answer!r} is not written as factors")
    gcf = parse(m.group(1)) if m.group(1).strip() else Poly.const(1)
    factors = []
    for body, power in _GROUP.findall(m.group(2)):
        factors += [parse(body)] * int(power or 1)
    return gcf, factors


def _min_x(p: Poly) -> int:
    return min(dict(m).get("x", 0) for m in p.terms)


def problems(f: Poly) -> list[str]:
    """Why a bracketed factor isn't finished: a common factor, a factor of x, a factorable quadratic."""
    out = []
    if f.content() != 1:
        out.append(f"{f.text()} still has a common factor {f.content()}")
    if _min_x(f) > 0:
        out.append(f"{f.text()} still has a factor of x")
    if f.variables() == {"x"} and f.degree() == 2:
        c0, c1, c2 = (int(c) for c in f.univariate())
        disc = c1 * c1 - 4 * c2 * c0
        if disc >= 0 and math.isqrt(disc) ** 2 == disc:
            out.append(f"{f.text()} factors further")
    if f.degree() == 2 and len(f.terms) == 2 and f.variables() == {"x", "y"}:
        out.append(f"{f.text()} factors further")
    return out


def _nz(rng, lo, hi):
    return rng.choice([k for k in range(lo, hi + 1) if k])


def choose(kind: str, rng, r: dict) -> tuple[Poly, list[Poly]]:
    lo, hi = r.get("root", [-9, 9])
    x = Poly.var("x")
    if kind in ("gcf2", "gcf3"):
        g, e = (rng.randint(2, 9), rng.randint(1, 3)) if kind == "gcf2" else (rng.randint(2, 5), rng.randint(1, 2))
        gcf = Poly.const(g) * x ** e
        while True:
            if kind == "gcf2":
                k = rng.randint(1, 2)
                inner = Poly({(("x", k),): rng.randint(1, 9), (): _nz(rng, -9, 9)})
            else:
                inner = Poly({(("x", 2),): rng.randint(1, 5), (("x", 1),): _nz(rng, -7, 7), (): _nz(rng, -7, 7)})
            if not problems(inner):
                return gcf, [inner]
    if kind in ("monic", "monic_gcf"):
        while True:
            p, q = _nz(rng, lo, hi), _nz(rng, lo, hi)
            if p + q != 0:
                break
        gcf = Poly.const(rng.randint(2, 5) if kind == "monic_gcf" else 1)
        return gcf, [lin(1, p), lin(1, q)]
    if kind in ("lead", "lead_gcf"):
        while True:
            lead = rng.choice(r["leads"])
            p, q = _nz(rng, lo, hi), _nz(rng, lo, hi)
            f1, f2 = lin(lead, p), lin(1, q)
            if math.gcd(lead, p) == 1 and (f1 * f2).content() == 1 and lead * q + p != 0:
                gcf = Poly.const(rng.randint(2, 3) if kind == "lead_gcf" else 1)
                return gcf, [f1, f2]
    if kind in ("squares", "squares_gcf"):
        p = rng.randint(1, max(hi, 2))
        gcf = Poly.const(rng.randint(2, 5) if kind == "squares_gcf" else 1)
        return gcf, [lin(1, -p), lin(1, p)]
    if kind == "squares_lead":
        while True:
            j, p = rng.randint(2, 5), rng.randint(1, 9)
            if math.gcd(j, p) == 1:
                return Poly.const(1), [lin(j, -p), lin(j, p)]
    if kind == "squares_two":
        while True:
            j, k = rng.randint(1, 5), rng.randint(1, 5)
            if math.gcd(j, k) == 1 and (j, k) != (1, 1):
                return Poly.const(1), [lin(j, -k, "x", "y"), lin(j, k, "x", "y")]
    raise ValueError(f"unknown polynomial_factoring kind {kind!r}")


def _product(gcf: Poly, factors: list[Poly]) -> Poly:
    out = gcf
    for f in factors:
        out = out * f
    return out


@register("polynomial_factoring")
class PolynomialFactoring(SheetType):
    template = "polynomial_factoring.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        items, seen = [], set()
        for n in range(1, r.get("items", ITEMS) + 1):
            kind = r["kinds"][(n - 1) % len(r["kinds"])]
            for _ in range(200):
                gcf, factors = choose(kind, ctx.rng, r)
                q = _product(gcf, factors).text()
                if q not in seen:
                    break
            seen.add(q)
            items.append({"n": n, "kind": kind, "q": q, "answer": canonical(gcf, factors)})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[f"{i['n']}) {pretty(i['answer'])}" for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        count = r.get("items", ITEMS)
        if len(sheet.items) != count:
            issues.append(error(sheet, f"{len(sheet.items)} problems; this part has {count}"))
        lo, hi = r.get("root", [-9, 9])
        for k, i in enumerate(sheet.items):
            label = f"problem {i.get('n')} ({i.get('kind')})"
            if i.get("n") != k + 1 or i["kind"] != r["kinds"][k % len(r["kinds"])]:
                issues.append(error(sheet, f"{label}: numbering or kind doesn't follow the part"))
            try:
                q = parse(i["q"])
                gcf, factors = split(i["answer"])
            except ValueError as e:
                issues.append(error(sheet, f"{label}: {e}"))
                continue
            if q.text() != i["q"]:
                issues.append(error(sheet, f"{label}: the problem isn't written in standard form"))
            if _product(gcf, factors) != q:
                issues.append(error(sheet, f"{label}: {i['answer']} doesn't multiply out to {i['q']}"))
            if canonical(gcf, factors) != i["answer"]:
                issues.append(error(sheet, f"{label}: answer isn't in the canonical order ({canonical(gcf, factors)})"))
            if len(gcf.terms) != 1 or any(c < 0 for c in gcf.terms.values()):
                issues.append(error(sheet, f"{label}: the outside factor should be one positive term"))
            for f in factors:
                for p in problems(f):
                    issues.append(error(sheet, f"{label}: not factored completely: {p}"))
            if not factors or len(factors) < 1:
                issues.append(error(sheet, f"{label}: no factors in brackets"))
            want_gcf = i["kind"] in ("gcf2", "gcf3", "monic_gcf", "lead_gcf", "squares_gcf")
            if want_gcf != (gcf != Poly.const(1)):
                issues.append(error(sheet, f"{label}: a {i['kind']} problem {'needs' if want_gcf else 'has no'} common factor"))
            consts = [int(c) for f in factors for m, c in f.terms.items() if not m or m[0][0] == "y"]
            if i["kind"] in ("monic", "monic_gcf", "lead", "lead_gcf", "squares", "squares_gcf") and \
                    any(not lo <= c <= hi for c in consts):
                issues.append(error(sheet, f"{label}: constants {consts} are outside {lo}…{hi}"))
            if i["kind"] in ("lead", "lead_gcf"):
                leads = sorted(int(f.coeff(("x", 1))) for f in factors)
                if leads[0] != 1 or leads[1] not in r["leads"]:
                    issues.append(error(sheet, f"{label}: leading numbers {leads} aren't 1 and one of {r['leads']}"))
            if i["kind"] in ("monic", "monic_gcf") and any(f.coeff(("x", 1)) != 1 for f in factors):
                issues.append(error(sheet, f"{label}: this kind has x² alone in front"))
        qs = [i["q"] for i in sheet.items]
        if len(set(qs)) != len(qs):
            issues.append(error(sheet, "the same problem is on the page twice"))
        if sheet.answer_key != [f"{i['n']}) {pretty(i['answer'])}" for i in sheet.items]:
            issues.append(error(sheet, "answer key doesn't match the problems"))
        return issues

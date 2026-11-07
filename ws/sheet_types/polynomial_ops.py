"""Polynomials: add, subtract, multiply (Whales math, A-APR.A.1).

Each item stores the problem `q` in the ASCII language of ws/algebra.py ('(2x - 3)(x + 4)') and the
canonical `answer` ('2x^2 + 5x - 12'). Verify parses `q`, multiplies it out exactly, and checks the answer,
the ranges and the box labels; nothing is taken on trust.

Rules (merged level → section → part):
- `kinds`: item kinds, cycled for the page's items: add, subtract (two trinomials up to `degree`),
  monomial (kxⁿ times a trinomial), simplify (k(x + p) − j(x + q)), binomial ((x + p)(x + q)),
  binomial_lead ((jx + p)(kx + q), j or k from 2 to 5), square ((x ± p)², (jx ± p)²), conjugate
  ((jx + p)(jx − p)), binomial_trinomial ((x + p)(x² + qx + s)).
- `layout` or `layouts` (cycled by page from the part's first page): rows (5 problems, answer line below
  each) or box (a multiplication box per problem, `box_items` a page, default 4).
- `coeff`: [lo, hi] for every coefficient and constant typed into a problem.
"""

from __future__ import annotations

from ..algebra import Poly, parse, pretty
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, nonzero_choice

ROW_ITEMS = 5
BOX_ITEMS = 4


def lin(j: int, p: int) -> str:
    return Poly({(("x", 1),): j, (): p}).text()


def term_texts(s: str) -> list[str]:
    """'2x^2 - 3x + 1' → ['2x^2', '-3x', '1'] (the box labels)."""
    p = parse(s)
    out = []
    for t in Poly(p.terms)._order():
        out.append(Poly({t: p.terms[t]}).text())
    return out


def layout_for(r: dict, page: int, first: int) -> str:
    if "layouts" in r:
        return r["layouts"][(page - first) % len(r["layouts"])]
    return r.get("layout", "rows")


def choose(kind: str, rng, r: dict) -> dict:
    lo, hi = r.get("coeff", [-9, 9])
    nz = lambda a=lo, b=hi: nonzero_choice(rng, a, b)
    if kind in ("add", "subtract"):
        def tri():
            return Poly({(("x", 2),): rng.randint(1, hi), (("x", 1),): nz(), (): nz()}).text()
        op = "+" if kind == "add" else "-"
        return {"q": f"({tri()}) {op} ({tri()})"}
    if kind == "monomial":
        k, e = nonzero_choice(rng, -6, 6), rng.choice([1, 1, 2])
        while k in (1, -1):
            k = nonzero_choice(rng, -6, 6)
        mono = Poly({(("x", e),): k}).text()
        tri = Poly({(("x", 2),): rng.randint(1, 6), (("x", 1),): nz(), (): nz()}).text()
        return {"q": f"{mono}({tri})"}
    if kind == "simplify":
        k, j = rng.randint(2, 6), rng.randint(2, 6)
        return {"q": f"{k}({lin(1, nz())}) - {j}({lin(1, nz())})"}
    if kind == "binomial":
        return {"q": f"({lin(1, nz())})({lin(1, nz())})"}
    if kind == "binomial_lead":
        j, k = rng.choice([(rng.randint(2, 5), 1), (1, rng.randint(2, 5)), (rng.randint(2, 3), rng.randint(2, 3))])
        return {"q": f"({lin(j, nz(-7, 7))})({lin(k, nz(-7, 7))})"}
    if kind == "square":
        j = rng.choice([1, 1, 2, 3])
        return {"q": f"({lin(j, nz())})^2"}
    if kind == "conjugate":
        j, p = rng.choice([1, 1, 2, 3, 4]), rng.randint(1, hi)
        pair = [lin(j, p), lin(j, -p)]
        rng.shuffle(pair)
        return {"q": f"({pair[0]})({pair[1]})"}
    if kind == "binomial_trinomial":
        tri = Poly({(("x", 2),): rng.choice([1, 1, 2]), (("x", 1),): nz(-6, 6), (): nz(-6, 6)}).text()
        return {"q": f"({lin(rng.choice([1, 1, 2]), nz(-6, 6))})({tri})"}
    raise ValueError(f"unknown polynomial_ops kind {kind!r}")


def box_labels(q: str) -> dict | None:
    """Row and column labels of the multiplication box for '(A)(B)' or '(A)^2'."""
    if q.endswith(")^2"):
        a = q[1:-3]
        return {"rows": term_texts(a), "cols": term_texts(a)}
    if q.startswith("(") and ")(" in q and q.endswith(")"):
        a, b = q[1:-1].split(")(")
        if len(term_texts(a)) > len(term_texts(b)):
            a, b = b, a
        return {"rows": term_texts(a), "cols": term_texts(b)}
    return None


def numbers_in(q: str) -> list[int]:
    import re
    return [int(n) for n in re.findall(r"(?<![\^\d])(\d+)", q)]


@register("polynomial_ops")
class PolynomialOps(SheetType):
    template = "polynomial_ops.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        from ..syllabus import load_level
        level = load_level(ctx.spec.subject, ctx.spec.level)
        part = level.section(ctx.spec.section).part_for_page(ctx.spec.page)
        layout = layout_for(r, ctx.spec.page, part.pages[0] if part else ctx.spec.page)
        count = r.get("box_items", BOX_ITEMS) if layout == "box" else r.get("items", ROW_ITEMS)
        items, seen = [], set()
        for n in range(1, count + 1):
            kind = r["kinds"][(n - 1) % len(r["kinds"])]
            for _ in range(200):
                q = choose(kind, ctx.rng, r)["q"]
                if q not in seen:
                    break
            seen.add(q)
            item = {"n": n, "kind": kind, "q": q, "answer": parse(q).text()}
            if layout == "box":
                item["box"] = box_labels(q)
            items.append(item)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name),
                            items=[{"layout": layout, **i} for i in items],
                            answer_key=[f"{i['n']}) {pretty(i['answer'])}" for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        level = load_level(sheet.subject, sheet.level)
        r = resolve_page(level, sheet.page_number).rules
        part = level.section(sheet.section).part_for_page(sheet.page_number)
        layout = layout_for(r, sheet.page_number, part.pages[0] if part else sheet.page_number)
        count = r.get("box_items", BOX_ITEMS) if layout == "box" else r.get("items", ROW_ITEMS)
        issues: list[Issue] = []
        if len(sheet.items) != count:
            issues.append(error(sheet, f"{len(sheet.items)} problems; a {layout} page has {count}"))
        lo, hi = r.get("coeff", [-9, 9])
        for k, i in enumerate(sheet.items):
            label = f"problem {i.get('n')} ({i.get('kind')})"
            if i.get("n") != k + 1 or i.get("layout") != layout:
                issues.append(error(sheet, f"{label}: numbering or layout is wrong"))
            if i["kind"] != r["kinds"][k % len(r["kinds"])]:
                issues.append(error(sheet, f"{label}: this part has {r['kinds'][k % len(r['kinds'])]} here"))
            try:
                worked = parse(i["q"])
            except ValueError as e:
                issues.append(error(sheet, f"{label}: {e}"))
                continue
            if i["answer"] != worked.text() or parse(i["answer"]) != worked:
                issues.append(error(sheet, f"{label}: answer {i['answer']!r}, worked out {worked.text()!r}"))
            if any(c.denominator != 1 for c in worked.terms.values()) or worked.variables() - {"x"}:
                issues.append(error(sheet, f"{label}: answers use whole numbers and x only"))
            if worked.degree() > 4:
                issues.append(error(sheet, f"{label}: degree {worked.degree()} is too high for this level"))
            big = [n for n in numbers_in(i["q"]) if not (lo <= n <= hi) and not -n >= lo]
            if big:
                issues.append(error(sheet, f"{label}: numbers {big} are outside {lo}…{hi}"))
            if layout == "box":
                box = i.get("box")
                if not box or box != box_labels(i["q"]):
                    issues.append(error(sheet, f"{label}: box labels don't match the problem"))
                else:
                    product = parse("+".join(f"({t})" for t in box["rows"])) * parse("+".join(f"({t})" for t in box["cols"]))
                    if product != worked:
                        issues.append(error(sheet, f"{label}: the box doesn't multiply out to the problem"))
            elif "box" in i:
                issues.append(error(sheet, f"{label}: a rows page has no box"))
        qs = [i["q"] for i in sheet.items]
        if len(set(qs)) != len(qs):
            issues.append(error(sheet, "the same problem is on the page twice"))
        expected = [f"{i['n']}) {pretty(i['answer'])}" for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, "answer key doesn't match the problems"))
        return issues

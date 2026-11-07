"""Adding and taking away decimals in columns, points lined up (Otters math, 5.NBT.7).

Each item is one problem: two decimals to hundredths written one above the other with their
points in one column. Numbers keep the places they were written with (3.5 over 12.47), so the
child sees why the points, not the last digits, line up. Rules (merged level → section → part):
- `op`: add | sub | mixed (half each way). `a`, `b`: ["lo", "hi"] as decimal strings.
- `ragged_min`: at least this many problems whose numbers have different numbers of places.
- `whole_top_min` (taking away): at least this many top numbers are whole (5 − 2.36).
- `answer_point` (default true): print the point in the answer row; false leaves it for the child.
- `problems` (default 6), `title`.
Each item stores `cols`: [whole-number columns, decimal columns] for the page grid. Answers are
canonical decimals ("2.64", "5").
"""

from __future__ import annotations

from decimal import Decimal

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules
from ._exact import dec, dec_str, from_hundredths, places

PROBLEMS = 6
MAX_TRIES = 20000
SIGN = {"add": "+", "sub": "−"}


def answer(item: dict) -> Decimal:
    a, b = dec(item["a"]), dec(item["b"])
    return a + b if item["op"] == "add" else a - b


def cols(a: str, b: str, ans: Decimal) -> list[int]:
    whole = max(len(str(int(Decimal(x)))) for x in (a, b, dec_str(ans)))
    return [whole, max(places(a), places(b))]


def problem_ok(r: dict, item: dict) -> str | None:
    op, a, b = item["op"], item["a"], item["b"]
    allowed = ("add", "sub") if r["op"] == "mixed" else (r["op"],)
    if op not in allowed:
        return f"{op} isn't used in this part"
    da, db = dec(a), dec(b)
    for x, (lo, hi), name in ((da, r["a"], "top"), (db, r["b"], "other")):
        if not Decimal(lo) <= x <= Decimal(hi):
            return f"{name} number {dec_str(x)} is outside {lo}–{hi}"
        if places(dec_str(x)) > 2:
            return f"{dec_str(x)} has more than 2 decimal places"
    if places(a) == 0 and places(b) == 0:
        return "neither number is a decimal"
    ans = answer(item)
    if ans <= 0:
        return f"answer {dec_str(ans)} isn't more than 0"
    if item.get("cols") != cols(a, b, ans):
        return f"columns {item.get('cols')} should be {cols(a, b, ans)}"
    return None


def _number(rng, lo: str, hi: str, p: int) -> str:
    lo_n, hi_n = int(Decimal(lo).scaleb(p).to_integral_value()), int(Decimal(hi).scaleb(p))
    while True:
        n = rng.randint(max(lo_n, 1), hi_n)
        if p == 0 or n % 10:   # keep the places it was written with (no 3.50)
            return dec_str(from_hundredths(n, p))


@register("decimal_column")
class DecimalColumn(SheetType):
    template = "decimal_column.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        n = r.get("problems", PROBLEMS)
        ops = [r["op"]] * n if r["op"] != "mixed" else ["add"] * ((n + 1) // 2) + ["sub"] * (n // 2)
        rng.shuffle(ops)
        ragged = [k < r.get("ragged_min", 0) for k in range(n)]
        rng.shuffle(ragged)
        subs = [k for k, op in enumerate(ops) if op == "sub"]
        whole_top = set(subs[:r.get("whole_top_min", 0)])
        items, seen = [], set()
        for k, (op, rag) in enumerate(zip(ops, ragged)):
            for _ in range(MAX_TRIES):
                if k in whole_top:
                    pa, pb = 0, rng.choice([1, 2])
                elif rag:
                    pa, pb = rng.sample([0, 1, 2] if k % 2 else [1, 2], 2)
                else:
                    pa = pb = rng.choice([1, 2])
                a, b = _number(rng, *r["a"], pa), _number(rng, *r["b"], pb)
                if op == "sub" and Decimal(a) < Decimal(b) and k not in whole_top:
                    a, b = b, a
                item = {"kind": "decimal_column", "op": op, "sign": SIGN[op], "a": a, "b": b,
                        "point": r.get("answer_point", True)}
                if op == "sub" and Decimal(a) <= Decimal(b):
                    continue
                item["cols"] = cols(a, b, answer(item))
                if (op, a, b) not in seen and problem_ok(r, item) is None:
                    break
            else:
                raise ValueError(f"decimal_column: can't find a {op} problem with these rules: {r}")
            seen.add((op, a, b))
            items.append(item)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[dec_str(answer(i)) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        issues: list[Issue] = []
        n = r.get("problems", PROBLEMS)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} problems; the part asks for {n}"))
        seen = set()
        for k, i in enumerate(sheet.items, 1):
            try:
                why = problem_ok(r, i)
            except Exception as e:
                why = repr(e)
            if why:
                issues.append(error(sheet, f"problem {k} ({i['a']} {i['sign']} {i['b']}): {why}"))
            if i.get("sign") != SIGN.get(i["op"]):
                issues.append(error(sheet, f"problem {k}: sign {i.get('sign')!r} doesn't match {i['op']}"))
            if i.get("point") != r.get("answer_point", True):
                issues.append(error(sheet, f"problem {k}: answer point shown must be {r.get('answer_point', True)}"))
            if (i["op"], i["a"], i["b"]) in seen:
                issues.append(error(sheet, f"problem {k} appears twice"))
            seen.add((i["op"], i["a"], i["b"]))
        if r["op"] == "mixed" and {i["op"] for i in sheet.items} != {"add", "sub"}:
            issues.append(error(sheet, "a mixed page needs both adding and taking away"))
        ragged = sum(places(i["a"]) != places(i["b"]) for i in sheet.items)
        if ragged < r.get("ragged_min", 0):
            issues.append(error(sheet, f"{ragged} problems mix places; this part needs {r['ragged_min']}"))
        whole_top = sum(i["op"] == "sub" and places(i["a"]) == 0 for i in sheet.items)
        if whole_top < r.get("whole_top_min", 0):
            issues.append(error(sheet, f"{whole_top} take-aways from a whole number; this part needs {r['whole_top_min']}"))
        try:
            expected = [dec_str(answer(i)) for i in sheet.items]
        except Exception as e:
            return issues + [error(sheet, f"can't work out the answers: {e!r}")]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues

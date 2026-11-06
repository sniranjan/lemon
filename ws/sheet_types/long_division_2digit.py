"""Long division by a two-digit number (Otters math, 5.NBT.6): up to four-digit dividends.

Each item is one problem written with the long-division bracket: the divisor on the left, the
dividend under the bar, a row of digit boxes above it for the answer and a squared work area
below (two rows per answer digit of the part's longest answer, the same on every problem: the product and what is left after taking it away).

Rules (merged level → section → part):
- `divisor`: [lo, hi]; `divisor_multiple_of` (optional, e.g. 10 for 20, 30 … 90).
- `dividend_digits`: 3 or 4. `quotient_digits`: allowed digit counts of the answer, e.g. [1] or [2, 3].
- `remainder`: none | all | mixed (mixed: about half the problems leave a remainder).
- `zero_in_quotient` (optional): at least this many answers have a 0 digit inside or at the end (2163 ÷ 21 = 103).
- `problems`: problems per page (default 4). `title`: the sheet title.
Answers read "36" or "36 R 12" (with spaces: R5 alone would look like an internal code).
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

PROBLEMS = 4
MAX_TRIES = 20000


def answer_text(dividend: int, divisor: int) -> str:
    q, r = divmod(dividend, divisor)
    return f"{q} R {r}" if r else str(q)


def has_inner_zero(q: int) -> bool:
    return len(str(q)) > 1 and "0" in str(q)[1:]


def problem_ok(r: dict, divisor: int, dividend: int, want_rem: bool | None) -> str | None:
    lo, hi = r["divisor"]
    if not lo <= divisor <= hi or not 10 <= divisor <= 99:
        return f"divisor {divisor} is outside {lo}–{hi}"
    if r.get("divisor_multiple_of") and divisor % r["divisor_multiple_of"]:
        return f"divisor {divisor} isn't a multiple of {r['divisor_multiple_of']}"
    if len(str(dividend)) != r["dividend_digits"]:
        return f"dividend {dividend} doesn't have {r['dividend_digits']} digits"
    q, rem = divmod(dividend, divisor)
    if len(str(q)) not in r["quotient_digits"] or q < 2:
        return f"answer {q} doesn't have {r['quotient_digits']} digits"
    if want_rem is True and rem == 0:
        return "has no remainder"
    if want_rem is False and rem:
        return f"leaves a remainder of {rem}"
    mode = r.get("remainder", "none")
    if mode == "none" and rem:
        return f"leaves a remainder of {rem}; this part has none"
    if mode == "all" and not rem:
        return "has no remainder; every problem here has one"
    return None


@register("long_division_2digit")
class LongDivision2Digit(SheetType):
    template = "long_division_2digit.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        n = r.get("problems", PROBLEMS)
        mode = r.get("remainder", "none")
        wants = {"none": [False] * n, "all": [True] * n}.get(mode) or \
            [True] * ((n + 1) // 2) + [False] * (n // 2)
        rng.shuffle(wants)
        zeros = r.get("zero_in_quotient", 0)
        qdigits = list(r["quotient_digits"])
        items, seen = [], set()
        for k, want in enumerate(wants):
            need_zero = k < zeros
            nd = qdigits[k % len(qdigits)]
            for _ in range(MAX_TRIES):
                divisor = rng.randint(*r["divisor"])
                if r.get("divisor_multiple_of"):
                    divisor -= divisor % r["divisor_multiple_of"]
                q = rng.randint(10 ** (nd - 1), 10 ** nd - 1)
                if need_zero:
                    s = list(str(q))
                    s[rng.randint(1, len(s) - 1)] = "0"
                    q = int("".join(s))
                rem = rng.randint(1, divisor - 1) if want else 0
                dividend = q * divisor + rem
                if (divisor, dividend) not in seen and problem_ok(r, divisor, dividend, want) is None \
                        and (not need_zero or has_inner_zero(q)):
                    break
            else:
                raise ValueError(f"long_division_2digit: can't find a problem with these rules: {r}")
            seen.add((divisor, dividend))
            items.append({"kind": "division", "divisor": divisor, "dividend": dividend})
        rng.shuffle(items)
        for i, item in enumerate(items, 1):
            item["n"] = i
            item["work_rows"] = 2 * max(qdigits)   # same on every problem: no hint at the answer's size
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer_text(i["dividend"], i["divisor"]) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        n = r.get("problems", PROBLEMS)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} problems; the part asks for {n}"))
        if [i.get("n") for i in sheet.items] != list(range(1, len(sheet.items) + 1)):
            issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
        seen, rems, zeros = set(), [], 0
        for i in sheet.items:
            d, D = i["divisor"], i["dividend"]
            why = problem_ok(r, d, D, None)
            if why:
                issues.append(error(sheet, f"{D} ÷ {d}: {why}"))
            q, rem = divmod(D, d)
            if q * d + rem != D or not 0 <= rem < d:   # belt and braces: the key must recombine
                issues.append(error(sheet, f"{D} ÷ {d}: answer doesn't recombine"))
            if i.get("work_rows") != 2 * max(r["quotient_digits"]):
                issues.append(error(sheet, f"{D} ÷ {d}: work area needs {2 * max(r['quotient_digits'])} rows"))
            if (d, D) in seen:
                issues.append(error(sheet, f"{D} ÷ {d} appears twice"))
            seen.add((d, D))
            rems.append(rem > 0)
            zeros += has_inner_zero(q)
        if r.get("remainder") == "mixed" and len(sheet.items) > 1 and (all(rems) or not any(rems)):
            issues.append(error(sheet, "a mixed page needs problems with and without a remainder"))
        if zeros < r.get("zero_in_quotient", 0):
            issues.append(error(sheet, f"{zeros} answers have a 0 inside; this part needs {r['zero_in_quotient']}"))
        expected = [answer_text(i["dividend"], i["divisor"]) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues

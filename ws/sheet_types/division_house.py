"""Long division in the division house (Owls math, 4.NBT.6): up to four-digit numbers divided by one digit,
with remainders.

The number to share sits under the roof, the divisor on the left; the child writes the answer digits in
boxes on the roof and works the divide, multiply, take away, bring down steps in squared space below.

Rules (merged level → section → part):
- `dividend`, `divisor`, `quotient`: [lo, hi] ranges. The divisor range is a rule, not fixed to one digit
  (Otters math, 5.NBT.6, uses two-digit divisors). `divisor_multiple_of` (optional, Otters): divisors are
  multiples of this (10: dividing by 20, 30 … 90).
- `remainder`: none (every problem divides evenly), all (every problem has one), mixed (both on every page).
  Parts with remainders show an "R" box after the answer boxes.
- `small_first`: at least this many problems whose first digit is smaller than the divisor (156 ÷ 4),
  so the answer starts over the second digit.
- `zero_in_quotient`: at least this many answers with a 0 inside (832 ÷ 4 = 208).
- `problems`: problems a page (4 → 2 × 2; 2 → side by side with more room to work). `title`.

Each item stores whole numbers only. `start` is the dividend digit (0 = leftmost) the answer starts over:
the first digit where the digits so far make at least the divisor. The answer has one box for each
dividend digit from `start` on, so its digits line up over the digits they come from.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

REMAINDERS = ("none", "all", "mixed")
MAX_TRIES = 20000


def start(dividend: int, divisor: int) -> int:
    s = str(dividend)
    for k in range(len(s)):
        if int(s[: k + 1]) >= divisor:
            return k
    raise ValueError(f"{dividend} is smaller than {divisor}")


def zero_inside(quotient: int) -> bool:
    return "0" in str(quotient)[1:]


def answer_text(item: dict) -> str:
    q = str(item["quotient"])
    return f"{q} R {item['remainder']}" if item["r_box"] else q


def problem_ok(r: dict, dividend: int, divisor: int, quotient: int, remainder: int) -> str | None:
    if r.get("divisor_multiple_of") and divisor % r["divisor_multiple_of"]:
        return f"divisor {divisor} isn't a multiple of {r['divisor_multiple_of']}"
    for name, value in (("dividend", dividend), ("divisor", divisor), ("quotient", quotient)):
        lo, hi = r[name]
        if not lo <= value <= hi:
            return f"{name} {value} is outside {lo}–{hi}"
    if quotient * divisor + remainder != dividend:
        return f"{quotient} × {divisor} + {remainder} isn't {dividend}"
    if not 0 <= remainder < divisor:
        return f"remainder {remainder} must be smaller than {divisor}"
    mode = r.get("remainder", "none")
    if mode == "none" and remainder:
        return "this part divides evenly, with nothing left over"
    if mode == "all" and not remainder:
        return "this part always has a remainder"
    return None


def _flags(n: int, count: int, rng) -> list[bool]:
    flags = [True] * min(count, n) + [False] * max(0, n - count)
    rng.shuffle(flags)
    return flags


@register("division_house")
class DivisionHouse(SheetType):
    template = "division_house.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        mode = r.get("remainder", "none")
        if mode not in REMAINDERS:
            raise ValueError(f"division_house: unknown remainder {mode!r} (use one of {', '.join(REMAINDERS)})")
        n = r.get("problems", 4)
        rems = {"none": [False] * n, "all": [True] * n}.get(mode) or _flags(n, (n + 1) // 2, rng)
        smalls = _flags(n, r.get("small_first", 0), rng)
        zeros = _flags(n, r.get("zero_in_quotient", 0), rng)
        items, seen = [], set()
        for want_rem, small, zero in zip(rems, smalls, zeros):
            for _ in range(MAX_TRIES):
                # divisor first, then an answer that fits: every divisor turns up, not just the small ones
                d = rng.randint(*r["divisor"])
                if r.get("divisor_multiple_of"):   # Otters: dividing by tens (no extra RNG call, so Owls is unchanged)
                    d -= d % r["divisor_multiple_of"]
                rem = rng.randint(1, d - 1) if want_rem else 0
                q_lo = max(r["quotient"][0], -(-(r["dividend"][0] - rem) // d))
                q_hi = min(r["quotient"][1], (r["dividend"][1] - rem) // d)
                if q_lo > q_hi:
                    continue
                q = rng.randint(q_lo, q_hi)
                big = q * d + rem
                if (big, d) in seen or problem_ok(r, big, d, q, rem) is not None:
                    continue
                if small and start(big, d) != 1 or zero and not zero_inside(q):
                    continue
                break
            else:
                raise ValueError(f"division_house: can't find a problem with these rules: {r}")
            seen.add((big, d))
            items.append({"kind": "divide", "dividend": big, "divisor": d, "quotient": q, "remainder": rem,
                          "start": start(big, d), "r_box": mode != "none"})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer_text(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        mode = r.get("remainder", "none")
        n = r.get("problems", 4)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} problems; the part asks for {n}"))
        seen = set()
        for i in sheet.items:
            big, d, q, rem = i["dividend"], i["divisor"], i["quotient"], i["remainder"]
            label = f"{big} ÷ {d}"
            why = problem_ok(r, big, d, q, rem)
            if why:
                issues.append(error(sheet, f"{label}: {why}"))
            if big >= d and i["start"] != start(big, d):
                issues.append(error(sheet, f"{label}: the answer must start over digit {start(big, d) + 1}"))
            if len(str(q)) != len(str(big)) - i["start"]:
                issues.append(error(sheet, f"{label}: {q} doesn't line up over the digits of {big}"))
            if i["r_box"] != (mode != "none"):
                issues.append(error(sheet, f"{label}: the R box shows exactly on remainder parts"))
            if (big, d) in seen:
                issues.append(error(sheet, f"{label} appears twice"))
            seen.add((big, d))
        if mode == "mixed" and len({i["remainder"] > 0 for i in sheet.items}) < 2:
            issues.append(error(sheet, "a mixed page needs problems with and without a remainder"))
        smalls = sum(i["start"] == 1 for i in sheet.items)
        if smalls < r.get("small_first", 0):
            issues.append(error(sheet, f"{smalls} problems start over the second digit; the part needs {r['small_first']}"))
        zeros = sum(zero_inside(i["quotient"]) for i in sheet.items)
        if zeros < r.get("zero_in_quotient", 0):
            issues.append(error(sheet, f"{zeros} answers have a 0 inside; the part needs {r['zero_in_quotient']}"))
        expected = [answer_text(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues

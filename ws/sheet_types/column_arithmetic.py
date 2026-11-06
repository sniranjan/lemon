"""Cubs math (M2-D…H): vertical column adding and taking away, with carry / borrow boxes.

Rules (merged level → section → part):
- `op`: add | sub | mixed (mixed: half the problems each way).
- `a`, `b`: [lo, hi] for the top number and for the other number(s). `addends`: 2 or 3 (adding only).
- `max_answer` (optional), `min_answer` (default 1, so never a negative or a zero answer).
- `regroup`: none (no column carries or borrows), all (every problem regroups), mixed (some do,
  some don't). `max_regroups` (default 1): how many columns may regroup in one problem, so
  borrowing across a zero (402 − 158) never turns up.
- `problems`: problems per page (default 6; 4 for three-digit pages).

Regrouping parts show small dashed boxes above the columns: one above each column a carry can
land in (adding), or one above every digit of the top number (taking away, for the new digit
after breaking a ten). Parts without regrouping show no boxes.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

OPS = ("add", "sub", "mixed")
REGROUPS = ("none", "all", "mixed")
SIGN = {"add": "+", "sub": "−"}
MAX_TRIES = 20000


def digit(n: int, col: int) -> int:
    return n // 10 ** col % 10


def answer(op: str, numbers: list[int]) -> int:
    return sum(numbers) if op == "add" else numbers[0] - sum(numbers[1:])


def regroups(op: str, numbers: list[int]) -> int:
    """How many columns carry (adding) or need a ten broken (taking away), right to left."""
    width = max(len(str(n)) for n in numbers)
    count = carry = 0
    for col in range(width):
        if op == "add":
            carry = (sum(digit(n, col) for n in numbers) + carry) // 10
            count += carry > 0
        else:
            top = digit(numbers[0], col) - carry
            carry = int(top < digit(numbers[1], col))
            count += carry
    return count


def _ops(rules: dict, n: int, rng) -> list[str]:
    op = rules["op"]
    if op not in OPS:
        raise ValueError(f"column_arithmetic: unknown op {op!r} (use one of {', '.join(OPS)})")
    if op != "mixed":
        return [op] * n
    ops = ["add"] * ((n + 1) // 2) + ["sub"] * (n // 2)
    rng.shuffle(ops)
    return ops


def _wants(rules: dict, n: int, rng) -> list[bool]:
    """Which problems must regroup."""
    mode = rules.get("regroup", "none")
    if mode not in REGROUPS:
        raise ValueError(f"column_arithmetic: unknown regroup {mode!r} (use one of {', '.join(REGROUPS)})")
    if mode != "mixed":
        return [mode == "all"] * n
    wants = [True] * ((n + 1) // 2) + [False] * (n // 2)
    rng.shuffle(wants)
    return wants


def problem_ok(rules: dict, op: str, numbers: list[int], must_regroup: bool | None) -> str | None:
    """Why this problem breaks the part's rules, or None. `must_regroup` None = either is fine."""
    lo_a, hi_a = rules["a"]
    lo_b, hi_b = rules["b"]
    if not lo_a <= numbers[0] <= hi_a:
        return f"top number {numbers[0]} is outside {lo_a}–{hi_a}"
    for n in numbers[1:]:
        if not lo_b <= n <= hi_b:
            return f"number {n} is outside {lo_b}–{hi_b}"
    want_n = rules.get("addends", 2) if op == "add" else 2
    if len(numbers) != want_n:
        return f"{len(numbers)} numbers; the part asks for {want_n}"
    ans = answer(op, numbers)
    if ans < rules.get("min_answer", 1):
        return f"answer {ans} is below {rules.get('min_answer', 1)}"
    if "max_answer" in rules and ans > rules["max_answer"]:
        return f"answer {ans} is above {rules['max_answer']}"
    r = regroups(op, numbers)
    if r > rules.get("max_regroups", 1):
        return f"regroups in {r} columns (at most {rules.get('max_regroups', 1)})"
    if must_regroup is True and r == 0:
        return "doesn't regroup, but this part is about regrouping"
    if must_regroup is False and r > 0:
        return "regroups, but this part has no regrouping"
    return None


def columns(rules: dict) -> int:
    """Digit columns every problem on the page uses (the widest number the part allows)."""
    widest = max(rules["a"][1], rules["b"][1], rules.get("max_answer", 0))
    return len(str(widest))


@register("column_arithmetic")
class ColumnArithmetic(SheetType):
    template = "column_arithmetic.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        n = r.get("problems", 6)
        ops, wants = _ops(r, n, rng), _wants(r, n, rng)
        boxes = r.get("regroup", "none") != "none"
        cols = columns(r)
        items, seen = [], set()
        for op, want in zip(ops, wants):
            k = r.get("addends", 2) if op == "add" else 2
            for _ in range(MAX_TRIES):
                numbers = [rng.randint(*r["a"])] + [rng.randint(*r["b"]) for _ in range(k - 1)]
                key = (op, tuple(numbers))
                if key not in seen and problem_ok(r, op, numbers, want) is None:
                    break
            else:
                raise ValueError(f"column_arithmetic: can't find a {op} problem with these rules: {r}")
            seen.add(key)
            items.append({"kind": "column", "op": op, "sign": SIGN[op], "numbers": numbers,
                          "cols": cols, "boxes": boxes})
        title = {"add": "Adding", "sub": "Taking away", "mixed": "Add and take away"}[r["op"]]
        if r.get("addends", 2) == 3:
            title = "Adding three numbers"
        return SheetContent(title=title, parent_tip=ctx.tip(self.tip_key(r)), items=items,
                            answer_key=[answer(i["op"], i["numbers"]) for i in items])

    @staticmethod
    def tip_key(r: dict) -> str:
        if r.get("addends", 2) == 3:
            return "column_add_three"
        regroup = "" if r.get("regroup", "none") == "none" else "_regroup"
        return f"column_{r['op']}{regroup}"

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues = []
        n = r.get("problems", 6)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} problems; the part asks for {n}"))
        mode = r.get("regroup", "none")
        flags, keys, answers = [], set(), []
        for i in sheet.items:
            op, numbers = i["op"], i["numbers"]
            if r["op"] != "mixed" and op != r["op"]:
                issues.append(error(sheet, f"{op} problem on a {r['op']} page"))
            if i["sign"] != SIGN.get(op):
                issues.append(error(sheet, f"sign {i['sign']!r} doesn't match {op}"))
            why = problem_ok(r, op, numbers, {"none": False, "all": True}.get(mode))
            if why:
                shown = f" {i['sign']} ".join(map(str, numbers))
                issues.append(error(sheet, f"{shown}: {why}"))
            if i["boxes"] != (mode != "none"):
                issues.append(error(sheet, "carry/borrow boxes must show exactly on regrouping parts"))
            width = max(len(str(x)) for x in [*numbers, answer(op, numbers)])
            if i["cols"] < width:
                issues.append(error(sheet, f"{i['cols']} columns can't hold {numbers}"))
            key = (op, tuple(numbers))
            if key in keys:
                issues.append(error(sheet, f"problem {numbers} appears twice"))
            keys.add(key)
            flags.append(regroups(op, numbers) > 0)
            answers.append(answer(op, numbers))
        if mode == "mixed" and (all(flags) or not any(flags)):
            issues.append(error(sheet, "a mixed page needs problems with and without regrouping"))
        if r["op"] == "mixed" and len({i["op"] for i in sheet.items}) < 2:
            issues.append(error(sheet, "a mixed page needs both adding and taking away"))
        if sheet.answer_key != answers:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {answers}"))
        return issues

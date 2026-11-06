"""Column adding and taking away with regrouping (Foxes math: 3-digit numbers within 1000, 3.NBT.2).

Each problem is written in columns, `a` over `op b`, with a ruled line and one answer box per
digit, plus small boxes above the columns for the carried or traded ten / hundred. Rules
(merged level → section → part):
- `ops`: "+" and/or "-" (ASCII in items; the template prints a real minus sign).
- `first`, `second`: [lo, hi] ranges for `a` and `b`. `max_total`: no sum above it.
  Taking away never goes below 0.
- `regroups`: how many places a problem may regroup in (0, 1, 2…). Every count in the list is on
  every page (when the page has room), so a page with `[0, 1, 2]` mixes "no trade" problems in.
- `across_zero`: at least this many taking-away problems on the page have a 0 in the tens of the
  top number and need a trade from the ones (402 − 168), so the trade goes through the zero.
- `count`: problems per page (default 9, a 3 × 3 grid). `title`: the sheet title.

Problems are numbered `n` in reading order (left to right, top to bottom, shown small for
grown-ups); `answer_key` lists the answers in that order.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

COUNT = 9
MAX_TRIES = 2000


def digits(n: int, width: int) -> list[int]:
    """Digits of n from the ones up, padded to `width`."""
    return [(n // 10 ** i) % 10 for i in range(width)]


def value(a: int, op: str, b: int) -> int:
    return a + b if op == "+" else a - b


def regroup_count(a: int, op: str, b: int) -> int:
    """How many columns carry (adding) or trade (taking away), worked from the ones."""
    width = max(len(str(a)), len(str(b)))
    da, db = digits(a, width), digits(b, width)
    n, carry = 0, 0
    for x, y in zip(da, db):
        if op == "+":
            carry = 1 if x + y + carry >= 10 else 0
            n += carry
        else:
            carry = 1 if x - carry < y else 0
            n += carry
    return n


def across_zero(a: int, op: str, b: int) -> bool:
    """Taking away where the ones need a trade and the top number has 0 tens (402 − 168)."""
    return op == "-" and a >= 100 and (a // 10) % 10 == 0 and a % 10 < b % 10


def problem_ok(p: dict, r: dict) -> str | None:
    a, op, b = p["a"], p["op"], p["b"]
    label = f"{a} {op} {b}"
    if op not in r["ops"]:
        return f"sign {op!r} isn't used in this part (only {r['ops']})"
    lo, hi = r["first"]
    if not lo <= a <= hi:
        return f"{label}: first number outside {lo}–{hi}"
    lo, hi = r["second"]
    if not lo <= b <= hi:
        return f"{label}: second number outside {lo}–{hi}"
    c = value(a, op, b)
    if c < 0:
        return f"{label} is below zero"
    if c > r.get("max_total", 999):
        return f"{label} = {c} is above {r.get('max_total', 999)}"
    k = regroup_count(a, op, b)
    if k not in r["regroups"]:
        return f"{label} regroups in {k} places; this part uses {r['regroups']}"
    return None


def _draw(ctx: GenContext, op: str, k: int, zero: bool) -> tuple[int, str, int]:
    r = ctx.rules
    for _ in range(MAX_TRIES):
        a = ctx.rng.randint(*r["first"])
        if zero:   # a 0 in the tens, and ones that need a trade
            a = a // 100 * 100 + ctx.rng.randint(0, 8)
        b = ctx.rng.randint(*r["second"])
        p = {"a": a, "op": op, "b": b}
        if problem_ok(p, r) is None and regroup_count(a, op, b) == k and (not zero or across_zero(a, op, b)):
            return a, op, b
    raise ValueError(f"column_arithmetic: no {op} problem with {k} regroups fits this part")


@register("column_arithmetic")
class ColumnArithmetic(SheetType):
    template = "column_arithmetic.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        count = r.get("count", COUNT)
        # one slot per problem: a sign, a regroup count and whether it trades across a zero.
        # The across-zero slots come first; the rest cycle through every sign and every count.
        zeros = r.get("across_zero", 0)
        if zeros and ("-" not in r["ops"] or 2 not in r["regroups"]):
            raise ValueError("column_arithmetic: across_zero needs '-' and 2 regroups in the part")
        rest = count - zeros
        ops = [r["ops"][i % len(r["ops"])] for i in range(rest)]
        ks = [r["regroups"][i % len(r["regroups"])] for i in range(rest)]
        ctx.rng.shuffle(ks)
        slots = [("-", 2, True)] * zeros + [(op, k, False) for op, k in zip(ops, ks)]
        ctx.rng.shuffle(slots)
        picked: list[tuple[int, str, int]] = []
        for op, k, zero in slots:
            for _ in range(50):
                t = _draw(ctx, op, k, zero)
                if t not in picked:
                    break
            picked.append(t)
        items = []
        for n, (a, op, b) in enumerate(picked, 1):
            items.append({"kind": "column", "n": n, "a": a, "op": op, "b": b, "c": value(a, op, b),
                          "regroups": regroup_count(a, op, b), "width": 3})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["c"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        items = sheet.items
        issues: list[Issue] = []
        count = r.get("count", COUNT)
        if len(items) != count:
            issues.append(error(sheet, f"{len(items)} problems; this part has {count} a page"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
        for p in items:
            label = f"{p['a']} {p['op']} {p['b']}"
            if p.get("kind") != "column":
                issues.append(error(sheet, f"{label}: not a column problem"))
            if p["c"] != value(p["a"], p["op"], p["b"]):
                issues.append(error(sheet, f"{label} = {p['c']} is wrong"))
            if p.get("regroups") != regroup_count(p["a"], p["op"], p["b"]):
                issues.append(error(sheet, f"{label}: regroup count {p.get('regroups')} is wrong"))
            if max(len(str(p["a"])), len(str(p["b"])), len(str(max(p["c"], 0)))) > p.get("width", 3):
                issues.append(error(sheet, f"{label}: too many digits for {p.get('width')} columns"))
            why = problem_ok(p, r)
            if why:
                issues.append(error(sheet, why))
        keys = [(p["a"], p["op"], p["b"]) for p in items]
        if len(set(keys)) != len(keys):
            issues.append(error(sheet, "the same problem is on the page twice"))
        if sheet.answer_key != [p["c"] for p in items]:
            issues.append(error(sheet, "answer key doesn't match the problems"))
        for op in r["ops"]:
            if not any(p["op"] == op for p in items):
                issues.append(error(sheet, f"no {op!r} problem on the page"))
        seen = {p["regroups"] for p in items}
        missing = [k for k in r["regroups"] if k not in seen]
        if missing and len(r["regroups"]) <= len(items):
            issues.append(error(sheet, f"no problem regrouping in {missing} places (this part needs each of "
                                       f"{r['regroups']})"))
        zeros = sum(across_zero(p["a"], p["op"], p["b"]) for p in items)
        if zeros < r.get("across_zero", 0):
            issues.append(error(sheet, f"{zeros} problems trade across a zero; this part needs {r['across_zero']}"))
        return issues

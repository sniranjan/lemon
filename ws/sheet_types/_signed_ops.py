"""Arithmetic with negative numbers (Penguins math, grade 7: 7.NS.1–2): integers, then fractions
and decimals with signs, and fractions turned into decimals by long division.

This is the `layout: operations` mode of the `signed_numbers` sheet type (Pandas math's numbers
below zero); signed_numbers hands these pages to `generate` / `verify` here and prints them with
signed_numbers_ops.html.j2.

Every number is stored as a string ("-3", "-3/4", "1.25") and every answer is recomputed exactly
(Fraction) by verify. Printed math uses the true minus sign; a negative number after a sign gets
brackets (5 − (−3)). Rules, merged level → section → part:
- `layout: operations`, then `layouts`: pages of this type cycle through them, counted within the part:
  - `line`: 6 facts, each above its own number line from −10 to 10 to draw the jump on
    (`opposite: true`: a take-away is first rewritten as adding the opposite, two boxes).
  - `grid`: 12 facts (10 with fractions, 8 with decimals); `distance: N` of them ask how far apart two
    numbers are (|a − b|, 7.NS.1c).
  - `pattern`: a column a × b for a = 3, 2, … −3 (the first three filled in), so the child sees why
    a negative times a negative is positive; then 6 facts.
  - `chain`: 8 facts with three numbers and the order of operations; every division comes out even.
  - `convert`: 8 fractions to write as decimals (some stop, some repeat; 7.NS.2d).
- `numbers`: `integer` | `fraction` | `decimal`. `ops`: the signs facts use ("+", "-", "*", "/").
- `range`: [lo, hi] for every number in a fact; `answer_range`: [lo, hi] for the answer.
- `denominators` (fractions) and `places` (decimals: most digits after the point, default 2).
- `max_den`: largest denominator of a fraction answer (default 24).
- `convert_denominators`: denominators for `convert`. `title`: the sheet title.
- `alternate`: rules that replace these on every other page of the type (fractions, then decimals).
Every fact has at least one negative number in it, and no fact is on the page twice.
"""

from __future__ import annotations

from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent
from ._common import error, page_spec
from ._linear import compute, decimal_places, decimal_text, fmt, page_index, parse, repeating, show, show_fact, tokens

COUNTS = {"line": 6, "grid": 12, "pattern": 6, "chain": 8, "convert": 8}
RATIONAL_GRID = {"fraction": 10, "decimal": 8}
LINE_RANGE = (-10, 10)
PATTERN_ROWS = [3, 2, 1, 0, -1, -2, -3]
PATTERN_SHOWN = 3
MAX_TRIES = 20000


def page_rules(spec) -> tuple[dict, str]:
    """This page's rules and layout. `alternate: {...}` rules replace the part's on every other
    page of this type (fraction pages, then decimal pages)."""
    idx = page_index(spec)
    r = dict(spec.rules)
    if "alternate" in r and idx % 2:
        r.update(r["alternate"])
    return r, r["layouts"][idx % len(r["layouts"])]


def _style(r: dict) -> str:
    return "decimal" if r.get("numbers") == "decimal" else "fraction"


def count_for(layout: str, r: dict) -> int:
    if layout == "grid" and r.get("numbers", "integer") != "integer":
        return RATIONAL_GRID[r["numbers"]]
    return COUNTS[layout]


def answer_text(x: Fraction, r: dict) -> str:
    if _style(r) == "decimal":
        return show(x, "decimal")
    if x.denominator != 1 and abs(x) > 1:
        return f"{show(x)} = {show(x, 'mixed')}"
    return show(x)


def _number(rng, r: dict) -> Fraction:
    lo, hi = r["range"]
    kind = r.get("numbers", "integer")
    while True:
        if kind == "integer":
            x = Fraction(rng.randint(lo, hi))
        elif kind == "fraction":
            d = rng.choice(r["denominators"])
            x = Fraction(rng.randint(lo * d, hi * d), d)
            if x.denominator == 1:
                continue
        else:
            p = rng.randint(1, r.get("places", 2))
            x = Fraction(rng.randint(lo * 10 ** p, hi * 10 ** p), 10 ** p)
            if x.denominator == 1:
                continue
        if x != 0:
            return x


def number_ok(x: Fraction, r: dict) -> bool:
    lo, hi = r["range"]
    kind = r.get("numbers", "integer")
    if not lo <= x <= hi or x == 0:
        return False
    if kind == "integer":
        return x.denominator == 1
    if kind == "fraction":
        return x.denominator in r["denominators"]
    return x.denominator != 1 and _terminates(x) and decimal_places(x) <= r.get("places", 2)


def _terminates(x: Fraction) -> bool:
    try:
        decimal_places(x)
        return True
    except ValueError:
        return False


def answer_ok(ans: Fraction, r: dict, layout: str) -> bool:
    lo, hi = LINE_RANGE if layout == "line" else r.get("answer_range", [-100, 100])
    if not lo <= ans <= hi:
        return False
    kind = r.get("numbers", "integer")
    if kind == "integer":
        return ans.denominator == 1
    if kind == "fraction":
        return ans.denominator <= r.get("max_den", 24)
    return _terminates(ans) and decimal_places(ans) <= r.get("places", 2) + 1


def _fact(rng, r: dict, op: str, layout: str) -> tuple[list[Fraction], Fraction]:
    rr = dict(r, range=[-9, 9]) if layout == "line" else r
    for _ in range(MAX_TRIES):
        if op == "/" and r.get("numbers", "integer") != "fraction":
            b, q = _number(rng, rr), _number(rng, rr)
            nums = [b * q, b]
            if not number_ok(nums[0], dict(rr, range=r.get("dividend_range", [-100, 100]))):
                continue
        else:
            nums = [_number(rng, rr), _number(rng, rr)]
        if not any(x < 0 for x in nums):
            continue
        ans = compute([fmt(x) for x in nums], [op])
        if answer_ok(ans, r, layout):
            return nums, ans
    raise ValueError(f"signed_arithmetic: no {op} fact fits {r}")


def chain_exact(operands: list[str], ops: list[str]) -> bool:
    """Every ÷ in a whole-number chain gives a whole number (left to right within × ÷ runs)."""
    acc = parse(operands[0])
    for op, x in zip(ops, operands[1:]):
        v = parse(x)
        if op in "+-":
            acc = v
        elif op == "*":
            acc *= v
        else:
            if v == 0 or (acc / v).denominator != 1:
                return False
            acc /= v
    return True


def _chain(rng, r: dict) -> tuple[list[Fraction], list[str], Fraction]:
    for _ in range(MAX_TRIES):
        ops = [rng.choice(r["ops"]) for _ in range(r.get("terms", 3) - 1)]
        if any(o in "*/" for o in r["ops"]) and not any(o in "*/" for o in ops):
            continue   # a page with times or sharing puts one in every chain
        nums = [_number(rng, r) for _ in range(len(ops) + 1)]
        strs = [fmt(x) for x in nums]
        if not any(x < 0 for x in nums) or not chain_exact(strs, ops):
            continue
        ans = compute(strs, ops)
        if answer_ok(ans, r, "chain"):
            return nums, ops, ans
    raise ValueError(f"signed_arithmetic: no chain fits {r}")


def _convert_pool(r: dict) -> list[Fraction]:
    return sorted({Fraction(n, d) for d in r["convert_denominators"] for n in range(1, d)
                   if Fraction(n, d).denominator == d})


def fact_item(n: int, nums: list[Fraction], ops: list[str], r: dict, kind: str = "fact") -> dict:
    strs = [fmt(x) for x in nums]
    ans = compute(strs, ops)
    return {"kind": kind, "n": n, "operands": strs, "ops": ops,
            "show": tokens(show_fact(strs, ops, _style(r))), "answer": answer_text(ans, r)}


def item_answers(i: dict, r: dict) -> list[str]:
    if i["kind"] == "pattern":
        return [", ".join(row["answer"] for row in i["rows"] if row["blank"])]
    if i["kind"] == "line" and i.get("opposite"):
        b = parse(i["operands"][1])
        return [f"{show(i['operands'][0])} + ({show(-b)}) = {i['answer']}"
                if -b < 0 else f"{show(i['operands'][0])} + {show(-b)} = {i['answer']}"]
    return [i["answer"]]


TEMPLATE = "signed_numbers_ops.html.j2"


def is_operations(rules: dict) -> bool:
    return rules.get("layout") == "operations"


def generate(ctx: GenContext, name: str) -> SheetContent:
    r, layout = page_rules(ctx.spec)
    rng = ctx.rng
    items: list[dict] = []
    seen: set = set()

    def add_fact(op: str, kind: str = "fact") -> None:
        while True:
            nums, _ = _fact(rng, r, op, layout)
            key = (tuple(nums), op)
            if key not in seen:
                seen.add(key)
                item = fact_item(len(items) + 1, nums, [op], r, kind)
                if kind == "line" and op == "-" and r.get("opposite"):
                    item["opposite"] = True
                items.append(item)
                return

    count = count_for(layout, r)
    if layout == "pattern":
        b = -rng.randint(2, 9)
        rows = [{"a": str(a), "answer": show(a * b), "blank": k >= PATTERN_SHOWN}
                for k, a in enumerate(PATTERN_ROWS)]
        items.append({"kind": "pattern", "n": 1, "b": str(b), "rows": rows})
    if layout == "convert":
        pool = _convert_pool(r)
        stop = [x for x in pool if not repeating(x)[2]]
        rep = [x for x in pool if repeating(x)[2]]
        picks = rng.sample(stop, count // 2) + rng.sample(rep, count - count // 2)
        rng.shuffle(picks)
        signs = [-1] * (count // 2) + [1] * (count - count // 2)
        rng.shuffle(signs)
        for k, (x, s) in enumerate(zip(picks, signs), 1):
            v = x * s
            items.append({"kind": "convert", "n": k, "operands": [fmt(v)],
                          "show": tokens(show(v)), "answer": decimal_text(v)})
    elif layout == "chain":
        while len(items) < count:
            nums, ops, _ = _chain(rng, r)
            key = (tuple(nums), tuple(ops))
            if key not in seen:
                seen.add(key)
                items.append(fact_item(len(items) + 1, nums, ops, r))
    else:
        ops = [r["ops"][k % len(r["ops"])] for k in range(count)]
        rng.shuffle(ops)
        dist = r.get("distance", 0) if layout == "grid" else 0
        for k, op in enumerate(ops):
            if k >= count - dist:
                while True:
                    a, b = _number(rng, r), _number(rng, r)
                    if (a < 0) != (b < 0) and (a, b) not in seen:
                        seen.add((a, b))
                        break
                items.append({"kind": "distance", "n": len(items) + 1, "operands": [fmt(a), fmt(b)],
                              "show": [tokens(show(a, _style(r))), tokens(show(b, _style(r)))],
                              "answer": answer_text(abs(a - b), r)})
            else:
                add_fact(op, "line" if layout == "line" else "fact")
    for i in items:
        i["layout"], i["numbers"] = layout, r.get("numbers", "integer")
    answers = [a for i in items for a in item_answers(i, r)]
    return SheetContent(title=r["title"], parent_tip=ctx.tip(name), items=items, answer_key=answers)


def verify(sheet: Sheet) -> list[Issue]:
    spec = page_spec(sheet)
    spec = spec.model_copy(update={"sheet_type": sheet.sheet_type})
    r, layout = page_rules(spec)
    issues: list[Issue] = []
    items = sheet.items
    facts = [i for i in items if i["kind"] in ("fact", "line")]
    want = count_for(layout, r) + (layout == "pattern")
    if len(items) != want:
        issues.append(error(sheet, f"{len(items)} items; a {layout} page has {want}"))
    if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
        issues.append(error(sheet, "items are not numbered 1, 2, 3… in order"))
    kinds = {"line": {"line"}, "grid": {"fact", "distance"}, "pattern": {"pattern", "fact"},
             "chain": {"fact"}, "convert": {"convert"}}[layout]
    for i in items:
        label = f"item {i.get('n')}"
        if i.get("layout") != layout or i.get("numbers") != r.get("numbers", "integer"):
            issues.append(error(sheet, f"{label}: this page is a {layout} page"))
        if i["kind"] not in kinds:
            issues.append(error(sheet, f"{label}: a {i['kind']!r} item doesn't belong on a {layout} page"))
            continue
        if i["kind"] == "pattern":
            b = parse(i["b"])
            if [parse(row["a"]) for row in i["rows"]] != PATTERN_ROWS or b >= 0:
                issues.append(error(sheet, f"{label}: the pattern must run 3 down to −3 times a negative"))
            for k, row in enumerate(i["rows"]):
                if row["answer"] != show(parse(row["a"]) * b) or row["blank"] != (k >= PATTERN_SHOWN):
                    issues.append(error(sheet, f"{label}: row {row['a']} × {i['b']} is wrong"))
            continue
        nums = [parse(x) for x in i["operands"]]
        if i["kind"] == "convert":
            x = nums[0]
            if x.denominator not in r["convert_denominators"] or not 0 < abs(x) < 1:
                issues.append(error(sheet, f"{label}: {i['operands'][0]} isn't one of this part's fractions"))
            if i["answer"] != decimal_text(x) or i["show"] != tokens(show(x)):
                issues.append(error(sheet, f"{label}: {i['operands'][0]} as a decimal is {decimal_text(x)}"))
            continue
        rr = dict(r, range=[-9, 9]) if layout == "line" else r
        checked = nums
        if i.get("ops") == ["/"] and r.get("numbers", "integer") != "fraction" and nums[1] != 0:
            # a division is built as (divisor × quotient) ÷ divisor: check those two and the dividend
            checked = [nums[1], nums[0] / nums[1]]
            if not number_ok(nums[0], dict(rr, range=r.get("dividend_range", [-100, 100]))):
                issues.append(error(sheet, f"{label}: {show(nums[0], _style(r))} is too big to share"))
        for x in checked:
            if not number_ok(x, rr):
                issues.append(error(sheet, f"{label}: {show(x, _style(r))} is outside this part's numbers"))
        if not any(x < 0 for x in nums):
            issues.append(error(sheet, f"{label}: no negative number in it"))
        if i["kind"] == "distance":
            if i["answer"] != answer_text(abs(nums[0] - nums[1]), r):
                issues.append(error(sheet, f"{label}: the distance is {abs(nums[0] - nums[1])}"))
            continue
        ops = i["ops"]
        if any(o not in r["ops"] for o in ops):
            issues.append(error(sheet, f"{label}: sign {ops} isn't used in this part"))
        if len(ops) != (r.get("terms", 3) - 1 if layout == "chain" else 1):
            issues.append(error(sheet, f"{label}: wrong number of signs for a {layout} page"))
        if layout == "chain" and not chain_exact(i["operands"], ops):
            issues.append(error(sheet, f"{label}: a division doesn't come out even"))
        ans = compute(i["operands"], ops)
        if not answer_ok(ans, r, layout):
            issues.append(error(sheet, f"{label}: answer {show(ans)} is outside this part's range"))
        if i["answer"] != answer_text(ans, r):
            issues.append(error(sheet, f"{label}: answer {i['answer']} is wrong, it's {answer_text(ans, r)}"))
        if i["show"] != tokens(show_fact(i["operands"], ops, _style(r))):
            issues.append(error(sheet, f"{label}: printed fact doesn't match its numbers"))
        if bool(i.get("opposite")) != (layout == "line" and ops == ["-"] and bool(r.get("opposite"))):
            issues.append(error(sheet, f"{label}: the add-the-opposite step is missing or extra"))
    keys = [(tuple(i.get("operands", [])), tuple(i.get("ops", []))) for i in items if i["kind"] != "pattern"]
    if len(set(keys)) != len(keys):
        issues.append(error(sheet, "the same fact is on the page twice"))
    if layout == "convert":
        reps = sum(bool(repeating(parse(i["operands"][0]))[2]) for i in items)
        if not 0 < reps < len(items):
            issues.append(error(sheet, "a convert page needs decimals that stop and decimals that repeat"))
    if layout in ("grid", "line", "pattern") and facts:
        used = {o for i in facts for o in i["ops"]}
        if used != set(r["ops"]) and len(facts) >= len(r["ops"]):
            issues.append(error(sheet, f"signs {sorted(used)}; this part uses {r['ops']}"))
    expected = [a for i in items for a in item_answers(i, r)]
    if sheet.answer_key != expected:
        issues.append(error(sheet, "answer key doesn't match the items"))
    return issues

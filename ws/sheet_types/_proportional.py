"""Is it proportional? (Penguins math, grade 7: 7.RP.2a–c): tables from real situations; the
child decides whether y ÷ x is the same in every column, finds the constant of proportionality k,
writes the equation y = kx and fills in the missing number.

This is the `mode: proportional` of the `ratio_table` sheet type (Pandas math's ratio tables);
ratio_table hands these pages to `generate` / `verify` here and prints them with
ratio_table_proportional.html.j2. Rules (merged level → section → part):
- `tables`: tables a page (default 3); exactly one of them is not proportional (it has a fixed
  fee or start-up amount, y = kx + b), the others are.
- `title`: the sheet title. Each situation has its own sensible rates and fixed amounts (CONTEXTS).
A proportional table has one empty y cell to fill in. Every number is stored as text and verify
recomputes every cell, k, the equation and the answers exactly.
"""

from __future__ import annotations

from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent
from ._common import error
from ._linear import decimal_places, fmt, is_terminating, parse

TEMPLATE = "ratio_table_proportional.html.j2"
TABLES = 3
COLUMNS = 4
# (x label, y label, sentence, sensible rates k, fixed amounts that make it not proportional or None)
CONTEXTS = (
    ("Hours", "Dollars earned", "Dev earns money babysitting.", ("8", "10", "12", "12.5", "15"), None),
    ("Gallons of gas", "Miles driven", "A car uses gas on a trip.", ("24", "28", "30", "32"), None),
    ("Pounds of apples", "Cost ($)", "Apples are sold by the pound.", ("1.25", "1.5", "1.75", "2.5"), None),
    ("Minutes", "Pages printed", "A printer prints pages.", ("12", "15", "20", "24"), None),
    ("Tickets", "Cost ($)", "Tickets for the school play.", ("6", "7.5", "8", "12"), ("2", "3", "4")),
    ("Hours", "Cost ($)", "Renting a kayak at the lake.", ("12", "15", "18", "20"), ("5", "8", "10")),
    ("Months", "Cost ($)", "A swim club membership.", ("15", "18", "20", "25"), ("20", "25", "40")),
    ("Weeks", "Dollars saved", "Mina saves the same amount each week.", ("5", "6", "7.5", "10"), ("10", "15", "20")),
    ("Cups of flour", "Muffins", "A muffin recipe.", ("6", "8", "12"), None),
    ("Minutes", "Laps", "Jon swims laps at a steady pace.", ("0.5", "1.5", "2"), None),
    ("Rides", "Cost ($)", "Rides at the county fair.", ("1.5", "2", "2.5", "3"), ("5", "8", "10")),
    ("Hours", "Inches of snow", "Snow falls at a steady rate.", ("0.5", "0.75", "1.5", "2"), ("2", "3", "4")),
)
MAX_Y = 500
MAX_TRIES = 3000


def is_proportional_mode(rules: dict) -> bool:
    return rules.get("mode") == "proportional"


def cell(c: int, y: Fraction) -> str:
    """A y cell as printed: cents for money columns (7.50), a plain decimal otherwise."""
    return fmt(y, "money") if "$" in CONTEXTS[c][1] or "Dollars" in CONTEXTS[c][1] else fmt(y, "decimal")


def _nice(y: Fraction) -> bool:
    return is_terminating(y) and decimal_places(y) <= 2


def answers_for(t: dict) -> str:
    if not t["proportional"]:
        return "not proportional (y ÷ x changes)"
    miss = t["y"][t["blank"]]
    return f"proportional, k = {t['k']}, y = {t['k']}x, missing {miss}"


def _table(rng, prop: bool, used: set) -> dict | None:
    pool = [i for i, c in enumerate(CONTEXTS) if i not in used and (prop or c[4])]
    c = rng.choice(pool)
    k = parse(rng.choice(CONTEXTS[c][3]))
    xs = sorted(rng.sample(range(1, 13), COLUMNS))
    fee = Fraction(0) if prop else parse(rng.choice(CONTEXTS[c][4]))
    ys = [k * x + fee for x in xs]
    if not all(_nice(y) for y in ys) or max(ys) > MAX_Y:
        return None
    t = {"kind": "proportion", "context": c, "x_label": CONTEXTS[c][0], "y_label": CONTEXTS[c][1],
         "say": CONTEXTS[c][2], "x": [str(x) for x in xs], "y": [cell(c, y) for y in ys],
         "proportional": prop, "k": fmt(k, "decimal") if prop else None,
         "fee": fmt(fee, "decimal") if not prop else None,
         "blank": rng.randrange(1, COLUMNS) if prop else None}
    return t


def generate(ctx: GenContext, name: str) -> SheetContent:
    r = ctx.rules
    rng = ctx.rng
    count = r.get("tables", TABLES)
    odd = rng.randrange(count)
    items, used = [], set()
    for n in range(1, count + 1):
        for _ in range(MAX_TRIES):
            t = _table(rng, n - 1 != odd, used)
            if t:
                break
        else:
            raise ValueError(f"ratio_table: no proportional table fits {r}")
        used.add(t["context"])
        t["n"] = n
        t["answer"] = answers_for(t)
        items.append(t)
    return SheetContent(title=r["title"], parent_tip=ctx.tip(name), items=items,
                        answer_key=[t["answer"] for t in items])


def verify(sheet: Sheet, r: dict) -> list[Issue]:
    items = sheet.items
    issues: list[Issue] = []
    count = r.get("tables", TABLES)
    if len(items) != count:
        issues.append(error(sheet, f"{len(items)} tables; this part has {count}"))
    if [t.get("n") for t in items] != list(range(1, len(items) + 1)):
        issues.append(error(sheet, "tables are not numbered 1, 2, 3… in order"))
    if sum(not t.get("proportional") for t in items) != 1:
        issues.append(error(sheet, "a page needs exactly one table that isn't proportional"))
    if len({t.get("context") for t in items}) != len(items):
        issues.append(error(sheet, "two tables share a situation"))
    for t in items:
        label = f"table {t.get('n')}"
        if [t.get("x_label"), t.get("y_label"), t.get("say")] != list(CONTEXTS[t["context"]][:3]):
            issues.append(error(sheet, f"{label}: labels don't match situation {t['context']}"))
        xs = [parse(x) for x in t["x"]]
        ys = [parse(y) for y in t["y"]]
        if len(xs) != COLUMNS or xs != sorted(set(xs)) or xs[0] < 1:
            issues.append(error(sheet, f"{label}: x values must be {COLUMNS} different whole numbers, in order"))
        ratios = {y / x for x, y in zip(xs, ys)}
        if t["proportional"]:
            k = parse(t["k"])
            if t["k"] not in CONTEXTS[t["context"]][3] or ratios != {k}:
                issues.append(error(sheet, f"{label}: y ÷ x isn't always {t['k']}"))
            if not isinstance(t.get("blank"), int) or not 1 <= t["blank"] < COLUMNS:
                issues.append(error(sheet, f"{label}: one y cell after the first must be empty"))
        else:
            c = CONTEXTS[t["context"]]
            fee = parse(t["fee"] or "0")
            k = (ys[1] - ys[0]) / (xs[1] - xs[0])
            if (not c[4] or t["fee"] not in c[4] or fmt(k, "decimal") not in c[3]
                    or any(y != k * x + fee for x, y in zip(xs, ys)) or len(ratios) == 1):
                issues.append(error(sheet, f"{label}: a non-proportional table must be a steady rate plus a fixed amount"))
            if t.get("blank") is not None:
                issues.append(error(sheet, f"{label}: a non-proportional table has no empty cell"))
        if t["y"] != [cell(t["context"], y) for y in ys] or not all(_nice(y) for y in ys) or max(ys) > MAX_Y:
            issues.append(error(sheet, f"{label}: numbers aren't written as tidy decimals"))
        if t.get("answer") != answers_for(t):
            issues.append(error(sheet, f"{label}: answer should read {answers_for(t)!r}"))
    if sheet.answer_key != [t.get("answer") for t in items]:
        issues.append(error(sheet, "answer key doesn't match the tables"))
    return issues

"""Numbers below zero (Pandas math, 6.NS.5–7): number lines with negatives, opposites, signed
numbers for real situations, comparing, absolute value and ordering.

Rules (merged level → section → part):
- `layout`: `lines` (number lines from `range` lo to hi) or `facts` (two columns of short questions).
- `tasks`: what the items ask, cycling down the page.
  Lines: `name` (a dot on a tick: write its number), `mark` (a number: draw its dot),
  `opposite` (a dot with its number: draw the dot for the opposite number).
  Facts: `context` (write a signed number for "8 degrees below zero"), `opposite` ("the opposite
  of −7 is ☐"), `compare` (−3 ☐ −7: write < or >), `abs` (|−6| = ☐), `order` (four numbers,
  least to greatest; takes a whole row).
- `range`: [lo, hi], the numbers used (lines run from lo to hi with a tick at every whole number).
- `context_max`: largest size of a `context` number (default: the top of `range`).
- `halves`: true lets compare, abs and order use halves (−2.5) as well as whole numbers.
- `problems`: items a page (default 5 lines, 12 facts). `title`: the sheet title.
Numbers are stored as text ("-3", "2.5"); verify recomputes every answer exactly with Fraction.

`layout: operations` (Penguins math, 7.NS.1–2): adding, taking away, multiplying and dividing
signed integers, fractions and decimals, and fractions as decimals; see _signed_ops.py.
"""

from __future__ import annotations

from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from . import _signed_ops
from ._common import error
from ._rational import fmt, parse, show

LINES, FACTS = 5, 12
MAX_TRIES = 2000
# Real situations for signed numbers (6.NS.5): (text with {n}, sign of the number, largest sensible size)
CONTEXTS = (
    ("{n} degrees below zero", -1, 30), ("{n} degrees above zero", 1, 40),
    ("{n} feet below sea level", -1, 50), ("{n} feet above sea level", 1, 50),
    ("a gain of {n} yards in a football game", 1, 20), ("a loss of {n} yards in a football game", -1, 15),
    ("{n} floors below the ground floor", -1, 4), ("{n} floors above the ground floor", 1, 12),
    ("putting ${n} into a savings account", 1, 50), ("taking ${n} out of a savings account", -1, 40),
    ("losing {n} points in a game", -1, 20), ("winning {n} points in a game", 1, 30),
    ("a diver {n} meters under the water", -1, 30), ("a kite {n} meters above the ground", 1, 40),
)
ONE_ROW = {"order"}


def num(x: Fraction) -> str:
    return fmt(x, "decimal")


def answer_for(i: dict) -> str:
    t = i["task"]
    if t == "name":
        return show(i["value"])
    if t == "mark":
        return f"dot at {show(i['value'])}"
    if t == "opposite" and i["kind"] == "line":
        return f"dot at {show(num(-parse(i['value'])))}"
    if t == "opposite":
        return show(num(-parse(i["value"])))
    if t == "context":
        return show(i["value"])
    if t == "compare":
        a, b = parse(i["values"][0]), parse(i["values"][1])
        return "<" if a < b else ">"
    if t == "abs":
        return show(num(abs(parse(i["value"]))))
    if t == "order":
        return " < ".join(show(v) for v in sorted(i["values"], key=parse))
    raise ValueError(f"unknown task {t!r}")


def context_text(i: dict) -> str:
    text = CONTEXTS[i["context"]][0]
    return text.format(n=num(abs(parse(i["value"]))))


@register("signed_numbers")
class SignedNumbers(SheetType):
    template = "signed_numbers.html.j2"

    def template_for(self, sheet: Sheet) -> str:
        return _signed_ops.TEMPLATE if sheet.items and "layout" in sheet.items[0] else self.template

    def generate(self, ctx: GenContext) -> SheetContent:
        if _signed_ops.is_operations(ctx.rules):
            return _signed_ops.generate(ctx, self.name)
        r = ctx.rules
        rng = ctx.rng
        lo, hi = r["range"]
        lines = r["layout"] == "lines"
        count = r.get("problems", LINES if lines else FACTS)
        wholes = [x for x in range(lo, hi + 1)]
        halves = [Fraction(2 * k + 1, 2) for k in range(lo, hi)] if r.get("halves") else []

        def pick(nonzero=True, allow_half=False):
            pool = wholes + (halves if allow_half else [])
            return Fraction(rng.choice([x for x in pool if x != 0 or not nonzero]))

        items, seen = [], set()
        tasks = [r["tasks"][k % len(r["tasks"])] for k in range(count)]
        ctx_order = list(range(len(CONTEXTS)))
        rng.shuffle(ctx_order)
        for n, task in enumerate(tasks, 1):
            for _ in range(MAX_TRIES):
                item = {"kind": "line" if lines else "fact", "n": n, "task": task}
                if lines:
                    v = pick()
                    item.update(lo=lo, hi=hi, value=num(v))
                    if task == "opposite" and v < 0 and rng.random() < 0.5:
                        v = -v
                        item["value"] = num(v)
                elif task == "context":
                    c = ctx_order.pop()
                    v = Fraction(rng.randint(2, min(r.get("context_max", hi), CONTEXTS[c][2])) * CONTEXTS[c][1])
                    item.update(context=c, value=num(v))
                    item["text"] = context_text(item)
                elif task in ("opposite", "abs"):
                    v = pick(allow_half=task == "abs" and rng.random() < 0.5)
                    if task == "abs" and v > 0 and rng.random() < 0.7:
                        v = -v if -v >= lo else v
                    item["value"] = num(v)
                elif task == "compare":
                    a = pick(nonzero=False, allow_half=True)
                    b = pick(nonzero=False, allow_half=True)
                    if a == b or min(a, b) >= 0:
                        continue   # two positives are grade 3 work: keep a negative in every pair
                    item["values"] = [num(a), num(b)]
                elif task == "order":
                    vals = set()
                    while len(vals) < 4:
                        vals.add(pick(nonzero=False, allow_half=True))
                    vals = list(vals)
                    rng.shuffle(vals)
                    if sorted(vals) == vals or sum(x < 0 for x in vals) < 2:
                        continue
                    item["values"] = [num(x) for x in vals]
                key = repr({k: v for k, v in item.items() if k != "n"})
                if key not in seen:
                    seen.add(key)
                    break
            else:
                raise ValueError(f"signed_numbers: no {task} item fits {r}")
            item["answer"] = answer_for(item)
            items.append(item)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["answer"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        if _signed_ops.is_operations(r):
            return _signed_ops.verify(sheet)
        lo, hi = r["range"]
        lines = r["layout"] == "lines"
        count = r.get("problems", LINES if lines else FACTS)
        items = sheet.items
        issues: list[Issue] = []
        if len(items) != count:
            issues.append(error(sheet, f"{len(items)} items; this part has {count}"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "items are not numbered 1, 2, 3… in order"))
        for idx, i in enumerate(items):
            label = f"item {i.get('n')} ({i.get('task')})"
            task = r["tasks"][idx % len(r["tasks"])]
            if i.get("task") != task or i.get("kind") != ("line" if lines else "fact"):
                issues.append(error(sheet, f"{label}: should be a {task!r} {'line' if lines else 'fact'}"))
                continue
            try:
                vals = [parse(v) for v in i.get("values", [])] + ([parse(i["value"])] if "value" in i else [])
            except (ValueError, ZeroDivisionError):
                issues.append(error(sheet, f"{label}: numbers aren't readable"))
                continue
            vlo, vhi = (-r.get("context_max", hi), r.get("context_max", hi)) if task == "context" else (lo, hi)
            for v in vals:
                if not vlo <= v <= vhi or (v.denominator not in (1, 2)) or (v.denominator == 2 and not r.get("halves")):
                    issues.append(error(sheet, f"{label}: {num(v)} isn't a number this part uses ({lo} to {hi})"))
                if num(v) not in i.get("values", []) + [i.get("value")]:
                    issues.append(error(sheet, f"{label}: numbers aren't written in simplest form"))
            if lines:
                if (i.get("lo"), i.get("hi")) != (lo, hi) or vals[0].denominator != 1 or vals[0] == 0:
                    issues.append(error(sheet, f"{label}: a line runs {lo} to {hi} with its dot on a whole number, not 0"))
                if task == "opposite" and not lo <= -vals[0] <= hi:
                    issues.append(error(sheet, f"{label}: the opposite is off the line"))
            if task == "context":
                c = i.get("context")
                if not isinstance(c, int) or not 0 <= c < len(CONTEXTS):
                    issues.append(error(sheet, f"{label}: unknown situation"))
                else:
                    if abs(vals[0]) > CONTEXTS[c][2]:
                        issues.append(error(sheet, f"{label}: {num(vals[0])} is too big for {i.get('text')!r}"))
                    if (vals[0] > 0) != (CONTEXTS[c][1] > 0) or i.get("text") != context_text(i):
                        issues.append(error(sheet, f"{label}: the number's sign doesn't match {i.get('text')!r}"))
            if task == "compare" and (len(vals) != 2 or vals[0] == vals[1] or min(vals) >= 0):
                issues.append(error(sheet, f"{label}: compare two different numbers, at least one below zero"))
            if task == "order" and (len(vals) != 4 or len(set(vals)) != 4 or vals == sorted(vals)
                                    or sum(v < 0 for v in vals) < 2):
                issues.append(error(sheet, f"{label}: order four different numbers (two below zero), not already in order"))
            if i.get("answer") != answer_for(i):
                issues.append(error(sheet, f"{label}: answer {i.get('answer')} is wrong, it's {answer_for(i)}"))
        keys = [repr({k: v for k, v in i.items() if k != "n"}) for i in items]
        if len(set(keys)) != len(keys):
            issues.append(error(sheet, "the same question is on the page twice"))
        contexts = [i["context"] for i in items if "context" in i]
        if len(set(contexts)) != len(contexts):
            issues.append(error(sheet, "the same situation is on the page twice"))
        if sheet.answer_key != [i.get("answer") for i in items]:
            issues.append(error(sheet, "answer key doesn't match the items"))
        return issues

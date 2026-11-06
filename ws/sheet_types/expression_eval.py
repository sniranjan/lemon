"""Letters for numbers (Pandas math, 6.EE.1–2): whole-number exponents and the order of
operations, writing expressions from words, and evaluating expressions and formulas.

Rules (merged level → section → part):
- `task`: `power` (work out 2³ + 5 or 3(4 + 2)²), `write` (write "7 more than n" as n + 7),
  `substitute` (if n = 5, 3n + 4 = ☐), `formula` (two or three letters: if l = 7 and w = 4, A = lw = ☐).
- `problems`: items a page (default 10; `write` and `formula` 8).
- `max_value`: largest answer (default 200). `max_var`: largest value a letter takes (default 12).
- `title`: the sheet title.
Expressions are stored in Python form ("3*n+4") and as printed ("3n + 4"); verify prints and
evaluates each one again (exactly, with Fraction) and checks it against its form. Letters are
never `a`, so a printed term can't spell an internal level code ("6a").

`task: tidy` (Penguins math, 7.EE.1–2): collecting like terms, opening brackets, factoring and
rewriting linear expressions; see _tidy.py.
"""

from __future__ import annotations

import re
from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from . import _tidy
from ._common import error
from ._rational import evaluate, pretty

MAX_TRIES = 3000
NUMS = {"A": (2, 10), "B": (2, 20), "C": (2, 9), "D": (2, 5)}
LETTERS = "nxytpk"

# Numerical expressions with whole-number exponents (6.EE.1); A, B, C, D become numbers
POWER_FORMS = (
    "{A}**2", "{D}**3", "{A}**2 + {B}", "{B} + {D}**3", "{C} * {A}**2", "({A} + {B})**2", "{A}**2 + {B}**2",
    "{A}**2 - {B}", "{B} + {C} * {A}", "({B} + {C}) * {A}", "{D}**3 - {A}", "{C} * ({A} + {B})", "{C}**2 - {B} + {A}", "({A} - {D})**2 + {B}",
)
# Words to expressions (6.EE.2a): phrase, expression; v is the letter, K and J are numbers
WRITE_FORMS = (
    ("{K} more than {v}", "{v} + {K}"), ("{K} less than {v}", "{v} - {K}"), ("{K} times {v}", "{K}*{v}"),
    ("{v} divided by {K}", "{v} / {K}"), ("the sum of {v} and {K}", "{v} + {K}"), ("the product of {K} and {v}", "{K}*{v}"),
    ("subtract {v} from {K}", "{K} - {v}"), ("{K} more than twice {v}", "2*{v} + {K}"), ("{v} squared", "{v}**2"),
    ("{K} times the sum of {v} and {J}", "{K}*({v} + {J})"), ("the quotient of {v} and {K}", "{v} / {K}"),
    ("{K} less than 3 times {v}", "3*{v} - {K}"), ("{v} cubed", "{v}**3"), ("half of {v}, plus {K}", "{v} / 2 + {K}"),
)
# One letter (6.EE.2c); v is the letter
SUB_FORMS = (
    "{C}*{v} + {B}", "{C}*{v} - {B}", "{v}**2 + {B}", "{C}*({v} + {B})", "{v} / {C} + {B}", "{B} - {v}", "{v}**2 - {B}", "{C}*{v}**2",
    "({v} + {B}) / {C}", "{B} + {C}*{v}", "{v}**3 + {B}", "{C}*({v} - {D})",
)
# Formulas and two-letter expressions (6.EE.2c): name printed before "=", expression, letter ranges
FORMULAS = (
    ("A", "l*w", {"l": (3, 15), "w": (2, 12)}), ("P", "2*l + 2*w", {"l": (3, 20), "w": (2, 15)}),
    ("V", "s**3", {"s": (2, 6)}), ("A", "s**2", {"s": (3, 14)}), ("d", "r*t", {"r": (3, 30), "t": (2, 9)}),
    ("V", "l*w*h", {"l": (2, 10), "w": (2, 6), "h": (2, 5)}), ("P", "4*s", {"s": (3, 40)}),
    (None, "3*x + 2*y", {"x": (1, 12), "y": (1, 12)}), (None, "x*y - 4", {"x": (2, 12), "y": (2, 12)}),
    (None, "x**2 + y", {"x": (2, 12), "y": (1, 30)}), (None, "(x + y) / 2", {"x": (1, 20), "y": (1, 20)}),
    (None, "5*x - y", {"x": (2, 12), "y": (1, 20)}), (None, "2*(x + y)", {"x": (1, 15), "y": (1, 15)}),
    (None, "x**2 - y**2", {"x": (3, 12), "y": (1, 11)}),
)
FEWER = {"write": 8, "formula": 8, "substitute": 10, "power": 10}


def fill(form: str, nums: dict[str, int], letter: str = "v") -> str:
    """'{C}*{v} + {B}' with C=3, B=4, letter n -> '3*n + 4'."""
    return form.format(v=letter, **nums)


def uses(form: str) -> set[str]:
    return set(re.findall(r"\{([A-Z])\}", form))


def _whole(x) -> bool:
    return isinstance(x, Fraction) and x.denominator == 1 and x >= 0


def check_item(i: dict, r: dict) -> str | None:
    """None if the item is right, else why not."""
    task = i.get("task")
    max_value, max_var = r.get("max_value", 200), r.get("max_var", 12)
    try:
        if task == "power":
            expr = fill(POWER_FORMS[i["form"]], i["nums"])
            vals: dict = {}
        elif task == "write":
            phrase, form = WRITE_FORMS[i["form"]]
            v = i["letter"]
            expr = fill(form, i["nums"], v)
            if i.get("phrase") != fill(phrase, i["nums"], v):
                return f"phrase {i.get('phrase')!r} doesn't match its form"
            vals = {v: 1}
        elif task == "substitute":
            expr = fill(SUB_FORMS[i["form"]], i["nums"], i["letter"])
            vals = i["vars"]
        elif task == "formula":
            name, expr, ranges = FORMULAS[i["form"]]
            vals = i["vars"]
            if i.get("name") != name or set(vals) != set(ranges):
                return "formula name or letters don't match"
            for k, (lo, hi) in ranges.items():
                if not lo <= vals[k] <= hi:
                    return f"{k} = {vals[k]} is outside {lo}–{hi}"
        else:
            return f"unknown task {task!r}"
    except (KeyError, IndexError, TypeError):
        return "form or numbers missing"
    if i.get("expr") != expr:
        return f"expression {i.get('expr')!r} should be {expr!r}"
    if i.get("show") != pretty(expr):
        return f"printed as {i.get('show')!r}, should be {pretty(expr)!r}"
    if "a" in vals or ("letter" in i and i["letter"] not in LETTERS):
        return "letters must not be `a`"
    if task == "substitute" and not all(2 <= x <= max_var for x in vals.values()):
        return f"letter values {vals} are outside 2–{max_var}"
    for k, (lo, hi) in NUMS.items():
        if k in i.get("nums", {}) and not lo <= i["nums"][k] <= hi:
            return f"number {k} = {i['nums'][k]} is outside {lo}–{hi}"
    if task == "write":
        answer = pretty(expr)
    else:
        try:
            x = evaluate(expr, vals)
        except ValueError as e:
            return f"can't work out {expr}: {e}"
        if not _whole(x) or x > max_value:
            return f"{pretty(expr)} = {x}: answers are whole numbers 0–{max_value}"
        answer = str(x)
    if i.get("answer") != answer:
        return f"answer {i.get('answer')} is wrong, it's {answer}"
    return None


@register("expression_eval")
class ExpressionEval(SheetType):
    template = "expression_eval.html.j2"

    def template_for(self, sheet: Sheet) -> str:
        return _tidy.TEMPLATE if sheet.items and sheet.items[0].get("kind") == "tidy" else self.template

    def generate(self, ctx: GenContext) -> SheetContent:
        if _tidy.is_tidy(ctx.rules):
            return _tidy.generate(ctx, self.name)
        r = ctx.rules
        rng = ctx.rng
        task = r["task"]
        count = r.get("problems", FEWER.get(task, 12))
        forms = {"power": POWER_FORMS, "write": WRITE_FORMS, "substitute": SUB_FORMS, "formula": FORMULAS}[task]
        order = list(range(len(forms)))
        rng.shuffle(order)
        items = []
        for n in range(1, count + 1):
            form = order[(n - 1) % len(order)]
            for _ in range(MAX_TRIES):
                nums = {k: rng.randint(lo, hi) for k, (lo, hi) in NUMS.items()}
                item = {"kind": "expr", "n": n, "task": task, "form": form}
                if task == "power":
                    used = {k: v for k, v in nums.items() if k in uses(POWER_FORMS[form])}
                    item.update(nums=used, expr=fill(POWER_FORMS[form], used))
                elif task == "write":
                    phrase, f = WRITE_FORMS[form]
                    used = {"K": rng.randint(2, 12), "J": rng.randint(2, 9)}
                    used = {k: v for k, v in used.items() if k in uses(f)}
                    v = rng.choice(LETTERS)
                    item.update(nums=used, letter=v, phrase=fill(phrase, used, v), expr=fill(f, used, v))
                elif task == "substitute":
                    f = SUB_FORMS[form]
                    used = {k: v for k, v in nums.items() if k in uses(f)}
                    v = rng.choice(LETTERS)
                    item.update(nums=used, letter=v, vars={v: rng.randint(2, r.get("max_var", 12))},
                                expr=fill(f, used, v))
                else:
                    name, expr, ranges = FORMULAS[form]
                    item.update(name=name, vars={k: rng.randint(lo, hi) for k, (lo, hi) in ranges.items()},
                                expr=expr)
                item["show"] = pretty(item["expr"])
                if task == "write":
                    item["answer"] = item["show"]
                else:
                    try:
                        x = evaluate(item["expr"], item.get("vars", {}))
                    except ValueError:
                        continue
                    if not _whole(x) or x > r.get("max_value", 200) or x < 1:
                        continue
                    item["answer"] = str(x)
                if check_item(item, r) is None:
                    break
            else:
                raise ValueError(f"expression_eval: form {form} of {task} never fits {r}")
            items.append(item)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["answer"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page
        from ..verify import banned_words

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        if _tidy.is_tidy(r):
            return _tidy.verify(sheet, r)
        task = r["task"]
        count = r.get("problems", FEWER.get(task, 12))
        items = sheet.items
        issues: list[Issue] = []
        if len(items) != count:
            issues.append(error(sheet, f"{len(items)} items; this part has {count}"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "items are not numbered 1, 2, 3… in order"))
        for i in items:
            if i.get("task") != task:
                issues.append(error(sheet, f"item {i.get('n')}: should be a {task!r} item"))
                continue
            why = check_item(i, r)
            if why:
                issues.append(error(sheet, f"item {i.get('n')}: {why}"))
            for w in banned_words(" ".join(str(i.get(k, "")) for k in ("show", "phrase", "answer"))):
                issues.append(error(sheet, f"item {i.get('n')}: printed text spells {w!r}"))
        forms = [i.get("form") for i in items]
        if len(set(forms)) != min(len(items), {"power": len(POWER_FORMS), "write": len(WRITE_FORMS),
                                              "substitute": len(SUB_FORMS), "formula": len(FORMULAS)}[task]):
            issues.append(error(sheet, "a form repeats before every form has been used"))
        if sheet.answer_key != [i.get("answer") for i in items]:
            issues.append(error(sheet, "answer key doesn't match the items"))
        return issues

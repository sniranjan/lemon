"""Fraction friends (Owls math): equivalent fractions with fraction bars (4.NF.1) and adding and taking
away fractions with the same denominator (4.NF.3a).

Rules (merged level → section → part):
- `tasks`: cycled over the page's problems, in order:
  - `bars`: two bars of the same length, the top cut into b parts with a shaded, the bottom cut into n × b
    parts with n × a shaded; the child writes the top number of the second fraction (a/b = □/nb).
  - `times`: a/b = □/d or a/b = c/□ (multiply top and bottom by the same number).
  - `divide`: c/d = □/b (the same fraction in bigger pieces: divide top and bottom by the same number).
  - `add`, `sub`: a/d + c/d or a/d − c/d, answer written as a fraction; sums stay within one whole;
    taking away starts below one whole and stays above 0 (mixed numbers are later).
- `denominators`: the bottom numbers allowed (grade 4: 2, 3, 4, 5, 6, 8, 10, 12, 100). Bars use at most 12 parts.
- `bars`: on add/sub pages, the first this many problems show a bar (shaded parts + striped parts, or
  shaded parts with the taken-away ones crossed out).
- `problems`: problems a page. `title`.

Every fraction is stored as whole numbers (top, bottom), so verify can check each one exactly.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules

TASKS = ("bars", "times", "divide", "add", "sub")
GRADE4_DENOMINATORS = {2, 3, 4, 5, 6, 8, 10, 12, 100}
MAX_BAR_PARTS = 12
MAX_TRIES = 20000


def kind_of(task: str) -> str:
    return {"bars": "bars", "times": "equiv", "divide": "equiv"}.get(task, "op")


def answer_text(item: dict) -> str:
    k = item["kind"]
    if k == "bars":
        return f"{item['a']}/{item['b']} = {item['a'] * item['n']}/{item['b'] * item['n']}"
    if k == "equiv":
        (a, b), (c, d) = item["left"], item["right"]
        return f"{a}/{b} = {c}/{d}"
    return f"{op_result(item)}/{item['den']}"


def op_result(item: dict) -> int:
    return item["a"] + item["c"] if item["op"] == "add" else item["a"] - item["c"]


def _pairs(dens: list[int], limit: int | None = None) -> list[tuple[int, int]]:
    """(small bottom, big bottom) pairs where the big one is a whole number times the small one."""
    return [(b, d) for b in dens for d in dens if d > b and d % b == 0 and (limit is None or d <= limit)
            and (d != 100 or b == 10)]   # hundredths only from tenths (3/10 = 30/100)


def _make(task: str, r: dict, rng, index: int) -> dict:
    dens = sorted(r["denominators"])
    if task == "bars":
        b, d = rng.choice(_pairs(dens, MAX_BAR_PARTS))
        return {"kind": "bars", "a": rng.randint(1, b - 1), "b": b, "n": d // b}
    if task in ("times", "divide"):
        b, d = rng.choice(_pairs(dens))
        a = rng.randint(1, b - 1)
        small, big = [a, b], [a * d // b, d]
        if task == "times":
            return {"kind": "equiv", "dir": "times", "left": small, "right": big, "blank": rng.choice(["num", "den"])}
        return {"kind": "equiv", "dir": "divide", "left": big, "right": small, "blank": "num"}
    den = rng.choice([x for x in dens if x <= MAX_BAR_PARTS])
    if task == "add":
        a = rng.randint(1, den - 1)
        c = rng.randint(1, den - a)
    else:
        a = rng.randint(1, den - 1)
        c = rng.randint(1, a)
    return {"kind": "op", "op": task, "den": den, "a": a, "c": c, "bar": index < r.get("bars", 0)}


def _key(item: dict) -> tuple:
    return tuple(sorted((k, str(v)) for k, v in item.items() if k not in ("bar", "blank", "n_")))


def item_ok(item: dict, task: str, r: dict) -> str | None:
    dens = set(r["denominators"])
    k = item["kind"]
    if k != kind_of(task):
        return f"a {k} problem where the part asks for {task}"
    if k == "bars":
        a, b, n = item["a"], item["b"], item["n"]
        if b not in dens or b * n not in dens or not dens <= GRADE4_DENOMINATORS:
            return f"{a}/{b} = ?/{b * n}: bottom numbers must be from {sorted(dens)}"
        if n < 2 or b * n > MAX_BAR_PARTS or not 1 <= a < b:
            return f"{a}/{b} with {n} times as many parts doesn't fit a bar (at most {MAX_BAR_PARTS} parts)"
        return None
    if k == "equiv":
        (a, b), (c, d) = item["left"], item["right"]
        if b not in dens or d not in dens or not dens <= GRADE4_DENOMINATORS:
            return f"{a}/{b} = {c}/{d}: bottom numbers must be from {sorted(dens)}"
        if a * d != b * c:
            return f"{a}/{b} and {c}/{d} aren't equal"
        if not (0 < a < b and 0 < c < d):
            return f"{a}/{b} = {c}/{d}: fractions here are between 0 and 1"
        if item["dir"] != task or (task == "times") != (d > b) or max(b, d) % min(b, d):
            return f"{a}/{b} = {c}/{d} isn't a {task} problem"
        if item["blank"] not in (("num", "den") if task == "times" else ("num",)):
            return f"{a}/{b} = {c}/{d}: unknown blank {item['blank']!r}"
        return None
    den, a, c = item["den"], item["a"], item["c"]
    if item["op"] != task:
        return f"{item['op']} problem where the part asks for {task}"
    if den not in dens or den > MAX_BAR_PARTS:
        return f"bottom number {den} isn't used here"
    if a < 1 or c < 1:
        return "both fractions need at least one part"
    if task == "add" and a + c > den:
        return f"{a}/{den} + {c}/{den} is more than one whole"
    if task == "sub" and (a - c < 1 or a >= den):
        return f"{a}/{den} − {c}/{den}: start below one whole and stay above 0"
    return None


@register("fraction_bars")
class FractionBars(SheetType):
    template = "fraction_bars.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        for t in r["tasks"]:
            if t not in TASKS:
                raise ValueError(f"fraction_bars: unknown task {t!r} (use one of {', '.join(TASKS)})")
        n = r.get("problems", 4)
        items, seen = [], set()
        for idx in range(n):
            task = r["tasks"][idx % len(r["tasks"])]
            for _ in range(MAX_TRIES):
                item = _make(task, r, rng, idx)
                if _key(item) not in seen and item_ok(item, task, r) is None:
                    break
            else:
                raise ValueError(f"fraction_bars: can't find a {task} problem with these rules: {r}")
            seen.add(_key(item))
            items.append({"n_": idx + 1, **item})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer_text(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        issues: list[Issue] = []
        n = r.get("problems", 4)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} problems; the part asks for {n}"))
        seen = set()
        for idx, item in enumerate(sheet.items):
            task = r["tasks"][idx % len(r["tasks"])]
            why = item_ok(item, task, r)
            if why:
                issues.append(error(sheet, f"problem {idx + 1}: {why}"))
            if item.get("n_") != idx + 1:
                issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
            if item["kind"] == "op" and item["bar"] != (idx < r.get("bars", 0)):
                issues.append(error(sheet, f"problem {idx + 1}: only the first {r.get('bars', 0)} problems show a bar"))
            if _key(item) in seen:
                issues.append(error(sheet, f"problem {idx + 1} appears twice"))
            seen.add(_key(item))
        expected = [answer_text(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the problems {expected}"))
        return issues

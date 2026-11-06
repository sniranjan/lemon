"""Adding and taking-away facts within 20 (Puppies math), in four layouts.

Each fact is `a op b = c` with one empty box: `blank: c` (the answer) or `blank: b` (a missing
number, 1.OA.8). Rules (merged level → section → part, see syllabus/math/M1.yaml):
- `ops`: "+" and/or "-". Items store ASCII "-"; the template prints a real minus sign.
- `amounts`: the number added or taken away (b). `first`: [lo, hi] for a.
- `turnarounds`: adding facts may also show the amount first (9 + 3 next to 3 + 9).
- `max_total`: no sum above it. Taking away never goes below 0.
- `blanks`: which box is empty ("c" or "b"). `title`: the sheet title.
- `layouts`: pages cycle through them, counted from the first page of the part (or section):
  `horizontal` 12 facts in two columns · `vertical` 12 column facts in a 4 × 3 grid ·
  `bridge` 4 number tracks (count on / count back, amounts ≤ 3) above 6 facts ·
  `families` 3 fact families (a + b, b + a, c − b, c − a).

Facts are numbered `n` = 1, 2, … in reading order (shown small for grown-ups); `answer_key`
lists the empty boxes in that order, so the answers page lines up with the sheet.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

COUNTS = {"horizontal": 12, "vertical": 12, "bridge": 10, "families": 3}
BRIDGE_ROWS = 4
BRIDGE_MAX = 3


def _layout(subject: str, level: str, page: int, layouts: list[str]) -> str:
    from ..syllabus import load_level

    section = load_level(subject, level).section_for_page(page)
    part = section.part_for_page(page)
    first = (part.pages if part else section.pages)[0]
    return layouts[(page - first) % len(layouts)]


def _value(a: int, op: str, b: int) -> int:
    return a + b if op == "+" else a - b


def _fact(a: int, op: str, b: int, blank: str) -> dict:
    c = _value(a, op, b)
    return {"kind": "fact", "a": a, "op": op, "b": b, "c": c, "blank": blank}


def _amount_of(f: dict, turnarounds: bool, amounts: list[int], first: list[int]) -> set[int]:
    """The amount(s) a fact practises: b, or (turned around) a."""
    out = {f["b"]} if f["b"] in amounts else set()
    if f["op"] == "+" and turnarounds and f["a"] in amounts and first[0] <= f["b"] <= first[1]:
        out.add(f["a"])
    return out


def fact_ok(f: dict, r: dict) -> str | None:
    """Why fact `f` breaks the part's rules, or None."""
    lo, hi = r["first"]
    a, op, b = f["a"], f["op"], f["b"]
    if op not in r["ops"]:
        return f"sign {op!r} isn't used in this part (only {r['ops']})"
    c = _value(a, op, b)
    if c < 0:
        return f"{a} {op} {b} is below zero"
    if c > r.get("max_total", 20):
        return f"{a} {op} {b} = {c} is above {r.get('max_total', 20)}"
    plain = lo <= a <= hi and b in r["amounts"]
    turned = op == "+" and r.get("turnarounds") and lo <= b <= hi and a in r["amounts"]
    if not (plain or turned):
        return f"{a} {op} {b}: needs a first number {lo}–{hi} and an amount in {r['amounts']}"
    return None


def _pool(r: dict, op: str) -> list[tuple[int, str, int]]:
    lo, hi = r["first"]
    out = []
    for x in range(lo, hi + 1):
        for y in r["amounts"]:
            for a, b in ((x, y), (y, x)) if op == "+" and r.get("turnarounds") else ((x, y),):
                if (a, op, b) not in out and fact_ok({"a": a, "op": op, "b": b}, r) is None:
                    out.append((a, op, b))
    return out


def _same(t: tuple[int, str, int]) -> tuple:
    """3 + 9 and 9 + 3 count as one fact when picking a sheet's facts."""
    a, op, b = t
    return (op, min(a, b), max(a, b)) if op == "+" else t


def pick_facts(ctx: GenContext, count: int, max_amount: int | None = None) -> list[tuple[int, str, int]]:
    r = ctx.rules
    pools = {op: [t for t in _pool(r, op) if max_amount is None or t[2] <= max_amount] for op in r["ops"]}
    if len({t for p in pools.values() for t in p}) < count:
        raise ValueError(f"fact_drill: only {len(distinct)} different facts fit this part's rules; "
                         f"a page needs {count}")
    picked: list[tuple[int, str, int]] = []
    used: set[tuple] = set()

    short_ok = False

    def take(options: list[tuple[int, str, int]]) -> bool:
        # a fact and its turnaround (3 + 9, 9 + 3) share a page only when the part has too few facts
        if any(_value(*t) == 0 for t in picked):   # at most one "take away all" fact a page
            options = [t for t in options if _value(*t) != 0]
        options = [t for t in options if _same(t) not in used] or \
                  [t for t in options if t not in picked and short_ok]
        if not options:
            return False
        t = ctx.rng.choice(options)
        picked.append(t)
        used.add(_same(t))
        return True

    # every sign and every amount at least once
    needs = [(op, k) for op in r["ops"] for k in r["amounts"] if max_amount is None or k <= max_amount]
    ctx.rng.shuffle(needs)
    for op, k in needs[:count]:
        take([t for t in pools[op] if t[2] == k or (op == "+" and t[0] == k)])
    i = 0
    while len(picked) < count:   # then fill, keeping the signs balanced
        op = r["ops"][i % len(r["ops"])]
        if not take(pools[op]) and not take([t for p in pools.values() for t in p]):
            if short_ok:
                raise ValueError("fact_drill: ran out of facts")
            short_ok = True
        i += 1
    ctx.rng.shuffle(picked)
    return picked


def _bridge(f: dict) -> dict:
    lo, hi = sorted((f["a"], f["c"]))
    return {**f, "track": list(range(lo, hi + 1))}


def all_facts(items: list[dict]) -> list[dict]:
    return [f for i in items for f in (i["facts"] if i["kind"] == "family" else [i])]


@register("fact_drill")
class FactDrill(SheetType):
    template = "fact_drill.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, spec = ctx.rules, ctx.spec
        layout = _layout(spec.subject, spec.level, spec.page, r["layouts"])
        if layout == "families":
            items = self._families(ctx)
        else:
            facts = []
            if layout == "bridge":
                if max(r["amounts"]) > BRIDGE_MAX:
                    raise ValueError(f"fact_drill: bridge tracks only go up to {BRIDGE_MAX} hops")
                if r["blanks"] != ["c"]:
                    raise ValueError("fact_drill: bridge tracks need blanks [c]")
            for t in pick_facts(ctx, COUNTS[layout]):
                facts.append(_fact(*t, blank=ctx.rng.choice(r["blanks"])))
            if layout == "bridge":
                facts = [_bridge(f) for f in facts[:BRIDGE_ROWS]] + facts[BRIDGE_ROWS:]
            items = facts
        for i in items:
            i["layout"] = layout
        for n, f in enumerate(all_facts(items), 1):
            f["n"] = n
        answers = [f[f["blank"]] for f in all_facts(items)]
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name),
                            items=items, answer_key=answers)

    def _families(self, ctx: GenContext) -> list[dict]:
        r = ctx.rules
        lo, hi = r["first"]
        triples = sorted({(min(a, b), max(a, b)) for a in range(lo, hi + 1) for b in r["amounts"]
                          if a != b and a + b <= r.get("max_total", 20)})
        if len(triples) < COUNTS["families"]:
            raise ValueError("fact_drill: too few fact families in this part")
        items = []
        for x, y in ctx.rng.sample(triples, COUNTS["families"]):
            a, b = (x, y) if ctx.rng.random() < 0.5 else (y, x)
            c = a + b
            items.append({"kind": "family", "numbers": [a, b, c],
                          "facts": [_fact(a, "+", b, "c"), _fact(b, "+", a, "c"),
                                    _fact(c, "-", b, "c"), _fact(c, "-", a, "c")]})
        return items

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        layout = _layout(sheet.subject, sheet.level, sheet.page_number, r["layouts"])
        issues: list[Issue] = []
        items = sheet.items
        if len(items) != COUNTS[layout]:
            issues.append(error(sheet, f"{len(items)} items; a {layout} page has {COUNTS[layout]}"))
        if any(i["kind"] != ("family" if layout == "families" else "fact") or i.get("layout") != layout
               for i in items):
            issues.append(error(sheet, f"a {layout} page has the wrong kind of item"))
            return issues
        facts = all_facts(items)
        if [f.get("n") for f in facts] != list(range(1, len(facts) + 1)):
            issues.append(error(sheet, "facts are not numbered 1, 2, 3… in order"))
        for f in facts:
            label = f"{f['a']} {f['op']} {f['b']}"
            if f["c"] != _value(f["a"], f["op"], f["b"]):
                issues.append(error(sheet, f"{label} = {f['c']} is wrong"))
            why = None if layout == "families" else fact_ok(f, r)
            if why:
                issues.append(error(sheet, why))
            allowed = ["c"] if layout == "families" else r["blanks"]
            if f["blank"] not in allowed:
                issues.append(error(sheet, f"{label}: empty box {f['blank']!r}, this part uses {allowed}"))
        keys = [(f["a"], f["op"], f["b"]) for f in facts]
        if layout != "families" and len(set(keys)) != len(keys):
            issues.append(error(sheet, "the same fact is on the page twice"))
        if layout != "families" and sum(f["c"] == 0 for f in facts) > 1:
            issues.append(error(sheet, "more than one fact with the answer 0"))
        expected = [f[f["blank"]] for f in facts]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the facts {expected}"))
        if layout != "families":
            for op in r["ops"]:
                if not any(f["op"] == op for f in facts):
                    issues.append(error(sheet, f"no {op!r} fact on the page"))
            covered = {k for f in facts for k in _amount_of(f, r.get("turnarounds", False), r["amounts"], r["first"])}
            missing = [k for k in r["amounts"] if k not in covered]
            if missing and len(r["amounts"]) * len(r["ops"]) <= len(facts):
                issues.append(error(sheet, f"amounts {missing} never appear on the page"))
        if layout == "bridge":
            tracks = [f for f in facts if "track" in f]
            if [f["n"] for f in tracks] != list(range(1, BRIDGE_ROWS + 1)):
                issues.append(error(sheet, f"the first {BRIDGE_ROWS} facts should have number tracks"))
            for f in tracks:
                lo, hi = sorted((f["a"], f["c"]))
                if f["track"] != list(range(lo, hi + 1)):
                    issues.append(error(sheet, f"track {f['track']} doesn't run from {f['a']} to {f['c']}"))
                if not 1 <= f["b"] <= BRIDGE_MAX or f["blank"] != "c":
                    issues.append(error(sheet, f"track for {f['a']} {f['op']} {f['b']} needs 1–{BRIDGE_MAX} hops"))
        if layout == "families":
            for i in items:
                a, b, c = i["numbers"]
                want = [(a, "+", b), (b, "+", a), (c, "-", b), (c, "-", a)]
                if a == b or c != a + b or c > r.get("max_total", 20) or [(f["a"], f["op"], f["b"]) for f in i["facts"]] != want:
                    issues.append(error(sheet, f"family {i['numbers']} doesn't have its four facts"))
                lo, hi = r["first"]
                if not ((lo <= a <= hi and b in r["amounts"]) or (lo <= b <= hi and a in r["amounts"])):
                    issues.append(error(sheet, f"family {i['numbers']} is outside this part's numbers"))
            fams = [frozenset(i["numbers"]) for i in items]
            if len(set(fams)) != len(fams):
                issues.append(error(sheet, "the same family is on the page twice"))
        return issues

"""Number facts: adding and taking away within 20 (Puppies math), times and sharing facts within
100 (Foxes math).

Each fact is `a op b = c` with one empty box: `blank: c` (the answer) or `blank: b` (a missing
number, 1.OA.8). Rules (merged level → section → part, see syllabus/math/M1.yaml):
- `ops`: "+", "-", "*", "/". Items store ASCII; the template prints −, × and ÷.
- `amounts`: the number added, taken away, multiplied by or shared by (b). `first`: [lo, hi] for a;
  for "/" it is the range of the answer, so every sharing fact is a times fact backwards
  (`q * b / b`) and always comes out even.
- `turnarounds`: adding and times facts may also show the amount first (9 + 3 next to 3 + 9).
- `max_total`: no sum or product above it (dividends too). Taking away never goes below 0.
- `blanks`: which box is empty ("c" or "b"). `title`: the sheet title.
- `layouts`: pages cycle through them, counted from the first page of the part (or section):
  `horizontal` 12 facts in two columns · `vertical` 12 column facts in a 4 × 3 grid ·
  `bridge` 4 number tracks (count on / count back, amounts ≤ 3) above 6 facts ·
  `families` 3 fact families (a + b, b + a, c − b, c − a; or a × b, b × a, c ÷ b, c ÷ a).
  Times and sharing layouts (Foxes math):
  `skip` a skip-counting track (b, 2b … 10b with 4 empty cells) above 8 facts of that table ·
  `arrays` 4 dot arrays (a rows of b dots for a × b; b rows for c ÷ b) beside their fact ·
  `pairs` 6 rows of "box × b = c" next to "c ÷ b = box" (sharing is the times table backwards).

Facts are numbered `n` = 1, 2, … in reading order (shown small for grown-ups); `answer_key`
lists the empty boxes in that order, so the answers page lines up with the sheet.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules, part_offset

COUNTS = {"horizontal": 12, "vertical": 12, "bridge": 10, "families": 3, "skip": 9, "arrays": 4, "pairs": 6}
SKIP_FACTS = 8
SKIP_LEN = 10
SKIP_BLANKS = 4
TURNS = ("+", "*")   # signs whose facts can be turned around
BRIDGE_ROWS = 4
BRIDGE_MAX = 3


def _layout(subject: str, level: str, page: int, layouts: list[str]) -> str:
    return layouts[part_offset(subject, level, page) % len(layouts)]


def _value(a: int, op: str, b: int) -> int:
    if op == "*":
        return a * b
    if op == "/":
        return a // b
    return a + b if op == "+" else a - b


def _fact(a: int, op: str, b: int, blank: str) -> dict:
    c = _value(a, op, b)
    return {"kind": "fact", "a": a, "op": op, "b": b, "c": c, "blank": blank}


def _amount_of(f: dict, turnarounds: bool, amounts: list[int], first: list[int]) -> set[int]:
    """The amount(s) a fact practises: b, or (turned around) a."""
    out = {f["b"]} if f["b"] in amounts else set()
    if f["op"] in TURNS and turnarounds and f["a"] in amounts and first[0] <= f["b"] <= first[1]:
        out.add(f["a"])
    return out


def fact_ok(f: dict, r: dict) -> str | None:
    """Why fact `f` breaks the part's rules, or None."""
    lo, hi = r["first"]
    a, op, b = f["a"], f["op"], f["b"]
    if op not in r["ops"]:
        return f"sign {op!r} isn't used in this part (only {r['ops']})"
    if op == "/":
        if b == 0 or a % b:
            return f"{a} / {b} doesn't come out even"
        if a > r.get("max_total", 20):
            return f"{a} / {b}: {a} is above {r.get('max_total', 20)}"
        if not (lo <= a // b <= hi and b in r["amounts"]):
            return f"{a} / {b}: needs an answer {lo}–{hi} and an amount in {r['amounts']}"
        return None
    c = _value(a, op, b)
    if c < 0:
        return f"{a} {op} {b} is below zero"
    if c > r.get("max_total", 20):
        return f"{a} {op} {b} = {c} is above {r.get('max_total', 20)}"
    plain = lo <= a <= hi and b in r["amounts"]
    turned = op in TURNS and r.get("turnarounds") and lo <= b <= hi and a in r["amounts"]
    if not (plain or turned):
        return f"{a} {op} {b}: needs a first number {lo}–{hi} and an amount in {r['amounts']}"
    return None


def _pool(r: dict, op: str) -> list[tuple[int, str, int]]:
    lo, hi = r["first"]
    out = []
    for x in range(lo, hi + 1):
        for y in r["amounts"]:
            if op == "/":   # the times fact x * y backwards
                if fact_ok({"a": x * y, "op": op, "b": y}, r) is None:
                    out.append((x * y, op, y))
                continue
            for a, b in ((x, y), (y, x)) if op in TURNS and r.get("turnarounds") else ((x, y),):
                if (a, op, b) not in out and fact_ok({"a": a, "op": op, "b": b}, r) is None:
                    out.append((a, op, b))
    return out


def _same(t: tuple[int, str, int]) -> tuple:
    """3 + 9 and 9 + 3 count as one fact when picking a sheet's facts."""
    a, op, b = t
    return (op, min(a, b), max(a, b)) if op in TURNS else t


def pick_facts(ctx: GenContext, count: int, max_amount: int | None = None,
               rules: dict | None = None) -> list[tuple[int, str, int]]:
    r = ctx.rules if rules is None else rules
    pools = {op: [t for t in _pool(r, op) if max_amount is None or t[2] <= max_amount] for op in r["ops"]}
    distinct = {t for p in pools.values() for t in p}
    if len(distinct) < count:
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
        take([t for t in pools[op] if t[2] == k or (op in TURNS and t[0] == k)])
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
    """Every fact on the page in reading order (a skip-counting track is not a fact)."""
    return [f for i in items if i["kind"] != "track"
            for f in (i["facts"] if i["kind"] in ("family", "pair") else [i])]


def answers_of(items: list[dict]) -> list[int]:
    """The empty boxes in reading order: track cells left to right, then the facts."""
    track = [i["cells"][k] for i in items if i["kind"] == "track" for k in i["blanks"]]
    return track + [f[f["blank"]] for f in all_facts(items)]


def _times(r: dict) -> bool:
    return bool(set(r["ops"]) & {"*", "/"})


def _kinds(layout: str) -> list[str]:
    if layout == "skip":
        return ["track"] + ["fact"] * SKIP_FACTS
    one = {"families": "family", "pairs": "pair"}.get(layout, "fact")
    return [one] * COUNTS[layout]


@register("fact_drill")
class FactDrill(SheetType):
    template = "fact_drill.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, spec = ctx.rules, ctx.spec
        layout = _layout(spec.subject, spec.level, spec.page, r["layouts"])
        if layout == "families":
            items = self._families(ctx)
        elif layout in ("skip", "arrays", "pairs"):
            items = self._times_layout(ctx, layout)
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
        answers = answers_of(items)
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name),
                            items=items, answer_key=answers)

    def _times_layout(self, ctx: GenContext, layout: str) -> list[dict]:
        r = ctx.rules
        if not _times(r):
            raise ValueError(f"fact_drill: the {layout} layout is for times and sharing facts")
        if layout == "skip":
            k = ctx.rng.choice(r["amounts"])
            blanks = sorted(ctx.rng.sample(range(1, SKIP_LEN), SKIP_BLANKS))
            track = {"kind": "track", "step": k, "cells": [k * (i + 1) for i in range(SKIP_LEN)],
                     "blanks": blanks}
            one = {**r, "amounts": [k], "ops": ["*"]}
            return [track] + [_fact(*t, blank="c") for t in pick_facts(ctx, SKIP_FACTS, rules=one)]
        if layout == "arrays":
            facts = [_fact(*t, blank="c") for t in pick_facts(ctx, COUNTS[layout])]
            for f in facts:
                # a × b: a rows of b dots; c ÷ b: the c dots shared into b rows
                f["rows"], f["cols"] = (f["a"], f["b"]) if f["op"] == "*" else (f["b"], f["c"])
            return facts
        # pairs: "box × b = c" next to "c ÷ b = box"
        share = {**r, "ops": ["/"]}
        items = []
        for a, _, b in pick_facts(ctx, COUNTS[layout], rules=share):
            q = a // b
            items.append({"kind": "pair", "facts": [_fact(q, "*", b, "a"), _fact(a, "/", b, "c")]})
        return items

    def _families(self, ctx: GenContext) -> list[dict]:
        r = ctx.rules
        if _times(r):
            return self._times_families(ctx)
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

    def _times_families(self, ctx: GenContext) -> list[dict]:
        r = ctx.rules
        lo, hi = r["first"]
        pairs = sorted({(min(a, b), max(a, b)) for a in range(lo, hi + 1) for b in r["amounts"]
                        if a != b and a * b <= r.get("max_total", 100)})
        if len(pairs) < COUNTS["families"]:
            raise ValueError("fact_drill: too few fact families in this part")
        items = []
        for x, y in ctx.rng.sample(pairs, COUNTS["families"]):
            a, b = (x, y) if ctx.rng.random() < 0.5 else (y, x)
            c = a * b
            items.append({"kind": "family", "numbers": [a, b, c],
                          "facts": [_fact(a, "*", b, "c"), _fact(b, "*", a, "c"),
                                    _fact(c, "/", b, "c"), _fact(c, "/", a, "c")]})
        return items

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        layout = _layout(sheet.subject, sheet.level, sheet.page_number, r["layouts"])
        issues: list[Issue] = []
        items = sheet.items
        if len(items) != COUNTS[layout]:
            issues.append(error(sheet, f"{len(items)} items; a {layout} page has {COUNTS[layout]}"))
        if [i["kind"] for i in items] != _kinds(layout) or any(i.get("layout") != layout for i in items):
            issues.append(error(sheet, f"a {layout} page has the wrong kind of item"))
            return issues
        facts = all_facts(items)
        if [f.get("n") for f in facts] != list(range(1, len(facts) + 1)):
            issues.append(error(sheet, "facts are not numbered 1, 2, 3… in order"))
        for f in facts:
            label = f"{f['a']} {f['op']} {f['b']}"
            if f["c"] != _value(f["a"], f["op"], f["b"]):
                issues.append(error(sheet, f"{label} = {f['c']} is wrong"))
            why = None if layout in ("families", "pairs", "skip") else fact_ok(f, r)
            if why:
                issues.append(error(sheet, why))
            allowed = ["c"] if layout in ("families", "skip", "arrays") else ["a", "c"] if layout == "pairs" \
                else r["blanks"]
            if f["blank"] not in allowed:
                issues.append(error(sheet, f"{label}: empty box {f['blank']!r}, this part uses {allowed}"))
        keys = [(f["a"], f["op"], f["b"]) for f in facts]
        if layout != "families" and len(set(keys)) != len(keys):
            issues.append(error(sheet, "the same fact is on the page twice"))
        if layout != "families" and sum(f["c"] == 0 for f in facts) > 1:
            issues.append(error(sheet, "more than one fact with the answer 0"))
        expected = answers_of(items)
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the facts {expected}"))
        if layout == "skip":
            issues += self._check_skip(sheet, items, r)
        elif layout == "arrays":
            for f in facts:
                want = (f["a"], f["b"]) if f["op"] == "*" else (f["b"], f["c"])
                if (f.get("rows"), f.get("cols")) != want:
                    issues.append(error(sheet, f"array for {f['a']} {f['op']} {f['b']} should be "
                                               f"{want[0]} rows of {want[1]}"))
        elif layout == "pairs":
            for i in items:
                times, share = i["facts"]
                if times["op"] != "*" or share["op"] != "/" or times["blank"] != "a" or share["blank"] != "c" \
                        or (times["a"], times["b"], times["c"]) != (share["c"], share["b"], share["a"]):
                    issues.append(error(sheet, f"pair {times['a']} * {times['b']} and {share['a']} / {share['b']} "
                                               f"isn't a times fact and its sharing fact"))
                why = fact_ok(share, r)
                if why:
                    issues.append(error(sheet, why))
        if layout not in ("families", "skip", "pairs"):
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
            add, back = ("*", "/") if _times(r) else ("+", "-")
            for i in items:
                a, b, c = i["numbers"]
                want = [(a, add, b), (b, add, a), (c, back, b), (c, back, a)]
                if a == b or c != _value(a, add, b) or c > r.get("max_total", 20) \
                        or [(f["a"], f["op"], f["b"]) for f in i["facts"]] != want:
                    issues.append(error(sheet, f"family {i['numbers']} doesn't have its four facts"))
                lo, hi = r["first"]
                if not ((lo <= a <= hi and b in r["amounts"]) or (lo <= b <= hi and a in r["amounts"])):
                    issues.append(error(sheet, f"family {i['numbers']} is outside this part's numbers"))
            fams = [frozenset(i["numbers"]) for i in items]
            if len(set(fams)) != len(fams):
                issues.append(error(sheet, "the same family is on the page twice"))
        return issues

    def _check_skip(self, sheet: Sheet, items: list[dict], r: dict) -> list[Issue]:
        issues = []
        track, facts = items[0], items[1:]
        k = track["step"]
        if k not in r["amounts"]:
            issues.append(error(sheet, f"skip-counting by {k}, but this part's tables are {r['amounts']}"))
        if track["cells"] != [k * (i + 1) for i in range(SKIP_LEN)]:
            issues.append(error(sheet, f"the track doesn't count by {k} from {k} to {k * SKIP_LEN}"))
        b = track["blanks"]
        if len(b) != SKIP_BLANKS or b != sorted(set(b)) or not all(1 <= x < SKIP_LEN for x in b):
            issues.append(error(sheet, f"the track needs {SKIP_BLANKS} empty cells after the first"))
        for f in facts:
            if f["op"] != "*" or k not in (f["a"], f["b"]) or f["c"] not in track["cells"]:
                issues.append(error(sheet, f"{f['a']} * {f['b']} isn't in the {k} times table on the track"))
            why = fact_ok(f, {**r, "amounts": [k], "ops": ["*"]})
            if why:
                issues.append(error(sheet, why))
        return issues

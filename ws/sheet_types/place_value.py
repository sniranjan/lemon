"""Cubs math (M2-A/B): place value. `rules.mode` picks the page:

- `blocks`: base-ten pictures (hundred squares, tens bars, ones) to write as
  "☐ hundreds ☐ tens ☐ ones = ☐". Two-digit pages show 4, three-digit pages 3.
  Three-digit pages always include a number with a zero digit (706 = 7 hundreds, 0 tens, 6 ones).
- `expanded`: six lines, cycling through `forms`:
  `parts_to_number` "300 + 40 + 7 = ☐" (zero parts left out), `number_to_parts` "347 = ☐ + ☐ + ☐"
  (no zero digits), `units_to_number` "3 hundreds 4 tens 7 ones = ☐", `name_to_number`
  "three hundred forty-seven = ☐".
- `compare`: six pairs "347 ◯ 374" to write <, > or =; at most one pair is equal, and both
  < and > turn up.

`min`, `max`: the part's number range.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

MODES = ("blocks", "expanded", "compare")
FORMS = ("parts_to_number", "number_to_parts", "units_to_number", "name_to_number")
LINES = 6
PLACE_NAMES = ("ones", "tens", "hundreds")

_ONES = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
         "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def number_name(n: int) -> str:
    """US number name, no "and": 347 → "three hundred forty-seven"."""
    if not 1 <= n <= 999:
        raise ValueError(f"number_name: {n} is outside 1–999")
    h, rest = divmod(n, 100)
    words = [f"{_ONES[h]} hundred"] if h else []
    if rest >= 20:
        words.append(_TENS[rest // 10] + (f"-{_ONES[rest % 10]}" if rest % 10 else ""))
    elif rest:
        words.append(_ONES[rest])
    return " ".join(words)


def places(n: int, width: int) -> list[int]:
    """Digits, biggest place first: places(347, 3) = [3, 4, 7]."""
    return [n // 10 ** p % 10 for p in reversed(range(width))]


def parts(n: int) -> list[int]:
    """Expanded form without zero parts: 307 → [300, 7]."""
    width = len(str(n))
    return [d * 10 ** p for d, p in zip(places(n, width), reversed(range(width))) if d]


def blocks_item(n: int, width: int) -> dict:
    return {"kind": "blocks", "n": n, "places": places(n, width), "width": width}


def expanded_item(n: int, form: str) -> dict:
    width = len(str(n))
    item = {"kind": "expanded", "form": form, "n": n, "width": width, "places": places(n, width)}
    if form in ("parts_to_number", "number_to_parts"):
        item["parts"] = parts(n)
    if form == "units_to_number":
        item["units"] = [{"count": d, "name": PLACE_NAMES[p]} for d, p in zip(places(n, width), reversed(range(width)))]
    if form == "name_to_number":
        item["name"] = number_name(n)
    return item


def expanded_answer(item: dict):
    return " + ".join(map(str, item["parts"])) if item["form"] == "number_to_parts" else item["n"]


def compare_symbol(a: int, b: int) -> str:
    return "<" if a < b else ">" if a > b else "="


def _compare_pair(rng, lo: int, hi: int, kind: str) -> tuple[int, int]:
    """A pair that makes the child look at one place: the hundreds, the tens, the ones, or swapped digits."""
    for _ in range(1000):
        a = rng.randint(lo, hi)
        h, t, o = places(a, 3)
        if kind == "hundreds":
            b = rng.randint(1, 9) * 100 + rng.randint(0, 9) * 10 + rng.randint(0, 9)
        elif kind == "tens":
            b = h * 100 + rng.randint(0, 9) * 10 + rng.randint(0, 9)
        elif kind == "ones":
            b = h * 100 + t * 10 + rng.randint(0, 9)
        elif kind == "swap":
            b = h * 100 + o * 10 + t
        else:
            b = a
        if lo <= b <= hi and (kind == "equal") == (a == b) and (kind != "hundreds" or b // 100 != h) \
                and (kind != "tens" or (b // 10) % 10 != t):
            return (a, b) if rng.random() < 0.5 else (b, a)
    raise ValueError(f"place_value: can't make a {kind} pair in {lo}–{hi}")


@register("place_value")
class PlaceValue(SheetType):
    template = "place_value.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        lo, hi, mode = r["min"], r["max"], r["mode"]
        if mode not in MODES:
            raise ValueError(f"place_value: unknown mode {mode!r} (use one of {', '.join(MODES)})")
        width = len(str(hi))
        if mode == "blocks":
            count = 4 if width == 2 else 3
            while True:
                numbers = rng.sample(range(lo, hi + 1), count)
                if width < 3 or any(0 in places(n, 3)[1:] for n in numbers):
                    break
            items = [blocks_item(n, width) for n in numbers]
            title = "Tens and ones" if width == 2 else "Hundreds, tens, ones"
            answers = [i["n"] for i in items]
        elif mode == "expanded":
            forms = r["forms"]
            if any(f not in FORMS for f in forms):
                raise ValueError(f"place_value: unknown form in {forms} (use {', '.join(FORMS)})")
            items, used = [], set()
            for k in range(LINES):
                form = forms[k % len(forms)]
                while True:
                    n = rng.randint(lo, hi)
                    if n not in used and (form != "number_to_parts" or 0 not in places(n, len(str(n)))):
                        break
                used.add(n)
                items.append(expanded_item(n, form))
            rng.shuffle(items)
            title = "Numbers in parts"
            answers = [expanded_answer(i) for i in items]
        else:
            kinds = ["hundreds", "tens", "tens", "ones", "swap", rng.choice(["equal", "ones", "hundreds"])]
            while True:
                rng.shuffle(kinds)
                items = [{"kind": "compare", "left": a, "right": b}
                         for a, b in (_compare_pair(rng, lo, hi, k) for k in kinds)]
                symbols = [compare_symbol(i["left"], i["right"]) for i in items]
                if "<" in symbols and ">" in symbols:
                    break
            title = "Bigger or smaller?"
            answers = symbols
        return SheetContent(title=title, parent_tip=ctx.tip(f"place_value_{mode}"), items=items,
                            answer_key=answers)

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        lo, hi, mode = r["min"], r["max"], r["mode"]
        issues, answers = [], []
        numbers = [n for i in sheet.items for n in ([i["left"], i["right"]] if i["kind"] == "compare" else [i["n"]])]
        for n in numbers:
            if not lo <= n <= hi:
                issues.append(error(sheet, f"{n} is outside this part's range {lo}–{hi}"))
        if any(i["kind"] != {"blocks": "blocks", "expanded": "expanded", "compare": "compare"}[mode]
               for i in sheet.items):
            issues.append(error(sheet, f"items don't match the part's mode {mode}"))
            return issues
        width = len(str(hi))
        if mode == "blocks":
            if len(sheet.items) != (4 if width == 2 else 3):
                issues.append(error(sheet, f"{len(sheet.items)} pictures on a {width}-digit page"))
            for i in sheet.items:
                if i["places"] != places(i["n"], width) or i["width"] != width:
                    issues.append(error(sheet, f"blocks {i['places']} don't show {i['n']}"))
                answers.append(i["n"])
            if width == 3 and not any(0 in i["places"][1:] for i in sheet.items):
                issues.append(error(sheet, "a three-digit blocks page needs a number with a zero"))
        elif mode == "expanded":
            if len(sheet.items) != LINES:
                issues.append(error(sheet, f"{len(sheet.items)} lines; expected {LINES}"))
            if {i["form"] for i in sheet.items} != set(r["forms"]):
                issues.append(error(sheet, f"forms {sorted({i['form'] for i in sheet.items})} aren't the part's {r['forms']}"))
            for i in sheet.items:
                n, form = i["n"], i["form"]
                if form in ("parts_to_number", "number_to_parts") and (sum(i["parts"]) != n or i["parts"] != parts(n)):
                    issues.append(error(sheet, f"parts {i['parts']} don't make {n}"))
                if form == "number_to_parts" and len(i["parts"]) != len(str(n)):
                    issues.append(error(sheet, f"{n} has a zero digit; it can't fill {len(str(n))} part boxes"))
                if form == "units_to_number":
                    total = sum(u["count"] * 10 ** PLACE_NAMES.index(u["name"]) for u in i["units"])
                    if total != n or not all(0 <= u["count"] <= 9 for u in i["units"]):
                        issues.append(error(sheet, f"{i['units']} don't make {n}"))
                if form == "name_to_number" and i["name"] != number_name(n):
                    issues.append(error(sheet, f"{i['name']!r} is not the name of {n}"))
                answers.append(expanded_answer(i))
            if len({i["n"] for i in sheet.items}) != len(sheet.items):
                issues.append(error(sheet, "a number appears twice"))
        else:
            symbols = [compare_symbol(i["left"], i["right"]) for i in sheet.items]
            if symbols.count("=") > 1 or "<" not in symbols or ">" not in symbols:
                issues.append(error(sheet, f"answers {symbols}: need both < and >, at most one ="))
            answers = symbols
        if sheet.answer_key != answers:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the items {answers}"))
        return issues

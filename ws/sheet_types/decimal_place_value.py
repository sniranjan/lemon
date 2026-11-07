"""Decimal place value (Otters math, 5.NBT.3–4): compare, round and name the value of a digit.

Every page has `compare` pairs (two decimals to thousandths and a circle for <, > or =; written
as printed, so 2.30 and 2.3 can be equal), `round` lines (round a thousandths number to the
nearest whole, tenth or hundredth) and `value` lines (what one digit of a number is worth).
Rules (merged level → section → part): `counts` (default {compare: 4, round: 3, value: 3}), `title`.
Answers: "<", ">" or "=", the rounded number with its places ("4.0"), and the digit's value ("0.08", "40").
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules
from ._exact import dec, dec_str, from_hundredths

COUNTS = {"compare": 4, "round": 3, "value": 3}
PLACES = {"whole": 0, "tenth": 1, "hundredth": 2}
MAX_TRIES = 5000


def answer(item: dict) -> str:
    if item["task"] == "compare":
        a, b = Decimal(item["a"]), Decimal(item["b"])
        return "<" if a < b else ">" if a > b else "="
    if item["task"] == "round":
        q = Decimal(1).scaleb(-PLACES[item["place"]])
        return str(dec(item["x"]).quantize(q, rounding=ROUND_HALF_UP))
    s, k = item["x"], item["digit"]
    point = s.index(".") if "." in s else len(s)
    power = point - k - 1 if k < point else point - k
    return dec_str(Decimal(int(s[k])).scaleb(power))


def _decimal(rng, lo_int: int, hi_int: int, places: int) -> str:
    return dec_str(from_hundredths(rng.randint(lo_int * 10 ** places, hi_int * 10 ** places), places))


def _compare(rng, want: str) -> dict:
    while True:
        if want == "=":   # the same number, one written with an extra zero
            a = _decimal(rng, 0, 20, rng.choice([1, 2]))
            if "." not in a:
                continue
            b = a + "0"
        else:   # fewer digits can be bigger: 0.5 vs 0.45, 3.07 vs 3.7
            whole = rng.randint(0, 20)
            a = dec_str(Decimal(whole) + from_hundredths(rng.randint(1, 999), 3))
            b = dec_str(Decimal(whole) + from_hundredths(rng.randint(1, 99), rng.choice([1, 2])))
        item = {"task": "compare", "a": a, "b": b} if rng.random() < 0.5 else {"task": "compare", "a": b, "b": a}
        if answer(item) == want and item["a"] != item["b"]:
            return item


def _round(rng, place: str) -> dict:
    while True:
        x = _decimal(rng, 0, 99, 3)
        if x.count(".") and len(x.split(".")[1]) == 3:
            item = {"task": "round", "x": x, "place": place}
            if Decimal(answer(item)) != Decimal(x):
                return item


def _value(rng) -> dict:
    while True:
        x = _decimal(rng, 1, 999, rng.choice([2, 3]))
        digits = [c for c in x if c != "."]
        if "." not in x or len(set(digits)) != len(digits):
            continue   # every digit different, so "the 8" names one place
        frac_ks = [k for k, c in enumerate(x) if k > x.index(".") and c != "0"]
        k = rng.choice(frac_ks) if rng.random() < 0.75 else rng.choice([k for k in range(x.index(".")) if x[k] != "0"])
        return {"task": "value", "x": x, "digit": k}


def item_ok(item: dict) -> str | None:
    t = item["task"]
    if t == "compare":
        for s in (item["a"], item["b"]):
            d = Decimal(s)
            if d < 0 or (d.as_tuple().exponent < -3):
                return f"{s} isn't a decimal to thousandths"
        if item["a"] == item["b"]:
            return "compares a number with itself"
    elif t == "round":
        x = dec(item["x"])
        if item["place"] not in PLACES or "." not in item["x"] or len(item["x"].split(".")[1]) != 3:
            return f"rounds {item['x']} to {item['place']}: needs a thousandths number and a place"
        if Decimal(answer(item)) == x:
            return f"{item['x']} doesn't change when rounded"
    elif t == "value":
        s, k = item["x"], item["digit"]
        dec(s)
        digits = [c for c in s if c != "."]
        if not 0 <= k < len(s) or s[k] in ".0" or len(set(digits)) != len(digits):
            return f"digit {k} of {s} isn't one clear non-zero digit"
    else:
        return f"unknown task {t!r}"
    return None


@register("decimal_place_value")
class DecimalPlaceValue(SheetType):
    template = "decimal_place_value.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        counts = r.get("counts", COUNTS)
        items: list[dict] = []
        wants = ["<", ">", "="] * counts["compare"]
        wants = wants[:counts["compare"]]
        rng.shuffle(wants)
        items += [_compare(rng, w) for w in wants]
        places = list(PLACES)
        rng.shuffle(places)
        items += [_round(rng, places[k % 3]) for k in range(counts["round"])]
        values: list[dict] = []
        while len(values) < counts["value"]:
            v = _value(rng)
            if v not in values:
                values.append(v)
        items += values
        for k, item in enumerate(items, 1):
            item["n"] = k
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[answer(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        counts = r.get("counts", COUNTS)
        issues: list[Issue] = []
        got = {t: sum(i["task"] == t for i in sheet.items) for t in COUNTS}
        if got != counts:
            issues.append(error(sheet, f"tasks {got}; this part has {counts}"))
        if [i.get("n") for i in sheet.items] != list(range(1, len(sheet.items) + 1)):
            issues.append(error(sheet, "items are not numbered 1, 2, 3… in order"))
        for i in sheet.items:
            try:
                why = item_ok(i)
            except Exception as e:   # a malformed number
                why = repr(e)
            if why:
                issues.append(error(sheet, f"item {i.get('n')}: {why}"))
        cmp = {answer(i) for i in sheet.items if i["task"] == "compare"}
        if counts["compare"] >= 3 and cmp != {"<", ">", "="}:
            issues.append(error(sheet, f"compare answers {sorted(cmp)}; a page needs <, > and ="))
        keys = [repr(sorted((k, v) for k, v in i.items() if k != "n")) for i in sheet.items]
        if len(set(keys)) != len(keys):
            issues.append(error(sheet, "an item appears twice"))
        try:
            expected = [answer(i) for i in sheet.items]
        except Exception as e:
            return issues + [error(sheet, f"can't work out the answers: {e!r}")]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the items {expected}"))
        return issues

"""MA 4A-A: large dotted numerals to trace, one number per row.

Each row shows the number once as a solid model (with that many dots under it), then
`traces` dotted copies for the child to trace with a pencil. The dotted numerals are the
Andika glyphs (our early-reader font, single-storey shapes) filled with a dot pattern, so
the pencil runs down the middle of each stroke.

Rules (merged level → section → part):
- `min`, `max`: the part's numbers. `rows` numbers per sheet (default 4); `traces` per row (default 3).
- `new` (optional): numbers that appear on every sheet of the part. When the range has no more
  numbers than rows (1–3), every number in it is on every sheet.
Rows never repeat the number of the row above, so each sheet mixes its numbers.
"""

from __future__ import annotations

import struct
from functools import cache
from pathlib import Path

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, new_numbers, page_rules

TRACE_FONT = Path(__file__).resolve().parents[2] / "assets" / "fonts" / "Andika-Regular.ttf"


@cache
def font_chars(path: Path = TRACE_FONT) -> frozenset[str]:
    """Characters with a glyph in a TrueType font (cmap format 4, the Basic Multilingual Plane)."""
    data = path.read_bytes()
    num_tables = struct.unpack(">H", data[4:6])[0]
    for i in range(num_tables):
        tag, _, offset, _ = struct.unpack(">4sIII", data[12 + 16 * i: 28 + 16 * i])
        if tag == b"cmap":
            break
    else:
        raise ValueError(f"{path.name}: no cmap table")
    n_sub = struct.unpack(">H", data[offset + 2: offset + 4])[0]
    for j in range(n_sub):
        _, _, sub = struct.unpack(">HHI", data[offset + 4 + 8 * j: offset + 12 + 8 * j])
        t = offset + sub
        if struct.unpack(">H", data[t: t + 2])[0] != 4:
            continue
        segs = struct.unpack(">H", data[t + 6: t + 8])[0] // 2
        # endCode[segs], reservedPad, startCode[segs], idDelta[segs], idRangeOffset[segs]
        starts_at = [t + 14, t + 16 + 2 * segs, t + 16 + 4 * segs, t + 16 + 6 * segs]
        ends, starts, deltas, range_offs = (struct.unpack(f">{segs}H", data[a: a + 2 * segs]) for a in starts_at)
        ro_base = starts_at[3]
        chars = set()
        for s in range(segs):
            for c in range(starts[s], min(ends[s], 0xFFFE) + 1):
                if range_offs[s] == 0:
                    gid = (c + deltas[s]) & 0xFFFF
                else:
                    at = ro_base + 2 * s + range_offs[s] + 2 * (c - starts[s])
                    gid = struct.unpack(">H", data[at: at + 2])[0]
                    gid = (gid + deltas[s]) & 0xFFFF if gid else 0
                if gid:
                    chars.add(chr(c))
        return frozenset(chars)
    raise ValueError(f"{path.name}: no format-4 cmap")


def missing_glyphs(numbers: list[int]) -> set[str]:
    return {c for n in numbers for c in str(n)} - font_chars()


def check_range(sheet: Sheet, numbers: list[int], lo: int, hi: int) -> list[Issue]:
    issues = [error(sheet, f"{n} is outside this part's range {lo}–{hi}") for n in numbers if not lo <= n <= hi]
    if missing := missing_glyphs(numbers):
        issues.append(error(sheet, f"the trace font has no glyph for {sorted(missing)}"))
    return issues


@register("number_trace")
class NumberTrace(SheetType):
    template = "number_trace.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        lo, hi, rows, traces = r["min"], r["max"], r.get("rows", 4), r.get("traces", 3)
        news = new_numbers(r)
        if hi - lo + 1 <= rows:
            news = list(range(lo, hi + 1))   # a small range (1–3): every number on every sheet
        if len(news) > rows or hi - lo < 1:
            raise ValueError(f"number_trace: {rows} rows can't hold {news} from {lo}–{hi}")
        for _ in range(1000):
            numbers = news + [ctx.rng.randint(lo, hi) for _ in range(rows - len(news))]
            ctx.rng.shuffle(numbers)
            if all(a != b for a, b in zip(numbers, numbers[1:])):
                break
        else:
            raise ValueError("number_trace: can't order the rows without repeats")
        items = [{"kind": "trace", "n": n, "traces": traces} for n in numbers]
        return SheetContent(title="Trace the numbers", parent_tip=ctx.tip(self.name), items=items)

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        numbers = [i["n"] for i in sheet.items]
        issues = check_range(sheet, numbers, r["min"], r["max"])
        if len(numbers) != r.get("rows", 4):
            issues.append(error(sheet, f"{len(numbers)} rows; the part asks for {r.get('rows', 4)}"))
        if any(i["traces"] != r.get("traces", 3) for i in sheet.items):
            issues.append(error(sheet, f"each row needs {r.get('traces', 3)} numbers to trace"))
        if any(a == b for a, b in zip(numbers, numbers[1:])):
            issues.append(error(sheet, f"two rows in a row trace the same number: {numbers}"))
        news = set(range(r["min"], r["max"] + 1)) if r["max"] - r["min"] + 1 <= len(numbers) else set(new_numbers(r))
        if missing := news - set(numbers):
            issues.append(error(sheet, f"the part's new numbers {sorted(missing)} are not on the sheet"))
        if sheet.answer_key:
            issues.append(error(sheet, "a tracing sheet has nothing to check, so no answer key"))
        return issues

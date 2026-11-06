"""MA 6A-C, 5A-A/E: numerals in boxes to read aloud, each with a picture of how many.

`rules.show` picks the picture under each numeral:
- `pictures` (default, up to 10): that many small object pictures (6A-C).
- `ten_frames` (5A-A, up to 30): full ten-frames for the tens plus one partly filled frame
  for the ones, so 23 reads as "ten, twenty, twenty-one, twenty-two, twenty-three".
- `rods` (5A-E, 51-100): one bar of ten squares per ten plus single squares, because
  eight or nine ten-frames don't fit a card.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, pick_numbers
from .count_and_say import check_counts, count_rows

CARDS = 4
SHOWS = ("pictures", "ten_frames", "rods")
FRAME_MAX = 30   # three ten-frames per card is the most that fits
ROD_MAX = 100


def tens_item(n: int, show: str) -> dict:
    tens, ones = divmod(n, 10)
    item = {"kind": "tens", "n": n, "show": show, "tens": tens, "ones": ones}
    if show == "ten_frames":
        # one entry per frame: how many of its 10 cells are filled
        item["frames"] = [10] * tens + ([ones] if ones else [])
    return item


@register("number_read")
class NumberRead(SheetType):
    template = "number_read.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        show = ctx.rules.get("show", "pictures")
        if show == "pictures":
            items = count_rows(ctx, CARDS)
        elif show in SHOWS:
            items = [tens_item(n, show) for n in pick_numbers(ctx.rng, ctx.rules, CARDS)]
        else:
            raise ValueError(f"number_read: unknown show {show!r} (use one of {', '.join(SHOWS)})")
        return SheetContent(title="Read the numbers", parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["n"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = check_counts(sheet)
        for i in sheet.items:
            if i["kind"] != "tens":
                continue
            n = i["n"]
            if i["tens"] * 10 + i["ones"] != n or not 0 <= i["ones"] <= 9:
                issues.append(error(sheet, f"{i['tens']} tens and {i['ones']} ones don't make {n}"))
            if i["show"] == "ten_frames":
                f = i["frames"]
                if sum(f) != n or any(not 1 <= c <= 10 for c in f) or any(c != 10 for c in f[:-1]):
                    issues.append(error(sheet, f"ten-frames {f} don't show {n}"))
                if n > FRAME_MAX:
                    issues.append(error(sheet, f"{n} needs more than {FRAME_MAX // 10} ten-frames"))
            elif n > ROD_MAX:
                issues.append(error(sheet, f"{n} needs more than {ROD_MAX // 10} rods"))
        return issues

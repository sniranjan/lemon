"""ZI-A: one or two big outline shapes to color inside. No text for the child."""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ..shapes import SHAPES
from ._common import error


@register("colouring")
class Colouring(SheetType):
    template = "colouring.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        names = ctx.rng.sample(sorted(SHAPES), ctx.rules["shapes_per_sheet"])
        return SheetContent(
            title="Color it in",
            parent_tip=ctx.tip(self.name),
            items=[{"kind": "shape", "shape": n, "path": SHAPES[n], "size": ctx.rules["shape_size"]} for n in names],
        )

    def verify(self, sheet: Sheet) -> list[Issue]:
        unknown = [i["shape"] for i in sheet.items if i["shape"] not in SHAPES]
        return [error(sheet, f"unknown shapes {unknown}")] if unknown else []

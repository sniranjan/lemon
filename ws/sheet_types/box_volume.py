"""Volume of boxes (rectangular prisms) with a simple drawn box (Otters math, 5.MD.3–5).

Each page has one of each task (shuffled):
- `cubes`: a small box built from unit cubes (edges 2–4), drawn with the cube lines; count them.
- `box`: a box with its length, width and height labeled; V = l × w × h.
- `base`: the base area and the height are given; V = B × h (the base is shaded).
- `two_boxes`: two boxes side by side with the same width; add their volumes (5.MD.5c). Edges are
  labeled with bare numbers and one "Edges in inches" line, so the labels stay apart.
Items store whole-number edges only (`dims`: one [l, w, h] per box) and a `unit` (cm, in, ft, m);
the template draws the boxes from them, so verify can check every number. Rules: `tasks`
(default the four above), `max_volume` (default 1000), `title` (default "Volume").
Answers are the volumes as whole numbers.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules

TASKS = ["cubes", "box", "base", "two_boxes"]
UNITS = ["cm", "in", "ft", "m"]
MAX_TRIES = 5000


def volume(item: dict) -> int:
    return sum(l * w * h for l, w, h in item["dims"])


def two_box_scale(dims: list[list[int]]) -> float:
    """Pixels per unit the template uses for two boxes (keep in step with box_volume.html.j2)."""
    (l1, w, h1), (l2, _, h2) = dims
    return min(170 / (l1 + l2 + 0.55 * w), 150 / (max(h1, h2) + 0.45 * w), 26)


LABEL_GAP = 46   # px between the two length labels' centers (bare numbers; the unit is on its own line)


def item_ok(item: dict, max_volume: int) -> str | None:
    t, dims = item["task"], item["dims"]
    if t not in TASKS:
        return f"unknown task {t!r}"
    if len(dims) != (2 if t == "two_boxes" else 1):
        return f"{t} needs {2 if t == 'two_boxes' else 1} boxes"
    for d in dims:
        if len(d) != 3 or not all(isinstance(x, int) for x in d):
            return f"edges {d} aren't three whole numbers"
        lo, hi = (2, 4) if t == "cubes" else (2, 12)
        if not all(lo <= x <= hi for x in d):
            return f"edges {d} are outside {lo}–{hi}"
    if t == "two_boxes":
        (l1, w1, h1), (l2, w2, h2) = dims
        if w1 != w2 or h1 == h2 or max(l1, l2) > 8:
            return "two boxes share a width, have different heights and are at most 8 long"
        if (l1 + l2) / 2 * two_box_scale(dims) < LABEL_GAP:
            return "the two length labels would touch"
    if t != "cubes" and item.get("unit") not in UNITS:
        return f"unit {item.get('unit')!r} isn't one of {UNITS}"
    if t == "cubes" and item.get("unit") is not None:
        return "a cube count has no unit"
    if t == "base" and item.get("base") != dims[0][0] * dims[0][1]:
        return f"base area {item.get('base')} isn't length × width"
    if volume(item) > max_volume:
        return f"volume {volume(item)} is over {max_volume}"
    return None


@register("box_volume")
class BoxVolume(SheetType):
    template = "box_volume.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        tasks = list(r.get("tasks", TASKS))
        rng.shuffle(tasks)
        max_v = r.get("max_volume", 1000)
        items = []
        for t in tasks:
            for _ in range(MAX_TRIES):
                if t == "cubes":
                    item = {"task": t, "dims": [[rng.randint(2, 4) for _ in range(3)]], "unit": None}
                elif t == "two_boxes":
                    w = rng.randint(2, 6)
                    item = {"task": t, "dims": [[rng.randint(2, 8), w, rng.randint(2, 10)],
                                                [rng.randint(2, 8), w, rng.randint(2, 10)]],
                            "unit": rng.choice(UNITS)}
                else:
                    item = {"task": t, "dims": [[rng.randint(2, 12) for _ in range(3)]], "unit": rng.choice(UNITS)}
                    if t == "base":
                        item["base"] = item["dims"][0][0] * item["dims"][0][1]
                if item_ok(item, max_v) is None:
                    break
            else:
                raise ValueError(f"box_volume: can't make a {t} problem")
            items.append(item)
        for k, item in enumerate(items, 1):
            item["n"] = k
        return SheetContent(title=r.get("title", "Volume"), parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[volume(i) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        issues: list[Issue] = []
        tasks = r.get("tasks", TASKS)
        if sorted(i["task"] for i in sheet.items) != sorted(tasks):
            issues.append(error(sheet, f"tasks {[i['task'] for i in sheet.items]}; a page has one each of {tasks}"))
        if [i.get("n") for i in sheet.items] != list(range(1, len(sheet.items) + 1)):
            issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
        for i in sheet.items:
            why = item_ok(i, r.get("max_volume", 1000))
            if why:
                issues.append(error(sheet, f"problem {i.get('n')}: {why}"))
        expected = [volume(i) for i in sheet.items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the boxes {expected}"))
        return issues

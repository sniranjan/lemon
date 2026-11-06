"""Cubs math (M2-H): tiny story problems within 100 (2.OA.1), read aloud by a grown-up.

Each card: a picture of the things in the story, the story (from content/math/stories.yaml),
and a number sentence to fill in, "☐ ◯ ☐ = ☐". The answer key gives the whole sentence.

Rules (shared with column_arithmetic): `op` (add | sub | mixed), `a` and `b` ranges,
`max_answer`, `min_answer` (default 1). `stories`: problems per page (default 3); a mixed page
has both adding and taking-away stories.
"""

from __future__ import annotations

from ..content import math_objects, math_stories
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error
from .column_arithmetic import SIGN, answer, problem_ok

STORIES = 3


def sentence(op: str, a: int, b: int) -> str:
    return f"{a} {'+' if op == 'add' else '-'} {b} = {answer(op, [a, b])}"


def fill(frame: dict, thing: str, a: int, b: int) -> str:
    return frame["text"].format(a=a, b=b, things=math_stories()["plurals"][thing])


@register("math_story")
class MathStory(SheetType):
    template = "math_story.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        n = r.get("stories", STORIES)
        if r["op"] == "mixed":
            ops = ["add", "sub"] + [rng.choice(["add", "sub"]) for _ in range(n - 2)]
            rng.shuffle(ops)
        else:
            ops = [r["op"]] * n
        pictures = {o["name"]: o["picture"] for o in math_objects()}
        frames = math_stories()["frames"]
        items, used_frames, used_things = [], set(), set()
        for op in ops:
            choices = [(k, t) for k, f in enumerate(frames) if f["op"] == op and k not in used_frames
                       for t in f["things"] if t not in used_things and t in pictures]
            k, thing = rng.choice(choices)
            for _ in range(10000):
                a, b = rng.randint(*r["a"]), rng.randint(*r["b"])
                if problem_ok({**r, "addends": 2}, op, [a, b], None) is None:
                    break
            else:
                raise ValueError(f"math_story: no {op} numbers fit these rules: {r}")
            used_frames.add(k)
            used_things.add(thing)
            items.append({"kind": "story", "op": op, "sign": SIGN[op], "a": a, "b": b, "frame": k,
                          "thing": thing, "picture": pictures[thing], "text": fill(frames[k], thing, a, b)})
        return SheetContent(title="Story problems", parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[sentence(i["op"], i["a"], i["b"]) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        frames = math_stories()["frames"]
        issues, answers = [], []
        if len(sheet.items) != r.get("stories", STORIES):
            issues.append(error(sheet, f"{len(sheet.items)} stories; expected {r.get('stories', STORIES)}"))
        for i in sheet.items:
            op, a, b = i["op"], i["a"], i["b"]
            frame = frames[i["frame"]] if 0 <= i["frame"] < len(frames) else None
            if frame is None or frame["op"] != op or i["thing"] not in frame["things"]:
                issues.append(error(sheet, f"story frame {i['frame']} doesn't fit a {op} story about {i['thing']}"))
            elif i["text"] != fill(frame, i["thing"], a, b):
                issues.append(error(sheet, f"story text doesn't match its numbers: {i['text']!r}"))
            if r["op"] != "mixed" and op != r["op"]:
                issues.append(error(sheet, f"{op} story on a {r['op']} page"))
            why = problem_ok({**r, "addends": 2}, op, [a, b], None)
            if why:
                issues.append(error(sheet, f"story {a} {i['sign']} {b}: {why}"))
            answers.append(sentence(op, a, b))
        if r["op"] == "mixed" and len({i["op"] for i in sheet.items}) < 2:
            issues.append(error(sheet, "a mixed page needs adding and taking-away stories"))
        if len({i["frame"] for i in sheet.items}) != len(sheet.items):
            issues.append(error(sheet, "the same story appears twice"))
        if sheet.answer_key != answers:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the stories {answers}"))
        return issues

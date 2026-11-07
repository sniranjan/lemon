"""Story problems: short word problems with times and sharing (Foxes math, 3.OA.3, 3.OA.8).

Frames live in content/math/story_problems.yaml (see its header): a sentence with number slots,
ranges for the numbers, and the answer as a small expression. The generator fills the numbers in;
verify fills the frame in again from the stored numbers, recomputes every answer and checks that
the story stays true to life (whole answers of 2 or more, so units stay plural, nothing used up that isn't there, all
numbers within `max_value`). Rules (merged level → section → part):
- `problems`: problems per page (default 3).
- `ops`: one-step signs every page shows ("*" and "/": a times story and a sharing story).
- `two_step_min`: at least this many two-step problems (two signs in the answer) on each page.
- `max_value`: no number in a story or answer above it (default 100). `title`: the sheet title.
"""

from __future__ import annotations

import ast
import operator

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules

PROBLEMS = 3
MAX_TRIES = 500
_OPS = {ast.Add: ("+", operator.add), ast.Sub: ("-", operator.sub),
        ast.Mult: ("*", operator.mul), ast.Div: ("/", None)}
_CMP = {ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge}


def evaluate(expr: str, values: dict[str, int]) -> int | bool:
    """Whole-number arithmetic on names and numbers; a division that doesn't come out even fails."""

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            x, y = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Div):
                if y == 0 or x % y:
                    raise ValueError(f"{x} / {y} doesn't come out even")
                return x // y
            return _OPS[type(node.op)][1](x, y)
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _CMP:
            return _CMP[type(node.ops[0])](ev(node.left), ev(node.comparators[0]))
        raise ValueError(f"not allowed in a story expression: {ast.dump(node)}")

    return ev(ast.parse(expr, mode="eval"))


def signs(expr: str) -> list[str]:
    return [_OPS[type(n.op)][0] for n in ast.walk(ast.parse(expr, mode="eval")) if isinstance(n, ast.BinOp)]


def frames_by_id() -> dict[str, dict]:
    from ..content import story_problems

    return {f["id"]: f for f in story_problems()}


def fill(frame: dict, picks: dict[str, int], max_value: int) -> tuple[dict[str, int], int] | None:
    """All numbers of the story (vars + lets) and its answer, or None if the story doesn't work."""
    values = dict(picks)
    try:
        for name, expr in frame.get("let", {}).items():
            values[name] = evaluate(expr, values)
        answer = evaluate(frame["answer"], values)
        if not all(evaluate(c, values) for c in frame.get("checks", [])):
            return None
    except ValueError:
        return None
    if answer < 2 or any(v > max_value or v < 1 for v in [*values.values(), answer]):
        return None
    return values, answer


def story_ok(item: dict, r: dict) -> str | None:
    frame = frames_by_id().get(item.get("frame"))
    if frame is None:
        return f"story frame {item.get('frame')!r} doesn't exist"
    picks = {k: item["values"].get(k) for k in frame["vars"]}
    for k, (lo, hi) in frame["vars"].items():
        if not isinstance(picks[k], int) or not lo <= picks[k] <= hi:
            return f"{frame['id']}: {k} = {picks[k]} is outside {lo}–{hi}"
    got = fill(frame, picks, r.get("max_value", 100))
    if got is None:
        return f"{frame['id']}: the numbers {picks} don't make a true story"
    values, answer = got
    if values != item["values"]:
        return f"{frame['id']}: stored numbers {item['values']} should be {values}"
    if item["answer"] != answer:
        return f"{frame['id']}: answer {item['answer']} is wrong, it's {answer}"
    if item["text"] != frame["text"].format(**values):
        return f"{frame['id']}: text doesn't match the frame filled with {values}"
    if item.get("unit") != frame["unit"] or item.get("steps") != len(signs(frame["answer"])):
        return f"{frame['id']}: unit or step count doesn't match the frame"
    return None


@register("story_problem")
class StoryProblem(SheetType):
    template = "story_problem.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        from ..content import story_problems

        r = ctx.rules
        count = r.get("problems", PROBLEMS)
        frames = list(story_problems())
        two = [f for f in frames if len(signs(f["answer"])) == 2]
        one = {op: [f for f in frames if signs(f["answer"]) == [op]] for op in r["ops"]}
        chosen = ctx.rng.sample(two, r.get("two_step_min", 0))
        for op in r["ops"]:
            chosen.append(ctx.rng.choice(one[op]))
        rest = [f for f in frames if f not in chosen and len(signs(f["answer"])) == 1]
        chosen += ctx.rng.sample(rest, count - len(chosen))
        ctx.rng.shuffle(chosen)
        items = []
        for n, frame in enumerate(chosen, 1):
            for _ in range(MAX_TRIES):
                picks = {k: ctx.rng.randint(lo, hi) for k, (lo, hi) in frame["vars"].items()}
                got = fill(frame, picks, r.get("max_value", 100))
                if got:
                    break
            else:
                raise ValueError(f"story_problem: frame {frame['id']} never makes a true story")
            values, answer = got
            items.append({"kind": "story", "n": n, "frame": frame["id"], "values": values,
                          "text": frame["text"].format(**values), "answer": answer, "unit": frame["unit"],
                          "steps": len(signs(frame["answer"]))})
        return SheetContent(title=r["title"], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[i["answer"] for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        items = sheet.items
        issues: list[Issue] = []
        count = r.get("problems", PROBLEMS)
        if len(items) != count:
            issues.append(error(sheet, f"{len(items)} story problems; this part has {count} a page"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
        for i in items:
            why = story_ok(i, r)
            if why:
                issues.append(error(sheet, why))
        frames = [i.get("frame") for i in items]
        if len(set(frames)) != len(frames):
            issues.append(error(sheet, "the same story frame is on the page twice"))
        if sheet.answer_key != [i.get("answer") for i in items]:
            issues.append(error(sheet, "answer key doesn't match the problems"))
        known = frames_by_id()
        kinds = [signs(known[f]["answer"]) for f in frames if f in known]
        for op in r["ops"]:
            if [op] not in kinds:
                issues.append(error(sheet, f"no one-step {op!r} story on the page"))
        twos = sum(len(k) == 2 for k in kinds)
        if twos < r.get("two_step_min", 0):
            issues.append(error(sheet, f"{twos} two-step stories; this part needs {r['two_step_min']}"))
        return issues

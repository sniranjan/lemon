"""Word problems with exact fraction, decimal and money answers (Pandas math: dividing fractions,
unit rates and speed, unit prices, converting units, percents, one-step equations).

Frames live in content/math/rational_stories.yaml (see its header). The generator picks numbers
for a frame and works the story out with Fraction arithmetic; verify fills the frame in again
from the stored picks and recomputes everything exactly. Rules (merged level → section → part):
- `tags`: the kinds of problem on a page, one frame of each (in a shuffled order), e.g.
  [unit_rate, speed, unit_price, convert].
- `max_value`: no number in the story or the answer above it (default 2000).
- `max_den`: fraction answers and fractions in the text keep denominators at or below it (default 12).
- `title`: the sheet title; `story_title` overrides it when a part mixes stories with other pages.
Penguins math frames (grade 7) add: `signed: true` frames (numbers and answers may be below zero,
printed with a true minus sign), `show: percent` and `style: percent`, vars `{range: [lo, hi],
step: s}`, negative [lo, hi] ranges, and floor() / ceil() / abs() in answers (see the yaml header).
Stored items: the frame id, the picked numbers (`picks`, as text), every number of the story
(`values`, as text), the printed text, and the answer (as text, written in the frame's style).
"""

from __future__ import annotations

import re
from fractions import Fraction

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules
from ._rational import MINUS, evaluate, fmt, parse

MAX_TRIES = 2000
STYLES = ("whole", "fraction", "decimal", "money", "percent")


def frames_by_id() -> dict[str, dict]:
    from ..content import math_frames

    return {f["id"]: f for f in math_frames("rational_stories")}


def _show(x: Fraction, how: str | None) -> str:
    if how == "money":
        return fmt(x, "money").replace("-", MINUS)
    if how == "decimal":
        return fmt(x, "decimal").replace("-", MINUS)
    if how == "percent":
        return _percent(x)
    return fmt(x).replace("-", MINUS)


def _percent(x: Fraction) -> str:
    if (x * 10).denominator != 1:
        raise ValueError(f"{x}% needs more than one decimal place")
    return fmt(x, "decimal").replace("-", MINUS) + "%"


def answer_text(frame: dict, x: Fraction) -> str:
    style = frame["style"]
    if style == "money":
        return (MINUS if x < 0 else "") + "$" + fmt(abs(x), "money")
    if style == "percent":
        return _percent(x)
    return fmt(x, "decimal" if style == "decimal" else "fraction").replace("-", MINUS)


def work_out(frame: dict, picks: dict[str, str], r: dict) -> tuple[dict[str, Fraction], Fraction] | None:
    """Every number of the story and its answer, or None if the numbers don't make a true story."""
    values = {k: parse(v) for k, v in picks.items()}
    try:
        for name, expr in frame.get("let", {}).items():
            values[name] = evaluate(expr, values)
        answer = evaluate(frame["answer"], values)
        if not all(evaluate(c, values) for c in frame.get("checks", [])):
            return None
    except (ValueError, ZeroDivisionError):
        return None
    max_value, max_den = r.get("max_value", 2000), r.get("max_den", 12)
    if frame.get("signed"):
        if any(v == 0 or abs(v) > max_value for v in [*values.values(), answer]):
            return None
    elif any(v <= 0 or v > max_value for v in [*values.values(), answer]):
        return None
    if any(values[k].denominator != 1 for k in frame.get("whole", [])):
        return None
    show = frame.get("show", {})
    for k, v in values.items():
        how = show.get(k)
        if how in ("money", "decimal", "percent"):
            try:
                _show(v, how)
            except ValueError:
                return None
        elif v.denominator > max_den:
            return None
    style = frame["style"]
    if style == "whole" and answer.denominator != 1:
        return None
    if style == "fraction" and answer.denominator > max_den:
        return None
    try:
        answer_text(frame, answer)
    except ValueError:
        return None
    return values, answer


def fill_text(frame: dict, values: dict[str, Fraction]) -> str:
    show = frame.get("show", {})
    return frame["text"].format(**{k: _show(v, show.get(k)) for k, v in values.items()})


def _steps(spec: dict) -> list[str]:
    """{range: [lo, hi], step: s} -> every number lo, lo + s, … hi, as text."""
    lo, hi = (parse(str(x)) for x in spec["range"])
    step = parse(str(spec["step"]))
    return [fmt(lo + k * step, "decimal") for k in range(int((hi - lo) / step) + 1)]


def _pick(rng, spec) -> str:
    if isinstance(spec, dict):
        return rng.choice(spec["choices"] if "choices" in spec else _steps(spec))
    lo, hi = spec
    return str(rng.randint(lo, hi))


def _in_spec(value: str, spec) -> bool:
    if isinstance(spec, dict):
        return value in (spec["choices"] if "choices" in spec else _steps(spec))
    lo, hi = spec
    return value.lstrip("-").isdigit() and lo <= int(value) <= hi


def story_ok(item: dict, r: dict) -> str | None:
    frame = frames_by_id().get(item.get("frame"))
    if frame is None:
        return f"story frame {item.get('frame')!r} doesn't exist"
    picks = item.get("picks", {})
    if set(picks) != set(frame["vars"]):
        return f"{frame['id']}: picks {sorted(picks)} should be {sorted(frame['vars'])}"
    for k, spec in frame["vars"].items():
        if not _in_spec(picks[k], spec):
            return f"{frame['id']}: {k} = {picks[k]} isn't one of the frame's numbers"
    got = work_out(frame, picks, r)
    if got is None:
        return f"{frame['id']}: the numbers {picks} don't make a true story"
    values, answer = got
    if item.get("values") != {k: fmt(v) for k, v in values.items()}:
        return f"{frame['id']}: stored numbers {item.get('values')} don't match the story"
    if item.get("answer") != answer_text(frame, answer):
        return f"{frame['id']}: answer {item.get('answer')} is wrong, it's {answer_text(frame, answer)}"
    if item.get("text") != fill_text(frame, values):
        return f"{frame['id']}: text doesn't match the frame filled with {picks}"
    if item.get("unit") != frame["unit"] or item.get("equation", False) != frame.get("equation", False):
        return f"{frame['id']}: unit or equation line doesn't match the frame"
    if re.search(r"(^|[\s($])-\d", item.get("text", "") + " " + item.get("answer", "")):
        return f"{frame['id']}: a hyphen is printed where the minus sign {MINUS} belongs"
    return None


@register("rational_story")
class RationalStory(SheetType):
    template = "rational_story.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r = ctx.rules
        frames = list(frames_by_id().values())
        chosen = []
        for tag in r["tags"]:
            pool = [f for f in frames if f["tag"] == tag and f not in chosen]
            chosen.append(ctx.rng.choice(pool))
        ctx.rng.shuffle(chosen)
        items = []
        for n, frame in enumerate(chosen, 1):
            for _ in range(MAX_TRIES):
                picks = {k: _pick(ctx.rng, spec) for k, spec in frame["vars"].items()}
                got = work_out(frame, picks, r)
                if got:
                    break
            else:
                raise ValueError(f"rational_story: frame {frame['id']} never makes a true story")
            values, answer = got
            items.append({"kind": "story", "n": n, "frame": frame["id"], "picks": picks,
                          "values": {k: fmt(v) for k, v in values.items()},
                          "text": fill_text(frame, values), "answer": answer_text(frame, answer),
                          "unit": frame["unit"], "equation": frame.get("equation", False)})
        return SheetContent(title=r.get("story_title", r["title"]), parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[f"{i['answer']}" if i["unit"] == "$" else f"{i['answer']} {i['unit']}".rstrip()
                                        for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        r = page_rules(sheet)
        items = sheet.items
        issues: list[Issue] = []
        if len(items) != len(r["tags"]):
            issues.append(error(sheet, f"{len(items)} problems; this part has {len(r['tags'])} a page"))
        if [i.get("n") for i in items] != list(range(1, len(items) + 1)):
            issues.append(error(sheet, "problems are not numbered 1, 2, 3… in order"))
        for i in items:
            why = story_ok(i, r)
            if why:
                issues.append(error(sheet, why))
        frames = [i.get("frame") for i in items]
        if len(set(frames)) != len(frames):
            issues.append(error(sheet, "the same story frame is on the page twice"))
        known = frames_by_id()
        tags = sorted(known[f]["tag"] for f in frames if f in known)
        if tags != sorted(r["tags"]):
            issues.append(error(sheet, f"problem kinds {tags} should be {sorted(r['tags'])}"))
        expected = [i.get("answer") if i.get("unit") == "$" else f"{i.get('answer')} {i.get('unit')}".rstrip()
                    for i in items]
        if sheet.answer_key != expected:
            issues.append(error(sheet, "answer key doesn't match the problems"))
        return issues

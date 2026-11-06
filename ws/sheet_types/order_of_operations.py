"""Order of operations with parentheses and brackets (Otters math, 5.OA.1): one expression a line.

Expressions come from fixed shapes (SHAPES) filled with whole numbers 1–12. Every step stays a
whole number above 0 (no negatives, every sharing comes out even), the answer is at most
`max_value`, and the grouping always matters: dropping the parentheses and brackets (or, on a
`plain` line with none, working left to right) gives a different answer.
Rules: `problems` (default 10), `plain` (lines with no parentheses, testing times-before-plus;
default 2), `max_value` (default 100), `title` (default "Parentheses first").
Items store the expression as printed ("[(3 + 5) × 2] − 4"); verify parses it again.
"""

from __future__ import annotations

import ast
import re

from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

PROBLEMS = 10
PLAIN = 2
MAX_TRIES = 5000
SHAPES = [
    "(a + b) * c", "a * (b + c)", "(a - b) * c", "a * (b - c)", "(a + b) / c", "a - (b + c)",
    "a - (b - c)", "(a + b) * (c - d)", "[(a + b) * c] - d", "a + [b * (c - d)]", "[a * (b + c)] / d",
    "(a * b) - (c + d)",
]
PLAIN_SHAPES = ["a + b * c", "a - b * c", "a * b + c * d", "a + b / c", "a * b - c / d"]
PRETTY = {"*": "×", "/": "÷", "-": "−"}


def to_python(expr: str) -> str:
    out = expr.replace("[", "(").replace("]", ")")
    for k, v in PRETTY.items():
        out = out.replace(v, k)
    return out


def pretty(calc: str) -> str:
    return "".join(PRETTY.get(c, c) for c in calc)


def evaluate(expr: str) -> int:
    """Whole numbers only: a take-away step of 0 or less or an uneven sharing raises ValueError."""

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.BinOp):
            x, y = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return x + y
            if isinstance(node.op, ast.Sub):
                if x <= y:   # a step of 0 makes a line trivial (11 × (5 − 5))
                    raise ValueError(f"{x} − {y} isn't more than 0")
                return x - y
            if isinstance(node.op, ast.Mult):
                return x * y
            if isinstance(node.op, ast.Div):
                if y == 0 or x % y:
                    raise ValueError(f"{x} ÷ {y} doesn't come out even")
                return x // y
        raise ValueError(f"not allowed: {ast.dump(node)}")

    return ev(ast.parse(to_python(expr), mode="eval"))


def left_to_right(expr: str) -> int | None:
    """The answer if you just went left to right (the mistake a plain line tests)."""
    tokens = re.findall(r"\d+|[-+*/]", to_python(expr))
    try:
        val = int(tokens[0])
        for op, n in zip(tokens[1::2], tokens[2::2]):
            val = evaluate(f"{val} {op} {n}")
        return val
    except ValueError:
        return None


def without_grouping(expr: str) -> int | None:
    try:
        return evaluate(re.sub(r"[()\[\]]", "", expr))
    except ValueError:
        return None


def line_ok(expr: str, max_value: int) -> str | None:
    if not re.fullmatch(r"[\d +−×÷()\[\]]+", expr):
        return "has characters that aren't numbers, signs or parentheses"
    try:
        val = evaluate(expr)
    except (ValueError, SyntaxError) as e:
        return str(e)
    if val > max_value:
        return f"answer {val} is over {max_value}"
    if any(int(n) > 12 or int(n) < 1 for n in re.findall(r"\d+", expr)):
        return "numbers are 1–12"
    if re.search(r"[()\[\]]", expr):
        if without_grouping(expr) == val:
            return "the parentheses don't change the answer"
    elif left_to_right(expr) == val:
        return "working left to right gives the same answer"
    return None


@register("order_of_operations")
class OrderOfOperations(SheetType):
    template = "order_of_operations.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        r, rng = ctx.rules, ctx.rng
        n, plain = r.get("problems", PROBLEMS), r.get("plain", PLAIN)
        shapes = list(SHAPES)
        rng.shuffle(shapes)
        first = next(s for s in shapes if "[" in s)   # every page has a line with brackets
        shapes = [first] + [s for s in shapes if s != first]
        plains = list(PLAIN_SHAPES)
        rng.shuffle(plains)
        picks = [plains[k % len(plains)] for k in range(plain)] + [shapes[k % len(shapes)] for k in range(n - plain)]
        rng.shuffle(picks)
        items, seen = [], set()
        for shape in picks:
            for _ in range(MAX_TRIES):
                calc = re.sub(r"[abcd]", lambda m: str(rng.randint(1, 12)), shape)
                expr = pretty(calc)
                if expr not in seen and line_ok(expr, r.get("max_value", 100)) is None:
                    break
            else:
                raise ValueError(f"order_of_operations: can't fill {shape!r}")
            seen.add(expr)
            items.append({"kind": "expression", "expr": expr})
        for k, item in enumerate(items, 1):
            item["n"] = k
        return SheetContent(title=r.get("title", "Parentheses first"), parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[evaluate(i["expr"]) for i in items])

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        r = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        issues: list[Issue] = []
        n, plain = r.get("problems", PROBLEMS), r.get("plain", PLAIN)
        if len(sheet.items) != n:
            issues.append(error(sheet, f"{len(sheet.items)} lines; the part asks for {n}"))
        if [i.get("n") for i in sheet.items] != list(range(1, len(sheet.items) + 1)):
            issues.append(error(sheet, "lines are not numbered 1, 2, 3… in order"))
        exprs = [i["expr"] for i in sheet.items]
        if len(set(exprs)) != len(exprs):
            issues.append(error(sheet, "a line appears twice"))
        for e in exprs:
            why = line_ok(e, r.get("max_value", 100))
            if why:
                issues.append(error(sheet, f"{e}: {why}"))
        got_plain = sum(not re.search(r"[()\[\]]", e) for e in exprs)
        if got_plain != plain:
            issues.append(error(sheet, f"{got_plain} lines without parentheses; this part has {plain}"))
        if not any("[" in e for e in exprs):
            issues.append(error(sheet, "no line uses brackets"))
        try:
            expected = [evaluate(e) for e in exprs]
        except (ValueError, SyntaxError) as e:
            return issues + [error(sheet, f"can't work out the answers: {e}")]
        if sheet.answer_key != expected:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the lines {expected}"))
        return issues

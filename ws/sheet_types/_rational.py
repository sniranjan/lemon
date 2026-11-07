"""Exact numbers for upper math levels (Pandas math): parse, format and evaluate with Fraction.

Sheets store numbers as plain strings so they stay JSON ("3/4", "2 1/2", "1.25", "-3", "12"),
never Fraction or Decimal objects. Generators and verify both turn them back into Fractions here,
so every answer is recomputed exactly.

Display strings use the real minus sign (U+2212), × and ÷, so printed pages read like a math book;
`parse` accepts both minus signs.
"""

from __future__ import annotations

import ast
import operator
from fractions import Fraction

from . import _numbers
from ._numbers import MINUS, is_terminating, parse  # noqa: F401 (re-exported)

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow}
_CMP = {ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
        ast.Eq: operator.eq, ast.NotEq: operator.ne}


def fmt(x: Fraction, style: str = "fraction") -> str:
    """Answer-key text. style 'fraction': 5, 3/4, 2 1/3 (simplest form, mixed if above 1);
    'improper': 7/3; 'decimal': 1.25 (must terminate); 'money': 2.50."""
    if style not in ("decimal", "money"):
        style = "fraction" if style == "improper" else "mixed"
    return _numbers.fmt(Fraction(x), style)


show = _numbers.minus   # a stored number as printed: '-3' -> '−3' (the true minus sign)


def parts(s: str | Fraction) -> dict:
    """A number for a stacked-fraction template: {'sign', 'whole', 'num', 'den'} (num/den None if whole)."""
    x = parse(s) if not isinstance(s, Fraction) else s
    sign = MINUS if x < 0 else ""
    x = abs(x)
    if x.denominator == 1:
        return {"sign": sign, "whole": x.numerator, "num": None, "den": None}
    w = x.numerator // x.denominator
    r = x - w
    return {"sign": sign, "whole": w or None, "num": r.numerator, "den": r.denominator}


# --- expressions ---------------------------------------------------------------------------

_CALLS = {"floor": lambda x: Fraction(x.numerator // x.denominator),
          "ceil": lambda x: Fraction(-((-x.numerator) // x.denominator)),
          "abs": abs}


def evaluate(expr: str, values: dict[str, Fraction | int | str] | None = None) -> Fraction | bool:
    """Exact arithmetic on names and numbers: + − × ÷ and whole-number powers, comparisons.

    Numbers in the text may be ints or decimals (1.25 is read exactly as 5/4). Division by zero
    and non-whole exponents raise ValueError. Nothing else is allowed (no calls, no attributes).
    """
    vals = {k: (v if isinstance(v, Fraction) else parse(v)) for k, v in (values or {}).items()}

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Fraction(repr(node.value)) if isinstance(node.value, float) else Fraction(node.value)
        if isinstance(node, ast.Name):
            if node.id not in vals:
                raise ValueError(f"unknown name {node.id!r}")
            return vals[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            x, y = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Div) and y == 0:
                raise ValueError("division by zero")
            if isinstance(node.op, ast.Pow):
                if y.denominator != 1 or y < 0 or y > 6:
                    raise ValueError(f"exponent {y} isn't a small whole number")
                return x ** int(y)
            return _BIN[type(node.op)](x, y)
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _CMP:
            return _CMP[type(node.ops[0])](ev(node.left), ev(node.comparators[0]))
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            return all(ev(v) for v in node.values)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _CALLS
                and len(node.args) == 1 and not node.keywords):
            return _CALLS[node.func.id](ev(node.args[0]))   # Penguins: at most / at least how many
        raise ValueError(f"not allowed in an expression: {ast.dump(node)}")

    return ev(ast.parse(expr, mode="eval"))


_PREC = {ast.Add: 1, ast.Sub: 1, ast.Mult: 2, ast.Div: 2, ast.Pow: 3}
_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def pretty(expr: str) -> str:
    """'3*n+4' -> '3n + 4'; '2*(l+w)' -> '2(l + w)'; 'n**2' -> 'n²'; 'x/4' -> 'x ÷ 4'.

    A number times a letter (or a bracket) is written next to it, as in a math book; anything
    else times anything uses ×. Brackets appear only where the order of operations needs them.
    """

    def num(node) -> bool:
        return isinstance(node, ast.Constant)

    def term(node) -> bool:
        """A letter, or letters and one leading number written side by side (n, 3n, lw, 2lw)."""
        if isinstance(node, ast.Name):
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult) and isinstance(node.right, ast.Name):
            return num(node.left) or term(node.left)
        return False

    def wrap(node, parent_prec: int, right: bool = False) -> str:
        s = go(node)
        if isinstance(node, ast.BinOp):
            p = _PREC[type(node.op)]
            if p < parent_prec or (right and p == parent_prec and p < 3):
                return f"({s})"
        return s

    def go(node) -> str:
        if isinstance(node, ast.Expression):
            return go(node.body)
        if isinstance(node, ast.Constant):
            return repr(node.value) if isinstance(node.value, float) else str(node.value)
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return MINUS + wrap(node.operand, 3)
        if isinstance(node, ast.BinOp):
            op = type(node.op)
            p = _PREC[op]
            if op is ast.Pow:
                if not isinstance(node.right, ast.Constant):
                    raise ValueError("exponents must be numbers")
                base = go(node.left)
                if isinstance(node.left, ast.BinOp):
                    base = f"({base})"
                return base + str(node.right.value).translate(_SUP)
            left = wrap(node.left, p)
            right = wrap(node.right, p, right=True)
            if op is ast.Mult:
                r = node.right
                letter_like = isinstance(r, ast.Name) or (isinstance(r, ast.BinOp) and isinstance(r.op, ast.Pow)
                                                          and isinstance(r.left, ast.Name)) or right.startswith("(")
                if letter_like and (num(node.left) or term(node.left)):
                    return f"{left}{right}"
                return f"{left} × {right}"
            sym = {ast.Add: "+", ast.Sub: MINUS, ast.Div: "÷"}[op]
            return f"{left} {sym} {right}"
        raise ValueError(f"can't print {ast.dump(node)}")

    return go(ast.parse(expr, mode="eval"))

"""Exact numbers and linear expressions for Penguins math (grade 7): signed numbers, fractions,
decimals, expressions like 3x − 4 and equations like 2x + 5 = −7.

Conventions (shared with the other upper math levels): sheets store numbers as plain strings so
they stay JSON ("3/4", "-2 1/2", "1.25", "-3"), never Fraction objects; generators and verify both
turn them back into Fractions here, so every answer is recomputed exactly. Printed text uses the
real minus sign (U+2212, `MINUS`); `parse` accepts both minus signs.

A linear expression is `Lin`: a dict {variable: coefficient} plus a constant, all Fractions. Problem
sources are written as tiny Python-like strings ("-2*(x - 4) + 3*x", "(1/2)*x + 3/4") and read by
`lin()`, which allows only numbers, one-letter names, + − ×, division by a number and brackets, and
refuses anything that isn't linear (x*x). No computer-algebra library is needed.

Display text (`pretty`, `fmt_lin`) writes fractions as "3/4"; `tokens()` splits such text into
plain strings and {"n", "d"} pieces that templates stack (see _math_text.html.j2).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from fractions import Fraction

from ._numbers import MINUS, decimal_places, fmt, is_terminating, parse, show  # noqa: F401 (re-exported)

TIMES = "×"
DIVIDE = "÷"


# --- numbers -------------------------------------------------------------------------------

def repeating(x: Fraction) -> tuple[str, str, str]:
    """Long division of a fraction: (sign and whole part, digits that don't repeat, repeating digits).
    3/8 -> ('0', '375', ''); 5/6 -> ('0', '8', '3'); -1/3 -> ('-0', '', '3')."""
    x = Fraction(x)
    sign = "-" if x < 0 else ""
    n, d = abs(x.numerator), x.denominator
    whole, r = divmod(n, d)
    digits, seen = [], {}
    while r and r not in seen:
        seen[r] = len(digits)
        q, r = divmod(r * 10, d)
        digits.append(str(q))
    if not r:
        return f"{sign}{whole}", "".join(digits), ""
    k = seen[r]
    return f"{sign}{whole}", "".join(digits[:k]), "".join(digits[k:])


def decimal_text(x: Fraction) -> str:
    """Answer-key text: '0.375', '0.8(3) repeating', '−0.(3) repeating'."""
    whole, fixed, rep = repeating(x)
    whole = whole.replace("-", MINUS)
    if not rep:
        return f"{whole}.{fixed}" if fixed else whole
    return f"{whole}.{fixed}({rep}) repeating"


# --- linear expressions ------------------------------------------------------------------

@dataclass(frozen=True)
class Lin:
    coef: tuple[tuple[str, Fraction], ...] = ()     # sorted (variable, coefficient), no zeros
    const: Fraction = Fraction(0)

    @staticmethod
    def make(coef: dict[str, Fraction] | None = None, const: Fraction | int = 0) -> "Lin":
        c = tuple(sorted((v, Fraction(k)) for v, k in (coef or {}).items() if k != 0))
        return Lin(c, Fraction(const))

    @property
    def coefs(self) -> dict[str, Fraction]:
        return dict(self.coef)

    def __add__(self, o: "Lin") -> "Lin":
        c = self.coefs
        for v, k in o.coef:
            c[v] = c.get(v, 0) + k
        return Lin.make(c, self.const + o.const)

    def scale(self, k: Fraction) -> "Lin":
        return Lin.make({v: k * c for v, c in self.coef}, k * self.const)

    def __sub__(self, o: "Lin") -> "Lin":
        return self + o.scale(Fraction(-1))

    def is_number(self) -> bool:
        return not self.coef

    def at(self, values: dict[str, Fraction]) -> Fraction:
        return self.const + sum((k * values[v] for v, k in self.coef), Fraction(0))


def lin(src: str) -> Lin:
    """Read a linear expression source ('3*x - (x - 4)/2'); anything non-linear raises ValueError."""

    def ev(node) -> Lin:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Lin.make(const=Fraction(repr(node.value)) if isinstance(node.value, float) else node.value)
        if isinstance(node, ast.Name) and len(node.id) == 1:
            return Lin.make({node.id: 1})
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            x = ev(node.operand)
            return x.scale(Fraction(-1)) if isinstance(node.op, ast.USub) else x
        if isinstance(node, ast.BinOp):
            a, b = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                if a.is_number():
                    return b.scale(a.const)
                if b.is_number():
                    return a.scale(b.const)
                raise ValueError("not linear: a letter times a letter")
            if isinstance(node.op, ast.Div):
                if not b.is_number() or b.const == 0:
                    raise ValueError("can only divide by a number that isn't 0")
                return a.scale(1 / b.const)
        raise ValueError(f"not allowed in a linear expression: {ast.dump(node)}")

    return ev(ast.parse(src.replace(MINUS, "-"), mode="eval"))


def _coef_text(k: Fraction, var: str, style: str) -> str:
    """|k| written before a letter: '' for 1, '3', '3/4', '1.05'."""
    k = abs(k)
    if k == 1:
        return ""
    return fmt(k, "decimal" if style == "decimal" else "fraction")


def fmt_lin(e: Lin, style: str = "fraction", minus: str = MINUS) -> str:
    """The one canonical form: letters in alphabetical order, then the number; 'x' not '1x',
    '−x' not '−1x', no '+ 0', no '+ −'. Fractions are 'n/d' ('3/4x'), decimals in style 'decimal'."""
    parts: list[tuple[bool, str]] = []
    for v, k in e.coef:
        parts.append((k < 0, f"{_coef_text(k, v, style)}{v}"))
    if e.const != 0 or not parts:
        parts.append((e.const < 0, fmt(abs(e.const), "decimal" if style == "decimal" else "fraction")))
    out = ""
    for n, (neg, text) in enumerate(parts):
        if n == 0:
            out = (minus if neg else "") + text
        else:
            out += f" {minus} {text}" if neg else f" + {text}"
    return out


def read_lin(text: str) -> Lin:
    """Read a canonical answer string back ('3/4x − 2', '−x + 5', '1.05a') into a Lin."""
    t = text.replace(MINUS, "-").replace(" ", "")
    if not t:
        raise ValueError("empty expression")
    src = re.sub(r"(\d+(?:\.\d+)?(?:/\d+)?)([a-z(])", r"(\1)*\2", t)
    return lin(src)


_TOKEN = re.compile(r"(\d+|[a-z])/(\d+)")


def tokens(text: str) -> list:
    """'−3/4 + 1/2x' -> ['−', {'n': 3, 'd': 4}, ' + ', {'n': 1, 'd': 2}, 'x'] for stacked fractions."""
    out: list = []
    pos = 0
    for m in _TOKEN.finditer(text):
        if m.start() > pos:
            out.append(text[pos:m.start()])
        n = m.group(1)
        out.append({"n": int(n) if n.isdigit() else n, "d": int(m.group(2))})
        pos = m.end()
    if pos < len(text):
        out.append(text[pos:])
    return out


# --- signed facts: operands and signs -------------------------------------------------------

_SIGN = {"+": "+", "-": MINUS, "*": TIMES, "/": DIVIDE}


def compute(operands: list[str], ops: list[str]) -> Fraction:
    """a op b op c… with the order of operations (× and ÷ before + and −), exactly."""
    vals = [parse(x) for x in operands]
    terms, signs_ = [vals[0]], []
    for op, v in zip(ops, vals[1:]):
        if op in "*/":
            if op == "/" and v == 0:
                raise ValueError("division by zero")
            terms[-1] = terms[-1] * v if op == "*" else terms[-1] / v
        else:
            terms.append(v)
            signs_.append(op)
    total = terms[0]
    for op, t in zip(signs_, terms[1:]):
        total = total + t if op == "+" else total - t
    return total


def show_fact(operands: list[str], ops: list[str], style: str = "fraction") -> str:
    """'-4', '*', '-6' -> '−4 × (−6)': a negative number after a sign gets brackets."""
    out = show(operands[0], style)
    for op, x in zip(ops, operands[1:]):
        s = show(x, style)
        out += f" {_SIGN[op]} " + (f"({s})" if parse(x) < 0 else s)
    return out


def page_index(spec) -> int:
    """How many pages of this sheet type come before this one in its part (or section), so a
    part that alternates two sheet types still cycles each type's layouts in order."""
    from ..syllabus import load_level

    section = load_level(spec.subject, spec.level).section_for_page(spec.page)
    part = section.part_for_page(spec.page)
    types = (part.sheet_types if part and part.sheet_types else None) or section.sheet_types
    first = (part.pages if part else section.pages)[0]
    return sum(types[(p - first) % len(types)] == spec.sheet_type for p in range(first, spec.page))


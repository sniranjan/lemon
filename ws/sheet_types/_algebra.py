"""Exact helpers shared by the Lions math sheet types (not a sheet type itself).

Numbers are stored in sheets as ints or "p/q" strings (JSON-safe) and turned back into `Fraction`s
here, so every check is exact. Printed math is a list of *tokens*: plain strings, or
`{"f": [n, d]}` for a stacked fraction n/d (always positive; its sign is in the string before it).
Verify rebuilds the tokens from the stored structure and compares, so a wrongly printed problem
can't pass while its numbers check out.

Linear expressions (one letter) are lists of terms:
- `{"c": "3", "v": "x"}`: 3x (`v` is "" for a plain number). The letter is always stored as "x";
  `tokens(..., letter)` prints the page's letter instead.
- `{"k": "2", "in": [terms]}`: 2( … ), a bracket times a number.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt

from . import _numbers
from ._numbers import MINUS


def q(value) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def fstr(value) -> str:
    """Fraction → "3" or "-1/2" (how numbers are stored)."""
    return _numbers.fmt(q(value))


def show(value) -> str:
    """Fraction → printed plain text with a real minus sign: "−1/2"."""
    return _numbers.show(q(value))


def merge(tokens: list) -> list:
    """Join neighboring strings so token lists compare (and print) simply."""
    out: list = []
    for t in tokens:
        if isinstance(t, str) and out and isinstance(out[-1], str):
            out[-1] += t
        elif t != "":
            out.append(t)
    return out


def number_tokens(value, stacked: bool = True) -> list:
    """A number with its sign; a non-whole one as a stacked fraction (or "n/d" if not `stacked`)."""
    v = q(value)
    sign = MINUS if v < 0 else ""
    a = abs(v)
    if a.denominator == 1:
        return [sign + str(a.numerator)]
    return merge([sign, {"f": [a.numerator, a.denominator]}]) if stacked else [sign + f"{a.numerator}/{a.denominator}"]


def text(tokens: list) -> str:
    """Tokens as one plain line (answer keys): fractions become n/d."""
    return "".join(t if isinstance(t, str) else f"{t['f'][0]}/{t['f'][1]}" for t in tokens)


# --- linear expressions --------------------------------------------------------------------------

def _magnitude(c: Fraction, with_letter: bool) -> list:
    a = abs(c)
    if with_letter and a == 1:
        return []
    return [str(a.numerator)] if a.denominator == 1 else [{"f": [a.numerator, a.denominator]}]


def side_tokens(terms: list[dict], letter: str = "x") -> list:
    out: list = []
    for i, t in enumerate(terms):
        c = q(t["k"] if "k" in t else t["c"])
        if i == 0:
            out.append(MINUS if c < 0 else "")
        else:
            out.append(f" {MINUS} " if c < 0 else " + ")
        if "k" in t:
            out += _magnitude(c, True) + ["("] + side_tokens(t["in"], letter) + [")"]
        else:
            out += _magnitude(c, bool(t["v"]))
            if t["v"]:
                out.append(letter if t["v"] == "x" else t["v"])
    return merge(out) if terms else ["0"]


def equation_tokens(left: list[dict], right: list[dict], letter: str = "x") -> list:
    return merge(side_tokens(left, letter) + [" = "] + side_tokens(right, letter))


def linear(terms: list[dict]) -> tuple[Fraction, Fraction]:
    """(A, B) with terms = A·x + B."""
    A = B = Fraction(0)
    for t in terms:
        if "k" in t:
            a, b = linear(t["in"])
            A += q(t["k"]) * a
            B += q(t["k"]) * b
        elif t["v"]:
            A += q(t["c"])
        else:
            B += q(t["c"])
    return A, B


def solve(left: list[dict], right: list[dict]) -> Fraction | str:
    """The solution of left = right, or "none" / "all"."""
    a1, b1 = linear(left)
    a2, b2 = linear(right)
    if a1 == a2:
        return "all" if b1 == b2 else "none"
    return (b2 - b1) / (a1 - a2)


def numbers_in(terms: list[dict]) -> list[Fraction]:
    out = []
    for t in terms:
        if "k" in t:
            out.append(q(t["k"]))
            out += numbers_in(t["in"])
        else:
            out.append(q(t["c"]))
    return out


# --- lines on a grid -----------------------------------------------------------------------------

def line_tokens(m, b, x: str = "x") -> list:
    """y = mx + b as printed tokens (y = 2x − 3, y = −x, y = 4, y = ½x + 1)."""
    m, b = q(m), q(b)
    terms = []
    if m != 0:
        terms.append({"c": fstr(m), "v": "x"})
    if b != 0 or m == 0:
        terms.append({"c": fstr(b), "v": ""})
    return merge(["y = "] + side_tokens(terms, x))


def clip(m, b, R: int) -> list[list[Fraction]]:
    """Where y = mx + b enters and leaves the square −R ≤ x, y ≤ R (left to right)."""
    m, b = q(m), q(b)
    pts = set()
    for x in (-R, R):
        y = m * x + b
        if -R <= y <= R:
            pts.add((Fraction(x), y))
    if m != 0:
        for y in (-R, R):
            x = (y - b) / m
            if -R <= x <= R:
                pts.add((x, Fraction(y)))
    ends = sorted(pts)
    return [list(ends[0]), list(ends[-1])] if len(ends) >= 2 else []


def lattice(m, b, R: int) -> list[list[int]]:
    """Whole-number points of y = mx + b inside the grid, left to right."""
    m, b = q(m), q(b)
    out = []
    for x in range(-R, R + 1):
        y = m * x + b
        if y.denominator == 1 and -R <= y <= R:
            out.append([x, int(y)])
    return out


def floats(points) -> list[list[float]]:
    """Exact points as floats for drawing (4 decimals, so the HTML is stable)."""
    return [[round(float(x), 4), round(float(y), 4)] for x, y in points]


# --- roots ---------------------------------------------------------------------------------------

def root_one_decimal(n: int) -> str:
    """√n rounded half up to one decimal, exactly: "8.1" for 65."""
    tenths = isqrt(100 * n)                      # floor(10·√n)
    # round half up: compare √n with (tenths + 0.5)/10, i.e. 400 n with (2·tenths + 1)²
    if 400 * n >= (2 * tenths + 1) ** 2:
        tenths += 1
    return f"{tenths // 10}.{tenths % 10}"


def is_square(n: int) -> bool:
    return n >= 0 and isqrt(n) ** 2 == n

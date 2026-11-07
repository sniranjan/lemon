"""The exact-number core shared by the upper math helpers (not a sheet type itself).

Pandas (`_rational`), Penguins (`_linear`), Lions (`_algebra`), Whales (`ws.algebra`) and Whales'
graphs (`_lines`) all store numbers as JSON-safe text and print them with the true minus sign
(U+2212). The pieces they had each written for themselves live here; each module re-exports what
it used to define, so their own names keep working. Otters' `_exact` stays separate: it works in
`Decimal` and non-negative mixed-number dicts.
"""

from __future__ import annotations

from fractions import Fraction

MINUS = "−"


def parse(s: str | int | Fraction) -> Fraction:
    """'3/4', '2 1/2', '-1.25', '−3', 7 -> Fraction."""
    if isinstance(s, (int, Fraction)):
        return Fraction(s)
    t = str(s).strip().replace(MINUS, "-")
    sign = -1 if t.startswith("-") else 1
    t = t.lstrip("-")
    if " " in t:
        whole, frac = t.split(" ", 1)
        return sign * (int(whole) + Fraction(frac))
    return sign * Fraction(t)


def is_terminating(x: Fraction) -> bool:
    d = Fraction(x).denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1


def decimal_places(x: Fraction) -> int:
    if not is_terminating(x):
        raise ValueError(f"{x} has no exact decimal")
    places = 0
    while (x * 10 ** places).denominator != 1:
        places += 1
    return places


def fmt(x: Fraction | int | str, style: str = "fraction", minus: str = "-") -> str:
    """Stored/answer text for a number. 'fraction': 5, 3/4, -7/4 (simplest form, improper);
    'mixed': -1 3/4; 'decimal': -1.25 (must terminate); 'money': 2.50 (whole cents)."""
    x = parse(x)
    sign = minus if x < 0 else ""
    x = abs(x)
    if style in ("decimal", "money"):
        places = decimal_places(x)
        if style == "money":
            if places > 2:
                raise ValueError(f"{x} isn't a whole number of cents")
            places = 2 if places else 0     # $3 or $2.50, never $2.5
        digits = str((x * 10 ** places).numerator)
        if places:
            digits = digits.rjust(places + 1, "0")
            return f"{sign}{digits[:-places]}.{digits[-places:]}"
        return f"{sign}{digits}"
    if x.denominator == 1:
        return f"{sign}{x.numerator}"
    if style == "mixed" and x > 1:
        w = x.numerator // x.denominator
        r = x - w
        return f"{sign}{w} {r.numerator}/{r.denominator}"
    return f"{sign}{x.numerator}/{x.denominator}"


def show(x: Fraction | int | str, style: str = "fraction") -> str:
    """A number as printed, with the true minus sign."""
    return fmt(x, style, minus=MINUS)


def minus(s) -> str:
    """Stored text as printed: '-3' -> '−3' (every hyphen becomes the true minus sign)."""
    return str(s).replace("-", MINUS)

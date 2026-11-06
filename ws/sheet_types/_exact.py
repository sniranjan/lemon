"""Exact numbers for Otters math (not a sheet type): fractions and decimals.

Sheets store only JSON-native values: a fraction or mixed number is `{"whole", "num", "den"}` of
ints, a decimal is its canonical string ("4.07", "12", "0.5"). Generators and verify compute with
`fractions.Fraction` and `decimal.Decimal` only, never floats.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction


def operand(whole: int = 0, num: int = 0, den: int = 1) -> dict:
    return {"whole": whole, "num": num, "den": den}


def value(o: dict) -> Fraction:
    return o["whole"] + Fraction(o["num"], o["den"])


def as_mixed(f: Fraction) -> dict:
    """Simplest form; more than 1 becomes a mixed number (whole + proper fraction)."""
    if f < 0:
        raise ValueError(f"negative fraction {f}")
    whole, rest = divmod(f.numerator, f.denominator)
    return operand(whole, rest, f.denominator if rest else 1)


def frac_str(f: Fraction) -> str:
    """'5/6', '1 1/12', '3' (simplest form, mixed when more than 1)."""
    m = as_mixed(f)
    if not m["num"]:
        return str(m["whole"])
    tail = f"{m['num']}/{m['den']}"
    return f"{m['whole']} {tail}" if m["whole"] else tail


def is_simplest(o: dict) -> bool:
    """A shown fraction part is proper and in lowest terms (or absent)."""
    if o["num"] == 0:
        return o["den"] == 1
    return 0 < o["num"] < o["den"] and Fraction(o["num"], o["den"]).denominator == o["den"]


def dec(s: str) -> Decimal:
    d = Decimal(s)
    if dec_str(d) != s:
        raise ValueError(f"{s!r} is not a canonical decimal (expected {dec_str(d)!r})")
    return d


def dec_str(d: Decimal) -> str:
    """Canonical text: no exponent, no trailing zeros after the point, a 0 before a leading point."""
    if d != d.to_integral_value():
        s = format(d.normalize(), "f")
    else:
        s = str(int(d))
    return s


def places(d: Decimal | str) -> int:
    """Decimal places of the canonical form (12.50 -> 1)."""
    s = dec_str(Decimal(d)) if not isinstance(d, str) else d
    return len(s.split(".")[1]) if "." in s else 0


def from_hundredths(n: int, scale: int = 2) -> Decimal:
    """n / 10**scale as an exact Decimal."""
    return Decimal(n).scaleb(-scale)

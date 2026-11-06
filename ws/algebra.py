"""A tiny exact algebra kit for Whales math (Algebra 1): polynomials, monomials with rational exponents,
radicals and quadratic roots. No CAS: integer and Fraction arithmetic only, so verify can recompute
every answer exactly.

- `Poly`: a polynomial in one or more variables with Fraction coefficients. `parse("(2x - 3)(x + 4)")`
  reads the small ASCII language the sheets store (numbers, one-letter variables, + - *, ^ whole
  number, parentheses, implicit multiplication). `Poly.text()` is the canonical ASCII form
  ("2x^2 + 5x - 12"); `pretty()` turns ASCII into what a reader sees ("2x² + 5x − 12": real minus,
  superscript digits).
- `Mono`: coefficient × variables with Fraction exponents (exponent rules, rational exponents).
- `root_parts(n, k)`: k = out^n × inside with `inside` free of n-th powers (√72 = 6√2).
- `QRoot`: (p + q√d)/s, the exact form of a quadratic's root; `quadratic_roots(a, b, c)`.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from fractions import Fraction

MINUS = "−"
SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")

Monomial = tuple[tuple[str, int], ...]   # sorted (variable, exponent) pairs; () is the constant term


def _mono_mul(a: Monomial, b: Monomial) -> Monomial:
    exps: dict[str, int] = dict(a)
    for v, e in b:
        exps[v] = exps.get(v, 0) + e
    return tuple(sorted((v, e) for v, e in exps.items() if e))


class Poly:
    """A polynomial with exact coefficients. Immutable in use; equality compares terms."""

    __slots__ = ("terms",)

    def __init__(self, terms: dict[Monomial, Fraction] | None = None):
        self.terms = {m: Fraction(c) for m, c in (terms or {}).items() if c}

    @classmethod
    def const(cls, c) -> Poly:
        return cls({(): Fraction(c)})

    @classmethod
    def var(cls, v: str) -> Poly:
        return cls({((v, 1),): Fraction(1)})

    def __add__(self, other: Poly) -> Poly:
        out = dict(self.terms)
        for m, c in other.terms.items():
            out[m] = out.get(m, 0) + c
        return Poly(out)

    def __neg__(self) -> Poly:
        return Poly({m: -c for m, c in self.terms.items()})

    def __sub__(self, other: Poly) -> Poly:
        return self + (-other)

    def __mul__(self, other: Poly) -> Poly:
        out: dict[Monomial, Fraction] = {}
        for m1, c1 in self.terms.items():
            for m2, c2 in other.terms.items():
                m = _mono_mul(m1, m2)
                out[m] = out.get(m, 0) + c1 * c2
        return Poly(out)

    def __pow__(self, n: int) -> Poly:
        out = Poly.const(1)
        for _ in range(n):
            out = out * self
        return out

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Poly) and self.terms == other.terms

    def __hash__(self) -> int:
        return hash(frozenset(self.terms.items()))

    def __repr__(self) -> str:
        return f"Poly({self.text()!r})"

    def degree(self) -> int:
        return max((sum(e for _, e in m) for m in self.terms), default=0)

    def variables(self) -> set[str]:
        return {v for m in self.terms for v, _ in m}

    def coeff(self, *mono: tuple[str, int]) -> Fraction:
        return self.terms.get(tuple(sorted(mono)), Fraction(0))

    def univariate(self, v: str = "x") -> list[Fraction]:
        """Coefficients [c0, c1, …] of a polynomial in v alone."""
        if self.variables() - {v}:
            raise ValueError(f"{self.text()} is not a polynomial in {v} alone")
        n = self.degree()
        return [self.terms.get(((v, k),) if k else (), Fraction(0)) for k in range(n + 1)]

    def content(self) -> int:
        """gcd of the (integer) coefficients."""
        g = 0
        for c in self.terms.values():
            if c.denominator != 1:
                raise ValueError("content() needs integer coefficients")
            g = math.gcd(g, c.numerator)
        return g

    def _order(self) -> list[Monomial]:
        # descending total degree, then alphabetical variables first (x² before xy before y²)
        def key(m: Monomial):
            return (-sum(e for _, e in m), [(v, -e) for v, e in m])
        return sorted(self.terms, key=key)

    def text(self) -> str:
        """Canonical ASCII: '3x^2 - 5x + 2', 'x^2y - 1', '0'."""
        if not self.terms:
            return "0"
        parts = []
        for i, m in enumerate(self._order()):
            c = self.terms[m]
            sign = "-" if c < 0 else "+"
            a = abs(c)
            body = "".join(v + (f"^{e}" if e != 1 else "") for v, e in m)
            num = _frac_text(a)
            if body and a == 1:
                num = ""
            elif body and a.denominator != 1:
                num = f"({num})"
            term = num + body
            parts.append(("-" if sign == "-" else "") + term if i == 0 else f" {sign} {term}")
        return "".join(parts)


def _frac_text(f: Fraction) -> str:
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


# --- parser ------------------------------------------------------------------------------

_TOKEN = re.compile(r"\s*(?:(\d+)|([a-z])|(.))")


def _tokens(s: str) -> list[str]:
    out = []
    for num, var, other in _TOKEN.findall(s):
        tok = num or var or other
        if tok.strip():
            out.append(tok)
    return out


def parse(s: str) -> Poly:
    """Parse the ASCII expression language: '3x^2 - 2(x + 1)(x - 4) + (x - 1)^2'."""
    toks = _tokens(s.replace(MINUS, "-").replace("·", "*"))
    pos = 0

    def peek() -> str | None:
        return toks[pos] if pos < len(toks) else None

    def take(expected: str | None = None) -> str:
        nonlocal pos
        tok = peek()
        if tok is None or (expected and tok != expected):
            raise ValueError(f"bad expression {s!r}: expected {expected or 'more'} at token {pos}")
        pos += 1
        return tok

    def expr() -> Poly:
        out = term()
        while peek() in ("+", "-"):
            op = take()
            out = out + term() if op == "+" else out - term()
        return out

    def term() -> Poly:
        out = unary()
        while True:
            tok = peek()
            if tok == "*":
                take()
                out = out * unary()
            elif tok is not None and (tok == "(" or tok.isalnum()):
                out = out * power()
            else:
                return out

    def unary() -> Poly:
        if peek() == "-":
            take()
            return -unary()
        return power()

    def power() -> Poly:
        base = atom()
        if peek() == "^":
            take()
            n = take()
            if not n.isdigit():
                raise ValueError(f"bad expression {s!r}: exponents must be whole numbers")
            return base ** int(n)
        return base

    def atom() -> Poly:
        tok = take()
        if tok.isdigit():
            return Poly.const(int(tok))
        if tok.isalpha():
            return Poly.var(tok)
        if tok == "(":
            inner = expr()
            take(")")
            return inner
        raise ValueError(f"bad expression {s!r}: unexpected {tok!r}")

    out = expr()
    if pos != len(toks):
        raise ValueError(f"bad expression {s!r}: trailing {toks[pos:]}")
    return out


_RADICAL = re.compile(r"R\((\d)\|([^()|]*(?:\([^()]*\)[^()|]*)*)\)")
_ROOT_SIGN = {2: "√", 3: "∛", 4: "∜"}


def radical(n: int, body: str) -> str:
    """The ASCII markup for an n-th root: radical(2, "2x") = 'R(2|2x)'."""
    return f"R({n}|{body})"


def pretty(s: str) -> str:
    """ASCII → reader text: '-' → '−', '^12' → '¹²', '*' → '·', rational exponents '^(2/3)' → '²⁄³',
    roots 'R(2|72)' → '√72', 'R(3|2x)' → '∛(2x)'."""
    def root(m):
        body = m.group(2)
        simple = body.isdigit() or (len(body) == 1 and body.isalpha())
        return _ROOT_SIGN[int(m.group(1))] + (body if simple else f"({body})")
    s = _RADICAL.sub(root, s)
    s = re.sub(r"\^\((-?\d+)/(\d+)\)", lambda m: m.group(1).translate(SUP) + "⁄" + m.group(2).translate(SUP), s)
    s = re.sub(r"\^(-?\d+)", lambda m: m.group(1).translate(SUP), s)
    return s.replace("-", MINUS).replace("*", "·")


def html_expr(s: str) -> str:
    """ASCII → HTML for a sheet: like pretty(), but rational exponents become a raised span (class rexp)
    big enough to read, since Unicode has no superscript slash, and roots get an index and a bar
    (classes rad, idx, rd). The template sets the sizes."""
    import html as _html
    from markupsafe import Markup

    s = _html.escape(s)
    s = re.sub(r"\^\((-?\d+)/(\d+)\)",
               lambda m: f'<span class="rexp">{m.group(1)}/{m.group(2)}</span>', s)
    s = re.sub(r"\^(-?\d+)", lambda m: m.group(1).translate(SUP), s)
    s = s.replace("-", MINUS).replace("*", "·")
    s = s.replace("R(", "\x00(")
    s = re.sub(r"\x00\((\d)\|([^()|]*(?:\([^()]*\)[^()|]*)*)\)",
               lambda m: ('<span class="rad">' + (f'<span class="idx">{m.group(1)}</span>' if m.group(1) != "2" else "")
                          + f'√<span class="rd">{m.group(2)}</span></span>'), s)
    return Markup(s.replace("\x00", "R"))


# --- monomials with rational exponents ----------------------------------------------------

@dataclass(frozen=True)
class Mono:
    """coeff × Π var^exp, exponents may be negative or fractional. Exponents of 0 are dropped."""

    coeff: Fraction
    exps: tuple[tuple[str, Fraction], ...] = ()

    @classmethod
    def make(cls, coeff, exps: dict[str, Fraction] | None = None) -> Mono:
        e = tuple(sorted((v, Fraction(x)) for v, x in (exps or {}).items() if Fraction(x) != 0))
        return cls(Fraction(coeff), e)

    @classmethod
    def from_json(cls, d: dict) -> Mono:
        """{"c": "3", "x": "2", "y": "-1/2"} → 3x²y^(−1/2)."""
        return cls.make(Fraction(d.get("c", "1")), {v: Fraction(x) for v, x in d.items() if v != "c"})

    def to_json(self) -> dict:
        out = {"c": _frac_text(self.coeff)}
        out.update({v: _frac_text(e) for v, e in self.exps})
        return out

    def __mul__(self, o: Mono) -> Mono:
        e = dict(self.exps)
        for v, x in o.exps:
            e[v] = e.get(v, 0) + x
        return Mono.make(self.coeff * o.coeff, e)

    def __truediv__(self, o: Mono) -> Mono:
        return self * o.inverse()

    def inverse(self) -> Mono:
        return Mono.make(1 / self.coeff, {v: -x for v, x in self.exps})

    def power(self, p: Fraction) -> Mono:
        p = Fraction(p)
        c = rational_power(self.coeff, p)
        if c is None:
            raise ValueError(f"({self.coeff})^{p} is not rational")
        return Mono.make(c, {v: x * p for v, x in self.exps})

    def text(self, positive: bool = True) -> str:
        """ASCII, e.g. '12x^7', '3/x^2' (positive=True moves negative exponents below the bar),
        'x^(2/3)'."""
        def var_text(items):
            return "".join(v + ("" if e == 1 else f"^{_frac_text(e)}" if e.denominator == 1 else
                                f"^({e.numerator}/{e.denominator})") for v, e in items)
        c = self.coeff
        if not positive:
            body = var_text(self.exps)
            return _coeff_prefix(c, bool(body)) + body
        up = [(v, e) for v, e in self.exps if e > 0]
        down = [(v, -e) for v, e in self.exps if e < 0]
        top_c, bot_c = abs(c.numerator), c.denominator
        sign = "-" if c < 0 else ""
        top = var_text(up)
        top = (str(top_c) if top_c != 1 or not top else "") + top
        bottom = var_text(down)
        bottom = (str(bot_c) if bot_c != 1 or not bottom else "") + bottom
        return sign + (top if bottom == "1" else f"{top}/{bottom}")


def _coeff_prefix(c: Fraction, has_body: bool) -> str:
    if has_body and c == 1:
        return ""
    if has_body and c == -1:
        return "-"
    return _frac_text(c)


def int_root(n: int, k: int) -> int | None:
    """The whole k-th root of n ≥ 0, or None."""
    if n < 0:
        return None
    r = round(n ** (1 / k))
    for cand in (r - 1, r, r + 1):
        if cand >= 0 and cand ** k == n:
            return cand
    return None


def rational_power(base: Fraction, p: Fraction) -> Fraction | None:
    """base^p exactly, when it is rational (8^(2/3) = 4, 16^(-1/2) = 1/4); else None."""
    base, p = Fraction(base), Fraction(p)
    if p.denominator == 1:
        if base == 0 and p < 0:
            return None
        return base ** p.numerator
    if base < 0:
        return None
    num, den = int_root(base.numerator, p.denominator), int_root(base.denominator, p.denominator)
    if num is None or den is None:
        return None
    return Fraction(num, den) ** p.numerator


def root_parts(n: int, k: int) -> tuple[int, int]:
    """k = out^n × inside with inside free of n-th powers: root_parts(2, 72) = (6, 2)."""
    if k < 1:
        raise ValueError("root_parts needs k ≥ 1")
    out, inside, f = 1, k, 2
    while f ** n <= inside:
        while inside % (f ** n) == 0:
            inside //= f ** n
            out *= f
        f += 1
    return out, inside


def squarefree(d: int) -> bool:
    return d >= 1 and root_parts(2, d)[1] == d


# --- quadratic roots -----------------------------------------------------------------------

@dataclass(frozen=True)
class QRoot:
    """(p + q√d)/s exactly: d square-free ≥ 2 when q ≠ 0, s > 0, gcd(p, q, s) = 1."""

    p: int
    q: int
    d: int
    s: int

    def is_rational(self) -> bool:
        return self.q == 0

    def value(self) -> float:
        return (self.p + self.q * math.sqrt(self.d)) / self.s

    def rational(self) -> Fraction:
        if self.q:
            raise ValueError("irrational root")
        return Fraction(self.p, self.s)

    def satisfies(self, a: int, b: int, c: int) -> bool:
        """a·t² + b·t + c = 0 for t = (p + q√d)/s, in exact Q(√d) arithmetic (times s²)."""
        p, q, d, s = self.p, self.q, self.d, self.s
        rational = a * (p * p + q * q * d) + b * p * s + c * s * s
        irrational = 2 * a * p * q + b * q * s
        return rational == 0 and irrational == 0


def _reduce(p: int, q: int, d: int, s: int) -> QRoot:
    if s < 0:
        p, q, s = -p, -q, -s
    if q == 0:
        d = 1
    g = math.gcd(math.gcd(p, q), s)
    return QRoot(p // g, q // g, d, s // g)


def quadratic_roots(a: int, b: int, c: int) -> list[QRoot]:
    """Real roots of a·x² + b·x + c = 0 (a ≠ 0), smaller first; a double root once."""
    if a == 0:
        raise ValueError("not a quadratic")
    disc = b * b - 4 * a * c
    if disc < 0:
        return []
    out_, d = root_parts(2, disc) if disc else (0, 1)
    if d == 1:
        roots = sorted({Fraction(-b + sgn * out_, 2 * a) for sgn in (1, -1)})
        return [_reduce(r.numerator, 0, 1, r.denominator) for r in roots]
    lo, hi = _reduce(-b, -out_, d, 2 * a), _reduce(-b, out_, d, 2 * a)
    return sorted([lo, hi], key=QRoot.value)


def roots_text(roots: list[QRoot], var: str = "x") -> str:
    """Canonical answer text: 'x = −3 or x = 1/2', 'x = 4', 'x = (3 ± √5)/2', 'x = 1 ± 2√3', 'x = ±√7'."""
    if not roots:
        return "no real solutions"
    if all(r.is_rational() for r in roots):
        return " or ".join(f"{var} = {_signed(r.rational())}" for r in roots)
    r = max(roots, key=QRoot.value)          # the + root: q > 0
    rad = ("" if r.q == 1 else str(r.q)) + f"√{r.d}"
    if r.p == 0:
        core = f"±{rad}"
    else:
        core = f"{_signed(Fraction(r.p))} ± {rad}"
    if r.s == 1:
        return f"{var} = {core}"
    return f"{var} = ({core})/{r.s}" if r.p else f"{var} = {core}/{r.s}"


def _signed(f: Fraction) -> str:
    return _frac_text(f).replace("-", MINUS)


def fmt_int(n: int) -> str:
    """A whole number with a real minus sign."""
    return str(n).replace("-", MINUS)

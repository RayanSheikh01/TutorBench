"""Formatting + parsing helpers shared by Maths templates.

`to_expr` normalises GCSE-style display maths ("3x + 2", "x² + 5x + 6") into a
SymPy expression so verification can re-derive answers from the rendered stem
rather than trusting the value computed at generation time.
"""
import re

from sympy import Symbol, sympify

x = Symbol("x")


def normalize_math(s: str) -> str:
    """Turn display maths into a SymPy-parseable string (implicit mult, ², ^)."""
    s = s.replace("−", "-").replace("²", "**2").replace("^", "**")
    # implicit multiplication: 3x -> 3*x, 2( -> 2*(
    s = re.sub(r"(\d)\s*([A-Za-z(])", r"\1*\2", s)
    # x( -> x*(  ,  )( -> )*(
    s = re.sub(r"([A-Za-z)])\s*\(", r"\1*(", s)
    return s


def to_expr(s: str):
    """Parse a display-maths string into a SymPy expression."""
    return sympify(normalize_math(s))


def linear_str(m: int, c: int, var: str = "x") -> str:
    """Render m*var + c as readable maths: '3x + 2', '-x - 5', 'x', '4'."""
    if m == 0:
        return str(c)
    if m == 1:
        term = var
    elif m == -1:
        term = f"-{var}"
    else:
        term = f"{m}{var}"
    if c > 0:
        return f"{term} + {c}"
    if c < 0:
        return f"{term} - {abs(c)}"
    return term


def quad_str(b: int, c: int, var: str = "x") -> str:
    """Render var² + b*var + c, e.g. 'x² + 5x + 6', 'x² - 3x - 10'."""
    out = f"{var}²"
    if b == 1:
        out += f" + {var}"
    elif b == -1:
        out += f" - {var}"
    elif b > 0:
        out += f" + {b}{var}"
    elif b < 0:
        out += f" - {abs(b)}{var}"
    if c > 0:
        out += f" + {c}"
    elif c < 0:
        out += f" - {abs(c)}"
    return out


def signed(n: int) -> str:
    """' + 3' or ' - 3' — for factor display like (x - 3)."""
    return f"+ {n}" if n >= 0 else f"- {abs(n)}"

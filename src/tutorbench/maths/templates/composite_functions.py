"""Composite functions template (M-FUNC-COMP-01).

Random linear f, g; ask for fg(x) or gf(x). SymPy composes for the model answer;
verification independently re-parses f, g and the claimed answer from the rendered
stem and checks they agree.
"""
import re
from random import Random

from sympy import expand, simplify

from tutorbench.maths.base import Template
from tutorbench.maths.util import linear_str, to_expr, x
from tutorbench.models import Difficulty, MarkPoint, QType, Question, Subject

_NONZERO = [n for n in range(-5, 6) if n != 0]


class CompositeFunctions(Template):
    spec_code = "M-FUNC-COMP-01"
    topic = "Functions"
    subtopic = "Composite functions"

    def generate(self, rng: Random) -> Question:
        a, c = rng.choice(_NONZERO), rng.choice(_NONZERO)
        b, d = rng.randint(-9, 9), rng.randint(-9, 9)
        which = rng.choice(["fg", "gf"])

        f, g = a * x + b, c * x + d
        inner, outer = (g, f) if which == "fg" else (f, g)
        answer = expand(outer.subs(x, inner))
        ans_str = _expr_to_display(answer)

        f_str, g_str = linear_str(a, b), linear_str(c, d)
        stem = (
            f"The functions f and g are defined by f(x) = {f_str} and "
            f"g(x) = {g_str}. Work out {which}(x), giving your answer in its "
            f"simplest form."
        )
        # fg(x) means f(g(x)) (apply g first, then f); gf(x) means g(f(x)).
        if which == "fg":
            outer, inner_name, inner_str = "f", "g", g_str
        else:
            outer, inner_name, inner_str = "g", "f", f_str
        working = (
            f"{which}(x) = {outer}({inner_name}(x)) = apply {outer} to "
            f"({inner_str}) = {ans_str}"
        )
        marks = 3
        scheme = [
            MarkPoint(description=f"Substitutes {inner_name}(x) into {outer}", marks=1),
            MarkPoint(description="Expands the brackets correctly", marks=1),
            MarkPoint(description=f"Correct simplified answer {ans_str}", marks=1),
        ]
        return Question(
            id=f"comp-{a}-{b}-{c}-{d}-{which}",
            subject=Subject.maths,
            spec_code=self.spec_code,
            topic=self.topic,
            subtopic=self.subtopic,
            difficulty=Difficulty.medium,
            marks=marks,
            type=QType.calculation,
            stem=stem,
            model_answer=f"{which}(x) = {ans_str}",
            working=working,
            mark_scheme=scheme,
        )

    def _verify(self, q: Question) -> bool:
        m = re.search(
            r"f\(x\) = (.+?) and g\(x\) = (.+?)\. Work out (fg|gf)\(x\)", q.stem
        )
        if not m:
            return False
        f, g, which = to_expr(m.group(1)), to_expr(m.group(2)), m.group(3)
        inner, outer = (g, f) if which == "fg" else (f, g)
        recomputed = expand(outer.subs(x, inner))
        claimed = to_expr(q.model_answer.split("=", 1)[1])
        return simplify(recomputed - claimed) == 0


def _expr_to_display(expr) -> str:
    """SymPy expr -> '6*x - 1' style turned into readable '6x - 1'."""
    return str(expr).replace("*", "")

"""Quadratics template (M-QUAD-SOLVE-01).

Integer roots by construction so factorising is clean: (x - r1)(x - r2) = 0.
Verification re-parses the quadratic from the stem and solves it independently
with SymPy, comparing the root set to the claimed answer.
"""
import re
from random import Random

from sympy import solve

from tutorbench.maths.base import Template
from tutorbench.maths.util import quad_str, signed, to_expr, x
from tutorbench.models import Difficulty, MarkPoint, QType, Question, Subject


class Quadratics(Template):
    spec_code = "M-QUAD-SOLVE-01"
    topic = "Quadratics"
    subtopic = "Solving quadratics"

    def generate(self, rng: Random) -> Question:
        r1 = rng.randint(-9, 9)
        r2 = rng.randint(-9, 9)
        while r2 == r1:
            r2 = rng.randint(-9, 9)
        b, c = -(r1 + r2), r1 * r2
        lo, hi = sorted((r1, r2))

        stem = f"Solve the equation {quad_str(b, c)} = 0 by factorising."
        working = (
            f"(x {signed(-r1)})(x {signed(-r2)}) = 0, so x = {r1} or x = {r2}"
        )
        return Question(
            id=f"quad-{r1}-{r2}",
            subject=Subject.maths,
            spec_code=self.spec_code,
            topic=self.topic,
            subtopic=self.subtopic,
            difficulty=Difficulty.medium,
            marks=3,
            type=QType.calculation,
            stem=stem,
            model_answer=f"x = {lo} or x = {hi}",
            working=working,
            mark_scheme=[
                MarkPoint(description="Factorises into two correct brackets", marks=1),
                MarkPoint(description=f"First root x = {lo}", marks=1),
                MarkPoint(description=f"Second root x = {hi}", marks=1),
            ],
        )

    def _verify(self, q: Question) -> bool:
        m = re.search(r"equation (.+?) = 0", q.stem)
        if not m:
            return False
        roots = {int(r) for r in solve(to_expr(m.group(1)), x)}
        claimed = {int(r) for r in re.findall(r"x = (-?\d+)", q.model_answer)}
        return roots == claimed

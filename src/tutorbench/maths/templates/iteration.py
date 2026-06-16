"""Iteration / fixed-point template (M-ITER-FIXP-01).

Newton-style iteration x_(n+1) = (x_n + a/x_n)/2 converging to √a. Student gives
x_1..x_3 to N d.p. Generation picks a non-square a and guards rounding stability
(x_3 and x_4 must round identically) so the answer is unambiguous. Verification
re-extracts a and x_0 from the stem and recomputes.
"""
import math
import re
from random import Random

from tutorbench.maths.base import Template
from tutorbench.models import Difficulty, MarkPoint, QType, Question, Subject

N_DP = 3


def _iterate(a: float, x0: float, steps: int) -> list[float]:
    vals = []
    prev = x0
    for _ in range(steps):
        prev = (prev + a / prev) / 2
        vals.append(prev)
    return vals


class Iteration(Template):
    spec_code = "M-ITER-FIXP-01"
    topic = "Solving equations"
    subtopic = "Iterative methods"

    def generate(self, rng: Random) -> Question:
        a = self._pick_a(rng)
        x0 = round(math.sqrt(a))
        x1, x2, x3 = _iterate(a, x0, 3)
        stem = (
            f"Show that the equation x² = {a} can be solved using the iterative "
            f"formula x_(n+1) = (x_n + {a}/x_n) / 2. Starting with x_0 = {x0}, "
            f"find x_1, x_2 and x_3, giving each value to {N_DP} decimal places."
        )
        working = (
            f"x_1 = {x1:.{N_DP}f}, x_2 = {x2:.{N_DP}f}, x_3 = {x3:.{N_DP}f} "
            f"(→ √{a} ≈ {math.sqrt(a):.{N_DP}f})"
        )
        return Question(
            id=f"iter-{a}-{x0}",
            subject=Subject.maths,
            spec_code=self.spec_code,
            topic=self.topic,
            subtopic=self.subtopic,
            difficulty=Difficulty.medium,
            marks=3,
            type=QType.calculation,
            stem=stem,
            model_answer=f"x_3 = {x3:.{N_DP}f}",
            working=working,
            mark_scheme=[
                MarkPoint(description=f"Correct x_1 = {x1:.{N_DP}f}", marks=1),
                MarkPoint(description=f"Correct x_2 = {x2:.{N_DP}f}", marks=1),
                MarkPoint(description=f"Correct x_3 = {x3:.{N_DP}f}", marks=1),
            ],
        )

    @staticmethod
    def _pick_a(rng: Random) -> int:
        while True:
            a = rng.randint(2, 50)
            if math.isqrt(a) ** 2 == a:
                continue  # skip perfect squares
            x0 = round(math.sqrt(a))
            x3, x4 = _iterate(a, x0, 4)[-2:]
            if round(x3, N_DP) == round(x4, N_DP):  # rounding is stable
                return a

    def _verify(self, q: Question) -> bool:
        a = int(re.search(r"x² = (\d+)", q.stem).group(1))
        x0 = int(re.search(r"x_0 = (\d+)", q.stem).group(1))
        n = int(re.search(r"to (\d+) decimal", q.stem).group(1))
        x3 = _iterate(a, x0, 3)[-1]
        return q.model_answer.strip() == f"x_3 = {x3:.{n}f}"

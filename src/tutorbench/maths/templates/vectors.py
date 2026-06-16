"""2D vectors template (M-VEC-ARITH-01 combine / M-VEC-ARITH-02 magnitude).

Two subtypes chosen at random: a scalar combination of two column vectors, or the
magnitude of one. Verification re-parses the vectors and operation from the stem and
recomputes independently.
"""
import re
from random import Random

from sympy import Integer, sqrt

from tutorbench.maths.base import Template
from tutorbench.maths.util import to_expr
from tutorbench.models import Difficulty, MarkPoint, QType, Question, Subject

# clean Pythagorean triples for integer magnitudes
_TRIPLES = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (7, 24, 25), (9, 12, 15)]
_VEC_RE = re.compile(r"\((-?\d+),\s*(-?\d+)\)")


def _scaled(k: int, name: str) -> str:
    if k == 1:
        return name
    if k == -1:
        return f"-{name}"
    return f"{k}{name}"


def _op_string(s1: int, s2: int) -> str:
    t1 = _scaled(s1, "a")
    if s2 >= 0:
        return f"{t1} + {_scaled(s2, 'b')}"
    return f"{t1} - {_scaled(abs(s2), 'b')}"


def _apply_op(op: str, av: tuple[int, int], bv: tuple[int, int]) -> tuple:
    out = []
    for ai, bi in zip(av, bv):
        s = op.replace("a", f"({ai})").replace("b", f"({bi})")
        out.append(to_expr(s))
    return tuple(out)


class Vectors(Template):
    spec_code = "M-VEC-ARITH-01"
    topic = "Vectors"
    subtopic = "2D vector arithmetic"

    def generate(self, rng: Random) -> Question:
        if rng.random() < 0.5:
            return self._combine(rng)
        return self._magnitude(rng)

    def _combine(self, rng: Random) -> Question:
        av = (rng.randint(-6, 6), rng.randint(-6, 6))
        bv = (rng.randint(-6, 6), rng.randint(-6, 6))
        nz = [n for n in range(-3, 4) if n != 0]
        s1, s2 = rng.choice(nz), rng.choice(nz)
        op = _op_string(s1, s2)
        rx, ry = _apply_op(op, av, bv)
        stem = (
            f"The vectors are a = ({av[0]}, {av[1]}) and b = ({bv[0]}, {bv[1]}). "
            f"Work out {op}, giving your answer as a column vector."
        )
        return Question(
            id=f"vec-comb-{av[0]}-{av[1]}-{bv[0]}-{bv[1]}-{s1}-{s2}",
            subject=Subject.maths,
            spec_code="M-VEC-ARITH-01",
            topic=self.topic,
            subtopic=self.subtopic,
            difficulty=Difficulty.easy,
            marks=2,
            type=QType.calculation,
            stem=stem,
            model_answer=f"({rx}, {ry})",
            working=f"{op} = ({rx}, {ry}) (component-wise)",
            mark_scheme=[
                MarkPoint(description="Correct method (component-wise)", marks=1),
                MarkPoint(description=f"Correct answer ({rx}, {ry})", marks=1),
            ],
        )

    def _magnitude(self, rng: Random) -> Question:
        p, q, h = rng.choice(_TRIPLES)
        ax = p * rng.choice([-1, 1])
        ay = q * rng.choice([-1, 1])
        stem = (
            f"The vector a = ({ax}, {ay}). Work out the magnitude |a|, "
            f"giving your answer as an integer."
        )
        return Question(
            id=f"vec-mag-{ax}-{ay}",
            subject=Subject.maths,
            spec_code="M-VEC-ARITH-02",
            topic=self.topic,
            subtopic=self.subtopic,
            difficulty=Difficulty.easy,
            marks=2,
            type=QType.calculation,
            stem=stem,
            model_answer=f"|a| = {h}",
            working=f"|a| = √({ax}² + {ay}²) = √{ax**2 + ay**2} = {h}",
            mark_scheme=[
                MarkPoint(description="Squares and sums the components", marks=1),
                MarkPoint(description=f"Correct magnitude {h}", marks=1),
            ],
        )

    def _verify(self, q: Question) -> bool:
        vecs = _VEC_RE.findall(q.stem)
        if "magnitude" in q.stem:
            (ax, ay) = vecs[0]
            recomputed = sqrt(Integer(ax) ** 2 + Integer(ay) ** 2)
            claimed = to_expr(q.model_answer.split("=", 1)[1])
            return recomputed == claimed
        (ax, ay), (bx, by) = vecs[0], vecs[1]
        m = re.search(r"Work out (.+?), giving", q.stem)
        if not m:
            return False
        rx, ry = _apply_op(m.group(1), (int(ax), int(ay)), (int(bx), int(by)))
        cx, cy = _VEC_RE.findall(q.model_answer)[0]
        return rx == Integer(cx) and ry == Integer(cy)

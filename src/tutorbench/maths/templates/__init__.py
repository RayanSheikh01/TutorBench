"""Registry of deterministic Maths templates."""
from tutorbench.maths.base import Template
from tutorbench.maths.templates.composite_functions import CompositeFunctions
from tutorbench.maths.templates.iteration import Iteration
from tutorbench.maths.templates.quadratics import Quadratics
from tutorbench.maths.templates.vectors import Vectors

TEMPLATES: dict[str, type[Template]] = {
    "composite": CompositeFunctions,
    "vectors": Vectors,
    "iteration": Iteration,
    "quadratics": Quadratics,
}

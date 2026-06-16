

from abc import ABC, abstractmethod

from tutorbench.models import Question


class Template(ABC):
    spec_code: str
    topic: str
    subtopic: str

    @abstractmethod
    def generate(self, rng) -> Question: ...
    @abstractmethod
    def _verify(self, q) -> bool: ...
    
    

def build_question_from_template(template: Template, rng) -> Question:
    q = template.generate(rng)
    assert template._verify(q), "Generated question does not meet template specifications"
    return q
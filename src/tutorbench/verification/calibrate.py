from pydantic import BaseModel
from tutorbench.models import Question
from tutorbench.verification.cs import _reanswer_agrees


class LabelledQ(BaseModel):
    question: Question
    good: bool

def sweep(items, *, client, model, ns=(1,3,5), thresholds=(0.5, 0.66, 0.75)):
    """Run a sweep of re-answering and thresholding; return labelled questions."""
    labelled = []
    for q in items:
        for n in ns:
            agree = _reanswer_agrees(q, client=client, model=model, n=n)
            for threshold in thresholds:
                good = agree >= threshold
                labelled.append(LabelledQ(question=q, good=good))
                
    return labelled
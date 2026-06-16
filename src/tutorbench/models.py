    

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Subject(str, Enum):
    math = "math"
    physics = "physics"
    chemistry = "chemistry"
    biology = "biology"
    
class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
    
    
class QType(str, Enum):
    mcq = "mcq"
    short_answer = "short_answer"
    long_answer = "long_answer"
    
class MarkPoint(BaseModel):
    description: str
    points: int
    
class Question(BaseModel):
    subject: Subject
    difficulty: Difficulty
    qtype: QType
    question: str = Field(..., min_length=1)  # non-empty question stem
    options: Optional[List[str]] = None  # for MCQs
    answer: str = Field(..., min_length=1)  # non-empty answer
    mark_points: List[MarkPoint]
    
class MarkAward(BaseModel):
    description: str
    points_awarded: int
    justification: Optional[str] = None

class Submission(BaseModel):
    question: Question
    student_answer: str
    awarded_marks: List[MarkAward]
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class EvaluationResult(BaseModel):
    question_id: UUID
    question_number: int
    student_answer: str
    marks_obtained: float
    max_marks: int
    feedback: str
    
    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    paper_id: UUID

class Submission(BaseModel):
    id: UUID
    paper_id: UUID
    student_id: UUID
    image_path: str
    extracted_text: Optional[str]
    submitted_at: datetime
    status: str
    total_marks: Optional[float] = None
    max_marks: Optional[int] = None
    evaluations: List[EvaluationResult] = []
    
    class Config:
        from_attributes = True

class SubmissionList(BaseModel):
    id: UUID
    student_name: str
    student_email: str
    submitted_at: datetime
    status: str
    total_marks: Optional[float] = None
    max_marks: Optional[int] = None
    
    class Config:
        from_attributes = True

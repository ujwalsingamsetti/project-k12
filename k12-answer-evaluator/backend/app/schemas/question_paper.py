from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.question_paper import Subject

class QuestionBase(BaseModel):
    question_number: int
    question_text: str
    question_type: str
    marks: int
    expected_keywords: Optional[List[str]] = None
    options: Optional[dict] = None  # For MCQ
    correct_answer: Optional[str] = None  # For MCQ

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: UUID
    paper_id: UUID
    
    class Config:
        from_attributes = True

class QuestionPaperBase(BaseModel):
    title: str
    subject: Subject
    class_level: int = 12
    total_marks: int
    duration_minutes: int
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None

class QuestionPaperCreate(QuestionPaperBase):
    questions: List[QuestionCreate]

class QuestionPaper(QuestionPaperBase):
    id: UUID
    teacher_id: UUID
    created_at: datetime
    questions: List[Question] = []
    
    class Config:
        from_attributes = True

class QuestionPaperList(BaseModel):
    id: UUID
    title: str
    subject: Subject
    total_marks: int
    duration_minutes: int
    created_at: datetime
    questions_count: int
    submissions_count: int
    
    class Config:
        from_attributes = True

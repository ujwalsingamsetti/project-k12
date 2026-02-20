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
    section: Optional[str] = None  # e.g. 'A', 'B', 'C', 'D', 'E'
    question_subtype: Optional[str] = None  # 'assertion_reason', 'case_study', etc.
    has_or_option: Optional[bool] = False  # True if question has OR alternative

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
    class_level: str = "12"
    total_marks: int
    duration_minutes: int
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    # Exam mode fields
    is_exam_mode: bool = False
    exam_start_time: Optional[datetime] = None
    exam_end_time: Optional[datetime] = None

class QuestionPaperCreate(QuestionPaperBase):
    questions: List[QuestionCreate]

class QuestionPaper(QuestionPaperBase):
    id: UUID
    teacher_id: UUID
    created_at: datetime
    questions: List[Question] = []
    pdf_path: Optional[str] = None
    
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

from sqlalchemy import Column, String, Integer, Text, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base

class QuestionType(str, enum.Enum):
    SHORT = "short"
    LONG = "long"
    MCQ = "mcq"

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("question_papers.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    marks = Column(Integer, nullable=False)
    expected_keywords = Column(JSON)
    options = Column(JSON, nullable=True)  # For MCQ: {"A": "option1", "B": "option2", ...}
    correct_answer = Column(String(10), nullable=True)  # For MCQ: "A", "B", "C", "D"
    section = Column(String(10), nullable=True)  # Section A, B, C, etc.
    has_or_option = Column(Boolean, default=False)  # True if question has OR/Either-Or
    
    paper = relationship("QuestionPaper", back_populates="questions")
    evaluations = relationship("Evaluation", back_populates="question")

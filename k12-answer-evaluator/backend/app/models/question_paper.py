from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class Subject(str, enum.Enum):
    SCIENCE = "science"
    MATHEMATICS = "mathematics"

class QuestionPaper(Base):
    __tablename__ = "question_papers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    subject = Column(Enum(Subject), nullable=False)
    class_level = Column(Integer, default=12)
    total_marks = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    instructions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    pdf_path = Column(String, nullable=True)  # Path to uploaded PDF/image
    
    questions = relationship("Question", back_populates="paper", cascade="all, delete-orphan")
    submissions = relationship("AnswerSubmission", back_populates="paper")

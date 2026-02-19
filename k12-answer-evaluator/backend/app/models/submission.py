from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    EVALUATED = "evaluated"
    FAILED = "failed"

class AnswerSubmission(Base):
    __tablename__ = "answer_submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("question_papers.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    image_path = Column(String, nullable=False)
    extracted_text = Column(Text)
    diagram_metadata = Column(JSON, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING)
    
    paper = relationship("QuestionPaper", back_populates="submissions")
    evaluations = relationship("Evaluation", back_populates="submission", cascade="all, delete-orphan")

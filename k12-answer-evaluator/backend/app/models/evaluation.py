from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("answer_submissions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    student_answer = Column(Text)
    marks_obtained = Column(Float, nullable=False)
    max_marks = Column(Integer, nullable=False)
    feedback = Column(Text)
    rag_context = Column(Text)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    
    submission = relationship("AnswerSubmission", back_populates="evaluations")
    question = relationship("Question", back_populates="evaluations")

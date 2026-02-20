from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class Subject(str, enum.Enum):
    # Sciences
    SCIENCE = "science"            # General Science (K-8)
    PHYSICS = "physics"            # Class 9-12
    CHEMISTRY = "chemistry"        # Class 9-12
    BIOLOGY = "biology"            # Class 9-12
    ENVIRONMENTAL_SCIENCE = "environmental_science"  # K-5
    # Mathematics
    MATHEMATICS = "mathematics"
    # Languages
    ENGLISH = "english"
    HINDI = "hindi"
    # Social Studies
    SOCIAL_SCIENCE = "social_science"   # Combined (K-8)
    HISTORY = "history"                  # Class 9-12
    GEOGRAPHY = "geography"             # Class 9-12
    CIVICS = "civics"                   # Class 9-12
    # Commerce / Humanities
    ECONOMICS = "economics"             # Class 11-12
    ACCOUNTANCY = "accountancy"         # Class 11-12
    BUSINESS_STUDIES = "business_studies"  # Class 11-12
    # General
    GENERAL = "general"

class ClassLevel(str, enum.Enum):
    KG    = "kg"     # Kindergarten
    G1    = "1"
    G2    = "2"
    G3    = "3"
    G4    = "4"
    G5    = "5"
    G6    = "6"
    G7    = "7"
    G8    = "8"
    G9    = "9"
    G10   = "10"
    G11   = "11"
    G12   = "12"


class QuestionPaper(Base):
    __tablename__ = "question_papers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    subject = Column(Enum(Subject, values_callable=lambda x: [e.value for e in x]), nullable=False)
    class_level = Column(String(10), default="12")
    total_marks = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    instructions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    pdf_path = Column(String, nullable=True)
    # Exam mode
    is_exam_mode    = Column(Boolean, default=False, nullable=False)
    exam_start_time = Column(DateTime, nullable=True)
    exam_end_time   = Column(DateTime, nullable=True)
    
    questions = relationship("Question", back_populates="paper", cascade="all, delete-orphan")
    submissions = relationship("AnswerSubmission", back_populates="paper")
    assignments = relationship("StudentAssignment", back_populates="paper", cascade="all, delete-orphan")

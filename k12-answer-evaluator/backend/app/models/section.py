from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class Section(Base):
    """A class/group that a teacher manages."""
    __tablename__ = "sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)       # e.g. "Grade 10 - Section A"
    class_level = Column(String(10), nullable=True)  # e.g. "10"
    subject = Column(String(50), nullable=True)      # optional subject filter
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("SectionMember", back_populates="section", cascade="all, delete-orphan")

class SectionMember(Base):
    """A student enrolled in a section."""
    __tablename__ = "section_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    section = relationship("Section", back_populates="members")
    student = relationship("User")

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class SubjectEnum(str, Enum):
    """Supported subjects"""
    SCIENCE = "Science"
    MATHEMATICS = "Mathematics"

class ClassLevelEnum(str, Enum):
    """Supported class levels"""
    CLASS_12 = "12"

class UploadResponse(BaseModel):
    """Response after file upload"""
    success: bool
    file_id: str
    file_name: str
    file_size: int
    subject: str
    class_level: str
    message: str
    uploaded_at: str

class EvaluationRequest(BaseModel):
    """Request to evaluate an answer sheet"""
    file_id: str = Field(..., description="Uploaded file identifier")
    subject: SubjectEnum = Field(..., description="Subject of the answer sheet")
    class_level: ClassLevelEnum = Field(default=ClassLevelEnum.CLASS_12, description="Class level")
    
    @validator('file_id')
    def validate_file_id(cls, v):
        if not v or len(v) < 10:
            raise ValueError("Invalid file_id")
        return v

class ScoreBreakdown(BaseModel):
    """Score breakdown by category"""
    correctness: int
    completeness: int
    understanding: int

class ErrorDetail(BaseModel):
    """Detailed error information"""
    what: str = Field(..., description="What is wrong")
    why: str = Field(..., description="Why it is wrong")
    impact: str = Field(..., description="Impact on understanding")

class ImprovementGuidance(BaseModel):
    """Improvement guidance for student"""
    suggestion: str = Field(..., description="Specific suggestion")
    resource: str = Field(..., description="Textbook reference")
    practice: str = Field(..., description="Practice recommendation")

class QuestionEvaluation(BaseModel):
    """Evaluation result for a single question"""
    question_number: int
    question_text: str
    student_answer: str
    score: int
    max_score: int
    score_breakdown: ScoreBreakdown
    correct_points: List[str]
    errors: List[ErrorDetail]
    missing_concepts: List[str]
    correct_answer_should_include: List[str]
    improvement_guidance: List[ImprovementGuidance]
    overall_feedback: str

class PracticeRecommendation(BaseModel):
    """Practice recommendation"""
    topic: str
    action: str
    resource: str

class OverallSummary(BaseModel):
    """Overall performance summary"""
    performance_level: str
    overall_message: str
    strengths: List[str]
    areas_for_improvement: List[str]
    recommended_practice: List[PracticeRecommendation]

class EvaluationResponse(BaseModel):
    """Complete evaluation response"""
    evaluation_id: str
    file_id: str
    subject: str
    class_level: str
    overall_score: int
    max_possible_score: int
    percentage: float
    total_questions: int
    evaluations: List[QuestionEvaluation]
    summary: OverallSummary
    evaluated_at: str
    processing_time: float

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: str

class EvaluationStatus(str, Enum):
    """Evaluation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class StatusResponse(BaseModel):
    """Status check response"""
    evaluation_id: str
    status: EvaluationStatus
    progress: Optional[int] = None  # 0-100
    message: Optional[str] = None
    result: Optional[EvaluationResponse] = None

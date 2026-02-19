from sqlalchemy.orm import Session
from app.models.evaluation import Evaluation
from typing import List
from uuid import UUID

def create_evaluation(
    db: Session,
    submission_id: UUID,
    question_id: UUID,
    student_answer: str,
    marks_obtained: float,
    max_marks: int,
    feedback: str,
    rag_context: str = None
) -> Evaluation:
    db_eval = Evaluation(
        submission_id=submission_id,
        question_id=question_id,
        student_answer=student_answer,
        marks_obtained=marks_obtained,
        max_marks=max_marks,
        feedback=feedback,
        rag_context=rag_context
    )
    db.add(db_eval)
    db.commit()
    db.refresh(db_eval)
    return db_eval

def get_submission_evaluations(db: Session, submission_id: UUID) -> List[Evaluation]:
    return db.query(Evaluation).filter(Evaluation.submission_id == submission_id).all()

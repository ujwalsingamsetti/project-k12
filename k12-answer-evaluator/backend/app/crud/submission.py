from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.submission import AnswerSubmission, SubmissionStatus
from app.models.evaluation import Evaluation
from app.models.user import User
from app.models.question import Question
from typing import List
from uuid import UUID

def create_submission(db: Session, paper_id: UUID, student_id: UUID, image_path: str, uploaded_files: list = None) -> AnswerSubmission:
    db_submission = AnswerSubmission(
        paper_id=paper_id,
        student_id=student_id,
        image_path=image_path,
        uploaded_files=uploaded_files,
        status=SubmissionStatus.PENDING
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

def get_submission(db: Session, submission_id: UUID) -> AnswerSubmission:
    return db.query(AnswerSubmission).filter(AnswerSubmission.id == submission_id).first()

def update_submission_text(db: Session, submission_id: UUID, text: str):
    db.query(AnswerSubmission).filter(AnswerSubmission.id == submission_id).update(
        {"extracted_text": text}
    )
    db.commit()

def update_submission_status(db: Session, submission_id: UUID, status: SubmissionStatus):
    db.query(AnswerSubmission).filter(AnswerSubmission.id == submission_id).update(
        {"status": status}
    )
    db.commit()

def get_paper_submissions(db: Session, paper_id: UUID) -> List:
    submissions = db.query(
        AnswerSubmission,
        User.full_name,
        User.email
    ).join(User, AnswerSubmission.student_id == User.id).filter(
        AnswerSubmission.paper_id == paper_id
    ).all()
    
    result = []
    for submission, student_name, student_email in submissions:
        total_marks = db.query(func.sum(Evaluation.marks_obtained)).filter(
            Evaluation.submission_id == submission.id
        ).scalar() or 0
        
        max_marks = db.query(func.sum(Evaluation.max_marks)).filter(
            Evaluation.submission_id == submission.id
        ).scalar() or 0

        evals = db.query(Evaluation).filter(
            Evaluation.submission_id == submission.id
        ).options(joinedload(Evaluation.question)).all()

        evaluations_data = [{
            "question_id": str(e.id),      # evaluation row id (for override endpoint)
            "question_number": e.question.question_number if e.question else "?",
            "student_answer": e.student_answer,
            "marks_obtained": e.marks_obtained,
            "max_marks": e.max_marks,
            "teacher_override": e.teacher_override,
            "override_marks": e.override_marks,
            "override_feedback": e.override_feedback,
        } for e in evals]

        result.append({
            "id": submission.id,
            "student_name": student_name,
            "student_email": student_email,
            "submitted_at": submission.submitted_at,
            "status": submission.status,
            "total_marks": total_marks,
            "max_marks": max_marks,
            "evaluations": evaluations_data,
        })
    
    return result

def _count_submission_pages(image_path: str) -> int:
    """Count uploaded pages for a submission by scanning its folder."""
    if not image_path:
        return 0
    import os
    folder = os.path.dirname(image_path)
    uuid_prefix = os.path.basename(image_path).split("_page")[0]
    import re
    files = os.listdir(folder) if os.path.exists(folder) else []
    # Match uuid_prefix + _page + digits + extension (no other characters in between)
    pattern = re.compile(rf"^{re.escape(uuid_prefix)}_page\d+\.[^.]+$")
    pages = [f for f in files if pattern.match(f)]
    return len(pages) if pages else (1 if os.path.exists(image_path) else 0)

def get_submission_details(db: Session, submission_id: UUID, student_id: UUID) -> dict:
    submission = db.query(AnswerSubmission).filter(
        AnswerSubmission.id == submission_id,
        AnswerSubmission.student_id == student_id
    ).options(joinedload(AnswerSubmission.evaluations).joinedload(Evaluation.question)).first()
    
    if not submission:
        return None
        
    evaluations_data = []
    for evaluation in submission.evaluations:
        evaluations_data.append({
            "question_id": evaluation.question_id,
            "question_number": evaluation.question.question_number if evaluation.question else "?",
            "student_answer": evaluation.student_answer,
            "marks_obtained": evaluation.marks_obtained,
            "max_marks": evaluation.max_marks,
            "feedback": evaluation.feedback
        })
    
    total_marks = sum(e.marks_obtained for e in submission.evaluations)
    max_marks = sum(e.max_marks for e in submission.evaluations)
    
    return {
        "id": submission.id,
        "paper_id": submission.paper_id,
        "student_id": submission.student_id,
        "image_path": submission.image_path,
        "page_count": len(submission.uploaded_files) if submission.uploaded_files else _count_submission_pages(submission.image_path),
        "uploaded_files": submission.uploaded_files,
        "extracted_text": submission.extracted_text,
        "submitted_at": submission.submitted_at,
        "status": submission.status.value,
        "total_marks": total_marks,
        "max_marks": max_marks,
        "evaluations": evaluations_data
    }

def get_student_submissions(db: Session, student_id: UUID) -> List:

    submissions = db.query(AnswerSubmission).filter(
        AnswerSubmission.student_id == student_id
    ).options(joinedload(AnswerSubmission.evaluations).joinedload(Evaluation.question)).all()
    
    result = []
    for submission in submissions:
        evaluations_data = []
        for evaluation in submission.evaluations:
            evaluations_data.append({
                "question_id": evaluation.question_id,
                "question_number": evaluation.question.question_number,
                "student_answer": evaluation.student_answer,
                "marks_obtained": evaluation.marks_obtained,
                "max_marks": evaluation.max_marks,
                "feedback": evaluation.feedback
            })
        
        total_marks = sum(e.marks_obtained for e in submission.evaluations)
        max_marks = sum(e.max_marks for e in submission.evaluations)
        
        result.append({
            "id": submission.id,
            "paper_id": submission.paper_id,
            "student_id": submission.student_id,
            "image_path": submission.image_path,
            "page_count": len(submission.uploaded_files) if submission.uploaded_files else _count_submission_pages(submission.image_path),
            "uploaded_files": submission.uploaded_files,
            "extracted_text": submission.extracted_text,
            "submitted_at": submission.submitted_at,
            "status": submission.status.value,
            "total_marks": total_marks,
            "max_marks": max_marks,
            "evaluations": evaluations_data
        })
    
    return result

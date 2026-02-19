from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.models.submission import AnswerSubmission
from app.schemas.question_paper import QuestionPaperCreate
from typing import List
from uuid import UUID

def create_question_paper(db: Session, paper: QuestionPaperCreate, teacher_id: UUID) -> QuestionPaper:
    db_paper = QuestionPaper(
        teacher_id=teacher_id,
        title=paper.title,
        subject=paper.subject,
        class_level=paper.class_level,
        total_marks=paper.total_marks,
        duration_minutes=paper.duration_minutes,
        instructions=paper.instructions,
        due_date=paper.due_date
    )
    db.add(db_paper)
    db.flush()
    
    for q in paper.questions:
        db_question = Question(
            paper_id=db_paper.id,
            question_number=q.question_number,
            question_text=q.question_text,
            question_type=q.question_type,
            marks=q.marks,
            expected_keywords=q.expected_keywords,
            options=q.options,
            correct_answer=q.correct_answer
        )
        db.add(db_question)
    
    db.commit()
    db.refresh(db_paper)
    return db_paper

def get_teacher_papers(db: Session, teacher_id: UUID) -> List[QuestionPaper]:
    return db.query(QuestionPaper).filter(QuestionPaper.teacher_id == teacher_id).all()

def get_all_papers(db: Session) -> List[QuestionPaper]:
    return db.query(QuestionPaper).all()

def get_paper(db: Session, paper_id: UUID) -> QuestionPaper:
    return db.query(QuestionPaper).filter(QuestionPaper.id == paper_id).first()

def get_paper_with_stats(db: Session, paper_id: UUID):
    paper = db.query(QuestionPaper).filter(QuestionPaper.id == paper_id).first()
    if paper:
        questions_count = len(paper.questions)
        submissions_count = db.query(func.count(AnswerSubmission.id)).filter(
            AnswerSubmission.paper_id == paper_id
        ).scalar()
        return {
            **paper.__dict__,
            "questions_count": questions_count,
            "submissions_count": submissions_count
        }
    return None

def delete_paper(db: Session, paper_id: UUID):
    paper = db.query(QuestionPaper).filter(QuestionPaper.id == paper_id).first()
    if paper:
        db.delete(paper)
        db.commit()
    return paper

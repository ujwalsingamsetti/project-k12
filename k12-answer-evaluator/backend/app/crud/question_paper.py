from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.question_paper import QuestionPaper
from app.models.question import Question
from app.models.submission import AnswerSubmission
from app.models.evaluation import Evaluation
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
        # Determine question_type — DB uses QuestionType enum (short/long/mcq)
        # Map new subtypes to the closest enum value
        raw_type = (q.question_type or "short").lower()
        if raw_type == "mcq":
            db_q_type = "mcq"
        elif raw_type in ("assertion_reason",):
            db_q_type = "mcq"  # stored as mcq in DB enum
        elif raw_type in ("long", "case_study"):
            db_q_type = "long"
        else:
            db_q_type = "short"

        db_question = Question(
            paper_id=db_paper.id,
            question_number=q.question_number,
            question_text=q.question_text,
            question_type=db_q_type,
            marks=q.marks,
            expected_keywords=q.expected_keywords,
            options=q.options,
            correct_answer=q.correct_answer,
            section=q.section,
            has_or_option=q.has_or_option or False,
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
        # Get all submissions for this paper
        submissions = db.query(AnswerSubmission).filter(AnswerSubmission.paper_id == paper_id).all()
        
        # Delete evaluations for each submission
        for submission in submissions:
            db.query(Evaluation).filter(Evaluation.submission_id == submission.id).delete()
        
        # Delete submissions
        db.query(AnswerSubmission).filter(AnswerSubmission.paper_id == paper_id).delete()
        
        # Delete questions
        db.query(Question).filter(Question.paper_id == paper_id).delete()
        
        # Delete paper
        db.delete(paper)
        db.commit()
    return paper

def update_question_paper(db: Session, paper_id: UUID, paper_update: QuestionPaperCreate, teacher_id: UUID) -> QuestionPaper:
    db_paper = db.query(QuestionPaper).filter(QuestionPaper.id == paper_id, QuestionPaper.teacher_id == teacher_id).first()
    if not db_paper:
        return None
        
    db_paper.title = paper_update.title
    db_paper.subject = paper_update.subject
    db_paper.class_level = paper_update.class_level
    db_paper.total_marks = paper_update.total_marks
    db_paper.duration_minutes = paper_update.duration_minutes
    db_paper.instructions = paper_update.instructions
    db_paper.due_date = paper_update.due_date
    
    existing_questions = {q.question_number: q for q in db.query(Question).filter(Question.paper_id == paper_id).all()}
    updated_q_nums = set()
    
    for q in paper_update.questions:
        updated_q_nums.add(q.question_number)
        raw_type = (q.question_type or "short").lower()
        if raw_type == "mcq" or raw_type == "assertion_reason":
            db_q_type = "mcq"
        elif raw_type in ("long", "case_study"):
            db_q_type = "long"
        else:
            db_q_type = "short"

        if q.question_number in existing_questions:
            db_question = existing_questions[q.question_number]
            db_question.question_text = q.question_text
            db_question.question_type = db_q_type
            db_question.marks = q.marks
            db_question.expected_keywords = q.expected_keywords
            db_question.options = q.options
            db_question.correct_answer = q.correct_answer
            db_question.section = q.section
            db_question.has_or_option = q.has_or_option or False
        else:
            db_question = Question(
                paper_id=db_paper.id,
                question_number=q.question_number,
                question_text=q.question_text,
                question_type=db_q_type,
                marks=q.marks,
                expected_keywords=q.expected_keywords,
                options=q.options,
                correct_answer=q.correct_answer,
                section=q.section,
                has_or_option=q.has_or_option or False,
            )
            db.add(db_question)

    for q_num, existing_q in existing_questions.items():
        if q_num not in updated_q_nums:
            db.query(Evaluation).filter(Evaluation.question_id == existing_q.id).delete(synchronize_session=False)
            db.delete(existing_q)
        
    db.commit()
    db.refresh(db_paper)
    return db_paper

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, BackgroundTasks, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
import os
import uuid
from uuid import UUID
import logging
import traceback
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.textbook import Textbook
from app.models.evaluation import Evaluation
from app.models.assignment import StudentAssignment
from app.schemas.question_paper import QuestionPaperCreate, QuestionPaper, QuestionPaperList
from app.schemas.submission import SubmissionList
from app.crud import question_paper as crud_paper
from app.crud import submission as crud_submission
from app.services.textbook_ingestion_service import TextbookIngestionService
from app.services.question_paper_ocr_service import QuestionPaperOCRService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teacher", tags=["teacher"])

def get_teacher(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

@router.post("/extract-questions")
async def extract_questions_from_image(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    """Extract questions from uploaded images/PDFs using OCR without creating a paper record"""
    
    # Save files temporarily
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    file_paths = []
    
    try:
        for file in files:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in ['.png', '.jpg', '.jpeg', '.pdf']:
                raise HTTPException(status_code=400, detail="Only image (PNG, JPG) and PDF files allowed")
            
            file_id = str(uuid.uuid4())
            file_path = os.path.join(temp_dir, f"{file_id}{file_ext}")
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            file_paths.append(file_path)
        
        # Extract questions using mixed file processor
        ocr_service = QuestionPaperOCRService()
        questions = ocr_service.extract_questions_from_mixed_files(file_paths)
        
        if not questions:
            raise HTTPException(status_code=400, detail="No questions found in uploaded file(s)")
        
        logger.info(f"Extracted {len(questions)} questions from question paper")
        
        return {
            "questions": questions,
            "questions_count": len(questions),
            "diagrams_detected": sum(1 for q in questions if q.get('has_diagram', False)),
            "sections": list(set(q.get('section') for q in questions if q.get('section')))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Failed to extract questions: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")
    
    finally:
        # Clean up temp files
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass


@router.post("/papers", response_model=QuestionPaper)
def create_paper(
    paper: QuestionPaperCreate,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    return crud_paper.create_question_paper(db, paper, teacher.id)

@router.put("/papers/{paper_id}", response_model=QuestionPaper)
def update_paper(
    paper_id: UUID,
    paper: QuestionPaperCreate,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    updated_paper = crud_paper.update_question_paper(db, paper_id, paper, teacher.id)
    if not updated_paper:
        raise HTTPException(status_code=404, detail="Paper not found or you don't have permission to edit it")
    return updated_paper

@router.get("/papers", response_model=List[QuestionPaper])
def get_my_papers(
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    return crud_paper.get_teacher_papers(db, teacher.id)

@router.get("/papers/{paper_id}", response_model=QuestionPaper)
def get_paper(
    paper_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    paper = crud_paper.get_paper(db, paper_id)
    if not paper or paper.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@router.get("/papers/{paper_id}/submissions", response_model=List[SubmissionList])
def get_paper_submissions(
    paper_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    paper = crud_paper.get_paper(db, paper_id)
    if not paper or paper.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    submissions = crud_submission.get_paper_submissions(db, paper_id)
    # Only show evaluated submissions to the teacher in history
    # 'submissions' is a list of dicts, so use s["status"]
    return [s for s in submissions if s.get("status") == "evaluated"]

@router.delete("/papers/{paper_id}")
def delete_paper(
    paper_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    try:
        paper = crud_paper.get_paper(db, paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        if paper.teacher_id != teacher.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this paper")
        
        crud_paper.delete_paper(db, paper_id)
        return {"message": "Paper deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/textbooks")
async def upload_textbook(
    file: UploadFile = File(...),
    title: str = Form(None),
    subject: str = Form(None),
    class_level: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Save file
    textbook_dir = os.path.join(
        settings.UPLOAD_DIR, 
        "textbooks", 
        str(class_level or "general").replace("/", "_"), 
        str(subject or "general").replace("/", "_")
    )
    os.makedirs(textbook_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(textbook_dir, f"{file_id}.pdf")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create DB record
    textbook = Textbook(
        teacher_id=teacher.id,
        title=title or file.filename,
        subject=subject or "general",
        class_level=class_level or None,
        file_path=file_path
    )
    db.add(textbook)
    db.commit()
    db.refresh(textbook)
    
    # Ingest in background (pass class_level so Qdrant payload includes it)
    background_tasks.add_task(
        ingest_textbook_task,
        str(textbook.id), file_path,
        subject or "general",
        class_level or "",
        str(teacher.id), db
    )
    
    return {"id": str(textbook.id), "title": textbook.title, "message": "Textbook uploaded, processing..."}

def ingest_textbook_task(textbook_id: str, file_path: str, subject: str, class_level: str, teacher_id: str, db: Session):
    try:
        service = TextbookIngestionService()
        chunk_count = service.ingest_textbook(file_path, subject, textbook_id, teacher_id, class_level=class_level)
        
        # Update chunk count
        textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
        if textbook:
            textbook.chunk_count = chunk_count
            db.commit()
    except Exception as e:
        print(f"Textbook ingestion failed: {e}")

@router.get("/textbooks")
def get_my_textbooks(
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    textbooks = db.query(Textbook).filter(Textbook.teacher_id == teacher.id).all()
    return [{
        "id": str(t.id), "title": t.title, "subject": t.subject,
        "class_level": t.class_level, "chunk_count": t.chunk_count, "uploaded_at": t.uploaded_at
    } for t in textbooks]

@router.delete("/textbooks/{textbook_id}")
def delete_textbook(
    textbook_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook or textbook.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Delete from vector DB
    service = TextbookIngestionService()
    service.delete_textbook_chunks(textbook_id)
    
    # Delete file
    if os.path.exists(textbook.file_path):
        os.remove(textbook.file_path)
    
    # Delete DB record
    db.delete(textbook)
    db.commit()
    
    return {"message": "Textbook deleted successfully"}

@router.post("/papers/from-image")
async def create_paper_from_image(
    files: List[UploadFile] = File(...),
    title: str = None,
    subject: str = None,
    duration_minutes: int = 180,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    """Create question paper from uploaded images/PDFs using OCR (supports mixed types)"""
    
    # Save files temporarily
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save files permanently for student viewing
    papers_dir = os.path.join(settings.UPLOAD_DIR, "question_papers")
    os.makedirs(papers_dir, exist_ok=True)
    
    file_paths = []
    saved_pdf_path = None
    
    try:
        for idx, file in enumerate(files):
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext not in ['.png', '.jpg', '.jpeg', '.pdf']:
                raise HTTPException(status_code=400, detail="Only image (PNG, JPG) and PDF files allowed")
            
            file_id = str(uuid.uuid4())
            file_path = os.path.join(temp_dir, f"{file_id}{file_ext}")
            
            content = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            file_paths.append(file_path)
            
            # Save first PDF for student viewing
            if file_ext == '.pdf' and not saved_pdf_path:
                permanent_path = os.path.join(papers_dir, f"{file_id}.pdf")
                with open(permanent_path, "wb") as f:
                    f.write(content)
                saved_pdf_path = permanent_path
        
        # Extract questions using mixed file processor
        ocr_service = QuestionPaperOCRService()
        questions = ocr_service.extract_questions_from_mixed_files(file_paths)
        
        if not questions:
            raise HTTPException(status_code=400, detail="No questions found in uploaded file(s)")
        
        logger.info(f"Extracted {len(questions)} questions from question paper")
        
        # Calculate total marks
        total_marks = sum(q['marks'] for q in questions)
        
        # Create paper data
        paper_data = QuestionPaperCreate(
            title=title or f"Paper from {files[0].filename}",
            subject=subject or "science",
            class_level="12",
            total_marks=total_marks,
            duration_minutes=duration_minutes,
            questions=questions
        )
        
        # Create paper
        paper = crud_paper.create_question_paper(db, paper_data, teacher.id)
        
        # Update with PDF path if available
        if saved_pdf_path:
            paper.pdf_path = saved_pdf_path
            db.commit()
        
        return {
            "id": str(paper.id),
            "title": paper.title,
            "questions_count": len(questions),
            "total_marks": total_marks,
            "diagrams_detected": sum(1 for q in questions if q.get('has_diagram', False)),
            "sections": list(set(q.get('section') for q in questions if q.get('section')))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Failed to process files: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        # Clean up temp files
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass


# ═══════════════════════════════════════════════════════════════
# FEATURE #3 – Teacher Manual Override / Re-grading
# ═══════════════════════════════════════════════════════════════

class OverrideRequest(BaseModel):
    marks: float
    comment: str = ""

@router.patch("/evaluations/{evaluation_id}/override")
def override_evaluation(
    evaluation_id: str,
    body: OverrideRequest,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    """Allow teacher to manually adjust an AI-assigned mark."""
    from app.models.submission import AnswerSubmission
    from app.models.question_paper import QuestionPaper

    eval_ = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not eval_:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Verify the teacher owns the paper
    sub = db.query(AnswerSubmission).filter(AnswerSubmission.id == eval_.submission_id).first()
    paper = db.query(QuestionPaper).filter(QuestionPaper.id == sub.paper_id).first()
    if not paper or paper.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if body.marks < 0 or body.marks > eval_.max_marks:
        raise HTTPException(status_code=400, detail=f"Marks must be between 0 and {eval_.max_marks}")

    eval_.override_marks = body.marks
    eval_.override_feedback = body.comment
    eval_.teacher_override = True
    eval_.override_at = datetime.utcnow()
    # Update the displayed marks_obtained so responses reflect the override
    eval_.marks_obtained = body.marks
    db.commit()
    return {"message": "Override saved", "evaluation_id": evaluation_id, "new_marks": body.marks}


# ═══════════════════════════════════════════════════════════════
# FEATURE #4 – Paper Assignment to Students
# ═══════════════════════════════════════════════════════════════

class AssignRequest(BaseModel):
    student_ids: List[str]
    due_date: Optional[datetime] = None

@router.post("/papers/{paper_id}/assign")
def assign_paper(
    paper_id: str,
    body: AssignRequest,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    """Assign a paper to one or more students."""
    paper = crud_paper.get_paper(db, paper_id)
    if not paper or paper.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Paper not found")

    assigned = []
    for sid in body.student_ids:
        # Skip if already assigned
        existing = db.query(StudentAssignment).filter(
            StudentAssignment.paper_id == paper.id,
            StudentAssignment.student_id == sid
        ).first()
        if existing:
            existing.is_active = True
            existing.due_date = body.due_date
        else:
            db.add(StudentAssignment(
                paper_id=paper.id,
                student_id=sid,
                due_date=body.due_date
            ))
        assigned.append(sid)

    db.commit()
    return {"message": f"Assigned to {len(assigned)} student(s)", "assigned": assigned}

@router.get("/papers/{paper_id}/assignments")
def get_paper_assignments(
    paper_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    """List all student assignments for a paper."""
    paper = crud_paper.get_paper(db, paper_id)
    if not paper or paper.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Paper not found")

    rows = db.query(StudentAssignment, User).join(
        User, StudentAssignment.student_id == User.id
    ).filter(StudentAssignment.paper_id == paper.id).all()

    return [{
        "assignment_id": str(a.id),
        "student_id": str(a.student_id),
        "student_name": u.full_name,
        "student_email": u.email,
        "due_date": a.due_date,
        "assigned_at": a.assigned_at,
        "is_active": a.is_active,
    } for a, u in rows]

@router.delete("/papers/{paper_id}/assignments/{student_id}")
def remove_assignment(
    paper_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    paper = crud_paper.get_paper(db, paper_id)
    if not paper or paper.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Paper not found")

    a = db.query(StudentAssignment).filter(
        StudentAssignment.paper_id == paper.id,
        StudentAssignment.student_id == student_id
    ).first()
    if a:
        db.delete(a)
        db.commit()
    return {"message": "Assignment removed"}

@router.get("/students")
def list_students(
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    """Return all registered students (for assignment UI)."""
    students = db.query(User).filter(User.role == UserRole.STUDENT).all()
    return [{"id": str(s.id), "name": s.full_name, "email": s.email} for s in students]


# ═══════════════════════════════════════════════════════════════
# FEATURE #1 – Analytics Dashboard
# ═══════════════════════════════════════════════════════════════

@router.get("/papers/{paper_id}/analytics")
def get_paper_analytics(
    paper_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    """Return class-wide analytics for a paper."""
    from app.models.submission import AnswerSubmission
    from app.models.question import Question

    paper = crud_paper.get_paper(db, paper_id)
    if not paper or paper.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Paper not found")

    # All evaluated submissions
    submissions = db.query(AnswerSubmission).filter(
        AnswerSubmission.paper_id == paper.id,
        AnswerSubmission.status == "evaluated"
    ).all()

    total_subs = len(submissions)
    if total_subs == 0:
        return {
            "paper_title": paper.title,
            "total_submissions": db.query(AnswerSubmission).filter(AnswerSubmission.paper_id == paper.id).count(),
            "evaluated": 0,
            "class_average": 0, "highest_score": 0, "lowest_score": 0,
            "max_marks": paper.total_marks or 100,
            "score_distribution": [], 
            "grade_distribution": [],
            "student_scores": [],
            "per_question": [{"question_number": q.question_number, "question_text": q.question_text[:80], "max_marks": q.marks, "avg_marks": 0, "attempts": 0} for q in db.query(Question).filter(Question.paper_id == paper.id).all()]
        }

    # Per-submission totals
    sub_scores = []
    for sub in submissions:
        total = db.query(func.sum(Evaluation.marks_obtained)).filter(
            Evaluation.submission_id == sub.id
        ).scalar() or 0
        sub_scores.append(float(total))

    max_marks = paper.total_marks or 1

    # Score distribution buckets (0-24%, 25-49%, 50-74%, 75-100%)
    def bucket(score):
        pct = (score / max_marks) * 100
        if pct < 25: return "0–24%"
        if pct < 50: return "25–49%"
        if pct < 75: return "50–74%"
        return "75–100%"

    dist = {"0–24%": 0, "25–49%": 0, "50–74%": 0, "75–100%": 0}
    for s in sub_scores:
        dist[bucket(s)] += 1

    score_distribution = [{"range": k, "count": v} for k, v in dist.items()]

    # Per-question stats
    questions = db.query(Question).filter(Question.paper_id == paper.id).order_by(Question.question_number).all()
    per_question = []
    for q in questions:
        evals = db.query(Evaluation).filter(Evaluation.question_id == q.id).all()
        if not evals:
            per_question.append({
                "question_number": q.question_number,
                "question_text": q.question_text[:80],
                "max_marks": q.marks,
                "avg_marks": 0, "attempts": 0
            })
        else:
            avg = sum(e.marks_obtained for e in evals) / len(evals)
            per_question.append({
                "question_number": q.question_number,
                "question_text": q.question_text[:80],
                "max_marks": q.marks,
                "avg_marks": round(avg, 2),
                "attempts": len(evals),
                "full_marks_count": sum(1 for e in evals if e.marks_obtained >= q.marks),
                "zero_marks_count": sum(1 for e in evals if e.marks_obtained == 0),
            })

    # ─── Grade distribution ───────────────────────────────────────────────────
    from app.models.user import User as UserModel
    def grade_label(pct):
        if pct >= 90: return "A+"
        if pct >= 75: return "A"
        if pct >= 60: return "B"
        if pct >= 45: return "C"
        if pct >= 33: return "D"
        return "F"

    grade_counts = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    student_scores = []
    for sub, score in zip(submissions, sub_scores):
        if float(max_marks) > 0:
            pct = (float(score) / float(max_marks)) * 100
        else:
            pct = 0
        gl = grade_label(pct)
        grade_counts[gl] += 1
        student = db.query(UserModel).filter(UserModel.id == sub.student_id).first()
        student_scores.append({
            "name": student.full_name if student else "Unknown",
            "score": score,
            "max_marks": max_marks,
            "percentage": round(pct, 1),
            "grade": gl,
        })

    grade_distribution = [{"grade": k, "count": v} for k, v in grade_counts.items() if v > 0]

    return {
        "paper_title": paper.title,
        "total_submissions": db.query(AnswerSubmission).filter(AnswerSubmission.paper_id == paper.id).count(),
        "evaluated": total_subs,
        "class_average": round(sum(sub_scores) / total_subs, 2),
        "highest_score": max(sub_scores),
        "lowest_score": min(sub_scores),
        "max_marks": max_marks,
        "score_distribution": score_distribution,
        "grade_distribution": grade_distribution,
        "student_scores": sorted(student_scores, key=lambda s: -s["score"]),
        "per_question": per_question,
    }


# ═══════════════════════════════════════════════════════════════
# PHASE 2 – FEATURE #5: Class Sections
# ═══════════════════════════════════════════════════════════════

from app.models.section import Section, SectionMember

class SectionCreate(BaseModel):
    name: str
    class_level: Optional[str] = None
    subject: Optional[str] = None

class SectionMembersUpdate(BaseModel):
    student_ids: List[str]

@router.post("/sections")
def create_section(body: SectionCreate, db: Session = Depends(get_db), teacher: User = Depends(get_teacher)):
    section = Section(teacher_id=teacher.id, name=body.name, class_level=body.class_level, subject=body.subject)
    db.add(section)
    db.commit()
    db.refresh(section)
    return {"id": str(section.id), "name": section.name, "class_level": section.class_level, "subject": section.subject, "created_at": section.created_at, "member_count": 0}

@router.get("/sections")
def list_sections(db: Session = Depends(get_db), teacher: User = Depends(get_teacher)):
    sections = db.query(Section).filter(Section.teacher_id == teacher.id).all()
    result = []
    for s in sections:
        result.append({
            "id": str(s.id), "name": s.name,
            "class_level": s.class_level, "subject": s.subject,
            "created_at": s.created_at,
            "member_count": db.query(SectionMember).filter(SectionMember.section_id == s.id).count()
        })
    return result

@router.get("/sections/{section_id}/members")
def get_section_members(section_id: str, db: Session = Depends(get_db), teacher: User = Depends(get_teacher)):
    section = db.query(Section).filter(Section.id == section_id, Section.teacher_id == teacher.id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    rows = db.query(SectionMember, User).join(User, SectionMember.student_id == User.id).filter(SectionMember.section_id == section.id).all()
    return [{"student_id": str(u.id), "name": u.full_name, "email": u.email, "joined_at": m.joined_at} for m, u in rows]

@router.put("/sections/{section_id}/members")
def update_section_members(section_id: str, body: SectionMembersUpdate, db: Session = Depends(get_db), teacher: User = Depends(get_teacher)):
    """Replace the member list of a section."""
    section = db.query(Section).filter(Section.id == section_id, Section.teacher_id == teacher.id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    db.query(SectionMember).filter(SectionMember.section_id == section.id).delete()
    for sid in body.student_ids:
        db.add(SectionMember(section_id=section.id, student_id=sid))
    db.commit()
    return {"message": f"Section updated with {len(body.student_ids)} members"}

@router.delete("/sections/{section_id}")
def delete_section(section_id: str, db: Session = Depends(get_db), teacher: User = Depends(get_teacher)):
    section = db.query(Section).filter(Section.id == section_id, Section.teacher_id == teacher.id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    db.delete(section)
    db.commit()
    return {"message": "Section deleted"}

@router.post("/sections/{section_id}/assign-paper/{paper_id}")
def assign_paper_to_section(section_id: str, paper_id: str, due_date: Optional[datetime] = None,
                            db: Session = Depends(get_db), teacher: User = Depends(get_teacher)):
    """Assign a paper to every member of a section at once."""
    section = db.query(Section).filter(Section.id == section_id, Section.teacher_id == teacher.id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    paper = crud_paper.get_paper(db, paper_id)
    if not paper or paper.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Paper not found")

    members = db.query(SectionMember).filter(SectionMember.section_id == section.id).all()
    assigned = 0
    for m in members:
        existing = db.query(StudentAssignment).filter(
            StudentAssignment.paper_id == paper.id,
            StudentAssignment.student_id == m.student_id
        ).first()
        if existing:
            existing.is_active = True
            existing.due_date = due_date
        else:
            db.add(StudentAssignment(paper_id=paper.id, student_id=m.student_id, due_date=due_date))
        assigned += 1

    db.commit()
    return {"message": f"Assigned to {assigned} students in section '{section.name}'"}

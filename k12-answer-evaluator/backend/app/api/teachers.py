from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import logging
import traceback
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.textbook import Textbook
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

@router.post("/papers", response_model=QuestionPaper)
def create_paper(
    paper: QuestionPaperCreate,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    return crud_paper.create_question_paper(db, paper, teacher.id)

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
    
    return crud_submission.get_paper_submissions(db, paper_id)

@router.delete("/papers/{paper_id}")
def delete_paper(
    paper_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    paper = crud_paper.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if paper.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this paper")
    
    crud_paper.delete_paper(db, paper_id)
    return {"message": "Paper deleted successfully"}

@router.post("/textbooks")
async def upload_textbook(
    file: UploadFile = File(...),
    title: str = None,
    subject: str = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    teacher: User = Depends(get_teacher)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Save file
    textbook_dir = os.path.join(settings.UPLOAD_DIR, "textbooks")
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
        file_path=file_path
    )
    db.add(textbook)
    db.commit()
    db.refresh(textbook)
    
    # Ingest in background
    background_tasks.add_task(ingest_textbook_task, str(textbook.id), file_path, subject or "general", str(teacher.id), db)
    
    return {"id": str(textbook.id), "title": textbook.title, "message": "Textbook uploaded, processing..."}

def ingest_textbook_task(textbook_id: str, file_path: str, subject: str, teacher_id: str, db: Session):
    try:
        service = TextbookIngestionService()
        chunk_count = service.ingest_textbook(file_path, subject, textbook_id, teacher_id)
        
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
    return [{"id": str(t.id), "title": t.title, "subject": t.subject, "chunk_count": t.chunk_count, "uploaded_at": t.uploaded_at} for t in textbooks]

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
        
        # Calculate total marks
        total_marks = sum(q['marks'] for q in questions)
        
        # Create paper data
        paper_data = QuestionPaperCreate(
            title=title or f"Paper from {files[0].filename}",
            subject=subject or "science",
            class_level=12,
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

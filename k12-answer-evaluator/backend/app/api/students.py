from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.submission import SubmissionStatus
from app.schemas.question_paper import QuestionPaper
from app.schemas.submission import Submission
from app.schemas.user import UserResponse
from app.crud import question_paper as crud_paper
from app.crud import submission as crud_submission
from app.crud import evaluation as crud_evaluation
from app.crud import user as crud_user
from app.services.ocr_service import OCRService
from app.services.answer_parser import AnswerParser
from app.services.rag_service import RAGService
from app.services.evaluation_service import EvaluationService
from app.services.mcq_evaluator import evaluate_mcq

router = APIRouter(prefix="/student", tags=["student"])

def get_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

@router.get("/teachers", response_model=List[UserResponse])
def get_all_teachers(
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    """Get all teachers for student to select from"""
    return crud_user.get_teachers(db)

@router.get("/papers", response_model=List[QuestionPaper])
def get_available_papers(
    teacher_id: str = None,
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    """Get papers, optionally filtered by teacher"""
    if teacher_id:
        return crud_paper.get_teacher_papers(db, teacher_id)
    return crud_paper.get_all_papers(db)

@router.get("/papers/{paper_id}", response_model=QuestionPaper)
def get_paper_details(
    paper_id: str,
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    paper = crud_paper.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@router.post("/submit/{paper_id}", response_model=Submission)
async def submit_answer(
    paper_id: str,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    paper = crud_paper.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Save uploaded files
    file_paths = []
    date_folder = datetime.now().strftime("%Y-%m-%d")
    upload_dir = os.path.join(settings.UPLOAD_DIR, date_folder)
    os.makedirs(upload_dir, exist_ok=True)
    
    for idx, file in enumerate(files):
        file_ext = os.path.splitext(file.filename)[1]
        file_id = str(uuid.uuid4())
        file_path = os.path.join(upload_dir, f"{file_id}_page{idx+1}{file_ext}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_paths.append(file_path)
    
    # Store all file paths as JSON
    import json
    all_paths_json = json.dumps(file_paths)
    
    # Create submission with first file path (for compatibility)
    submission = crud_submission.create_submission(db, paper_id, student.id, file_paths[0])
    
    # Process in background
    background_tasks.add_task(process_submission_multiple, submission.id, file_paths, paper_id, db)
    
    return submission

def process_submission_multiple(submission_id: str, image_paths: list, paper_id: str, db: Session):
    try:
        # OCR all images and combine text + diagrams
        ocr_service = OCRService()
        all_text = []
        all_diagrams = []
        
        for idx, image_path in enumerate(image_paths):
            extracted_text, diagram_metadata = ocr_service.extract_text_from_image(image_path)
            all_text.append(f"\n--- Page {idx+1} ---\n{extracted_text}")
            
            if diagram_metadata.get("has_diagrams"):
                all_diagrams.append({
                    "page": idx + 1,
                    "shapes": diagram_metadata.get("shapes_detected", []),
                    "diagram_paths": diagram_metadata.get("diagram_paths", []),
                    "question_diagrams": diagram_metadata.get("question_diagrams", {})
                })
        
        combined_text = "\n".join(all_text)
        crud_submission.update_submission_text(db, submission_id, combined_text)
        
        # Store diagram metadata
        if all_diagrams:
            import json
            from app.models.submission import AnswerSubmission
            submission = db.query(AnswerSubmission).filter(AnswerSubmission.id == submission_id).first()
            if submission:
                submission.diagram_metadata = {"diagrams": all_diagrams}
                db.commit()
        
        # Parse answers
        parser = AnswerParser()
        parsed_answers = parser.parse_answers(combined_text)
        
        # Get paper questions
        paper = crud_paper.get_paper(db, paper_id)
        
        # Evaluate each question
        rag_service = RAGService()
        eval_service = EvaluationService()
        
        for question in paper.questions:
            student_answer = parsed_answers.get(question.question_number, "")
            
            # Check if MCQ
            if hasattr(question.question_type, 'value'):
                q_type = question.question_type.value
            else:
                q_type = str(question.question_type)
            
            if q_type == "mcq":
                # Evaluate MCQ
                result = evaluate_mcq(question, student_answer)
                context_chunks = []
            else:
                # Evaluate descriptive question
                diagram_info = None
                if all_diagrams:
                    question_shapes = []
                    for page_diagrams in all_diagrams:
                        q_diagrams = page_diagrams.get("question_diagrams", {})
                        if str(question.question_number) in q_diagrams:
                            question_shapes.extend(q_diagrams[str(question.question_number)])
                    
                    if question_shapes:
                        diagram_info = {"has_diagrams": True, "shapes_detected": question_shapes}
                
                context_chunks = rag_service.retrieve_relevant_context(
                    question.question_text,
                    subject=paper.subject.value
                )
                context = rag_service.format_context_for_llm(context_chunks)
                
                result = eval_service.evaluate_answer(
                    question=question.question_text,
                    student_answer=student_answer,
                    textbook_context=context,
                    subject=paper.subject.value,
                    class_level=str(paper.class_level),
                    max_score=question.marks,
                    diagram_info=diagram_info
                )
            
            # Store evaluation
            import json
            crud_evaluation.create_evaluation(
                db,
                submission_id=submission_id,
                question_id=question.id,
                student_answer=student_answer,
                marks_obtained=result.get("score", 0),
                max_marks=question.marks,
                feedback=json.dumps(result),
                rag_context=json.dumps(context_chunks)
            )
        
        crud_submission.update_submission_status(db, submission_id, SubmissionStatus.EVALUATED)
        
    except Exception as e:
        print(f"Error processing submission: {e}")
        crud_submission.update_submission_status(db, submission_id, SubmissionStatus.FAILED)

def process_submission(submission_id: str, image_path: str, paper_id: str, db: Session):
    try:
        # OCR with diagram extraction
        ocr_service = OCRService()
        extracted_text, diagram_metadata = ocr_service.extract_text_from_image(image_path)
        crud_submission.update_submission_text(db, submission_id, extracted_text)
        
        # Store diagram metadata
        if diagram_metadata.get("has_diagrams"):
            import json
            from app.models.submission import AnswerSubmission
            submission = db.query(AnswerSubmission).filter(AnswerSubmission.id == submission_id).first()
            if submission:
                submission.diagram_metadata = diagram_metadata
                db.commit()
        
        # Parse answers
        parser = AnswerParser()
        parsed_answers = parser.parse_answers(extracted_text)
        
        # Get paper questions
        paper = crud_paper.get_paper(db, paper_id)
        
        # Evaluate each question
        rag_service = RAGService()
        eval_service = EvaluationService()
        
        for question in paper.questions:
            student_answer = parsed_answers.get(question.question_number, "")
            
            # Get RAG context
            context_chunks = rag_service.retrieve_relevant_context(
                question.question_text,
                subject=paper.subject.value
            )
            context = rag_service.format_context_for_llm(context_chunks)
            
            # Evaluate with diagram info
            result = eval_service.evaluate_answer(
                question=question.question_text,
                student_answer=student_answer,
                textbook_context=context,
                subject=paper.subject.value,
                class_level=str(paper.class_level),
                max_score=question.marks,
                diagram_info=diagram_metadata if diagram_metadata.get("has_diagrams") else None
            )
            
            # Store evaluation
            import json
            crud_evaluation.create_evaluation(
                db,
                submission_id=submission_id,
                question_id=question.id,
                student_answer=student_answer,
                marks_obtained=result.get("score", 0),
                max_marks=question.marks,
                feedback=json.dumps(result),
                rag_context=json.dumps(context_chunks)
            )
        
        crud_submission.update_submission_status(db, submission_id, SubmissionStatus.EVALUATED)
        
    except Exception as e:
        print(f"Error processing submission: {e}")
        crud_submission.update_submission_status(db, submission_id, SubmissionStatus.FAILED)

@router.get("/submissions", response_model=List[Submission])
def get_my_submissions(
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    return crud_submission.get_student_submissions(db, student.id)

@router.get("/submissions/{submission_id}")
def get_submission_details(
    submission_id: str,
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    submissions = crud_submission.get_student_submissions(db, student.id)
    submission_data = next((s for s in submissions if str(s["id"]) == submission_id), None)
    
    if not submission_data:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submission_data

@router.get("/papers/{paper_id}/pdf")
def get_question_paper_pdf(
    paper_id: str,
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    """Get the uploaded question paper PDF for viewing"""
    paper = crud_paper.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.pdf_path or not os.path.exists(paper.pdf_path):
        raise HTTPException(status_code=404, detail="Question paper PDF not available")
    
    return FileResponse(
        paper.pdf_path,
        media_type="application/pdf",
        filename=f"{paper.title}.pdf"
    )

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
    
    # Create submission and immediately mark as evaluating
    submission = crud_submission.create_submission(db, paper_id, student.id, file_paths[0], uploaded_files=file_paths)
    crud_submission.update_submission_status(db, submission.id, SubmissionStatus.EVALUATING)
    db.refresh(submission)
    
    # Process in background
    background_tasks.add_task(process_submission_multiple, submission.id, file_paths, paper_id, db)
    
    return submission

def process_submission_multiple(submission_id: str, image_paths: list, paper_id: str, _old_db: Session = None):
    from app.core.database import SessionLocal
    db = SessionLocal()
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
        
        # Log question mapping for debugging
        print(f"\n=== QUESTION IDENTIFICATION ===")
        print(f"Paper has {len(paper.questions)} questions")
        print(f"Parsed {len(parsed_answers)} answers from student sheet")
        print(f"Question numbers in paper: {[q.question_number for q in paper.questions]}")
        print(f"Question numbers parsed: {list(parsed_answers.keys())}")
        
        # Smart Answer Mapping (Hackathon fallback for misnumbered OCR)
        mapped_answers = {}
        unmapped_answers = []
        for q_num, ans_text in parsed_answers.items():
            if any(q.question_number == q_num for q in paper.questions):
                mapped_answers[q_num] = ans_text
            else:
                unmapped_answers.append(ans_text)
                
        unmapped_questions = [q for q in paper.questions if q.question_number not in mapped_answers]
        
        import re
        for ans_text in unmapped_answers:
            if not unmapped_questions:
                break
            
            # For a single missing map, just assign it directly
            if len(unmapped_answers) == 1 and len(unmapped_questions) == 1:
                mapped_answers[unmapped_questions[0].question_number] = ans_text
                unmapped_questions.pop(0)
                break
                
            best_q = None
            best_score = -1
            ans_words = set(re.findall(r'\w+', ans_text.lower()))
            
            for q in unmapped_questions:
                q_words = set(re.findall(r'\w+', q.question_text.lower()))
                score = len(ans_words.intersection(q_words))
                if score > best_score:
                    best_score = score
                    best_q = q
            
            if best_q:
                mapped_answers[best_q.question_number] = ans_text
                unmapped_questions.remove(best_q)
        
        # Evaluate each question
        rag_service = RAGService()
        eval_service = EvaluationService()
        
        for question in paper.questions:
            student_answer = mapped_answers.get(question.question_number, "").strip()
            
            # Match question type
            if hasattr(question.question_type, 'value'):
                q_type = question.question_type.value
            else:
                q_type = str(question.question_type)

            # Log question matching
            print(f"\nQ{question.question_number} [{q_type}]: {question.question_text[:80]}...")
            print(f"Student answer: {student_answer[:100] if student_answer else '(empty branch)'}...")
            
            if q_type == "mcq":
                # Evaluate MCQ (simple comparison, no RAG)
                result = evaluate_mcq(question, student_answer)
                context_chunks = []
            elif not student_answer:
                # Descriptive but empty - award 0 without calling AI
                result = {
                    "score": 0,
                    "score_breakdown": {"correctness": 0, "completeness": 0, "understanding": 0},
                    "overall_feedback": "Question was not answered.",
                    "correct_points": [],
                    "errors": [{"what": "Unanswered", "why": "No text detected", "impact": "0 marks"}],
                    "missing_concepts": ["Complete explanation"],
                    "improvement_guidance": [{"suggestion": "Try to solve every question.", "resource": "Revision", "practice": "Mock test"}]
                }
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
                
                # Build question paper context
                qp_context = f"Question {question.question_number} ({question.marks} marks): {question.question_text}"
                if question.section:
                    qp_context = f"Section {question.section} - " + qp_context
                
                # RAG retrieval with question paper context prioritized
                context_chunks = rag_service.retrieve_relevant_context(
                    question.question_text,
                    subject=paper.subject.value,
                    question_paper_context=qp_context,
                    class_level=str(paper.class_level)
                )
                context = rag_service.format_context_for_llm(context_chunks)
                
                # Extract RAG scores for confidence calculation
                rag_scores = [c.get('score', 0) for c in context_chunks if c.get('source') == 'textbook']
                
                # Get marking scheme if available
                marking_scheme = question.marking_scheme if hasattr(question, 'marking_scheme') else None
                
                # Log RAG retrieval
                print(f"RAG retrieved {len(context_chunks)} chunks for Q{question.question_number}")
                if context_chunks:
                    print(f"Top chunk score: {context_chunks[0].get('score', 0):.3f}")
                    print(f"Context preview: {context[:150]}...")
                
                result = eval_service.evaluate_answer(
                    question=question.question_text,
                    student_answer=student_answer,
                    textbook_context=context,
                    subject=paper.subject.value,
                    class_level=str(paper.class_level),
                    max_score=question.marks,
                    diagram_info=diagram_info,
                    marking_scheme=marking_scheme,
                    rag_scores=rag_scores
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
            
            print(f"Q{question.question_number} evaluated: {result.get('score', 0)}/{question.marks} marks")
        
        print(f"\n=== EVALUATION COMPLETE ===")
        crud_submission.update_submission_status(db, submission_id, SubmissionStatus.EVALUATED)

        # ── Fire "graded" notification to the student ────────────────────────
        try:
            from app.models.submission import AnswerSubmission
            from app.models.question_paper import QuestionPaper
            from app.utils.notify import create_notification
            from sqlalchemy import func as _func
            from app.models.evaluation import Evaluation
            sub = db.query(AnswerSubmission).filter(AnswerSubmission.id == submission_id).first()
            if sub:
                paper_obj = crud_paper.get_paper(db, paper_id)
                total = db.query(_func.sum(Evaluation.marks_obtained)).filter(
                    Evaluation.submission_id == submission_id
                ).scalar() or 0
                max_m = db.query(_func.sum(Evaluation.max_marks)).filter(
                    Evaluation.submission_id == submission_id
                ).scalar() or 1
                pct = round(float(total) / float(max_m) * 100, 1) if max_m else 0
                paper_title = paper_obj.title if paper_obj else "your paper"
                create_notification(
                    db, str(sub.student_id),
                    type_="graded",
                    title=f"✅ {paper_title} has been graded!",
                    body=f"You scored {total}/{max_m} ({pct}%)",
                    link=f"/student/submissions/{submission_id}",
                )
        except Exception as notify_err:
            print(f"Notification error (non-fatal): {notify_err}")
        
    except Exception as e:
        print(f"Error processing submission: {e}")
        import traceback
        traceback.print_exc()
        try:
            crud_submission.update_submission_status(db, submission_id, SubmissionStatus.FAILED)
        except:
            pass
    finally:
        db.close()

def process_submission(submission_id: str, image_path: str, paper_id: str, _old_db: Session = None):
    from app.core.database import SessionLocal
    db = SessionLocal()
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
        
        # Smart Answer Mapping (Hackathon fallback for misnumbered OCR)
        mapped_answers = {}
        unmapped_answers = []
        for q_num, ans_text in parsed_answers.items():
            if any(q.question_number == q_num for q in paper.questions):
                mapped_answers[q_num] = ans_text
            else:
                unmapped_answers.append(ans_text)
                
        unmapped_questions = [q for q in paper.questions if q.question_number not in mapped_answers]
        
        import re
        for ans_text in unmapped_answers:
            if not unmapped_questions:
                break
            
            # For a single missing map, just assign it directly
            if len(unmapped_answers) == 1 and len(unmapped_questions) == 1:
                mapped_answers[unmapped_questions[0].question_number] = ans_text
                unmapped_questions.pop(0)
                break
                
            best_q = None
            best_score = -1
            ans_words = set(re.findall(r'\w+', ans_text.lower()))
            
            for q in unmapped_questions:
                q_words = set(re.findall(r'\w+', q.question_text.lower()))
                score = len(ans_words.intersection(q_words))
                if score > best_score:
                    best_score = score
                    best_q = q
            
            if best_q:
                mapped_answers[best_q.question_number] = ans_text
                unmapped_questions.remove(best_q)
        
        # Evaluate each question
        rag_service = RAGService()
        eval_service = EvaluationService()
        
        for question in paper.questions:
            student_answer = mapped_answers.get(question.question_number, "").strip()
            
            # Get RAG context
            context_chunks = rag_service.retrieve_relevant_context(
                question.question_text,
                subject=paper.subject.value,
                class_level=str(paper.class_level)
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
        import traceback
        traceback.print_exc()
        try:
            crud_submission.update_submission_status(db, submission_id, SubmissionStatus.FAILED)
        except:
            pass
    finally:
        db.close()

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
    submission_data = crud_submission.get_submission_details(db, submission_id, student.id)
    
    if not submission_data:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submission_data

@router.get("/submissions/{submission_id}/image")
def get_submission_image(
    submission_id: str,
    page: int = 0,
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    """Serve original uploaded answer sheet image by page index."""
    submission = crud_submission.get_submission(db, submission_id)
    if not submission:
        print(f"IMAGE ERROR: Submission {submission_id} not found")
        raise HTTPException(status_code=404, detail="Submission not found")
    if str(submission.student_id) != str(student.id):
        print(f"IMAGE ERROR: Access denied for {student.id} to {submission_id}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    base_path = submission.image_path
    if not base_path:
        raise HTTPException(status_code=404, detail="No image found")
    
    # Prefer uploaded_files (only the originals the student uploaded)
    if submission.uploaded_files and isinstance(submission.uploaded_files, list):
        pages = submission.uploaded_files
    else:
        # Legacy fallback: scan folder for matching UUID prefix
        import glob
        folder = os.path.dirname(base_path)
        uuid_prefix = os.path.basename(base_path).split("_page")[0]
        pattern = os.path.join(folder, f"{uuid_prefix}_page*")
        pages = sorted(glob.glob(pattern))
        if not pages:
            pages = [base_path]
    
    # Handle 1-based indexing from frontend (page 1 = index 0)
    # If page is 0, we treat it as requesting the first page (index 0)
    page_idx = max(0, page - 1) if page > 0 else 0
    
    if page_idx >= len(pages):
        raise HTTPException(status_code=404, detail=f"Page {page} not found (total: {len(pages)})")
    
    target = pages[page_idx]
    if not os.path.exists(target):
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    
    ext = os.path.splitext(target)[1].lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    
    return FileResponse(target, media_type=mime)

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


# ═══════════════════════════════════════════════════════════════
# PHASE 2 – #13: Exam mode paper listing
# ═══════════════════════════════════════════════════════════════

@router.get("/papers/{paper_id}/exam-status")
def get_exam_status(
    paper_id: str,
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    """Returns the live exam window status for a paper."""
    paper = crud_paper.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    now = datetime.utcnow()
    if not paper.is_exam_mode:
        return {"mode": "practice", "can_submit": True}

    if paper.exam_start_time and now < paper.exam_start_time:
        return {
            "mode": "exam", "status": "upcoming",
            "can_submit": False,
            "opens_at": paper.exam_start_time.isoformat(),
            "seconds_until_open": int((paper.exam_start_time - now).total_seconds()),
        }
    if paper.exam_end_time and now > paper.exam_end_time:
        return {
            "mode": "exam", "status": "closed",
            "can_submit": False,
            "closed_at": paper.exam_end_time.isoformat(),
        }
    return {
        "mode": "exam", "status": "live", "can_submit": True,
        "ends_at": paper.exam_end_time.isoformat() if paper.exam_end_time else None,
        "seconds_remaining": int((paper.exam_end_time - now).total_seconds()) if paper.exam_end_time else None,
    }


# ═══════════════════════════════════════════════════════════════
# PHASE 2 – #6: Student Progress API
# ═══════════════════════════════════════════════════════════════

@router.get("/progress")
def get_my_progress(
    db: Session = Depends(get_db),
    student: User = Depends(get_student)
):
    """
    Returns a timeline of all evaluated submissions with per-subject aggregation.
    Used by the student progress dashboard.
    """
    from app.models.submission import AnswerSubmission
    from app.models.question_paper import QuestionPaper
    from app.models.evaluation import Evaluation
    from sqlalchemy import func

    # Fetch all evaluated submissions for this student, newest first
    rows = (
        db.query(AnswerSubmission, QuestionPaper)
        .join(QuestionPaper, AnswerSubmission.paper_id == QuestionPaper.id)
        .filter(
            AnswerSubmission.student_id == student.id,
            AnswerSubmission.status == "evaluated"
        )
        .order_by(AnswerSubmission.submitted_at.asc())
        .all()
    )

    timeline = []
    subject_buckets = {}  # subject -> list of (pct, submitted_at)

    for sub, paper in rows:
        total = db.query(func.sum(Evaluation.marks_obtained)).filter(
            Evaluation.submission_id == sub.id
        ).scalar() or 0
        max_m = db.query(func.sum(Evaluation.max_marks)).filter(
            Evaluation.submission_id == sub.id
        ).scalar() or 1
        pct = round((float(total) / float(max_m)) * 100, 1) if max_m else 0

        entry = {
            "submission_id": str(sub.id),
            "paper_title": paper.title,
            "subject": paper.subject.value if hasattr(paper.subject, 'value') else str(paper.subject),
            "submitted_at": sub.submitted_at.isoformat(),
            "marks_obtained": float(total),
            "max_marks": float(max_m),
            "percentage": pct,
        }
        timeline.append(entry)

        subj = entry["subject"]
        subject_buckets.setdefault(subj, []).append(pct)

    # Per-subject stats
    subject_stats = []
    for subj, pcts in subject_buckets.items():
        subject_stats.append({
            "subject": subj,
            "attempts": len(pcts),
            "average": round(sum(pcts) / len(pcts), 1),
            "best": round(max(pcts), 1),
            "trend": "improving" if len(pcts) > 1 and pcts[-1] > pcts[0] else
                     "declining"  if len(pcts) > 1 and pcts[-1] < pcts[0] else
                     "stable",
        })

    return {
        "total_submissions": len(timeline),
        "overall_average": round(sum(e["percentage"] for e in timeline) / len(timeline), 1) if timeline else 0,
        "timeline": timeline,
        "subject_stats": subject_stats,
    }

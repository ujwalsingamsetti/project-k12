from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import time
import logging
from datetime import datetime
from typing import Optional
import json
import uuid

from app.config import settings
from app.models import EvaluationRequest, EvaluationStatus
from app.routes.upload import get_upload_metadata
from app.services.ocr_service import OCRService
from app.services.answer_parser import AnswerSheetParser
from app.services.rag_service import RAGService
from app.services.evaluation_service import EvaluationService

router = APIRouter(tags=["Evaluation"])
logger = logging.getLogger(__name__)

ocr_service = None
parser_service = None
rag_service = None
eval_service = None

def get_services():
    """Lazy initialization of services"""
    global ocr_service, parser_service, rag_service, eval_service
    
    if ocr_service is None:
        logger.info("Initializing services...")
        ocr_service = OCRService()
        parser_service = AnswerSheetParser()
        rag_service = RAGService()
        eval_service = EvaluationService()
        logger.info("Services initialized successfully")
    
    return ocr_service, parser_service, rag_service, eval_service

def save_evaluation_result(evaluation_id: str, result: dict) -> None:
    """Save evaluation result to disk"""
    results_dir = os.path.join(settings.DATA_DIR, "evaluations")
    os.makedirs(results_dir, exist_ok=True)
    
    result_path = os.path.join(results_dir, f"{evaluation_id}.json")
    
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)

def get_evaluation_result(evaluation_id: str) -> Optional[dict]:
    """Retrieve evaluation result from disk"""
    result_path = os.path.join(settings.DATA_DIR, "evaluations", f"{evaluation_id}.json")
    
    if not os.path.exists(result_path):
        return None
    
    with open(result_path, 'r') as f:
        return json.load(f)

def update_evaluation_status(evaluation_id: str, status: str, progress: int = None, message: str = None):
    """Update evaluation status"""
    status_dir = os.path.join(settings.DATA_DIR, "status")
    os.makedirs(status_dir, exist_ok=True)
    
    status_data = {
        "evaluation_id": evaluation_id,
        "status": status,
        "progress": progress,
        "message": message,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    status_path = os.path.join(status_dir, f"{evaluation_id}.json")
    with open(status_path, 'w') as f:
        json.dump(status_data, f, indent=2)

async def process_evaluation(evaluation_id: str, file_id: str, subject: str, class_level: str):
    """Background task to process evaluation"""
    
    try:
        update_evaluation_status(evaluation_id, EvaluationStatus.PROCESSING, 0, "Starting evaluation...")
        
        ocr, parser, rag, evaluator = get_services()
        
        metadata = get_upload_metadata(file_id)
        if not metadata:
            raise Exception(f"File not found: {file_id}")
        
        file_path = metadata["file_path"]
        
        # Step 1: OCR
        update_evaluation_status(evaluation_id, EvaluationStatus.PROCESSING, 20, "Extracting text...")
        logger.info(f"[{evaluation_id}] OCR extraction")
        extracted_text = ocr.extract_text_from_image(file_path)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise Exception("No text extracted")
        
        # Step 2: Parse
        update_evaluation_status(evaluation_id, EvaluationStatus.PROCESSING, 40, "Parsing answers...")
        logger.info(f"[{evaluation_id}] Parsing")
        parsed_questions = parser.parse_answer_sheet(extracted_text)
        
        if not parsed_questions:
            raise Exception("No questions found")
        
        logger.info(f"[{evaluation_id}] Found {len(parsed_questions)} questions")
        
        # Step 3: RAG
        update_evaluation_status(evaluation_id, EvaluationStatus.PROCESSING, 60, "Retrieving context...")
        logger.info(f"[{evaluation_id}] RAG retrieval")
        
        questions_data = []
        for q in parsed_questions:
            context_chunks = rag.retrieve_relevant_context(
                query=q.get('question_text', q['student_answer']),
                subject=subject,
                top_k=settings.MAX_CHUNKS_PER_QUERY
            )
            
            textbook_context = rag.format_context_for_llm(context_chunks, max_tokens=800)
            
            questions_data.append({
                "question_number": q['question_number'],
                "question_text": q.get('question_text', f"Question {q['question_number']}"),
                "student_answer": q['student_answer'],
                "textbook_context": textbook_context,
                "max_score": 10
            })
        
        # Step 4: Evaluate
        update_evaluation_status(evaluation_id, EvaluationStatus.PROCESSING, 80, "Evaluating with AI...")
        logger.info(f"[{evaluation_id}] LLM evaluation")
        
        start_time = time.time()
        
        def progress_callback(current, total):
            progress = 80 + int((current / total) * 15)
            update_evaluation_status(evaluation_id, EvaluationStatus.PROCESSING, progress, f"Evaluating {current}/{total}...")
        
        evaluation_result = evaluator.evaluate_answer_sheet_with_progress(
            questions_data=questions_data,
            subject=subject,
            progress_callback=progress_callback
        )
        
        processing_time = time.time() - start_time
        
        # Step 5: Finalize
        update_evaluation_status(evaluation_id, EvaluationStatus.PROCESSING, 95, "Finalizing...")
        
        final_result = {
            "evaluation_id": evaluation_id,
            "file_id": file_id,
            "subject": subject,
            "class_level": class_level,
            "overall_score": evaluation_result["overall_score"],
            "max_possible_score": evaluation_result["max_possible_score"],
            "percentage": evaluation_result["percentage"],
            "total_questions": evaluation_result["total_questions"],
            "evaluations": evaluation_result["evaluations"],
            "summary": evaluation_result["summary"],
            "evaluated_at": datetime.utcnow().isoformat(),
            "processing_time": round(processing_time, 2)
        }
        
        save_evaluation_result(evaluation_id, final_result)
        update_evaluation_status(evaluation_id, EvaluationStatus.COMPLETED, 100, "Completed!")
        
        logger.info(f"[{evaluation_id}] Completed in {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"[{evaluation_id}] Failed: {str(e)}")
        update_evaluation_status(evaluation_id, EvaluationStatus.FAILED, None, str(e))

@router.post("/evaluate")
async def evaluate_answer_sheet(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """Start evaluation (async)"""
    
    try:
        metadata = get_upload_metadata(request.file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_id}")
        
        evaluation_id = str(uuid.uuid4())
        
        background_tasks.add_task(
            process_evaluation,
            evaluation_id=evaluation_id,
            file_id=request.file_id,
            subject=request.subject,
            class_level=request.class_level
        )
        
        update_evaluation_status(evaluation_id, EvaluationStatus.PENDING, 0, "Queued")
        
        logger.info(f"Evaluation started: {evaluation_id}")
        
        return {
            "evaluation_id": evaluation_id,
            "status": EvaluationStatus.PENDING,
            "progress": 0,
            "message": "Evaluation started"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evaluate/{evaluation_id}/status")
async def get_evaluation_status(evaluation_id: str):
    """Check evaluation status"""
    
    status_path = os.path.join(settings.DATA_DIR, "status", f"{evaluation_id}.json")
    
    if not os.path.exists(status_path):
        raise HTTPException(status_code=404, detail=f"Evaluation not found: {evaluation_id}")
    
    with open(status_path, 'r') as f:
        status_data = json.load(f)
    
    result = None
    if status_data["status"] == EvaluationStatus.COMPLETED:
        result = get_evaluation_result(evaluation_id)
    
    return {
        "evaluation_id": status_data["evaluation_id"],
        "status": status_data["status"],
        "progress": status_data.get("progress"),
        "message": status_data.get("message"),
        "result": result
    }

@router.get("/evaluate/{evaluation_id}/result")
async def get_result(evaluation_id: str):
    """Get final result"""
    
    result = get_evaluation_result(evaluation_id)
    
    if not result:
        status_path = os.path.join(settings.DATA_DIR, "status", f"{evaluation_id}.json")
        if os.path.exists(status_path):
            with open(status_path, 'r') as f:
                status_data = json.load(f)
            
            if status_data["status"] in [EvaluationStatus.PENDING, EvaluationStatus.PROCESSING]:
                raise HTTPException(status_code=202, detail="Still processing")
            elif status_data["status"] == EvaluationStatus.FAILED:
                raise HTTPException(status_code=500, detail=status_data.get('message', 'Failed'))
        
        raise HTTPException(status_code=404, detail="Result not found")
    
    return result

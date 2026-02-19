from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
import logging
from typing import Optional
import json
import re

from app.config import settings
from app.models import UploadResponse

router = APIRouter(tags=["Upload"])
logger = logging.getLogger(__name__)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

def generate_file_id() -> str:
    """Generate unique file identifier"""
    return str(uuid.uuid4())

def get_file_extension(filename: str) -> str:
    """Extract file extension"""
    return Path(filename).suffix.lower()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    filename = os.path.basename(filename)
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[^\w\-.]', '', filename)
    return filename

def validate_file_size(file: UploadFile) -> bool:
    """Validate file size"""
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    return file_size <= settings.MAX_UPLOAD_SIZE

def save_upload_metadata(file_id: str, metadata: dict) -> None:
    """Save upload metadata to JSON file"""
    metadata_dir = os.path.join(settings.DATA_DIR, "metadata")
    os.makedirs(metadata_dir, exist_ok=True)
    
    metadata_path = os.path.join(metadata_dir, f"{file_id}.json")
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def get_upload_metadata(file_id: str) -> Optional[dict]:
    """Retrieve upload metadata"""
    metadata_path = os.path.join(settings.DATA_DIR, "metadata", f"{file_id}.json")
    
    if not os.path.exists(metadata_path):
        return None
    
    with open(metadata_path, 'r') as f:
        return json.load(f)

@router.post("/upload", response_model=UploadResponse)
async def upload_answer_sheet(
    file: UploadFile = File(..., description="Answer sheet image or PDF"),
    subject: str = Form(..., description="Subject (Science/Mathematics)"),
    class_level: str = Form(default="10", description="Class level")
):
    """
    Upload an answer sheet for evaluation.
    
    - **file**: Image (PNG, JPG, JPEG, TIFF, BMP) or PDF file
    - **subject**: Subject name (Science or Mathematics)
    - **class_level**: Class level (default: 10)
    
    Returns file_id to use for evaluation.
    """
    
    try:
        if subject not in ["Science", "Mathematics"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid subject. Must be 'Science' or 'Mathematics'"
            )
        
        file_ext = get_file_extension(file.filename)
        if not settings.is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.allowed_extensions)}"
            )
        
        if not validate_file_size(file):
            max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size_mb}MB"
            )
        
        file_id = generate_file_id()
        safe_filename = sanitize_filename(file.filename)
        new_filename = f"{file_id}_{safe_filename}"
        
        today = datetime.now().strftime("%Y-%m-%d")
        upload_subdir = os.path.join(settings.UPLOAD_DIR, today)
        os.makedirs(upload_subdir, exist_ok=True)
        
        file_path = os.path.join(upload_subdir, new_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        metadata = {
            "file_id": file_id,
            "original_filename": file.filename,
            "saved_filename": new_filename,
            "file_path": file_path,
            "file_size": file_size,
            "file_extension": file_ext,
            "subject": subject,
            "class_level": class_level,
            "uploaded_at": datetime.utcnow().isoformat(),
            "status": "uploaded"
        }
        
        save_upload_metadata(file_id, metadata)
        
        logger.info(f"File uploaded successfully: {file_id} - {safe_filename} ({file_size} bytes)")
        
        return UploadResponse(
            success=True,
            file_id=file_id,
            file_name=safe_filename,
            file_size=file_size,
            subject=subject,
            class_level=class_level,
            message="File uploaded successfully",
            uploaded_at=metadata["uploaded_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/upload/{file_id}/info")
async def get_upload_info(file_id: str):
    """Get information about an uploaded file"""
    
    metadata = get_upload_metadata(file_id)
    
    if not metadata:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_id}"
        )
    
    safe_metadata = {
        "file_id": metadata["file_id"],
        "original_filename": metadata["original_filename"],
        "file_size": metadata["file_size"],
        "subject": metadata["subject"],
        "class_level": metadata["class_level"],
        "uploaded_at": metadata["uploaded_at"],
        "status": metadata.get("status", "uploaded")
    }
    
    return safe_metadata

@router.delete("/upload/{file_id}")
async def delete_upload(file_id: str):
    """Delete an uploaded file"""
    
    metadata = get_upload_metadata(file_id)
    
    if not metadata:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_id}"
        )
    
    file_path = metadata["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)
    
    metadata_path = os.path.join(settings.DATA_DIR, "metadata", f"{file_id}.json")
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
    
    logger.info(f"File deleted: {file_id}")
    
    return {
        "success": True,
        "message": f"File {file_id} deleted successfully"
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.api import auth, teachers, students
from app.core.config import settings

app = FastAPI(
    title="K12 Answer Sheet Evaluator",
    description="Automated answer sheet evaluation system with OCR and AI",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(teachers.router, prefix="/api")
app.include_router(students.router, prefix="/api")

# Serve uploaded files
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
def root():
    return {"message": "K12 Answer Sheet Evaluator API v2.0"}

@app.get("/api/health")
def health():
    return {"status": "healthy", "version": "2.0.0"}

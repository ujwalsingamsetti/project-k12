from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://localhost/k12_evaluator"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # LLM
    OPENAI_API_KEY: str = "not-needed-for-local-llm"
    OPENAI_MODEL: str = "llama3.1:8b"
    OPENAI_BASE_URL: str = "http://localhost:11434/v1"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_NAME: str = "k12_textbooks"
    
    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Google Vision
    GOOGLE_VISION_CREDENTIALS: str = "./google-vision-credentials.json"
    
    # File Storage
    UPLOAD_DIR: str = "./data/uploads"
    QUESTION_PAPER_DIR: str = "./data/question_papers"
    MAX_UPLOAD_SIZE: int = 10485760
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

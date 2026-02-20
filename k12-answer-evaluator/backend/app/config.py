from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Settings
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    DEBUG: str = "False"
    LOG_LEVEL: str = "INFO"
    
    # LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: str = "not-needed-for-local-llm"
    OPENAI_MODEL: str = "llama3.1:8b"
    OPENAI_BASE_URL: str = "http://localhost:11434/v1"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 2000
    USE_LOCAL_LLM: bool = True
    
    # Vector Database Settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "k12_textbooks"
    QDRANT_VECTOR_SIZE: int = 384
    QDRANT_DISTANCE_METRIC: str = "Cosine"
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32
    
    # OCR Settings
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    TESSERACT_LANG: str = "eng"
    TESSERACT_CONFIG: str = "--psm 6"
    GOOGLE_VISION_CREDENTIALS: str = "./google-vision-credentials.json"
    
    # File Storage Settings
    UPLOAD_DIR: str = "./data/uploads"
    TEXTBOOK_DIR: str = "./data/textbooks"
    DATA_DIR: str = "./data"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_IMAGE_EXTENSIONS: str = ".png,.jpg,.jpeg,.tiff,.bmp"
    ALLOWED_PDF_EXTENSIONS: str = ".pdf"
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_PER_QUERY: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def allowed_extensions(self) -> list:
        """Get list of allowed file extensions"""
        image_exts = self.ALLOWED_IMAGE_EXTENSIONS.split(',')
        pdf_exts = self.ALLOWED_PDF_EXTENSIONS.split(',')
        return image_exts + pdf_exts
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return any(filename.lower().endswith(ext) for ext in self.allowed_extensions)

# Create global settings instance
settings = Settings()

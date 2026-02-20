import PyPDF2
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid
import logging
import os

logger = logging.getLogger(__name__)

class TextbookIngestionService:
    """Ingest teacher-uploaded textbooks into Qdrant"""
    
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.client = QdrantClient(url="http://localhost:6333")
    
    def ingest_textbook(self, pdf_path: str, subject: str, textbook_id: str, teacher_id: str, class_level: str = "") -> int:
        """Ingest PDF textbook into vector database"""
        
        try:
            # Extract text from PDF
            with open(pdf_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()
            
            # Split into chunks
            chunks = []
            chunk_size = 1000
            overlap = 200
            
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if len(chunk.strip()) > 50:
                    chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks from {os.path.basename(pdf_path)}")
            
            # Generate embeddings and upload
            points = []
            for idx, chunk in enumerate(chunks):
                embedding = self.model.encode(chunk).tolist()
                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "subject": subject.lower(),
                        "class_level": class_level.lower() if class_level else "",
                        "source": os.path.basename(pdf_path),
                        "chunk_index": idx,
                        "textbook_id": textbook_id,
                        "teacher_id": teacher_id,
                        "is_teacher_upload": True
                    }
                ))
            
            self.client.upsert(collection_name="k12_textbooks", points=points)
            logger.info(f"Uploaded {len(points)} chunks to Qdrant")
            
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Textbook ingestion failed: {e}")
            raise
    
    def delete_textbook_chunks(self, textbook_id: str):
        """Delete all chunks for a textbook"""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            self.client.delete(
                collection_name="k12_textbooks",
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="textbook_id",
                            match=MatchValue(value=textbook_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted chunks for textbook {textbook_id}")
        except Exception as e:
            logger.error(f"Failed to delete textbook chunks: {e}")

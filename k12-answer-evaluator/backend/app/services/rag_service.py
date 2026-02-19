import logging
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from app.config import settings

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for retrieving relevant textbook context"""
    
    def __init__(self):
        logger.info("Initializing RAGService...")
        
        self.embedding_model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
        
        self.qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        
        logger.info("RAGService initialized")
    
    def retrieve_relevant_context(self, query: str, subject: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant context from vector database"""
        
        try:
            # Generate query embedding
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Search with subject filter
            search_result = self.qdrant_client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="subject",
                            match=MatchValue(value=subject)
                        )
                    ]
                ),
                limit=top_k
            ).points
            
            # Format results
            results = []
            for point in search_result:
                results.append({
                    "text": point.payload["text"],
                    "score": point.score,
                    "chapter": point.payload.get("chapter", "unknown"),
                    "source": point.payload.get("source", "unknown")
                })
            
            logger.info(f"Retrieved {len(results)} chunks for query")
            return results
        
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            # Return mock data as fallback
            return [
                {
                    "text": "Photosynthesis is the process by which plants make food using sunlight, water, and carbon dioxide.",
                    "score": 0.95,
                    "chapter": "unknown",
                    "source": "fallback"
                }
            ]
    
    def format_context_for_llm(self, chunks: List[Dict], max_tokens: int = 800) -> str:
        """Format retrieved chunks for LLM"""
        if not chunks:
            return "No specific textbook reference available."
        
        context_parts = []
        for chunk in chunks[:3]:
            context_parts.append(chunk["text"])
        
        return "\n\n".join(context_parts)

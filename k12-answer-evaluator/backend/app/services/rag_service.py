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
    
    def retrieve_relevant_context(self, query: str, subject: str, top_k: int = 5, question_paper_context: str = None, class_level: str = None) -> List[Dict]:
        """Retrieve relevant context using hybrid search (semantic + keyword)"""
        
        results = []
        
        # First priority: Question paper context
        if question_paper_context:
            results.append({
                "text": question_paper_context,
                "score": 1.0,
                "chapter": "Question Paper",
                "source": "question_paper"
            })
            logger.info("Added question paper context as primary reference")
        
        try:
            # Extract keywords for hybrid search
            keywords = self._extract_keywords(query)
            
            # Generate query embedding for semantic search
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Build filters
            conditions = [
                FieldCondition(
                    key="subject",
                    match=MatchValue(value=subject.lower())
                )
            ]
            
            if class_level:
                conditions.append(
                    FieldCondition(
                        key="class_level",
                        match=MatchValue(value=class_level.lower())
                    )
                )

            # Semantic search
            search_result = self.qdrant_client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=query_vector,
                query_filter=Filter(must=conditions),
                limit=top_k * 2  # Get more for re-ranking
            ).points
            
            # Re-rank results using keyword matching
            ranked_results = self._rerank_with_keywords(search_result, keywords)
            
            # Format top results
            for point in ranked_results[:top_k]:
                results.append({
                    "text": point.payload["text"],
                    "score": point.score,
                    "chapter": point.payload.get("chapter", "unknown"),
                    "source": point.payload.get("source", "textbook")
                })
            
            logger.info(f"Retrieved {len(results)} total chunks (hybrid search)")
            return results
        
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return results if results else [{
                "text": "No reference material available.",
                "score": 0.0,
                "chapter": "unknown",
                "source": "fallback"
            }]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from question"""
        import re
        
        # Remove common words
        stop_words = {'what', 'why', 'how', 'when', 'where', 'is', 'are', 'the', 'a', 'an', 'of', 'in', 'to', 'for'}
        
        # Extract words (alphanumeric + keep scientific notation)
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', query.lower())
        
        # Filter stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        return keywords[:10]  # Top 10 keywords
    
    def _rerank_with_keywords(self, search_results, keywords: List[str]):
        """Re-rank results by boosting keyword matches"""
        if not keywords:
            return search_results
        
        for point in search_results:
            text_lower = point.payload["text"].lower()
            keyword_matches = sum(1 for kw in keywords if kw in text_lower)
            
            # Boost score by keyword match ratio
            keyword_boost = (keyword_matches / len(keywords)) * 0.2
            point.score = min(point.score + keyword_boost, 1.0)
        
        # Sort by boosted score
        return sorted(search_results, key=lambda x: x.score, reverse=True)
    
    def format_context_for_llm(self, chunks: List[Dict], max_tokens: int = 2000) -> str:
        """Format retrieved chunks for LLM with increased context window"""
        if not chunks:
            return "No specific reference available."
        
        context_parts = []
        
        # Separate question paper and textbook chunks
        qp_chunks = [c for c in chunks if c.get("source") == "question_paper"]
        tb_chunks = [c for c in chunks if c.get("source") != "question_paper"]
        
        # Add question paper context first
        if qp_chunks:
            context_parts.append("[QUESTION PAPER CONTEXT]")
            context_parts.append(qp_chunks[0]["text"])
        
        # Add top 3 textbook chunks (increased from 2)
        if tb_chunks:
            context_parts.append("\n[TEXTBOOK REFERENCE]")
            for idx, chunk in enumerate(tb_chunks[:3], 1):
                context_parts.append(f"Source {idx} (relevance: {chunk.get('score', 0):.2f}):")
                context_parts.append(chunk["text"])
        
        full_context = "\n\n".join(context_parts)
        
        # Truncate if exceeds max_tokens (1 token ≈ 0.75 chars)
        max_chars = int(max_tokens * 0.75)
        if len(full_context) > max_chars:
            full_context = full_context[:max_chars] + "..."
        
        return full_context

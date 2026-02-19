from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest
)
from typing import List, Dict, Optional
import logging
from time import sleep
from app.config import get_settings
from app.services.textbook_processor import TextbookChunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self):
        self.settings = get_settings()
        self.collection_name = self.settings.qdrant_collection_name
        self.client = self._initialize_client()
    
    def _initialize_client(self) -> QdrantClient:
        try:
            if self.settings.qdrant_url.startswith("http://localhost") or self.settings.qdrant_url.startswith("http://127.0.0.1"):
                host, port = self.settings.qdrant_url.replace("http://", "").split(":")
                client = QdrantClient(host=host, port=int(port))
            else:
                client = QdrantClient(
                    url=self.settings.qdrant_url,
                    api_key=self.settings.qdrant_api_key if self.settings.qdrant_api_key else None
                )
            
            logger.info(f"Connected to Qdrant at {self.settings.qdrant_url}")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def init_collection(self) -> bool:
        try:
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if collection_exists:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return True
            
            distance_metric = Distance.COSINE if self.settings.qdrant_distance_metric == "Cosine" else Distance.EUCLID
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.settings.qdrant_vector_size,
                    distance=distance_metric
                )
            )
            
            logger.info(f"Created collection '{self.collection_name}' with vector size {self.settings.qdrant_vector_size}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            return False
    
    def upsert_chunks(
        self,
        chunks: List[TextbookChunk],
        embeddings: List[List[float]],
        batch_size: int = 100
    ) -> bool:
        if len(chunks) != len(embeddings):
            logger.error("Number of chunks and embeddings must match")
            return False
        
        try:
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(chunks))
                
                batch_chunks = chunks[start_idx:end_idx]
                batch_embeddings = embeddings[start_idx:end_idx]
                
                points = []
                for chunk, embedding in zip(batch_chunks, batch_embeddings):
                    point = PointStruct(
                        id=chunk.chunk_id,
                        vector=embedding,
                        payload={
                            "chunk_id": chunk.chunk_id,
                            "content": chunk.content,
                            "subject": chunk.subject,
                            "class_level": chunk.class_level,
                            "chapter_title": chunk.chapter_title,
                            "chapter_number": chunk.chapter_number,
                            "page_number": chunk.page_number,
                            "concepts": chunk.concepts,
                            "metadata": chunk.metadata
                        }
                    )
                    points.append(point)
                
                retry_count = 0
                max_retries = 3
                
                while retry_count < max_retries:
                    try:
                        self.client.upsert(
                            collection_name=self.collection_name,
                            points=points
                        )
                        logger.info(f"Uploaded batch {batch_idx + 1}/{total_batches} ({len(points)} points)")
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            logger.error(f"Failed to upload batch {batch_idx + 1} after {max_retries} retries: {e}")
                            return False
                        logger.warning(f"Retry {retry_count}/{max_retries} for batch {batch_idx + 1}")
                        sleep(2 ** retry_count)
            
            logger.info(f"Successfully uploaded {len(chunks)} chunks to Qdrant")
            return True
        
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            return False
    
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        subject: Optional[str] = None,
        class_level: Optional[str] = None
    ) -> List[Dict]:
        try:
            query_filter = None
            
            if subject or class_level:
                conditions = []
                if subject:
                    conditions.append(
                        FieldCondition(key="subject", match=MatchValue(value=subject))
                    )
                if class_level:
                    conditions.append(
                        FieldCondition(key="class_level", match=MatchValue(value=class_level))
                    )
                query_filter = Filter(must=conditions)
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=top_k
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "chunk_id": result.payload["chunk_id"],
                    "content": result.payload["content"],
                    "subject": result.payload["subject"],
                    "class_level": result.payload["class_level"],
                    "chapter_title": result.payload["chapter_title"],
                    "chapter_number": result.payload["chapter_number"],
                    "page_number": result.payload["page_number"],
                    "concepts": result.payload["concepts"],
                    "metadata": result.payload["metadata"],
                    "score": result.score
                })
            
            logger.info(f"Found {len(search_results)} similar chunks")
            return search_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[chunk_id]
            )
            
            if not result:
                logger.warning(f"Chunk {chunk_id} not found")
                return None
            
            point = result[0]
            return {
                "chunk_id": point.payload["chunk_id"],
                "content": point.payload["content"],
                "subject": point.payload["subject"],
                "class_level": point.payload["class_level"],
                "chapter_title": point.payload["chapter_title"],
                "chapter_number": point.payload["chapter_number"],
                "page_number": point.payload["page_number"],
                "concepts": point.payload["concepts"],
                "metadata": point.payload["metadata"]
            }
        
        except Exception as e:
            logger.error(f"Failed to retrieve chunk {chunk_id}: {e}")
            return None
    
    def delete_collection(self) -> bool:
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection '{self.collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    def get_collection_info(self) -> Optional[Dict]:
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None

from sentence_transformers import SentenceTransformer
import torch
import re
import logging
from typing import List, Optional
from functools import lru_cache
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: Optional[str] = None):
        self.settings = get_settings()
        self.model_name = model_name or self.settings.embedding_model
        self.device = self._get_device()
        self.model = self._load_model()
        self.max_seq_length = 256
        logger.info(f"Initialized EmbeddingService with model '{self.model_name}' on {self.device}")
    
    def _get_device(self) -> str:
        if self.settings.embedding_device == "cuda" and torch.cuda.is_available():
            return "cuda"
        elif self.settings.embedding_device == "mps" and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    
    def _load_model(self) -> SentenceTransformer:
        try:
            model = SentenceTransformer(self.model_name, device=self.device)
            model.max_seq_length = self.max_seq_length
            return model
        except Exception as e:
            logger.error(f"Failed to load model '{self.model_name}': {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:()\-\']', '', text)
        
        words = text.split()
        if len(words) > self.max_seq_length:
            text = ' '.join(words[:self.max_seq_length])
        
        return text
    
    def generate_embedding(self, text: str) -> List[float]:
        try:
            preprocessed_text = self._preprocess_text(text)
            
            if not preprocessed_text:
                logger.warning("Empty text after preprocessing, returning zero vector")
                return [0.0] * self.get_embedding_dimension()
            
            embedding = self.model.encode(
                preprocessed_text,
                convert_to_tensor=False,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * self.get_embedding_dimension()
    
    def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        batch_size = batch_size or self.settings.embedding_batch_size
        
        try:
            preprocessed_texts = [self._preprocess_text(text) for text in texts]
            
            valid_texts = [text if text else " " for text in preprocessed_texts]
            
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_tensor=False,
                show_progress_bar=len(texts) > 100,
                normalize_embeddings=True
            )
            
            logger.info(f"Generated {len(embeddings)} embeddings in batches of {batch_size}")
            return embeddings.tolist()
        
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [[0.0] * self.get_embedding_dimension()] * len(texts)
    
    @lru_cache(maxsize=1000)
    def encode_query(self, query: str) -> List[float]:
        preprocessed_query = self._preprocess_text(query)
        
        if not preprocessed_query:
            logger.warning("Empty query after preprocessing")
            return [0.0] * self.get_embedding_dimension()
        
        try:
            embedding = self.model.encode(
                preprocessed_query,
                convert_to_tensor=False,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            
            return embedding.tolist()
        
        except Exception as e:
            logger.error(f"Failed to encode query: {e}")
            return [0.0] * self.get_embedding_dimension()
    
    def get_embedding_dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
    
    def clear_cache(self):
        self.encode_query.cache_clear()
        logger.info("Cleared embedding cache")

"""
Semantic search module using FAISS index.
Supports text search, image search, query expansion, reranking, and feedback integration.
"""

import logging
import numpy as np
import faiss
from pathlib import Path
from typing import List, Tuple
from PIL import Image

from .clip_model import CLIPModel
from .utils import load_metadata
from .logger import get_logger
from . import config

logger = get_logger(__name__)


class ImageSearcher:
    """Handles semantic image search using FAISS index."""
    
    def __init__(self, clip_model: CLIPModel):
        """
        Initialize searcher with CLIP model.
        
        Args:
            clip_model: CLIPModel instance
        """
        self.clip_model = clip_model
        self.index = None
        self.metadata = None
        self._reranker = None
        self._feedback_store = None
        self._load_index()
        self._init_reranker()
        self._init_feedback()
    
    def _load_index(self):
        """Load FAISS index and metadata from disk."""
        index_path = config.FAISS_INDEX_PATH
        metadata_path = config.METADATA_PATH
        
        if index_path.exists() and metadata_path.exists():
            try:
                logger.info("Loading FAISS index and metadata...")
                self.index = faiss.read_index(str(index_path))
                self.metadata = load_metadata(metadata_path)
                logger.info(f"Loaded index with {self.index.ntotal} vectors (dim={self.index.d}).")
            except Exception as e:
                logger.error(f"Failed to load index or metadata: {e}")
                self.index = None
                self.metadata = {}
        else:
            logger.info("No existing index found.")
            self.index = None
            self.metadata = {}
    
    def _init_reranker(self):
        """Initialize the cross-encoder reranker if enabled."""
        if config.ENABLE_RERANKING:
            try:
                from .reranker import CLIPReranker
                self._reranker = CLIPReranker(
                    model=self.clip_model.model,
                    preprocess=self.clip_model.preprocess,
                    device=self.clip_model.device
                )
                logger.info("Cross-encoder reranker initialized.")
            except Exception as e:
                logger.warning(f"Failed to initialize reranker: {e}")
                self._reranker = None
        else:
            self._reranker = None
    
    def _init_feedback(self):
        """Initialize the feedback store."""
        try:
            from .feedback import FeedbackStore
            self._feedback_store = FeedbackStore()
            logger.info("Feedback store initialized.")
        except Exception as e:
            logger.warning(f"Failed to initialize feedback store: {e}")
            self._feedback_store = None
    
    @property
    def feedback_store(self):
        """Public access to feedback store for UI integration."""
        return self._feedback_store
    
    def is_indexed(self) -> bool:
        """Check if index is loaded and ready."""
        return self.index is not None and self.metadata is not None and len(self.metadata) > 0
    
    def _expand_query_embedding(self, query: str) -> np.ndarray:
        """
        Encode query using multiple prompt templates in a single batch
        and average for richer representation.
        """
        import clip as clip_module
        import torch
        
        templates = [
            f"a photo of {query}",
            f"an image showing {query}",
            f"a picture depicting {query}",
        ]
        
        # Batch encode all templates in ONE forward pass (3x faster)
        with torch.no_grad():
            tokens = clip_module.tokenize(templates).to(self.clip_model.device)
            features = self.clip_model.model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
            avg = features.mean(dim=0, keepdim=True)
            avg = avg / avg.norm(dim=-1, keepdim=True)
        
        result = avg.cpu().numpy().flatten()
        logger.debug(f"Query expansion: batch-encoded {len(templates)} templates")
        return result
    
    def search(self, query: str, top_k: int = config.DEFAULT_TOP_K) -> List[Tuple[str, float]]:
        """
        Search for similar images given a text query.
        
        Uses query expansion, FAISS retrieval, optional reranking, and feedback boosting.
        
        Args:
            query: Text query string
            top_k: Number of results to return
        
        Returns:
            List of tuples (image_path, similarity_score)
        """
        if not self.is_indexed():
            logger.warning("Attempted search but no index is loaded.")
            return []
            
        if not query or not query.strip():
            logger.warning("Attempted search with empty query.")
            return []
            
        # Validate query length (CLIP token limit)
        max_chars = config.MAX_QUERY_LENGTH * 4
        if len(query) > max_chars:
            logger.warning(f"Query too long ({len(query)} chars). Truncating to {max_chars} chars.")
            query = query[:max_chars]
        
        try:
            # Determine how many candidates to retrieve from FAISS
            faiss_k = top_k
            if config.ENABLE_RERANKING and self._reranker:
                faiss_k = min(config.RERANKING_CANDIDATES, self.index.ntotal)
            else:
                faiss_k = min(top_k, self.index.ntotal)
            
            # Encode query — with or without expansion
            if config.ENABLE_QUERY_EXPANSION:
                query_embedding = self._expand_query_embedding(query)
            else:
                prompted_query = f"a photo of {query}"
                query_embedding = self.clip_model.encode_text(prompted_query)

            # Format for FAISS
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding, faiss_k)
            
            # Retrieve image paths
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:  # FAISS returns -1 for invalid indices
                    continue
                image_id = str(idx)
                if image_id in self.metadata:
                    results.append((self.metadata[image_id], float(score)))
            
            logger.info(f"FAISS search for '{query}' returned {len(results)} candidates.")
            
            # Stage 2: Cross-encoder reranking (if enabled)
            if config.ENABLE_RERANKING and self._reranker and len(results) > top_k:
                results = self._reranker.rerank(query, results, top_k=top_k)
                logger.info(f"Reranked to {len(results)} results.")
            else:
                results = results[:top_k]
            
            # Stage 3: Feedback boost (if available)
            if self._feedback_store:
                results = self._feedback_store.apply_feedback_boost(results, query)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def reload_index(self):
        """Reload index from disk (useful after re-indexing)."""
        logger.info("Reloading index...")
        self._load_index()
    
    def search_by_image(
        self, query_image: Image.Image, top_k: int = config.DEFAULT_TOP_K
    ) -> List[Tuple[str, float]]:
        """
        Search for similar images given a query image (reverse image search).
        
        Args:
            query_image: PIL Image object to use as the search query
            top_k: Number of results to return
        
        Returns:
            List of tuples (image_path, similarity_score)
        """
        if not self.is_indexed():
            logger.warning("Attempted image search but no index is loaded.")
            return []
        
        try:
            # Convert to RGB if needed
            if query_image.mode != 'RGB':
                query_image = query_image.convert('RGB')
            
            # Encode query image (already returns normalized embedding)
            query_embedding = self.clip_model.encode_image(query_image)

            # Format for FAISS
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
            
            # Search FAISS index
            scores, indices = self.index.search(
                query_embedding, min(top_k, self.index.ntotal)
            )
            
            # Retrieve image paths
            results: List[Tuple[str, float]] = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:  # FAISS returns -1 for invalid indices
                    continue
                image_id = str(idx)
                if image_id in self.metadata:
                    results.append((self.metadata[image_id], float(score)))
            
            logger.info(f"Image search returned {len(results)} results.")
            return results
            
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return []

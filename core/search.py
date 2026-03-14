"""
Semantic search module using FAISS index.
"""

import logging
import numpy as np
import faiss
from pathlib import Path
from typing import List, Tuple

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
        self._load_index()
    
    def _load_index(self):
        """Load FAISS index and metadata from disk."""
        index_path = config.FAISS_INDEX_PATH
        metadata_path = config.METADATA_PATH
        
        if index_path.exists() and metadata_path.exists():
            try:
                logger.info("Loading FAISS index and metadata...")
                self.index = faiss.read_index(str(index_path))
                self.metadata = load_metadata(metadata_path)
                logger.info(f"Loaded index with {self.index.ntotal} vectors.")
            except Exception as e:
                logger.error(f"Failed to load index or metadata: {e}")
                self.index = None
                self.metadata = {}
        else:
            logger.info("No existing index found.")
            self.index = None
            self.metadata = {}
    
    def is_indexed(self) -> bool:
        """Check if index is loaded and ready."""
        return self.index is not None and len(self.metadata) > 0
    
    def search(self, query: str, top_k: int = config.DEFAULT_TOP_K) -> List[Tuple[str, float]]:
        """
        Search for similar images given a text query.
        
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
        # 1 token is roughly 4 characters, so we'll use a conservative character limit
        max_chars = config.MAX_QUERY_LENGTH * 4
        if len(query) > max_chars:
            logger.warning(f"Query too long ({len(query)} chars). Truncating to {max_chars} chars.")
            query = query[:max_chars]
        
        try:
            # Encode query text
            query_embedding = self.clip_model.encode_text(query)
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
            
            # Retrieve image paths
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:  # FAISS returns -1 for invalid indices
                    continue
                image_id = str(idx)
                if image_id in self.metadata:
                    results.append((self.metadata[image_id], float(score)))
            
            logger.info(f"Search for '{query}' returned {len(results)} results.")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def reload_index(self):
        """Reload index from disk (useful after re-indexing)."""
        logger.info("Reloading index...")
        self._load_index()

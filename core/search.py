"""
Semantic search module using FAISS index.
"""

import numpy as np
import faiss
from pathlib import Path
from typing import List, Tuple

from .clip_model import CLIPModel
from .utils import load_metadata


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
        index_path = Path('storage/faiss.index')
        metadata_path = Path('storage/metadata.json')
        
        if index_path.exists() and metadata_path.exists():
            self.index = faiss.read_index(str(index_path))
            self.metadata = load_metadata(metadata_path)
        else:
            self.index = None
            self.metadata = {}
    
    def is_indexed(self) -> bool:
        """Check if index is loaded and ready."""
        return self.index is not None and len(self.metadata) > 0
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for similar images given a text query.
        
        Args:
            query: Text query string
            top_k: Number of results to return
        
        Returns:
            List of tuples (image_path, similarity_score)
        """
        if not self.is_indexed():
            return []
        
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
        
        return results
    
    def reload_index(self):
        """Reload index from disk (useful after re-indexing)."""
        self._load_index()

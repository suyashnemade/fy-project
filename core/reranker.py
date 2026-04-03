"""
Cross-encoder reranking module.
Re-scores FAISS candidates using CLIP's cosine similarity on full forward pass
for improved ranking quality.
"""

import numpy as np
import torch
import clip
from PIL import Image
from pathlib import Path
from typing import List, Tuple
from collections import OrderedDict

from .logger import get_logger
from . import config

logger = get_logger(__name__)

# Maximum number of preprocessed image tensors to cache in the reranker.
_RERANKER_CACHE_MAX = 100


class CLIPReranker:
    """Re-ranks search candidates using CLIP cosine similarity for better precision."""
    
    def __init__(self, model, preprocess, device: str):
        self.model = model
        self.preprocess = preprocess
        self.device = device
        # LRU-bounded cache: OrderedDict with oldest-eviction policy
        self._preprocess_cache: OrderedDict = OrderedDict()
    
    def _load_and_preprocess(self, path: str):
        """Load and preprocess an image, with LRU caching (bounded)."""
        if path in self._preprocess_cache:
            # Move to end (most recently used)
            self._preprocess_cache.move_to_end(path)
            return self._preprocess_cache[path]
        try:
            img = Image.open(path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            tensor = self.preprocess(img)
            # Evict oldest if cache is full (LRU policy)
            if len(self._preprocess_cache) >= _RERANKER_CACHE_MAX:
                self._preprocess_cache.popitem(last=False)
            self._preprocess_cache[path] = tensor
            return tensor
        except Exception as e:
            logger.warning(f"Reranker: failed to load {path}: {e}")
            return None
    
    def rerank(
        self, 
        query: str, 
        candidates: List[Tuple[str, float]], 
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Rerank candidates using CLIP cosine similarity (NOT softmax).
        
        Computes image and text embeddings through full CLIP forward pass,
        then uses cosine similarity for scoring — keeping scores in the same
        range as FAISS scores for consistency with feedback boosting.
        """
        if not candidates:
            return []
        
        # Load and preprocess candidate images (in sub-batches to avoid OOM)
        valid_tensors = []
        valid_paths = []
        
        for path, _ in candidates:
            tensor = self._load_and_preprocess(path)
            if tensor is not None:
                valid_tensors.append(tensor)
                valid_paths.append(path)
        
        if not valid_tensors:
            logger.warning("Reranker: no valid images to rerank.")
            return candidates[:top_k]
        
        try:
            with torch.no_grad():
                # Process in sub-batches of 16 to limit memory
                sub_batch_size = 16
                all_image_features = []
                
                for i in range(0, len(valid_tensors), sub_batch_size):
                    batch = torch.stack(valid_tensors[i:i + sub_batch_size]).to(self.device)
                    features = self.model.encode_image(batch)
                    features = features / features.norm(dim=-1, keepdim=True)
                    all_image_features.append(features)
                
                image_features = torch.cat(all_image_features, dim=0)
                
                # Encode query text
                text_tokens = clip.tokenize([query]).to(self.device)
                text_features = self.model.encode_text(text_tokens)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                # Cosine similarity (same scale as FAISS IndexFlatIP scores)
                scores = (image_features @ text_features.T).squeeze(-1)
                scores = scores.cpu().numpy().astype(float)
            
            # Pair paths with cosine scores and sort
            reranked = list(zip(valid_paths, scores.tolist()))
            reranked.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(
                f"Reranked {len(valid_paths)} candidates → "
                f"top: {reranked[0][1]:.4f} ({Path(reranked[0][0]).name})"
            )
            
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return candidates[:top_k]

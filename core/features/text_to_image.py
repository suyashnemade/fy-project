"""
Text-to-Image search feature module.

Handles encoding text queries into CLIP embeddings, searching a FAISS index,
and returning ranked image results. Includes query expansion and embedding caching.
"""

import numpy as np
import faiss
from collections import OrderedDict
from typing import List, Tuple, Optional

from ..logger import get_logger
from .. import config

logger = get_logger(__name__)

# Module-level LRU embedding cache: maps query string → normalized embedding vector.
# Uses OrderedDict to maintain access order for true LRU eviction.
_embedding_cache: OrderedDict = OrderedDict()
_CACHE_MAX_SIZE = config.EMBEDDING_CACHE_SIZE


def _cache_get(query: str) -> Optional[np.ndarray]:
    """Retrieve a cached text embedding (LRU: moves to most-recently-used)."""
    if query in _embedding_cache:
        _embedding_cache.move_to_end(query)
        return _embedding_cache[query]
    return None


def _cache_put(query: str, embedding: np.ndarray):
    """Store a text embedding. Evicts least-recently-used entry if cache is full."""
    if query in _embedding_cache:
        _embedding_cache.move_to_end(query)
    elif len(_embedding_cache) >= _CACHE_MAX_SIZE:
        _embedding_cache.popitem(last=False)  # Evict LRU (front of OrderedDict)
    _embedding_cache[query] = embedding


def clear_cache():
    """Clear the text embedding cache (useful after model changes)."""
    _embedding_cache.clear()
    logger.debug("Text embedding cache cleared.")


def expand_query_embedding(clip_model, query: str) -> np.ndarray:
    """
    Encode query using multiple prompt templates and average them
    for a richer, more robust text representation.

    Uses batch encoding for efficiency (single forward pass for all templates).

    Args:
        clip_model: CLIPModel instance
        query: Raw text query string

    Returns:
        Normalized embedding vector as numpy array (1D, shape=(dim,))
    """
    import clip as clip_module
    import torch

    templates = [
        f"a photo of {query}",
        f"an image showing {query}",
        f"a picture depicting {query}",
    ]

    with torch.no_grad():
        tokens = clip_module.tokenize(templates).to(clip_model.device)
        features = clip_model.model.encode_text(tokens)
        features = features / features.norm(dim=-1, keepdim=True)
        avg = features.mean(dim=0, keepdim=True)
        avg = avg / avg.norm(dim=-1, keepdim=True)

    result = avg.cpu().numpy().flatten()
    logger.debug(f"Query expansion: batch-encoded {len(templates)} templates")
    return result


def encode_query(clip_model, query: str, use_expansion: bool = True) -> np.ndarray:
    """
    Encode a text query into a CLIP embedding vector, with caching.

    Args:
        clip_model: CLIPModel instance
        query: Text query string
        use_expansion: Whether to use multi-template query expansion

    Returns:
        Normalized embedding vector as numpy array (1D)
    """
    # Check cache first
    cache_key = f"exp:{query}" if use_expansion else f"raw:{query}"
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.debug(f"Text embedding cache hit for: '{query}'")
        return cached

    # Encode
    if use_expansion:
        embedding = expand_query_embedding(clip_model, query)
    else:
        prompted_query = f"a photo of {query}"
        embedding = clip_model.encode_text(prompted_query)

    # Cache and return
    _cache_put(cache_key, embedding)
    return embedding


def text_search(
    clip_model,
    index: faiss.Index,
    metadata: dict,
    query: str,
    top_k: int = 10,
    feedback_store=None,
) -> List[Tuple[str, float]]:
    """
    Search for images matching a text query.

    Pipeline:
        1. Encode query text → CLIP embedding (with optional expansion + caching)
        2. FAISS nearest neighbor search
        3. Optional user relevance feedback score boosting

    Args:
        clip_model: CLIPModel instance
        index: FAISS index containing image embeddings
        metadata: Dict mapping str(index_id) → image_path
        query: Text query string
        top_k: Number of results to return
        feedback_store: Optional FeedbackStore instance

    Returns:
        List of (image_path, similarity_score) tuples, sorted by relevance
    """
    if index is None or metadata is None or len(metadata) == 0:
        logger.warning("text_search: no index loaded.")
        return []

    if not query or not query.strip():
        logger.warning("text_search: empty query.")
        return []

    # Validate query length (CLIP token limit)
    max_chars = config.MAX_QUERY_LENGTH * 4
    if len(query) > max_chars:
        logger.warning(f"Query too long ({len(query)} chars). Truncating to {max_chars}.")
        query = query[:max_chars]

    try:
        faiss_k = min(top_k, index.ntotal)

        # Encode query (with cache)
        query_embedding = encode_query(
            clip_model, query,
            use_expansion=config.ENABLE_QUERY_EXPANSION
        )
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

        # FAISS search
        scores, indices = index.search(query_embedding, faiss_k)

        # Map indices to image paths
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            image_id = str(idx)
            if image_id in metadata:
                results.append((metadata[image_id], float(score)))

        logger.info(f"FAISS text search for '{query}' returned {len(results)} results.")

        # Apply user relevance feedback boost if available
        if feedback_store:
            results = feedback_store.apply_feedback_boost(results, query)

        return results

    except Exception as e:
        logger.error(f"text_search failed: {e}")
        return []

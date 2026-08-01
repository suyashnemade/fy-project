"""
Image-to-Image search feature module.

Handles encoding a query image into a CLIP embedding and searching a FAISS index
for visually similar images.
"""

import numpy as np
import faiss
from PIL import Image
from typing import List, Tuple

from ..logger import get_logger
from .. import config

logger = get_logger(__name__)


def image_search(
    clip_model,
    index: faiss.Index,
    metadata: dict,
    query_image: Image.Image,
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """
    Search for images visually similar to a query image.

    Pipeline:
        1. Convert query image to RGB
        2. Encode via CLIP image encoder → normalized embedding
        3. FAISS inner-product search

    Args:
        clip_model: CLIPModel instance
        index: FAISS index containing image embeddings
        metadata: Dict mapping str(index_id) → image_path
        query_image: PIL Image object to use as the search query
        top_k: Number of results to return

    Returns:
        List of (image_path, similarity_score) tuples, sorted by relevance
    """
    if index is None or metadata is None or len(metadata) == 0:
        logger.warning("image_search: no index loaded.")
        return []

    try:
        # Convert to RGB if needed
        if query_image.mode != 'RGB':
            query_image = query_image.convert('RGB')

        # Encode query image (returns normalized embedding)
        query_embedding = clip_model.encode_image(query_image)
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

        # FAISS search
        k = min(top_k, index.ntotal)
        scores, indices = index.search(query_embedding, k)

        # Map indices to image paths
        results: List[Tuple[str, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            image_id = str(idx)
            if image_id in metadata:
                results.append((metadata[image_id], float(score)))

        logger.info(f"Image search returned {len(results)} results.")

        return results

    except Exception as e:
        logger.error(f"image_search failed: {e}")
        return []

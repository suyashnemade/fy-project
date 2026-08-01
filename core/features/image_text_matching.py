"""
Image-Text Matching feature module.

Computes cosine similarity between images and text descriptions using CLIP.
This is the core "how well does this image match this text?" functionality,
useful for:
    - Verifying search result relevance
    - Filtering results by a minimum similarity threshold

The similarity score ranges from -1 to 1 (cosine similarity), where:
    - ~0.25-0.35 = strong match
    - ~0.18-0.25 = moderate match
    - < 0.18 = weak match
"""

import numpy as np
import torch
import clip
from PIL import Image
from typing import List, Tuple

from ..logger import get_logger

logger = get_logger(__name__)


def compute_similarity(
    clip_model,
    image: Image.Image,
    text: str,
) -> float:
    """
    Compute cosine similarity between a single image and text description.

    This measures how semantically related the image content is to the text.
    Uses CLIP's joint embedding space: both image and text are encoded into
    the same vector space, and their cosine similarity indicates relevance.

    Args:
        clip_model: CLIPModel instance (with .model, .preprocess, .device)
        image: PIL Image object
        text: Text description string

    Returns:
        Cosine similarity score (float, typically in range 0.15-0.35 for matches)
    """
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')

        with torch.no_grad():
            # Encode image
            image_tensor = clip_model.preprocess(image).unsqueeze(0).to(clip_model.device)
            image_features = clip_model.model.encode_image(image_tensor)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Encode text
            text_tokens = clip.tokenize([text]).to(clip_model.device)
            text_features = clip_model.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Cosine similarity
            similarity = float((image_features @ text_features.T).item())

        logger.debug(f"Image-text similarity: {similarity:.4f} for text='{text[:50]}'")
        return similarity

    except Exception as e:
        logger.error(f"compute_similarity failed: {e}")
        return 0.0

"""
Image-Text Matching feature module.

Computes cosine similarity between images and text descriptions using CLIP.
This is the core "how well does this image match this text?" functionality,
useful for:
    - Verifying search result relevance
    - Filtering results by a minimum similarity threshold
    - Comparing multiple captions against a single image
    - Building ranking/scoring pipelines

The similarity score ranges from -1 to 1 (cosine similarity), where:
    - ~0.25-0.35 = strong match
    - ~0.18-0.25 = moderate match
    - < 0.18 = weak match
"""

import numpy as np
import torch
import clip
from PIL import Image
from typing import List, Tuple, Optional

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


def batch_match(
    clip_model,
    images: List[Image.Image],
    texts: List[str],
) -> np.ndarray:
    """
    Compute pairwise cosine similarities between a batch of images and texts.

    Returns a matrix where entry [i, j] is the similarity between image[i] and text[j].
    This is efficient because it encodes all images and texts in batches rather than
    one-by-one.

    Args:
        clip_model: CLIPModel instance
        images: List of PIL Image objects
        texts: List of text description strings

    Returns:
        np.ndarray of shape (len(images), len(texts)) with cosine similarity scores
    """
    if not images or not texts:
        logger.warning("batch_match: empty images or texts list.")
        return np.array([])

    try:
        # Convert images to RGB
        rgb_images = []
        for img in images:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            rgb_images.append(img)

        with torch.no_grad():
            # Batch encode images
            image_tensors = torch.stack(
                [clip_model.preprocess(img) for img in rgb_images]
            ).to(clip_model.device)
            image_features = clip_model.model.encode_image(image_tensors)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Batch encode texts
            text_tokens = clip.tokenize(texts).to(clip_model.device)
            text_features = clip_model.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Pairwise cosine similarity matrix: (N_images, N_texts)
            similarity_matrix = (image_features @ text_features.T).cpu().numpy()

        logger.info(
            f"batch_match: computed {len(images)}×{len(texts)} similarity matrix"
        )
        return similarity_matrix

    except Exception as e:
        logger.error(f"batch_match failed: {e}")
        return np.array([])


def rank_texts_for_image(
    clip_model,
    image: Image.Image,
    texts: List[str],
) -> List[Tuple[str, float]]:
    """
    Rank multiple text descriptions by their relevance to a single image.

    Useful for finding which caption best describes an image, or for
    multi-label classification tasks.

    Args:
        clip_model: CLIPModel instance
        image: PIL Image object
        texts: List of candidate text descriptions

    Returns:
        List of (text, score) tuples sorted by descending similarity
    """
    if not texts:
        return []

    scores = batch_match(clip_model, [image], texts)
    if scores.size == 0:
        return []

    # scores shape: (1, N_texts) → flatten to (N_texts,)
    scores_flat = scores[0]
    ranked = sorted(
        zip(texts, scores_flat.tolist()),
        key=lambda x: x[1],
        reverse=True
    )
    return ranked


def rank_images_for_text(
    clip_model,
    images: List[Image.Image],
    text: str,
) -> List[Tuple[int, float]]:
    """
    Rank multiple images by their relevance to a single text query.

    Args:
        clip_model: CLIPModel instance
        images: List of PIL Image objects
        text: Text query string

    Returns:
        List of (image_index, score) tuples sorted by descending similarity
    """
    if not images:
        return []

    scores = batch_match(clip_model, images, [text])
    if scores.size == 0:
        return []

    # scores shape: (N_images, 1) → flatten
    scores_flat = scores[:, 0]
    ranked = sorted(
        enumerate(scores_flat.tolist()),
        key=lambda x: x[1],
        reverse=True
    )
    return ranked

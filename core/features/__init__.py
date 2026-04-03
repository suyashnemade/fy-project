"""
Feature modules for semantic image search.

Each module provides independent, reusable search functionality:
    - text_to_image: Text query → image retrieval
    - image_to_image: Image query → similar image retrieval
    - image_text_matching: Compute image-text similarity scores
    - video_search: Search video frames by text query
"""

from .text_to_image import text_search
from .image_to_image import image_search
from .image_text_matching import compute_similarity, batch_match
from .video_search import search_video

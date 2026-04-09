"""
Semantic search orchestrator using FAISS index.

This module serves as the main entry point and backward-compatible router for
all search functionality. It delegates actual search logic to the feature modules
in core/features/ while maintaining the same public API that the desktop app and
Streamlit app depend on.

Supports: text search, image search, video search, image-text matching,
query expansion, reranking, and feedback integration.
"""

import logging
import numpy as np
import faiss
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from PIL import Image

from .clip_model import CLIPModel
from .utils import load_metadata
from .logger import get_logger
from . import config

# Feature modules
from .features.text_to_image import text_search
from .features.image_to_image import image_search
from .features.image_text_matching import compute_similarity, batch_match
from .features.video_search import search_video

logger = get_logger(__name__)


class ImageSearcher:
    """
    Main search orchestrator for semantic image retrieval.

    Routes search requests to the appropriate feature module while managing
    shared resources (FAISS index, metadata, reranker, feedback store).

    This class maintains backward compatibility — all existing method signatures
    are preserved. The desktop app and Streamlit app can use this without changes.
    """

    def __init__(self, clip_model: CLIPModel):
        """
        Initialize searcher with CLIP model.

        Loads the FAISS index, initializes the reranker and feedback store.

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

    def search(self, query: str, top_k: int = config.DEFAULT_TOP_K) -> List[Tuple[str, float]]:
        """
        Search for similar images given a text query.

        Delegates to core.features.text_to_image.text_search() which handles:
        query expansion, FAISS retrieval, optional reranking, and feedback boosting.

        Args:
            query: Text query string
            top_k: Number of results to return

        Returns:
            List of tuples (image_path, similarity_score)
        """
        if not self.is_indexed():
            logger.warning("Attempted search but no index is loaded.")
            return []

        return text_search(
            clip_model=self.clip_model,
            index=self.index,
            metadata=self.metadata,
            query=query,
            top_k=top_k,
            reranker=self._reranker,
            feedback_store=self._feedback_store,
        )

    def reload_index(self):
        """Reload index from disk (useful after re-indexing)."""
        logger.info("Reloading index...")
        self._load_index()

    def search_by_image(
        self, query_image: Image.Image, top_k: int = config.DEFAULT_TOP_K
    ) -> List[Tuple[str, float]]:
        """
        Search for similar images given a query image (reverse image search).

        Delegates to core.features.image_to_image.image_search().
        Now includes feedback boosting (Bug Fix: was previously missing).

        Args:
            query_image: PIL Image object to use as the search query
            top_k: Number of results to return

        Returns:
            List of tuples (image_path, similarity_score)
        """
        if not self.is_indexed():
            logger.warning("Attempted image search but no index is loaded.")
            return []

        return image_search(
            clip_model=self.clip_model,
            index=self.index,
            metadata=self.metadata,
            query_image=query_image,
            top_k=top_k,
            feedback_store=self._feedback_store,
        )

    # --- New feature methods (added by refactor) ---

    def search_video(
        self,
        video_path: str,
        query: str,
        fps: float = None,
        top_k: int = 5,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> list:
        """
        Search a video for frames matching a text query.

        Extracts frames at configurable FPS, encodes with CLIP, and returns
        the top matching frames with timestamps.

        Args:
            video_path: Path to the video file
            query: Text query describing what to find
            fps: Frame extraction rate (default: config.VIDEO_FRAME_FPS)
            top_k: Number of top matching frames to return
            is_cancelled: Optional callback to check for user cancellation

        Returns:
            List of (frame_image, timestamp_seconds, similarity_score) tuples
        """
        if fps is None:
            fps = config.VIDEO_FRAME_FPS

        return search_video(
            clip_model=self.clip_model,
            video_path=video_path,
            query=query,
            fps=fps,
            top_k=top_k,
            max_frames=config.VIDEO_MAX_FRAMES,
            is_cancelled=is_cancelled,
        )

    def index_video(
        self,
        video_path: str,
        fps: float = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> dict:
        from .features.video_search import encode_video
        if fps is None:
            fps = config.VIDEO_FRAME_FPS
        return encode_video(
            clip_model=self.clip_model,
            video_path=video_path,
            fps=fps,
            max_frames=config.VIDEO_MAX_FRAMES,
            is_cancelled=is_cancelled,
        )

    def query_indexed_video(
        self,
        video_index: dict,
        query: str,
        top_k: int = 5,
    ) -> list:
        from .features.video_search import query_video_index
        return query_video_index(
            clip_model=self.clip_model,
            video_index=video_index,
            query=query,
            top_k=top_k,
        )

    def compute_image_text_similarity(
        self,
        image: Image.Image,
        text: str,
    ) -> float:
        """
        Compute cosine similarity between an image and text description.

        Useful for verifying how well an image matches a query, or for
        building filtering/scoring pipelines.

        Args:
            image: PIL Image object
            text: Text description string

        Returns:
            Cosine similarity score (float, typically 0.15-0.35 for matches)
        """
        return compute_similarity(
            clip_model=self.clip_model,
            image=image,
            text=text,
        )

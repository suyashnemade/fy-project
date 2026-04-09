"""
Shared application state and FastAPI dependency injection.

Manages singleton instances of CLIPModel, ImageSearcher, and ImageIndexer.
These are heavy objects (GPU/CPU model, FAISS index) that must be created
once at startup and shared across all request handlers.
"""

from typing import Optional

from core.clip_model import CLIPModel
from core.search import ImageSearcher
from core.indexer import ImageIndexer


class AppState:
    """
    Holds shared application state as singletons.

    Initialized once during FastAPI lifespan startup.
    Injected into endpoints via FastAPI's Depends() mechanism.
    """

    def __init__(self):
        self.clip_model: Optional[CLIPModel] = None
        self.searcher: Optional[ImageSearcher] = None
        self.indexer: Optional[ImageIndexer] = None
        self.is_ready: bool = False
        self.stop_requested: bool = False
        self.video_index: Optional[dict] = None

    def initialize(self):
        """
        Load CLIP model and initialize searcher + indexer.

        Called once at application startup. This is the slow step
        (~5-15 seconds depending on hardware and whether the model
        needs downloading).
        """
        self.clip_model = CLIPModel(device=None)
        self.indexer = ImageIndexer(self.clip_model)
        self.searcher = ImageSearcher(self.clip_model)
        self.is_ready = True

    def reload_index(self):
        """Reload FAISS index from disk after re-indexing."""
        if self.searcher:
            self.searcher.reload_index()


# ── Global singleton ────────────────────────────────────────────────────────

app_state = AppState()


# ── Dependency functions for FastAPI Depends() ──────────────────────────────

def get_app_state() -> AppState:
    """Inject the full application state."""
    return app_state


def get_searcher() -> ImageSearcher:
    """Inject the ImageSearcher instance."""
    if not app_state.is_ready or app_state.searcher is None:
        raise RuntimeError(
            "Models are not loaded yet. Please wait for startup to complete."
        )
    return app_state.searcher


def get_indexer() -> ImageIndexer:
    """Inject the ImageIndexer instance."""
    if not app_state.is_ready or app_state.indexer is None:
        raise RuntimeError(
            "Models are not loaded yet. Please wait for startup to complete."
        )
    return app_state.indexer


def get_clip_model() -> CLIPModel:
    """Inject the CLIPModel instance."""
    if not app_state.is_ready or app_state.clip_model is None:
        raise RuntimeError(
            "Models are not loaded yet. Please wait for startup to complete."
        )
    return app_state.clip_model

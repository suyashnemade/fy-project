"""
Unit tests for core/config.py — verify configuration values are sane.
"""

import pytest
from pathlib import Path

from core import config


class TestConfig:
    """Tests for centralized configuration."""

    def test_app_dir_exists(self):
        """APP_DIR should resolve to the project root."""
        assert config.APP_DIR.exists()
        assert config.APP_DIR.is_dir()

    def test_storage_dir_is_under_app_dir(self):
        """STORAGE_DIR should be a subdirectory of APP_DIR."""
        assert str(config.STORAGE_DIR).startswith(str(config.APP_DIR))

    def test_model_name_is_set(self):
        """MODEL_NAME should be a non-empty string."""
        assert isinstance(config.MODEL_NAME, str)
        assert len(config.MODEL_NAME) > 0

    def test_embedding_dimension(self):
        """EMBEDDING_DIM should be 512 for ViT-B/32."""
        assert config.EMBEDDING_DIM == 512

    def test_batch_size_positive(self):
        """BATCH_SIZE must be a positive integer."""
        assert isinstance(config.BATCH_SIZE, int)
        assert config.BATCH_SIZE > 0

    def test_supported_extensions_non_empty(self):
        """SUPPORTED_EXTENSIONS should contain at least .jpg and .png."""
        assert '.jpg' in config.SUPPORTED_EXTENSIONS
        assert '.png' in config.SUPPORTED_EXTENSIONS

    def test_max_query_length(self):
        """MAX_QUERY_LENGTH should be 77 (CLIP token limit)."""
        assert config.MAX_QUERY_LENGTH == 77

    def test_default_top_k(self):
        """DEFAULT_TOP_K should be a positive integer."""
        assert isinstance(config.DEFAULT_TOP_K, int)
        assert config.DEFAULT_TOP_K > 0

    def test_clip_model_path_default_none(self):
        """CLIP_MODEL_PATH should default to None."""
        assert config.CLIP_MODEL_PATH is None

    def test_logs_dir_is_under_app_dir(self):
        """LOGS_DIR should be a subdirectory of APP_DIR."""
        assert str(config.LOGS_DIR).startswith(str(config.APP_DIR))

    def test_paths_are_path_objects(self):
        """All path configs should be pathlib.Path instances."""
        assert isinstance(config.STORAGE_DIR, Path)
        assert isinstance(config.EMBEDDINGS_PATH, Path)
        assert isinstance(config.METADATA_PATH, Path)
        assert isinstance(config.FAISS_INDEX_PATH, Path)
        assert isinstance(config.LOGS_DIR, Path)
        assert isinstance(config.LOG_FILE, Path)

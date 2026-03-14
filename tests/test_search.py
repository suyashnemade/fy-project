"""
Unit tests for core/search.py — text search and image-to-image search.
"""

import pytest
import json
import numpy as np
import faiss
from pathlib import Path
from PIL import Image

from core.clip_model import CLIPModel
from core.indexer import ImageIndexer
from core.search import ImageSearcher
from core import config


# --------------- Fixtures ---------------

@pytest.fixture(scope="module")
def clip_model():
    """Load CLIPModel once and reuse across tests."""
    return CLIPModel(device="cpu")


@pytest.fixture(scope="module")
def indexed_data(clip_model, tmp_path_factory):
    """
    Create a temporary directory with dummy images, index them, and return
    the searcher + image dir path. Runs once per module.
    """
    img_dir = tmp_path_factory.mktemp("search_images")
    for i in range(6):
        img = Image.new("RGB", (224, 224), color=(i * 40, i * 20, 255 - i * 30))
        img.save(img_dir / f"img_{i}.jpg")

    indexer = ImageIndexer(clip_model)
    indexer.index_directory(str(img_dir))

    searcher = ImageSearcher(clip_model)
    return searcher, img_dir


# --------------- Tests ---------------

class TestImageSearcher:
    """Tests for ImageSearcher text and image search."""

    def test_is_indexed_after_indexing(self, indexed_data):
        """Searcher should report is_indexed=True after indexing."""
        searcher, _ = indexed_data
        assert searcher.is_indexed()

    def test_text_search_returns_results(self, indexed_data):
        """Text search should return a non-empty list of results."""
        searcher, _ = indexed_data
        results = searcher.search("a colorful image", top_k=5)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_text_search_result_format(self, indexed_data):
        """Each result should be a (path, score) tuple."""
        searcher, _ = indexed_data
        results = searcher.search("test image", top_k=3)
        for path, score in results:
            assert isinstance(path, str)
            assert isinstance(score, float)

    def test_text_search_paths_exist(self, indexed_data):
        """Returned paths should point to real files."""
        searcher, _ = indexed_data
        results = searcher.search("some image", top_k=3)
        for path, score in results:
            assert Path(path).exists()

    def test_text_search_respects_top_k(self, indexed_data):
        """Number of results should not exceed top_k."""
        searcher, _ = indexed_data
        results = searcher.search("anything", top_k=2)
        assert len(results) <= 2

    def test_empty_query_returns_empty(self, indexed_data):
        """An empty query should return no results."""
        searcher, _ = indexed_data
        results = searcher.search("", top_k=5)
        assert results == []

    def test_image_search_returns_results(self, indexed_data):
        """Image-to-image search should return a non-empty list."""
        searcher, _ = indexed_data
        query_image = Image.new("RGB", (224, 224), color=(100, 50, 200))
        results = searcher.search_by_image(query_image, top_k=5)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_image_search_result_format(self, indexed_data):
        """Each image search result should be a (path, score) tuple."""
        searcher, _ = indexed_data
        query_image = Image.new("RGB", (224, 224), color=(50, 50, 50))
        results = searcher.search_by_image(query_image, top_k=3)
        for path, score in results:
            assert isinstance(path, str)
            assert isinstance(score, float)

    def test_image_search_respects_top_k(self, indexed_data):
        """Image search should not return more than top_k results."""
        searcher, _ = indexed_data
        query_image = Image.new("RGB", (224, 224), color=(0, 255, 0))
        results = searcher.search_by_image(query_image, top_k=2)
        assert len(results) <= 2

    def test_reload_index(self, indexed_data):
        """reload_index should not raise and should keep the index valid."""
        searcher, _ = indexed_data
        searcher.reload_index()
        assert searcher.is_indexed()

    def test_search_no_index_returns_empty(self, clip_model):
        """Searcher with no index on disk should return empty results."""
        # Create a searcher that points to missing index
        searcher = ImageSearcher(clip_model)
        searcher.index = None
        searcher.metadata = {}
        results = searcher.search("hello", top_k=5)
        assert results == []

"""
Unit tests for core/indexer.py — incremental indexing and FAISS index building.
"""

import pytest
import shutil
import json
import numpy as np
import faiss
from pathlib import Path
from PIL import Image

from core.clip_model import CLIPModel
from core.indexer import ImageIndexer
from core import config


# --------------- Fixtures ---------------

@pytest.fixture(scope="module")
def clip_model():
    """Load CLIPModel once and reuse across tests."""
    return CLIPModel(device="cpu")


@pytest.fixture
def temp_image_dir(tmp_path):
    """Create a temporary directory with dummy images."""
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    for i in range(5):
        img = Image.new("RGB", (224, 224), color=(i * 50, i * 30, i * 20))
        img.save(img_dir / f"test_image_{i}.jpg")
    return img_dir


@pytest.fixture
def second_image_dir(tmp_path):
    """Create a second temporary directory with different dummy images."""
    img_dir = tmp_path / "images2"
    img_dir.mkdir()
    for i in range(3):
        img = Image.new("RGB", (224, 224), color=(200 - i * 30, i * 60, 100))
        img.save(img_dir / f"second_image_{i}.png")
    return img_dir


@pytest.fixture(autouse=True)
def clean_storage():
    """Remove storage files before and after each test."""
    paths = [config.EMBEDDINGS_PATH, config.METADATA_PATH, config.FAISS_INDEX_PATH, config.MODEL_FINGERPRINT_PATH]
    for p in paths:
        if p.exists():
            p.unlink()
    yield
    for p in paths:
        if p.exists():
            p.unlink()


# --------------- Tests ---------------

class TestImageIndexer:
    """Tests for ImageIndexer."""

    def test_index_directory_creates_files(self, clip_model, temp_image_dir):
        """Indexing should create embeddings.npy, metadata.json, and faiss.index."""
        indexer = ImageIndexer(clip_model)
        successful, failed = indexer.index_directory(str(temp_image_dir))

        assert successful == 5
        assert failed == 0
        assert config.EMBEDDINGS_PATH.exists()
        assert config.METADATA_PATH.exists()
        assert config.FAISS_INDEX_PATH.exists()

    def test_metadata_mapping_is_correct(self, clip_model, temp_image_dir):
        """metadata.json should map string IDs to absolute image paths."""
        indexer = ImageIndexer(clip_model)
        indexer.index_directory(str(temp_image_dir))

        with open(config.METADATA_PATH, "r") as f:
            metadata = json.load(f)

        assert len(metadata) == 5
        for key, path in metadata.items():
            assert key.isdigit()
            assert Path(path).exists()

    def test_faiss_index_has_correct_count(self, clip_model, temp_image_dir):
        """FAISS index should contain exactly as many vectors as images indexed."""
        indexer = ImageIndexer(clip_model)
        indexer.index_directory(str(temp_image_dir))

        index = faiss.read_index(str(config.FAISS_INDEX_PATH))
        assert index.ntotal == 5

    def test_embeddings_shape(self, clip_model, temp_image_dir):
        """embeddings.npy should have shape (N, 512)."""
        indexer = ImageIndexer(clip_model)
        indexer.index_directory(str(temp_image_dir))

        embeddings = np.load(config.EMBEDDINGS_PATH)
        assert embeddings.shape == (5, config.EMBEDDING_DIM)

    def test_incremental_indexing_skips_existing(self, clip_model, temp_image_dir):
        """Running index_directory twice on the same dir should not add duplicates."""
        indexer = ImageIndexer(clip_model)

        s1, _ = indexer.index_directory(str(temp_image_dir))
        assert s1 == 5

        s2, _ = indexer.index_directory(str(temp_image_dir))
        assert s2 == 0  # all images already indexed

        # Total should still be 5
        embeddings = np.load(config.EMBEDDINGS_PATH)
        assert embeddings.shape[0] == 5

        index = faiss.read_index(str(config.FAISS_INDEX_PATH))
        assert index.ntotal == 5

    def test_multi_directory_merging(self, clip_model, temp_image_dir, second_image_dir):
        """Indexing two directories should merge them into one index."""
        indexer = ImageIndexer(clip_model)

        s1, _ = indexer.index_directory(str(temp_image_dir))
        assert s1 == 5

        s2, _ = indexer.index_directory(str(second_image_dir))
        assert s2 == 3

        # Total should be 8
        embeddings = np.load(config.EMBEDDINGS_PATH)
        assert embeddings.shape[0] == 8

        index = faiss.read_index(str(config.FAISS_INDEX_PATH))
        assert index.ntotal == 8

        with open(config.METADATA_PATH, "r") as f:
            metadata = json.load(f)
        assert len(metadata) == 8

    def test_empty_directory_returns_zero(self, clip_model, tmp_path):
        """Indexing an empty directory should return (0, 0)."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        indexer = ImageIndexer(clip_model)
        successful, failed = indexer.index_directory(str(empty_dir))
        assert successful == 0
        assert failed == 0

    def test_progress_callback_is_called(self, clip_model, temp_image_dir):
        """progress_callback should be invoked during indexing."""
        indexer = ImageIndexer(clip_model)
        callback_calls = []

        def track_progress(current, total):
            callback_calls.append((current, total))

        indexer.index_directory(str(temp_image_dir), progress_callback=track_progress)
        assert len(callback_calls) > 0

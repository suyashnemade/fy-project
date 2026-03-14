"""
Unit tests for core/clip_model.py — CLIP model encoding.
"""

import pytest
import numpy as np
from PIL import Image

from core.clip_model import CLIPModel
from core import config


# Shared fixture: load the model once for all tests in this module
@pytest.fixture(scope="module")
def clip_model():
    """Load CLIPModel once and reuse across tests."""
    return CLIPModel(device="cpu")


@pytest.fixture
def dummy_image():
    """Create a simple 224×224 RGB test image."""
    return Image.new("RGB", (224, 224), color=(128, 64, 32))


class TestCLIPModel:
    """Tests for CLIPModel encoding methods."""

    def test_model_loads_successfully(self, clip_model):
        """Model and preprocessor should not be None after init."""
        assert clip_model.model is not None
        assert clip_model.preprocess is not None

    def test_encode_image_returns_512_dim(self, clip_model, dummy_image):
        """encode_image should return a 1-D array of shape (512,)."""
        embedding = clip_model.encode_image(dummy_image)
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (config.EMBEDDING_DIM,)

    def test_encode_image_is_normalized(self, clip_model, dummy_image):
        """Image embedding should be L2-normalized (norm ≈ 1.0)."""
        embedding = clip_model.encode_image(dummy_image)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-4

    def test_encode_text_returns_512_dim(self, clip_model):
        """encode_text should return a 1-D array of shape (512,)."""
        embedding = clip_model.encode_text("a photo of a cat")
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (config.EMBEDDING_DIM,)

    def test_encode_text_is_normalized(self, clip_model):
        """Text embedding should be L2-normalized (norm ≈ 1.0)."""
        embedding = clip_model.encode_text("hello world")
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-4

    def test_encode_images_batch(self, clip_model, dummy_image):
        """encode_images_batch should return (N, 512) array."""
        images = [dummy_image, dummy_image.copy()]
        embeddings = clip_model.encode_images_batch(images)
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (2, config.EMBEDDING_DIM)

    def test_batch_embeddings_are_normalized(self, clip_model, dummy_image):
        """Each embedding in a batch should be L2-normalized."""
        images = [dummy_image, dummy_image.copy(), dummy_image.copy()]
        embeddings = clip_model.encode_images_batch(images)
        for i in range(len(images)):
            norm = np.linalg.norm(embeddings[i])
            assert abs(norm - 1.0) < 1e-4

    def test_encode_images_batch_empty(self, clip_model):
        """Batch encoding an empty list should return an empty array."""
        embeddings = clip_model.encode_images_batch([])
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.size == 0

    def test_different_texts_produce_different_embeddings(self, clip_model):
        """Two semantically different queries should produce different vectors."""
        e1 = clip_model.encode_text("a dog running in the park")
        e2 = clip_model.encode_text("a skyscraper at night")
        assert not np.allclose(e1, e2, atol=1e-2)

"""
CLIP model wrapper for encoding images and text.
Uses pretrained CLIP ViT-B/32 model.
"""

import logging
import torch
import numpy as np
from PIL import Image
from typing import List
import clip
from pathlib import Path
import os
from concurrent.futures import ThreadPoolExecutor

from .logger import get_logger
from . import config

logger = get_logger(__name__)


class CLIPModel:
    """Wrapper for CLIP model for encoding images and text."""
    
    def __init__(self, device=None):
        """
        Initialize CLIP model.
        
        Args:
            device: torch device (default: 'cpu')
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        
        # Optimize PyTorch CPU threads dynamically
        if self.device == "cpu":
            num_cores = os.cpu_count() or 4
            torch.set_num_threads(num_cores)
            logger.info(f"Optimized PyTorch to safely use {num_cores} native CPU threads.")

        self.model = None
        self.preprocess = None
        self._load_model()
    
    def _load_model(self):
        """Load CLIP model by name (downloads on first run)."""
        try:
            logger.info(f"Loading CLIP model '{config.MODEL_NAME}' on {self.device}...")
            self.model, self.preprocess = clip.load(
                config.MODEL_NAME, device=self.device
            )
            self.model.eval()
            logger.info("CLIP model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise RuntimeError(
                f"Could not load CLIP model '{config.MODEL_NAME}'. "
                f"Check your internet connection if this is your first run.\nDetails: {e}"
            )
    
    def encode_image(self, image: Image.Image) -> np.ndarray:
        """
        Encode a single image into an embedding vector.
        
        Args:
            image: PIL Image object
        
        Returns:
            Normalized embedding vector as numpy array
        """
        with torch.no_grad():
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            image_features = self.model.encode_image(image_tensor)
            # Normalize embeddings
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            return image_features.cpu().numpy().flatten()
            
    def encode_images_batch(self, images: List[Image.Image]) -> np.ndarray:
        """
        Encode a batch of images into embedding vectors.
        This is significantly faster than encoding one by one.
        
        Args:
            images: List of PIL Image objects
        
        Returns:
            Normalized embedding vectors as numpy array of shape (N, dim)
        """
        if not images:
            return np.array([])
            
        def _process_img(img):
            return self.preprocess(img)
            
        with torch.no_grad():
            # Secure multithreading: Parallelize the heavy CPU-bound bounding/scaling
            num_workers = min(len(images), os.cpu_count() or 4)
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                processed_tensors = list(executor.map(_process_img, images))

            # Stack into a single tensor batch and compute
            batch_tensor = torch.stack(processed_tensors).to(self.device)
            
            # Encode batch natively
            image_features = self.model.encode_image(batch_tensor)
            
            # Normalize embeddings along the embedding dimension
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy()
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text into an embedding vector.
        
        Args:
            text: Input text string
        
        Returns:
            Normalized embedding vector as numpy array
        """
        with torch.no_grad():
            text_tokens = clip.tokenize([text]).to(self.device)
            text_features = self.model.encode_text(text_tokens)
            # Normalize embeddings
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            return text_features.cpu().numpy().flatten()

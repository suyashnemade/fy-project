"""
CLIP model wrapper for encoding images and text.
Uses pretrained CLIP ViT-B/32 model.
"""

import torch
import numpy as np
from PIL import Image
import clip


class CLIPModel:
    """Wrapper for CLIP model for encoding images and text."""
    
    def __init__(self, device=None):
        """
        Initialize CLIP model.
        
        Args:
            device: torch device (default: 'cpu')
        """
        if device is None:
            device = 'cpu'
        self.device = device
        self.model = None
        self.preprocess = None
        self._load_model()
    
    def _load_model(self):
        """Load pretrained CLIP ViT-B/32 model."""
        model_name = "ViT-B/32"
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        self.model.eval()
    
    def encode_image(self, image: Image.Image) -> np.ndarray:
        """
        Encode an image into an embedding vector.
        
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

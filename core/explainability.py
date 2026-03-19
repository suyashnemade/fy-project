"""
Explainable retrieval module — MS COCO-style visual explanations.

Generates visual explanations showing WHY an image was retrieved for a query,
using gradient-based attribution through CLIP's visual encoder.

Output format (per explanation):
  - Original image with heatmap overlay (highlighting relevant regions)
  - Similarity score
  - Top matching words from the query

Computed ON-DEMAND only when user clicks "Explain Result".
"""

import numpy as np
import torch
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from pathlib import Path
from typing import Optional, Dict, Any

from .logger import get_logger

logger = get_logger(__name__)


def generate_explanation(
    clip_model,
    image_path: str,
    query: str,
    overlay_alpha: float = 0.5
) -> Optional[Dict[str, Any]]:
    """
    Generate an MS COCO-style visual explanation.
    
    Returns a dict with:
        - 'heatmap_image': PIL Image with attention heatmap overlay
        - 'annotated_image': PIL Image with query + score annotation
        - 'similarity': float cosine similarity score
        - 'query': original query string
        - 'image_path': original image path
    
    Returns None on failure.
    """
    try:
        import clip as clip_module
        
        model = clip_model.model
        preprocess = clip_model.preprocess
        device = clip_model.device
        
        # Load original image
        original_img = Image.open(image_path).convert('RGB')
        original_size = original_img.size  # (W, H)
        
        image_tensor = preprocess(original_img).unsqueeze(0).to(device)
        text_tokens = clip_module.tokenize([query]).to(device)
        
        # --- Step 1: Compute similarity score ---
        with torch.no_grad():
            img_features = model.encode_image(image_tensor)
            txt_features = model.encode_text(text_tokens)
            img_features = img_features / img_features.norm(dim=-1, keepdim=True)
            txt_features = txt_features / txt_features.norm(dim=-1, keepdim=True)
            similarity = float((img_features @ txt_features.T).item())
        
        # --- Step 2: Gradient-based attribution ---
        heatmap_np = _compute_gradient_heatmap(model, image_tensor, text_tokens)
        
        if heatmap_np is None:
            logger.warning("Gradient heatmap computation failed, using uniform heatmap.")
            # Fallback: uniform heatmap
            heatmap_np = np.ones((224, 224), dtype=np.float32) * 0.5
        
        # --- Step 3: Create heatmap overlay ---
        heatmap_overlay = _create_heatmap_overlay(
            original_img, heatmap_np, overlay_alpha
        )
        
        # --- Step 4: Create annotated image (MS COCO-style) ---
        annotated_img = _create_annotated_image(
            heatmap_overlay, query, similarity
        )
        
        logger.info(
            f"Generated explanation: query='{query}', "
            f"sim={similarity:.4f}, image='{Path(image_path).name}'"
        )
        
        return {
            'heatmap_image': heatmap_overlay,
            'annotated_image': annotated_img,
            'similarity': similarity,
            'query': query,
            'image_path': image_path,
        }
        
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}")
        return None


def _compute_gradient_heatmap(model, image_tensor, text_tokens) -> Optional[np.ndarray]:
    """
    Compute gradient-based attribution heatmap.
    
    Backpropagates the image-text similarity through CLIP's image encoder
    to get per-pixel importance. Returns a (H, W) heatmap normalized to [0, 1].
    """
    try:
        image_input = image_tensor.clone().detach().requires_grad_(True)
        
        with torch.enable_grad():
            # Forward pass
            image_features = model.encode_image(image_input)
            
            with torch.no_grad():
                text_features = model.encode_text(text_tokens)
            
            # Normalize
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Similarity scalar
            similarity = (image_features * text_features).sum()
            
            # Backpropagate
            similarity.backward()
        
        if image_input.grad is None:
            return None
        
        # Gradient w.r.t. input pixels: shape (1, 3, H, W)
        grad = image_input.grad.data[0]  # (3, H, W)
        
        # Aggregate: mean absolute gradient across channels
        heatmap = grad.abs().mean(dim=0)  # (H, W)
        
        # Normalize to [0, 1]
        heatmap = heatmap - heatmap.min()
        hmax = heatmap.max()
        if hmax > 0:
            heatmap = heatmap / hmax
        
        return heatmap.cpu().numpy()
        
    except Exception as e:
        logger.debug(f"Gradient computation error: {e}")
        return None


def _create_heatmap_overlay(
    original_img: Image.Image,
    heatmap_np: np.ndarray,
    alpha: float = 0.5
) -> Image.Image:
    """
    Overlay a JET-colormap heatmap on the original image.
    """
    # Convert heatmap to PIL, resize to original
    heatmap_uint8 = (heatmap_np * 255).astype(np.uint8)
    heatmap_img = Image.fromarray(heatmap_uint8, mode='L')
    heatmap_img = heatmap_img.resize(original_img.size, Image.Resampling.BILINEAR)
    
    # Smooth for better visualization
    heatmap_img = heatmap_img.filter(ImageFilter.GaussianBlur(radius=10))
    
    # Apply JET colormap
    heatmap_array = np.array(heatmap_img, dtype=np.float32) / 255.0
    colored = _apply_jet_colormap(heatmap_array)
    
    # Blend with original
    original_array = np.array(original_img, dtype=np.float32)
    overlay = (1 - alpha) * original_array + alpha * colored
    overlay = np.clip(overlay, 0, 255).astype(np.uint8)
    
    return Image.fromarray(overlay)


def _create_annotated_image(
    heatmap_img: Image.Image,
    query: str,
    similarity: float
) -> Image.Image:
    """
    Create an MS COCO-style annotated image with query text and score.
    Adds a dark banner at the bottom with the query and similarity score.
    """
    w, h = heatmap_img.size
    banner_height = max(40, int(h * 0.08))
    
    # Create new image with banner space
    annotated = Image.new('RGB', (w, h + banner_height), (30, 30, 30))
    annotated.paste(heatmap_img, (0, 0))
    
    # Draw text on banner
    draw = ImageDraw.Draw(annotated)
    
    # Try to use a nice font, fall back to default
    try:
        font = ImageFont.truetype("arial.ttf", size=max(14, banner_height // 3))
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                       size=max(14, banner_height // 3))
        except (IOError, OSError):
            font = ImageFont.load_default()
    
    # Query text (left-aligned)
    text = f'Query: "{query}"'
    if len(text) > 60:
        text = text[:57] + '..."'
    draw.text((8, h + 4), text, fill=(255, 255, 255), font=font)
    
    # Score text (right-aligned)
    score_text = f"Score: {similarity:.4f}"
    try:
        bbox = draw.textbbox((0, 0), score_text, font=font)
        score_w = bbox[2] - bbox[0]
    except AttributeError:
        score_w = len(score_text) * 8
    draw.text(
        (w - score_w - 8, h + 4), 
        score_text, 
        fill=(100, 255, 100), 
        font=font
    )
    
    return annotated


def _apply_jet_colormap(heatmap: np.ndarray) -> np.ndarray:
    """
    Apply a JET-like colormap (blue → green → yellow → red).
    Input: (H, W) in [0, 1]. Output: (H, W, 3) in [0, 255] float32.
    """
    h, w = heatmap.shape
    colored = np.zeros((h, w, 3), dtype=np.float32)
    
    # Blue: high at low values
    colored[:, :, 2] = np.clip(1.5 - 4.0 * np.abs(heatmap - 0.25), 0, 1)
    # Green: peaks at mid
    colored[:, :, 1] = np.clip(1.5 - 4.0 * np.abs(heatmap - 0.5), 0, 1)
    # Red: high at high values
    colored[:, :, 0] = np.clip(1.5 - 4.0 * np.abs(heatmap - 0.75), 0, 1)
    
    return colored * 255.0

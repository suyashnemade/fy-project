"""
Fine-tune CLIP on Flickr30k dataset.

This script fine-tunes a CLIP model on image-caption pairs from Flickr30k
using symmetric contrastive loss. It is NOT integrated into the main application
and should be run standalone.

Usage:
    python fine_tuning/fine_tune_clip.py --dataset_dir data/flickr30_data --epochs 4

Requirements (additional to main project):
    pip install transformers datasets

DO NOT auto-execute this script. It requires GPU and significant compute time.
"""

import os
import sys
import csv
import argparse
import logging
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Flickr30kDataset(Dataset):
    """
    Dataset for Flickr30k image-caption pairs.
    
    Expects:
        - images_dir: directory containing .jpg images
        - captions_file: CSV with columns [image_name, caption]
    """
    
    def __init__(self, images_dir: str, captions_file: str, processor):
        self.images_dir = Path(images_dir)
        self.processor = processor
        self.pairs = []
        
        # Parse captions file (one caption per image)
        seen_images = set()
        with open(captions_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                next(reader)  # skip header
            except StopIteration:
                pass
            
            for row in reader:
                if len(row) >= 2:
                    img_name = row[0].strip()
                    caption = row[1].strip()
                    img_path = self.images_dir / img_name
                    
                    if img_path.exists() and img_name not in seen_images:
                        self.pairs.append((str(img_path), caption))
                        seen_images.add(img_name)
        
        logger.info(f"Loaded {len(self.pairs)} image-caption pairs from {captions_file}")
    
    def __len__(self):
        return len(self.pairs)
    
    def __getitem__(self, idx):
        img_path, caption = self.pairs[idx]
        
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception:
            # Return a black image on failure
            image = Image.new('RGB', (224, 224), (0, 0, 0))
        
        # Process using CLIPProcessor
        inputs = self.processor(
            text=caption,
            images=image,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=77
        )
        
        # Squeeze batch dimension (DataLoader will add it back)
        return {
            'pixel_values': inputs['pixel_values'].squeeze(0),
            'input_ids': inputs['input_ids'].squeeze(0),
            'attention_mask': inputs['attention_mask'].squeeze(0),
        }


def contrastive_loss(logits_per_image, logits_per_text):
    """
    Symmetric contrastive loss (CLIP's native training objective).
    
    For a batch of N image-text pairs:
    - logits_per_image[i, j] = similarity(image_i, text_j)
    - The target is the identity matrix (image_i should match text_i)
    """
    batch_size = logits_per_image.shape[0]
    labels = torch.arange(batch_size, device=logits_per_image.device)
    
    loss_i = F.cross_entropy(logits_per_image, labels)
    loss_t = F.cross_entropy(logits_per_text, labels)
    
    return (loss_i + loss_t) / 2


def fine_tune(
    dataset_dir: str,
    captions_file: str,
    model_name: str = "openai/clip-vit-base-patch32",
    epochs: int = 4,
    batch_size: int = 16,
    learning_rate: float = 1e-6,
    checkpoint_dir: str = "fine_tuning/checkpoints",
    device: str = None
):
    """
    Fine-tune CLIP on Flickr30k.
    
    Args:
        dataset_dir: Path to directory containing Flickr30k images
        captions_file: Path to captions CSV file
        model_name: HuggingFace model name for CLIP
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate (use very low to avoid catastrophic forgetting)
        checkpoint_dir: Directory to save model checkpoints
        device: torch device (auto-detected if None)
    """
    from transformers import CLIPModel, CLIPProcessor
    
    # Setup device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    if device == "cpu":
        logger.warning(
            "Fine-tuning on CPU will be very slow. "
            "GPU with at least 8GB VRAM is strongly recommended."
        )
    
    # Load model and processor
    logger.info(f"Loading model: {model_name}")
    model = CLIPModel.from_pretrained(model_name).to(device)
    processor = CLIPProcessor.from_pretrained(model_name)
    
    # Create dataset and dataloader
    dataset = Flickr30kDataset(dataset_dir, captions_file, processor)
    
    if len(dataset) == 0:
        logger.error("No training data found. Exiting.")
        return
    
    dataloader = DataLoader(
        dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=2,
        pin_memory=(device == "cuda"),
        drop_last=True  # Drop incomplete batch for stable gradients
    )
    
    # Optimizer — very low LR to avoid catastrophic forgetting
    optimizer = torch.optim.AdamW(
        model.parameters(), 
        lr=learning_rate, 
        weight_decay=0.01
    )
    
    # Learning rate scheduler — cosine annealing
    total_steps = len(dataloader) * epochs
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=total_steps, eta_min=learning_rate * 0.1
    )
    
    # Create checkpoint directory
    ckpt_dir = Path(checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    
    # Training loop
    logger.info(f"Starting fine-tuning: {epochs} epochs, {len(dataset)} samples, batch_size={batch_size}")
    logger.info(f"Total steps: {total_steps}, LR: {learning_rate}")
    
    model.train()
    best_loss = float('inf')
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        num_batches = 0
        
        for batch_idx, batch in enumerate(dataloader):
            # Move to device
            pixel_values = batch['pixel_values'].to(device)
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            # Forward pass
            outputs = model(
                pixel_values=pixel_values,
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_loss=False
            )
            
            # Compute symmetric contrastive loss
            loss = contrastive_loss(
                outputs.logits_per_image,
                outputs.logits_per_text
            )
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            scheduler.step()
            
            epoch_loss += loss.item()
            num_batches += 1
            
            # Log progress
            if (batch_idx + 1) % 50 == 0 or (batch_idx + 1) == len(dataloader):
                avg_loss = epoch_loss / num_batches
                current_lr = optimizer.param_groups[0]['lr']
                logger.info(
                    f"Epoch {epoch+1}/{epochs} | "
                    f"Step {batch_idx+1}/{len(dataloader)} | "
                    f"Loss: {loss.item():.4f} | "
                    f"Avg Loss: {avg_loss:.4f} | "
                    f"LR: {current_lr:.2e}"
                )
        
        avg_epoch_loss = epoch_loss / max(num_batches, 1)
        logger.info(f"Epoch {epoch+1}/{epochs} completed. Average Loss: {avg_epoch_loss:.4f}")
        
        # Save checkpoint
        ckpt_path = ckpt_dir / f"clip_flickr30k_epoch_{epoch+1}"
        model.save_pretrained(str(ckpt_path))
        processor.save_pretrained(str(ckpt_path))
        logger.info(f"Checkpoint saved to: {ckpt_path}")
        
        # Track best model
        if avg_epoch_loss < best_loss:
            best_loss = avg_epoch_loss
            best_path = ckpt_dir / "clip_flickr30k_best"
            model.save_pretrained(str(best_path))
            processor.save_pretrained(str(best_path))
            logger.info(f"New best model saved (loss={best_loss:.4f})")
    
    logger.info(f"Fine-tuning complete! Best loss: {best_loss:.4f}")
    logger.info(f"Checkpoints saved in: {ckpt_dir}")
    logger.info(
        "To use the fine-tuned model, update config.py:\n"
        f"  CLIP_MODEL_PATH = '{ckpt_dir / 'clip_flickr30k_best'}'"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fine-tune CLIP on Flickr30k dataset"
    )
    parser.add_argument(
        "--dataset_dir",
        type=str,
        default="data/flickr30_data/flickr30k_images",
        help="Path to Flickr30k images directory"
    )
    parser.add_argument(
        "--captions_file",
        type=str,
        default="evaluation/data/flickr_subset/captions.txt",
        help="Path to captions CSV file"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="openai/clip-vit-base-patch32",
        help="HuggingFace CLIP model name"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=4,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=16,
        help="Training batch size"
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-6,
        help="Learning rate"
    )
    parser.add_argument(
        "--checkpoint_dir",
        type=str,
        default="fine_tuning/checkpoints",
        help="Directory for saving checkpoints"
    )
    
    args = parser.parse_args()
    
    fine_tune(
        dataset_dir=args.dataset_dir,
        captions_file=args.captions_file,
        model_name=args.model_name,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        checkpoint_dir=args.checkpoint_dir
    )

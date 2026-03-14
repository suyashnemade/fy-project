"""
Image indexing module.
Scans directory, generates embeddings, and builds FAISS index.
"""

import logging
import numpy as np
import faiss
from pathlib import Path
from PIL import Image
from typing import List, Optional, Tuple, Callable
import json

from .clip_model import CLIPModel
from .utils import find_images_in_directory, save_metadata, ensure_storage_directory
from .logger import get_logger
from . import config

logger = get_logger(__name__)


class ImageIndexer:
    """Handles image indexing and FAISS index creation."""
    
    def __init__(self, clip_model: CLIPModel):
        """
        Initialize indexer with CLIP model.
        
        Args:
            clip_model: CLIPModel instance
        """
        self.clip_model = clip_model
        ensure_storage_directory()
    
    def index_directory(
        self, 
        directory: str, 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[int, int]:
        """
        Index all images in a directory using batch processing.
        
        Args:
            directory: Directory path to index
            progress_callback: Optional callback function(current, total)
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        # Find all images
        image_paths = find_images_in_directory(directory)
        
        if not image_paths:
            logger.info(f"No valid images found in {directory}")
            return 0, 0
            
        logger.info(f"Found {len(image_paths)} images to index in {directory}")
        
        all_embeddings = []
        metadata = {}
        failed_count = 0
        successful_count = 0
        total = len(image_paths)
        
        # Process in batches
        batch_size = config.BATCH_SIZE
        for i in range(0, total, batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_images = []
            valid_paths = []
            
            # Load images for the current batch
            for path in batch_paths:
                try:
                    image = Image.open(path)
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    batch_images.append(image)
                    valid_paths.append(path)
                except Exception as e:
                    logger.warning(f"Failed to load image {path}: {e}")
                    failed_count += 1
            
            if not batch_images:
                continue
                
            # Encode entire batch at once
            try:
                batch_embeddings = self.clip_model.encode_images_batch(batch_images)
                
                # Store embeddings and metadata
                for j, path in enumerate(valid_paths):
                    all_embeddings.append(batch_embeddings[j])
                    image_id = successful_count
                    metadata[str(image_id)] = path
                    successful_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to encode batch: {e}")
                failed_count += len(valid_paths)
            
            # Call progress callback
            if progress_callback:
                progress_callback(min(i + batch_size, total), total)
        
        if not all_embeddings:
            logger.warning("No images were successfully encoded.")
            return 0, failed_count
            
        logger.info(f"Saving {successful_count} embeddings and building index...")
        
        # Convert to numpy array
        embeddings = np.array(all_embeddings, dtype=np.float32)
        
        # Save embeddings
        np.save(config.EMBEDDINGS_PATH, embeddings)
        
        # Save metadata
        save_metadata(metadata, config.METADATA_PATH)
        
        # Build FAISS index (cosine similarity using inner product on normalized vectors)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for normalized vectors
        index.add(embeddings)
        
        # Save FAISS index
        faiss.write_index(index, str(config.FAISS_INDEX_PATH))
        
        logger.info(f"Indexing complete. Success: {successful_count}, Failed: {failed_count}")
        return successful_count, failed_count

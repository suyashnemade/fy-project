"""
Image indexing module.
Scans directory, generates embeddings, and builds FAISS index.
Supports incremental indexing and multi-directory merging.
"""

import logging
import numpy as np
import faiss
from pathlib import Path
from PIL import Image
from typing import List, Optional, Tuple, Callable, Dict
import json

from .clip_model import CLIPModel
from .utils import find_images_in_directory, save_metadata, load_metadata, ensure_storage_directory
from .logger import get_logger
from . import config

logger = get_logger(__name__)


class ImageIndexer:
    """Handles image indexing and FAISS index creation with incremental support."""
    
    def __init__(self, clip_model: CLIPModel):
        """
        Initialize indexer with CLIP model.
        
        Args:
            clip_model: CLIPModel instance
        """
        self.clip_model = clip_model
        ensure_storage_directory()
    
    def _load_existing_data(self) -> Tuple[Dict[str, str], Optional[np.ndarray], Optional[faiss.Index]]:
        """
        Load existing metadata, embeddings, and FAISS index from disk.
        
        Returns:
            Tuple of (metadata_dict, embeddings_array_or_None, faiss_index_or_None)
        """
        metadata: Dict[str, str] = {}
        embeddings: Optional[np.ndarray] = None
        index: Optional[faiss.Index] = None
        
        # Load existing metadata
        if config.METADATA_PATH.exists():
            metadata = load_metadata(config.METADATA_PATH)
            logger.info(f"Loaded existing metadata with {len(metadata)} entries.")
        
        # Load existing embeddings
        if config.EMBEDDINGS_PATH.exists():
            try:
                embeddings = np.load(config.EMBEDDINGS_PATH)
                logger.info(f"Loaded existing embeddings: shape {embeddings.shape}")
            except Exception as e:
                logger.warning(f"Failed to load existing embeddings: {e}")
        
        # Load existing FAISS index
        if config.FAISS_INDEX_PATH.exists():
            try:
                index = faiss.read_index(str(config.FAISS_INDEX_PATH))
                logger.info(f"Loaded existing FAISS index with {index.ntotal} vectors.")
            except Exception as e:
                logger.warning(f"Failed to load existing FAISS index: {e}")
        
        return metadata, embeddings, index
    
    def index_directory(
        self, 
        directory: str, 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[int, int]:
        """
        Incrementally index images in a directory.
        
        Already-indexed images (by path) are skipped. New images are encoded
        and appended to the existing FAISS index, embeddings file, and metadata.
        This supports multi-directory merging — calling this method on different
        directories will accumulate all images into a single searchable index.
        
        Args:
            directory: Directory path to index
            progress_callback: Optional callback function(current, total)
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        # --- 1. Load existing data ---
        existing_metadata, existing_embeddings, existing_index = self._load_existing_data()
        existing_paths = set(existing_metadata.values())
        next_id = len(existing_metadata)
        
        # --- 2. Find new images only ---
        all_image_paths = find_images_in_directory(directory)
        
        if not all_image_paths:
            logger.info(f"No valid images found in {directory}")
            return 0, 0
        
        new_image_paths = [p for p in all_image_paths if p not in existing_paths]
        skipped_count = len(all_image_paths) - len(new_image_paths)
        
        if skipped_count > 0:
            logger.info(f"Skipping {skipped_count} already-indexed images.")
        
        if not new_image_paths:
            logger.info("All images in this directory are already indexed.")
            return 0, 0
        
        logger.info(f"Found {len(new_image_paths)} new images to index in {directory}")
        
        # --- 3. Encode new images in batches ---
        new_embeddings: List[np.ndarray] = []
        new_metadata: Dict[str, str] = {}
        failed_count = 0
        successful_count = 0
        total = len(new_image_paths)
        
        batch_size = config.BATCH_SIZE
        for i in range(0, total, batch_size):
            batch_paths = new_image_paths[i:i + batch_size]
            batch_images: List[Image.Image] = []
            valid_paths: List[str] = []
            
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
                
                for j, path in enumerate(valid_paths):
                    new_embeddings.append(batch_embeddings[j])
                    image_id = next_id + successful_count
                    new_metadata[str(image_id)] = path
                    successful_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to encode batch: {e}")
                failed_count += len(valid_paths)
            
            # Call progress callback
            if progress_callback:
                progress_callback(min(i + batch_size, total), total)
        
        if not new_embeddings:
            logger.warning("No new images were successfully encoded.")
            return 0, failed_count
        
        # --- 4. Merge with existing data ---
        logger.info(f"Merging {successful_count} new embeddings with existing index...")
        
        new_embeddings_array = np.array(new_embeddings, dtype=np.float32)
        
        # Merge embeddings
        if existing_embeddings is not None and existing_embeddings.size > 0:
            merged_embeddings = np.vstack([existing_embeddings, new_embeddings_array])
        else:
            merged_embeddings = new_embeddings_array
        
        # Merge metadata
        merged_metadata = {**existing_metadata, **new_metadata}
        
        # Save merged embeddings
        np.save(config.EMBEDDINGS_PATH, merged_embeddings)
        
        # Save merged metadata
        save_metadata(merged_metadata, config.METADATA_PATH)
        
        # Update FAISS index (append new vectors to existing, or create fresh)
        if existing_index is not None:
            existing_index.add(new_embeddings_array)
            faiss.write_index(existing_index, str(config.FAISS_INDEX_PATH))
        else:
            dimension = merged_embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)
            index.add(merged_embeddings)
            faiss.write_index(index, str(config.FAISS_INDEX_PATH))
        
        logger.info(
            f"Indexing complete. New: {successful_count}, Skipped: {skipped_count}, "
            f"Failed: {failed_count}, Total indexed: {len(merged_metadata)}"
        )
        return successful_count, failed_count

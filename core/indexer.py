"""
Image indexing module.
Scans directory, generates embeddings, and builds FAISS index.
Supports incremental indexing, multi-directory merging, and model change detection.
"""

import json
import logging
import numpy as np
import faiss
from pathlib import Path
from PIL import Image
from typing import List, Optional, Tuple, Callable, Dict

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
    
    def _get_model_fingerprint(self) -> dict:
        """Get current model fingerprint for consistency checking."""
        return {
            "model_name": config.MODEL_NAME,
            "embedding_dim": config.EMBEDDING_DIM
        }
    
    def _save_model_fingerprint(self):
        """Save current model fingerprint to disk."""
        fingerprint = self._get_model_fingerprint()
        try:
            with open(config.MODEL_FINGERPRINT_PATH, 'w') as f:
                json.dump(fingerprint, f, indent=2)
            logger.info(f"Saved model fingerprint: {fingerprint}")
        except Exception as e:
            logger.error(f"Failed to save model fingerprint: {e}")
    
    def _check_model_consistency(self):
        """
        Check if the stored index was built with the current model.
        If model has changed, delete old index files so a fresh rebuild occurs.
        """
        if not config.MODEL_FINGERPRINT_PATH.exists():
            # No fingerprint file — could be first run or legacy index
            if config.FAISS_INDEX_PATH.exists():
                logger.warning(
                    "No model fingerprint found but index exists. "
                    "Assuming model may have changed — deleting old index for safety."
                )
                self._delete_index_files()
            return
        
        try:
            with open(config.MODEL_FINGERPRINT_PATH, 'r') as f:
                stored = json.load(f)
            
            current = self._get_model_fingerprint()
            
            if stored.get("model_name") != current["model_name"] or \
               stored.get("embedding_dim") != current["embedding_dim"]:
                logger.warning(
                    f"Model changed! Stored: {stored.get('model_name')} (dim={stored.get('embedding_dim')}), "
                    f"Current: {current['model_name']} (dim={current['embedding_dim']}). "
                    f"Deleting old index for rebuild."
                )
                self._delete_index_files()
            else:
                logger.info(f"Model fingerprint matches: {current['model_name']} (dim={current['embedding_dim']})")
        except Exception as e:
            logger.warning(f"Failed to read model fingerprint: {e}. Deleting index for safety.")
            self._delete_index_files()
    
    def _delete_index_files(self):
        """Delete all index-related files to force a fresh rebuild."""
        files_to_delete = [
            config.FAISS_INDEX_PATH,
            config.EMBEDDINGS_PATH,
            config.METADATA_PATH,
            config.MODEL_FINGERPRINT_PATH
        ]
        for path in files_to_delete:
            if path.exists():
                path.unlink()
                logger.info(f"Deleted: {path}")
    
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
        This supports multi-directory merging.
        
        Automatically detects model changes and rebuilds from scratch if needed.
        
        Args:
            directory: Directory path to index
            progress_callback: Optional callback function(current, total)
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        # Check if model has changed — if so, old index is deleted
        self._check_model_consistency()
        
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
                
            # Encode entire batch at once (already returns normalized embeddings)
            try:
                batch_embeddings = self.clip_model.encode_images_batch(batch_images)
                
                # Debug: log embedding shape
                logger.debug(f"Batch embedding shape: {batch_embeddings.shape}")
                
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
                if progress_callback(min(i + batch_size, total), total):
                    logger.info("Indexing cancelled by user. Saving partial progress...")
                    break
        
        if not new_embeddings:
            logger.warning("No new images were successfully encoded.")
            return 0, failed_count
        
        # --- 4. Merge with existing data ---
        logger.info(f"Merging {successful_count} new embeddings with existing index...")
        
        new_embeddings_array = np.array(new_embeddings, dtype=np.float32)
        logger.info(f"New embeddings array shape: {new_embeddings_array.shape}")
        
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
        
        # Update FAISS index — use dynamic dimension from actual embedding shape
        dimension = merged_embeddings.shape[1]
        logger.info(f"Building FAISS index with dimension={dimension}")
        
        if existing_index is not None and existing_index.d == dimension:
            existing_index.add(new_embeddings_array)
            faiss.write_index(existing_index, str(config.FAISS_INDEX_PATH))
        else:
            if existing_index is not None and existing_index.d != dimension:
                logger.warning(
                    f"Existing index dimension ({existing_index.d}) != current ({dimension}). "
                    f"Rebuilding entire index."
                )
            index = faiss.IndexFlatIP(dimension)
            index.add(merged_embeddings)
            faiss.write_index(index, str(config.FAISS_INDEX_PATH))
        
        # Save model fingerprint after successful indexing
        self._save_model_fingerprint()
        
        # Debug: log final index stats
        final_index = faiss.read_index(str(config.FAISS_INDEX_PATH))
        logger.info(
            f"Indexing complete. New: {successful_count}, Skipped: {skipped_count}, "
            f"Failed: {failed_count}, Total indexed: {len(merged_metadata)}, "
            f"index.ntotal: {final_index.ntotal}, dimension: {final_index.d}"
        )
        return successful_count, failed_count

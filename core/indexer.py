"""
Image indexing module.
Scans directory, generates embeddings, and builds FAISS index.
"""

import numpy as np
import faiss
from pathlib import Path
from PIL import Image
from typing import List, Optional, Tuple, Callable
import json

from .clip_model import CLIPModel
from .utils import find_images_in_directory, save_metadata, ensure_storage_directory


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
        Index all images in a directory.
        
        Args:
            directory: Directory path to index
            progress_callback: Optional callback function(current, total)
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        # Find all images
        image_paths = find_images_in_directory(directory)
        
        if not image_paths:
            return 0, 0
        
        embeddings_list = []
        metadata = {}
        failed_count = 0
        
        total = len(image_paths)
        for idx, image_path in enumerate(image_paths):
            try:
                # Load image
                image = Image.open(image_path)
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Generate embedding
                embedding = self.clip_model.encode_image(image)
                embeddings_list.append(embedding)
                
                # Store metadata
                image_id = len(embeddings_list) - 1
                metadata[str(image_id)] = image_path
                
            except Exception as e:
                # Skip corrupt or unreadable images
                failed_count += 1
                continue
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(idx + 1, total)
        
        if not embeddings_list:
            return 0, failed_count
        
        # Convert to numpy array
        embeddings = np.array(embeddings_list, dtype=np.float32)
        
        # Save embeddings
        embeddings_path = Path('storage/embeddings.npy')
        np.save(embeddings_path, embeddings)
        
        # Save metadata
        metadata_path = Path('storage/metadata.json')
        save_metadata(metadata, metadata_path)
        
        # Build FAISS index (cosine similarity using inner product on normalized vectors)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for normalized vectors
        index.add(embeddings)
        
        # Save FAISS index
        index_path = Path('storage/faiss.index')
        faiss.write_index(index, str(index_path))
        
        successful_count = len(embeddings_list)
        return successful_count, failed_count

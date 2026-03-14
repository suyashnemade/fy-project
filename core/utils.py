"""
Utility functions for image search application.
"""

import os
import json
import logging
from pathlib import Path
from typing import List

from .logger import get_logger
from . import config

logger = get_logger(__name__)


def find_images_in_directory(directory: str) -> List[str]:
    """
    Recursively find all image files in a directory.
    Uses case-insensitive matching and prevents duplicates.
    
    Args:
        directory: Root directory path
    
    Returns:
        List of absolute paths to image files
    """
    directory = Path(directory)
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    image_paths = []
    
    # Use rglob('*') and check suffix instead of multiple rglob calls
    # This avoids duplicates on case-insensitive file systems (like Windows)
    try:
        for f in directory.rglob('*'):
            if f.is_file() and f.suffix.lower() in config.SUPPORTED_EXTENSIONS:
                image_paths.append(str(f.absolute()))
                
        # Deduplicate and sort
        unique_paths = sorted(list(set(image_paths)))
        return unique_paths
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")
        return []


def save_metadata(metadata: dict, filepath: str | Path):
    """
    Save metadata dictionary to JSON file.
    
    Args:
        metadata: Dictionary to save
        filepath: Output file path
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save metadata to {filepath}: {e}")


def load_metadata(filepath: str | Path) -> dict:
    """
    Load metadata dictionary from JSON file.
    
    Args:
        filepath: Input file path
    
    Returns:
        Dictionary containing metadata
    """
    if not os.path.exists(filepath):
        return {}
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load metadata from {filepath}: {e}")
        return {}


def ensure_storage_directory():
    """Ensure storage directory exists."""
    config.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

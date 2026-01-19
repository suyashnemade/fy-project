"""
Utility functions for image search application.
"""

import os
import json
from pathlib import Path
from typing import List


def get_image_extensions() -> List[str]:
    """Get list of supported image file extensions."""
    return ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']


def find_images_in_directory(directory: str) -> List[str]:
    """
    Recursively find all image files in a directory.
    
    Args:
        directory: Root directory path
    
    Returns:
        List of absolute paths to image files
    """
    directory = Path(directory)
    if not directory.exists():
        return []
    
    image_paths = []
    extensions = get_image_extensions()
    
    for ext in extensions:
        image_paths.extend(directory.rglob(f'*{ext}'))
    
    # Convert to strings and sort
    return sorted([str(p.absolute()) for p in image_paths])


def save_metadata(metadata: dict, filepath: str):
    """
    Save metadata dictionary to JSON file.
    
    Args:
        metadata: Dictionary to save
        filepath: Output file path
    """
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)


def load_metadata(filepath: str) -> dict:
    """
    Load metadata dictionary from JSON file.
    
    Args:
        filepath: Input file path
    
    Returns:
        Dictionary containing metadata
    """
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, 'r') as f:
        return json.load(f)


def ensure_storage_directory():
    """Ensure storage directory exists."""
    storage_dir = Path('storage')
    storage_dir.mkdir(exist_ok=True)

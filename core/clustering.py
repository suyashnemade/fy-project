"""
Semantic clustering module.
Clusters image embeddings using KMeans and reduces to 2D via PCA
for visualization. No sklearn dependency — uses numpy for both.
"""

import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any

from .logger import get_logger

logger = get_logger(__name__)


def compute_clusters(
    embeddings: np.ndarray,
    image_paths: List[str],
    n_clusters: int = 5,
    n_components: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Cluster embeddings with KMeans and project to 2D with PCA.
    
    Args:
        embeddings: (N, D) embedding vectors
        image_paths: paths corresponding to each embedding
        n_clusters: number of KMeans clusters (auto-capped to N)
        n_components: PCA dimensions (2 for scatter plot)
    
    Returns:
        Dict with keys:
            - 'points': list of dicts with 'path', 'label', 'x', 'y', 'cluster'
            - 'n_clusters': actual number of clusters used
            - 'explained_variance': PCA explained variance ratio
            - 'cluster_sizes': list of (cluster_id, count) tuples
        or None on failure
    """
    if embeddings is None or len(embeddings) < 2:
        logger.warning("Need at least 2 embeddings for clustering.")
        return None
    
    try:
        n_samples = embeddings.shape[0]
        actual_k = min(n_clusters, n_samples)
        
        # --- KMeans clustering (numpy implementation) ---
        labels = _kmeans(embeddings, actual_k, max_iters=50)
        
        # --- PCA dimensionality reduction ---
        projected, explained_var = _pca(embeddings, n_components)
        
        # --- Build result ---
        points = []
        for i, path in enumerate(image_paths):
            points.append({
                'path': path,
                'label': Path(path).name,
                'x': float(projected[i, 0]),
                'y': float(projected[i, 1]) if n_components > 1 else 0.0,
                'cluster': int(labels[i])
            })
        
        # Cluster sizes
        unique, counts = np.unique(labels, return_counts=True)
        cluster_sizes = [(int(u), int(c)) for u, c in zip(unique, counts)]
        
        logger.info(
            f"Clustered {n_samples} images → {actual_k} clusters, "
            f"PCA explained variance: {explained_var:.2%}"
        )
        
        return {
            'points': points,
            'n_clusters': actual_k,
            'explained_variance': explained_var,
            'cluster_sizes': cluster_sizes,
        }
        
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return None


def _kmeans(
    data: np.ndarray, k: int, max_iters: int = 50, seed: int = 42
) -> np.ndarray:
    """
    Simple KMeans clustering (numpy only, no sklearn).
    
    Args:
        data: (N, D) array
        k: number of clusters
        max_iters: maximum iterations
        seed: random seed for reproducibility
    
    Returns:
        (N,) array of cluster labels
    """
    rng = np.random.RandomState(seed)
    n_samples = data.shape[0]
    
    # Initialize centroids with KMeans++ (better than random)
    centroids = _kmeans_plus_plus_init(data, k, rng)
    
    labels = np.zeros(n_samples, dtype=np.int32)
    
    for iteration in range(max_iters):
        # Assign each point to nearest centroid
        # distances: (N, k)
        distances = np.linalg.norm(
            data[:, np.newaxis, :] - centroids[np.newaxis, :, :], axis=2
        )
        new_labels = np.argmin(distances, axis=1)
        
        # Check convergence
        if np.array_equal(new_labels, labels) and iteration > 0:
            logger.debug(f"KMeans converged after {iteration + 1} iterations.")
            break
        
        labels = new_labels
        
        # Update centroids
        for c in range(k):
            mask = labels == c
            if mask.sum() > 0:
                centroids[c] = data[mask].mean(axis=0)
    
    return labels


def _kmeans_plus_plus_init(
    data: np.ndarray, k: int, rng: np.random.RandomState
) -> np.ndarray:
    """KMeans++ initialization for better convergence."""
    n_samples, n_features = data.shape
    centroids = np.zeros((k, n_features), dtype=data.dtype)
    
    # First centroid: random
    idx = rng.randint(0, n_samples)
    centroids[0] = data[idx]
    
    for c in range(1, k):
        # Distance to nearest existing centroid
        dists = np.min(
            np.linalg.norm(data[:, np.newaxis, :] - centroids[:c][np.newaxis, :, :], axis=2),
            axis=1
        )
        # Probability proportional to distance squared
        probs = dists ** 2
        probs_sum = probs.sum()
        if probs_sum > 0:
            probs = probs / probs_sum
        else:
            probs = np.ones(n_samples) / n_samples
        
        idx = rng.choice(n_samples, p=probs)
        centroids[c] = data[idx]
    
    return centroids


def _pca(
    data: np.ndarray, n_components: int = 2
) -> tuple:
    """
    PCA via eigendecomposition (no sklearn).
    Returns (projected_data, explained_variance_ratio).
    """
    mean = np.mean(data, axis=0)
    centered = data - mean
    
    n_samples = centered.shape[0]
    cov = np.dot(centered.T, centered) / max(n_samples - 1, 1)
    
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    
    # Sort descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Project
    components = eigenvectors[:, :n_components]
    projected = np.dot(centered, components)
    
    # Normalize to [0, 1] for plotting
    for d in range(n_components):
        col = projected[:, d]
        col_min, col_max = col.min(), col.max()
        if col_max - col_min > 1e-8:
            projected[:, d] = (col - col_min) / (col_max - col_min)
        else:
            projected[:, d] = 0.5
    
    # Explained variance
    total_var = eigenvalues.sum()
    explained = eigenvalues[:n_components].sum() / total_var if total_var > 0 else 0
    
    return projected, explained


def get_result_embeddings(
    clip_model,
    image_paths: List[str]
) -> Optional[np.ndarray]:
    """
    Get embeddings for a list of image paths (for clustering visualization).
    """
    from PIL import Image
    
    try:
        images = []
        valid_paths = []
        
        for path in image_paths:
            try:
                img = Image.open(path).convert('RGB')
                images.append(img)
                valid_paths.append(path)
            except Exception as e:
                logger.warning(f"Clustering: failed to load {path}: {e}")
        
        if len(images) < 2:
            logger.warning("Need at least 2 valid images for clustering.")
            return None
        
        embeddings = clip_model.encode_images_batch(images)
        logger.info(f"Computed embeddings for {len(images)} images, shape: {embeddings.shape}")
        return embeddings
        
    except Exception as e:
        logger.error(f"Failed to compute embeddings for clustering: {e}")
        return None

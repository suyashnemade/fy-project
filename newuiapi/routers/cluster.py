"""
Clustering endpoint: cluster images using KMeans + PCA visualization.
"""

from fastapi import APIRouter, Depends, HTTPException

from core.clip_model import CLIPModel
from ..dependencies import get_clip_model
from ..models import ClusterRequest, ClusterResponse
from .. import services

router = APIRouter(prefix="/cluster", tags=["Clustering"])


@router.post("/results", response_model=ClusterResponse)
def cluster_results(
    request: ClusterRequest,
    clip_model: CLIPModel = Depends(get_clip_model),
):
    """
    Cluster a set of images using KMeans and project to 2D with PCA.

    Requires at least 2 image paths. Returns cluster assignments and
    2D coordinates suitable for scatter plot visualization.
    """
    # Validate all paths exist
    from pathlib import Path

    missing = [p for p in request.image_paths if not Path(p).exists()]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Images not found: {missing[:5]}",  # Show first 5 at most
        )

    result = services.perform_clustering(
        clip_model, request.image_paths, request.n_clusters
    )

    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Clustering failed. Ensure at least 2 valid images are provided.",
        )

    return result

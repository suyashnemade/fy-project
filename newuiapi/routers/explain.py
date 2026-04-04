"""
Explainability endpoint: generate gradient-based visual explanations.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from core.clip_model import CLIPModel
from ..dependencies import get_clip_model
from ..models import ExplainRequest, ExplainResponse
from .. import services

router = APIRouter(prefix="/explain", tags=["Explainability"])


@router.post("/result", response_model=ExplainResponse)
def explain_result(
    request: ExplainRequest,
    clip_model: CLIPModel = Depends(get_clip_model),
):
    """
    Generate a visual explanation for why an image matched a query.

    Uses gradient-based attribution through CLIP's visual encoder to
    produce a heatmap showing which image regions are most relevant
    to the query. Returns base64-encoded heatmap and annotated images.
    """
    if not Path(request.image_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Image not found: {request.image_path}",
        )

    result = services.perform_explain(clip_model, request.image_path, request.query)

    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate explanation. The image may be corrupt or unreadable.",
        )

    return result

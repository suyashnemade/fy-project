"""
Image-text matching endpoint: compute similarity between an image and text.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from core.search import ImageSearcher
from ..dependencies import get_searcher
from ..models import MatchResponse
from .. import services

router = APIRouter(prefix="/match", tags=["Matching"])


@router.post("/image-text", response_model=MatchResponse)
def match_image_text(
    file: UploadFile = File(..., description="Image file to score"),
    text: str = Form(..., min_length=1, description="Text description to compare against"),
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Compute cosine similarity between an uploaded image and a text description.

    Returns a score (typically 0.15–0.35 for matches) and a human-readable
    verdict: Strong match (>0.25), Moderate match (>0.18), or Weak match.
    """
    contents = file.file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        return services.perform_match(
            searcher, contents, text, file.filename or ""
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Match scoring failed: {e}")

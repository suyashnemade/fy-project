"""
Search endpoints: text-to-image, image-to-image, and video frame search.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException

from core.search import ImageSearcher
from ..dependencies import get_searcher
from ..models import SearchResponse, ImageSearchBase64Request, VideoSearchRequest, VideoSearchResponse
from .. import services

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/text", response_model=SearchResponse)
def search_by_text(
    query: str = Query(..., min_length=1, description="Text search query"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Search for images matching a natural language text description.

    Uses CLIP embeddings + FAISS index with optional reranking and feedback boosting.
    """
    if not searcher.is_indexed():
        raise HTTPException(
            status_code=400,
            detail="No images indexed yet. Please index a directory first.",
        )

    return services.perform_text_search(searcher, query, top_k)


@router.post("/image", response_model=SearchResponse)
def search_by_image(
    file: UploadFile = File(..., description="Query image file"),
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Search for visually similar images by uploading a query image.

    The uploaded image is encoded with CLIP and compared against the FAISS index.
    """
    if not searcher.is_indexed():
        raise HTTPException(
            status_code=400,
            detail="No images indexed yet. Please index a directory first.",
        )

    contents = file.file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        return services.perform_image_search(
            searcher, contents, top_k, file.filename or ""
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")


@router.post("/image-b64", response_model=SearchResponse)
def search_by_image_base64(
    request: ImageSearchBase64Request,
    top_k: int = Query(10, ge=1, le=100, description="Number of results to return"),
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Search for visually similar images using a base64-encoded query image.

    Alternative to the multipart /search/image endpoint.
    Accepts a JSON body with the image encoded as a base64 string.
    """
    if not searcher.is_indexed():
        raise HTTPException(
            status_code=400,
            detail="No images indexed yet. Please index a directory first.",
        )

    import base64 as b64module

    try:
        contents = b64module.b64decode(request.image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data.")

    if not contents:
        raise HTTPException(status_code=400, detail="Image data is empty.")

    try:
        return services.perform_image_search(
            searcher, contents, top_k, request.filename
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")


@router.post("/video", response_model=VideoSearchResponse)
def search_video(
    request: VideoSearchRequest,
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Search video frames for scenes matching a text query.

    Extracts frames at the specified FPS, encodes them with CLIP,
    and returns the top matching frames as base64-encoded images.
    Requires opencv-python to be installed.
    """
    if not Path(request.video_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Video file not found: {request.video_path}",
        )

    try:
        return services.perform_video_search(
            searcher, request.video_path, request.query, request.top_k, request.fps
        )
    except InterruptedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Video search requires opencv-python. Install with: pip install opencv-python",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video search failed: {e}")

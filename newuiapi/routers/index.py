"""
Indexing endpoints: index a directory, check status, reload index.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from core.search import ImageSearcher
from core.indexer import ImageIndexer
from ..dependencies import get_searcher, get_indexer, app_state
from ..models import IndexRequest, IndexVideoRequest, IndexResponse, IndexStatusResponse
from .. import services

router = APIRouter(prefix="/index", tags=["Indexing"])


@router.get("/status", response_model=IndexStatusResponse)
def index_status(
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Get current index status.

    Returns whether an index is loaded, how many images are indexed,
    and the index file size on disk.
    """
    return services.get_index_status(searcher)


@router.post("/directory", response_model=IndexResponse)
def index_directory(
    request: IndexRequest,
    indexer: ImageIndexer = Depends(get_indexer),
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Index all images in a directory.

    Incrementally indexes new images — already-indexed images are skipped.
    Supports multiple directories (call repeatedly to merge).
    Automatically reloads the search index after completion.

    This is a synchronous operation that blocks until indexing finishes.
    """
    directory = Path(request.directory)
    if not directory.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Directory not found: {request.directory}",
        )
    if not directory.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Path is not a directory: {request.directory}",
        )

    try:
        return services.perform_index_directory(indexer, searcher, request.directory)
    except InterruptedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

@router.post("/video")
def index_video(
    request: IndexVideoRequest,
    searcher: ImageSearcher = Depends(get_searcher),
):
    """
    Extract and encode frames from a video file into temporary memory cache.
    Must be called before searching a video.
    """
    video_path = Path(request.video_path)
    if not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Video not found: {request.video_path}",
        )
    if not video_path.is_file():
        raise HTTPException(
            status_code=400,
            detail=f"Path is not a file: {request.video_path}",
        )

    try:
        return services.perform_index_video(searcher, request.video_path, request.fps)
    except InterruptedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Video search requires opencv-python. Install with: pip install opencv-python",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video indexing failed: {e}")


@router.post("/reload")
def reload_index():
    """
    Reload the FAISS index from disk.

    Useful if the index was modified externally or after manual changes.
    """
    app_state.reload_index()
    is_indexed = app_state.searcher.is_indexed() if app_state.searcher else False
    return {
        "message": "Index reloaded successfully.",
        "is_indexed": is_indexed,
    }

@router.delete("/clear")
def clear_index(
    indexer: ImageIndexer = Depends(get_indexer),
):
    """
    Clear all index files from disk.
    
    Wipes the FAISS vectors, embeddings, and sqlite metadata,
    and unloads them from application memory.
    """
    try:
        indexer._delete_index_files()
        app_state.reload_index()
        return {
            "message": "Index cleared successfully.",
            "is_indexed": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear index: {e}")

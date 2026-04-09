"""
Service layer bridging FastAPI endpoints to core functionality.

Each function in this module:
  1. Accepts simple Python types (bytes, strings, model instances)
  2. Calls into core/ functions WITHOUT modifying them
  3. Returns Pydantic response models ready for JSON serialization

This layer handles PIL Image conversion, base64 encoding, timing,
and any data transformation needed between the API contract and core.
"""

import io
import base64
import time
from pathlib import Path
from typing import List, Optional

from PIL import Image

from core.search import ImageSearcher
from core.indexer import ImageIndexer
from core.clip_model import CLIPModel
from core import config

from .dependencies import app_state

from .models import (
    SearchResult,
    SearchResponse,
    VideoFrameResult,
    VideoSearchResponse,
    IndexResponse,
    IndexStatusResponse,
    MatchResponse,
    ClusterPoint,
    ClusterResponse,
    ExplainResponse,
)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _image_to_base64(image: Image.Image, fmt: str = "JPEG") -> str:
    """Convert a PIL Image to a base64-encoded string."""
    buffer = io.BytesIO()
    # JPEG doesn't support alpha channel
    if image.mode == "RGBA" and fmt == "JPEG":
        image = image.convert("RGB")
    elif image.mode != "RGB" and fmt == "JPEG":
        image = image.convert("RGB")
    image.save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# ── Search Services ────────────────────────────────────────────────────────


def perform_text_search(
    searcher: ImageSearcher,
    query: str,
    top_k: int = 10,
) -> SearchResponse:
    """Execute text-to-image search and return structured response."""
    start = time.time()
    results = searcher.search(query, top_k=top_k)
    took_ms = (time.time() - start) * 1000

    search_results = [
        SearchResult(
            image_path=path,
            filename=Path(path).name,
            score=round(score, 6),
            rank=idx + 1,
        )
        for idx, (path, score) in enumerate(results)
    ]

    return SearchResponse(
        query=query,
        results=search_results,
        count=len(search_results),
        took_ms=round(took_ms, 2),
    )


def perform_image_search(
    searcher: ImageSearcher,
    image_bytes: bytes,
    top_k: int = 10,
    filename: str = "",
) -> SearchResponse:
    """Execute image-to-image search from uploaded file bytes."""
    start = time.time()
    query_image = Image.open(io.BytesIO(image_bytes))
    results = searcher.search_by_image(query_image, top_k=top_k)
    took_ms = (time.time() - start) * 1000

    query_label = f"image:{filename}" if filename else "image:upload"

    search_results = [
        SearchResult(
            image_path=path,
            filename=Path(path).name,
            score=round(score, 6),
            rank=idx + 1,
        )
        for idx, (path, score) in enumerate(results)
    ]

    return SearchResponse(
        query=query_label,
        results=search_results,
        count=len(search_results),
        took_ms=round(took_ms, 2),
    )


def perform_index_video(
    searcher: ImageSearcher,
    video_path: str,
    fps: float = 1.0,
):
    """Extract and encode video frames into memory."""
    app_state.stop_requested = False
    
    def check_cancel(current=0, total=0):
        app_state.indexing_progress = {"current": current, "total": total}
        if getattr(app_state, "stop_requested", False):
            return True
        return False
        
    app_state.video_index = searcher.index_video(
        video_path=video_path,
        fps=fps,
        is_cancelled=check_cancel
    )

    # Clear progress tracking
    app_state.indexing_progress = None

    if not app_state.video_index or "frames" not in app_state.video_index:
        if getattr(app_state, "stop_requested", False):
            raise InterruptedError("Video indexing safely stopped but no frames were extracted yet.")
        raise RuntimeError("Failed to index video. No frames were extracted.")
    
    message = f"Successfully indexed {len(app_state.video_index['frames'])} frames from video."
    if getattr(app_state, "stop_requested", False):
        message = f"Video indexing stopped dynamically. {len(app_state.video_index['frames'])} frames were successfully processed."
        
    return {"message": message}

def perform_video_search(
    searcher: ImageSearcher,
    video_path: str,
    query: str,
    top_k: int = 5,
    fps: float = 1.0,
) -> VideoSearchResponse:
    """Execute video frame search dynamically against the cached video index."""
    from core.features.video_search import format_timestamp

    if not app_state.video_index or app_state.video_index.get("video_path") != video_path:
        raise ValueError("Video has not been indexed yet. Please Index Video first.")

    results = searcher.query_indexed_video(
        video_index=app_state.video_index,
        query=query,
        top_k=top_k,
    )

    frame_results = []
    for frame_img, timestamp, score in results:
        frame_results.append(
            VideoFrameResult(
                timestamp=round(timestamp, 2),
                formatted_time=format_timestamp(timestamp),
                score=round(score, 6),
                frame_base64=_image_to_base64(frame_img),
            )
        )

    return VideoSearchResponse(
        query=query,
        video_path=video_path,
        results=frame_results,
        count=len(frame_results),
    )


# ── Index Services ──────────────────────────────────────────────────────────


def perform_index_directory(
    indexer: ImageIndexer,
    searcher: ImageSearcher,
    directory: str,
) -> IndexResponse:
    """Index a directory of images and reload the search index."""
    app_state.stop_requested = False
    app_state.indexing_progress = {"current": 0, "total": 0}
    
    def check_cancel(current, total):
        app_state.indexing_progress = {"current": current, "total": total}
        if getattr(app_state, "stop_requested", False):
            return True
        return False

    successful, failed = indexer.index_directory(directory, progress_callback=check_cancel)
    searcher.reload_index()

    # Clear progress after run
    app_state.indexing_progress = None

    total_indexed = len(searcher.metadata) if searcher.metadata else 0

    message = f"Indexing complete. {successful} new images indexed."
    if getattr(app_state, "stop_requested", False):
        message = f"Indexing stopped safely by user. {successful} partial images indexed."

    return IndexResponse(
        message=message,
        successful=successful,
        failed=failed,
        total_indexed=total_indexed,
    )


def get_index_status(searcher: ImageSearcher) -> IndexStatusResponse:
    """Get current index status information."""
    is_indexed = searcher.is_indexed()
    image_count = len(searcher.metadata) if searcher.metadata else 0

    index_size = 0
    if config.FAISS_INDEX_PATH.exists():
        index_size = config.FAISS_INDEX_PATH.stat().st_size

    progress = None
    if getattr(app_state, "indexing_progress", None):
        progress = {
            "current": app_state.indexing_progress["current"],
            "total": app_state.indexing_progress["total"]
        }

    return IndexStatusResponse(
        is_indexed=is_indexed,
        image_count=image_count,
        index_size_bytes=index_size,
        progress=progress,
    )


# ── Match Services ──────────────────────────────────────────────────────────


def perform_match(
    searcher: ImageSearcher,
    image_bytes: bytes,
    text: str,
    image_filename: str = "",
) -> MatchResponse:
    """Compute image-text similarity score with verdict classification."""
    query_image = Image.open(io.BytesIO(image_bytes))
    score = searcher.compute_image_text_similarity(query_image, text)

    if score > 0.25:
        verdict = "Strong match"
    elif score > 0.18:
        verdict = "Moderate match"
    else:
        verdict = "Weak match"

    return MatchResponse(
        score=round(score, 6),
        verdict=verdict,
        image_path=image_filename,
        text=text,
    )


# ── Explainability Services ────────────────────────────────────────────────


def perform_explain(
    clip_model: CLIPModel,
    image_path: str,
    query: str,
) -> Optional[ExplainResponse]:
    """Generate gradient-based visual explanation for a search result."""
    from core.explainability import generate_explanation

    result = generate_explanation(clip_model, image_path, query)
    if result is None:
        return None

    return ExplainResponse(
        similarity=round(result["similarity"], 6),
        query=result["query"],
        image_path=result["image_path"],
        heatmap_base64=_image_to_base64(result["heatmap_image"]),
        annotated_base64=_image_to_base64(result["annotated_image"]),
    )


# ── Clustering Services ────────────────────────────────────────────────────


def perform_clustering(
    clip_model: CLIPModel,
    image_paths: List[str],
    n_clusters: int = 5,
) -> Optional[ClusterResponse]:
    """Cluster images using KMeans and project to 2D with PCA."""
    from core.clustering import compute_clusters, get_result_embeddings

    embeddings = get_result_embeddings(clip_model, image_paths)
    if embeddings is None:
        return None

    result = compute_clusters(embeddings, image_paths, n_clusters=n_clusters)
    if result is None:
        return None

    points = [
        ClusterPoint(
            path=p["path"],
            label=p["label"],
            x=round(p["x"], 6),
            y=round(p["y"], 6),
            cluster=p["cluster"],
        )
        for p in result["points"]
    ]

    return ClusterResponse(
        points=points,
        n_clusters=result["n_clusters"],
        explained_variance=round(result["explained_variance"], 6),
        cluster_sizes=[[cid, count] for cid, count in result["cluster_sizes"]],
    )

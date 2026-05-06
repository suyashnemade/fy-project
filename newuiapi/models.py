"""
Pydantic request/response models for all API endpoints.

These schemas define the JSON contracts between the FastAPI backend
and the React frontend. All fields are JSON-serializable.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ── Search ──────────────────────────────────────────────────────────────────


class SearchResult(BaseModel):
    """A single search result."""
    image_path: str
    filename: str
    score: float
    rank: int


class SearchResponse(BaseModel):
    """Response for text and image search endpoints."""
    query: str
    results: List[SearchResult]
    count: int
    took_ms: float


class ImageSearchBase64Request(BaseModel):
    """Request body for image-to-image search using base64-encoded image data.

    Used instead of multipart form upload to avoid body-parsing issues
    in Tauri's webview and certain python-multipart versions.
    """
    image_base64: str = Field(..., description="Base64-encoded image data (no data-URL prefix)")
    filename: str = Field(default="", description="Original filename for logging")


# ── Video Search ────────────────────────────────────────────────────────────


class VideoSearchRequest(BaseModel):
    """Request body for video frame search."""
    video_path: str = Field(..., description="Absolute path to the video file")
    query: str = Field(..., min_length=1, description="Text query to search for")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top frames to return")
    fps: float = Field(default=1.0, gt=0, le=30, description="Frame extraction rate (fps)")


class VideoFrameResult(BaseModel):
    """A single matched video frame."""
    timestamp: float
    formatted_time: str
    score: float
    frame_base64: str = Field(..., description="Base64-encoded JPEG of the frame")


class VideoSearchResponse(BaseModel):
    """Response for video search endpoint."""
    query: str
    video_path: str
    results: List[VideoFrameResult]
    count: int


# ── Indexing ────────────────────────────────────────────────────────────────


class IndexRequest(BaseModel):
    """Request body for indexing a directory."""
    directory: str = Field(..., description="Absolute path to the image directory")

class IndexVideoRequest(BaseModel):
    """Request body for indexing a video."""
    video_path: str = Field(..., description="Absolute path to the video file")
    fps: float = Field(default=1.0, gt=0, le=30, description="Frame extraction rate (fps)")


class IndexResponse(BaseModel):
    """Response after indexing completes."""
    message: str
    successful: int
    failed: int
    total_indexed: int

class IndexProgress(BaseModel):
    """Progress tracker for long-running indexing operations."""
    current: int
    total: int

class IndexStatusResponse(BaseModel):
    """Current index status."""
    is_indexed: bool
    image_count: int
    index_size_bytes: int
    progress: Optional[IndexProgress] = None


# ── Image-Text Matching ────────────────────────────────────────────────────


class MatchResponse(BaseModel):
    """Response for image-text similarity scoring."""
    score: float
    verdict: str
    image_path: str = ""
    text: str = ""


# ── Feedback ────────────────────────────────────────────────────────────────


class FeedbackRequest(BaseModel):
    """Request body for submitting relevance feedback."""
    query: str = Field(..., min_length=1)
    image_path: str = Field(..., min_length=1)
    feedback: str = Field(..., pattern="^(relevant|not_relevant)$",
                          description="Must be 'relevant' or 'not_relevant'")
    rank: int = Field(default=-1, description="Original rank in search results")
    score: float = Field(default=0.0, description="Original similarity score")


class FeedbackStatsResponse(BaseModel):
    """Feedback statistics."""
    total: int
    relevant: int
    not_relevant: int


# ── Clustering ──────────────────────────────────────────────────────────────


class ClusterRequest(BaseModel):
    """Request body for clustering images."""
    image_paths: List[str] = Field(..., min_length=2,
                                   description="At least 2 image paths required")
    n_clusters: int = Field(default=5, ge=2, le=20)


class ClusterPoint(BaseModel):
    """A single point in the PCA-projected cluster visualization."""
    path: str
    label: str
    x: float
    y: float
    cluster: int


class ClusterResponse(BaseModel):
    """Response for clustering endpoint."""
    points: List[ClusterPoint]
    n_clusters: int
    explained_variance: float
    cluster_sizes: List[List[int]]


# ── Explainability ──────────────────────────────────────────────────────────


class ExplainRequest(BaseModel):
    """Request body for generating visual explanations."""
    image_path: str = Field(..., description="Path to the image to explain")
    query: str = Field(..., min_length=1, description="Search query that produced this result")


class ExplainResponse(BaseModel):
    """Response with visual explanation data."""
    similarity: float
    query: str
    image_path: str
    heatmap_base64: str = Field(..., description="Base64-encoded heatmap overlay image")
    annotated_base64: str = Field(..., description="Base64-encoded annotated image with score")

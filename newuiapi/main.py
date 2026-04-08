"""
FastAPI backend for Semantic Image Search.

Exposes all core functionality (text search, image search, video search,
indexing, explainability, clustering, feedback) as REST APIs for a
React frontend.

Run with:
    cd d:\\project\\college\\imageproject
    uvicorn newuiapi.main:app --reload --host 0.0.0.0 --port 8000
"""

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .dependencies import app_state
from .routers import search, index, match, explain, cluster, feedback
from core import config


# ── Lifespan: load models at startup ────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load CLIP model and initialize search engine at startup."""
    print("=" * 60)
    print("[STARTUP] Semantic Image Search API - Starting up...")
    print("  Loading CLIP model (this may take a moment)...")
    print("=" * 60)

    app_state.initialize()

    is_indexed = app_state.searcher.is_indexed() if app_state.searcher else False
    image_count = len(app_state.searcher.metadata) if (app_state.searcher and app_state.searcher.metadata) else 0

    print("=" * 60)
    print("[OK] Models loaded successfully!")
    print(f"  Index ready : {is_indexed}")
    print(f"  Images      : {image_count}")
    print(f"  Swagger docs: http://localhost:8000/docs")
    print("=" * 60)

    yield  # App is running

    print("[SHUTDOWN] Semantic Image Search API stopped.")


# ── FastAPI app ─────────────────────────────────────────────────────────────


app = FastAPI(
    title="Semantic Image Search API",
    description=(
        "REST API for CLIP-powered semantic image retrieval.\n\n"
        "**Features:** Text search, image search, video frame search, "
        "indexing, explainability, clustering, and relevance feedback.\n\n"
        "Built on top of the existing `core/` module without modifications."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS middleware ─────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React (Create React App)
        "http://localhost:5173",    # Vite default
        "http://localhost:5174",    # Vite alternate
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Mount routers ───────────────────────────────────────────────────────────

app.include_router(search.router)
app.include_router(index.router)
app.include_router(match.router)
app.include_router(explain.router)
app.include_router(cluster.router)
app.include_router(feedback.router)


# ── Root & utility endpoints ────────────────────────────────────────────────


@app.get("/", tags=["Health"])
def health_check():
    """
    Health check endpoint.

    Returns API status, model loading state, and index readiness.
    """
    is_indexed = False
    image_count = 0

    if app_state.is_ready and app_state.searcher:
        is_indexed = app_state.searcher.is_indexed()
        if app_state.searcher.metadata:
            image_count = len(app_state.searcher.metadata)

    return {
        "status": "ok",
        "service": "Semantic Image Search API",
        "version": "1.0.0",
        "model_loaded": app_state.is_ready,
        "index_ready": is_indexed,
        "image_count": image_count,
    }


@app.get("/files/image", tags=["Files"])
def serve_image(
    path: str = Query(..., description="Absolute path to the image file"),
):
    """
    Serve an image file from the local filesystem.

    Used by the React frontend to display images from search results.
    Only serves files with supported image extensions as a security measure.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file.")

    if file_path.suffix.lower() not in config.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_path.suffix}. "
                   f"Supported: {', '.join(sorted(config.SUPPORTED_EXTENSIONS))}",
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
    )

@app.get("/files/video", tags=["Files"])
def serve_video(
    path: str = Query(..., description="Absolute path to the video file"),
):
    """
    Serve a video file from the local filesystem for HTML5 playback.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file.")

    supported = [".mp4", ".mkv", ".avi", ".webm"]
    if file_path.suffix.lower() not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_path.suffix}. Supported: {', '.join(supported)}",
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
    )

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
        "http://localhost:1420",    # Tauri dev
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:1420",
        "tauri://localhost",
        "https://tauri.localhost",
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
    Only serves files that are part of the indexed collection.
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

    # Security: only serve images that belong to the indexed collection.
    # Prevents arbitrary file access via path manipulation.
    if app_state.is_ready and app_state.searcher and app_state.searcher.metadata:
        indexed_paths = set(app_state.searcher.metadata.values())
        resolved = str(file_path.resolve())
        if resolved not in indexed_paths:
            raise HTTPException(
                status_code=403,
                detail="Access denied: file is not in the indexed collection.",
            )
    else:
        raise HTTPException(
            status_code=403,
            detail="No index loaded. Cannot verify file access.",
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


# ── Native file dialogs ─────────────────────────────────────────────────────
# These endpoints use tkinter to open native OS file/directory dialogs.
# They are used when running as a local desktop app. In the Tauri desktop
# build, these can be replaced by Tauri's dialog API.
# These endpoints are not part of the core retrieval pipeline.

import tkinter as tk
from tkinter import filedialog
import threading
import queue

def _open_file_dialog(q, filetypes):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(filetypes=filetypes)
    root.destroy()
    q.put(file_path)

def _open_dir_dialog(q):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    dir_path = filedialog.askdirectory()
    root.destroy()
    q.put(dir_path)

@app.get("/system/select-file", tags=["System"])
def system_select_file(filetypes: str = Query(..., description="Comma separated extensions, e.g. .mp4,.avi")):
    """Open native file dialog on the host to select a file."""
    try:
        exts = [f"*{ext.strip()}" for ext in filetypes.split(",")]
        # Needs to run in main thread or simple thread
        q = queue.Queue()
        t = threading.Thread(target=_open_file_dialog, args=(q, [("Files", " ".join(exts)), ("All files", "*.*")]))
        t.start()
        t.join()
        file_path = q.get()
        return {"path": file_path or ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/select-directory", tags=["System"])
def system_select_directory():
    """Open native directory dialog on the host to select a folder."""
    try:
        q = queue.Queue()
        t = threading.Thread(target=_open_dir_dialog, args=(q,))
        t.start()
        t.join()
        dir_path = q.get()
        return {"path": dir_path or ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/stop", tags=["System"])
def system_stop():
    """Request ongoing operations to stop gracefully."""
    app_state.stop_requested = True
    return {"message": "Stop requested."}


import os
from pathlib import Path
from datetime import datetime

# Application Directory (resolves to the root of the project)
APP_DIR = Path(__file__).resolve().parent.parent

# Storage configuration
STORAGE_DIR = APP_DIR / "storage"
EMBEDDINGS_PATH = STORAGE_DIR / "embeddings.npy"
METADATA_PATH = STORAGE_DIR / "metadata.json"
FAISS_INDEX_PATH = STORAGE_DIR / "faiss.index"
SEARCH_HISTORY_PATH = STORAGE_DIR / "search_history.json"
FEEDBACK_PATH = STORAGE_DIR / "feedback.json"
MODEL_FINGERPRINT_PATH = STORAGE_DIR / "model_fingerprint.json"

# Logging configuration
LOGS_DIR = APP_DIR / "logs"
LOG_FILE = LOGS_DIR / f"app_{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"

# Model configuration

MODEL_NAME = "ViT-B/32"
EMBEDDING_DIM = 512

# MODEL_NAME = "ViT-L/14"
# EMBEDDING_DIM = 768

MAX_QUERY_LENGTH = 77  # CLIP token limit

# Optional: Path to a local CLIP model file.
# Set to a valid path (e.g. APP_DIR / "models" / "ViT-B-32.pt") to load from disk
# instead of downloading. If None or the path doesn't exist, falls back to download.
CLIP_MODEL_PATH = None

# Indexing configuration
BATCH_SIZE = 32
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
DEFAULT_TOP_K = 10

# Reranking configuration
ENABLE_RERANKING = True
RERANKING_CANDIDATES = 20  # Retrieve this many from FAISS, then rerank

# Query expansion
ENABLE_QUERY_EXPANSION = True

# Video search configuration
VIDEO_FRAME_FPS = 1        # Frames per second to extract from video
VIDEO_MAX_FRAMES = 300     # Safety limit on extracted frames

# Embedding cache
EMBEDDING_CACHE_SIZE = 128  # Max cached text embeddings


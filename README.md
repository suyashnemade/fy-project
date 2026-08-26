
# Seekr — Semantic Image & Video Search Engine

An offline semantic multimedia retrieval application powered by **CLIP (ViT-B/32)** and **FAISS**. Search through local image and video collections using natural language queries or visual matching, completely offline.


## Features

* **Text-to-Image Search:** Find images using natural language queries (e.g., "a cat sitting on a couch").
* **Image-to-Image Search (Reverse Search):** Upload an image to find visually similar ones
* **Video Scene Search:** Search for specific scenes inside a video using natural language queries.
* **Fast Vector Retrieval:** Powered by FAISS `IndexFlatIP` for exact cosine similarity search across pre-computed image embeddings.
* **User Relevance Feedback:** User ratings (↑/↓) record relevance feedback to gently adjust score boosts for future searches of the same query.
* **Visual Explainability:** Gradient-based attribution heatmaps showing *why* an image matched a specific text query.
* **Semantic Clustering:** KMeans clustering with PCA projection for 2D visualization of how your image collection groups semantically.
* **Desktop App:** React (Vite) frontend with dark/light mode, lightbox, grid views, and real-time indexing, packaged for desktop with Tauri.
## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* Node.js v18+ and npm
* ~1 GB disk space (for initial CLIP model download and FAISS storage)

### 1. Setting up the Backend

```bash
# Clone the repository
git clone https://github.com/suyashnemade/seekr.git
cd seekr

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python requirements
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn newuiapi.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be available at `http://localhost:8000`.

### 2. Setting up the Frontend

```bash
cd newui
npm install
npm run dev
```

The web application will open at `http://localhost:5173`.

## 📖 Usage Guide

### 1. Indexing Your Collection
Click **Load Directory** in the UI and select a folder containing your images. The backend incrementally scans images, encodes them via CLIP, and appends embeddings to the FAISS index. Already-indexed images are skipped automatically.

### 2. Searching
- **Text Search**: Type natural language queries (e.g., "sunset over mountains") to find matching images.
- **Image Search**: Upload an image to find visually similar ones via CLIP's visual embedding space.
- **Video Search**: Select a video file, index its frames, then search for specific scenes by text.

### 3. Relevance Feedback
Click 👍 or 👎 on search results. The system records this feedback and applies small score adjustments to future runs of the same query.

## Architecture

The project follows a decoupled 3-layer architecture for offline desktop deployment:

```
┌──────────────────────────────────────────────────┐
│  React + Vite Frontend (newui/)                  │
│  Sidebar, ImageGrid, Lightbox, Settings, etc.    │
├──────────────────────────────────────────────────┤
│  FastAPI REST Backend (newuiapi/)                 │
│  Routers → Service Layer → Pydantic Schemas      │
├──────────────────────────────────────────────────┤
│  AI Core Engine (core/)                          │
│  CLIP model, FAISS index, Features, Clustering,  │
│  Explainability, Feedback, Logging               │
└──────────────────────────────────────────────────┘
```

1. **AI Core Engine (`core/`)**: Handles CLIP model loading, FAISS vector indexing, prompt ensemble query expansion, relevance feedback, image clustering, gradient-based explainability, and video frame extraction.
2. **REST API Backend (`newuiapi/`)**: FastAPI server with 6 router modules exposing endpoints for search, indexing, explainability, clustering, matching, and feedback.
3. **Web Frontend (`newui/`)**: React + Vite SPA with Tauri desktop packaging.

## Project Structure

```text
├── core/                  # AI Core Engine
│   ├── features/          # Feature modules
│   │   ├── text_to_image.py       # Text query → image retrieval (with query expansion + LRU cache)
│   │   ├── image_to_image.py      # Image query → similar image retrieval
│   │   ├── image_text_matching.py # Cosine similarity scoring
│   │   └── video_search.py        # Video frame extraction + search
│   ├── clip_model.py      # CLIP ViT-B/32 wrapper with batch encoding
│   ├── clustering.py      # KMeans++ clustering & PCA visualization (numpy only)
│   ├── config.py          # Centralized configuration
│   ├── explainability.py  # Gradient-based visual attribution heatmaps
│   ├── feedback.py        # User relevance feedback storage & score boosting
│   ├── indexer.py         # Incremental FAISS indexing with model fingerprinting
│   ├── logger.py          # Rotating file + console logging
│   ├── search.py          # Search orchestrator (routes to feature modules)
│   └── utils.py           # File discovery & serialization helpers
├── newuiapi/              # FastAPI REST Backend
│   ├── routers/           # Endpoint modules (search, index, feedback, explain, cluster, match)
│   ├── dependencies.py    # Singleton application state & DI
│   ├── main.py            # FastAPI entry point with CORS, lifespan, file serving
│   ├── models.py          # Pydantic request/response schemas
│   └── services.py        # Service layer bridging API ↔ core
├── newui/                 # React + Vite Frontend
│   ├── src/               # React components (Sidebar, ImageGrid, Lightbox, etc.)
│   └── src-tauri/         # Tauri desktop packaging configuration
├── tests/                 # Pytest unit test suite
├── requirements.txt       # Python dependencies
├── HOW_TO_RUN.md          # Detailed setup and execution guide
└── build_backend.ps1      # Packaging script for Tauri backend sidecar
```
## Built With

* [CLIP by OpenAI](https://github.com/openai/CLIP) — Multimodal vision-language understanding
* [FAISS by Meta](https://github.com/facebookresearch/faiss) — High-performance vector similarity search
* [FastAPI](https://fastapi.tiangolo.com/) — Asynchronous Python web framework
* [React](https://react.dev/) & [Vite](https://vitejs.dev/) — Modern frontend UI engine
* [Tauri](https://tauri.app/) — Desktop application packaging
* [OpenCV](https://opencv.org/) — Video frame extraction


## Note

I built this project as my final-year project. Feel free to download it, explore the code, and experiment with it. Feedback and suggestions are always welcome.

If you find this project helpful or interesting, feel free to give it a ⭐ on GitHub!

**Find Me on Social Media**

* LinkedIn: [https://www.linkedin.com/in/suyashnemade](https://www.linkedin.com/in/suyashnemade)
* GitHub: [https://github.com/suyashnemade](https://github.com/suyashnemade)
* X: [https://x.com/suyashx_](https://x.com/suyashx_)


## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
# Semantic Image & Video Search Engine

An advanced, offline semantic multimedia retrieval application powered by **CLIP (ViT-B/32)** and **FAISS**. This project allows you to search through your local image and video collections using natural language queries or visual matching, completely offline.

## 🌟 Key Features

* **Text-to-Image Search:** Find images using natural language queries (e.g., "a cat sitting on a couch", "cyberpunk city") with multi-prompt ensemble query expansion.
* **Image-to-Image Search (Reverse Search):** Upload an image to find visually similar ones in your indexed database using CLIP visual embeddings.
* **Video Scene Search:** Search for specific scenes inside a video file using natural language queries to instantly locate the exact timestamp matching your description.
* **Fast Vector Retrieval:** Powered by FAISS (`IndexFlatIP`) for exact inner-product vector similarity search across pre-computed image embeddings.
* **User Relevance Feedback:** User interactions (↑/↓) record relevance feedback to gently adjust score boosts for future searches of identical queries.
* **Advanced Explainability:** MS COCO-style visual heatmaps using gradient-based attribution to visualize *why* an image matched a specific text query.
* **Modern Web UI & Desktop Packaging:** A responsive React (Vite) frontend with dark/light mode, lightbox, grid views, and real-time indexing status, packaged with Tauri.

---

## 🏗️ Architecture

The project follows a decoupled service architecture designed for offline desktop deployment:

1. **AI Core Engine (`core/`)**: The algorithmic core. Handles CLIP model loading, FAISS vector indexing, prompt ensemble query expansion, relevance feedback storage, image clustering, explainability, and OpenCV video frame extraction.
2. **REST API Backend (`newuiapi/`)**: A fast Python FastAPI server providing endpoints for search, indexing, explainability, and system utilities for local desktop communication.
3. **Web Frontend (`newui/`)**: A modern Single Page Application (SPA) built with React and Vite, packaged for desktop execution via Tauri.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* Node.js v18+ and npm
* ~1 GB disk space (for initial CLIP model download and FAISS storage)

### 1. Setting up the Backend

1. **Clone the repository and install dependencies**:
   ```bash
   # Create a virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install Python requirements
   pip install -r requirements.txt
   ```
   *(Note: Ensure you have `opencv-python` installed for video search functionality).*

2. **Start the FastAPI Server**:
   ```bash
   uvicorn newuiapi.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend API will be available at `http://localhost:8000`. Automated Swagger documentation is available at `http://localhost:8000/docs`.

### 2. Setting up the Frontend

1. **Navigate to the frontend directory**:
   ```bash
   cd newui
   ```

2. **Install node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   The web application will open in your browser at `http://localhost:5173`.

---

## 📖 Usage Guide

### 1. Indexing Your Collection
Before searching, build an index of your image collection:
- In the Web UI, click the **Load Directory** button at the top.
- Select a folder containing your images. The backend incrementally scans images, tensorizes them via CLIP, and appends embeddings to the FAISS index.

### 2. Performing Searches
Use the left sidebar to switch between search modes:
- **Text Search**: Type natural language queries to find images.
- **Image Search**: Upload an image to find visually similar ones.
- **Video Search**: Provide a local video path and type a query. The engine extracts frames at a configurable FPS and finds matching timestamps.

### 3. Relevance Feedback
Click **Thumbs Up (👍)** on relevant search results. The system records this feedback and applies small score adjustments to future runs of the same query.

---

## 📁 Project Structure

```text
├── core/                  # Core Machine Learning & AI logic
│   ├── features/          # Feature modules (Image, text, and video search)
│   ├── clip_model.py      # OpenAI CLIP model wrapper & batch encoding
│   ├── clustering.py      # KMeans clustering & PCA visualization
│   ├── explainability.py  # Visual attribution heatmaps
│   ├── feedback.py        # User relevance feedback storage
│   ├── indexer.py         # Incremental FAISS indexing
│   ├── logger.py          # Centralized logging configuration
│   ├── search.py          # Main search orchestrator facade
│   └── utils.py           # Serialization & helper utilities
├── newui/                 # React + Vite Frontend & Tauri Desktop App
│   ├── src/               # React UI components (Sidebar, Lightbox, etc.)
│   └── src-tauri/         # Tauri Rust configuration for desktop packaging
├── newuiapi/              # FastAPI Backend Server
│   ├── routers/           # REST endpoints (Search, Index, Feedback, Explain, Cluster)
│   ├── dependencies.py    # Singleton application state injection
│   ├── main.py            # FastAPI application entry point
│   ├── models.py          # Pydantic schemas
│   └── services.py        # Service layer bridging API to AI core
├── storage/               # Autogenerated: FAISS index, metadata, feedback store
├── tests/                 # Pytest unit testing suite
├── build_backend.ps1      # Packaging script for Tauri backend sidecar
├── HOW_TO_RUN.md          # Setup and execution instructions
└── requirements.txt       # Python dependencies
```

## 🛠️ Built With
* [CLIP by OpenAI](https://github.com/openai/CLIP) - Multimodal Vision-Language understanding
* [FAISS by Meta](https://github.com/facebookresearch/faiss) - High-density vector similarity search
* [FastAPI](https://fastapi.tiangolo.com/) - Asynchronous Python web framework
* [React](https://react.dev/) & [Vite](https://vitejs.dev/) - Modern Frontend UI Engine
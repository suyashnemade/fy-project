# Semantic Image & Video Search Engine

An advanced, offline semantic multimedia retrieval application powered by **CLIP (ViT-B/32)** and **FAISS**. This project allows you to search through your local image and video collections using natural language queries or visual matching, completely offline.

## 🌟 Key Features

* **Text-to-Image Search:** Find images using natural language queries (e.g., "a cat sitting on a couch", "cyberpunk city").
* **Image-to-Image Search (Reverse Search):** Upload an image to find visually similar ones in your indexed database.
* **Video Search:** Search for specific frames inside a video file using natural language queries to instantly find the exact timestamp of a scene.
* **Fast Vector Search:** Powered by FAISS (Facebook AI Similarity Search) for near-instant retrieval across large collections.
* **Cross-Encoder Reranking:** Computes precise image-text cosine similarity on top candidates to drastically improve search precision.
* **Relevance Feedback:** Employs a reinforcement learning-inspired feedback loop (👍/👎). User interactions permanently adjust and boost rankings for future searches.
* **Advanced Explainability:** MS COCO-style visual heatmaps (using gradient-based attribution) to explain *why* an image matched a specific query.
* **Modern Web UI:** A beautiful, responsive React (Vite) frontend with dark/light mode, fullscreen lightbox, grid views, and real-time indexing status.

---

## 🏗️ Architecture

The project has transitioned from a simple Streamlit/PyQt application to a robust decoupled service architecture:

1. **AI Core Engine (`core/`)**: The algorithmic brain. Houses CLIP model loading, FAISS indexing (with incremental append support), reranking, feedback storage, and extraction logic (OpenCV for video processing).
2. **REST API Backend (`newuiapi/`)**: A fast, asynchronous FastAPI server providing endpoints for the frontend, serving images locally and streaming search results.
3. **Web Frontend (`newui/`)**: A modern Single Page Application (SPA) built with React and Vite. Beautifully designed with raw CSS for maximal performance and customized themes.
4. **Legacy Desktop App (`desktop_app/`)**: The original PyQt6-based desktop application (maintained for backward compatibility).

---

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* Node.js v18+ and npm
* ~1 GB disk space (for the initial CLIP model download and FAISS storage)

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
   The backend API will be available at `http://localhost:8000`. You can view the automated Swagger documentation at `http://localhost:8000/docs`.

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
   The web application will open in your browser, typically at `http://localhost:5173`.

---

## 📖 Usage Guide

### 1. Indexing Your Collection
Before searching, you must build an index of your images. 
- In the Web UI, click the **Load Directory** button at the top.
- Select a folder containing your images. The backend will incrementally scan, tensorize via CLIP, and save the embeddings to the FAISS index.

### 2. Performing Searches
Use the left sidebar to switch between modes:
- **Text Search**: Type entirely natural sentences.
- **Image Search**: Click to upload an image to find visually similar ones.
- **Video Search**: Provide an absolute path to a local MP4/MKV video and type a query. The engine extracts frames and locates the exact timestamp matching your description.

### 3. Training the Engine
Click the **Thumbs Up (👍)** on highly relevant search results. The system records this. Subsequent searches for the same query will securely boost this image over time.

---

## 📁 Project Structure

```text
├── core/                  # Core Machine Learning & AI logic
│   ├── features/          # Text search, image matching, video framing logic
│   ├── clip_model.py      # OpenAI CLIP wrapper
│   ├── indexer.py         # Incremental FAISS indexing
│   └── reranker.py        # Cross-encoder rescoring
├── newui/                 # React + Vite Frontend Web App
│   └── src/
│       ├── components/    # Reusable React UI (Sidebar, Lightbox, ImageGrid)
│       └── styles/        # CSS variables and component stylesheets
├── newuiapi/              # FastAPI Backend Server
│   └── routers/           # REST endpoints (Search, Index, Feedback, Explain)
├── desktop_app/           # Legacy PyQt6 Desktop Client
├── storage/               # Autogenerated: FAISS index, metadata, feedback DB
├── tests/                 # Unit testing suite
└── requirements.txt       # Python dependencies
```

## 🛠️ Built With
* [CLIP by OpenAI](https://github.com/openai/CLIP) - Multimodal Vision-Language understanding
* [FAISS by Meta](https://github.com/facebookresearch/faiss) - High-density vector similarity search
* [FastAPI](https://fastapi.tiangolo.com/) - Lightning-fast Python web framework
* [React](https://react.dev/) & [Vite](https://vitejs.dev/) - Modern Frontend Tooling
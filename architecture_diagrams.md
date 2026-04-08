# Semantic Image Search — Architecture & Flow Diagrams

Here are the detailed workflow representations of the application. 

## 1. High-Level Working Diagram
This diagram illustrates how data flows conceptually from the user's interaction in the browser down through the backend and into the AI core, specifically highlighting how representations are passed to the FAISS DB.

```mermaid
graph TD
    User(["User (Browser)"])
    
    subgraph Frontend ["React + Vite Frontend (newui)"]
        UI["Main State (AppNew.jsx)"]
        PC["UI Components (Sidebar, TopBar, Grid, Lightbox)"]
        API_Client["API Fetch Wrapper (api.js)"]
        
        UI -->|"Updates React DOM"| PC
        PC -->|"User clicks / inputs"| UI
        UI -->|"Triggers Request"| API_Client
    end
    
    subgraph Backend ["FastAPI Server (newuiapi)"]
        Routers["Endpoint Routers (search.py, index.py, etc.)"]
        Services["Business Logic (services.py)"]
        
        API_Client -->|"HTTP request (JSON/FormData)"| Routers
        Routers -->|"Validates schema & pass to"| Services
    end

    subgraph CoreEngine ["AI Core Engine (core)"]
        Searcher["ImageSearcher (Main Orchestrator)"]
        Indexer["ImageIndexer (Background processor)"]
        CLIP["CLIP ViT-B/32 (clip_model.py)"]
        
        FAISS_DB[("FAISS Vector Index")]
        MetadataDB[("Metadata DB (JSON)")]
        
        Services -->|"Search calls"| Searcher
        Services -->|"Background tasks"| Indexer
        
        Searcher -->|"Encodes Text/Img queries"| CLIP
        Indexer -->|"Batch encodes Images"| CLIP
        
        Searcher <-->|"Nearest Neighbor Search"| FAISS_DB
        Searcher <-->|"Maps IDs to image paths"| MetadataDB
        
        Indexer -->|"Appends Embeddings"| FAISS_DB
        Indexer -->|"Appends Paths"| MetadataDB
    end

    User -->|"Interacts with UI"| Frontend
    CoreEngine -->|"Returns Search Results"| Backend
    Backend -->|"JSON Response"| Frontend
```

---

## 2. File-to-File Feature Routing Graph
This diagram tracks the exact files triggered from the moment a specific feature is activated in the UI until the core executes the response.

```mermaid
graph LR
    %% Frontend Elements
    subgraph ReactUI ["Frontend UI Components"]
        UI_TEXT("Text Search Box")
        UI_IMAGE("Image Upload Dialog")
        UI_VIDEO("Video Search Panel")
        UI_INDEX("Load Directory (TopBar)")
        UI_FDBK("Thumbs Up/Down (ImageCard)")
    end
    
    %% API Endpoints
    subgraph APIRoutes ["FastAPI Endpoint Routers"]
        R_TXT("routers/search.py: search_text")
        R_IMG("routers/search.py: search_image")
        R_VID("routers/search.py: search_video")
        R_IDX("routers/index.py: index_directory")
        R_FDB("routers/feedback.py: add_feedback")
    end
    
    %% Services Bridge
    subgraph FastAPIService ["Service Layer"]
        S_SRCH("services.py: handle_search")
        S_VID("services.py: handle_video")
        S_IDX("services.py: handle_index")
    end
    
    %% Core Main Controllers
    subgraph CoreMain ["Core Orchestrators"]
        C_SEARCH("core/search.py<br>(ImageSearcher)")
        C_INDEX("core/indexer.py<br>(ImageIndexer)")
        C_FDBK("core/feedback.py<br>(FeedbackStore)")
    end

    %% Specialized Features
    subgraph CoreFeatures ["Machine Learning Feature Implementations"]
        F_TXT("features/text_to_image.py")
        F_IMG("features/image_to_image.py")
        F_VID("features/video_search.py")
        F_RANK("core/reranker.py")
    end

    %% Model
    CLIP_MODEL("core/clip_model.py<br>(PyTorch / CLIP)")

    %% Flows from UI to Router
    UI_TEXT -->|"query"| R_TXT
    UI_IMAGE -->|"image file"| R_IMG
    UI_VIDEO -->|"video path + query"| R_VID
    UI_INDEX -->|"dir path"| R_IDX
    UI_FDBK -->|"isRelevant + query"| R_FDB
    
    %% Router to Services
    R_TXT --> S_SRCH
    R_IMG --> S_SRCH
    R_VID --> S_VID
    R_IDX --> S_IDX
    
    %% Services to Main Controllers
    S_SRCH -->|"search()"| C_SEARCH
    S_SRCH -->|"search_by_image()"| C_SEARCH
    S_VID -->|"search_video()"| C_SEARCH
    S_IDX -->|"index_directory()"| C_INDEX
    R_FDB -->|"add_feedback()"| C_FDBK
    
    %% Main Controllers to Features
    C_SEARCH -->|"delegates to"| F_TXT
    C_SEARCH -->|"delegates to"| F_IMG
    C_SEARCH -->|"delegates to"| F_VID
    C_SEARCH -->|"optional rescore"| F_RANK
    
    %% Features to CLIP Model
    F_TXT -->|"encode text"| CLIP_MODEL
    F_IMG -->|"encode image"| CLIP_MODEL
    C_INDEX -->|"encode batch"| CLIP_MODEL
    F_VID -->|"encode frames"| CLIP_MODEL
    F_RANK -->|"full forward pass"| CLIP_MODEL
```

"""
Streamlit application for semantic image search.
Features: text search, image search, feedback, explainability, clustering.
"""

import streamlit as st
from pathlib import Path
import os
import numpy as np

from core.clip_model import CLIPModel
from core.indexer import ImageIndexer
from core.search import ImageSearcher
from core.feedback import FeedbackStore
from core.explainability import generate_explanation
from core.clustering import compute_clusters, get_result_embeddings
from PIL import Image


# Page configuration
st.set_page_config(
    page_title="Semantic Image Search",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'clip_model' not in st.session_state:
    st.session_state.clip_model = None
if 'indexer' not in st.session_state:
    st.session_state.indexer = None
if 'searcher' not in st.session_state:
    st.session_state.searcher = None
if 'indexed' not in st.session_state:
    st.session_state.indexed = False
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'last_results' not in st.session_state:
    st.session_state.last_results = None


def initialize_models():
    """Initialize CLIP model and related components."""
    if st.session_state.clip_model is None:
        with st.spinner("Loading CLIP model..."):
            st.session_state.clip_model = CLIPModel(device=None)
            st.session_state.indexer = ImageIndexer(st.session_state.clip_model)
            st.session_state.searcher = ImageSearcher(st.session_state.clip_model)


def main():
    """Main application function."""
    st.title("🔍 Semantic Image Search")
    st.markdown("**Offline semantic image search using CLIP and FAISS**")
    st.markdown("---")
    
    # Initialize models on first load
    initialize_models()
    
    # Sidebar for indexing
    with st.sidebar:
        st.header("Index Images")
        directory_path = st.text_input(
            "Image Directory Path",
            value="",
            help="Enter the path to the directory containing images"
        )
        
        index_button = st.button("Index Images", type="primary")
        
        if index_button:
            if not directory_path or not os.path.exists(directory_path):
                st.error("Please enter a valid directory path")
            else:
                with st.spinner("Indexing images... This may take a while."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def progress_callback(current, total):
                        progress = current / total
                        progress_bar.progress(progress)
                        status_text.text(f"Processing {current}/{total} images...")
                    
                    successful, failed = st.session_state.indexer.index_directory(
                        directory_path,
                        progress_callback=progress_callback
                    )
                    
                    progress_bar.progress(1.0)
                    status_text.text("Indexing complete!")
                    
                    st.success(f"Successfully indexed {successful} images")
                    if failed > 0:
                        st.warning(f"Failed to index {failed} images (corrupt or unreadable)")
                    
                    # Reload search index
                    st.session_state.searcher.reload_index()
                    st.session_state.indexed = st.session_state.searcher.is_indexed()
                    
                    # Clear progress bar after a moment
                    st.rerun()
        
        # Check indexing status
        index_path = Path('storage/faiss.index')
        if index_path.exists():
            st.success("✓ Index ready")
            st.session_state.indexed = True
        else:
            st.info("No index found. Please index images first.")
            st.session_state.indexed = False
        
        # Feedback stats
        st.markdown("---")
        st.header("📊 Feedback Stats")
        searcher = st.session_state.searcher
        if searcher and searcher.feedback_store:
            stats = searcher.feedback_store.get_stats()
            st.metric("Total Feedback", stats["total"])
            col1, col2 = st.columns(2)
            col1.metric("👍 Relevant", stats["relevant"])
            col2.metric("👎 Not Relevant", stats["not_relevant"])
    
    # Main search area
    st.header("Search Images")
    
    if not st.session_state.indexed:
        st.info("👈 Please index images first using the sidebar.")
        return
    
    # Search mode selector
    search_mode = st.radio(
        "Search Mode",
        ["🔤 Text Search", "🖼️ Image Search"],
        horizontal=True,
        help="Choose between searching by text description or by uploading a reference image"
    )
    
    # Top-K slider
    top_k = st.slider("Number of results", min_value=1, max_value=50, value=10)
    
    results = None
    query_label = ""
    
    if search_mode == "🔤 Text Search":
        # Text search query input
        query = st.text_input(
            "Enter your search query",
            placeholder="e.g., 'a cat sitting on a couch', 'sunset over mountains'",
            help="Describe what you're looking for in natural language"
        )
        
        search_button = st.button("Search", type="primary")
        
        if search_button and query:
            with st.spinner("Searching..."):
                results = st.session_state.searcher.search(query, top_k=top_k)
            query_label = query
            st.session_state.last_query = query
            st.session_state.last_results = results
    
    else:
        # Image search — upload a reference image
        uploaded_file = st.file_uploader(
            "Upload a reference image",
            type=["jpg", "jpeg", "png", "bmp", "gif", "tiff", "webp"],
            help="Upload an image to find visually similar images in the index"
        )
        
        if uploaded_file is not None:
            query_image = Image.open(uploaded_file)
            st.image(query_image, caption="Query image", width=250)
            
            search_button = st.button("Find Similar Images", type="primary")
            
            if search_button:
                with st.spinner("Searching by image..."):
                    results = st.session_state.searcher.search_by_image(
                        query_image, top_k=top_k
                    )
                query_label = f"image: {uploaded_file.name}"
                st.session_state.last_query = query_label
                st.session_state.last_results = results
    
    # Display results
    if results is not None:
        if not results:
            st.warning("No results found.")
        else:
            st.markdown(f"**Found {len(results)} results:**")
            
            # Show Clusters button
            if len(results) >= 2:
                if st.button("📊 Show Clusters", help="Visualize search results in 2D semantic space"):
                    _show_clusters(results)
            
            st.markdown("---")
            
            num_cols = 3
            cols = st.columns(num_cols)
            
            for idx, (image_path, score) in enumerate(results):
                col = cols[idx % num_cols]
                
                with col:
                    try:
                        img = Image.open(image_path)
                        st.image(img, use_container_width=True)
                        st.caption(f"**Score:** {score:.4f}")
                        st.caption(f"**Path:** {Path(image_path).name}")
                        
                        # Feedback buttons
                        feedback_cols = st.columns(3)
                        
                        with feedback_cols[0]:
                            if st.button("👍", key=f"rel_{idx}", help="Mark as relevant"):
                                _record_feedback(image_path, score, idx, "relevant")
                        
                        with feedback_cols[1]:
                            if st.button("👎", key=f"irr_{idx}", help="Mark as not relevant"):
                                _record_feedback(image_path, score, idx, "not_relevant")
                        
                        with feedback_cols[2]:
                            if st.button("🔍", key=f"exp_{idx}", help="Explain why this was retrieved"):
                                _show_explanation(image_path)
                        
                    except Exception as e:
                        st.error(f"Error loading image: {image_path}")


def _record_feedback(image_path: str, score: float, rank: int, feedback_type: str):
    """Record feedback for a search result."""
    searcher = st.session_state.searcher
    if searcher and searcher.feedback_store:
        searcher.feedback_store.add_feedback(
            query=st.session_state.last_query,
            image_path=image_path,
            feedback=feedback_type,
            original_rank=rank + 1,
            original_score=score
        )
        emoji = "👍" if feedback_type == "relevant" else "👎"
        st.toast(f"{emoji} Feedback recorded!")


def _show_explanation(image_path: str):
    """Show MS COCO-style explainability panel for a search result."""
    query = st.session_state.last_query
    clip_model = st.session_state.clip_model
    
    if not query or not clip_model:
        st.warning("No query context available for explanation.")
        return
    
    with st.spinner("Generating explanation heatmap..."):
        result = generate_explanation(clip_model, image_path, query)
    
    if result:
        st.image(
            result['annotated_image'],
            caption=f"Attention heatmap — Score: {result['similarity']:.4f}",
            use_container_width=True
        )
    else:
        st.error("Failed to generate explanation.")


def _show_clusters(results):
    """Show KMeans + PCA clustering visualization of search results."""
    clip_model = st.session_state.clip_model
    if not clip_model:
        return
    
    image_paths = [path for path, _ in results]
    
    with st.spinner("Computing cluster visualization..."):
        embeddings = get_result_embeddings(clip_model, image_paths)
        
        if embeddings is None:
            st.error("Failed to compute embeddings for clustering.")
            return
        
        n_clusters = min(5, len(image_paths))
        cluster_result = compute_clusters(embeddings, image_paths, n_clusters=n_clusters)
    
    if cluster_result is None:
        st.error("Clustering failed (need at least 2 results).")
        return
    
    import pandas as pd
    
    df = pd.DataFrame(cluster_result['points'])
    
    st.subheader("📊 Semantic Clustering")
    st.scatter_chart(
        df,
        x='x',
        y='y',
        color='cluster',
        size=80,
        use_container_width=True
    )
    
    st.caption(
        f"{cluster_result['n_clusters']} clusters, "
        f"PCA explained variance: {cluster_result['explained_variance']:.1%}  |  "
        f"Cluster sizes: {', '.join(f'C{cid}={cnt}' for cid, cnt in cluster_result['cluster_sizes'])}"
    )
    st.caption("Images positioned by semantic similarity — closer = more similar")


if __name__ == "__main__":
    main()

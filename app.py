"""
Streamlit application for semantic image search.
"""

import streamlit as st
from pathlib import Path
import os

from core.clip_model import CLIPModel
from core.indexer import ImageIndexer
from core.search import ImageSearcher
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


def initialize_models():
    """Initialize CLIP model and related components."""
    if st.session_state.clip_model is None:
        with st.spinner("Loading CLIP model..."):
            st.session_state.clip_model = CLIPModel(device='cpu')
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
    
    # Main search area
    st.header("Search Images")
    
    if not st.session_state.indexed:
        st.info("👈 Please index images first using the sidebar.")
        return
    
    # Search query input
    query = st.text_input(
        "Enter your search query",
        placeholder="e.g., 'a cat sitting on a couch', 'sunset over mountains'",
        help="Describe what you're looking for in natural language"
    )
    
    # Top-K slider
    top_k = st.slider("Number of results", min_value=1, max_value=50, value=10)
    
    # Search button
    search_button = st.button("Search", type="primary")
    
    # Perform search
    if search_button and query:
        with st.spinner("Searching..."):
            results = st.session_state.searcher.search(query, top_k=top_k)
        
        if not results:
            st.warning("No results found.")
        else:
            st.markdown(f"**Found {len(results)} results:**")
            st.markdown("---")
            
            # Display results in a grid
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
                    except Exception as e:
                        st.error(f"Error loading image: {image_path}")


if __name__ == "__main__":
    main()

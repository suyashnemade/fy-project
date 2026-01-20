"""
CustomTkinter desktop application for semantic image search.
"""

import customtkinter as ctk
from pathlib import Path
import os
import threading
from PIL import Image, ImageTk
import tkinter.filedialog as filedialog
import tkinter as tk

from core.clip_model import CLIPModel
from core.indexer import ImageIndexer
from core.search import ImageSearcher


# Configure CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ImageSearchApp(ctk.CTk):
    """Main application window for semantic image search."""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("🔍 Semantic Image Search")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        
        # Initialize models (None initially)
        self.clip_model = None
        self.indexer = None
        self.searcher = None
        self.is_indexed = False
        
        # Directory path for indexing
        self.index_directory = ""
        
        # Create UI
        self.create_widgets()
        
        # Initialize models in background
        self.initialize_models()
        
        # Check if index exists
        self.check_index_status()
    
    def create_widgets(self):
        """Create all UI widgets."""
        # Main container
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Main content
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar for indexing
        self.create_sidebar()
        
        # Main content area for search
        self.create_search_area()
    
    def create_sidebar(self):
        """Create sidebar with indexing controls."""
        sidebar = ctk.CTkFrame(self, width=300)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sidebar.grid_rowconfigure(4, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            sidebar,
            text="Index Images",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 10), padx=20)
        
        # Directory path label
        dir_label = ctk.CTkLabel(sidebar, text="Image Directory:")
        dir_label.grid(row=1, column=0, sticky="w", padx=20, pady=(10, 5))
        
        # Directory path entry
        self.dir_entry = ctk.CTkEntry(
            sidebar,
            placeholder_text="Select directory...",
            width=260
        )
        self.dir_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Browse button
        browse_btn = ctk.CTkButton(
            sidebar,
            text="Browse",
            command=self.browse_directory,
            width=120
        )
        browse_btn.grid(row=3, column=0, padx=20, pady=(0, 10))
        
        # Index button
        self.index_btn = ctk.CTkButton(
            sidebar,
            text="Index Images",
            command=self.index_images,
            state="disabled",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.index_btn.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="s")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(sidebar)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            sidebar,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.grid(row=6, column=0, padx=20, pady=(0, 10))
        self.progress_label.grid_remove()
        
        # Status label
        self.status_label = ctk.CTkLabel(
            sidebar,
            text="No index found",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.grid(row=7, column=0, padx=20, pady=(0, 20))
        
        # Loading label (for model initialization)
        self.loading_label = ctk.CTkLabel(
            sidebar,
            text="Loading CLIP model...",
            font=ctk.CTkFont(size=12),
            text_color="yellow"
        )
        self.loading_label.grid(row=8, column=0, padx=20, pady=(0, 20))
    
    def create_search_area(self):
        """Create main search area with query input and results."""
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        search_frame.grid_columnconfigure(0, weight=1)
        search_frame.grid_rowconfigure(2, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            search_frame,
            text="Semantic Image Search",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 10), padx=20)
        
        subtitle_label = ctk.CTkLabel(
            search_frame,
            text="Offline semantic image search using CLIP and FAISS",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.grid(row=0, column=0, pady=(50, 10), padx=20)
        
        # Search input frame
        search_input_frame = ctk.CTkFrame(search_frame)
        search_input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        search_input_frame.grid_columnconfigure(0, weight=1)
        
        # Query entry
        self.query_entry = ctk.CTkEntry(
            search_input_frame,
            placeholder_text="Enter your search query (e.g., 'a cat sitting on a couch', 'sunset over mountains')",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.query_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.query_entry.bind("<Return>", lambda e: self.perform_search())
        
        # Top-K slider frame
        slider_frame = ctk.CTkFrame(search_input_frame)
        slider_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        slider_frame.grid_columnconfigure(0, weight=1)
        
        top_k_label = ctk.CTkLabel(
            slider_frame,
            text="Number of results:",
            font=ctk.CTkFont(size=12)
        )
        top_k_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.top_k_var = ctk.IntVar(value=10)
        self.top_k_slider = ctk.CTkSlider(
            slider_frame,
            from_=1,
            to=50,
            number_of_steps=49,
            variable=self.top_k_var,
            command=self.update_top_k_label
        )
        self.top_k_slider.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="ew", columnspan=2)
        slider_frame.grid_columnconfigure(1, weight=1)
        
        self.top_k_value_label = ctk.CTkLabel(
            slider_frame,
            text="10",
            font=ctk.CTkFont(size=12)
        )
        self.top_k_value_label.grid(row=0, column=3, padx=(10, 20), pady=(10, 5))
        
        # Search button
        self.search_btn = ctk.CTkButton(
            search_input_frame,
            text="Search",
            command=self.perform_search,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.search_btn.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Results area (scrollable)
        results_frame = ctk.CTkFrame(search_frame)
        results_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)
        
        # Scrollable frame for results
        self.results_canvas = ctk.CTkScrollableFrame(
            results_frame,
            label_text="Search Results"
        )
        self.results_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.results_canvas.grid_columnconfigure(0, weight=1)
        
        # Info label
        self.info_label = ctk.CTkLabel(
            search_frame,
            text="👈 Please index images first using the sidebar.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.info_label.grid(row=2, column=0, padx=20, pady=20)
    
    def update_top_k_label(self, value):
        """Update the top-k value label."""
        self.top_k_value_label.configure(text=str(int(value)))
    
    def browse_directory(self):
        """Open directory browser dialog."""
        directory = filedialog.askdirectory(title="Select Image Directory")
        if directory:
            self.index_directory = directory
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.index_btn.configure(state="normal")
    
    def initialize_models(self):
        """Initialize CLIP model and related components in background thread."""
        def load_models():
            try:
                self.clip_model = CLIPModel(device='cpu')
                self.indexer = ImageIndexer(self.clip_model)
                self.searcher = ImageSearcher(self.clip_model)
                
                # Update UI on main thread
                self.after(0, self.on_models_loaded)
            except Exception as e:
                self.after(0, lambda: self.on_model_load_error(str(e)))
        
        thread = threading.Thread(target=load_models, daemon=True)
        thread.start()
    
    def on_models_loaded(self):
        """Callback when models are loaded."""
        self.loading_label.grid_remove()
        self.check_index_status()
    
    def on_model_load_error(self, error_msg):
        """Callback when model loading fails."""
        self.loading_label.configure(
            text=f"Error loading model: {error_msg}",
            text_color="red"
        )
    
    def check_index_status(self):
        """Check if index exists and update status."""
        index_path = Path('storage/faiss.index')
        if index_path.exists() and self.searcher:
            self.searcher.reload_index()
            self.is_indexed = self.searcher.is_indexed()
            
            if self.is_indexed:
                self.status_label.configure(
                    text="✓ Index ready",
                    text_color="green"
                )
                self.search_btn.configure(state="normal")
                self.info_label.grid_remove()
                self.results_canvas.grid()
            else:
                self.status_label.configure(
                    text="No index found",
                    text_color="gray"
                )
                self.search_btn.configure(state="disabled")
        else:
            self.is_indexed = False
            self.status_label.configure(
                text="No index found",
                text_color="gray"
            )
            self.search_btn.configure(state="disabled")
    
    def index_images(self):
        """Index images in the selected directory."""
        if not self.index_directory or not os.path.exists(self.index_directory):
            self.show_error("Please select a valid directory path")
            return
        
        if not self.indexer:
            self.show_error("Models are still loading. Please wait...")
            return
        
        # Disable indexing button
        self.index_btn.configure(state="disabled")
        
        # Show progress bar
        self.progress_bar.grid()
        self.progress_label.grid()
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting indexing...")
        
        def index_thread():
            try:
                def progress_callback(current, total):
                    progress = current / total
                    self.after(0, lambda: self.progress_bar.set(progress))
                    self.after(0, lambda: self.progress_label.configure(
                        text=f"Processing {current}/{total} images..."
                    ))
                
                successful, failed = self.indexer.index_directory(
                    self.index_directory,
                    progress_callback=progress_callback
                )
                
                # Reload search index
                self.searcher.reload_index()
                self.is_indexed = self.searcher.is_indexed()
                
                # Update UI on main thread
                self.after(0, lambda: self.on_indexing_complete(successful, failed))
            except Exception as e:
                self.after(0, lambda: self.on_indexing_error(str(e)))
        
        thread = threading.Thread(target=index_thread, daemon=True)
        thread.start()
    
    def on_indexing_complete(self, successful, failed):
        """Callback when indexing is complete."""
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Indexing complete!")
        
        # Update status
        if successful > 0:
            self.status_label.configure(
                text=f"✓ Index ready ({successful} images)",
                text_color="green"
            )
            self.is_indexed = True
            self.search_btn.configure(state="normal")
            self.info_label.grid_remove()
            self.results_canvas.grid()
        
        # Show result message
        msg = f"Successfully indexed {successful} images"
        if failed > 0:
            msg += f"\nFailed to index {failed} images (corrupt or unreadable)"
        
        self.show_info(msg)
        
        # Hide progress after a moment
        self.after(2000, lambda: (
            self.progress_bar.grid_remove(),
            self.progress_label.grid_remove()
        ))
        
        # Re-enable button
        self.index_btn.configure(state="normal")
    
    def on_indexing_error(self, error_msg):
        """Callback when indexing fails."""
        self.progress_bar.grid_remove()
        self.progress_label.grid_remove()
        self.show_error(f"Error during indexing: {error_msg}")
        self.index_btn.configure(state="normal")
    
    def perform_search(self):
        """Perform semantic search."""
        query = self.query_entry.get().strip()
        
        if not query:
            self.show_error("Please enter a search query")
            return
        
        if not self.is_indexed or not self.searcher:
            self.show_error("Please index images first")
            return
        
        # Disable search button
        self.search_btn.configure(state="disabled", text="Searching...")
        
        def search_thread():
            try:
                top_k = self.top_k_var.get()
                results = self.searcher.search(query, top_k=top_k)
                
                # Update UI on main thread
                self.after(0, lambda: self.display_results(results, query))
            except Exception as e:
                self.after(0, lambda: self.on_search_error(str(e)))
            finally:
                self.after(0, lambda: self.search_btn.configure(
                    state="normal",
                    text="Search"
                ))
        
        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()
    
    def display_results(self, results, query):
        """Display search results in a grid."""
        # Clear previous results
        for widget in self.results_canvas.winfo_children():
            widget.destroy()
        
        if not results:
            no_results_label = ctk.CTkLabel(
                self.results_canvas,
                text="No results found.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            no_results_label.grid(row=0, column=0, pady=20)
            return
        
        # Results header
        header_label = ctk.CTkLabel(
            self.results_canvas,
            text=f"Found {len(results)} results for: '{query}'",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.grid(row=0, column=0, columnspan=3, pady=(10, 20), sticky="w")
        
        # Display results in grid (3 columns)
        num_cols = 3
        max_thumb_size = 250
        
        for idx, (image_path, score) in enumerate(results):
            row = (idx // num_cols) + 1
            col = idx % num_cols
            
            # Create frame for each result
            result_frame = ctk.CTkFrame(self.results_canvas)
            result_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            try:
                # Load and resize image
                img = Image.open(image_path)
                img.thumbnail((max_thumb_size, max_thumb_size), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img)
                
                # Create label for image
                img_label = ctk.CTkLabel(
                    result_frame,
                    image=photo,
                    text=""
                )
                img_label.image = photo  # Keep a reference
                img_label.grid(row=0, column=0, padx=10, pady=10)
                
                # Score label
                score_label = ctk.CTkLabel(
                    result_frame,
                    text=f"Score: {score:.4f}",
                    font=ctk.CTkFont(size=12)
                )
                score_label.grid(row=1, column=0, padx=10, pady=(0, 5))
                
                # Filename label
                filename = Path(image_path).name
                filename_label = ctk.CTkLabel(
                    result_frame,
                    text=filename,
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                    wraplength=200
                )
                filename_label.grid(row=2, column=0, padx=10, pady=(0, 10))
                
            except Exception as e:
                error_label = ctk.CTkLabel(
                    result_frame,
                    text=f"Error loading image:\n{Path(image_path).name}",
                    font=ctk.CTkFont(size=11),
                    text_color="red"
                )
                error_label.grid(row=0, column=0, padx=10, pady=10)
    
    def on_search_error(self, error_msg):
        """Callback when search fails."""
        self.show_error(f"Error during search: {error_msg}")
    
    def show_error(self, message):
        """Show error message in a dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        label = ctk.CTkLabel(
            dialog,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        label.pack(pady=30, padx=20)
        
        btn = ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy,
            width=100
        )
        btn.pack(pady=10)
    
    def show_info(self, message):
        """Show info message in a dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Information")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        label = ctk.CTkLabel(
            dialog,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        label.pack(pady=30, padx=20)
        
        btn = ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy,
            width=100
        )
        btn.pack(pady=10)


def main():
    """Main entry point for the application."""
    app = ImageSearchApp()
    app.mainloop()


if __name__ == "__main__":
    main()

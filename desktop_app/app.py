"""
Main application class for the semantic image search desktop app.
Features: text search, image search, video search, image-text matching,
feedback, explainability, clustering.
"""

import customtkinter as ctk
import tkinter as tk
import tkinter.filedialog as filedialog
import threading
import logging
from pathlib import Path
from PIL import Image, ImageTk

# Core imports
from core.clip_model import CLIPModel
from core.indexer import ImageIndexer
from core.search import ImageSearcher
from core.config import FAISS_INDEX_PATH
from core.logger import get_logger

# UI Components
from .theme import COLORS
from .helpers import (
    human_size, 
    load_search_history, 
    save_search_history,
    MAX_HISTORY
)
from .widgets.dialogs import show_dialog
from .widgets.result_card import create_result_card

logger = get_logger(__name__)

# Basic theme setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ImageSearchApp(ctk.CTk):
    """Main application window for semantic image search."""

    def __init__(self):
        super().__init__()

        # -- Window configuration --
        self.title("Semantic Image Search")
        self.geometry("1300x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg_dark"])

        # -- State --
        self.clip_model = None
        self.indexer = None
        self.searcher = None
        self.is_indexed = False
        self.index_directory = ""
        self.search_history: list = load_search_history()
        self._last_results: list = []
        self._last_query: str = ""
        self._photo_refs: list = []  # prevent GC of PhotoImages

        # -- Build UI --
        self._build_layout()
        self.initialize_models()
        self.check_index_status()

    # -- Layout --
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)   # sidebar
        self.grid_columnconfigure(1, weight=1)   # main
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)      # status bar

        self._build_sidebar()
        self._build_main_area()
        self._build_status_bar()

    # -- Sidebar --
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=310, corner_radius=0,
            fg_color=COLORS["bg_sidebar"], border_width=0,
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Indexing section
        ctk.CTkLabel(self.sidebar, text="📁  INDEX IMAGES", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=COLORS["accent"], anchor="w").grid(row=0, column=0, sticky="w", padx=24, pady=(20, 8))
        ctk.CTkLabel(self.sidebar, text="Image Directory", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"], anchor="w").grid(row=1, column=0, sticky="w", padx=24)

        dir_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        dir_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 8))
        dir_frame.grid_columnconfigure(0, weight=1)

        self.dir_entry = ctk.CTkEntry(dir_frame, placeholder_text="Select directory…", height=34, corner_radius=8, fg_color=COLORS["bg_card"], border_color=COLORS["border"], text_color=COLORS["text_primary"])
        self.dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        browse_btn = ctk.CTkButton(dir_frame, text="📂", width=36, height=34, corner_radius=8, fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"], command=self.browse_directory)
        browse_btn.grid(row=0, column=1)

        self.index_btn = ctk.CTkButton(self.sidebar, text="⚡  Index Images", height=38, corner_radius=10, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color="#000000", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), command=self.index_images, state="disabled")
        self.index_btn.grid(row=3, column=0, padx=24, pady=(4, 8), sticky="ew")

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self.sidebar, height=6, corner_radius=3, progress_color=COLORS["accent"])
        self.progress_bar.grid(row=4, column=0, padx=24, sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        self.progress_label = ctk.CTkLabel(self.sidebar, text="", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"])
        self.progress_label.grid(row=5, column=0, padx=24, pady=(4, 0))
        self.progress_label.grid_remove()

        # Status
        self.status_label = ctk.CTkLabel(self.sidebar, text="● No index found", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="w")
        self.status_label.grid(row=6, column=0, sticky="w", padx=24, pady=(8, 4))
        self.loading_label = ctk.CTkLabel(self.sidebar, text="⏳ Loading model…", font=ctk.CTkFont(size=11), text_color=COLORS["warning"])
        self.loading_label.grid(row=7, column=0, padx=24, pady=(0, 10))

        sep1 = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"])
        sep1.grid(row=8, column=0, sticky="ew", padx=20, pady=10)

        # Tools section
        ctk.CTkLabel(self.sidebar, text="🛠  TOOLS", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=COLORS["accent"], anchor="w").grid(row=9, column=0, sticky="w", padx=24, pady=(0, 6))

        tools_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        tools_frame.grid(row=10, column=0, sticky="ew", padx=20, pady=(0, 4))
        tools_frame.grid_columnconfigure((0, 1), weight=1)

        self.video_search_btn = ctk.CTkButton(
            tools_frame, text="🎬 Video Search", height=32, corner_radius=8,
            fg_color=COLORS["bg_card"], hover_color=COLORS["accent_dim"],
            text_color=COLORS["text_secondary"], font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self.perform_video_search, state="disabled"
        )
        self.video_search_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)

        self.match_score_btn = ctk.CTkButton(
            tools_frame, text="📏 Match Score", height=32, corner_radius=8,
            fg_color=COLORS["bg_card"], hover_color=COLORS["accent_dim"],
            text_color=COLORS["text_secondary"], font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self.perform_image_text_match, state="disabled"
        )
        self.match_score_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)

        from .widgets.tooltip import ToolTip
        ToolTip(self.video_search_btn, "Search video frames by text query (requires opencv-python)")
        ToolTip(self.match_score_btn, "Measure how well an image matches a text description")

        sep2 = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"])
        sep2.grid(row=11, column=0, sticky="ew", padx=20, pady=10)

        # History
        hist_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        hist_header.grid(row=12, column=0, sticky="ew", padx=24, pady=(0, 4))
        hist_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hist_header, text="🕑  RECENT SEARCHES", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=COLORS["accent"], anchor="w").grid(row=0, column=0, sticky="w")
        
        self.clear_hist_btn = ctk.CTkButton(hist_header, text="Clear", width=50, height=22, corner_radius=6, fg_color=COLORS["bg_card"], hover_color=COLORS["border"], text_color=COLORS["text_secondary"], font=ctk.CTkFont(size=10), command=self._clear_history)
        self.clear_hist_btn.grid(row=0, column=1, sticky="e")

        self.history_frame = ctk.CTkScrollableFrame(self.sidebar, height=180, fg_color=COLORS["bg_card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.history_frame.grid(row=13, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.history_frame.grid_columnconfigure(0, weight=1)
        self._refresh_history_ui()

    # -- Main Area --
    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 5))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Search", font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"), text_color=COLORS["text_primary"], anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Describe what you're looking for in natural language", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=COLORS["text_muted"], anchor="w").grid(row=1, column=0, sticky="w", pady=(0, 5))

        # Search bar
        search_card = ctk.CTkFrame(self.main_frame, corner_radius=14, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["border"])
        search_card.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 10))
        search_card.grid_columnconfigure(0, weight=1)

        query_row = ctk.CTkFrame(search_card, fg_color="transparent")
        query_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        query_row.grid_columnconfigure(0, weight=1)

        self.query_entry = ctk.CTkEntry(query_row, placeholder_text="e.g. 'a red sports car', 'sunset over mountains' …", height=42, corner_radius=10, font=ctk.CTkFont(family="Segoe UI", size=14), fg_color=COLORS["bg_dark"], border_color=COLORS["border"], text_color=COLORS["text_primary"])
        self.query_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.query_entry.bind("<Return>", lambda e: self.perform_search())

        self.search_btn = ctk.CTkButton(query_row, text="🔍  Search", width=120, height=42, corner_radius=10, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color="#000000", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), command=self.perform_search, state="disabled")
        self.search_btn.grid(row=0, column=1)

        self.img_search_btn = ctk.CTkButton(query_row, text="🖼️", width=42, height=42, corner_radius=10, fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"], text_color=COLORS["text_primary"], font=ctk.CTkFont(size=18), command=self.perform_image_search, state="disabled")
        self.img_search_btn.grid(row=0, column=2, padx=(6, 0))
        from .widgets.tooltip import ToolTip
        ToolTip(self.img_search_btn, "Search by image — upload a reference image to find similar ones")

        # Options row
        opts_row = ctk.CTkFrame(search_card, fg_color="transparent")
        opts_row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        opts_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(opts_row, text="Results:", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"]).grid(row=0, column=0, padx=(0, 6))
        
        self.top_k_var = ctk.IntVar(value=10)
        self.top_k_slider = ctk.CTkSlider(opts_row, from_=1, to=50, number_of_steps=49, variable=self.top_k_var, button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"], progress_color=COLORS["accent_dim"], command=self._update_top_k_label)
        self.top_k_slider.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.top_k_value_label = ctk.CTkLabel(opts_row, text="10", width=30, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["accent"])
        self.top_k_value_label.grid(row=0, column=2)

        # Show Clusters button
        self.clusters_btn = ctk.CTkButton(
            opts_row, text="📊 Clusters", width=90, height=28, corner_radius=6,
            fg_color=COLORS["bg_dark"], hover_color=COLORS["accent_dim"],
            text_color=COLORS["text_secondary"], font=ctk.CTkFont(size=11),
            command=self._show_clusters, state="disabled"
        )
        self.clusters_btn.grid(row=0, column=3, padx=(10, 0))

        # Results area
        self.results_outer = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.results_outer.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 10))
        self.results_outer.grid_columnconfigure(0, weight=1)
        self.results_outer.grid_rowconfigure(0, weight=1)

        self.results_canvas = ctk.CTkScrollableFrame(self.results_outer, fg_color=COLORS["bg_dark"], corner_radius=0, label_text="", label_fg_color="transparent")
        self.results_canvas.grid(row=0, column=0, sticky="nsew")
        self.results_canvas.grid_columnconfigure((0, 1, 2), weight=1)

        self.info_label = ctk.CTkLabel(self.results_outer, text="👈  Index a directory first, then search by describing what you want.", font=ctk.CTkFont(family="Segoe UI", size=14), text_color=COLORS["text_muted"])
        self.info_label.grid(row=0, column=0, padx=20, pady=60)

    # -- Status Bar --
    def _build_status_bar(self):
        self.statusbar = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color=COLORS["bg_sidebar"], border_width=0)
        self.statusbar.grid(row=1, column=1, sticky="ew")
        self.statusbar.grid_columnconfigure(1, weight=1)
        self.statusbar.grid_propagate(False)

        self.sb_left = ctk.CTkLabel(self.statusbar, text="  No index loaded", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=COLORS["text_muted"], anchor="w")
        self.sb_left.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=2)

        self.sb_right = ctk.CTkLabel(self.statusbar, text="Ready  ", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=COLORS["text_muted"], anchor="e")
        self.sb_right.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=2)

    def _update_statusbar(self):
        if FAISS_INDEX_PATH.exists() and self.searcher and self.searcher.metadata:
            idx_size = human_size(FAISS_INDEX_PATH.stat().st_size)
            count = len(self.searcher.metadata)
            self.sb_left.configure(text=f"  📊 {count} images indexed  -  Index size: {idx_size}")
        else:
            self.sb_left.configure(text="  No index loaded")

    # -- Search History --
    def _refresh_history_ui(self):
        for w in self.history_frame.winfo_children():
            w.destroy()
        if not self.search_history:
            ctk.CTkLabel(self.history_frame, text="No recent searches", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"]).grid(row=0, column=0, pady=8)
            return
        for i, q in enumerate(self.search_history):
            btn = ctk.CTkButton(self.history_frame, text=f"  {q}", height=28, anchor="w", corner_radius=6, fg_color="transparent", hover_color=COLORS["border"], text_color=COLORS["text_secondary"], font=ctk.CTkFont(family="Segoe UI", size=11), command=lambda query=q: self._rerun_query(query))
            btn.grid(row=i, column=0, sticky="ew", pady=1, padx=4)

    def _add_to_history(self, query: str):
        if query in self.search_history:
            self.search_history.remove(query)
        self.search_history.insert(0, query)
        self.search_history = self.search_history[:MAX_HISTORY]
        save_search_history(self.search_history)
        self._refresh_history_ui()

    def _clear_history(self):
        self.search_history = []
        save_search_history([])
        self._refresh_history_ui()

    def _rerun_query(self, query: str):
        self.query_entry.delete(0, tk.END)
        self.query_entry.insert(0, query)
        self.perform_search()

    # -- UI Helpers --
    def _update_top_k_label(self, value):
        self.top_k_value_label.configure(text=str(int(value)))

    def browse_directory(self):
        directory = filedialog.askdirectory(title="Select Image Directory")
        if directory:
            self.index_directory = directory
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.index_btn.configure(state="normal")

    # -- Model Loading --
    def initialize_models(self):
        def load_models():
            try:
                self.clip_model = CLIPModel(device=None)
                self.indexer = ImageIndexer(self.clip_model)
                self.searcher = ImageSearcher(self.clip_model)
                self.after(0, self.on_models_loaded)
            except Exception as e:
                logger.error(f"Models failed to load: {e}")
                self.after(0, lambda: self.on_model_load_error(str(e)))
        threading.Thread(target=load_models, daemon=True).start()

    def on_models_loaded(self):
        self.loading_label.grid_remove()
        self.video_search_btn.configure(state="normal")
        self.match_score_btn.configure(state="normal")
        self.check_index_status()

    def on_model_load_error(self, error_msg):
        self.loading_label.configure(text=f"❌ Model error: {error_msg}", text_color=COLORS["error"])

    # -- Index Status --
    def check_index_status(self):
        if FAISS_INDEX_PATH.exists() and self.searcher:
            self.searcher.reload_index()
            self.is_indexed = self.searcher.is_indexed()
            if self.is_indexed:
                self.status_label.configure(text="● Index ready", text_color=COLORS["success"])
                self.search_btn.configure(state="normal")
                self.img_search_btn.configure(state="normal")
                self.info_label.grid_remove()
                self.results_canvas.grid()
            else:
                self._set_no_index()
        else:
            self._set_no_index()
        self._update_statusbar()

    def _set_no_index(self):
        self.is_indexed = False
        self.status_label.configure(text="● No index found", text_color=COLORS["text_muted"])
        self.search_btn.configure(state="disabled")
        self.img_search_btn.configure(state="disabled")

    # -- Indexing --
    def index_images(self):
        if not self.index_directory or not Path(self.index_directory).exists():
            show_dialog(self, "Error", "Please select a valid directory path.", "error")
            return
        if not self.indexer:
            show_dialog(self, "Error", "Models are still loading. Please wait…", "error")
            return

        self.index_btn.configure(state="disabled")
        self.progress_bar.grid()
        self.progress_label.grid()
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting indexing…")

        def index_thread():
            try:
                def progress_callback(current, total):
                    p = current / total
                    self.after(0, lambda: self.progress_bar.set(p))
                    self.after(0, lambda: self.progress_label.configure(text=f"Processing {current}/{total} images…"))

                successful, failed = self.indexer.index_directory(self.index_directory, progress_callback=progress_callback)
                self.searcher.reload_index()
                self.is_indexed = self.searcher.is_indexed()
                self.after(0, lambda: self.on_indexing_complete(successful, failed))
            except Exception as e:
                logger.error(f"Indexing thread failed: {e}")
                self.after(0, lambda: self.on_indexing_error(str(e)))

        threading.Thread(target=index_thread, daemon=True).start()

    def on_indexing_complete(self, successful, failed):
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Indexing complete!")
        if successful > 0:
            self.status_label.configure(text=f"● Index ready ({successful} images)", text_color=COLORS["success"])
            self.is_indexed = True
            self.search_btn.configure(state="normal")
            self.img_search_btn.configure(state="normal")
            self.info_label.grid_remove()
            self.results_canvas.grid()

        msg = f"Successfully indexed {successful} images"
        if failed > 0:
            msg += f"\nFailed to index {failed} images (corrupt/unreadable)"
        show_dialog(self, "Indexing Complete", msg, "info")

        self.after(2500, lambda: (self.progress_bar.grid_remove(), self.progress_label.grid_remove()))
        self.index_btn.configure(state="normal")
        self._update_statusbar()

    def on_indexing_error(self, error_msg):
        self.progress_bar.grid_remove()
        self.progress_label.grid_remove()
        show_dialog(self, "Error", f"Indexing failed: {error_msg}", "error")
        self.index_btn.configure(state="normal")

    # -- Text Search --
    def perform_search(self):
        query = self.query_entry.get().strip()
        if not query:
            show_dialog(self, "Error", "Please enter a search query.", "error")
            return
        if not self.is_indexed or not self.searcher:
            show_dialog(self, "Error", "Please index images first.", "error")
            return

        self._last_query = query
        self.search_btn.configure(state="disabled", text="Searching…")
        self.sb_right.configure(text="Searching…  ")

        def search_thread():
            try:
                top_k = self.top_k_var.get()
                results = self.searcher.search(query, top_k=top_k)
                self.after(0, lambda: self.display_results(results, query))
            except Exception as e:
                logger.error(f"Search thread failed: {e}")
                self.after(0, lambda: show_dialog(self, "Error", f"Search failed: {e}", "error"))
            finally:
                self.after(0, lambda: self.search_btn.configure(state="normal", text="🔍  Search"))

        threading.Thread(target=search_thread, daemon=True).start()

    # -- Image Search --
    def perform_image_search(self):
        """Open a file dialog to select a query image, then search by visual similarity."""
        if not self.is_indexed or not self.searcher:
            show_dialog(self, "Error", "Please index images first.", "error")
            return

        file_path = filedialog.askopenfilename(
            title="Select a query image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        self._last_query = f"🖼️ {Path(file_path).name}"
        self.img_search_btn.configure(state="disabled")
        self.sb_right.configure(text="Searching by image…  ")

        def image_search_thread():
            try:
                query_image = Image.open(file_path)
                top_k = self.top_k_var.get()
                results = self.searcher.search_by_image(query_image, top_k=top_k)
                label = f"🖼️ {Path(file_path).name}"
                self.after(0, lambda: self.display_results(results, label))
            except Exception as e:
                logger.error(f"Image search failed: {e}")
                self.after(0, lambda: show_dialog(self, "Error", f"Image search failed: {e}", "error"))
            finally:
                self.after(0, lambda: self.img_search_btn.configure(state="normal"))

        threading.Thread(target=image_search_thread, daemon=True).start()

    # -- Video Search --
    def perform_video_search(self):
        """Open a dialog to select a video file and text query, then search frames."""
        if not self.clip_model:
            show_dialog(self, "Error", "Models are still loading. Please wait…", "error")
            return

        # Select video file
        video_path = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv"),
                ("All files", "*.*"),
            ],
        )
        if not video_path:
            return

        # Get query from the main search field
        query = self.query_entry.get().strip()
        if not query:
            show_dialog(self, "Info", "Enter a text query in the search bar first,\nthen click Video Search.", "info")
            return

        self.video_search_btn.configure(state="disabled")
        self.sb_right.configure(text="Searching video frames…  ")

        def video_thread():
            try:
                results = self.searcher.search_video(
                    video_path=video_path,
                    query=query,
                    top_k=self.top_k_var.get(),
                )
                self.after(0, lambda: self._display_video_results(results, query, video_path))
            except ImportError:
                self.after(0, lambda: show_dialog(
                    self, "Missing Dependency",
                    "Video search requires opencv-python.\n\nInstall it with:\npip install opencv-python",
                    "error"
                ))
            except Exception as e:
                logger.error(f"Video search failed: {e}")
                self.after(0, lambda: show_dialog(self, "Error", f"Video search failed: {e}", "error"))
            finally:
                self.after(0, lambda: self.video_search_btn.configure(state="normal"))
                self.after(0, lambda: self.sb_right.configure(text="Ready  "))

        threading.Thread(target=video_thread, daemon=True).start()

    def _display_video_results(self, results, query, video_path):
        """Display video search results in a toplevel window."""
        if not results:
            show_dialog(self, "Info", "No matching frames found.", "info")
            return

        from core.features.video_search import format_timestamp

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"🎬 Video Search: {Path(video_path).name}")
        dlg.geometry("900x650")
        dlg.attributes("-topmost", True)
        dlg.configure(fg_color=COLORS["bg_dark"])

        ctk.CTkLabel(
            dlg, text=f"🎬  Top {len(results)} frames for: \"{query}\"",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLORS["accent"], wraplength=800,
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            dlg, text=f"Video: {Path(video_path).name}",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"],
        ).pack(pady=(0, 10))

        # Scrollable frame for results
        scroll = ctk.CTkScrollableFrame(dlg, fg_color=COLORS["bg_dark"])
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        scroll.grid_columnconfigure((0, 1, 2), weight=1)

        for idx, (frame_img, timestamp, score) in enumerate(results):
            row = idx // 3
            col = idx % 3

            card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=COLORS["bg_card"],
                                border_width=1, border_color=COLORS["border"])
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            # Thumbnail
            frame_img_copy = frame_img.copy()
            frame_img_copy.thumbnail((240, 180), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(frame_img_copy)
            self._photo_refs.append(photo)

            img_label = ctk.CTkLabel(card, image=photo, text="")
            img_label.image = photo
            img_label.pack(padx=8, pady=(8, 4))

            # Timestamp + Score
            ts_text = format_timestamp(timestamp)
            score_color = (
                COLORS["score_high"] if score > 0.25
                else COLORS["score_mid"] if score > 0.18
                else COLORS["score_low"]
            )
            ctk.CTkLabel(
                card, text=f"⏱ {ts_text}  •  Score: {score:.4f}",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=score_color,
            ).pack(pady=(0, 6))

        ctk.CTkButton(
            dlg, text="Close", width=100, height=30, corner_radius=8,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            command=dlg.destroy,
        ).pack(pady=(0, 14))

        dlg.bind("<Escape>", lambda e: dlg.destroy())

        # Centre
        dlg.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - dlg.winfo_width()) // 2
        y = (screen_h - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")

    # -- Image-Text Matching --
    def perform_image_text_match(self):
        """Open dialogs to select an image and text, then compute match score."""
        if not self.clip_model:
            show_dialog(self, "Error", "Models are still loading. Please wait…", "error")
            return

        # Select image
        file_path = filedialog.askopenfilename(
            title="Select an image to match",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        # Get text from the main search field
        text = self.query_entry.get().strip()
        if not text:
            show_dialog(self, "Info", "Enter a text description in the search bar first,\nthen click Match Score.", "info")
            return

        self.match_score_btn.configure(state="disabled")
        self.sb_right.configure(text="Computing match score…  ")

        def match_thread():
            try:
                query_image = Image.open(file_path)
                score = self.searcher.compute_image_text_similarity(query_image, text)
                self.after(0, lambda: self._display_match_result(file_path, text, score))
            except Exception as e:
                logger.error(f"Match score failed: {e}")
                self.after(0, lambda: show_dialog(self, "Error", f"Match score failed: {e}", "error"))
            finally:
                self.after(0, lambda: self.match_score_btn.configure(state="normal"))
                self.after(0, lambda: self.sb_right.configure(text="Ready  "))

        threading.Thread(target=match_thread, daemon=True).start()

    def _display_match_result(self, image_path, text, score):
        """Display image-text match result in a dialog."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("📏 Image-Text Match Score")
        dlg.attributes("-topmost", True)
        dlg.configure(fg_color=COLORS["bg_dark"])
        dlg.grab_set()

        # Header
        ctk.CTkLabel(
            dlg, text="📏  Image-Text Match Score",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(16, 8))

        # Image preview
        try:
            img = Image.open(image_path)
            img.thumbnail((350, 350), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._photo_refs.append(photo)
            img_label = ctk.CTkLabel(dlg, image=photo, text="")
            img_label.image = photo
            img_label.pack(padx=20, pady=(0, 8))
        except Exception:
            ctk.CTkLabel(dlg, text="⚠ Could not load image preview",
                         text_color=COLORS["error"]).pack(pady=10)

        # Text query
        ctk.CTkLabel(
            dlg, text=f"Text: \"{text}\"",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"], wraplength=400,
        ).pack(pady=(0, 4))

        # Score display
        score_color = (
            COLORS["score_high"] if score > 0.25
            else COLORS["score_mid"] if score > 0.18
            else COLORS["score_low"]
        )

        if score > 0.25:
            verdict = "Strong match"
        elif score > 0.18:
            verdict = "Moderate match"
        else:
            verdict = "Weak match"

        score_frame = ctk.CTkFrame(dlg, fg_color=COLORS["bg_card"], corner_radius=10)
        score_frame.pack(padx=40, pady=8, fill="x")

        ctk.CTkLabel(
            score_frame, text=f"{score:.4f}",
            font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"),
            text_color=score_color,
        ).pack(pady=(12, 2))

        ctk.CTkLabel(
            score_frame, text=verdict,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 12))

        # Score bar
        bar = ctk.CTkProgressBar(dlg, height=8, corner_radius=4,
                                  progress_color=score_color, fg_color=COLORS["border"])
        bar.pack(padx=40, fill="x")
        bar.set(min(score / 0.35, 1.0))

        ctk.CTkLabel(
            dlg, text=f"Image: {Path(image_path).name}",
            font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"],
        ).pack(pady=(8, 4))

        ctk.CTkButton(
            dlg, text="Close", width=100, height=30, corner_radius=8,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            command=dlg.destroy,
        ).pack(pady=(8, 14))

        dlg.bind("<Escape>", lambda e: dlg.destroy())

        # Centre
        dlg.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - dlg.winfo_width()) // 2
        y = (screen_h - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")

    # -- Display Results --
    def display_results(self, results, query):
        self._add_to_history(query)

        for w in self.results_canvas.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        self._last_results = results

        if not results:
            ctk.CTkLabel(self.results_canvas, text="No results found.", font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"]).grid(row=0, column=0, columnspan=3, pady=40)
            self.sb_right.configure(text="0 results  ")
            self.clusters_btn.configure(state="disabled")
            return

        ctk.CTkLabel(self.results_canvas, text=f"Found {len(results)} results for '{query}'", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=COLORS["text_primary"], anchor="w").grid(row=0, column=0, columnspan=3, sticky="w", pady=(8, 12))
        self.sb_right.configure(text=f"{len(results)} results - '{query}'  ")
        
        # Enable clusters button if enough results
        if len(results) >= 2:
            self.clusters_btn.configure(state="normal")
        else:
            self.clusters_btn.configure(state="disabled")

        # Get feedback store from searcher
        feedback_store = self.searcher.feedback_store if self.searcher else None

        num_cols = 3
        for idx, (image_path, score) in enumerate(results):
            row = (idx // num_cols) + 1
            col = idx % num_cols
            create_result_card(
                self.results_canvas, self, image_path, score, row, col,
                query=self._last_query,
                feedback_store=feedback_store,
                clip_model=self.clip_model,
                rank=idx + 1
            )

    # -- Clustering --
    def _show_clusters(self):
        """Show PCA clustering visualization of current search results."""
        if not self._last_results or len(self._last_results) < 2:
            show_dialog(self, "Info", "Need at least 2 search results for clustering.", "info")
            return
        
        self.sb_right.configure(text="Computing clusters...  ")
        
        def compute():
            try:
                from core.clustering import compute_clusters, get_result_embeddings
                
                image_paths = [path for path, _ in self._last_results]
                embeddings = get_result_embeddings(self.clip_model, image_paths)
                
                if embeddings is None:
                    self.after(0, lambda: show_dialog(self, "Error", "Failed to compute embeddings.", "error"))
                    return
                
                n_clusters = min(5, len(image_paths))
                cluster_result = compute_clusters(embeddings, image_paths, n_clusters=n_clusters)
                
                if cluster_result is None:
                    self.after(0, lambda: show_dialog(self, "Error", "Clustering failed.", "error"))
                    return
                
                self.after(0, lambda: self._display_clusters(cluster_result))
            except Exception as e:
                self.after(0, lambda: show_dialog(self, "Error", f"Clustering failed: {e}", "error"))
            finally:
                self.after(0, lambda: self.sb_right.configure(text="Ready  "))
        
        threading.Thread(target=compute, daemon=True).start()
    
    def _display_clusters(self, cluster_result):
        """Display cluster visualization in a toplevel window using tkinter Canvas."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("📊 Clustering")
        dlg.geometry("700x620")
        dlg.attributes("-topmost", True)
        dlg.configure(fg_color=COLORS["bg_dark"])
        
        ctk.CTkLabel(
            dlg, text="📊  Clustering (KMeans + PCA)",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(16, 4))
        
        # Cluster info
        info_parts = [f"C{cid}={cnt}" for cid, cnt in cluster_result['cluster_sizes']]
        explained = cluster_result['explained_variance']
        ctk.CTkLabel(
            dlg, text=f"{cluster_result['n_clusters']} clusters | PCA variance: {explained:.1%} | {', '.join(info_parts)}",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"],
        ).pack(pady=(0, 10))
        
        # Draw scatter plot on a Canvas
        canvas = tk.Canvas(dlg, width=640, height=480, bg="#0f1117", highlightthickness=0)
        canvas.pack(padx=20, pady=(0, 10))
        
        padding = 40
        plot_w = 640 - 2 * padding
        plot_h = 480 - 2 * padding
        
        # Draw axes
        canvas.create_line(padding, 480 - padding, 640 - padding, 480 - padding, fill="#2a2d3a")
        canvas.create_line(padding, padding, padding, 480 - padding, fill="#2a2d3a")
        
        # Cluster colors
        cluster_colors = ["#00c8a0", "#ff6b6b", "#5b9bd5", "#ffd93d", "#c084fc", "#ff8c42", "#34d399"]
        
        # Plot points with cluster colors
        for item in cluster_result['points']:
            px = padding + int(item['x'] * plot_w)
            py = 480 - padding - int(item['y'] * plot_h)
            
            cluster_id = item.get('cluster', 0)
            color = cluster_colors[cluster_id % len(cluster_colors)]
            
            r = 6
            canvas.create_oval(px - r, py - r, px + r, py + r, fill=color, outline=color)
            
            label = item['label'][:15]
            canvas.create_text(px, py + r + 10, text=label, fill="#8b8fa3", 
                             font=("Segoe UI", 7), anchor="n")
        
        ctk.CTkButton(
            dlg, text="Close", width=100, height=30, corner_radius=8,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            command=dlg.destroy,
        ).pack(pady=(0, 14))
        
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        
        # Centre
        dlg.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - dlg.winfo_width()) // 2
        y = (screen_h - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")


def main():
    """Main entry point."""
    app = ImageSearchApp()
    app.mainloop()

if __name__ == "__main__":
    main()

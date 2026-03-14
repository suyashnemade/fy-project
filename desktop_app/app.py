"""
Main application class for the semantic image search desktop app.
"""

import customtkinter as ctk
import tkinter as tk
import tkinter.filedialog as filedialog
import threading
import logging
from pathlib import Path

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
        self.title("🔍 Semantic Image Search")
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

        # Brand
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(25, 5))
        ctk.CTkLabel(brand_frame, text="🔍", font=ctk.CTkFont(size=32)).pack(side="left", padx=(0, 8))
        title_col = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_col.pack(side="left")
        ctk.CTkLabel(title_col, text="Semantic Search", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(title_col, text="CLIP + FAISS  -  Offline", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=COLORS["text_muted"]).pack(anchor="w")

        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"])
        sep.grid(row=1, column=0, sticky="ew", padx=20, pady=15)

        # Indexing
        ctk.CTkLabel(self.sidebar, text="📁  INDEX IMAGES", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=COLORS["accent"], anchor="w").grid(row=2, column=0, sticky="w", padx=24, pady=(0, 8))
        ctk.CTkLabel(self.sidebar, text="Image Directory", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"], anchor="w").grid(row=3, column=0, sticky="w", padx=24)

        dir_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        dir_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 8))
        dir_frame.grid_columnconfigure(0, weight=1)

        self.dir_entry = ctk.CTkEntry(dir_frame, placeholder_text="Select directory…", height=34, corner_radius=8, fg_color=COLORS["bg_card"], border_color=COLORS["border"], text_color=COLORS["text_primary"])
        self.dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        browse_btn = ctk.CTkButton(dir_frame, text="📂", width=36, height=34, corner_radius=8, fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"], command=self.browse_directory)
        browse_btn.grid(row=0, column=1)

        self.index_btn = ctk.CTkButton(self.sidebar, text="⚡  Index Images", height=38, corner_radius=10, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color="#000000", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), command=self.index_images, state="disabled")
        self.index_btn.grid(row=5, column=0, padx=24, pady=(4, 8), sticky="ew")

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self.sidebar, height=6, corner_radius=3, progress_color=COLORS["accent"])
        self.progress_bar.grid(row=6, column=0, padx=24, sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        self.progress_label = ctk.CTkLabel(self.sidebar, text="", font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"])
        self.progress_label.grid(row=7, column=0, padx=24, pady=(4, 0))
        self.progress_label.grid_remove()

        # Status
        self.status_label = ctk.CTkLabel(self.sidebar, text="● No index found", font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="w")
        self.status_label.grid(row=8, column=0, sticky="w", padx=24, pady=(8, 4))
        self.loading_label = ctk.CTkLabel(self.sidebar, text="⏳ Loading CLIP model…", font=ctk.CTkFont(size=11), text_color=COLORS["warning"])
        self.loading_label.grid(row=9, column=0, padx=24, pady=(0, 10))

        sep2 = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"])
        sep2.grid(row=10, column=0, sticky="ew", padx=20, pady=10)

        # History
        hist_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        hist_header.grid(row=11, column=0, sticky="ew", padx=24, pady=(0, 4))
        hist_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hist_header, text="🕑  RECENT SEARCHES", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=COLORS["accent"], anchor="w").grid(row=0, column=0, sticky="w")
        
        self.clear_hist_btn = ctk.CTkButton(hist_header, text="Clear", width=50, height=22, corner_radius=6, fg_color=COLORS["bg_card"], hover_color=COLORS["border"], text_color=COLORS["text_secondary"], font=ctk.CTkFont(size=10), command=self._clear_history)
        self.clear_hist_btn.grid(row=0, column=1, sticky="e")

        self.history_frame = ctk.CTkScrollableFrame(self.sidebar, height=180, fg_color=COLORS["bg_card"], corner_radius=8, border_width=1, border_color=COLORS["border"])
        self.history_frame.grid(row=12, column=0, sticky="ew", padx=20, pady=(0, 10))
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
        ctk.CTkLabel(header, text="Semantic Image Search", font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"), text_color=COLORS["text_primary"], anchor="w").grid(row=0, column=0, sticky="w")
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

    # -- Search --
    def perform_search(self):
        query = self.query_entry.get().strip()
        if not query:
            show_dialog(self, "Error", "Please enter a search query.", "error")
            return
        if not self.is_indexed or not self.searcher:
            show_dialog(self, "Error", "Please index images first.", "error")
            return

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
            return

        ctk.CTkLabel(self.results_canvas, text=f"Found {len(results)} results for '{query}'", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=COLORS["text_primary"], anchor="w").grid(row=0, column=0, columnspan=3, sticky="w", pady=(8, 12))
        self.sb_right.configure(text=f"{len(results)} results - '{query}'  ")

        num_cols = 3
        for idx, (image_path, score) in enumerate(results):
            row = (idx // num_cols) + 1
            col = idx % num_cols
            create_result_card(self.results_canvas, self, image_path, score, row, col)

def main():
    """Main entry point for testing the module directly."""
    app = ImageSearchApp()
    app.mainloop()

if __name__ == "__main__":
    main()

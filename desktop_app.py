"""
CustomTkinter desktop application for semantic image search.
Redesigned UI with modern aesthetics and practical features.
"""

import customtkinter as ctk
from pathlib import Path
import os
import sys
import threading
import subprocess
import json
import shutil
from datetime import datetime
from PIL import Image, ImageTk
import tkinter.filedialog as filedialog
import tkinter as tk
import io

from core.clip_model import CLIPModel
from core.indexer import ImageIndexer
from core.search import ImageSearcher


# ─── Theme & Colors ───────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Custom colour palette
COLORS = {
    "bg_dark":       "#0f1117",
    "bg_card":       "#1a1d27",
    "bg_sidebar":    "#13151d",
    "accent":        "#00c8a0",
    "accent_hover":  "#00e6b8",
    "accent_dim":    "#007a63",
    "text_primary":  "#e8eaf0",
    "text_secondary":"#8b8fa3",
    "text_muted":    "#555970",
    "border":        "#2a2d3a",
    "score_high":    "#00e676",
    "score_mid":     "#ffd740",
    "score_low":     "#ff5252",
    "error":         "#ff5252",
    "success":       "#00e676",
    "warning":       "#ffd740",
}

SEARCH_HISTORY_PATH = Path("storage/search_history.json")
MAX_HISTORY = 20


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _human_size(nbytes: int) -> str:
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def _open_in_explorer(filepath: str):
    """Open the containing folder in Explorer and select the file."""
    filepath = os.path.normpath(filepath)
    if sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", filepath])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", filepath])
    else:
        subprocess.Popen(["xdg-open", os.path.dirname(filepath)])


def _open_in_default_viewer(filepath: str):
    """Open file in the system default viewer."""
    filepath = os.path.normpath(filepath)
    if sys.platform == "win32":
        os.startfile(filepath)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", filepath])
    else:
        subprocess.Popen(["xdg-open", filepath])


def _load_search_history() -> list:
    """Load search history from disk."""
    if SEARCH_HISTORY_PATH.exists():
        try:
            with open(SEARCH_HISTORY_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_search_history(history: list):
    """Save search history to disk."""
    Path("storage").mkdir(exist_ok=True)
    with open(SEARCH_HISTORY_PATH, "w") as f:
        json.dump(history[:MAX_HISTORY], f, indent=2)


# ─── Tooltip helper ──────────────────────────────────────────────────────────
class ToolTip:
    """Show a tooltip on hover after a short delay."""

    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._tipwindow = None
        self._id = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _schedule(self, event=None):
        self._hide()
        self._id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self._tipwindow:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = tk.Label(
            tw,
            text=self.text,
            background="#1e2030",
            foreground="#e8eaf0",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
        )
        label.pack()
        self._tipwindow = tw

    def _hide(self, event=None):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None
        if self._tipwindow:
            self._tipwindow.destroy()
            self._tipwindow = None

    def update_text(self, text):
        self.text = text


# ─── Main application ────────────────────────────────────────────────────────
class ImageSearchApp(ctk.CTk):
    """Main application window for semantic image search."""

    def __init__(self):
        super().__init__()

        # ── Window configuration ──────────────────
        self.title("🔍 Semantic Image Search")
        self.geometry("1300x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg_dark"])

        # ── State ─────────────────────────────────
        self.clip_model = None
        self.indexer = None
        self.searcher = None
        self.is_indexed = False
        self.index_directory = ""
        self.search_history: list = _load_search_history()
        self._last_results: list = []
        self._photo_refs: list = []          # prevent GC of PhotoImages

        # ── Build UI ──────────────────────────────
        self._build_layout()
        self.initialize_models()
        self.check_index_status()

    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT
    # ══════════════════════════════════════════════════════════════════════════
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)   # sidebar
        self.grid_columnconfigure(1, weight=1)   # main
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)      # status bar

        self._build_sidebar()
        self._build_main_area()
        self._build_status_bar()

    # ── Sidebar ────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=310, corner_radius=0,
            fg_color=COLORS["bg_sidebar"],
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # ── App branding ───────
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(25, 5))

        ctk.CTkLabel(
            brand_frame, text="🔍", font=ctk.CTkFont(size=32),
        ).pack(side="left", padx=(0, 8))

        title_col = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_col.pack(side="left")
        ctk.CTkLabel(
            title_col, text="Semantic Search",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col, text="CLIP + FAISS  -  Offline",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        # ── Separator ─────────
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"])
        sep.grid(row=1, column=0, sticky="ew", padx=20, pady=15)

        # ── Index section ─────
        ctk.CTkLabel(
            self.sidebar, text="📁  INDEX IMAGES",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS["accent"], anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=24, pady=(0, 8))

        ctk.CTkLabel(
            self.sidebar, text="Image Directory",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"],
            anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=24)

        dir_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        dir_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 8))
        dir_frame.grid_columnconfigure(0, weight=1)

        self.dir_entry = ctk.CTkEntry(
            dir_frame, placeholder_text="Select directory…",
            height=34, corner_radius=8,
            fg_color=COLORS["bg_card"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
        )
        self.dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        browse_btn = ctk.CTkButton(
            dir_frame, text="📂", width=36, height=34, corner_radius=8,
            fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
            command=self.browse_directory,
        )
        browse_btn.grid(row=0, column=1)

        self.index_btn = ctk.CTkButton(
            self.sidebar, text="⚡  Index Images", height=38, corner_radius=10,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#000000",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.index_images, state="disabled",
        )
        self.index_btn.grid(row=5, column=0, padx=24, pady=(4, 8), sticky="ew")

        # Progress
        self.progress_bar = ctk.CTkProgressBar(
            self.sidebar, height=6, corner_radius=3,
            progress_color=COLORS["accent"],
        )
        self.progress_bar.grid(row=6, column=0, padx=24, sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        self.progress_label = ctk.CTkLabel(
            self.sidebar, text="", font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
        )
        self.progress_label.grid(row=7, column=0, padx=24, pady=(4, 0))
        self.progress_label.grid_remove()

        # Status
        self.status_label = ctk.CTkLabel(
            self.sidebar, text="● No index found",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"], anchor="w",
        )
        self.status_label.grid(row=8, column=0, sticky="w", padx=24, pady=(8, 4))

        self.loading_label = ctk.CTkLabel(
            self.sidebar, text="⏳ Loading CLIP model…",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["warning"],
        )
        self.loading_label.grid(row=9, column=0, padx=24, pady=(0, 10))

        # ── Separator ─────────
        sep2 = ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"])
        sep2.grid(row=10, column=0, sticky="ew", padx=20, pady=10)

        # ── Search history section ──
        hist_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        hist_header.grid(row=11, column=0, sticky="ew", padx=24, pady=(0, 4))
        hist_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hist_header, text="🕑  RECENT SEARCHES",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLORS["accent"], anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.clear_hist_btn = ctk.CTkButton(
            hist_header, text="Clear", width=50, height=22, corner_radius=6,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(size=10),
            command=self._clear_history,
        )
        self.clear_hist_btn.grid(row=0, column=1, sticky="e")

        self.history_frame = ctk.CTkScrollableFrame(
            self.sidebar, height=180,
            fg_color=COLORS["bg_card"], corner_radius=8,
            border_width=1, border_color=COLORS["border"],
        )
        self.history_frame.grid(row=12, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.history_frame.grid_columnconfigure(0, weight=1)
        self._refresh_history_ui()

    # ── Main area ──────────────────────────────────────────────────────────
    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color=COLORS["bg_dark"],
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # ── Header ──────
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 5))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="Semantic Image Search",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color=COLORS["text_primary"], anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header, text="Describe what you're looking for in natural language",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"], anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(0, 5))

        # ── Search bar ──────
        search_card = ctk.CTkFrame(
            self.main_frame, corner_radius=14,
            fg_color=COLORS["bg_card"], border_width=1,
            border_color=COLORS["border"],
        )
        search_card.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 10))
        search_card.grid_columnconfigure(0, weight=1)

        # Query row
        query_row = ctk.CTkFrame(search_card, fg_color="transparent")
        query_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        query_row.grid_columnconfigure(0, weight=1)

        self.query_entry = ctk.CTkEntry(
            query_row,
            placeholder_text="e.g. 'a red sports car', 'sunset over mountains' …",
            height=42, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=COLORS["bg_dark"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
        )
        self.query_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.query_entry.bind("<Return>", lambda e: self.perform_search())

        self.search_btn = ctk.CTkButton(
            query_row, text="🔍  Search", width=120, height=42, corner_radius=10,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#000000",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.perform_search, state="disabled",
        )
        self.search_btn.grid(row=0, column=1)

        # Options row
        opts_row = ctk.CTkFrame(search_card, fg_color="transparent")
        opts_row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        opts_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            opts_row, text="Results:",
            font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, 6))

        self.top_k_var = ctk.IntVar(value=10)
        self.top_k_slider = ctk.CTkSlider(
            opts_row, from_=1, to=50, number_of_steps=49,
            variable=self.top_k_var,
            button_color=COLORS["accent"], button_hover_color=COLORS["accent_hover"],
            progress_color=COLORS["accent_dim"],
            command=self._update_top_k_label,
        )
        self.top_k_slider.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        self.top_k_value_label = ctk.CTkLabel(
            opts_row, text="10", width=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"],
        )
        self.top_k_value_label.grid(row=0, column=2)

        # ── Results area ────
        self.results_outer = ctk.CTkFrame(
            self.main_frame, fg_color="transparent",
        )
        self.results_outer.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 10))
        self.results_outer.grid_columnconfigure(0, weight=1)
        self.results_outer.grid_rowconfigure(0, weight=1)

        self.results_canvas = ctk.CTkScrollableFrame(
            self.results_outer,
            fg_color=COLORS["bg_dark"], corner_radius=0,
            label_text="", label_fg_color="transparent",
        )
        self.results_canvas.grid(row=0, column=0, sticky="nsew")
        self.results_canvas.grid_columnconfigure((0, 1, 2), weight=1)

        # Info label (shown when no index)
        self.info_label = ctk.CTkLabel(
            self.results_outer,
            text="👈  Index a directory first, then search by describing what you want.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text_muted"],
        )
        self.info_label.grid(row=0, column=0, padx=20, pady=60)

    # ── Status bar ─────────────────────────────────────────────────────────
    def _build_status_bar(self):
        self.statusbar = ctk.CTkFrame(
            self, height=28, corner_radius=0,
            fg_color=COLORS["bg_sidebar"], border_width=0,
        )
        self.statusbar.grid(row=1, column=1, sticky="ew")
        self.statusbar.grid_columnconfigure(1, weight=1)
        self.statusbar.grid_propagate(False)

        self.sb_left = ctk.CTkLabel(
            self.statusbar, text="  No index loaded",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_muted"], anchor="w",
        )
        self.sb_left.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=2)

        self.sb_right = ctk.CTkLabel(
            self.statusbar, text="Ready  ",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_muted"], anchor="e",
        )
        self.sb_right.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=2)

    # ══════════════════════════════════════════════════════════════════════════
    # STATUS BAR UPDATES
    # ══════════════════════════════════════════════════════════════════════════
    def _update_statusbar(self):
        index_path = Path("storage/faiss.index")
        meta_path = Path("storage/metadata.json")
        if index_path.exists() and meta_path.exists():
            idx_size = _human_size(index_path.stat().st_size)
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                count = len(meta)
            except Exception:
                count = "?"
            self.sb_left.configure(
                text=f"  📊 {count} images indexed  -  Index size: {idx_size}"
            )
        else:
            self.sb_left.configure(text="  No index loaded")

    # ══════════════════════════════════════════════════════════════════════════
    # SEARCH HISTORY
    # ══════════════════════════════════════════════════════════════════════════
    def _refresh_history_ui(self):
        for w in self.history_frame.winfo_children():
            w.destroy()
        if not self.search_history:
            ctk.CTkLabel(
                self.history_frame, text="No recent searches",
                font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"],
            ).grid(row=0, column=0, pady=8)
            return
        for i, q in enumerate(self.search_history):
            btn = ctk.CTkButton(
                self.history_frame, text=f"  {q}", height=28, anchor="w",
                corner_radius=6,
                fg_color="transparent", hover_color=COLORS["border"],
                text_color=COLORS["text_secondary"],
                font=ctk.CTkFont(family="Segoe UI", size=11),
                command=lambda query=q: self._rerun_query(query),
            )
            btn.grid(row=i, column=0, sticky="ew", pady=1, padx=4)

    def _add_to_history(self, query: str):
        if query in self.search_history:
            self.search_history.remove(query)
        self.search_history.insert(0, query)
        self.search_history = self.search_history[:MAX_HISTORY]
        _save_search_history(self.search_history)
        self._refresh_history_ui()

    def _clear_history(self):
        self.search_history = []
        _save_search_history([])
        self._refresh_history_ui()

    def _rerun_query(self, query: str):
        self.query_entry.delete(0, tk.END)
        self.query_entry.insert(0, query)
        self.perform_search()

    # ══════════════════════════════════════════════════════════════════════════
    # UI HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _update_top_k_label(self, value):
        self.top_k_value_label.configure(text=str(int(value)))

    def browse_directory(self):
        directory = filedialog.askdirectory(title="Select Image Directory")
        if directory:
            self.index_directory = directory
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.index_btn.configure(state="normal")

    # ══════════════════════════════════════════════════════════════════════════
    # MODEL LOADING
    # ══════════════════════════════════════════════════════════════════════════
    def initialize_models(self):
        def load_models():
            try:
                self.clip_model = CLIPModel(device="cpu")
                self.indexer = ImageIndexer(self.clip_model)
                self.searcher = ImageSearcher(self.clip_model)
                self.after(0, self.on_models_loaded)
            except Exception as e:
                self.after(0, lambda: self.on_model_load_error(str(e)))
        threading.Thread(target=load_models, daemon=True).start()

    def on_models_loaded(self):
        self.loading_label.grid_remove()
        self.check_index_status()

    def on_model_load_error(self, error_msg):
        self.loading_label.configure(
            text=f"❌ Model error: {error_msg}",
            text_color=COLORS["error"],
        )

    # ══════════════════════════════════════════════════════════════════════════
    # INDEX STATUS
    # ══════════════════════════════════════════════════════════════════════════
    def check_index_status(self):
        index_path = Path("storage/faiss.index")
        if index_path.exists() and self.searcher:
            self.searcher.reload_index()
            self.is_indexed = self.searcher.is_indexed()
            if self.is_indexed:
                self.status_label.configure(
                    text="● Index ready",
                    text_color=COLORS["success"],
                )
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
        self.status_label.configure(
            text="● No index found",
            text_color=COLORS["text_muted"],
        )
        self.search_btn.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════════════
    # INDEXING
    # ══════════════════════════════════════════════════════════════════════════
    def index_images(self):
        if not self.index_directory or not os.path.exists(self.index_directory):
            self._show_dialog("Error", "Please select a valid directory path.", "error")
            return
        if not self.indexer:
            self._show_dialog("Error", "Models are still loading. Please wait…", "error")
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
                    self.after(0, lambda: self.progress_label.configure(
                        text=f"Processing {current}/{total} images…"
                    ))

                successful, failed = self.indexer.index_directory(
                    self.index_directory,
                    progress_callback=progress_callback,
                )
                self.searcher.reload_index()
                self.is_indexed = self.searcher.is_indexed()
                self.after(0, lambda: self.on_indexing_complete(successful, failed))
            except Exception as e:
                self.after(0, lambda: self.on_indexing_error(str(e)))

        threading.Thread(target=index_thread, daemon=True).start()

    def on_indexing_complete(self, successful, failed):
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Indexing complete!")
        if successful > 0:
            self.status_label.configure(
                text=f"● Index ready ({successful} images)",
                text_color=COLORS["success"],
            )
            self.is_indexed = True
            self.search_btn.configure(state="normal")
            self.info_label.grid_remove()
            self.results_canvas.grid()

        msg = f"Successfully indexed {successful} images"
        if failed > 0:
            msg += f"\nFailed to index {failed} images (corrupt/unreadable)"
        self._show_dialog("Indexing Complete", msg, "info")

        self.after(2500, lambda: (
            self.progress_bar.grid_remove(),
            self.progress_label.grid_remove(),
        ))
        self.index_btn.configure(state="normal")
        self._update_statusbar()

    def on_indexing_error(self, error_msg):
        self.progress_bar.grid_remove()
        self.progress_label.grid_remove()
        self._show_dialog("Error", f"Indexing failed: {error_msg}", "error")
        self.index_btn.configure(state="normal")

    # ══════════════════════════════════════════════════════════════════════════
    # SEARCH
    # ══════════════════════════════════════════════════════════════════════════
    def perform_search(self):
        query = self.query_entry.get().strip()
        if not query:
            self._show_dialog("Error", "Please enter a search query.", "error")
            return
        if not self.is_indexed or not self.searcher:
            self._show_dialog("Error", "Please index images first.", "error")
            return

        self.search_btn.configure(state="disabled", text="Searching…")
        self.sb_right.configure(text="Searching…  ")

        def search_thread():
            try:
                top_k = self.top_k_var.get()
                results = self.searcher.search(query, top_k=top_k)
                self.after(0, lambda: self.display_results(results, query))
            except Exception as e:
                self.after(0, lambda: self._show_dialog(
                    "Error", f"Search failed: {e}", "error"
                ))
            finally:
                self.after(0, lambda: self.search_btn.configure(
                    state="normal", text="🔍  Search"
                ))

        threading.Thread(target=search_thread, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # DISPLAY RESULTS
    # ══════════════════════════════════════════════════════════════════════════
    def display_results(self, results, query):
        # Save to history
        self._add_to_history(query)

        # Clear previous
        for w in self.results_canvas.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        self._last_results = results

        if not results:
            ctk.CTkLabel(
                self.results_canvas, text="No results found.",
                font=ctk.CTkFont(size=14), text_color=COLORS["text_muted"],
            ).grid(row=0, column=0, columnspan=3, pady=40)
            self.sb_right.configure(text="0 results  ")
            return

        # Header
        ctk.CTkLabel(
            self.results_canvas,
            text=f"Found {len(results)} results for '{query}'",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text_primary"], anchor="w",
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(8, 12))

        self.sb_right.configure(text=f"{len(results)} results - '{query}'  ")

        num_cols = 3
        thumb_size = 240

        for idx, (image_path, score) in enumerate(results):
            row = (idx // num_cols) + 1
            col = idx % num_cols

            card = ctk.CTkFrame(
                self.results_canvas, corner_radius=12,
                fg_color=COLORS["bg_card"],
                border_width=1, border_color=COLORS["border"],
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            try:
                img = Image.open(image_path)
                w_orig, h_orig = img.size
                img_size_bytes = os.path.getsize(image_path)

                img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._photo_refs.append(photo)

                # Image label
                img_label = ctk.CTkLabel(card, image=photo, text="")
                img_label.image = photo
                img_label.grid(row=0, column=0, padx=10, pady=(10, 6))

                # ── Click = open directory ──
                img_label.bind("<Button-1>", lambda e, p=image_path: _open_in_explorer(p))
                img_label.configure(cursor="hand2")

                # ── Double-click = lightbox ──
                img_label.bind("<Double-Button-1>", lambda e, p=image_path, s=score: self._open_lightbox(p, s))

                # ── Right-click context menu ──
                img_label.bind("<Button-3>", lambda e, p=image_path: self._show_context_menu(e, p))
                card.bind("<Button-3>", lambda e, p=image_path: self._show_context_menu(e, p))

                # ── Tooltip ──
                ToolTip(card, text=image_path)

                # ── Score bar ──
                score_frame = ctk.CTkFrame(card, fg_color="transparent")
                score_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 2))
                score_frame.grid_columnconfigure(1, weight=1)

                score_color = (
                    COLORS["score_high"] if score > 0.25
                    else COLORS["score_mid"] if score > 0.18
                    else COLORS["score_low"]
                )
                ctk.CTkLabel(
                    score_frame, text=f"{score:.2%}",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    text_color=score_color,
                ).grid(row=0, column=0, sticky="w")

                score_bar = ctk.CTkProgressBar(
                    score_frame, height=4, corner_radius=2,
                    progress_color=score_color,
                    fg_color=COLORS["border"],
                )
                score_bar.grid(row=0, column=1, sticky="ew", padx=(8, 0))
                score_bar.set(min(score / 0.35, 1.0))  # normalise to bar range

                # ── Meta info ──
                meta_text = f"{Path(image_path).name}"
                meta_sub = f"{w_orig}×{h_orig}  -  {_human_size(img_size_bytes)}"

                ctk.CTkLabel(
                    card, text=meta_text,
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=COLORS["text_secondary"],
                    wraplength=220, anchor="w",
                ).grid(row=2, column=0, sticky="w", padx=12, pady=(2, 0))

                ctk.CTkLabel(
                    card, text=meta_sub,
                    font=ctk.CTkFont(family="Segoe UI", size=10),
                    text_color=COLORS["text_muted"], anchor="w",
                ).grid(row=3, column=0, sticky="w", padx=12, pady=(0, 10))

            except Exception:
                ctk.CTkLabel(
                    card,
                    text=f"⚠ Error loading\n{Path(image_path).name}",
                    font=ctk.CTkFont(size=11), text_color=COLORS["error"],
                ).grid(row=0, column=0, padx=10, pady=10)

    # ══════════════════════════════════════════════════════════════════════════
    # CONTEXT MENU  (right-click)
    # ══════════════════════════════════════════════════════════════════════════
    def _show_context_menu(self, event, image_path: str):
        menu = tk.Menu(self, tearoff=0, bg="#1e2030", fg="#e8eaf0",
                       activebackground=COLORS["accent"],
                       activeforeground="#000000",
                       font=("Segoe UI", 10))
        menu.add_command(label="📂  Open Containing Folder",
                         command=lambda: _open_in_explorer(image_path))
        menu.add_command(label="🖼️  Open in Default Viewer",
                         command=lambda: _open_in_default_viewer(image_path))
        menu.add_separator()
        menu.add_command(label="📋  Copy File Path",
                         command=lambda: self._copy_to_clipboard(image_path))
        menu.add_command(label="📄  View Image Details",
                         command=lambda: self._show_image_details(image_path))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_to_clipboard(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.sb_right.configure(text="✓ Path copied to clipboard  ")
        self.after(2500, lambda: self.sb_right.configure(text="Ready  "))

    # ══════════════════════════════════════════════════════════════════════════
    # IMAGE DETAILS POPUP
    # ══════════════════════════════════════════════════════════════════════════
    def _show_image_details(self, image_path: str):
        try:
            p = Path(image_path)
            stat = p.stat()
            img = Image.open(image_path)
            w, h = img.size
            fmt = img.format or p.suffix.upper().lstrip(".")
            created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M")
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            details = (
                f"File name:    {p.name}\n"
                f"Directory:     {p.parent}\n"
                f"Format:         {fmt}\n"
                f"Dimensions:  {w} × {h} px\n"
                f"File size:      {_human_size(stat.st_size)}\n"
                f"Created:        {created}\n"
                f"Modified:       {modified}"
            )
        except Exception as e:
            details = f"Could not read details:\n{e}"

        self._show_dialog("Image Details", details, "info", width=480, height=260)

    # ══════════════════════════════════════════════════════════════════════════
    # LIGHTBOX PREVIEW  (double-click)
    # ══════════════════════════════════════════════════════════════════════════
    def _open_lightbox(self, image_path: str, score: float):
        lb = ctk.CTkToplevel(self)
        lb.title(Path(image_path).name)
        lb.attributes("-topmost", True)
        lb.configure(fg_color=COLORS["bg_dark"])
        lb.grab_set()
        lb.focus_force()

        # Determine size
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        max_w = int(screen_w * 0.75)
        max_h = int(screen_h * 0.80)

        try:
            img = Image.open(image_path)
            img.thumbnail((max_w, max_h - 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            img_label = ctk.CTkLabel(lb, image=photo, text="")
            img_label.image = photo
            img_label.pack(padx=20, pady=(20, 8))
        except Exception:
            ctk.CTkLabel(
                lb, text="⚠ Could not load image",
                text_color=COLORS["error"],
            ).pack(pady=40)

        # Info bar
        info_frame = ctk.CTkFrame(lb, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(
            info_frame, text=image_path,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_muted"], anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            info_frame, text=f"Score: {score:.2%}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["accent"], anchor="e",
        ).pack(side="right")

        # Buttons
        btn_row = ctk.CTkFrame(lb, fg_color="transparent")
        btn_row.pack(pady=(0, 16))

        ctk.CTkButton(
            btn_row, text="📂  Open Folder", width=130, height=32,
            corner_radius=8,
            fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
            text_color=COLORS["text_primary"],
            command=lambda: _open_in_explorer(image_path),
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row, text="🖼️  Open Image", width=130, height=32,
            corner_radius=8,
            fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
            text_color=COLORS["text_primary"],
            command=lambda: _open_in_default_viewer(image_path),
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row, text="✕  Close", width=90, height=32,
            corner_radius=8,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            command=lb.destroy,
        ).pack(side="left", padx=6)

        lb.bind("<Escape>", lambda e: lb.destroy())

        # Centre on screen
        lb.update_idletasks()
        win_w = lb.winfo_width()
        win_h = lb.winfo_height()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        lb.geometry(f"+{x}+{y}")

    # ══════════════════════════════════════════════════════════════════════════
    # DIALOGS
    # ══════════════════════════════════════════════════════════════════════════
    def _show_dialog(self, title, message, kind="info", width=420, height=180):
        d = ctk.CTkToplevel(self)
        d.title(title)
        d.geometry(f"{width}x{height}")
        d.transient(self)
        d.grab_set()
        d.configure(fg_color=COLORS["bg_card"])
        d.attributes("-topmost", True)

        icon = "❌" if kind == "error" else "ℹ️"
        ctk.CTkLabel(
            d, text=f"{icon}  {title}",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(pady=(18, 6), padx=20)

        ctk.CTkLabel(
            d, text=message,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_secondary"],
            wraplength=width - 50, justify="left",
        ).pack(pady=(0, 12), padx=20)

        ctk.CTkButton(
            d, text="OK", width=90, height=32, corner_radius=8,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color="#000000",
            command=d.destroy,
        ).pack(pady=(0, 14))

        # Centre
        d.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - d.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - d.winfo_height()) // 2
        d.geometry(f"+{x}+{y}")

    # Keep legacy names in case other code references them
    show_error = lambda self, msg: self._show_dialog("Error", msg, "error")
    show_info = lambda self, msg: self._show_dialog("Information", msg, "info")


# ─── Entry point ──────────────────────────────────────────────────────────────
def main():
    """Main entry point for the application."""
    app = ImageSearchApp()
    app.mainloop()


if __name__ == "__main__":
    main()

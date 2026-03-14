"""
Result card widget for displaying an individual search result.
"""

import customtkinter as ctk
import tkinter as tk
import os
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk

from ..theme import COLORS
from ..helpers import open_in_explorer, open_in_default_viewer, human_size
from .tooltip import ToolTip
from .lightbox import open_lightbox
from .dialogs import show_dialog

def create_result_card(parent_frame, app_instance, image_path: str, score: float, row: int, col: int):
    """
    Create a card representing a single search result.
    
    Args:
        parent_frame: Parent widget to place the card in
        app_instance: Main app instance (for clipboard/callbacks)
        image_path: Path to the image
        score: Similarity score
        row: Grid row
        col: Grid column
    """
    card = ctk.CTkFrame(
        parent_frame, corner_radius=12,
        fg_color=COLORS["bg_card"],
        border_width=1, border_color=COLORS["border"],
    )
    card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
    card.grid_columnconfigure(0, weight=1)

    thumb_size = 240

    try:
        img = Image.open(image_path)
        w_orig, h_orig = img.size
        img_size_bytes = os.path.getsize(image_path)

        img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        app_instance._photo_refs.append(photo)

        # Image label
        img_label = ctk.CTkLabel(card, image=photo, text="")
        img_label.image = photo
        img_label.grid(row=0, column=0, padx=10, pady=(10, 6))

        # Interactions
        img_label.bind("<Button-1>", lambda e, p=image_path: open_in_explorer(p))
        img_label.configure(cursor="hand2")
        img_label.bind("<Double-Button-1>", lambda e, p=image_path, s=score: open_lightbox(app_instance, p, s))
        
        def show_ctx(e, p=image_path):
            _show_context_menu(app_instance, e, p)
            
        img_label.bind("<Button-3>", show_ctx)
        card.bind("<Button-3>", show_ctx)

        ToolTip(card, text=image_path)

        # Score bar
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
        score_bar.set(min(score / 0.35, 1.0))  # normalize to bar range

        # Meta info
        meta_text = f"{Path(image_path).name}"
        meta_sub = f"{w_orig}×{h_orig}  -  {human_size(img_size_bytes)}"

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


def _show_context_menu(app_instance, event, image_path: str):
    menu = tk.Menu(app_instance, tearoff=0, bg="#1e2030", fg="#e8eaf0",
                   activebackground=COLORS["accent"],
                   activeforeground="#000000",
                   font=("Segoe UI", 10))
    menu.add_command(label="📂  Open Containing Folder",
                     command=lambda: open_in_explorer(image_path))
    menu.add_command(label="🖼️  Open in Default Viewer",
                     command=lambda: open_in_default_viewer(image_path))
    menu.add_separator()
    
    def copy_path():
        app_instance.clipboard_clear()
        app_instance.clipboard_append(image_path)
        app_instance.sb_right.configure(text="✓ Path copied to clipboard  ")
        app_instance.after(2500, lambda: app_instance.sb_right.configure(text="Ready  "))
        
    menu.add_command(label="📋  Copy File Path", command=copy_path)
    
    def show_details():
        _show_image_details(app_instance, image_path)
        
    menu.add_command(label="📄  View Image Details", command=show_details)
    
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()

def _show_image_details(app_instance, image_path: str):
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
            f"File size:      {human_size(stat.st_size)}\n"
            f"Created:        {created}\n"
            f"Modified:       {modified}"
        )
    except Exception as e:
        details = f"Could not read details:\n{e}"

    show_dialog(app_instance, "Image Details", details, "info", width=480, height=260)

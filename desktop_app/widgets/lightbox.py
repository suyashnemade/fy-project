"""
Lightbox preview widget for displaying full-sized images.
"""

import customtkinter as ctk
from PIL import Image, ImageTk
from pathlib import Path

from ..theme import COLORS
from ..helpers import open_in_explorer, open_in_default_viewer

def open_lightbox(parent, image_path: str, score: float):
    """
    Open an image in a lightbox view.
    
    Args:
        parent: Parent window
        image_path: Path to the image
        score: Similarity score
    """
    lb = ctk.CTkToplevel(parent)
    lb.title(Path(image_path).name)
    lb.attributes("-topmost", True)
    lb.configure(fg_color=COLORS["bg_dark"])
    lb.grab_set()
    lb.focus_force()

    # Determine size
    screen_w = parent.winfo_screenwidth()
    screen_h = parent.winfo_screenheight()
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
        command=lambda: open_in_explorer(image_path),
    ).pack(side="left", padx=6)

    ctk.CTkButton(
        btn_row, text="🖼️  Open Image", width=130, height=32,
        corner_radius=8,
        fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
        text_color=COLORS["text_primary"],
        command=lambda: open_in_default_viewer(image_path),
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

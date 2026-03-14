"""
Dialog windows for the desktop application.
"""

import customtkinter as ctk
from ..theme import COLORS

def show_dialog(parent, title, message, kind="info", width=420, height=180):
    """
    Show a custom dialog window.
    
    Args:
        parent: Parent window
        title: Dialog title
        message: Dialog message text
        kind: "info" or "error"
        width: Dialog width
        height: Dialog height
    """
    d = ctk.CTkToplevel(parent)
    d.title(title)
    d.geometry(f"{width}x{height}")
    d.transient(parent)
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
    x = parent.winfo_rootx() + (parent.winfo_width() - d.winfo_width()) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - d.winfo_height()) // 2
    d.geometry(f"+{x}+{y}")

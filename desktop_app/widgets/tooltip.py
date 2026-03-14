"""
Tooltip widget for CustomTkinter/Tkinter.
"""

import tkinter as tk

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

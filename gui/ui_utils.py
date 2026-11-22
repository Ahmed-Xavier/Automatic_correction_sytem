"""
Shared UI utilities: style constants, theme helpers, reusable widgets.
"""
import tkinter as tk
from tkinter import ttk

# ----- Colour palette -----
COLORS = {
    "bg": "#F5F6FA",
    "sidebar": "#1F2D40",
    "sidebar_active": "#2C4164",
    "sidebar_text": "#CDD3E0",
    "sidebar_active_text": "#FFFFFF",
    "accent": "#2D6CDF",
    "accent_dark": "#1A4FA8",
    "header_bg": "#FFFFFF",
    "card_bg": "#FFFFFF",
    "card_border": "#E1E4EC",
    "text_primary": "#1A1D2E",
    "text_secondary": "#6B7280",
    "success": "#16A34A",
    "warning": "#D97706",
    "danger": "#DC2626",
    "review": "#F59E0B",
}

FONTS = {
    "title": ("Segoe UI", 20, "bold"),
    "subtitle": ("Segoe UI", 13, "bold"),
    "heading": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 9),
}

def apply_theme(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["card_bg"],
                    relief="flat", borderwidth=1)
    style.configure("TLabel", background=COLORS["bg"],
                    foreground=COLORS["text_primary"],
                    font=FONTS["body"])
    style.configure("Card.TLabel", background=COLORS["card_bg"])
    style.configure("Title.TLabel", font=FONTS["title"],
                    foreground=COLORS["text_primary"], background=COLORS["bg"])
    style.configure("Subtitle.TLabel", font=FONTS["subtitle"],
                    foreground=COLORS["text_primary"], background=COLORS["card_bg"])
    style.configure("Secondary.TLabel", font=FONTS["small"],
                    foreground=COLORS["text_secondary"], background=COLORS["card_bg"])

    # Buttons
    style.configure("Accent.TButton", font=FONTS["heading"],
                    background=COLORS["accent"], foreground="white",
                    padding=(14, 7), relief="flat")
    style.map("Accent.TButton",
              background=[("active", COLORS["accent_dark"]), ("pressed", COLORS["accent_dark"])],
              foreground=[("active", "white")])

    style.configure("Danger.TButton", font=FONTS["body"],
                    background=COLORS["danger"], foreground="white",
                    padding=(10, 5), relief="flat")
    style.map("Danger.TButton", background=[("active", "#B91C1C")])

    style.configure("Success.TButton", font=FONTS["body"],
                    background=COLORS["success"], foreground="white",
                    padding=(10, 5), relief="flat")
    style.map("Success.TButton", background=[("active", "#15803D")])

    style.configure("TButton", font=FONTS["body"], padding=(10, 5), relief="flat")

    # Treeview
    style.configure("Treeview",
                    font=FONTS["body"], rowheight=26,
                    background="white", fieldbackground="white",
                    foreground=COLORS["text_primary"])
    style.configure("Treeview.Heading",
                    font=FONTS["heading"],
                    background=COLORS["card_border"],
                    foreground=COLORS["text_primary"])
    style.map("Treeview", background=[("selected", COLORS["accent"])],
              foreground=[("selected", "white")])

    # Entry / Combobox
    style.configure("TEntry", font=FONTS["body"], padding=5)
    style.configure("TCombobox", font=FONTS["body"], padding=5)

    # Notebook
    style.configure("TNotebook", background=COLORS["bg"], tabmargins=[0, 0, 0, 0])
    style.configure("TNotebook.Tab", font=FONTS["body"], padding=(12, 6))


def make_separator(parent, **grid_kwargs):
    sep = ttk.Separator(parent, orient="horizontal")
    sep.grid(**grid_kwargs)
    return sep


class StatCard(tk.Frame):
    """A compact stats card showing a label + value."""
    def __init__(self, parent, label: str, value: str = "0", color: str = None):
        super().__init__(parent, bg=COLORS["card_bg"],
                         highlightbackground=COLORS["card_border"],
                         highlightthickness=1,
                         pady=8, padx=12)

        self._label_text = label
        self._color = color or COLORS["accent"]

        tk.Label(self, text=label, bg=COLORS["card_bg"],
                 font=FONTS["small"], fg=COLORS["text_secondary"]).pack(anchor="w")

        self._val_label = tk.Label(self, text=value, bg=COLORS["card_bg"],
                                   font=("Segoe UI", 22, "bold"), fg=self._color)
        self._val_label.pack(anchor="w")

    def update_value(self, value: str):
        self._val_label.config(text=str(value))


class SectionHeader(tk.Frame):
    """Page title header with optional subtitle."""
    def __init__(self, parent, title: str, subtitle: str = ""):
        super().__init__(parent, bg=COLORS["bg"])
        tk.Label(self, text=title, font=FONTS["title"],
                 fg=COLORS["text_primary"], bg=COLORS["bg"]).pack(anchor="w")
        if subtitle:
            tk.Label(self, text=subtitle, font=FONTS["small"],
                     fg=COLORS["text_secondary"], bg=COLORS["bg"]).pack(anchor="w")


class StatusBar(tk.Frame):
    """Bottom status bar."""
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["sidebar"], height=28)
        self._label = tk.Label(self, text="Ready", bg=COLORS["sidebar"],
                                fg=COLORS["sidebar_text"], font=FONTS["small"],
                                padx=12)
        self._label.pack(side="left", fill="y")

    def set(self, message: str, color: str = None):
        c = color or COLORS["sidebar_text"]
        self._label.config(text=message, fg=c)

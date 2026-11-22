"""
Main Application Window — Examination Correction System.
Provides sidebar navigation and hosts all feature panels.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Callable

from gui.ui_utils import COLORS, FONTS, apply_theme, StatusBar
from database.repositories import ServiceManager

# Panel imports
from gui.dashboard import DashboardPanel
from gui.exam_manager import ExamManagerPanel
from gui.barcode_manager import BarcodeManagerPanel
from gui.answer_key_importer import AnswerKeyPanel
from gui.scan_manager import ScanManagerPanel
from gui.manual_review import ManualReviewPanel
from gui.results_viewer import ResultsPanel
from gui.settings_window import SettingsPanel

SIDEBAR_ITEMS = [
    ("dashboard",       "🏠  Dashboard"),
    ("exams",           "📋  Examinations"),
    ("barcode_import",  "🏷️   Barcode Database"),
    ("answer_key",      "🔑  Answer Keys"),
    ("scan_processing", "🖨️   Scan Processing"),
    ("manual_review",   "🔍  Manual Review"),
    ("results",         "📊  Results"),
    ("settings",        "⚙️   Settings"),
]

class MainWindow:
    def __init__(self, service_manager: ServiceManager):
        self.sm = service_manager
        self.root = tk.Tk()
        self.root.title("Examination Correction System")
        self.root.geometry("1280x820")
        self.root.minsize(1024, 680)

        apply_theme(self.root)
        self.root.configure(bg=COLORS["bg"])

        self._panels: Dict[str, tk.Frame] = {}
        self._sidebar_btns: Dict[str, tk.Button] = {}
        self._active_panel: str = ""

        self._build_ui()
        self.navigate("dashboard")

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Main layout: sidebar | content area
        outer = tk.Frame(self.root, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True)

        # --- Sidebar ---
        self._sidebar = tk.Frame(outer, bg=COLORS["sidebar"], width=210)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # App title
        title_frame = tk.Frame(self._sidebar, bg=COLORS["sidebar"], pady=18)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="📝", bg=COLORS["sidebar"],
                 font=("Segoe UI", 22)).pack()
        tk.Label(title_frame, text="Exam Correction", bg=COLORS["sidebar"],
                 font=("Segoe UI", 11, "bold"), fg="#FFFFFF").pack()
        tk.Label(title_frame, text="System", bg=COLORS["sidebar"],
                 font=("Segoe UI", 10), fg=COLORS["sidebar_text"]).pack()

        # Separator
        tk.Frame(self._sidebar, bg=COLORS["sidebar_active"], height=1).pack(fill="x", pady=4)

        # Nav buttons
        for key, label in SIDEBAR_ITEMS:
            btn = tk.Button(
                self._sidebar, text=label, anchor="w",
                font=FONTS["body"],
                bg=COLORS["sidebar"], fg=COLORS["sidebar_text"],
                activebackground=COLORS["sidebar_active"],
                activeforeground=COLORS["sidebar_active_text"],
                bd=0, padx=20, pady=10, cursor="hand2",
                command=lambda k=key: self.navigate(k)
            )
            btn.pack(fill="x")
            self._sidebar_btns[key] = btn

        # Version at bottom
        tk.Frame(self._sidebar, bg=COLORS["sidebar_active"], height=1).pack(fill="x", side="bottom", pady=4)
        tk.Label(self._sidebar, text="v1.0.0", bg=COLORS["sidebar"],
                 font=FONTS["small"], fg=COLORS["sidebar_text"],
                 pady=8).pack(side="bottom")

        # --- Content area ---
        self._content = tk.Frame(outer, bg=COLORS["bg"])
        self._content.pack(side="left", fill="both", expand=True)

        # Status bar at bottom
        self._status_bar = StatusBar(self.root)
        self._status_bar.pack(side="bottom", fill="x")

        # Lazy-build all panels
        self._panels["dashboard"]       = DashboardPanel(self._content, self.sm, self.navigate)
        self._panels["exams"]           = ExamManagerPanel(self._content, self.sm)
        self._panels["barcode_import"]  = BarcodeManagerPanel(self._content, self.sm)
        self._panels["answer_key"]      = AnswerKeyPanel(self._content, self.sm)
        self._panels["scan_processing"] = ScanManagerPanel(self._content, self.sm)
        self._panels["manual_review"]   = ManualReviewPanel(self._content, self.sm)
        self._panels["results"]         = ResultsPanel(self._content, self.sm)
        self._panels["settings"]        = SettingsPanel(self._content, self.sm)

        for panel in self._panels.values():
            panel.place(relx=0, rely=0, relwidth=1, relheight=1)
            panel.lower()

    def navigate(self, panel_key: str):
        if panel_key not in self._panels:
            return

        # Update sidebar highlight
        for key, btn in self._sidebar_btns.items():
            if key == panel_key:
                btn.config(bg=COLORS["sidebar_active"],
                           fg=COLORS["sidebar_active_text"],
                           font=FONTS["heading"])
            else:
                btn.config(bg=COLORS["sidebar"],
                           fg=COLORS["sidebar_text"],
                           font=FONTS["body"])

        # Show selected panel
        if self._active_panel and self._active_panel in self._panels:
            self._panels[self._active_panel].lower()

        panel = self._panels[panel_key]
        panel.lift()
        self._active_panel = panel_key

        # Refresh panels that need live data
        if hasattr(panel, "refresh"):
            panel.refresh()

        # Find label for status bar
        label = next((lbl for k, lbl in SIDEBAR_ITEMS if k == panel_key), panel_key)
        self._status_bar.set(f"  {label.strip()}")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        if messagebox.askokcancel("Quit", "Exit the Examination Correction System?"):
            self.root.destroy()

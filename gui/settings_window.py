"""
Settings panel.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from gui.ui_utils import COLORS, FONTS, SectionHeader
from config import paths, settings

class SettingsPanel(tk.Frame):
    def __init__(self, parent, service_manager):
        super().__init__(parent, bg=COLORS["bg"])
        self.sm = service_manager
        self._build()

    def _build(self):
        SectionHeader(self, "Settings",
                      "Configure application paths and processing parameters").pack(
                          fill="x", padx=24, pady=(24, 8))

        # --- Paths ---
        path_frame = tk.LabelFrame(self, text="  Directory Configuration  ",
                                    bg=COLORS["bg"], font=FONTS["heading"],
                                    fg=COLORS["text_primary"], bd=1, relief="groove")
        path_frame.pack(fill="x", padx=24, pady=8)
        path_frame.columnconfigure(1, weight=1)

        path_defs = [
            ("Scanner Input Folder", str(paths.SCANS_DIR)),
            ("Processed Output Folder", str(paths.PROCESSED_DIR)),
            ("Exports Folder", str(paths.EXPORTS_DIR)),
            ("Database File", str(paths.DEFAULT_DB_PATH)),
        ]

        self._path_vars = {}
        for row_idx, (label, default) in enumerate(path_defs):
            tk.Label(path_frame, text=label, bg=COLORS["bg"], font=FONTS["body"],
                     fg=COLORS["text_secondary"]).grid(row=row_idx, column=0,
                                                         sticky="w", padx=12, pady=6)
            var = tk.StringVar(value=default)
            self._path_vars[label] = var
            ttk.Entry(path_frame, textvariable=var, width=48).grid(
                row=row_idx, column=1, sticky="ew", padx=8, pady=6)
            ttk.Button(path_frame, text="…",
                       command=lambda v=var, lbl=label: self._browse(v, lbl)).grid(
                           row=row_idx, column=2, padx=4, pady=6)

        # --- OMR parameters ---
        omr_frame = tk.LabelFrame(self, text="  OMR Recognition Thresholds  ",
                                   bg=COLORS["bg"], font=FONTS["heading"],
                                   fg=COLORS["text_primary"], bd=1, relief="groove")
        omr_frame.pack(fill="x", padx=24, pady=8)

        thres_defs = [
            ("Bubble Fill Threshold", str(settings.BUBBLE_FILL_THRESHOLD)),
            ("Uncertain Low", str(settings.BUBBLE_UNCERTAIN_LOW)),
            ("Uncertain High", str(settings.BUBBLE_UNCERTAIN_HIGH)),
            ("Scan Render DPI", str(settings.SCAN_RENDER_DPI)),
        ]
        self._omr_vars = {}
        for row_idx, (label, default) in enumerate(thres_defs):
            tk.Label(omr_frame, text=label, bg=COLORS["bg"], font=FONTS["body"],
                     fg=COLORS["text_secondary"]).grid(row=row_idx, column=0,
                                                         sticky="w", padx=12, pady=6)
            var = tk.StringVar(value=default)
            self._omr_vars[label] = var
            ttk.Entry(omr_frame, textvariable=var, width=12).grid(
                row=row_idx, column=1, sticky="w", padx=8, pady=6)
        omr_frame.columnconfigure(1, weight=1)

        # --- DB stats ---
        db_frame = tk.LabelFrame(self, text="  Database Information  ",
                                  bg=COLORS["bg"], font=FONTS["heading"],
                                  fg=COLORS["text_primary"], bd=1, relief="groove")
        db_frame.pack(fill="x", padx=24, pady=8)

        self._db_info_text = tk.Text(db_frame, height=4, state="disabled",
                                      font=FONTS["mono"], bg="#F9FAFB",
                                      fg=COLORS["text_primary"], relief="flat", padx=8)
        self._db_info_text.pack(fill="x", padx=8, pady=8)

        btn_row = tk.Frame(db_frame, bg=COLORS["bg"])
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btn_row, text="🔄 Refresh DB Info", command=self._refresh_db_info).pack(side="left")

        self._refresh_db_info()

    def _browse(self, var: tk.StringVar, label: str):
        if "File" in label or "Database" in label:
            path = filedialog.asksaveasfilename(initialdir=str(paths.DATA_DIR), initialfile=Path(var.get()).name)
        else:
            path = filedialog.askdirectory(initialdir=var.get() or str(paths.DATA_DIR))
        if path:
            var.set(path)

    def _refresh_db_info(self):
        try:
            stats = self.sm.get_dashboard_stats()
            self._db_info_text.config(state="normal")
            self._db_info_text.delete("1.0", "end")
            self._db_info_text.insert("end",
                f"Students: {stats['total_students']}    "
                f"Barcode Mappings: {stats['total_barcodes']}\n"
                f"Answer Keys: {stats['total_answer_keys']}    "
                f"Total Results: {stats['total_results']}    "
                f"Pending Review: {stats['pending_review']}\n"
                f"Scan Batches: {stats['batches_count']}\n"
                f"Database: {str(paths.DEFAULT_DB_PATH)}"
            )
            self._db_info_text.config(state="disabled")
        except Exception as e:
            pass

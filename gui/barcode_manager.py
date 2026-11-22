"""
Barcode Database panel — import and inspect student barcode mappings.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from config.paths import BARCODE_DIR, dialog_dir
from gui.ui_utils import COLORS, FONTS, SectionHeader
from database.repositories import ServiceManager
from integrations.barcode_creator_importer import BarcodeImporter

class BarcodeManagerPanel(tk.Frame):
    def __init__(self, parent, service_manager: ServiceManager):
        super().__init__(parent, bg=COLORS["bg"])
        self.sm = service_manager
        self.importer = BarcodeImporter(self.sm.barcodes)
        self._build()
        self.refresh()

    def _build(self):
        SectionHeader(self, "Barcode Database",
                      "Import and inspect student barcode mappings").pack(
                          fill="x", padx=24, pady=(24, 8))

        # Import row
        import_frame = tk.LabelFrame(self, text="  Import Barcode Workbooks  ",
                                      bg=COLORS["bg"], font=FONTS["heading"],
                                      fg=COLORS["text_primary"], bd=1, relief="groove")
        import_frame.pack(fill="x", padx=24, pady=8)

        btn_row = tk.Frame(import_frame, bg=COLORS["bg"])
        btn_row.pack(fill="x", padx=8, pady=10)

        ttk.Button(btn_row, text="📄 Import File",
                   command=self._import_file, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(btn_row, text="📂 Import Folder",
                   command=self._import_folder).pack(side="left", padx=4)
        ttk.Button(btn_row, text="🔄 Refresh",
                   command=self.refresh).pack(side="right", padx=4)

        self._import_log = tk.Text(import_frame, height=4, state="disabled",
                                    font=FONTS["mono"], bg="#1A1D2E", fg="#A8D8A8",
                                    relief="flat", padx=8)
        self._import_log.pack(fill="x", padx=8, pady=(0, 8))

        # Search + List
        search_frame = tk.Frame(self, bg=COLORS["bg"])
        search_frame.pack(fill="x", padx=24, pady=(8, 4))
        tk.Label(search_frame, text="🔍 Search:", font=FONTS["body"],
                 bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(search_frame, textvariable=self._search_var, width=36).pack(
            side="left", padx=8)

        self._count_lbl = tk.Label(search_frame, text="", font=FONTS["small"],
                                    bg=COLORS["bg"], fg=COLORS["text_secondary"])
        self._count_lbl.pack(side="right")

        # Barcode table
        cols = ("Barcode Value", "Student ID", "Student Name", "Subject", "Exam ID", "Source File")
        self._tree = ttk.Treeview(self, columns=cols, show="headings")
        widths = [200, 110, 160, 110, 130, 180]
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="w")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.pack(side="left", fill="both", expand=True, padx=(24, 0), pady=8)
        vsb.pack(side="left", fill="y", pady=8)

    def refresh(self):
        self._tree.delete(*self._tree.get_children())
        q = self._search_var.get()
        mappings = self.sm.barcodes.get_all(search=q)
        for m in mappings:
            self._tree.insert("", "end", values=(
                m.barcode_value, m.student_id, m.student_name,
                m.subject, m.exam_id, m.source_file or ""
            ))
        self._count_lbl.config(text=f"{len(mappings)} records")

    def _import_file(self):
        path = filedialog.askopenfilename(
            title="Select Barcode Creator Excel File",
            initialdir=dialog_dir(BARCODE_DIR),
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if path:
            count, warnings = self.importer.import_file(Path(path))
            self._show_import_result(count, warnings)

    def _import_folder(self):
        path = filedialog.askdirectory(title="Select Folder Containing Barcode Excel Files",
                                     initialdir=dialog_dir(BARCODE_DIR))
        if path:
            count, warnings = self.importer.import_directory(Path(path))
            self._show_import_result(count, warnings)

    def _show_import_result(self, count: int, warnings: list):
        self._import_log.config(state="normal")
        self._import_log.delete("1.0", "end")
        self._import_log.insert("end", f"✅ Imported: {count} records\n")
        for w in warnings:
            self._import_log.insert("end", f"⚠️  {w}\n")
        self._import_log.config(state="disabled")
        self.refresh()

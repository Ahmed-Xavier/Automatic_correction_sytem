"""
Results Viewer panel.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional

from datetime import datetime
from config.paths import EXPORTS_DIR, dialog_dir
from gui.ui_utils import COLORS, FONTS, SectionHeader
from database.repositories import ServiceManager
from exports.excel_exporter import ExcelExporter

class ResultsPanel(tk.Frame):
    def __init__(self, parent, service_manager: ServiceManager):
        super().__init__(parent, bg=COLORS["bg"])
        self.sm = service_manager
        self.exporter = ExcelExporter(service_manager)
        self._build()
        self.refresh()

    def _build(self):
        SectionHeader(self, "Results",
                      "View and export examination results").pack(
                          fill="x", padx=24, pady=(24, 8))

        # Filters row
        filter_frame = tk.Frame(self, bg=COLORS["bg"])
        filter_frame.pack(fill="x", padx=24, pady=8)

        tk.Label(filter_frame, text="Filter by Exam:", bg=COLORS["bg"],
                 font=FONTS["body"], fg=COLORS["text_secondary"]).pack(side="left")
        self._exam_filter_var = tk.StringVar(value="All")
        self._exam_combo = ttk.Combobox(filter_frame, textvariable=self._exam_filter_var,
                                         values=["All"], width=20, state="readonly")
        self._exam_combo.pack(side="left", padx=6)
        self._exam_combo.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        tk.Label(filter_frame, text="Status:", bg=COLORS["bg"],
                 font=FONTS["body"], fg=COLORS["text_secondary"]).pack(side="left", padx=(12, 0))
        self._status_filter_var = tk.StringVar(value="All")
        ttk.Combobox(filter_frame, textvariable=self._status_filter_var,
                     values=["All", "Confirmed", "Pending Review", "Rejected"],
                     width=15, state="readonly").pack(side="left", padx=6)
        self._status_filter_var.trace_add("write", lambda *_: self.refresh())

        ttk.Button(filter_frame, text="🔄 Refresh",
                   command=self.refresh).pack(side="left", padx=12)
        ttk.Button(filter_frame, text="📊 Export to Excel",
                   command=self._export_excel, style="Accent.TButton").pack(side="right", padx=4)

        self._count_lbl = tk.Label(filter_frame, text="", font=FONTS["small"],
                                    bg=COLORS["bg"], fg=COLORS["text_secondary"])
        self._count_lbl.pack(side="right", padx=8)

        # Results table
        cols = ("Student ID", "Student Name", "Subject", "Exam ID",
                "Barcode", "Type", "Score", "Max", "Status", "Override")
        self._tree = ttk.Treeview(self, columns=cols, show="headings")
        widths = [100, 150, 100, 130, 180, 70, 70, 70, 120, 80]
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col,
                               command=lambda c=col: self._sort_by(c))
            self._tree.column(col, width=w, anchor="w")

        self._tree.tag_configure("review", background="#FEF3C7")
        self._tree.tag_configure("rejected", background="#FEE2E2", foreground="#B91C1C")
        self._tree.tag_configure("override", background="#ECFDF5")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.pack(side="left", fill="both", expand=True,
                        padx=(24, 0), pady=(0, 8))
        vsb.pack(side="left", fill="y", pady=(0, 8))

        self._sort_col = None
        self._sort_rev = False

    def refresh(self):
        # Refresh exam combo
        exams = ["All"] + [ex.exam_id for ex in self.sm.exams.get_all()]
        self._exam_combo.config(values=exams)

        exam_filter = self._exam_filter_var.get()
        status_filter = self._status_filter_var.get()

        exam_id = None if exam_filter == "All" else exam_filter
        status = None if status_filter == "All" else status_filter

        results = self.sm.results.get_all_results(exam_id=exam_id, status=status)

        self._tree.delete(*self._tree.get_children())
        for r in results:
            tag = ""
            if r.review_status == "Pending Review":
                tag = "review"
            elif r.review_status == "Rejected":
                tag = "rejected"
            elif r.manual_override:
                tag = "override"

            self._tree.insert("", "end", values=(
                r.student_id, r.student_name, r.subject, r.exam_id,
                r.barcode_value, r.correction_type,
                f"{r.score:.2f}", f"{r.maximum_score:.2f}",
                r.review_status, "Yes" if r.manual_override else ""
            ), tags=(tag,))

        self._count_lbl.config(text=f"{len(results)} results")

    def _sort_by(self, col: str):
        # Simple toggle sort
        items = [(self._tree.set(item, col), item) for item in self._tree.get_children("")]
        reverse = self._sort_col == col and not self._sort_rev
        items.sort(reverse=reverse)
        for idx, (_, item) in enumerate(items):
            self._tree.move(item, "", idx)
        self._sort_col = col
        self._sort_rev = reverse

    def _export_excel(self):
        exam_filter = self._exam_filter_var.get()
        exam_id = None if exam_filter == "All" else exam_filter

        path = filedialog.asksaveasfilename(
            title="Save Master Results Excel",
            initialdir=dialog_dir(EXPORTS_DIR),
            initialfile=f"master-results-{datetime.now():%Y%m%d-%H%M}.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if not path:
            return
        try:
            out = self.exporter.export_master_results(
                output_path=Path(path), exam_id_filter=exam_id
            )
            messagebox.showinfo("Export Complete", f"Results exported to:\n{out}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

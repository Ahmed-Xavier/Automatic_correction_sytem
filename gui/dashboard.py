"""
Dashboard panel — statistics overview and quick actions.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Dict, Any

from gui.ui_utils import COLORS, FONTS, StatCard, SectionHeader

class DashboardPanel(tk.Frame):
    def __init__(self, parent, service_manager, on_navigate: Callable[[str], None]):
        super().__init__(parent, bg=COLORS["bg"])
        self.sm = service_manager
        self.on_navigate = on_navigate

        self._build()
        self.refresh()

    def _build(self):
        # Title
        hdr = SectionHeader(self, "Dashboard", "Overview of examination processing status")
        hdr.pack(fill="x", padx=24, pady=(24, 8))

        # Stats grid
        self._stats_frame = tk.Frame(self, bg=COLORS["bg"])
        self._stats_frame.pack(fill="x", padx=24, pady=8)

        self._stat_cards: Dict[str, StatCard] = {}
        stat_defs = [
            ("total_exams",      "Examinations",       COLORS["accent"]),
            ("total_students",   "Students",           COLORS["success"]),
            ("total_barcodes",   "Barcode Mappings",   COLORS["accent"]),
            ("total_answer_keys","Answer Keys",        COLORS["accent"]),
            ("total_results",    "Total Results",      COLORS["text_primary"]),
            ("confirmed_results","Confirmed",          COLORS["success"]),
            ("pending_review",   "Pending Review",     COLORS["review"]),
            ("batches_count",    "Scan Batches",       COLORS["text_secondary"]),
        ]

        for col_idx, (key, label, color) in enumerate(stat_defs):
            card = StatCard(self._stats_frame, label=label, color=color)
            card.grid(row=col_idx // 4, column=col_idx % 4, padx=8, pady=8, sticky="nsew")
            self._stat_cards[key] = card

        for c in range(4):
            self._stats_frame.columnconfigure(c, weight=1)

        # Quick actions
        qa_frame = tk.LabelFrame(self, text="  Quick Actions  ", bg=COLORS["bg"],
                                  font=FONTS["heading"], fg=COLORS["text_primary"],
                                  bd=1, relief="groove")
        qa_frame.pack(fill="x", padx=24, pady=12)

        actions = [
            ("📂  Import Barcode File",   lambda: self.on_navigate("barcode_import")),
            ("🔑  Import Answer Key",     lambda: self.on_navigate("answer_key")),
            ("📋  Manage Examinations",   lambda: self.on_navigate("exams")),
            ("🖨️  Process Scans",          lambda: self.on_navigate("scan_processing")),
            ("🔍  Manual Review",          lambda: self.on_navigate("manual_review")),
            ("📊  Export Results",         lambda: self.on_navigate("results")),
        ]

        for col_idx, (label, cmd) in enumerate(actions):
            btn = ttk.Button(qa_frame, text=label, command=cmd, style="Accent.TButton")
            btn.grid(row=0, column=col_idx, padx=10, pady=12, sticky="ew")
            qa_frame.columnconfigure(col_idx, weight=1)

        # Recent activity placeholder
        recent_frame = tk.LabelFrame(self, text="  Recent Scan Batches  ", bg=COLORS["bg"],
                                      font=FONTS["heading"], fg=COLORS["text_primary"],
                                      bd=1, relief="groove")
        recent_frame.pack(fill="both", expand=True, padx=24, pady=12)

        cols = ("Batch ID", "Source File", "Pages", "Status", "Received")
        self._batch_tree = ttk.Treeview(recent_frame, columns=cols, show="headings", height=8)
        for col in cols:
            self._batch_tree.heading(col, text=col)
            self._batch_tree.column(col, width=160, anchor="w")
        self._batch_tree.pack(fill="both", expand=True, padx=8, pady=8)

        sb = ttk.Scrollbar(recent_frame, orient="vertical", command=self._batch_tree.yview)
        self._batch_tree.configure(yscrollcommand=sb.set)

        # Refresh button
        ttk.Button(self, text="🔄 Refresh", command=self.refresh).pack(anchor="e", padx=24, pady=8)

    def refresh(self):
        try:
            stats = self.sm.get_dashboard_stats()
            for key, card in self._stat_cards.items():
                card.update_value(stats.get(key, 0))

            # Update recent batches
            self._batch_tree.delete(*self._batch_tree.get_children())
            batches = self.sm.results.get_all_batches()
            for b in batches[:20]:
                self._batch_tree.insert("", "end", values=(
                    b.batch_id, b.source_file, b.total_pages, b.status, b.received_at or ""
                ))
        except Exception as e:
            pass  # DB not ready yet

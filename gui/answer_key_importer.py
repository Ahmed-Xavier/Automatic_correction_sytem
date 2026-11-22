"""
Answer Key Import panel.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional

from gui.ui_utils import COLORS, FONTS, SectionHeader
from database.repositories import ServiceManager
from integrations.answer_key_importer import AnswerKeyImporter

class AnswerKeyPanel(tk.Frame):
    def __init__(self, parent, service_manager: ServiceManager):
        super().__init__(parent, bg=COLORS["bg"])
        self.sm = service_manager
        self.importer = AnswerKeyImporter(
            key_repo=self.sm.answer_keys,
            exam_repo=self.sm.exams
        )
        self._build()
        self.refresh()

    def _build(self):
        SectionHeader(self, "Answer Key Import",
                      "Import and manage QCM answer keys and grading configurations").pack(
                          fill="x", padx=24, pady=(24, 8))

        # Import controls
        import_frame = tk.LabelFrame(self, text="  Import Answer Key Workbooks  ",
                                      bg=COLORS["bg"], font=FONTS["heading"],
                                      fg=COLORS["text_primary"], bd=1, relief="groove")
        import_frame.pack(fill="x", padx=24, pady=8)

        btn_row = tk.Frame(import_frame, bg=COLORS["bg"])
        btn_row.pack(fill="x", padx=8, pady=10)

        ttk.Button(btn_row, text="📄 Import File",
                   command=self._import_file, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(btn_row, text="🔄 Refresh",
                   command=self.refresh).pack(side="right", padx=4)

        self._import_log = tk.Text(import_frame, height=4, state="disabled",
                                    font=FONTS["mono"], bg="#1A1D2E", fg="#A8D8A8",
                                    relief="flat", padx=8)
        self._import_log.pack(fill="x", padx=8, pady=(0, 8))

        # Answer key list
        list_frame = tk.Frame(self, bg=COLORS["bg"])
        list_frame.pack(fill="both", expand=True, padx=24, pady=8)

        tk.Label(list_frame, text="Imported Answer Keys", font=FONTS["heading"],
                 bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(0, 4))

        cols = ("Key ID", "Exam ID", "Version", "Questions",
                "Correct Pts", "Incorrect Pts", "Status", "Source File")
        self._tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=12)
        widths = [70, 140, 70, 90, 100, 110, 100, 200]
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="w")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        # Preview frame
        preview_frame = tk.LabelFrame(self, text="  Answer Key Preview  ",
                                       bg=COLORS["bg"], font=FONTS["heading"],
                                       fg=COLORS["text_primary"], bd=1, relief="groove")
        preview_frame.pack(fill="x", padx=24, pady=8)

        self._preview_text = tk.Text(preview_frame, height=8, state="disabled",
                                      font=FONTS["mono"], bg="#F9FAFB",
                                      fg=COLORS["text_primary"], relief="flat", padx=8)
        self._preview_text.pack(fill="x", padx=8, pady=8)

    def refresh(self):
        self._tree.delete(*self._tree.get_children())
        keys = self.sm.answer_keys.get_all()
        for k in keys:
            self._tree.insert("", "end", iid=str(k.answer_key_id), values=(
                k.answer_key_id, k.exam_id, k.version, len(k.answers),
                k.correct_points, k.incorrect_points, k.status, k.source_file or ""
            ))

    def _on_select(self, event=None):
        sel = self._tree.selection()
        if not sel:
            return
        key_id = int(sel[0])
        keys = self.sm.answer_keys.get_all()
        key = next((k for k in keys if k.answer_key_id == key_id), None)
        if not key:
            return

        self._preview_text.config(state="normal")
        self._preview_text.delete("1.0", "end")
        self._preview_text.insert("end",
            f"Exam ID: {key.exam_id}  |  Version: {key.version}  |  Questions: {len(key.answers)}\n"
            f"Scoring: +{key.correct_points} / {key.incorrect_points} / {key.unanswered_points} (unanswered)\n\n"
        )
        line = ""
        for item in sorted(key.answers, key=lambda x: x.question_number):
            line += f"Q{item.question_number:>2}: {item.correct_answer}   "
            if item.question_number % 10 == 0:
                self._preview_text.insert("end", line + "\n")
                line = ""
        if line:
            self._preview_text.insert("end", line + "\n")
        self._preview_text.config(state="disabled")

    def _import_file(self):
        path = filedialog.askopenfilename(
            title="Select Answer Key Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if not path:
            return
        ok, msg, key = self.importer.import_file(Path(path))
        self._import_log.config(state="normal")
        self._import_log.delete("1.0", "end")
        icon = "✅" if ok else "❌"
        self._import_log.insert("end", f"{icon} {msg}\n")
        self._import_log.config(state="disabled")
        if ok:
            self.refresh()

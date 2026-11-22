"""
Examination Manager panel.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from gui.ui_utils import COLORS, FONTS, SectionHeader
from database.models import Examination

class ExamManagerPanel(tk.Frame):
    def __init__(self, parent, service_manager):
        super().__init__(parent, bg=COLORS["bg"])
        self.sm = service_manager
        self._selected_id: Optional[str] = None
        self._build()
        self.refresh()

    def _build(self):
        SectionHeader(self, "Examination Manager",
                      "Create and manage examinations").pack(fill="x", padx=24, pady=(24, 8))

        # Main layout: left=list, right=form
        panes = tk.PanedWindow(self, orient="horizontal", sashwidth=4,
                                bg=COLORS["card_border"])
        panes.pack(fill="both", expand=True, padx=24, pady=8)

        # ---- Left: exam list ----
        left = tk.Frame(panes, bg=COLORS["bg"])
        panes.add(left, minsize=320)

        tk.Label(left, text="Registered Examinations", font=FONTS["heading"],
                 bg=COLORS["bg"], fg=COLORS["text_primary"]).pack(anchor="w", pady=(0, 4))

        search_frame = tk.Frame(left, bg=COLORS["bg"])
        search_frame.pack(fill="x", pady=(0, 6))
        tk.Label(search_frame, text="🔍", bg=COLORS["bg"], font=FONTS["body"]).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(search_frame, textvariable=self._search_var).pack(side="left", fill="x", expand=True, padx=4)

        cols = ("Exam ID", "Subject", "Type", "Status")
        self._tree = ttk.Treeview(left, columns=cols, show="headings", height=16)
        for col in cols:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=90, anchor="w")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        sb = ttk.Scrollbar(left, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        btn_row = tk.Frame(left, bg=COLORS["bg"])
        btn_row.pack(fill="x", pady=6)
        ttk.Button(btn_row, text="➕ New", command=self._new_exam).pack(side="left", padx=2)
        ttk.Button(btn_row, text="🗂️ Archive", command=self._archive_exam).pack(side="left", padx=2)
        ttk.Button(btn_row, text="🔄 Refresh", command=self.refresh).pack(side="right", padx=2)

        # ---- Right: form ----
        right = tk.Frame(panes, bg=COLORS["card_bg"],
                          highlightbackground=COLORS["card_border"], highlightthickness=1)
        panes.add(right, minsize=340)

        tk.Label(right, text="Examination Details", font=FONTS["heading"],
                 bg=COLORS["card_bg"], fg=COLORS["text_primary"]).grid(
                     row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 8))

        fields = [
            ("Exam ID *",         "exam_id"),
            ("Subject *",         "subject"),
            ("Exam Name *",       "exam_name"),
            ("Date (YYYY-MM-DD)", "exam_date"),
            ("Maximum Score",     "maximum_score"),
            ("Num. Questions",    "num_questions"),
        ]

        self._vars: dict = {}
        for row_idx, (lbl, key) in enumerate(fields, start=1):
            tk.Label(right, text=lbl, font=FONTS["body"],
                     bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).grid(
                         row=row_idx, column=0, sticky="w", padx=16, pady=5)
            var = tk.StringVar()
            self._vars[key] = var
            ttk.Entry(right, textvariable=var, width=28).grid(
                row=row_idx, column=1, sticky="ew", padx=16, pady=5)

        # Type combo
        tk.Label(right, text="Exam Type *", font=FONTS["body"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).grid(
                     row=len(fields)+1, column=0, sticky="w", padx=16, pady=5)
        self._type_var = tk.StringVar(value="QCM")
        ttk.Combobox(right, textvariable=self._type_var,
                     values=["QCM", "Written"], width=26, state="readonly").grid(
                         row=len(fields)+1, column=1, sticky="ew", padx=16, pady=5)

        # Status combo
        tk.Label(right, text="Status *", font=FONTS["body"],
                 bg=COLORS["card_bg"], fg=COLORS["text_secondary"]).grid(
                     row=len(fields)+2, column=0, sticky="w", padx=16, pady=5)
        self._status_var = tk.StringVar(value="Active")
        ttk.Combobox(right, textvariable=self._status_var,
                     values=["Draft", "Active", "Archived"], width=26, state="readonly").grid(
                         row=len(fields)+2, column=1, sticky="ew", padx=16, pady=5)

        right.columnconfigure(1, weight=1)

        btn_save = ttk.Button(right, text="💾 Save Examination",
                               command=self._save_exam, style="Accent.TButton")
        btn_save.grid(row=len(fields)+3, column=0, columnspan=2,
                      sticky="ew", padx=16, pady=16)

        self._status_lbl = tk.Label(right, text="", bg=COLORS["card_bg"],
                                     font=FONTS["small"])
        self._status_lbl.grid(row=len(fields)+4, column=0, columnspan=2,
                               sticky="w", padx=16)

    def refresh(self):
        self._tree.delete(*self._tree.get_children())
        exams = self.sm.exams.get_all()
        q = self._search_var.get().lower()
        for ex in exams:
            if q and q not in ex.exam_id.lower() and q not in ex.subject.lower():
                continue
            tag = "archived" if ex.status == "Archived" else ""
            self._tree.insert("", "end", iid=ex.exam_id,
                               values=(ex.exam_id, ex.subject, ex.exam_type, ex.status),
                               tags=(tag,))
        self._tree.tag_configure("archived", foreground=COLORS["text_secondary"])

    def _on_select(self, event=None):
        sel = self._tree.selection()
        if not sel:
            return
        exam_id = sel[0]
        exam = self.sm.exams.get(exam_id)
        if exam:
            self._selected_id = exam_id
            self._vars["exam_id"].set(exam.exam_id)
            self._vars["subject"].set(exam.subject)
            self._vars["exam_name"].set(exam.exam_name)
            self._vars["exam_date"].set(exam.exam_date or "")
            self._vars["maximum_score"].set(str(exam.maximum_score))
            self._vars["num_questions"].set(str(exam.num_questions))
            self._type_var.set(exam.exam_type)
            self._status_var.set(exam.status)

    def _new_exam(self):
        self._selected_id = None
        for var in self._vars.values():
            var.set("")
        self._vars["maximum_score"].set("20.0")
        self._vars["num_questions"].set("40")
        self._type_var.set("QCM")
        self._status_var.set("Active")
        self._status_lbl.config(text="")

    def _save_exam(self):
        exam_id = self._vars["exam_id"].get().strip()
        subject = self._vars["subject"].get().strip()
        name = self._vars["exam_name"].get().strip()

        if not exam_id or not subject or not name:
            messagebox.showwarning("Missing Fields", "Exam ID, Subject, and Exam Name are required.")
            return

        try:
            max_score = float(self._vars["maximum_score"].get() or "20")
            num_q = int(self._vars["num_questions"].get() or "40")
        except ValueError:
            messagebox.showerror("Invalid Input", "Maximum Score must be a number, Num. Questions must be an integer.")
            return

        exam = Examination(
            exam_id=exam_id,
            subject=subject,
            exam_name=name,
            exam_type=self._type_var.get(),
            maximum_score=max_score,
            exam_date=self._vars["exam_date"].get().strip() or None,
            num_questions=num_q,
            status=self._status_var.get()
        )

        try:
            self.sm.exams.create_or_update(exam)
            self._status_lbl.config(text="✅ Saved successfully", fg=COLORS["success"])
            self.refresh()
        except Exception as e:
            self._status_lbl.config(text=f"❌ Error: {str(e)}", fg=COLORS["danger"])

    def _archive_exam(self):
        sel = self._tree.selection()
        if not sel:
            return
        exam_id = sel[0]
        if messagebox.askyesno("Archive Examination",
                                f"Archive examination '{exam_id}'?\nIt will not be deleted but marked inactive."):
            exam = self.sm.exams.get(exam_id)
            if exam:
                exam.status = "Archived"
                self.sm.exams.create_or_update(exam)
                self.refresh()

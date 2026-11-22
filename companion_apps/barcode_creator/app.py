"""
Companion App A — Student Barcode Creator.
Standalone Tkinter application for generating student barcode assignments.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import uuid
from datetime import datetime
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.paths import BARCODE_DIR, STICKERS_DIR, dialog_dir
from gui.ui_utils import COLORS, FONTS, apply_theme, SectionHeader
from companion_apps.barcode_creator.excel_generator import generate_barcode_excel
from companion_apps.barcode_creator.pdf_generator import generate_barcode_pdf


class BarCodeCreatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Student Barcode Creator")
        self.root.geometry("900x680")
        apply_theme(self.root)
        self.root.configure(bg=COLORS["bg"])
        self._students: list = []
        self._build()

    def _build(self):
        SectionHeader(self.root, "Student Barcode Creator",
                      "Generate student barcode identifiers and sticker sheets").pack(
                          fill="x", padx=24, pady=(24, 8))

        # Exam info row
        info_frame = tk.LabelFrame(self.root, text="  Examination Information  ",
                                    bg=COLORS["bg"], font=FONTS["heading"],
                                    fg=COLORS["text_primary"], bd=1, relief="groove")
        info_frame.pack(fill="x", padx=24, pady=8)

        row = tk.Frame(info_frame, bg=COLORS["bg"])
        row.pack(fill="x", padx=8, pady=10)

        for label, attr in [("Subject:", "_subject_var"), ("Exam ID:", "_exam_id_var")]:
            tk.Label(row, text=label, bg=COLORS["bg"], font=FONTS["body"],
                     fg=COLORS["text_secondary"]).pack(side="left", padx=4)
            var = tk.StringVar()
            setattr(self, attr, var)
            ttk.Entry(row, textvariable=var, width=20).pack(side="left", padx=4)

        # Student input
        input_frame = tk.LabelFrame(self.root, text="  Add Students  ",
                                     bg=COLORS["bg"], font=FONTS["heading"],
                                     fg=COLORS["text_primary"], bd=1, relief="groove")
        input_frame.pack(fill="x", padx=24, pady=8)

        add_row = tk.Frame(input_frame, bg=COLORS["bg"])
        add_row.pack(fill="x", padx=8, pady=8)
        tk.Label(add_row, text="Student Name:", bg=COLORS["bg"],
                 font=FONTS["body"], fg=COLORS["text_secondary"]).pack(side="left")
        self._name_var = tk.StringVar()
        name_entry = ttk.Entry(add_row, textvariable=self._name_var, width=30)
        name_entry.pack(side="left", padx=6)
        name_entry.bind("<Return>", lambda _: self._add_student())

        tk.Label(add_row, text="Student ID:", bg=COLORS["bg"],
                 font=FONTS["body"], fg=COLORS["text_secondary"]).pack(side="left")
        self._sid_var = tk.StringVar()
        ttk.Entry(add_row, textvariable=self._sid_var, width=18).pack(side="left", padx=6)

        ttk.Button(add_row, text="➕ Add", command=self._add_student,
                   style="Accent.TButton").pack(side="left", padx=6)
        ttk.Button(add_row, text="📂 Import from Excel",
                   command=self._import_excel).pack(side="left", padx=4)

        # Student list
        cols = ("Student Name", "Student ID", "Barcode ID", "Full Barcode")
        self._tree = ttk.Treeview(self.root, columns=cols, show="headings", height=12)
        for col in cols:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=200, anchor="w")

        vsb = ttk.Scrollbar(self.root, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(24, 0), pady=8)
        vsb.pack(side="left", fill="y", pady=8)

        # Action buttons on right
        action_frame = tk.Frame(self.root, bg=COLORS["bg"])
        action_frame.pack(side="left", fill="y", padx=12, pady=8)

        ttk.Button(action_frame, text="🗑️ Remove Selected",
                   command=self._remove_selected).pack(fill="x", pady=4)
        ttk.Button(action_frame, text="🧹 Clear All",
                   command=self._clear_all).pack(fill="x", pady=4)

        tk.Frame(action_frame, bg=COLORS["card_border"], height=1).pack(fill="x", pady=12)

        ttk.Button(action_frame, text="📊 Generate Excel",
                   command=self._generate_excel, style="Accent.TButton").pack(fill="x", pady=4)
        ttk.Button(action_frame, text="🖨️ Generate PDF Stickers",
                   command=self._generate_pdf, style="Accent.TButton").pack(fill="x", pady=4)

        self._status_lbl = tk.Label(action_frame, text="", bg=COLORS["bg"],
                                     font=FONTS["small"], wraplength=150)
        self._status_lbl.pack(pady=8)

    def _make_barcode_id(self) -> str:
        return uuid.uuid4().hex[:8].upper()

    def _add_student(self):
        name = self._name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Please enter a student name.")
            return
        subject = self._subject_var.get().strip() or "GENERAL"
        exam_id = self._exam_id_var.get().strip() or f"{subject.upper()}-EXAM"
        barcode_id = self._make_barcode_id()
        full_barcode = f"{subject.upper()}-{barcode_id}"
        student_id = self._sid_var.get().strip() or f"STU-{barcode_id}"

        record = {
            "student_name": name,
            "student_id": student_id,
            "subject": subject.upper(),
            "exam_id": exam_id,
            "barcode_id": barcode_id,
            "full_barcode": full_barcode,
        }
        self._students.append(record)
        self._tree.insert("", "end", values=(name, student_id, barcode_id, full_barcode))
        self._name_var.set("")
        self._sid_var.set("")

    def _import_excel(self):
        import openpyxl
        path = filedialog.askopenfilename(
            title="Select Student List Excel File",
            initialdir=dialog_dir(BARCODE_DIR),
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return
            headers = [str(c).strip().lower() if c else "" for c in rows[0]]
            for data_row in rows[1:]:
                if not any(data_row):
                    continue
                name_idx = next((i for i, h in enumerate(headers) if "name" in h or "nom" in h), 0)
                id_idx = next((i for i, h in enumerate(headers) if "id" in h and "student" in h), None)
                name = str(data_row[name_idx]).strip() if data_row[name_idx] else ""
                if name:
                    self._sid_var.set(str(data_row[id_idx]).strip() if id_idx is not None and data_row[id_idx] else "")
                    self._name_var.set(name)
                    self._add_student()
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _remove_selected(self):
        sel = self._tree.selection()
        for iid in sel:
            idx = self._tree.index(iid)
            self._tree.delete(iid)
            if 0 <= idx < len(self._students):
                self._students.pop(idx)

    def _clear_all(self):
        self._tree.delete(*self._tree.get_children())
        self._students.clear()

    def _generate_excel(self):
        if not self._students:
            messagebox.showwarning("No Students", "Add students before generating.")
            return
        path = filedialog.asksaveasfilename(
            title="Save Barcode Mapping Excel",
            initialdir=dialog_dir(BARCODE_DIR),
            initialfile=f"barcodes-{datetime.now():%Y%m%d-%H%M}.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if not path:
            return
        try:
            out = generate_barcode_excel(Path(path), self._students)
            self._status_lbl.config(text=f"✅ Saved:\n{out.name}", fg=COLORS["success"])
        except Exception as e:
            self._status_lbl.config(text=f"❌ Error:\n{e}", fg=COLORS["danger"])

    def _generate_pdf(self):
        if not self._students:
            messagebox.showwarning("No Students", "Add students before generating.")
            return
        path = filedialog.asksaveasfilename(
            title="Save Barcode Sticker PDF",
            initialdir=dialog_dir(STICKERS_DIR),
            initialfile=f"stickers-{datetime.now():%Y%m%d-%H%M}.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not path:
            return
        try:
            out = generate_barcode_pdf(Path(path), self._students)
            self._status_lbl.config(text=f"✅ Saved:\n{out.name}", fg=COLORS["success"])
        except Exception as e:
            self._status_lbl.config(text=f"❌ Error:\n{e}", fg=COLORS["danger"])

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    BarCodeCreatorApp().run()

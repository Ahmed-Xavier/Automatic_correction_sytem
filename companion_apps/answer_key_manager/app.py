"""
Companion App B — Answer Key Manager.
Standalone Tkinter application for creating QCM answer keys.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.paths import ANSWER_KEYS_DIR, dialog_dir
from gui.ui_utils import COLORS, FONTS, apply_theme, SectionHeader, size_window_to_screen

class AnswerKeyManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Answer Key Manager")
        apply_theme(self.root)
        self.root.configure(bg=COLORS["bg"])
        self._answers: dict = {}  # q_num -> selected option
        self._num_questions = 40
        self._options = ["A", "B", "C"]
        self._option_buttons: dict = {}  # (q_num, opt) -> tk.Button
        self._build()
        size_window_to_screen(self.root)

    def _build(self):
        SectionHeader(self.root, "Answer Key Manager",
                      "Create and export QCM answer keys and grading configurations").pack(
                          fill="x", padx=24, pady=(24, 8))

        # Exam config row
        config_frame = tk.LabelFrame(self.root, text="  Examination Configuration  ",
                                      bg=COLORS["bg"], font=FONTS["heading"],
                                      fg=COLORS["text_primary"], bd=1, relief="groove")
        config_frame.pack(fill="x", padx=24, pady=8)

        cfg_row = tk.Frame(config_frame, bg=COLORS["bg"])
        cfg_row.pack(fill="x", padx=8, pady=10)

        cfg_items = [
            ("Subject:", "_subject_var"),
            ("Exam Name:", "_exam_name_var"),
        ]
        for lbl, attr in cfg_items:
            tk.Label(cfg_row, text=lbl, bg=COLORS["bg"], font=FONTS["body"],
                     fg=COLORS["text_secondary"]).pack(side="left", padx=4)
            var = tk.StringVar()
            setattr(self, attr, var)
            ttk.Entry(cfg_row, textvariable=var, width=18).pack(side="left", padx=4)

        tk.Label(cfg_row, text="Questions:", bg=COLORS["bg"], font=FONTS["body"],
                 fg=COLORS["text_secondary"]).pack(side="left", padx=(12, 4))
        self._num_q_var = tk.StringVar(value="40")
        ttk.Entry(cfg_row, textvariable=self._num_q_var, width=5).pack(side="left", padx=4)
        ttk.Button(cfg_row, text="⚙ Apply", command=self._apply_num_q).pack(side="left", padx=8)

        # Grading row
        grade_frame = tk.Frame(config_frame, bg=COLORS["bg"])
        grade_frame.pack(fill="x", padx=8, pady=(0, 10))
        grade_defs = [
            ("Max Score:", "_max_score_var", "20.0"),
            ("Correct Pts:", "_correct_pts_var", "0.5"),
            ("Incorrect Pts:", "_incorrect_pts_var", "0.0"),
            ("Unanswered Pts:", "_unanswered_pts_var", "0.0"),
        ]
        for lbl, attr, default in grade_defs:
            tk.Label(grade_frame, text=lbl, bg=COLORS["bg"], font=FONTS["body"],
                     fg=COLORS["text_secondary"]).pack(side="left", padx=4)
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            ttk.Entry(grade_frame, textvariable=var, width=6).pack(side="left", padx=4)

        # Answer grid in a scrollable canvas
        grid_outer = tk.LabelFrame(self.root, text="  Answer Grid — Click to select correct answer  ",
                                    bg=COLORS["bg"], font=FONTS["heading"],
                                    fg=COLORS["text_primary"], bd=1, relief="groove")
        grid_outer.pack(fill="both", expand=True, padx=24, pady=8)

        self._canvas = tk.Canvas(grid_outer, bg=COLORS["bg"], highlightthickness=0)
        self._vsb = ttk.Scrollbar(grid_outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)
        self._vsb.pack(side="right", fill="y")
        self._canvas.pack(fill="both", expand=True)

        self._grid_frame = tk.Frame(self._canvas, bg=COLORS["bg"])
        self._canvas.create_window((0, 0), window=self._grid_frame, anchor="nw")
        self._grid_frame.bind("<Configure>",
                               lambda e: self._canvas.configure(
                                   scrollregion=self._canvas.bbox("all")))

        self._rebuild_grid()

        # Bottom action buttons
        btn_row = tk.Frame(self.root, bg=COLORS["bg"])
        btn_row.pack(fill="x", padx=24, pady=8)
        ttk.Button(btn_row, text="🧹 Clear All Answers",
                   command=self._clear_answers).pack(side="left", padx=4)
        ttk.Button(btn_row, text="👁 Preview Answer Key",
                   command=self._preview).pack(side="left", padx=4)
        ttk.Button(btn_row, text="💾 Export to Excel",
                   command=self._export_excel, style="Accent.TButton").pack(side="right", padx=4)

        self._status_lbl = tk.Label(self.root, text="", bg=COLORS["bg"], font=FONTS["small"])
        self._status_lbl.pack(pady=4)

    def _apply_num_q(self):
        try:
            n = int(self._num_q_var.get())
            assert 1 <= n <= 200
            self._num_questions = n
            self._answers = {k: v for k, v in self._answers.items() if k <= n}
            self._rebuild_grid()
        except Exception:
            messagebox.showwarning("Invalid", "Questions must be a number between 1 and 200.")

    def _rebuild_grid(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self._option_buttons = {}

        # Header
        tk.Label(self._grid_frame, text="Q#", width=4, font=FONTS["heading"],
                 bg=COLORS["bg"], fg=COLORS["text_secondary"]).grid(row=0, column=0, padx=4, pady=4)
        for opt_idx, opt in enumerate(self._options):
            tk.Label(self._grid_frame, text=opt, width=4, font=FONTS["heading"],
                     bg=COLORS["bg"], fg=COLORS["accent"]).grid(row=0, column=opt_idx+1, padx=4, pady=4)

        for q_num in range(1, self._num_questions + 1):
            tk.Label(self._grid_frame, text=str(q_num), width=4, font=FONTS["body"],
                     bg=COLORS["bg"], fg=COLORS["text_secondary"]).grid(
                         row=q_num, column=0, padx=4, pady=2)
            for opt_idx, opt in enumerate(self._options):
                is_selected = self._answers.get(q_num) == opt
                btn = tk.Button(
                    self._grid_frame, text="●" if is_selected else "○",
                    width=3, font=("Segoe UI", 11),
                    bg=COLORS["accent"] if is_selected else COLORS["card_bg"],
                    fg="white" if is_selected else COLORS["text_secondary"],
                    relief="flat", cursor="hand2",
                    command=lambda q=q_num, o=opt: self._select_answer(q, o)
                )
                btn.grid(row=q_num, column=opt_idx+1, padx=4, pady=2)
                self._option_buttons[(q_num, opt)] = btn

    def _select_answer(self, q_num: int, opt: str):
        prev = self._answers.get(q_num)
        if prev:
            old_btn = self._option_buttons.get((q_num, prev))
            if old_btn:
                old_btn.config(text="○", bg=COLORS["card_bg"], fg=COLORS["text_secondary"])

        if prev == opt:
            # Deselect
            del self._answers[q_num]
        else:
            self._answers[q_num] = opt
            new_btn = self._option_buttons.get((q_num, opt))
            if new_btn:
                new_btn.config(text="●", bg=COLORS["accent"], fg="white")

    def _clear_answers(self):
        self._answers.clear()
        self._rebuild_grid()

    def _preview(self):
        win = tk.Toplevel(self.root)
        win.title("Answer Key Preview")
        win.configure(bg=COLORS["bg"])
        txt = tk.Text(win, font=FONTS["mono"], bg="#F9FAFB",
                      fg=COLORS["text_primary"], padx=12, pady=8)
        txt.pack(fill="both", expand=True, padx=12, pady=12)
        txt.insert("end",
            f"Subject: {self._subject_var.get() or '—'}\n"
            f"Questions: {self._num_questions}   "
            f"Max Score: {self._max_score_var.get()}\n"
            f"Scoring: +{self._correct_pts_var.get()} / {self._incorrect_pts_var.get()} / "
            f"{self._unanswered_pts_var.get()} (unanswered)\n\n"
        )
        line = ""
        for q in range(1, self._num_questions + 1):
            ans = self._answers.get(q, "_")
            line += f"Q{q:>2}:{ans}  "
            if q % 10 == 0:
                txt.insert("end", line + "\n")
                line = ""
        if line:
            txt.insert("end", line + "\n")
        unanswered = [q for q in range(1, self._num_questions + 1) if q not in self._answers]
        if unanswered:
            txt.insert("end", f"\n⚠️  Unanswered questions: {unanswered}\n")
        txt.config(state="disabled")
        size_window_to_screen(win)

    def _export_excel(self):
        subject = self._subject_var.get().strip()
        if not subject:
            messagebox.showwarning("Missing Info", "Please fill in the Subject first.")
            return
        exam_id = f"{subject.upper()}-EXAM"
        if not self._answers:
            messagebox.showwarning("No Answers", "Please select correct answers first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save Answer Key Excel",
            initialdir=dialog_dir(ANSWER_KEYS_DIR),
            initialfile=f"{subject.strip().replace(' ', '-')}-answer-key.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if not path:
            return
        try:
            correct_pts = float(self._correct_pts_var.get())
            incorrect_pts = float(self._incorrect_pts_var.get())
            unanswered_pts = float(self._unanswered_pts_var.get())
            max_score = float(self._max_score_var.get())
        except ValueError:
            messagebox.showerror("Invalid", "Score values must be numbers.")
            return

        wb = openpyxl.Workbook()
        hfont = Font(bold=True, color="FFFFFF")
        hfill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

        # Sheet 1 — Exam Info
        ws1 = wb.active
        ws1.title = "Exam Information"
        ws1.append(["Exam ID", "Subject", "Exam Name", "Exam Type", "Maximum Score", "Version"])
        for c in range(1, 7):
            ws1.cell(1, c).font = hfont
            ws1.cell(1, c).fill = hfill
        ws1.append([exam_id, subject,
                    self._exam_name_var.get().strip() or f"{subject} Exam",
                    "QCM", max_score, 1])

        # Sheet 2 — Answer Key
        ws2 = wb.create_sheet("Answer Key")
        ws2.append(["Exam ID", "Question Number", "Correct Answer", "Points"])
        for c in range(1, 5):
            ws2.cell(1, c).font = hfont
            ws2.cell(1, c).fill = hfill
        for q_num in sorted(self._answers.keys()):
            ws2.append([exam_id, q_num, self._answers[q_num], correct_pts])

        # Sheet 3 — Grading Rules
        ws3 = wb.create_sheet("Grading Rules")
        ws3.append(["Exam ID", "Correct Points", "Incorrect Points",
                    "Unanswered Points", "Maximum Score"])
        for c in range(1, 6):
            ws3.cell(1, c).font = hfont
            ws3.cell(1, c).fill = hfill
        ws3.append([exam_id, correct_pts, incorrect_pts, unanswered_pts, max_score])

        wb.save(path)
        self._status_lbl.config(
            text=f"✅ Exported {len(self._answers)}/{self._num_questions} answers to {Path(path).name}",
            fg=COLORS["success"]
        )

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AnswerKeyManagerApp().run()

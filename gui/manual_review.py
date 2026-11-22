"""
Manual Review panel — view uncertain documents and correct recognition results.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional
from PIL import Image, ImageTk
import cv2
import numpy as np

from gui.ui_utils import COLORS, FONTS, SectionHeader
from database.repositories import ServiceManager
from database.models import ScannedDocument, ExamResult

class ManualReviewPanel(tk.Frame):
    def __init__(self, parent, service_manager: ServiceManager):
        super().__init__(parent, bg=COLORS["bg"])
        self.sm = service_manager
        self._current_doc: Optional[ScannedDocument] = None
        self._current_result: Optional[ExamResult] = None
        self._photo_ref = None
        self._build()
        self.refresh()

    def _build(self):
        SectionHeader(self, "Manual Review",
                      "Review and correct uncertain document recognition results").pack(
                          fill="x", padx=24, pady=(24, 8))

        # Document list
        list_frame = tk.LabelFrame(self, text="  Documents Requiring Review  ",
                                    bg=COLORS["bg"], font=FONTS["heading"],
                                    fg=COLORS["text_primary"], bd=1, relief="groove")
        list_frame.pack(fill="x", padx=24, pady=8)

        cols = ("Document ID", "Type", "Barcode", "Warning", "Status")
        self._doc_tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=5)
        widths = [200, 100, 180, 320, 120]
        for col, w in zip(cols, widths):
            self._doc_tree.heading(col, text=col)
            self._doc_tree.column(col, width=w, anchor="w")
        self._doc_tree.bind("<<TreeviewSelect>>", self._on_doc_select)

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self._doc_tree.yview)
        self._doc_tree.configure(yscrollcommand=vsb.set)
        self._doc_tree.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        vsb.pack(side="left", fill="y", pady=8)

        btn_row = tk.Frame(list_frame, bg=COLORS["bg"])
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btn_row, text="🔄 Refresh List", command=self.refresh).pack(side="left", padx=4)

        # Review workspace
        workspace = tk.Frame(self, bg=COLORS["bg"])
        workspace.pack(fill="both", expand=True, padx=24, pady=8)
        workspace.columnconfigure(0, weight=1)
        workspace.columnconfigure(1, weight=1)

        # Image canvas
        img_frame = tk.LabelFrame(workspace, text="  Scanned Document  ",
                                   bg=COLORS["bg"], font=FONTS["heading"],
                                   fg=COLORS["text_primary"], bd=1, relief="groove")
        img_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        self._canvas = tk.Canvas(img_frame, bg="#2D2D2D", width=380, height=480)
        self._canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # Correction form
        form_frame = tk.LabelFrame(workspace, text="  Correction Form  ",
                                    bg=COLORS["card_bg"], font=FONTS["heading"],
                                    fg=COLORS["text_primary"], bd=1, relief="groove")
        form_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)
        form_frame.columnconfigure(1, weight=1)

        field_defs = [
            ("Document ID",   "doc_id",        False),
            ("Document Type", "doc_type",       False),
            ("Barcode Value", "barcode",        True),
            ("Student Name",  "student_name",   False),
            ("Exam ID",       "exam_id",        False),
        ]

        self._form_vars: dict = {}
        for row_idx, (lbl, key, editable) in enumerate(field_defs):
            tk.Label(form_frame, text=lbl, bg=COLORS["card_bg"],
                     font=FONTS["body"], fg=COLORS["text_secondary"]).grid(
                         row=row_idx, column=0, sticky="w", padx=12, pady=5)
            var = tk.StringVar()
            self._form_vars[key] = var
            state = "normal" if editable else "readonly"
            ttk.Entry(form_frame, textvariable=var, state=state, width=28).grid(
                row=row_idx, column=1, sticky="ew", padx=12, pady=5)

        # Detected result
        tk.Label(form_frame, text="Detected Score / Result", bg=COLORS["card_bg"],
                 font=FONTS["heading"], fg=COLORS["text_primary"]).grid(
                     row=len(field_defs), column=0, columnspan=2, sticky="w", padx=12, pady=(12, 4))
        self._result_text = tk.Text(form_frame, height=6, font=FONTS["mono"],
                                     bg="#F9FAFB", fg=COLORS["text_primary"], relief="flat")
        self._result_text.grid(row=len(field_defs)+1, column=0, columnspan=2,
                                sticky="ew", padx=12, pady=4)
        self._result_text.config(state="disabled")

        # Manual score override
        tk.Label(form_frame, text="Override Score (optional):", bg=COLORS["card_bg"],
                 font=FONTS["body"], fg=COLORS["text_secondary"]).grid(
                     row=len(field_defs)+2, column=0, sticky="w", padx=12, pady=5)
        self._override_score_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self._override_score_var, width=12).grid(
            row=len(field_defs)+2, column=1, sticky="w", padx=12, pady=5)

        tk.Label(form_frame, text="Reason for correction:", bg=COLORS["card_bg"],
                 font=FONTS["body"], fg=COLORS["text_secondary"]).grid(
                     row=len(field_defs)+3, column=0, sticky="w", padx=12, pady=5)
        self._reason_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self._reason_var, width=28).grid(
            row=len(field_defs)+3, column=1, sticky="ew", padx=12, pady=5)

        # Buttons
        btn_frame = tk.Frame(form_frame, bg=COLORS["card_bg"])
        btn_frame.grid(row=len(field_defs)+4, column=0, columnspan=2,
                       sticky="ew", padx=12, pady=12)

        ttk.Button(btn_frame, text="✅ Confirm & Accept",
                   command=self._confirm_result, style="Success.TButton").pack(side="left", padx=4)
        ttk.Button(btn_frame, text="💾 Save Override",
                   command=self._save_override, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(btn_frame, text="❌ Reject",
                   command=self._reject_document, style="Danger.TButton").pack(side="right", padx=4)

        self._action_msg = tk.Label(form_frame, text="", bg=COLORS["card_bg"],
                                     font=FONTS["small"])
        self._action_msg.grid(row=len(field_defs)+5, column=0, columnspan=2,
                               sticky="w", padx=12)

    def refresh(self):
        self._doc_tree.delete(*self._doc_tree.get_children())
        docs = self.sm.results.get_documents_needing_review()
        for doc in docs:
            self._doc_tree.insert("", "end", iid=doc.document_id, values=(
                doc.document_id, doc.document_type,
                doc.barcode_value or "UNKNOWN",
                doc.warning_message or "",
                doc.processing_status
            ))

    def _on_doc_select(self, event=None):
        sel = self._doc_tree.selection()
        if not sel:
            return
        doc_id = sel[0]
        doc = self.sm.results.get_document(doc_id)
        if not doc:
            return
        self._current_doc = doc

        # Fill form
        self._form_vars["doc_id"].set(doc.document_id)
        self._form_vars["doc_type"].set(doc.document_type)
        self._form_vars["barcode"].set(doc.barcode_value or "")

        mapping = self.sm.barcodes.find_by_barcode(doc.barcode_value or "")
        if mapping:
            self._form_vars["student_name"].set(mapping.student_name)
            self._form_vars["exam_id"].set(mapping.exam_id)
        else:
            self._form_vars["student_name"].set("Unknown")
            self._form_vars["exam_id"].set("Unknown")

        # Load result
        result = self.sm.results.get_result_by_document(doc_id)
        self._current_result = result

        self._result_text.config(state="normal")
        self._result_text.delete("1.0", "end")
        if result:
            self._result_text.insert("end",
                f"Score: {result.score:.2f} / {result.maximum_score:.2f}\n"
                f"Type: {result.correction_type}\n"
                f"Status: {result.review_status}\n"
            )
            if result.override_reason:
                self._result_text.insert("end", f"Warning: {result.override_reason}\n")
        else:
            self._result_text.insert("end", "No result computed yet.\n")
        self._result_text.config(state="disabled")

        self._action_msg.config(text="")

        # Load image
        img_path = doc.processed_image_path or doc.original_image_path
        if img_path and Path(img_path).exists():
            self._load_image(img_path)

    def _load_image(self, path: str):
        try:
            img = cv2.imread(path)
            if img is None:
                return
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            # Fit to canvas
            canvas_w = max(self._canvas.winfo_width(), 380)
            canvas_h = max(self._canvas.winfo_height(), 480)
            pil_img.thumbnail((canvas_w, canvas_h), Image.LANCZOS)
            self._photo_ref = ImageTk.PhotoImage(pil_img)
            self._canvas.delete("all")
            self._canvas.create_image(canvas_w // 2, canvas_h // 2,
                                       image=self._photo_ref, anchor="center")
        except Exception as e:
            self._canvas.create_text(190, 240, text=f"Image load error:\n{e}",
                                      fill="red", font=FONTS["small"])

    def _confirm_result(self):
        if not self._current_result or not self._current_doc:
            messagebox.showwarning("No Selection", "Select a document from the list first.")
            return
        self._current_result.review_status = "Confirmed"
        self._current_result.override_reason = None
        self._current_doc.processing_status = "Processed"
        try:
            self.sm.results.save_result(self._current_result)
            self.sm.results.save_scanned_document(self._current_doc)
            self._action_msg.config(text="✅ Confirmed successfully", fg=COLORS["success"])
            self.refresh()
        except Exception as e:
            self._action_msg.config(text=f"❌ Error: {e}", fg=COLORS["danger"])

    def _save_override(self):
        if not self._current_result or not self._current_doc:
            messagebox.showwarning("No Selection", "Select a document first.")
            return
        try:
            override_val = self._override_score_var.get().strip()
            if override_val:
                self._current_result.score = float(override_val)
            reason = self._reason_var.get().strip()
            self._current_result.override_reason = reason or "Manual correction"
            self._current_result.manual_override = True
            self._current_result.review_status = "Confirmed"
            self._current_doc.processing_status = "Processed"
            self.sm.results.save_result(self._current_result)
            self.sm.results.save_scanned_document(self._current_doc)
            self._action_msg.config(text="✅ Override saved", fg=COLORS["success"])
            self.refresh()
        except ValueError:
            self._action_msg.config(text="❌ Invalid score value", fg=COLORS["danger"])
        except Exception as e:
            self._action_msg.config(text=f"❌ Error: {e}", fg=COLORS["danger"])

    def _reject_document(self):
        if not self._current_doc:
            return
        if messagebox.askyesno("Reject Document",
                                "Mark this document as rejected? The result will not be used."):
            self._current_doc.processing_status = "Failed"
            self.sm.results.save_scanned_document(self._current_doc)
            if self._current_result:
                self._current_result.review_status = "Rejected"
                self.sm.results.save_result(self._current_result)
            self._action_msg.config(text="Document rejected.", fg=COLORS["warning"])
            self.refresh()

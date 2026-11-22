"""
Master Excel Results Exporter.
Generates multi-sheet Excel reports per Section 13 of specifications.
"""
from pathlib import Path
from typing import Optional, List, Dict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from database.models import ExamResult, Student, Examination
from database.repositories import ServiceManager
from config.paths import EXPORTS_DIR, ensure_directories

class ExcelExporter:
    def __init__(self, service_manager: ServiceManager):
        self.sm = service_manager
        ensure_directories()

    def export_master_results(
        self,
        output_path: Optional[Path] = None,
        exam_id_filter: Optional[str] = None
    ) -> Path:
        """
        Exports the master examination results workbook.
        """
        if output_path is None:
            filename = f"Master_Results_{openpyxl.utils.datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            out_file = EXPORTS_DIR / filename
        else:
            out_file = Path(output_path)

        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        results = self.sm.results.get_all_results(exam_id=exam_id_filter)
        students = self.sm.students.get_all()
        exams = self.sm.exams.get_all()
        batches = self.sm.results.get_all_batches()

        # Styles
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        review_fill = PatternFill(start_color="F2DCDB", end_color="F2DCDB", fill_type="solid")
        border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9")
        )

        # -------------------------------------------------------------
        # 1. Sheet: Results
        # -------------------------------------------------------------
        ws_res = wb.create_sheet(title="Results")
        headers = [
            "Student ID", "Student Name", "Subject", "Exam ID",
            "Barcode", "Exam Type", "Score", "Maximum", "Status"
        ]
        ws_res.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws_res.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for r in results:
            row_data = [
                r.student_id,
                r.student_name,
                r.subject,
                r.exam_id,
                r.barcode_value,
                r.correction_type,
                round(r.score, 2),
                round(r.maximum_score, 2),
                r.review_status
            ]
            ws_res.append(row_data)
            current_row = ws_res.max_row
            # Format numeric score
            ws_res.cell(row=current_row, column=7).number_format = "0.00"
            ws_res.cell(row=current_row, column=8).number_format = "0.00"

            if r.review_status != "Confirmed":
                for col_idx in range(1, len(headers) + 1):
                    ws_res.cell(row=current_row, column=col_idx).fill = review_fill

        self._auto_fit_columns(ws_res)

        # -------------------------------------------------------------
        # 2. Sheet: Students
        # -------------------------------------------------------------
        ws_stu = wb.create_sheet(title="Students")
        s_headers = ["Student ID", "Student Name", "Registration Date"]
        ws_stu.append(s_headers)
        for col_idx in range(1, len(s_headers) + 1):
            cell = ws_stu.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill

        for s in students:
            ws_stu.append([s.student_id, s.student_name, s.created_at or ""])
        self._auto_fit_columns(ws_stu)

        # -------------------------------------------------------------
        # 3. Sheet: Examinations
        # -------------------------------------------------------------
        ws_ex = wb.create_sheet(title="Examinations")
        e_headers = ["Exam ID", "Subject", "Exam Name", "Exam Type", "Maximum Score", "Status"]
        ws_ex.append(e_headers)
        for col_idx in range(1, len(e_headers) + 1):
            cell = ws_ex.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill

        for ex in exams:
            ws_ex.append([ex.exam_id, ex.subject, ex.exam_name, ex.exam_type, ex.maximum_score, ex.status])
        self._auto_fit_columns(ws_ex)

        # -------------------------------------------------------------
        # 4. Sheet: Processing Summary
        # -------------------------------------------------------------
        ws_sum = wb.create_sheet(title="Processing Summary")
        b_headers = ["Batch ID", "Source File", "Total Pages", "Status", "Received At"]
        ws_sum.append(b_headers)
        for col_idx in range(1, len(b_headers) + 1):
            cell = ws_sum.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill

        for b in batches:
            ws_sum.append([b.batch_id, b.source_file, b.total_pages, b.status, b.received_at or ""])
        self._auto_fit_columns(ws_sum)

        # -------------------------------------------------------------
        # 5. Sheet: Review Required
        # -------------------------------------------------------------
        ws_rev = wb.create_sheet(title="Review Required")
        ws_rev.append(headers + ["Warning / Reason"])
        for col_idx in range(1, len(headers) + 2):
            cell = ws_rev.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")

        unconfirmed = [r for r in results if r.review_status != "Confirmed"]
        for r in unconfirmed:
            ws_rev.append([
                r.student_id,
                r.student_name,
                r.subject,
                r.exam_id,
                r.barcode_value,
                r.correction_type,
                round(r.score, 2),
                round(r.maximum_score, 2),
                r.review_status,
                r.override_reason or "Verification required"
            ])
        self._auto_fit_columns(ws_rev)

        out_file.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(out_file))
        return out_file

    def _auto_fit_columns(self, ws):
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

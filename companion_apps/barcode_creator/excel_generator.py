"""
Excel workbook generator for Student Barcode Creator.
"""
from pathlib import Path
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def generate_barcode_excel(
    output_path: Path,
    student_records: List[Dict[str, str]]
) -> Path:
    """
    Generates student-to-barcode mapping Excel file.
    Expected dict keys per record:
        student_name, subject, exam_id, barcode_id, full_barcode, student_id (optional)
    """
    out_file = Path(output_path)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Barcode Mappings"

    headers = ["Student Name", "Subject", "Exam ID", "Barcode ID", "Full Barcode", "Student ID", "Exam Type"]
    ws.append(headers)

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r in student_records:
        ws.append([
            r.get("student_name", ""),
            r.get("subject", ""),
            r.get("exam_id", ""),
            r.get("barcode_id", ""),
            r.get("full_barcode", ""),
            r.get("student_id", ""),
            r.get("exam_type", "QCM")
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_file))
    return out_file

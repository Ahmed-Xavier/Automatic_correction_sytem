"""
Excel schema validation utilities.
"""
from typing import List, Dict, Tuple, Optional, Any
import openpyxl

def normalize_header(header: Any) -> str:
    """Normalizes header string for robust matching."""
    if header is None:
        return ""
    return str(header).strip().lower().replace(" ", "_").replace("-", "_")

def find_column_index(headers: List[str], candidate_names: List[str]) -> Optional[int]:
    """Finds index of header matching any candidate name."""
    norm_candidates = [normalize_header(c) for c in candidate_names]
    for idx, h in enumerate(headers):
        if normalize_header(h) in norm_candidates:
            return idx
    return None

def validate_barcode_workbook(wb: openpyxl.Workbook) -> Tuple[bool, str, Dict[str, int]]:
    """
    Validates barcode mapping workbook.
    Expected columns: student name, subject, exam id, barcode id, full barcode (optional student id).
    """
    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return False, "Workbook is empty.", {}

    headers = [str(cell) if cell is not None else "" for cell in rows[0]]
    
    col_map = {
        "student_name": find_column_index(headers, ["student name", "student_name", "name", "nom", "student"]),
        "subject": find_column_index(headers, ["subject", "matiere", "course"]),
        "exam_id": find_column_index(headers, ["exam id", "exam_id", "code_examen", "exam"]),
        "barcode_id": find_column_index(headers, ["barcode id", "barcode_id", "id_barcode"]),
        "full_barcode": find_column_index(headers, ["full barcode", "full_barcode", "barcode", "barcode_value", "code_barre"]),
        "student_id": find_column_index(headers, ["student id", "student_id", "matricule", "id_student"]),
    }

    # Minimum required: full_barcode and student_name
    if col_map["full_barcode"] is None and col_map["barcode_id"] is None:
        return False, "Missing Barcode column in header.", {}
    if col_map["student_name"] is None:
        return False, "Missing Student Name column in header.", {}

    return True, "Valid barcode schema", col_map

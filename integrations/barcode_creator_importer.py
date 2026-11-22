"""
Importer for Barcode Creator Excel files.
"""
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import openpyxl
from database.models import BarcodeMapping
from database.barcode_repository import BarcodeRepository
from integrations.excel_schema_validator import validate_barcode_workbook

class BarcodeImporter:
    def __init__(self, repo: BarcodeRepository):
        self.repo = repo

    def import_file(self, file_path: Path) -> Tuple[int, List[str]]:
        """
        Imports student-barcode mappings from an Excel file.
        Returns (count_imported, list_of_warnings).
        """
        path = Path(file_path)
        if not path.exists():
            return 0, [f"File not found: {path}"]

        try:
            wb = openpyxl.load_workbook(path, data_only=True)
        except Exception as e:
            return 0, [f"Failed to open Excel file {path.name}: {str(e)}"]

        is_valid, msg, col_map = validate_barcode_workbook(wb)
        if not is_valid:
            return 0, [f"Invalid format in {path.name}: {msg}"]

        sheet = wb.active
        rows = list(sheet.iter_rows(values_only=True))[1:]  # skip header
        imported_count = 0
        warnings = []

        seen_barcodes = set()

        for row_idx, row in enumerate(rows, start=2):
            # Check empty row
            if not any(row):
                continue

            def get_val(key):
                idx = col_map.get(key)
                if idx is not None and idx < len(row):
                    v = row[idx]
                    return str(v).strip() if v is not None else ""
                return ""

            student_name = get_val("student_name")
            subject = get_val("subject") or "General"
            exam_id = get_val("exam_id") or f"{subject.upper()}-EXAM"
            exam_type = get_val("exam_type") or "QCM"
            if exam_type not in {"QCM", "Written"}:
                exam_type = "QCM"
            barcode_id = get_val("barcode_id")
            full_barcode = get_val("full_barcode") or barcode_id
            student_id = get_val("student_id")

            if not full_barcode:
                warnings.append(f"Row {row_idx}: Missing barcode value, skipping.")
                continue

            if not student_name:
                warnings.append(f"Row {row_idx}: Missing student name for barcode {full_barcode}, skipping.")
                continue

            # Generate stable student_id if missing (e.g. STU-<name_clean>)
            if not student_id:
                clean_name = "".join(c for c in student_name if c.isalnum()).upper()
                student_id = f"STU-{clean_name[:12]}"

            if full_barcode in seen_barcodes:
                warnings.append(f"Row {row_idx}: Duplicate barcode '{full_barcode}' in same file.")
                continue
            seen_barcodes.add(full_barcode)

            mapping = BarcodeMapping(
                barcode_value=full_barcode,
                barcode_id=barcode_id or full_barcode,
                student_id=student_id,
                student_name=student_name,
                exam_id=exam_id,
                subject=subject,
                source_file=path.name,
                exam_type=exam_type,
            )

            try:
                self.repo.add_mapping(mapping)
                imported_count += 1
            except Exception as e:
                warnings.append(f"Row {row_idx}: Failed to save {full_barcode} - {str(e)}")

        return imported_count, warnings

    def import_directory(self, dir_path: Path) -> Tuple[int, List[str]]:
        path = Path(dir_path)
        if not path.is_dir():
            return 0, [f"Not a directory: {dir_path}"]

        total_imported = 0
        all_warnings = []
        for file in path.glob("*.xlsx"):
            count, warns = self.import_file(file)
            total_imported += count
            all_warnings.extend(warns)
        return total_imported, all_warnings

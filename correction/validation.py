"""
Validation layer for examination recognition and correction pipeline.
"""
from typing import Optional, Tuple, List
from database.models import ScannedDocument, BarcodeMapping, Examination, AnswerKey

class DocumentValidator:
    @staticmethod
    def validate_pre_correction(
        doc: ScannedDocument,
        barcode_value: Optional[str],
        mapping: Optional[BarcodeMapping],
        exam: Optional[Examination],
        answer_key: Optional[AnswerKey] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validates page status before saving final grades.
        Returns (is_valid_for_auto_confirm, list_of_warnings).
        """
        warnings = []

        if not barcode_value:
            warnings.append("Barcode unreadable or missing.")
            return False, warnings

        if not mapping:
            warnings.append(f"Unknown barcode '{barcode_value}' not found in student database.")
            return False, warnings

        if not exam:
            warnings.append(f"Examination '{mapping.exam_id}' is not registered.")
            return False, warnings

        if doc.document_type == "Unknown":
            warnings.append("Document classification failed (Unknown type).")
            return False, warnings

        if doc.document_type == "QCM" and not answer_key:
            warnings.append(f"Missing answer key for QCM exam '{mapping.exam_id}'.")
            return False, warnings

        return len(warnings) == 0, warnings

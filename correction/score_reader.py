"""
Non-QCM Score Sheet Result Formatter.
"""
from typing import Optional, Tuple, Dict, Any
from database.models import ExamResult, ScannedDocument, BarcodeMapping
from database.repositories import ExamRepository

class ScoreReader:
    def __init__(self, exam_repo: ExamRepository):
        self.exam_repo = exam_repo

    def process(
        self,
        doc: ScannedDocument,
        mapping: BarcodeMapping,
        score_detection: Dict[str, Any]
    ) -> Tuple[Optional[ExamResult], bool, Optional[str]]:
        """
        Creates an ExamResult from score sheet detection.
        Returns (ExamResult, needs_review, warning_message).
        """
        exam = self.exam_repo.get(mapping.exam_id)
        max_score = exam.maximum_score if exam else 20.0

        score = score_detection.get("score")
        needs_review = score_detection.get("needs_review", False)
        warning = score_detection.get("warning")

        if score is None:
            needs_review = True
            final_score = 0.0
            review_status = "Pending Review"
            warning = warning or "Could not reconstruct complete numeric score"
        else:
            final_score = float(score)
            review_status = "Pending Review" if needs_review else "Confirmed"

        result = ExamResult(
            result_id=None,
            document_id=doc.document_id,
            student_id=mapping.student_id,
            student_name=mapping.student_name,
            exam_id=mapping.exam_id,
            subject=mapping.subject,
            barcode_value=mapping.barcode_value,
            score=final_score,
            maximum_score=max_score,
            correction_type="Written",
            answer_key_version=None,
            review_status=review_status,
            question_results=None,
            manual_override=False,
            override_reason=None
        )

        return result, needs_review, warning

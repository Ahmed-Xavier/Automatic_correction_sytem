"""
QCM Examination Corrector.
"""
from typing import Optional, Tuple, Dict, Any, List
from database.models import ExamResult, ScannedDocument, BarcodeMapping, AnswerKey
from database.answer_key_repository import AnswerKeyRepository
from database.repositories import ExamRepository
from correction.grading_rules import GradingEngine

class QCMCorrector:
    def __init__(self, key_repo: AnswerKeyRepository, exam_repo: ExamRepository):
        self.key_repo = key_repo
        self.exam_repo = exam_repo

    def correct(
        self,
        doc: ScannedDocument,
        mapping: BarcodeMapping,
        detection_result: Dict[str, Any]
    ) -> Tuple[Optional[ExamResult], bool, Optional[str]]:
        """
        Corrects a QCM document using its barcode mapping and latest answer key.
        Returns (ExamResult, needs_review, warning_message).
        """
        exam = self.exam_repo.get(mapping.exam_id)
        max_score = exam.maximum_score if exam else 20.0

        key = self.key_repo.get_latest_key(mapping.exam_id)
        if not key:
            return None, True, f"No answer key found for exam '{mapping.exam_id}'"

        questions = detection_result.get("questions", {})
        has_uncertain = detection_result.get("has_uncertain", False)

        score, q_results = GradingEngine.calculate_qcm_grade(
            detected_answers=questions,
            answer_key=key,
            maximum_score=max_score
        )

        review_status = "Pending Review" if has_uncertain else "Confirmed"
        warning = "Contains ambiguous or multiple bubble marks" if has_uncertain else None

        result = ExamResult(
            result_id=None,
            document_id=doc.document_id,
            student_id=mapping.student_id,
            student_name=mapping.student_name,
            exam_id=mapping.exam_id,
            subject=mapping.subject,
            barcode_value=mapping.barcode_value,
            score=score,
            maximum_score=max_score,
            correction_type="QCM",
            answer_key_version=key.version,
            review_status=review_status,
            question_results=q_results,
            manual_override=False,
            override_reason=None
        )

        return result, has_uncertain, warning

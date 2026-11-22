"""
End-to-End Batch Processor for mixed document batches.
Coordinates ingestion, barcode decoding, alignment, classification,
bubble evaluation, scoring, validation, and storage.
"""
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np

from database.models import ScanBatch, ScannedDocument, ExamResult
from database.repositories import ServiceManager
from scanner.file_ingestion import FileIngestion
from scanner.image_preprocessor import estimate_and_deskew
from recognition.barcode_reader import BarcodeReader
from recognition.image_alignment import ImageAligner
from recognition.document_classifier import DocumentClassifier
from recognition.qcm_detector import QCMDetector
from recognition.score_detector import ScoreDetector
from correction.qcm_corrector import QCMCorrector
from correction.score_reader import ScoreReader
from correction.validation import DocumentValidator
from config.paths import PROCESSED_DIR, ensure_directories

class BatchProcessor:
    def __init__(self, service_manager: ServiceManager, dpi: float = 300.0):
        self.sm = service_manager
        self.dpi = dpi
        ensure_directories()
        self.annotated_dir = PROCESSED_DIR / "annotated"
        self.annotated_dir.mkdir(parents=True, exist_ok=True)

        self.ingestion = FileIngestion(self.sm.results)
        self.barcode_reader = BarcodeReader()
        self.aligner = ImageAligner(dpi=dpi)
        self.classifier = DocumentClassifier(dpi=dpi)
        self.qcm_detector = QCMDetector(dpi=dpi)
        self.score_detector = ScoreDetector(dpi=dpi)
        self.qcm_corrector = QCMCorrector(self.sm.answer_keys, self.sm.exams)
        self.score_reader = ScoreReader(self.sm.exams)

    def process_file(self, file_path: Path) -> Tuple[ScanBatch, List[ExamResult]]:
        """Processes a single file (which may contain multiple pages)."""
        batch, extracted_docs = self.ingestion.ingest_file(file_path)
        batch_results: List[ExamResult] = []

        has_failures = False
        for doc, raw_img in extracted_docs:
            res = self.process_page(doc, raw_img)
            if res:
                batch_results.append(res)
            else:
                has_failures = True

        status = "Completed" if not has_failures else "Completed with Warnings"
        self.sm.results.update_batch_status(batch.batch_id, status)
        batch.status = status
        return batch, batch_results

    def process_page(self, doc: ScannedDocument, raw_img: np.ndarray) -> Optional[ExamResult]:
        """Processes a single page from a batch."""
        # 1. Barcode reading (prior to or alongside alignment)
        barcode_val = self.barcode_reader.read_barcode(raw_img)
        doc.barcode_value = barcode_val

        # 2. Deskew and align to canonical coordinates
        deskewed_img, _ = estimate_and_deskew(raw_img)
        aligned_img, align_ok = self.aligner.align(deskewed_img)

        # Retry barcode reading on aligned image if first pass failed
        if not barcode_val:
            barcode_val = self.barcode_reader.read_barcode(aligned_img)
            doc.barcode_value = barcode_val

        # 3. Classify document
        doc_type, conf = self.classifier.classify(aligned_img)
        doc.document_type = doc_type

        # 4. Lookup student mapping from barcode
        mapping = self.sm.barcodes.find_by_barcode(barcode_val) if barcode_val else None
        exam = self.sm.exams.get(mapping.exam_id) if mapping else None
        answer_key = self.sm.answer_keys.get_latest_key(mapping.exam_id) if mapping else None

        # 5. Pre-validation
        valid_pre, pre_warnings = DocumentValidator.validate_pre_correction(
            doc, barcode_val, mapping, exam, answer_key
        )

        annotated_path = self.annotated_dir / f"{doc.document_id}_annotated.png"

        result = None
        needs_review = not valid_pre
        warning_msg = "; ".join(pre_warnings) if pre_warnings else None

        if doc_type == "QCM":
            qcm_res = self.qcm_detector.detect(aligned_img)
            cv2.imwrite(str(annotated_path), qcm_res["annotated_image"])
            doc.processed_image_path = str(annotated_path)

            if mapping and answer_key:
                result, q_review, q_warn = self.qcm_corrector.correct(doc, mapping, qcm_res)
                if q_review:
                    needs_review = True
                    warning_msg = f"{warning_msg}; {q_warn}" if warning_msg else q_warn
            else:
                needs_review = True
                warning_msg = warning_msg or "Cannot score QCM without valid mapping and answer key"

        elif doc_type == "Score Sheet":
            max_sc = exam.maximum_score if exam else 20.0
            score_res = self.score_detector.detect(aligned_img, max_score=max_sc)
            cv2.imwrite(str(annotated_path), score_res["annotated_image"])
            doc.processed_image_path = str(annotated_path)

            if mapping:
                result, s_review, s_warn = self.score_reader.process(doc, mapping, score_res)
                if s_review:
                    needs_review = True
                    warning_msg = f"{warning_msg}; {s_warn}" if warning_msg else s_warn
            else:
                needs_review = True
                warning_msg = warning_msg or "Cannot score Score Sheet without valid student mapping"

        else:
            # Unknown type
            cv2.imwrite(str(annotated_path), aligned_img)
            doc.processed_image_path = str(annotated_path)
            needs_review = True
            warning_msg = warning_msg or "Unknown document type cannot be scored automatically"

        # Update document status in DB
        doc.processing_status = "Needs Review" if needs_review else "Processed"
        doc.warning_message = warning_msg
        self.sm.results.save_scanned_document(doc)

        # Save result if created
        if result:
            result.review_status = "Pending Review" if needs_review else "Confirmed"
            result.override_reason = warning_msg if needs_review else None
            self.sm.results.save_result(result)

        return result

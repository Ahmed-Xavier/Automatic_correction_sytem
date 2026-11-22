"""
Repository for Exam Results, Batches, and Scanned Documents.
"""
import json
import sqlite3
from typing import List, Optional, Dict, Any
from database.models import (
    ScanBatch, ScannedDocument, ExamResult, QuestionResult
)
from database.database import Database

class ResultRepository:
    def __init__(self, db: Database):
        self.db = db
        # Older databases only had a per-document uniqueness rule. Migrate
        # existing duplicates before enforcing one result per student/exam.
        with self.db.get_connection() as conn:
            conn.execute(
                """DELETE FROM results
                   WHERE result_id NOT IN (
                       SELECT MIN(result_id) FROM results GROUP BY student_id, exam_id
                   )"""
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_results_student_exam "
                "ON results(student_id, exam_id)"
            )
            conn.commit()

    def clear_scan_data(self) -> Dict[str, int]:
        """Delete scan history and results while preserving exam catalog data."""
        tables = ("results", "scanned_documents", "scan_batches", "audit_logs")
        with self.db.get_connection() as conn:
            deleted = {
                table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in tables
            }
            for table in tables:
                conn.execute(f"DELETE FROM {table}")
            conn.commit()
        return deleted

    # Batches
    def create_batch(self, batch: ScanBatch):
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT INTO scan_batches (batch_id, source_file, total_pages, status) VALUES (?, ?, ?, ?)
                   ON CONFLICT(batch_id) DO UPDATE SET source_file=excluded.source_file,
                     total_pages=excluded.total_pages, status=excluded.status""",
                (batch.batch_id, batch.source_file, batch.total_pages, batch.status)
            )
            conn.commit()

    def update_batch_status(self, batch_id: str, status: str):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE scan_batches SET status = ? WHERE batch_id = ?",
                (status, batch_id)
            )
            conn.commit()

    def get_batch(self, batch_id: str) -> Optional[ScanBatch]:
        with self.db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM scan_batches WHERE batch_id = ?", (batch_id,))
            row = cur.fetchone()
            if row:
                return ScanBatch(
                    batch_id=row["batch_id"],
                    source_file=row["source_file"],
                    total_pages=row["total_pages"],
                    status=row["status"],
                    received_at=row["received_at"],
                )
            return None

    def get_all_batches(self) -> List[ScanBatch]:
        with self.db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM scan_batches ORDER BY received_at DESC")
            return [
                ScanBatch(
                    batch_id=row["batch_id"],
                    source_file=row["source_file"],
                    total_pages=row["total_pages"],
                    status=row["status"],
                    received_at=row["received_at"],
                )
                for row in cur.fetchall()
            ]

    # Documents
    def save_scanned_document(self, doc: ScannedDocument):
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT INTO scanned_documents
                   (document_id, batch_id, page_number, document_type, barcode_value, processing_status, original_image_path, processed_image_path, warning_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(document_id) DO UPDATE SET batch_id=excluded.batch_id,
                     page_number=excluded.page_number, document_type=excluded.document_type,
                     barcode_value=excluded.barcode_value, processing_status=excluded.processing_status,
                     original_image_path=excluded.original_image_path,
                     processed_image_path=excluded.processed_image_path,
                     warning_message=excluded.warning_message""",
                (doc.document_id, doc.batch_id, doc.page_number, doc.document_type,
                 doc.barcode_value, doc.processing_status, doc.original_image_path,
                 doc.processed_image_path, doc.warning_message)
            )
            conn.commit()

    def get_document(self, document_id: str) -> Optional[ScannedDocument]:
        with self.db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM scanned_documents WHERE document_id = ?", (document_id,))
            row = cur.fetchone()
            if row:
                return ScannedDocument(
                    document_id=row["document_id"],
                    batch_id=row["batch_id"],
                    page_number=row["page_number"],
                    document_type=row["document_type"],
                    barcode_value=row["barcode_value"],
                    processing_status=row["processing_status"],
                    original_image_path=row["original_image_path"],
                    processed_image_path=row["processed_image_path"],
                    warning_message=row["warning_message"],
                    created_at=row["created_at"],
                )
            return None

    def get_documents_needing_review(self) -> List[ScannedDocument]:
        with self.db.get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM scanned_documents WHERE processing_status = 'Needs Review' ORDER BY created_at DESC"
            )
            return [
                ScannedDocument(
                    document_id=row["document_id"],
                    batch_id=row["batch_id"],
                    page_number=row["page_number"],
                    document_type=row["document_type"],
                    barcode_value=row["barcode_value"],
                    processing_status=row["processing_status"],
                    original_image_path=row["original_image_path"],
                    processed_image_path=row["processed_image_path"],
                    warning_message=row["warning_message"],
                    created_at=row["created_at"],
                )
                for row in cur.fetchall()
            ]

    # Results
    def save_result(self, res: ExamResult) -> int:
        q_json = None
        if res.question_results:
            q_list = [
                {
                    "q": q.question_number,
                    "ans": q.detected_answer,
                    "correct": q.correct_answer,
                    "pts": q.points_awarded,
                    "status": q.status,
                }
                for q in res.question_results
            ]
            q_json = json.dumps(q_list)

        with self.db.get_connection() as conn:
            existing = conn.execute(
                "SELECT result_id, document_id FROM results WHERE student_id = ? AND exam_id = ?",
                (res.student_id, res.exam_id),
            ).fetchone()
            if existing and existing["document_id"] != res.document_id:
                raise ValueError(
                    f"A result already exists for student {res.student_id} "
                    f"in exam {res.exam_id} (document {existing['document_id']}). "
                    "Reject or remove the existing result before accepting this scan."
                )

            cur = conn.execute(
                """INSERT INTO results
                   (document_id, student_id, student_name, exam_id, subject, barcode_value, score, maximum_score,
                    correction_type, answer_key_version, review_status, question_results_json, manual_override, override_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(document_id) DO UPDATE SET
                     student_id=excluded.student_id, student_name=excluded.student_name,
                     exam_id=excluded.exam_id, subject=excluded.subject,
                     barcode_value=excluded.barcode_value, score=excluded.score,
                     maximum_score=excluded.maximum_score, correction_type=excluded.correction_type,
                     answer_key_version=excluded.answer_key_version,
                     review_status=excluded.review_status,
                     question_results_json=excluded.question_results_json,
                     manual_override=excluded.manual_override, override_reason=excluded.override_reason""",
                (res.document_id, res.student_id, res.student_name, res.exam_id, res.subject,
                 res.barcode_value, res.score, res.maximum_score, res.correction_type,
                 res.answer_key_version, res.review_status, q_json,
                 1 if res.manual_override else 0, res.override_reason)
            )
            conn.commit()
            return cur.lastrowid

    def get_result_by_document(self, document_id: str) -> Optional[ExamResult]:
        with self.db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM results WHERE document_id = ?", (document_id,))
            row = cur.fetchone()
            if row:
                return self._row_to_result(row)
            return None

    def get_all_results(self, exam_id: Optional[str] = None, status: Optional[str] = None) -> List[ExamResult]:
        query = "SELECT * FROM results WHERE 1=1"
        params = []
        if exam_id:
            query += " AND exam_id = ?"
            params.append(exam_id)
        if status:
            query += " AND review_status = ?"
            params.append(status)
        query += " ORDER BY student_name, exam_id"

        with self.db.get_connection() as conn:
            cur = conn.execute(query, params)
            return [self._row_to_result(r) for r in cur.fetchall()]

    def count_results(self, status: Optional[str] = None) -> int:
        query = "SELECT COUNT(*) FROM results"
        params = []
        if status:
            query += " WHERE review_status = ?"
            params.append(status)
        with self.db.get_connection() as conn:
            return conn.execute(query, params).fetchone()[0]

    def _row_to_result(self, row: sqlite3.Row) -> ExamResult:
        q_results = None
        if row["question_results_json"]:
            raw = json.loads(row["question_results_json"])
            q_results = [
                QuestionResult(
                    question_number=item["q"],
                    detected_answer=item.get("ans"),
                    correct_answer=item.get("correct"),
                    points_awarded=item.get("pts", 0.0),
                    status=item.get("status", "Unknown")
                )
                for item in raw
            ]
        return ExamResult(
            result_id=row["result_id"],
            document_id=row["document_id"],
            student_id=row["student_id"],
            student_name=row["student_name"],
            exam_id=row["exam_id"],
            subject=row["subject"],
            barcode_value=row["barcode_value"],
            score=row["score"],
            maximum_score=row["maximum_score"],
            correction_type=row["correction_type"],
            answer_key_version=row["answer_key_version"],
            review_status=row["review_status"],
            question_results=q_results,
            manual_override=bool(row["manual_override"]),
            override_reason=row["override_reason"],
            processed_at=row["processed_at"],
        )

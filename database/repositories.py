"""
Consolidated repositories and Examination/Student operations.
"""
from typing import List, Optional, Dict, Any
import sqlite3
from database.database import Database
from database.models import Examination, Student
from database.barcode_repository import BarcodeRepository
from database.answer_key_repository import AnswerKeyRepository
from database.result_repository import ResultRepository

class ExamRepository:
    def __init__(self, db: Database):
        self.db = db

    def create_or_update(self, exam: Examination) -> bool:
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO examinations
                   (exam_id, subject, exam_name, exam_type, maximum_score, exam_date, num_questions, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (exam.exam_id, exam.subject, exam.exam_name, exam.exam_type,
                 exam.maximum_score, exam.exam_date, exam.num_questions, exam.status)
            )
            conn.commit()
            return True

    def get(self, exam_id: str) -> Optional[Examination]:
        with self.db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM examinations WHERE exam_id = ?", (exam_id,))
            row = cur.fetchone()
            if row:
                return Examination(
                    exam_id=row["exam_id"],
                    subject=row["subject"],
                    exam_name=row["exam_name"],
                    exam_type=row["exam_type"],
                    maximum_score=row["maximum_score"],
                    exam_date=row["exam_date"],
                    num_questions=row["num_questions"],
                    status=row["status"],
                    created_at=row["created_at"],
                )
            return None

    def get_all(self, status: Optional[str] = None) -> List[Examination]:
        query = "SELECT * FROM examinations"
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY subject, exam_name"

        with self.db.get_connection() as conn:
            cur = conn.execute(query, params)
            return [
                Examination(
                    exam_id=row["exam_id"],
                    subject=row["subject"],
                    exam_name=row["exam_name"],
                    exam_type=row["exam_type"],
                    maximum_score=row["maximum_score"],
                    exam_date=row["exam_date"],
                    num_questions=row["num_questions"],
                    status=row["status"],
                    created_at=row["created_at"],
                )
                for row in cur.fetchall()
            ]

    def count(self) -> int:
        with self.db.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM examinations").fetchone()[0]


class StudentRepository:
    def __init__(self, db: Database):
        self.db = db

    def count(self) -> int:
        with self.db.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    def get_all(self) -> List[Student]:
        with self.db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM students ORDER BY student_name")
            return [
                Student(
                    student_id=row["student_id"],
                    student_name=row["student_name"],
                    created_at=row["created_at"],
                )
                for row in cur.fetchall()
            ]


class ServiceManager:
    """Convenience facade grouping all repositories."""
    def __init__(self, db: Optional[Database] = None):
        self.db = db if db else Database()
        self.exams = ExamRepository(self.db)
        self.students = StudentRepository(self.db)
        self.barcodes = BarcodeRepository(self.db)
        self.answer_keys = AnswerKeyRepository(self.db)
        self.results = ResultRepository(self.db)

    def get_dashboard_stats(self) -> Dict[str, Any]:
        return {
            "total_exams": self.exams.count(),
            "total_students": self.students.count(),
            "total_barcodes": self.barcodes.count(),
            "total_answer_keys": self.answer_keys.count(),
            "total_results": self.results.count_results(),
            "confirmed_results": self.results.count_results(status="Confirmed"),
            "pending_review": self.results.count_results(status="Pending Review"),
            "batches_count": len(self.results.get_all_batches()),
        }

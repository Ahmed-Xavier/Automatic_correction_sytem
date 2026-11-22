"""
Repository for student barcode mappings.
"""
import sqlite3
from typing import List, Optional, Dict
from database.models import BarcodeMapping, Student
from database.database import Database

class BarcodeRepository:
    def __init__(self, db: Database):
        self.db = db

    def add_mapping(self, mapping: BarcodeMapping) -> bool:
        """Inserts or updates student and barcode mapping."""
        with self.db.get_connection() as conn:
            # Insert student if not exists
            conn.execute(
                "INSERT OR IGNORE INTO students (student_id, student_name) VALUES (?, ?)",
                (mapping.student_id, mapping.student_name)
            )
            # Ensure exam exists (or insert minimal placeholder if exam is not registered yet)
            conn.execute(
                "INSERT OR IGNORE INTO examinations (exam_id, subject, exam_name, exam_type, maximum_score) "
                "VALUES (?, ?, ?, ?, 20.0)",
                (mapping.exam_id, mapping.subject,
                 f"{mapping.subject} Exam ({mapping.exam_id})", mapping.exam_type)
            )
            # Insert or replace barcode mapping
            conn.execute(
                """INSERT OR REPLACE INTO barcode_mappings 
                   (barcode_value, barcode_id, student_id, student_name, exam_id, subject, source_file)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (mapping.barcode_value, mapping.barcode_id, mapping.student_id,
                 mapping.student_name, mapping.exam_id, mapping.subject, mapping.source_file)
            )
            conn.commit()
            return True

    def find_by_barcode(self, barcode_value: str) -> Optional[BarcodeMapping]:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM barcode_mappings WHERE barcode_value = ?",
                (barcode_value,)
            )
            row = cursor.fetchone()
            if row:
                return BarcodeMapping(
                    barcode_value=row["barcode_value"],
                    barcode_id=row["barcode_id"],
                    student_id=row["student_id"],
                    student_name=row["student_name"],
                    exam_id=row["exam_id"],
                    subject=row["subject"],
                    source_file=row["source_file"],
                    created_at=row["created_at"],
                )
            return None

    def get_all(self, search: str = "") -> List[BarcodeMapping]:
        with self.db.get_connection() as conn:
            if search:
                term = f"%{search}%"
                cursor = conn.execute(
                    """SELECT * FROM barcode_mappings 
                       WHERE barcode_value LIKE ? OR student_name LIKE ? OR student_id LIKE ? OR exam_id LIKE ?
                       ORDER BY student_name""",
                    (term, term, term, term)
                )
            else:
                cursor = conn.execute("SELECT * FROM barcode_mappings ORDER BY student_name")
            
            return [
                BarcodeMapping(
                    barcode_value=row["barcode_value"],
                    barcode_id=row["barcode_id"],
                    student_id=row["student_id"],
                    student_name=row["student_name"],
                    exam_id=row["exam_id"],
                    subject=row["subject"],
                    source_file=row["source_file"],
                    created_at=row["created_at"],
                )
                for row in cursor.fetchall()
            ]

    def count(self) -> int:
        with self.db.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM barcode_mappings").fetchone()[0]

"""
Repository for Answer Keys and Grading Configurations.
"""
import json
import sqlite3
from typing import List, Optional, Dict
from database.models import AnswerKey, AnswerKeyItem
from database.database import Database

class AnswerKeyRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_answer_key(self, key: AnswerKey) -> int:
        """Saves a new answer key version."""
        answers_dict = [
            {"q": item.question_number, "ans": item.correct_answer, "pts": item.points}
            for item in key.answers
        ]
        answers_json = json.dumps(answers_dict)

        with self.db.get_connection() as conn:
            # Check highest version for exam
            cur = conn.execute(
                "SELECT MAX(version) FROM answer_keys WHERE exam_id = ?",
                (key.exam_id,)
            )
            max_v = cur.fetchone()[0]
            if max_v is not None and key.version <= max_v:
                version = max_v + 1
            else:
                version = key.version if key.version > 0 else 1

            cursor = conn.execute(
                """INSERT INTO answer_keys 
                   (exam_id, version, answers_json, correct_points, incorrect_points, unanswered_points, source_file, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (key.exam_id, version, answers_json, key.correct_points,
                 key.incorrect_points, key.unanswered_points, key.source_file, key.status)
            )
            conn.commit()
            return cursor.lastrowid

    def get_latest_key(self, exam_id: str) -> Optional[AnswerKey]:
        with self.db.get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM answer_keys WHERE exam_id = ? ORDER BY version DESC LIMIT 1",
                (exam_id,)
            )
            row = cur.fetchone()
            if row:
                return self._row_to_model(row)
            return None

    def get_by_version(self, exam_id: str, version: int) -> Optional[AnswerKey]:
        with self.db.get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM answer_keys WHERE exam_id = ? AND version = ?",
                (exam_id, version)
            )
            row = cur.fetchone()
            if row:
                return self._row_to_model(row)
            return None

    def get_all(self) -> List[AnswerKey]:
        with self.db.get_connection() as conn:
            cur = conn.execute("SELECT * FROM answer_keys ORDER BY exam_id, version DESC")
            return [self._row_to_model(r) for r in cur.fetchall()]

    def count(self) -> int:
        with self.db.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM answer_keys").fetchone()[0]

    def _row_to_model(self, row: sqlite3.Row) -> AnswerKey:
        data = json.loads(row["answers_json"])
        items = [
            AnswerKeyItem(
                question_number=d["q"],
                correct_answer=d["ans"],
                points=d.get("pts", row["correct_points"])
            )
            for d in data
        ]
        return AnswerKey(
            answer_key_id=row["answer_key_id"],
            exam_id=row["exam_id"],
            version=row["version"],
            answers=items,
            correct_points=row["correct_points"],
            incorrect_points=row["incorrect_points"],
            unanswered_points=row["unanswered_points"],
            source_file=row["source_file"],
            status=row["status"],
            created_at=row["created_at"],
        )

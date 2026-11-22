"""
Database initialization, schema management, and connection helpers.
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional
from config.paths import DEFAULT_DB_PATH, ensure_directories

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    student_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS examinations (
    exam_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    exam_name TEXT NOT NULL,
    exam_type TEXT NOT NULL CHECK(exam_type IN ('QCM', 'Written')),
    maximum_score REAL NOT NULL DEFAULT 20.0,
    exam_date TEXT,
    num_questions INTEGER DEFAULT 40,
    status TEXT DEFAULT 'Active' CHECK(status IN ('Draft', 'Active', 'Archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS barcode_mappings (
    barcode_value TEXT PRIMARY KEY,
    barcode_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    student_name TEXT NOT NULL,
    exam_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY(exam_id) REFERENCES examinations(exam_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_barcode_exam ON barcode_mappings(exam_id);
CREATE INDEX IF NOT EXISTS idx_barcode_student ON barcode_mappings(student_id);

CREATE TABLE IF NOT EXISTS answer_keys (
    answer_key_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    answers_json TEXT NOT NULL,
    correct_points REAL NOT NULL DEFAULT 0.5,
    incorrect_points REAL NOT NULL DEFAULT 0.0,
    unanswered_points REAL NOT NULL DEFAULT 0.0,
    source_file TEXT,
    status TEXT DEFAULT 'Published' CHECK(status IN ('Draft', 'Published', 'Archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, version),
    FOREIGN KEY(exam_id) REFERENCES examinations(exam_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_answer_keys_exam ON answer_keys(exam_id);

CREATE TABLE IF NOT EXISTS scan_batches (
    batch_id TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    total_pages INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Processing', 'Completed', 'Failed')),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scanned_documents (
    document_id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    document_type TEXT NOT NULL CHECK(document_type IN ('QCM', 'Score Sheet', 'Unknown')),
    barcode_value TEXT,
    processing_status TEXT DEFAULT 'Pending' CHECK(processing_status IN ('Pending', 'Processed', 'Needs Review', 'Failed')),
    original_image_path TEXT,
    processed_image_path TEXT,
    warning_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(batch_id) REFERENCES scan_batches(batch_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scanned_docs_batch ON scanned_documents(batch_id);
CREATE INDEX IF NOT EXISTS idx_scanned_docs_barcode ON scanned_documents(barcode_value);

CREATE TABLE IF NOT EXISTS results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL UNIQUE,
    student_id TEXT NOT NULL,
    student_name TEXT NOT NULL,
    exam_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    barcode_value TEXT NOT NULL,
    score REAL NOT NULL,
    maximum_score REAL NOT NULL,
    correction_type TEXT NOT NULL CHECK(correction_type IN ('QCM', 'Written')),
    answer_key_version INTEGER,
    review_status TEXT DEFAULT 'Confirmed' CHECK(review_status IN ('Confirmed', 'Pending Review', 'Rejected')),
    question_results_json TEXT,
    manual_override INTEGER DEFAULT 0,
    override_reason TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES scanned_documents(document_id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY(exam_id) REFERENCES examinations(exam_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_results_student ON results(student_id);
CREATE INDEX IF NOT EXISTS idx_results_exam ON results(exam_id);
CREATE INDEX IF NOT EXISTS idx_results_status ON results(review_status);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    details TEXT,
    performed_by TEXT DEFAULT 'System',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

class Database:
    def __init__(self, db_path: Optional[Path] = None):
        ensure_directories()
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Initializes tables and indices."""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def log_audit(self, action: str, entity_type: str, entity_id: str, details: str = "", performed_by: str = "System"):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO audit_logs (action, entity_type, entity_id, details, performed_by) VALUES (?, ?, ?, ?, ?)",
                (action, entity_type, entity_id, details, performed_by)
            )
            conn.commit()

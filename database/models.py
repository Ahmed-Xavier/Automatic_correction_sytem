"""
Data models for the Examination Correction System.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Student:
    student_id: str
    student_name: str
    created_at: Optional[str] = None

@dataclass
class Examination:
    exam_id: str
    subject: str
    exam_name: str
    exam_type: str  # 'QCM' or 'Written'
    maximum_score: float = 20.0
    exam_date: Optional[str] = None
    num_questions: int = 40
    status: str = "Active"  # 'Draft', 'Active', 'Archived'
    created_at: Optional[str] = None

@dataclass
class BarcodeMapping:
    barcode_value: str
    barcode_id: str
    student_id: str
    student_name: str
    exam_id: str
    subject: str
    source_file: str
    created_at: Optional[str] = None

@dataclass
class AnswerKeyItem:
    question_number: int
    correct_answer: str
    points: float = 0.5

@dataclass
class AnswerKey:
    answer_key_id: Optional[int]
    exam_id: str
    version: int
    answers: List[AnswerKeyItem]
    correct_points: float = 0.5
    incorrect_points: float = 0.0
    unanswered_points: float = 0.0
    source_file: str = ""
    status: str = "Published"  # 'Draft', 'Published', 'Archived'
    created_at: Optional[str] = None

@dataclass
class ScanBatch:
    batch_id: str
    source_file: str
    total_pages: int = 0
    status: str = "Pending"  # 'Pending', 'Processing', 'Completed', 'Failed'
    received_at: Optional[str] = None

@dataclass
class ScannedDocument:
    document_id: str
    batch_id: str
    page_number: int
    document_type: str  # 'QCM', 'Score Sheet', 'Unknown'
    barcode_value: Optional[str] = None
    processing_status: str = "Pending"  # 'Pending', 'Processed', 'Needs Review', 'Failed'
    original_image_path: Optional[str] = None
    processed_image_path: Optional[str] = None
    warning_message: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class QuestionResult:
    question_number: int
    detected_answer: Optional[str]
    correct_answer: Optional[str]
    points_awarded: float
    status: str  # 'Correct', 'Incorrect', 'Unanswered', 'Ambiguous'

@dataclass
class ExamResult:
    result_id: Optional[int]
    document_id: str
    student_id: str
    student_name: str
    exam_id: str
    subject: str
    barcode_value: str
    score: float
    maximum_score: float
    correction_type: str  # 'QCM' or 'Written'
    answer_key_version: Optional[int] = None
    review_status: str = "Confirmed"  # 'Confirmed', 'Pending Review', 'Rejected'
    question_results: Optional[List[QuestionResult]] = None
    manual_override: bool = False
    override_reason: Optional[str] = None
    processed_at: Optional[str] = None

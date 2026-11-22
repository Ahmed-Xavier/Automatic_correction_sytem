"""
Importer for Answer Key Manager Excel files.
"""
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import openpyxl
from database.models import AnswerKey, AnswerKeyItem, Examination
from database.answer_key_repository import AnswerKeyRepository
from database.repositories import ExamRepository
from integrations.excel_schema_validator import normalize_header, find_column_index

class AnswerKeyImporter:
    def __init__(self, key_repo: AnswerKeyRepository, exam_repo: Optional[ExamRepository] = None):
        self.key_repo = key_repo
        self.exam_repo = exam_repo

    def import_file(self, file_path: Path) -> Tuple[bool, str, Optional[AnswerKey]]:
        path = Path(file_path)
        if not path.exists():
            return False, f"File not found: {path}", None

        try:
            wb = openpyxl.load_workbook(path, data_only=True)
        except Exception as e:
            return False, f"Failed to open Excel workbook: {str(e)}", None

        # Detect sheets
        sheet_names = [s.lower() for s in wb.sheetnames]
        
        exam_id = ""
        subject = "General"
        exam_name = ""
        max_score = 20.0
        num_questions = 40
        version = 1

        correct_pts = 0.5
        incorrect_pts = 0.0
        unanswered_pts = 0.0

        items: List[AnswerKeyItem] = []

        # 1. Parse Sheet 1: Exam Info if present
        info_sheet = None
        for s in wb.sheetnames:
            if any(k in s.lower() for k in ["exam", "info", "general"]):
                info_sheet = wb[s]
                break

        if info_sheet:
            rows = list(info_sheet.iter_rows(values_only=True))
            if len(rows) > 1:
                headers = [str(c) if c is not None else "" for c in rows[0]]
                data_row = rows[1]
                idx_id = find_column_index(headers, ["exam id", "exam_id", "id"])
                idx_sub = find_column_index(headers, ["subject", "matiere"])
                idx_name = find_column_index(headers, ["exam name", "exam_name", "name"])
                idx_max = find_column_index(headers, ["maximum score", "max_score", "maximum"])
                idx_ver = find_column_index(headers, ["version", "key_version"])

                if idx_id is not None and idx_id < len(data_row) and data_row[idx_id]:
                    exam_id = str(data_row[idx_id]).strip()
                if idx_sub is not None and idx_sub < len(data_row) and data_row[idx_sub]:
                    subject = str(data_row[idx_sub]).strip()
                if idx_name is not None and idx_name < len(data_row) and data_row[idx_name]:
                    exam_name = str(data_row[idx_name]).strip()
                if idx_max is not None and idx_max < len(data_row) and data_row[idx_max] is not None:
                    try:
                        max_score = float(data_row[idx_max])
                    except ValueError:
                        pass
                if idx_ver is not None and idx_ver < len(data_row) and data_row[idx_ver] is not None:
                    try:
                        version = int(data_row[idx_ver])
                    except ValueError:
                        pass

        # 2. Parse Sheet 3: Grading Rules if present
        rules_sheet = None
        for s in wb.sheetnames:
            if any(k in s.lower() for k in ["rule", "grading", "bareme"]):
                rules_sheet = wb[s]
                break

        if rules_sheet:
            rows = list(rules_sheet.iter_rows(values_only=True))
            if len(rows) > 1:
                headers = [str(c) if c is not None else "" for c in rows[0]]
                data_row = rows[1]
                idx_corr = find_column_index(headers, ["correct points", "correct", "bonne"])
                idx_inc = find_column_index(headers, ["incorrect points", "incorrect", "penalty", "fausse"])
                idx_unans = find_column_index(headers, ["unanswered points", "unanswered", "vide"])

                if idx_corr is not None and idx_corr < len(data_row) and data_row[idx_corr] is not None:
                    try:
                        correct_pts = float(data_row[idx_corr])
                    except ValueError:
                        pass
                if idx_inc is not None and idx_inc < len(data_row) and data_row[idx_inc] is not None:
                    try:
                        incorrect_pts = float(data_row[idx_inc])
                    except ValueError:
                        pass
                if idx_unans is not None and idx_unans < len(data_row) and data_row[idx_unans] is not None:
                    try:
                        unanswered_pts = float(data_row[idx_unans])
                    except ValueError:
                        pass

        # 3. Parse Sheet 2: Answer Key questions
        key_sheet = None
        for s in wb.sheetnames:
            if any(k in s.lower() for k in ["answer", "key", "reponse", "corrig"]):
                key_sheet = wb[s]
                break
        if key_sheet is None:
            # Fall back to active sheet if not already used
            key_sheet = wb.active

        key_rows = list(key_sheet.iter_rows(values_only=True))
        if not key_rows:
            return False, "Answer key sheet is empty.", None

        headers = [str(c) if c is not None else "" for c in key_rows[0]]
        idx_q = find_column_index(headers, ["question number", "question", "q_num", "no", "no."])
        idx_ans = find_column_index(headers, ["correct answer", "answer", "correct", "reponse"])
        idx_pts = find_column_index(headers, ["points", "pts", "poids"])
        idx_eid = find_column_index(headers, ["exam id", "exam_id"])

        if idx_ans is None:
            return False, "Could not find 'Correct Answer' column in answer key sheet.", None

        for row_idx, row in enumerate(key_rows[1:], start=2):
            if not any(row):
                continue

            q_num = row_idx - 1  # default question number
            if idx_q is not None and idx_q < len(row) and row[idx_q] is not None:
                try:
                    q_num = int(row[idx_q])
                except ValueError:
                    pass

            ans = str(row[idx_ans]).strip().upper() if idx_ans < len(row) and row[idx_ans] is not None else ""
            if not ans:
                continue

            pts = correct_pts
            if idx_pts is not None and idx_pts < len(row) and row[idx_pts] is not None:
                try:
                    pts = float(row[idx_pts])
                except ValueError:
                    pass

            if not exam_id and idx_eid is not None and idx_eid < len(row) and row[idx_eid]:
                exam_id = str(row[idx_eid]).strip()

            items.append(AnswerKeyItem(question_number=q_num, correct_answer=ans, points=pts))

        if not items:
            return False, "No valid question-answer records found.", None

        if not exam_id:
            exam_id = path.stem.upper()

        if not exam_name:
            exam_name = f"{subject} Examination ({exam_id})"

        # Register or update Examination in DB
        if self.exam_repo:
            exam = Examination(
                exam_id=exam_id,
                subject=subject,
                exam_name=exam_name,
                exam_type="QCM",
                maximum_score=max_score,
                num_questions=len(items)
            )
            self.exam_repo.create_or_update(exam)

        key = AnswerKey(
            answer_key_id=None,
            exam_id=exam_id,
            version=version,
            answers=items,
            correct_points=correct_pts,
            incorrect_points=incorrect_pts,
            unanswered_points=unanswered_pts,
            source_file=path.name,
            status="Published"
        )

        try:
            saved_id = self.key_repo.save_answer_key(key)
            key.answer_key_id = saved_id
            return True, f"Successfully imported answer key for exam '{exam_id}' with {len(items)} questions.", key
        except Exception as e:
            return False, f"Failed to save answer key to database: {str(e)}", None

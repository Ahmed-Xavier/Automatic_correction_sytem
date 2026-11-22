"""
Grading rules and score calculation logic.
"""
from typing import Dict, List, Optional, Tuple
from database.models import AnswerKey, QuestionResult

class GradingEngine:
    @staticmethod
    def calculate_qcm_grade(
        detected_answers: Dict[int, Dict],
        answer_key: AnswerKey,
        maximum_score: float = 20.0
    ) -> Tuple[float, List[QuestionResult]]:
        """
        Calculates QCM grade and question results against the provided AnswerKey.
        """
        key_map = {item.question_number: item for item in answer_key.answers}
        question_results: List[QuestionResult] = []
        total_score = 0.0

        for q_num in range(1, len(key_map) + 1):
            key_item = key_map.get(q_num)
            correct_ans = key_item.correct_answer if key_item else None
            pts_val = key_item.points if key_item else answer_key.correct_points

            det_info = detected_answers.get(q_num, {})
            det_ans = det_info.get("selected")
            det_status = det_info.get("status", "Unanswered")

            pts_awarded = 0.0
            if det_ans is not None and correct_ans is not None:
                if det_ans == correct_ans:
                    pts_awarded = pts_val
                    q_status = "Correct"
                else:
                    pts_awarded = answer_key.incorrect_points  # may be 0.0 or negative penalty
                    q_status = "Incorrect"
            elif det_status == "Multiple":
                pts_awarded = answer_key.incorrect_points
                q_status = "Multiple"
            elif det_status == "Uncertain":
                pts_awarded = 0.0
                q_status = "Uncertain"
            else:
                pts_awarded = answer_key.unanswered_points
                q_status = "Unanswered"

            total_score += pts_awarded
            question_results.append(
                QuestionResult(
                    question_number=q_num,
                    detected_answer=det_ans,
                    correct_answer=correct_ans,
                    points_awarded=pts_awarded,
                    status=q_status
                )
            )

        # Clamp score between 0 and maximum_score
        clamped_score = max(0.0, min(float(maximum_score), round(total_score, 2)))
        return clamped_score, question_results

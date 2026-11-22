"""
Score Sheet OMR Bubble Detector for 4 numeric columns (10, 1, 0.1, 0.01).
"""
from typing import Dict, Tuple, Optional, Any, List
import cv2
import numpy as np

from config.templates import get_score_bubble_coords, SCORE_COLUMNS
from config.settings import BUBBLE_FILL_THRESHOLD, BUBBLE_UNCERTAIN_LOW

class ScoreDetector:
    def __init__(self, dpi: float = 300.0):
        self.dpi = dpi
        self.coords = get_score_bubble_coords(dpi=dpi)

    def _threshold_block_size(self) -> int:
        """Adaptive-threshold window: must be larger than a bubble (~4x radius) or the
        solid centre of a filled bubble is treated as background and the mark is missed."""
        from config.templates import BUBBLE_RADIUS_PT
        return int(BUBBLE_RADIUS_PT * self.dpi / 72.0 * 4) | 1

    def detect(self, aligned_image: np.ndarray, max_score: float = 20.0) -> Dict[str, Any]:
        """
        Detects selected digits for the 4 numeric columns and reconstructs the grade.
        Returns:
            {
                "score": Optional[float],
                "digits": {'tens': int, 'units': int, 'tenths': int, 'hundredths': int},
                "status": str, # 'Valid', 'Missing Digit', 'Multiple Digits', 'Uncertain', 'Exceeds Maximum'
                "column_details": Dict[str, Dict],
                "annotated_image": np.ndarray,
                "needs_review": bool,
                "warning": Optional[str]
            }
        """
        gray = cv2.cvtColor(aligned_image, cv2.COLOR_BGR2GRAY) if len(aligned_image.shape) == 3 else aligned_image
        annotated = aligned_image.copy()

        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
            self._threshold_block_size(), 10
        )

        column_results = {}
        detected_digits = {}
        needs_review = False
        warnings = []

        for col_info in SCORE_COLUMNS:
            col_name = col_info["name"]
            digits_coords = self.coords.get(col_name, {})
            fill_ratios = {}

            for digit in range(10):
                if digit not in digits_coords:
                    continue
                cx, cy, r = digits_coords[digit]
                cx_i, cy_i, r_i = int(round(cx)), int(round(cy)), int(round(r))

                inner_r = max(2, int(r_i * 0.75))
                mask = np.zeros(binary.shape, dtype=np.uint8)
                cv2.circle(mask, (cx_i, cy_i), inner_r, 255, -1)

                bubble_pixels = cv2.bitwise_and(binary, binary, mask=mask)
                total_inner = np.pi * (inner_r ** 2)
                filled = cv2.countNonZero(bubble_pixels)
                ratio = filled / total_inner if total_inner > 0 else 0.0
                fill_ratios[digit] = float(min(1.0, ratio))

            filled_digits = [d for d, r in fill_ratios.items() if r >= BUBBLE_FILL_THRESHOLD]
            ambig_digits = [
                d for d, r in fill_ratios.items()
                if BUBBLE_UNCERTAIN_LOW <= r < BUBBLE_FILL_THRESHOLD
            ]

            selected_digit = None
            if len(filled_digits) == 1 and not ambig_digits:
                selected_digit = filled_digits[0]
                col_status = "Valid"
            elif len(filled_digits) > 1:
                col_status = "Multiple"
                needs_review = True
                warnings.append(f"Multiple digits marked in column '{col_name}'")
            elif ambig_digits:
                col_status = "Uncertain"
                needs_review = True
                warnings.append(f"Uncertain mark in column '{col_name}'")
            else:
                col_status = "Empty"
                needs_review = True
                warnings.append(f"Empty column '{col_name}'")

            detected_digits[col_name] = selected_digit
            column_results[col_name] = {
                "selected": selected_digit,
                "status": col_status,
                "fill_ratios": fill_ratios
            }

            # Annotate image
            for digit, ratio in fill_ratios.items():
                cx, cy, r = digits_coords[digit]
                pt = (int(round(cx)), int(round(cy)))
                rad = int(round(r))
                if digit == selected_digit:
                    cv2.circle(annotated, pt, rad + 3, (0, 200, 0), 2)
                elif ratio >= BUBBLE_FILL_THRESHOLD or digit in ambig_digits:
                    cv2.circle(annotated, pt, rad + 3, (0, 165, 255), 2)

        # Reconstruct numerical score
        score = None
        overall_status = "Valid"
        if all(detected_digits.get(c["name"]) is not None for c in SCORE_COLUMNS):
            t = detected_digits["tens"]
            u = detected_digits["units"]
            th = detected_digits["tenths"]
            h = detected_digits["hundredths"]
            calculated = round(t * 10.0 + u * 1.0 + th * 0.1 + h * 0.01, 2)
            score = calculated

            if calculated > max_score:
                overall_status = "Exceeds Maximum"
                needs_review = True
                warnings.append(f"Score {calculated:.2f} exceeds maximum score {max_score:.2f}")
            else:
                overall_status = "Valid"
        else:
            overall_status = "Incomplete"
            needs_review = True

        warning_text = "; ".join(warnings) if warnings else None

        return {
            "score": score,
            "digits": detected_digits,
            "status": overall_status,
            "column_details": column_results,
            "annotated_image": annotated,
            "needs_review": needs_review,
            "warning": warning_text
        }

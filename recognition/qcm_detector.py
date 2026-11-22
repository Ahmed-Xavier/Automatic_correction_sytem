"""
QCM OMR Bubble Detector for 40 Questions (Options A, B, C).
"""
from typing import Dict, Tuple, Optional, Any, List
import cv2
import numpy as np

from config.templates import get_qcm_bubble_coords
from config.settings import BUBBLE_FILL_THRESHOLD, BUBBLE_UNCERTAIN_LOW, BUBBLE_UNCERTAIN_HIGH

class QCMDetector:
    def __init__(self, dpi: float = 300.0):
        self.dpi = dpi
        self.bubble_coords = get_qcm_bubble_coords(dpi=dpi)

    def detect(self, aligned_image: np.ndarray) -> Dict[str, Any]:
        """
        Detects selected bubbles for all 40 questions.
        Returns:
            {
                "questions": {
                    q_num: {
                        "selected": Optional[str], # 'A', 'B', 'C', or None
                        "status": str, # 'Single', 'Unanswered', 'Multiple', 'Uncertain'
                        "fill_ratios": {'A': float, 'B': float, 'C': float},
                        "confidence": float
                    }
                },
                "annotated_image": np.ndarray,
                "has_uncertain": bool
            }
        """
        gray = cv2.cvtColor(aligned_image, cv2.COLOR_BGR2GRAY) if len(aligned_image.shape) == 3 else aligned_image
        annotated = aligned_image.copy()

        # Binarize with inverted values: ink = 255
        # Use adaptive or local threshold to handle lighting / pencil vs pen
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 10
        )

        questions_result = {}
        has_uncertain = False

        for q_num in range(1, 41):
            opts_coords = self.bubble_coords.get(q_num, {})
            fill_ratios = {}

            for opt in ["A", "B", "C"]:
                if opt not in opts_coords:
                    continue
                cx, cy, r = opts_coords[opt]
                cx_i, cy_i, r_i = int(round(cx)), int(round(cy)), int(round(r))

                # Measure inner circle area to ignore printed outline
                inner_r = max(2, int(r_i * 0.75))
                mask = np.zeros(binary.shape, dtype=np.uint8)
                cv2.circle(mask, (cx_i, cy_i), inner_r, 255, -1)

                bubble_pixels = cv2.bitwise_and(binary, binary, mask=mask)
                total_inner_pixels = np.pi * (inner_r ** 2)
                filled_pixels = cv2.countNonZero(bubble_pixels)
                ratio = filled_pixels / total_inner_pixels if total_inner_pixels > 0 else 0.0
                fill_ratios[opt] = float(min(1.0, ratio))

            # Classify marked options
            filled_opts = [opt for opt, r in fill_ratios.items() if r >= BUBBLE_FILL_THRESHOLD]
            ambig_opts = [
                opt for opt, r in fill_ratios.items() 
                if BUBBLE_UNCERTAIN_LOW <= r < BUBBLE_FILL_THRESHOLD
            ]

            selected = None
            if len(filled_opts) == 1 and not ambig_opts:
                selected = filled_opts[0]
                status = "Single"
                conf = fill_ratios[selected]
            elif len(filled_opts) > 1:
                status = "Multiple"
                conf = 0.5
                has_uncertain = True
            elif ambig_opts:
                status = "Uncertain"
                conf = 0.4
                has_uncertain = True
            else:
                status = "Unanswered"
                conf = 1.0

            questions_result[q_num] = {
                "selected": selected,
                "status": status,
                "fill_ratios": fill_ratios,
                "confidence": conf
            }

            # Draw visual feedback on annotated image
            for opt, ratio in fill_ratios.items():
                cx, cy, r = opts_coords[opt]
                pt = (int(round(cx)), int(round(cy)))
                rad = int(round(r))
                if opt == selected:
                    # Green circle for selected
                    cv2.circle(annotated, pt, rad + 3, (0, 200, 0), 2)
                elif ratio >= BUBBLE_FILL_THRESHOLD or opt in ambig_opts:
                    # Orange / Yellow circle for ambiguous / multiple
                    cv2.circle(annotated, pt, rad + 3, (0, 165, 255), 2)

        return {
            "questions": questions_result,
            "annotated_image": annotated,
            "has_uncertain": has_uncertain
        }

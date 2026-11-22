"""
Document Classification: classifies pages into QCM, Score Sheet, or Unknown.
"""
from typing import Tuple, Dict, Any
import cv2
import numpy as np
from config.templates import CANONICAL_WIDTH_PT, CANONICAL_HEIGHT_PT

class DocumentClassifier:
    def __init__(self, dpi: float = 300.0):
        self.dpi = dpi
        self.scale = dpi / 72.0

    def classify(self, aligned_image: np.ndarray, detected_text: str = "") -> Tuple[str, float]:
        """
        Classifies an aligned image.
        Returns (document_type, confidence).
        Types: 'QCM', 'Score Sheet', 'Unknown'.
        """
        h, w = aligned_image.shape[:2]
        gray = cv2.cvtColor(aligned_image, cv2.COLOR_BGR2GRAY) if len(aligned_image.shape) == 3 else aligned_image

        # 1. Text hint if provided (e.g. from PDF text or OCR)
        lower_text = detected_text.lower()
        if "qcm" in lower_text:
            return "QCM", 0.99
        if "total score" in lower_text or "barecode" in lower_text:
            return "Score Sheet", 0.99

        # 2. Geometric / Header Inspection
        # QCM header box is at top left: (22.68 to 66.99 pt, Y: 34.02 to 78.32 pt)
        # Score Sheet header box is larger: (22.68 to 115.65 pt, Y: 34.02 to 161.77 pt)
        # Inspect top-left region
        tl_w = int(120 * self.scale)
        tl_h = int(170 * self.scale)
        roi_tl = gray[int(30 * self.scale):tl_h, int(20 * self.scale):tl_w]

        # In QCM, the grid starts at Y ≈ 122 pt with 4 header columns
        # In Score Sheet, the grid starts at Y ≈ 161 pt with 4 columns
        # Let's count horizontal separator lines in Y range [120..190 pt]
        y_test_0 = int(120 * self.scale)
        y_test_1 = int(190 * self.scale)
        roi_mid = gray[y_test_0:y_test_1, int(w * 0.1):int(w * 0.9)]
        edges = cv2.Canny(roi_mid, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=int(w * 0.5), maxLineGap=10)

        num_horiz_lines = 0
        if lines is not None:
            for l in lines:
                x1, y1, x2, y2 = l[0]
                if abs(y2 - y1) <= 3:
                    num_horiz_lines += 1

        # Check column density in question area (Y ~ 200..300 pt)
        # QCM has 12 bubble columns across page width
        # Score Sheet has only 4 bubble columns across page width
        roi_bubbles = gray[int(220 * self.scale):int(280 * self.scale), :]
        _, bin_bubbles = cv2.threshold(roi_bubbles, 200, 255, cv2.THRESH_BINARY_INV)
        col_proj = np.sum(bin_bubbles > 0, axis=0)
        peaks = (col_proj > np.mean(col_proj) * 1.5).astype(np.uint8)
        num_peaks, _ = cv2.connectedComponents(peaks)

        if num_peaks >= 8:
            return "QCM", 0.95
        elif 2 <= num_peaks < 8:
            return "Score Sheet", 0.90

        # Secondary check on title aspect ratio
        if roi_tl.shape[0] > 0 and roi_tl.shape[1] > 0:
            dark_ratio = np.mean(roi_tl < 128)
            if dark_ratio > 0.05:
                # Distinguish by height of the dark title box
                return "QCM", 0.75

        return "Unknown", 0.40

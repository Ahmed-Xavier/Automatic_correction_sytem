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

        # The score sheet has a tall left header box with a vertical divider at
        # x=115.65 pt. QCM has no divider there (its short header divider is at
        # x=66.99 pt). This canonical template cue is more reliable than bubble
        # density, which can be distorted by completed marks.
        header_y0 = int(round(34.0 * self.scale))
        header_y1 = int(round(162.0 * self.scale))
        score_header_x = int(round(115.65 * self.scale))
        if header_y1 <= h and score_header_x < w:
            divider_ink = gray[header_y0:header_y1, score_header_x:score_header_x + 1] < 160
            if divider_ink.size and float(np.mean(divider_ink)) > 0.75:
                return "Score Sheet", 0.99

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
            for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
                if abs(y2 - y1) <= 3:
                    num_horiz_lines += 1

        # Check column density in question area (Y ~ 200..300 pt)
        # QCM has 12 bubble columns across page width
        # Score Sheet has only 4 bubble columns across page width
        roi_bubbles = gray[int(220 * self.scale):int(280 * self.scale), :]
        _, bin_bubbles = cv2.threshold(roi_bubbles, 200, 255, cv2.THRESH_BINARY_INV)
        col_proj = np.sum(bin_bubbles > 0, axis=0)
        peaks = (col_proj > np.mean(col_proj) * 1.5).astype(np.uint8)
        # Count runs in this 1-D mask directly. OpenCV builds differ in the
        # return value exposed by connectedComponents for a 1-D input.
        padded_peaks = np.pad(peaks.astype(np.int16), (1, 1))
        num_peaks = int(np.count_nonzero(np.diff(padded_peaks) == 1))

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

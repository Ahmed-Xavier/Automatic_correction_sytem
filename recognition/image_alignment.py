"""
Image alignment and registration to canonical template coordinates.
"""
from typing import Tuple, Optional, List
import cv2
import numpy as np
from config.templates import CANONICAL_WIDTH_PT, CANONICAL_HEIGHT_PT, CANONICAL_FIDUCIALS

class ImageAligner:
    def __init__(self, dpi: float = 300.0):
        self.dpi = dpi
        self.scale = dpi / 72.0
        self.target_w = int(round(CANONICAL_WIDTH_PT * self.scale))
        self.target_h = int(round(CANONICAL_HEIGHT_PT * self.scale))
        
        # Target corner coordinates in pixels
        self.target_pts = np.float32([
            [CANONICAL_FIDUCIALS["top_left"][0] * self.scale, CANONICAL_FIDUCIALS["top_left"][1] * self.scale],
            [CANONICAL_FIDUCIALS["top_right"][0] * self.scale, CANONICAL_FIDUCIALS["top_right"][1] * self.scale],
            [CANONICAL_FIDUCIALS["bottom_right"][0] * self.scale, CANONICAL_FIDUCIALS["bottom_right"][1] * self.scale],
            [CANONICAL_FIDUCIALS["bottom_left"][0] * self.scale, CANONICAL_FIDUCIALS["bottom_left"][1] * self.scale],
        ])

    def align(self, image: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        Aligns the image to the canonical template size (2480 x 3508 @ 300 DPI).
        Returns (aligned_image, success).
        """
        h, w = image.shape[:2]

        # If already exactly or very close to target dimensions and minimal skew, return resized
        if abs(w - self.target_w) < 15 and abs(h - self.target_h) < 15:
            if w != self.target_w or h != self.target_h:
                aligned = cv2.resize(image, (self.target_w, self.target_h), interpolation=cv2.INTER_AREA)
                return aligned, True
            return image, True

        # Try to detect corner fiducials
        corner_pts = self._find_corner_markers(image)
        if corner_pts is not None:
            M = cv2.getPerspectiveTransform(corner_pts, self.target_pts)
            aligned = cv2.warpPerspective(
                image, M, (self.target_w, self.target_h),
                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
            return aligned, True

        # Fallback: simple aspect-ratio preserving resize to target canonical size
        aligned = cv2.resize(image, (self.target_w, self.target_h), interpolation=cv2.INTER_AREA)
        return aligned, False

    def _find_corner_markers(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Searches for 4 solid black rectangular fiducials in the 4 corner zones."""
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        _, binary = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)

        margin_x = int(w * 0.15)
        margin_y = int(h * 0.15)

        corners = {
            "top_left": (0, 0, margin_x, margin_y),
            "top_right": (w - margin_x, 0, w, margin_y),
            "bottom_right": (w - margin_x, h - margin_y, w, h),
            "bottom_left": (0, h - margin_y, margin_x, h),
        }

        detected_centers = []
        for key in ["top_left", "top_right", "bottom_right", "bottom_left"]:
            x0, y0, x1, y1 = corners[key]
            roi = binary[y0:y1, x0:x1]
            contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            best_marker = None
            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Markers are roughly 10x30 to 20x50 px at 300 DPI (area ~ 300 - 3000)
                if 100 < area < 5000:
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    aspect = bh / float(bw) if bw > 0 else 0
                    if 1.2 <= aspect <= 4.0:
                        cx = x0 + bx + bw / 2.0
                        cy = y0 + by + bh / 2.0
                        best_marker = (cx, cy)
                        break

            if best_marker is None:
                return None
            detected_centers.append(best_marker)

        return np.float32(detected_centers)

"""
Image preprocessing utilities: binarization, grayscale, noise reduction, deskew.
"""
from typing import Tuple
import cv2
import numpy as np

def to_grayscale(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def binarize_image(gray: np.ndarray) -> np.ndarray:
    """Otsu binarization with inverted output (dark ink becomes white 255 for analysis)."""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary

def estimate_and_deskew(img: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Estimates global skew using Hough lines or minAreaRect on contours
    and corrects small angle rotations (-15 to +15 deg).
    """
    gray = to_grayscale(img)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=img.shape[1] // 4, maxLineGap=20)

    angle = 0.0
    if lines is not None and len(lines) > 0:
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 != x1:
                deg = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Consider near-horizontal lines
                if abs(deg) < 15:
                    angles.append(deg)
        if angles:
            angle = float(np.median(angles))

    if abs(angle) > 0.2:
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        deskewed = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return deskewed, angle

    return img, 0.0

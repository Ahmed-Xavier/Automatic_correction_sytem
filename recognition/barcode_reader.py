"""
Barcode reading module using zxingcpp with OpenCV fallback.
"""
from typing import Optional, List, Tuple
import cv2
import numpy as np
import zxingcpp

class BarcodeReader:
    def __init__(self):
        # Fallback OpenCV barcode detector
        try:
            self.cv_detector = cv2.barcode.BarcodeDetector()
        except Exception:
            self.cv_detector = None

    def read_barcode(self, image: np.ndarray) -> Optional[str]:
        """
        Detects and decodes the primary barcode on the document.
        Tries full page, then barcode search regions, then preprocessed versions.
        """
        # 1. Direct zxing-cpp full image
        barcodes = zxingcpp.read_barcodes(image)
        for b in barcodes:
            if b.text and len(b.text.strip()) > 0:
                return b.text.strip()

        # 2. Try top region crop (where barcodes are located in QCM and Score templates)
        h, w = image.shape[:2]
        # Crop top 25% of page
        top_crop = image[0:int(h * 0.25), int(w * 0.40):w]
        barcodes = zxingcpp.read_barcodes(top_crop)
        for b in barcodes:
            if b.text and len(b.text.strip()) > 0:
                return b.text.strip()

        # 3. Contrast enhanced / Binarized crop
        gray = cv2.cvtColor(top_crop, cv2.COLOR_BGR2GRAY) if len(top_crop.shape) == 3 else top_crop
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        barcodes = zxingcpp.read_barcodes(thresh)
        for b in barcodes:
            if b.text and len(b.text.strip()) > 0:
                return b.text.strip()

        # 4. Fallback OpenCV BarcodeDetector
        if self.cv_detector is not None:
            try:
                res = self.cv_detector.detectAndDecode(image)
                if len(res) == 3:
                    text, _, _ = res
                else:
                    _, text, _, _ = res
                if text and len(text.strip()) > 0:
                    return text.strip()
            except Exception:
                pass

        return None

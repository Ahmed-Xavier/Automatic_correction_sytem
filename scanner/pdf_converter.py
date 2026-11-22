"""
PDF to high-resolution OpenCV image conversion.
"""
from pathlib import Path
from typing import List, Tuple
import pymupdf
import cv2
import numpy as np

def convert_pdf_to_images(pdf_path: Path, dpi: int = 300) -> List[np.ndarray]:
    """
    Renders each page of a PDF document to an OpenCV BGR numpy array.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    doc = pymupdf.open(str(path))
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        
        # Convert to BGR format for OpenCV
        if pix.n == 4:
            bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        elif pix.n == 1:
            bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            bgr = img

        images.append(bgr)

    doc.close()
    return images

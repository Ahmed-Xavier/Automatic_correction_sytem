"""
TIFF / Image file loader and multi-page converter.
"""
from pathlib import Path
from typing import List
from PIL import Image, ImageSequence
import cv2
import numpy as np

def convert_tiff_to_images(tiff_path: Path) -> List[np.ndarray]:
    """
    Extracts all pages from a single or multi-page TIFF file into OpenCV BGR numpy arrays.
    """
    path = Path(tiff_path)
    if not path.exists():
        raise FileNotFoundError(f"TIFF file not found: {path}")

    pil_img = Image.open(str(path))
    images = []

    for frame in ImageSequence.Iterator(pil_img):
        rgb_frame = frame.convert("RGB")
        np_img = np.array(rgb_frame)
        bgr = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
        images.append(bgr)

    return images

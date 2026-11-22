"""
File ingestion and batch registration for scanned documents.
"""
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import datetime
import hashlib
import cv2
import numpy as np

from config.paths import SCANS_DIR, PROCESSED_DIR, ensure_directories
from config.settings import SCAN_RENDER_DPI, SUPPORTED_IMAGE_EXTENSIONS
from database.models import ScanBatch, ScannedDocument
from database.result_repository import ResultRepository
from scanner.pdf_converter import convert_pdf_to_images
from scanner.tiff_converter import convert_tiff_to_images

class FileIngestion:
    def __init__(self, result_repo: ResultRepository):
        self.result_repo = result_repo
        ensure_directories()
        self.pages_dir = SCANS_DIR / "extracted_pages"
        self.pages_dir.mkdir(parents=True, exist_ok=True)

    def ingest_file(self, file_path: Path) -> Tuple[ScanBatch, List[Tuple[ScannedDocument, np.ndarray]]]:
        """
        Ingests a document file (PDF, TIFF, PNG, JPG).
        Returns the registered ScanBatch and list of (ScannedDocument, image_bgr).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Compute file hash to prevent accidental re-imports
        file_hash = self._compute_hash(path)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_id = f"BATCH_{timestamp}_{file_hash[:6]}"

        ext = path.suffix.lower()
        images: List[np.ndarray] = []

        if ext == ".pdf":
            images = convert_pdf_to_images(path, dpi=SCAN_RENDER_DPI)
        elif ext in [".tiff", ".tif"]:
            images = convert_tiff_to_images(path)
        elif ext in SUPPORTED_IMAGE_EXTENSIONS:
            img = cv2.imread(str(path))
            if img is not None:
                images = [img]
            else:
                raise ValueError(f"Could not load image: {path}")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        batch = ScanBatch(
            batch_id=batch_id,
            source_file=path.name,
            total_pages=len(images),
            status="Processing"
        )
        self.result_repo.create_batch(batch)

        extracted_docs = []
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        for idx, img in enumerate(images, start=1):
            doc_id = f"{batch_id}_P{idx:03d}"
            page_save_path = self.pages_dir / f"{doc_id}.png"
            cv2.imwrite(str(page_save_path), img)

            doc = ScannedDocument(
                document_id=doc_id,
                batch_id=batch_id,
                page_number=idx,
                document_type="Unknown",
                processing_status="Pending",
                original_image_path=str(page_save_path),
            )
            self.result_repo.save_scanned_document(doc)
            extracted_docs.append((doc, img))

        return batch, extracted_docs

    def _compute_hash(self, path: Path) -> str:
        hasher = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

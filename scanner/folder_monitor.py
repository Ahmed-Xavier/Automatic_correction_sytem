"""
Scanner folder monitor.
"""
from pathlib import Path
from typing import List, Set
import time
from config.settings import SUPPORTED_DOCUMENT_EXTENSIONS

class FolderMonitor:
    def __init__(self, watch_dir: Path):
        self.watch_dir = Path(watch_dir)
        self.processed_files: Set[str] = set()

    def get_pending_files(self) -> List[Path]:
        """Returns list of completed files in folder not yet processed."""
        if not self.watch_dir.exists():
            return []

        pending = []
        for file in self.watch_dir.iterdir():
            if file.is_file() and file.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS:
                if file.name not in self.processed_files:
                    if self._is_file_ready(file):
                        pending.append(file)
        return sorted(pending)

    def mark_processed(self, file_path: Path):
        self.processed_files.add(file_path.name)

    def _is_file_ready(self, file_path: Path) -> bool:
        """Check if file is completely written and not currently locked."""
        try:
            size1 = file_path.stat().st_size
            time.sleep(0.05)
            size2 = file_path.stat().st_size
            return size1 == size2 and size1 > 0
        except Exception:
            return False

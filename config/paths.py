"""
Paths configuration for the Examination Correction System.
"""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Data subdirectories
SCANS_DIR = DATA_DIR / "scans"
PROCESSED_DIR = DATA_DIR / "processed"
FAILED_DIR = DATA_DIR / "failed"
EXPORTS_DIR = DATA_DIR / "exports"
BARCODE_DIR = DATA_DIR / "barcode_database"
ANSWER_KEYS_DIR = DATA_DIR / "answer_keys"
STICKERS_DIR = DATA_DIR / "stickers"  # printable barcode sticker PDFs

# Database path
DEFAULT_DB_PATH = DATA_DIR / "examination.sqlite"

def ensure_directories():
    """Ensure all required directories exist."""
    for directory in [
        DATA_DIR,
        SCANS_DIR,
        PROCESSED_DIR,
        FAILED_DIR,
        EXPORTS_DIR,
        BARCODE_DIR,
        ANSWER_KEYS_DIR,
        STICKERS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def dialog_dir(directory: Path) -> str:
    """Return a default folder for a Tkinter file dialog (created if missing)."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory)

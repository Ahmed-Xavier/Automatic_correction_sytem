"""
Application settings and defaults.
"""
from pathlib import Path
from config.paths import DEFAULT_DB_PATH, SCANS_DIR

# Database configuration
DATABASE_PATH = DEFAULT_DB_PATH

# Scanner configuration
SCANNER_INPUT_DIR = SCANS_DIR
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif"}
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf"}.union(SUPPORTED_IMAGE_EXTENSIONS)
SCAN_RENDER_DPI = 300

# OMR recognition thresholds
# Fill threshold: fraction of bubble area that must be dark to be considered filled
BUBBLE_FILL_THRESHOLD = 0.45
# Threshold to flag as ambiguous / uncertain mark
BUBBLE_UNCERTAIN_LOW = 0.30
BUBBLE_UNCERTAIN_HIGH = 0.50

# Default Grading Rules
DEFAULT_CORRECT_POINTS = 0.5
DEFAULT_INCORRECT_POINTS = 0.0
DEFAULT_UNANSWERED_POINTS = 0.0
DEFAULT_MAX_SCORE = 20.0

# Barcode configuration
BARCODE_FORMAT = "Code 128"

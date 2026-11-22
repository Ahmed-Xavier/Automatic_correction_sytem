"""
Centralized OMR template definitions and coordinates.
All coordinates are defined in canonical A4 point coordinates (72 points/inch)
and can be scaled to any target resolution (default 300 DPI).
"""

# Canonical A4 dimensions in points
CANONICAL_WIDTH_PT = 595.28
CANONICAL_HEIGHT_PT = 841.89

# Canonical corner fiducial marks (centers in points)
CANONICAL_FIDUCIALS = {
    "top_left": (13.04, 15.87),
    "top_right": (582.24, 15.87),
    "bottom_left": (13.04, 826.02),
    "bottom_right": (582.24, 826.02),
}

# 11 Top timing ticks X positions
TOP_TIMING_TICKS_X = [
    13.04, 69.96, 126.88, 183.80, 240.72,
    297.64, 354.56, 411.48, 468.40, 525.32, 582.24
]
TOP_TIMING_TICKS_Y = 15.87

# Barcode search regions (points): [x0, y0, x1, y1]
QCM_BARCODE_REGION_PT = (340.0, 45.0, 520.0, 120.0)
SCORE_BARCODE_REGION_PT = (340.0, 60.0, 520.0, 150.0)

# Bubble radius in points
BUBBLE_RADIUS_PT = 9.92

# -------------------------------------------------------------
# QCM TEMPLATE DEFINITIONS (40 Questions, 3 Options A, B, C)
# -------------------------------------------------------------
QCM_QUESTION_COLUMNS = [
    {"q_start": 1,  "q_end": 10, "x_options": {"A": 74.8,  "B": 108.0, "C": 141.2}},
    {"q_start": 11, "q_end": 20, "x_options": {"A": 212.2, "B": 245.4, "C": 278.6}},
    {"q_start": 21, "q_end": 30, "x_options": {"A": 349.6, "B": 382.8, "C": 416.1}},
    {"q_start": 31, "q_end": 40, "x_options": {"A": 487.0, "B": 520.3, "C": 553.5}},
]

QCM_ROW_Y_CENTERS = [
    189.5, 255.5, 321.6, 387.6, 453.7,
    519.7, 585.8, 651.8, 717.9, 783.9
]

def get_qcm_bubble_coords(dpi: float = 300.0):
    """
    Returns a dict mapping question number (1..40) to dict of option -> (cx, cy, radius) in pixels.
    """
    scale = dpi / 72.0
    radius_px = BUBBLE_RADIUS_PT * scale
    result = {}
    for col_info in QCM_QUESTION_COLUMNS:
        q_start = col_info["q_start"]
        x_opts = col_info["x_options"]
        for row_idx, cy_pt in enumerate(QCM_ROW_Y_CENTERS):
            q_num = q_start + row_idx
            result[q_num] = {}
            for opt, cx_pt in x_opts.items():
                result[q_num][opt] = (
                    cx_pt * scale,
                    cy_pt * scale,
                    radius_px
                )
    return result

# -------------------------------------------------------------
# NON-QCM SCORE SHEET DEFINITIONS (4 columns: 10, 1, 0.1, 0.01)
# -------------------------------------------------------------
SCORE_COLUMNS = [
    {"name": "tens",        "label": "10",   "cx": 90.7,  "multiplier": 10.0},
    {"name": "units",       "label": "1",    "cx": 226.7, "multiplier": 1.0},
    {"name": "tenths",      "label": "0.1",  "cx": 362.8, "multiplier": 0.1},
    {"name": "hundredths",  "label": "0.01", "cx": 500.3, "multiplier": 0.01},
]

SCORE_DIGIT_ROW_Y_CENTERS = [
    252.0, 311.4, 370.9, 430.4, 489.9,
    549.3, 608.8, 668.3, 727.7, 787.2
]

def get_score_bubble_coords(dpi: float = 300.0):
    """
    Returns a dict mapping column name ('tens', 'units', 'tenths', 'hundredths')
    to a dict of digit (0..9) -> (cx, cy, radius) in pixels.
    """
    scale = dpi / 72.0
    radius_px = BUBBLE_RADIUS_PT * scale
    result = {}
    for col_info in SCORE_COLUMNS:
        col_name = col_info["name"]
        cx_pt = col_info["cx"]
        result[col_name] = {}
        for digit, cy_pt in enumerate(SCORE_DIGIT_ROW_Y_CENTERS):
            result[col_name][digit] = (
                cx_pt * scale,
                cy_pt * scale,
                radius_px
            )
    return result

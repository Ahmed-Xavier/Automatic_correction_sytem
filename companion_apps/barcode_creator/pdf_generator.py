"""
PDF sticker sheet generator for Student Barcode Creator.
Generates printable A4 sheets of Code 128 barcode stickers.
"""
from pathlib import Path
from typing import List, Dict, Any
import io
import pymupdf
import zxingcpp
import numpy as np
from PIL import Image

def generate_barcode_pdf(
    output_path: Path,
    student_records: List[Dict[str, str]],
    stickers_per_row: int = 3,
    rows_per_page: int = 8
) -> Path:
    """
    Generates printable A4 PDF containing barcode stickers.
    """
    out_file = Path(output_path)
    doc = pymupdf.open()

    page_w = 595.28  # A4 width in pt
    page_h = 841.89  # A4 height in pt

    margin_x = 25.0
    margin_y = 30.0

    usable_w = page_w - (2 * margin_x)
    usable_h = page_h - (2 * margin_y)

    sticker_w = usable_w / stickers_per_row
    sticker_h = usable_h / rows_per_page

    stickers_per_page = stickers_per_row * rows_per_page

    for page_start in range(0, len(student_records), stickers_per_page):
        page_records = student_records[page_start:page_start + stickers_per_page]
        page = doc.new_page(width=page_w, height=page_h)

        for idx, rec in enumerate(page_records):
            row_idx = idx // stickers_per_row
            col_idx = idx % stickers_per_row

            x0 = margin_x + col_idx * sticker_w
            y0 = margin_y + row_idx * sticker_h
            x1 = x0 + sticker_w - 6.0
            y1 = y0 + sticker_h - 6.0

            code = rec.get("full_barcode", "")
            name = rec.get("student_name", "Student")
            sub = rec.get("subject", "")

            # Name stays on the paper, OUTSIDE the sticker box (above it)
            page.insert_text(
                pymupdf.Point(x0 + 2, y0 + 9),
                f"{name} ({sub})",
                fontsize=8,
                fontname="helv",
                color=(0.1, 0.1, 0.1)
            )

            # Sticker box (cut line): holds the barcode only, no name
            box = pymupdf.Rect(x0, y0 + 14, x1, y1)
            page.draw_rect(box, color=(0.6, 0.6, 0.6), width=0.5)

            try:
                bc = zxingcpp.create_barcode(code, format=zxingcpp.BarcodeFormat.Code128)
                zimg = zxingcpp.write_barcode_to_image(bc)
                pil_img = Image.fromarray(np.array(zimg))
                img_bytes = io.BytesIO()
                pil_img.save(img_bytes, format="PNG")
                page.insert_image(
                    pymupdf.Rect(x0 + 8, y0 + 20, x1 - 8, y1 - 14),
                    stream=img_bytes.getvalue()
                )
            except Exception:
                page.insert_text(pymupdf.Point(x0 + 8, y0 + 35),
                                 f"[Barcode Gen Error: {code}]",
                                 fontsize=7, color=(0.8, 0, 0))

            # Human-readable code inside the box, under the barcode
            page.insert_text(
                pymupdf.Point(x0 + 10, y1 - 4),
                code,
                fontsize=7,
                fontname="cour",
                color=(0.2, 0.2, 0.2)
            )

    out_file.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_file))
    doc.close()
    return out_file

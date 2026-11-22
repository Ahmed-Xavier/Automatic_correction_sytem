# Quick walkthrough

## 0. Install (once)
```
pip install -r requirements.txt
```
Tkinter ships with the normal Windows/macOS Python installer. (On Linux: `sudo apt install python3-tk`.)

## 1. Default folders
Every file dialog now opens in the right folder under `data/` (created automatically):

| What | Folder |
|---|---|
| Barcode mapping Excel (Barcode Creator output) | `data/barcode_database/` |
| Printable sticker PDFs | `data/stickers/` |
| Answer key Excel | `data/answer_keys/` |
| Scans to process | `data/scans/` |
| Master results Excel | `data/exports/` |

File names are pre-filled (e.g. `stickers-20261122-1430.pdf`). You can still browse elsewhere.

## 2. Barcode Creator  (`barcode_creator_run.bat`)
1. Type the **Subject** and **Exam ID** at the top.
2. Add students: type a name (+ optional Student ID) and press **Add**, or **Import from Excel** (needs a column with "name" or "nom").
3. **Generate Excel** -> mapping file (keep it, the main app needs it).
4. **Generate PDF Stickers** -> A4 sheet, 3 x 8 = 24 stickers per page. Print on sticker paper.

## 3. Answer Key Manager  (`answer_key_manager_run .bat`)
1. Fill Exam ID (must match the Exam ID used for the barcodes) and Subject.
2. Click the correct answer for each question in the grid. The printed card only has **A, B, C** and 40 questions.
3. Set points (correct / wrong / blank) and max score, then **Export Excel**.

## 4. Main app  (`main_run.bat`)
1. **Barcode Database** -> import the mapping Excel (or the whole `data/barcode_database` folder).
2. **Answer Keys** -> import the answer key Excel.
3. Students stick their barcode on the card, fill bubbles (pen or pencil), and you scan to PDF/TIFF/PNG/JPG (300 dpi recommended).
4. **Scan Processing** -> add the files or a folder -> start. Pages are aligned, the barcode identifies the student, bubbles are read and scored.
5. **Manual Review** -> check pages flagged (unknown barcode, double marks, unclear marks).
6. **Results** -> **Export Excel** for the master workbook.

Mixed batches work: QCM cards and numeric score sheets can be scanned together.

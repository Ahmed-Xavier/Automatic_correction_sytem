# Examination Correction System

A Windows desktop application for identifying students from exam barcodes, reading QCM answers or written scores, reviewing uncertain scans, and exporting results to Excel.

The repository contains three Tkinter apps:

- **Student Barcode Creator** creates a barcode mapping workbook and printable barcode stickers.
- **Answer Key Manager** creates answer keys for QCM exams.
- **Examination Correction System** imports those files, processes scans, and exports results.

## Quick start

### 1. Install dependencies

Install Python 3.10 or newer, then open a terminal in this folder and run:

```powershell
python -m pip install -r requirements.txt
```

Tkinter is included with the standard Windows Python installer. Double-click the `.bat` launchers from this folder.

### 2. Create student barcodes

Launch `barcode_creator_run.bat`.

1. Enter the **Subject before adding any students**. The app records the subject when each student is added; changing it afterward does not update students already listed.
2. Add students one at a time or import a student list from Excel.
3. Choose **Generate Excel** and save the mapping workbook.
4. Choose **Generate PDF Stickers** and print the stickers.

The app creates an exam ID from the subject, such as `MULTI-EXAM`. Keep the generated workbook: its barcode-to-student mappings are needed when scans are processed.

### 3. Create a QCM answer key (QCM only)

Launch `answer_key_manager_run .bat` (the launcher filename includes a space before `.bat`).

1. Enter the same **Subject** used for the barcodes. The generated exam ID must match, for example `MULTI-EXAM`.
2. Choose the correct option for each question and set the scoring values and maximum score.
3. Export the answer key workbook.

Written score sheets do not need an answer key. Their exam maximum score is used when reading the score columns.

### 4. Import setup files into the main app

Launch `main_run.bat`.

1. Open **Barcode Database** and import the workbook from Barcode Creator.
2. For QCM exams, open **Answer Keys** and import the Answer Key Manager workbook.
3. Verify the barcode mappings and answer key were imported before scanning.

The main app creates or updates its internal exam records from imported barcode and answer-key files. There is no separate Examinations screen. Use the same subject and resulting exam ID in the barcode workbook and answer key.

### 5. Process papers

1. Scan completed papers to PDF or image files. Straight, clear scans at about 300 DPI work best.
2. In **Scan Processing**, add files or a folder and start processing. QCM and written score sheets can be in the same batch.
3. Check **Manual Review** for unknown barcodes, unclear marks, multiple answers, or uncertain score digits. Confirm the detected result if it is correct, or save an override after entering the corrected score and reason.
4. In **Results**, export the results workbook.

For the included demo PDFs, import the matching files under `data/barcode_database` and `data/answer_keys` first. The normal and unclear QCM demos contain the same students and exam but use different barcodes. If processing both versions, use **Reset Scan Data** between runs; it clears prior results and scan history while keeping exam setup files and source PDFs.

## Data folders

| Folder | Contents |
|---|---|
| `data/barcode_database/` | Barcode mapping workbooks |
| `data/stickers/` | Printable barcode sticker PDFs |
| `data/answer_keys/` | QCM answer key workbooks |
| `data/scans/` | Source scans and demo scan PDFs |
| `data/exports/` | Exported result workbooks |
| `output/pdf/` | Demo PDFs and demo notes |

The SQLite database and generated processing images are also stored under `data/`.

## Common issues

- **Unknown barcode:** Import the correct mapping workbook and check that the barcode printed on the paper exactly matches one of its mappings.
- **QCM has no key:** Import the answer key for the same exam ID as the barcode mapping.
- **Subject appears as GENERAL:** In Barcode Creator, enter the subject before clicking **Add** for any student. Remove incorrectly added students and add them again after correcting the subject.
- **Duplicate student results:** The same student/exam can have only one result. Reset scan data before processing an alternate version of the same students' papers.
- **Reset cannot remove an export:** Close the exported workbook in Excel, then run Reset Scan Data again.

## More information

See [`USAGE.md`](USAGE.md) for a short walkthrough and [`Docs/README.md`](Docs/README.md) for the technical design and detailed project reference.

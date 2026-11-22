"""
Scan Processing panel — file selection, batch progress, background processing.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import queue
from typing import List

from config.paths import SCANS_DIR, PROCESSED_DIR, FAILED_DIR, EXPORTS_DIR, DATA_DIR, dialog_dir
from gui.ui_utils import COLORS, FONTS, SectionHeader
from database.repositories import ServiceManager
from scanner.batch_processor import BatchProcessor
from config.settings import SCANNER_INPUT_DIR

class ScanManagerPanel(tk.Frame):
    def __init__(self, parent, service_manager: ServiceManager):
        super().__init__(parent, bg=COLORS["bg"])
        self.sm = service_manager
        self.processor = BatchProcessor(service_manager)
        self._queue: queue.Queue = queue.Queue()
        self._processing = False
        self._build()
        self._poll_queue()

    def _build(self):
        SectionHeader(self, "Scan Processing",
                      "Process mixed batches of QCM papers and score sheets").pack(
                          fill="x", padx=24, pady=(24, 8))

        # Input selection
        input_frame = tk.LabelFrame(self, text="  Input  ", bg=COLORS["bg"],
                                     font=FONTS["heading"], fg=COLORS["text_primary"],
                                     bd=1, relief="groove")
        input_frame.pack(fill="x", padx=24, pady=8)

        # Scanner folder
        row1 = tk.Frame(input_frame, bg=COLORS["bg"])
        row1.pack(fill="x", padx=8, pady=8)
        tk.Label(row1, text="Scanner Folder:", bg=COLORS["bg"],
                 font=FONTS["body"], fg=COLORS["text_secondary"]).pack(side="left")
        self._folder_var = tk.StringVar(value=str(SCANNER_INPUT_DIR))
        ttk.Entry(row1, textvariable=self._folder_var, width=50).pack(side="left", padx=6)
        ttk.Button(row1, text="Browse…", command=self._browse_folder).pack(side="left")

        # File list
        row2 = tk.Frame(input_frame, bg=COLORS["bg"])
        row2.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(row2, text="📂 Add Files…",
                   command=self._add_files).pack(side="left", padx=4)
        ttk.Button(row2, text="📂 Add Folder…",
                   command=self._add_folder).pack(side="left", padx=4)
        ttk.Button(row2, text="🗑️ Clear List",
                   command=self._clear_files).pack(side="left", padx=4)
        ttk.Button(row2, text="Reset Scan Data",
                   command=self._reset_scan_data).pack(side="right", padx=4)
        ttk.Button(row2, text="▶  Start Processing",
                   command=self._start_processing, style="Accent.TButton").pack(side="right", padx=4)

        self._file_listbox = tk.Listbox(input_frame, height=5, font=FONTS["mono"],
                                         bg="#1A1D2E", fg="#A8D8A8", selectbackground=COLORS["accent"],
                                         relief="flat", activestyle="none")
        self._file_listbox.pack(fill="x", padx=8, pady=(0, 8))

        # Progress
        prog_frame = tk.LabelFrame(self, text="  Processing Progress  ", bg=COLORS["bg"],
                                    font=FONTS["heading"], fg=COLORS["text_primary"],
                                    bd=1, relief="groove")
        prog_frame.pack(fill="x", padx=24, pady=8)

        grid = tk.Frame(prog_frame, bg=COLORS["bg"])
        grid.pack(fill="x", padx=8, pady=8)
        self._stat_labels = {}
        stat_defs = [("Current Batch:", "batch"), ("Total Pages:", "total"),
                     ("Processed:", "processed"), ("Needs Review:", "review"),
                     ("Failed:", "failed")]
        for col_idx, (lbl, key) in enumerate(stat_defs):
            tk.Label(grid, text=lbl, bg=COLORS["bg"], font=FONTS["small"],
                     fg=COLORS["text_secondary"]).grid(row=0, column=col_idx*2, sticky="w", padx=4)
            var = tk.StringVar(value="—")
            self._stat_labels[key] = var
            tk.Label(grid, textvariable=var, bg=COLORS["bg"], font=FONTS["heading"],
                     fg=COLORS["text_primary"]).grid(row=0, column=col_idx*2+1, sticky="w", padx=4)

        self._progress_bar = ttk.Progressbar(prog_frame, mode="determinate", length=400)
        self._progress_bar.pack(fill="x", padx=8, pady=(0, 8))

        # Log output
        log_frame = tk.LabelFrame(self, text="  Processing Log  ", bg=COLORS["bg"],
                                   font=FONTS["heading"], fg=COLORS["text_primary"],
                                   bd=1, relief="groove")
        log_frame.pack(fill="both", expand=True, padx=24, pady=8)

        self._log_text = tk.Text(log_frame, state="disabled", font=FONTS["mono"],
                                  bg="#0D1117", fg="#C9D1D9", relief="flat",
                                  padx=8, pady=4)
        self._log_text.pack(fill="both", expand=True, padx=8, pady=8)
        log_sb = ttk.Scrollbar(log_frame, orient="vertical", command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_sb.set)

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select Scanner Input Folder",
                                     initialdir=dialog_dir(SCANS_DIR))
        if path:
            self._folder_var.set(path)

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Scan Files",
            initialdir=dialog_dir(SCANS_DIR),
            filetypes=[
                ("Supported Files", "*.pdf *.png *.jpg *.jpeg *.tiff *.tif"),
                ("All Files", "*.*")
            ]
        )
        for p in paths:
            if p not in self._file_listbox.get(0, "end"):
                self._file_listbox.insert("end", p)

    def _add_folder(self):
        path = filedialog.askdirectory(title="Select Folder with Scan Files",
                                     initialdir=dialog_dir(SCANS_DIR))
        if not path:
            return
        exts = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}
        for f in sorted(Path(path).iterdir()):
            if f.is_file() and f.suffix.lower() in exts:
                if str(f) not in self._file_listbox.get(0, "end"):
                    self._file_listbox.insert("end", str(f))

    def _clear_files(self):
        self._file_listbox.delete(0, "end")

    def _reset_scan_data(self):
        if self._processing:
            messagebox.showinfo("Processing", "Wait for the current scan batch to finish before resetting scan data.")
            return

        confirmed = messagebox.askyesno(
            "Reset Scan Data",
            "Delete all saved results, scan batches, extracted pages, annotated images, failed files, and result exports?\n\n"
            "This also clears the current file list. Exams, students, barcodes, answer keys, sticker PDFs, and source scan PDFs are kept."
        )
        if not confirmed:
            return

        data_root = DATA_DIR.resolve()
        cleanup_dirs = (
            SCANS_DIR / "extracted_pages",
            PROCESSED_DIR / "annotated",
            FAILED_DIR,
            EXPORTS_DIR,
        )
        try:
            for directory in cleanup_dirs:
                resolved = directory.resolve()
                if not resolved.is_relative_to(data_root):
                    raise ValueError(f"Refusing to clear a folder outside the data directory: {resolved}")
                directory.mkdir(parents=True, exist_ok=True)

            locked_items = []
            for directory in cleanup_dirs:
                locked_items.extend(self._clear_directory_contents(directory))

            deleted = self.sm.results.clear_scan_data()
            self._clear_files()
            self._progress_bar.config(value=0, maximum=1)
            for value in self._stat_labels.values():
                value.set("—")
            self._log_text.config(state="normal")
            self._log_text.delete("1.0", "end")
            self._log_text.config(state="disabled")
            summary = (
                "Scan data cleared. Exams, students, barcode mappings, and answer keys were preserved.\n\n"
                f"Deleted {deleted['results']} results, {deleted['scan_batches']} batches, and "
                f"{deleted['scanned_documents']} scanned pages."
            )
            if locked_items:
                remaining = "\n".join(str(path) for path in locked_items[:8])
                if len(locked_items) > 8:
                    remaining += f"\n…and {len(locked_items) - 8} more"
                messagebox.showwarning(
                    "Reset Mostly Complete",
                    f"{summary}\n\nThese files are still open or locked. Close them and run reset again to remove them:\n{remaining}"
                )
            else:
                messagebox.showinfo("Reset Complete", summary)
        except Exception as e:
            messagebox.showerror("Reset Failed", f"Could not finish clearing scan data:\n{e}")

    @classmethod
    def _clear_directory_contents(cls, directory: Path) -> List[Path]:
        locked = []
        for item in directory.iterdir():
            if item.is_dir() and not item.is_symlink():
                locked.extend(cls._clear_directory_contents(item))
                try:
                    item.rmdir()
                except OSError:
                    locked.append(item)
            else:
                try:
                    item.unlink()
                except OSError:
                    locked.append(item)
        return locked

    def _start_processing(self):
        if self._processing:
            messagebox.showinfo("Processing", "Already processing. Please wait.")
            return
        files = list(self._file_listbox.get(0, "end"))
        if not files:
            messagebox.showwarning("No Files", "Please add scan files or a folder first.")
            return

        self._processing = True
        self._progress_bar.config(value=0, maximum=len(files))
        self._log("=== Starting batch processing ===")

        thread = threading.Thread(target=self._process_thread, args=(files,), daemon=True)
        thread.start()

    def _process_thread(self, files: List[str]):
        for idx, file_path in enumerate(files):
            path = Path(file_path)
            self._queue.put(("log", f"Processing: {path.name}"))
            self._queue.put(("stat", {"batch": path.name}))
            try:
                batch, results = self.processor.process_file(path)
                n_review = sum(1 for r in results if r and r.review_status == "Pending Review")
                self._queue.put(("log",
                    f"  → {batch.total_pages} pages | {len(results)} results | {n_review} need review"))
                self._queue.put(("stat", {
                    "total": batch.total_pages,
                    "processed": len(results),
                    "review": n_review,
                    "failed": batch.total_pages - len(results)
                }))
            except Exception as e:
                self._queue.put(("log", f"  ❌ ERROR: {str(e)}"))

            self._queue.put(("progress", idx + 1))

        self._queue.put(("done", None))

    def _poll_queue(self):
        try:
            while True:
                msg_type, payload = self._queue.get_nowait()
                if msg_type == "log":
                    self._log(payload)
                elif msg_type == "stat":
                    for k, v in payload.items():
                        if k in self._stat_labels:
                            self._stat_labels[k].set(str(v))
                elif msg_type == "progress":
                    self._progress_bar.config(value=payload)
                elif msg_type == "done":
                    self._processing = False
                    self._log("=== Processing complete ===")
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _log(self, message: str):
        self._log_text.config(state="normal")
        self._log_text.insert("end", message + "\n")
        self._log_text.see("end")
        self._log_text.config(state="disabled")

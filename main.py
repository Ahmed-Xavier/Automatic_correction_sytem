"""
Main entry point for the Examination Correction System.
"""
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.repositories import ServiceManager
from gui.main_window import MainWindow

def main():
    # Initialize all services (creates DB and directories if needed)
    service_manager = ServiceManager()
    # Launch main window
    app = MainWindow(service_manager)
    app.run()

if __name__ == "__main__":
    main()

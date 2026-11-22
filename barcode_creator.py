"""
Entry point for Companion App A — Student Barcode Creator.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from companion_apps.barcode_creator.app import BarCodeCreatorApp
if __name__ == "__main__":
    BarCodeCreatorApp().run()

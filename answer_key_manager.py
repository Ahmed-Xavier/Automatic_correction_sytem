"""
Entry point for Companion App B — Answer Key Manager.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from companion_apps.answer_key_manager.app import AnswerKeyManagerApp
if __name__ == "__main__":
    AnswerKeyManagerApp().run()

"""
FaceMilling - CNC Facemilling Program Generator
Main entry point for the application.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path so imports work
# Support both dev environment and PyInstaller bundled exe
if getattr(sys, 'frozen', False):
    # Running as compiled exe (PyInstaller)
    project_root = Path(sys.executable).parent
else:
    # Running as Python script
    project_root = Path(__file__).parent

sys.path.insert(0, str(project_root))

from ui.main_window import run_application


if __name__ == "__main__":
    run_application()

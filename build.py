"""
Build script to create a portable EXE using PyInstaller.

Usage:
    python build.py

This will create an executable in the 'dist' directory.
"""

import subprocess
import sys
import os
from pathlib import Path


def build_exe():
    """Build the FaceMilling application to a portable EXE."""
    
    print("Building FaceMilling Application...")
    print("=" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
    except ImportError:
        print("✗ PyInstaller is not installed")
        print("  Install it with: pip install pyinstaller")
        sys.exit(1)
    
    # Build command
    build_cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window
        "--name", "FaceMilling",        # Application name
        "--add-data", "config.json:.",  # Include config file
        "--add-data", "assets:assets",  # Include assets
        "main.py"
    ]
    
    print(f"\nRunning: {' '.join(build_cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(build_cmd, check=True)
        
        print("-" * 60)
        print("✓ Build completed successfully!")
        print("\nThe executable has been created in the 'dist' directory:")
        print("  dist/FaceMilling.exe")
        print("\nYou can now distribute this file separately from the source code.")
        print("The config.json and assets folders can be included for customization.")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed with error code: {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()

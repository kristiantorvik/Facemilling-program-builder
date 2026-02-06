"""
Illustration display system for FaceMilling application.
Handles displaying images for input fields.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional
import os
import sys

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def get_images_dir() -> Path:
    """
    Get the path to the images directory, supporting both dev and exe environments.
    
    Returns:
        Path to the images directory
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled exe (PyInstaller)
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            return Path(meipass) / "assets" / "images"
        # Fallback to assets next to exe
        return Path(sys.executable).parent / "assets" / "images"
    else:
        # Running as Python script
        return Path(__file__).parent.parent / "assets" / "images"


class IllustrationWindow:
    """Displays an illustration in a separate window."""
    
    def __init__(self, parent: tk.Widget, images_dir: str = None):
        """
        Initialize the illustration window.
        
        Args:
            parent: Parent widget
            images_dir: Directory containing illustration images (optional)
        """
        self.parent = parent
        self.images_dir = Path(images_dir) if images_dir else get_images_dir()
        self.window: Optional[tk.Toplevel] = None
        self.current_image: Optional[ImageTk.PhotoImage] = None
        self.image_label: Optional[tk.Label] = None
    
    def show_illustration(self, image_name: str, title: str = "Illustration") -> None:
        """
        Display an illustration image.
        
        Args:
            image_name: Name of the image file (e.g., "X-pos.png")
            title: Title for the window
        """
        if not PIL_AVAILABLE:
            return
        
        image_path = self.images_dir / image_name
        
        if not image_path.exists():
            return
        
        # Create or bring to front the illustration window
        if self.window is None or not self.window.winfo_exists():
            self._create_window()
        
        # Load and display the image
        try:
            img = Image.open(image_path)
            
            # Resize image to fit window (max 300x200)
            img.thumbnail((300, 200), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image = ImageTk.PhotoImage(img)
            
            # Update label with new image
            if self.image_label:
                self.image_label.config(image=self.current_image)
            
            # Update window title
            self.window.title(f"Illustration - {title}")
            self.window.lift()
            
        except Exception as e:
            pass
    
    def _create_window(self) -> None:
        """Create the illustration display window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Illustration")
        self.window.geometry("320x240")
        self.window.resizable(False, False)
        
        # Create label for image
        self.image_label = tk.Label(self.window, bg="white", padx=10, pady=10)
        self.image_label.pack(fill=tk.BOTH, expand=True)
    
    def close(self) -> None:
        """Close the illustration window."""
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None


class ImageMapper:
    """Maps field names to image filenames."""
    
    # Mapping of field label text to image filename
    FIELD_IMAGE_MAP = {
        "Position Reference": "Table.png",  # Will be updated to G5x.png if G55/G56/G57 selected
        "X Position:": "X-pos.png",
        "Y Position:": "Y-pos.png",
        "X Size:": "X-size.png",
        "Y Size:": "Y-size.png",
        "Z Size:": "Z-size.png",
        "Finished Z Height:": "Finished-Z.png",
        "Stock Offset:": "Stock_offset.png",
        "Tool Number:": "ToolNr.png",
        "Tool Diameter:": "Tool_diameter.png",
        "Depth of Cut:": "Depth_of_cut.png",
        "Leave for Finishing:": "Finish_allowance.png",
        "Width of Cut:": "Width_of_cut.png",
        "RPM:": "RPM.png",
        "Feedrate:": "Feedrate.png",
        "Coolant": "Table.png",  # Generic image for coolant selection
    }
    
    @classmethod
    def get_image_for_field(cls, field_name: str) -> Optional[str]:
        """
        Get the image filename for a field.
        
        Args:
            field_name: The field label text
            
        Returns:
            Image filename or None if not found
        """
        return cls.FIELD_IMAGE_MAP.get(field_name)
    
    @classmethod
    def get_title_for_field(cls, field_name: str) -> str:
        """
        Get a display title for a field.
        
        Args:
            field_name: The field label text
            
        Returns:
            Display title
        """
        # Remove trailing colon and (units) if present
        title = field_name.rstrip(":")
        if "(" in title:
            title = title.split("(")[0].strip()
        return title

"""
Custom TKinter widgets for numeric input fields with validation.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class NumericInputFrame(tk.Frame):
    """
    A custom frame containing a label, text entry, and input validation.
    Handles both float and integer inputs.
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        label_text: str,
        input_type: str = "float",
        on_focus_callback: Optional[Callable] = None,
        default_value: str = "",
        width: int = 15,
        **kwargs
    ):
        """
        Initialize the NumericInputFrame.
        
        Args:
            parent: Parent widget
            label_text: Text for the label
            input_type: "float" or "int"
            on_focus_callback: Function to call when field gets focus
            default_value: Default value for the entry
            width: Width of the entry box
        """
        super().__init__(parent, **kwargs)
        
        self.label_text = label_text
        self.input_type = input_type
        self.on_focus_callback = on_focus_callback
        
        # Create label
        self.label = tk.Label(self, text=label_text, font=("Arial", 9))
        self.label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Create entry with validation
        vcmd = self.register(self._validate_input)
        self.entry = tk.Entry(
            self,
            width=width,
            validate="key",
            validatecommand=(vcmd, "%S", "%P"),
            font=("Arial", 9)
        )
        self.entry.pack(side=tk.LEFT, padx=3)
        
        # Bind focus events
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        
        # Set default value if provided
        if default_value:
            self.set_value(default_value)
    
    def _validate_input(self, char: str, new_value: str) -> bool:
        """
        Validate input based on input type.
        
        Args:
            char: The character being inserted
            new_value: The new complete value of the entry
            
        Returns:
            True if valid, False otherwise
        """
        # Allow empty string
        if new_value == "":
            return True
        
        if self.input_type == "float":
            try:
                if new_value.count(".") > 1:
                    return False
                if new_value.count("-") > 1:
                    return False
                if new_value != "" and new_value != "-" and new_value != ".":
                    float(new_value)
                return True
            except ValueError:
                return False
        
        elif self.input_type == "int":
            try:
                if new_value.count("-") > 1:
                    return False
                if new_value != "" and new_value != "-":
                    int(new_value)
                return True
            except ValueError:
                return False
        
        return True
    
    def _on_focus_in(self, event):
        """Handle focus in event."""
        if self.on_focus_callback:
            # Call the callback with the label text as parameter
            self.on_focus_callback(self.label_text)
    
    def _on_focus_out(self, event):
        """Handle focus out event."""
        pass
    
    def get_value(self):
        """
        Get the value from the entry.
        
        Returns:
            Converted value (float or int), or None if empty
        """
        value = self.entry.get().strip()
        
        if value == "":
            return None
        
        try:
            if self.input_type == "float":
                return float(value)
            else:
                return int(value)
        except ValueError:
            return None
    
    def set_value(self, value):
        """Set the value in the entry."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(value))
    
    def get_raw_value(self) -> str:
        """Get the raw string value from the entry."""
        return self.entry.get()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the input control visually and functionally."""
        state = 'normal' if enabled else 'disabled'
        fg = 'black' if enabled else 'gray'
        try:
            self.entry.config(state=state)
            self.label.config(fg=fg)
        except Exception:
            pass

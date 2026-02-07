"""
Main UI window for FaceMilling application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional
from pathlib import Path
import sys

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    ImageTk = None

from ui.widgets import NumericInputFrame
from ui.illustrations import IllustrationWindow, ImageMapper
from ui import statusbar
from config import get_config_manager
from gcode.generator import GCodeGenerator

from version import __version__


def get_asset_path(filename: str) -> Path:
    """
    Get the full path to an asset file, supporting both dev and exe environments.
    """
    # Determine assets root depending on dev or frozen (exe) mode
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            assets_root = Path(meipass) / "assets"
        else:
            assets_root = Path(sys.executable).parent / "assets"
    else:
        assets_root = Path(__file__).parent.parent / "assets"

    # Prefer a file in the assets root (useful for icon files), otherwise fall back to assets/images
    candidate_root = assets_root / filename
    if candidate_root.exists():
        return candidate_root

    images_dir = assets_root / "images"
    return images_dir / filename


class MainWindow:
    """Main application window."""

    def __init__(self, root: tk.Tk):
        """
        Initialize the main window.
        """
        self.root = root
        self.root.title("FaceMilling - CNC Program Generator")
        self.root.geometry("1000x900")

        # Set window icon (optional)
        try:
            # Try multiple common icon filenames
            for ico_name in ("Facemiller.ico", "icon.ico", "facemiller.ico"):
                icon_path = get_asset_path(ico_name)
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
                    break
        except Exception:
            pass

        # Load configuration
        self.config_manager = get_config_manager()
        config = self.config_manager.get_all()

        # Current illustration display
        self.current_illustration = None

        # Create UI
        self.create_ui()

        # Load default values
        try:
            self.load_defaults()
        except Exception:
            pass

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self) -> None:
        """Handle application closing."""
        self.root.destroy()

    def create_illustration_panel(self, parent: tk.Widget) -> None:
        """Create the illustration display panel on the right side."""
        right_frame = ttk.LabelFrame(parent, text="Illustration", padding=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.config(width=320, height=240)
        right_frame.pack_propagate(False)

        # Create label for image
        self.image_label = tk.Label(
            right_frame,
            bg="white",
            fg="gray",
            text="Select a field to view illustration",
            font=("Arial", 10),
            wraplength=300
        )
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Store reference for PhotoImage
        self.current_photo_image: Optional[ImageTk.PhotoImage] = None

    def create_ui(self) -> None:
        """Create the main UI layout."""
        # Main container with two columns: form (left) and image (right)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left side: non-scrollable form
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Create form sections directly in left_frame (non-scrollable)
        form_frame = ttk.Frame(left_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)

        self.create_position_section(form_frame)
        self.create_stock_section(form_frame)
        self.create_roughing_section(form_frame)
        self.create_finishing_section(form_frame)

        # Create button frame at bottom of form
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Right side: illustration display panel
        self.create_illustration_panel(main_frame)

        # POST PROGRAM button
        post_button = tk.Button(
            button_frame,
            text="POST PROGRAM",
            command=self.post_program,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10
        )
        post_button.pack(side=tk.LEFT, padx=5)

        # Reset button
        reset_button = tk.Button(
            button_frame,
            text="Reset",
            command=self.reset_form,
            bg="#2196F3",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10
        )
        reset_button.pack(side=tk.LEFT, padx=5)

        # Status bar (single-line feedback across bottom)
        status_frame = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Left side: status message
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, anchor="w", padx=6)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Right side: version label
        version_label = tk.Label(status_frame, text=f"v{__version__}", anchor="e", padx=6, fg="gray")
        version_label.pack(side=tk.RIGHT)

        # Register status label for global access via ui.statusbar
        try:
            statusbar.register(self.status_label)
        except Exception:
            pass

    def _create_aligned_input(self, parent: tk.Widget, row: int, label_text: str, 
                              input_type: str = "float", default_value: str = "0.0") -> tk.Entry:
        """
        Create a properly aligned label and entry field using grid.
        """
        label = tk.Label(parent, text=label_text, font=("Arial", 9), width=20, anchor="w")
        label.grid(row=row, column=0, sticky=tk.W, padx=(0, 8), pady=2)
        entry = tk.Entry(parent, font=("Arial", 9), width=15)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=2)
        if default_value:
            entry.insert(0, default_value)
        entry.bind("<FocusIn>", lambda e: self.display_illustration(label_text))
        return entry

    def _get_selected_coolants(self) -> dict:
        coolant_options = self.config_manager.get_section("coolant_options")
        selected_coolants = {}
        for coolant_name, var in self.coolant_vars.items():
            if var.get():
                selected_coolants[coolant_name] = coolant_options[coolant_name]
        return selected_coolants

    def create_position_section(self, parent: tk.Widget) -> None:
        frame = tk.LabelFrame(parent, text="Position", font=("Arial", 11, "bold"), padx=8, pady=6)
        frame.pack(fill=tk.X, pady=6)
        self.position_frame = frame
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)
        reference_frame = tk.Frame(frame)
        reference_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=3)
        tk.Label(reference_frame, text="Reference:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 8))
        self.position_reference = tk.StringVar(value="Table")
        for ref in ["Table", "G55", "G56", "G57"]:
            tk.Radiobutton(reference_frame, text=ref, variable=self.position_reference, value=ref, command=lambda r=ref: self._on_reference_change(r)).pack(side=tk.LEFT, padx=5)
        self.position_x = self._create_aligned_input(frame, 1, "X Position:", "float", "0.0")
        self.position_y = self._create_aligned_input(frame, 2, "Y Position:", "float", "0.0")

    def create_stock_section(self, parent: tk.Widget) -> None:
        frame = tk.LabelFrame(parent, text="Stock", font=("Arial", 11, "bold"), padx=8, pady=6)
        frame.pack(fill=tk.X, pady=6)
        self.stock_frame = frame
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)
        row = 0
        self.stock_x = self._create_aligned_input(frame, row, "X Size:", "float", "100.0")
        row += 1
        self.stock_y = self._create_aligned_input(frame, row, "Y Size:", "float", "100.0")
        row += 1
        self.stock_z = self._create_aligned_input(frame, row, "Z Size:", "float", "50.0")
        row += 1
        self.stock_finished_z = self._create_aligned_input(frame, row, "Finished Z Height:", "float", "10.0")
        row += 1
        self.stock_offset = self._create_aligned_input(frame, row, "Stock Offset:", "int", "0")
    
    def create_roughing_section(self, parent: tk.Widget) -> None:
        """Create Roughing input section."""
        frame = tk.LabelFrame(parent, text="Roughing", font=("Arial", 11, "bold"), padx=8, pady=6)
        frame.pack(fill=tk.X, pady=6)
        
        self.roughing_frame = frame
        
        # Configure two-column grid: labels (fixed width) and entries (expandable)
        frame.columnconfigure(0, weight=0)  # Label column - fixed width
        frame.columnconfigure(1, weight=1)  # Entry column - expandable
        
        row = 0
        
        # Tool Number
        self.roughing_tool = self._create_aligned_input(frame, row, "Tool Number:", "int", "1")
        row += 1
        
        # Tool Diameter
        self.roughing_diameter = self._create_aligned_input(frame, row, "Tool Diameter:", "float", "10.0")
        row += 1
        
        # Depth of Cut
        self.roughing_depth = self._create_aligned_input(frame, row, "Depth of Cut:", "float", "5.0")
        row += 1
        
        # Leave for Finishing
        self.roughing_leave = self._create_aligned_input(frame, row, "Leave for Finishing:", "float", "1.0")
        self.roughing_leave.bind("<KeyRelease>", lambda e: self._on_leave_for_finishing_change())
        row += 1
        
        # Width of Cut
        self.roughing_width = self._create_aligned_input(frame, row, "Width of Cut:", "float", "20.0")
        row += 1
        
        # RPM
        self.roughing_rpm = self._create_aligned_input(frame, row, "RPM:", "int", "5000")
        row += 1
        
        # Feedrate
        self.roughing_feedrate = self._create_aligned_input(frame, row, "Feedrate:", "int", "1000")

        # Coolant options (common area) - small section below roughing
        self.create_coolant_section(parent)
    
    def create_coolant_section(self, parent: tk.Widget) -> None:
        """Create Coolant selection section with checkboxes."""
        coolant_frame = tk.LabelFrame(parent, text="Coolant Options", font=("Arial", 11, "bold"), padx=8, pady=6)
        coolant_frame.pack(fill=tk.X, pady=6)
        
        # Get coolant options from config
        coolant_options = self.config_manager.get_section("coolant_options")
        
        # Store coolant checkboxes as BooleanVars
        self.coolant_vars = {}
        for coolant_name in sorted(coolant_options.keys()):
            self.coolant_vars[coolant_name] = tk.BooleanVar(value=False)
            tk.Checkbutton(
                coolant_frame,
                text=coolant_name,
                variable=self.coolant_vars[coolant_name]
            ).pack(side=tk.LEFT, padx=10, pady=2)
    
    def create_finishing_section(self, parent: tk.Widget) -> None:
        """Create Finishing input section."""
        frame = tk.LabelFrame(parent, text="Finishing", font=("Arial", 11, "bold"), padx=8, pady=6)
        frame.pack(fill=tk.X, pady=6)
        
        self.finishing_frame = frame
        
        # Configure two-column grid: labels (fixed width) and entries (expandable)
        frame.columnconfigure(0, weight=0)  # Label column - fixed width
        frame.columnconfigure(1, weight=1)  # Entry column - expandable
        
        row = 0
        
        # Tool Number
        self.finishing_tool = self._create_aligned_input(frame, row, "Tool Number:", "int", "2")
        row += 1
        
        # Tool Diameter
        self.finishing_diameter = self._create_aligned_input(frame, row, "Tool Diameter:", "float", "10.0")
        row += 1
        
        # Width of Cut
        self.finishing_width = self._create_aligned_input(frame, row, "Width of Cut:", "float", "20.0")
        row += 1
        
        # RPM
        self.finishing_rpm = self._create_aligned_input(frame, row, "RPM:", "int", "8000")
        row += 1
        
        # Feedrate
        self.finishing_feedrate = self._create_aligned_input(frame, row, "Feedrate:", "int", "1500")
        row += 1

        # Only finish cut checkbox - disable roughing when checked
        opts_frame = tk.Frame(frame)
        opts_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=4)
        self.only_finish_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="Only finish cut", variable=self.only_finish_var, command=self._on_only_finish_toggle).pack(side=tk.LEFT)
    
    def _on_field_focus(self, field_name: str):
        """
        Callback for field focus events.
        
        Args:
            field_name: Name of the focused field
        """
        self.display_illustration(field_name)
    
    def _on_reference_change(self, ref_type: str):
        """
        Handle reference radiobutton change.
        
        Args:
            ref_type: The selected reference type
        """
        # Show appropriate image based on selection
        if ref_type == "Table":
            self.display_illustration("Position Reference")
        else:
            # For G55, G56, G57, show the G5x image
            image_name = "G5x.png"
            image_path = get_asset_path(image_name)
            
            if not PIL_AVAILABLE or not image_path.exists():
                self.image_label.config(text="G-code Reference Position", fg="black")
                return
            
            try:
                img = Image.open(image_path)
                img.thumbnail((300, 200), Image.Resampling.LANCZOS)
                self.current_photo_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.current_photo_image, text="")
            except Exception as e:
                self.image_label.config(text=f"Error: {str(e)}", fg="red")

    def _on_only_finish_toggle(self):
        """Enable or disable roughing inputs based on Only finish checkbox."""
        enabled = not self.only_finish_var.get()
        rough_widgets = [
            self.roughing_tool,
            self.roughing_diameter,
            self.roughing_depth,
            self.roughing_leave,
            self.roughing_width,
            self.roughing_rpm,
            self.roughing_feedrate,
        ]
        for w in rough_widgets:
            try:
                w.config(state=tk.NORMAL if enabled else tk.DISABLED)
            except Exception:
                pass
    
    def _on_leave_for_finishing_change(self):
        """Enable or disable finishing inputs based on Leave for Finishing value."""
        try:
            value = float(self.roughing_leave.get())
        except Exception:
            return  # Invalid input, don't change state
        
        enabled = value != 0
        finish_widgets = [
            self.finishing_tool,
            self.finishing_diameter,
            self.finishing_width,
            self.finishing_rpm,
            self.finishing_feedrate,
        ]
        for w in finish_widgets:
            try:
                w.config(state=tk.NORMAL if enabled else tk.DISABLED)
            except Exception:
                pass
    
    def display_illustration(self, field_name: str) -> None:
        """
        Display an illustration based on the focused field.
        
        Args:
            field_name: Name of the focused field
        """
        if not PIL_AVAILABLE:
            return
        
        # Get the image filename from the mapper
        image_name = ImageMapper.get_image_for_field(field_name)
        
        if not image_name:
            return
        
        image_path = get_asset_path(image_name)
        
        if not image_path.exists():
            self.image_label.config(text=f"Image not found:\n{image_name}", fg="red")
            return
        
        try:
            img = Image.open(image_path)
            
            # Resize image to fit panel (max 300x200)
            img.thumbnail((300, 200), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_photo_image = ImageTk.PhotoImage(img)
            
            # Update label with new image
            title = ImageMapper.get_title_for_field(field_name)
            self.image_label.config(image=self.current_photo_image, text="", fg="black")
            
        except Exception as e:
            self.image_label.config(text=f"Error loading image:\n{str(e)}", fg="red")
    
    def load_defaults(self) -> None:
        """Load default values from config."""
        config = self.config_manager.get_all()
        
        # Load from "defaults" section
        defaults = config.get("defaults", {})
        
        # Position
        pos = defaults.get("position", {})
        self.position_reference.set(pos.get("reference", "Table"))
        self.position_x.delete(0, tk.END)
        self.position_x.insert(0, str(pos.get("x", 0.0)))
        self.position_y.delete(0, tk.END)
        self.position_y.insert(0, str(pos.get("y", 0.0)))
        
        # Stock
        stock = defaults.get("stock", {})
        self.stock_x.delete(0, tk.END)
        self.stock_x.insert(0, str(stock.get("x_size", 100.0)))
        self.stock_y.delete(0, tk.END)
        self.stock_y.insert(0, str(stock.get("y_size", 100.0)))
        self.stock_z.delete(0, tk.END)
        self.stock_z.insert(0, str(stock.get("z_size", 50.0)))
        self.stock_finished_z.delete(0, tk.END)
        self.stock_finished_z.insert(0, str(stock.get("finished_z_height", 10.0)))
        
        # Roughing
        rough = defaults.get("roughing", {})
        self.roughing_tool.delete(0, tk.END)
        self.roughing_tool.insert(0, str(rough.get("tool_number", 1)))
        self.roughing_diameter.delete(0, tk.END)
        self.roughing_diameter.insert(0, str(rough.get("tool_diameter", 10.0)))
        self.roughing_depth.delete(0, tk.END)
        self.roughing_depth.insert(0, str(rough.get("depth_of_cut", 5.0)))
        self.roughing_leave.delete(0, tk.END)
        self.roughing_leave.insert(0, str(rough.get("leave_for_finishing", 1.0)))
        self.roughing_width.delete(0, tk.END)
        self.roughing_width.insert(0, str(rough.get("width_of_cut", 20.0)))
        self.roughing_rpm.delete(0, tk.END)
        self.roughing_rpm.insert(0, str(rough.get("rpm", 5000)))
        self.roughing_feedrate.delete(0, tk.END)
        self.roughing_feedrate.insert(0, str(rough.get("feedrate", 1000)))
        
        # Finishing
        finish = defaults.get("finishing", {})
        self.finishing_tool.delete(0, tk.END)
        self.finishing_tool.insert(0, str(finish.get("tool_number", 2)))
        self.finishing_diameter.delete(0, tk.END)
        self.finishing_diameter.insert(0, str(finish.get("tool_diameter", 10.0)))
        self.finishing_width.delete(0, tk.END)
        self.finishing_width.insert(0, str(finish.get("width_of_cut", 20.0)))
        self.finishing_rpm.delete(0, tk.END)
        self.finishing_rpm.insert(0, str(finish.get("rpm", 8000)))
        self.finishing_feedrate.delete(0, tk.END)
        self.finishing_feedrate.insert(0, str(finish.get("feedrate", 1500)))

        # Coolant - reset all checkboxes
        default_coolants = defaults.get("coolant", [])
        for coolant_name, var in self.coolant_vars.items():
            var.set(coolant_name in default_coolants)

        # Stock offset
        stock_defaults = defaults.get("stock", {})
        # if stock_offset exists in defaults use it, otherwise 0
        self.stock_offset.delete(0, tk.END)
        self.stock_offset.insert(0, str(stock_defaults.get("stock_offset", 0)))

        # Only finish cut default and apply initial enabled/disabled state
        self.only_finish_var.set(defaults.get("only_finish", False))
        # Ensure roughing fields reflect the Only finish setting
        try:
            self._on_only_finish_toggle()
        except Exception:
            pass

        # Display default Home image
        home_image = get_asset_path("Home_image.png")
        if PIL_AVAILABLE and home_image.exists():
            try:
                img = Image.open(home_image)
                img.thumbnail((300, 200), Image.Resampling.LANCZOS)
                self.current_photo_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.current_photo_image, text="")
            except Exception:
                self.image_label.config(text="Home image error", fg="red")
        else:
            self.image_label.config(text="Home image not found", fg="gray")
    
    def collect_parameters(self) -> Dict[str, Any]:
        """
        Collect all parameters from input fields.
        
        Returns:
            Dictionary with all parameters organized by section
        """
        def to_float(s: str) -> float:
            try:
                return float(s)
            except (ValueError, TypeError):
                return 0.0
        
        def to_int(s: str) -> int:
            try:
                return int(s)
            except (ValueError, TypeError):
                return 0
        
        parameters = {
            "position": {
                "reference": self.position_reference.get(),
                "x": to_float(self.position_x.get()),
                "y": to_float(self.position_y.get())
            },
            "stock": {
                "x_size": to_float(self.stock_x.get()),
                "y_size": to_float(self.stock_y.get()),
                "z_size": to_float(self.stock_z.get()),
                "finished_z_height": to_float(self.stock_finished_z.get()),
                "stock_offset": to_int(self.stock_offset.get())
            },
            "roughing": {
                "tool_number": to_int(self.roughing_tool.get()),
                "tool_diameter": to_float(self.roughing_diameter.get()),
                "depth_of_cut": to_float(self.roughing_depth.get()),
                "leave_for_finishing": to_float(self.roughing_leave.get()),
                "width_of_cut": to_float(self.roughing_width.get()),
                "rpm": to_int(self.roughing_rpm.get()),
                "feedrate": to_int(self.roughing_feedrate.get())
            },
            "finishing": {
                "tool_number": to_int(self.finishing_tool.get()),
                "tool_diameter": to_float(self.finishing_diameter.get()),
                "width_of_cut": to_float(self.finishing_width.get()),
                "rpm": to_int(self.finishing_rpm.get()),
                "feedrate": to_int(self.finishing_feedrate.get())
            },
            "coolant": self._get_selected_coolants(),
            "only_finish": self.only_finish_var.get(),
            "machine_settings": self.config_manager.get_section("machine_settings")
        }
        
        return parameters
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate input parameters.
        
        Args:
            parameters: Dictionary with all parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for None values (empty inputs) in dictionary sections
        def check_dict(d, section_name):
            if not isinstance(d, dict):
                return True, ""
            for key, value in d.items():
                if value is None:
                    return False, f"Missing value in {section_name}: {key}"
            return True, ""
        
        for section, data in parameters.items():
            # Only validate dict sections (skip coolant, only_finish, machine_settings)
            if section in ["position", "stock", "roughing", "finishing"]:
                is_valid, msg = check_dict(data, section)
                if not is_valid:
                    return is_valid, msg
        
        # Additional validation
        stock = parameters.get("stock", {})
        if stock.get("z_size", 0) <= stock.get("finished_z_height", 0):
            return False, "Z Size must be greater than Finished Z Height"
        
        return True, ""
    
    def post_program(self) -> None:
        """Handle POST PROGRAM button click."""
        try:
            parameters = self.collect_parameters()
            
            # Validate parameters
            is_valid, error_msg = self.validate_parameters(parameters)
            
            if not is_valid:
                statusbar.set_status(f"Validation Error: {error_msg}", level='error')
                return
            
            # Generate G-code
            generator = GCodeGenerator()
            # Set output_dir from config if available
            ms = self.config_manager.get_section("machine_settings")
            out_dir = ms.get("output_path", ".")
            setattr(generator, 'output_dir', out_dir)
            gcode_program = generator.generate_program(parameters)
            
            # Build filename from config
            program_name = ms.get("program_name", "program")
            append_timestamp = ms.get("append_timestamp", True)
            
            if append_timestamp:
                timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{program_name}_{timestamp}"
            else:
                filename = program_name
            
            if generator.save_program(gcode_program, filename):
                statusbar.set_status(f"Program saved: {filename}", level='success', timeout_ms=10000)
            else:
                statusbar.set_status("Failed to save program", level='error')
        except ValueError as e:
            statusbar.set_status(f"Error: {str(e)}", level='error')
        except KeyError as e:
            statusbar.set_status(f"Missing config key: {str(e)}", level='error')
        except Exception as e:
            statusbar.set_status(f"Unexpected error: {str(e)}", level='error')
    
    def reset_form(self) -> None:
        """Reset form to default values."""
        self.load_defaults()
        statusbar.set_status("Form reset to default values", level='info', timeout_ms=5000)


def run_application() -> None:
    """Run the FaceMilling application."""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

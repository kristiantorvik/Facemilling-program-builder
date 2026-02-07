# FaceMilling

A TKinter-based CNC face milling G-code generator for composite materials processing.

## Features

- **Intuitive UI**: Organized input sections with field-specific illustrations
- **Flexible Workflow**: Support for roughing-only, finishing-only, or combined operations
- **Configurable Coolant**: Multiple coolant options with custom M-codes
- **Smart Validation**: Comprehensive input validation before G-code generation
- **Customizable Output**: Configure program naming and timestamp options
- **Portable**: Build to standalone Windows executable

## Quick Start

### Development

```powershell
# Install dependencies
pip install pillow

# Run the application
python main.py
```

### Building Executable

```powershell
# Build with PyInstaller
python build.py
```

The executable will be created in `dist/FaceMilling.exe`.

## Configuration

Settings are stored in `config.json`:

- **Defaults**: Default values for all input fields
- **Machine Settings**: Machine-specific parameters (table reference, clearance height, plunge feedrate, output path)
- **Coolant Options**: Custom coolant types with M-codes
- **Program Naming**: Base name and timestamp options

### Example Config

```json
{
  "machine_settings": {
    "program_name": "facemilling_job",
    "append_timestamp": true,
    "output_path": "./gcode"
  }
}
```

## Workflow

1. **Position**: Set reference coordinate system (Table, G55, G56, G57) and X/Y position
2. **Stock**: Define stock dimensions and finished height
3. **Roughing**: Configure roughing tool, depth of cut, and leave for finishing
   - Set "Leave for Finishing" to 0 to skip finishing operation
4. **Coolant**: Select coolant options (Air, Internal air, Cold air, Oil Mist)
5. **Finishing**: Configure finishing tool and parameters
   - Automatically disabled when "Leave for Finishing" is 0
6. **Post Program**: Generate and save G-code

## Project Structure

```
FaceMilling/
├── main.py                 # Application entry point
├── version.py              # Version constant
├── config.py               # Configuration management
├── config.json             # User configuration
├── build.py                # Build script for PyInstaller
├── ui/                     # User interface
│   ├── main_window.py      # Main application window
│   ├── illustrations.py    # Image display system
│   ├── statusbar.py        # Status bar module
│   └── widgets.py          # Custom widgets
├── gcode/                  # G-code generation
│   ├── generator.py        # G-code generator
│   ├── validator.py        # Input validation
│   └── path_calculator.py  # Spiral path calculation
└── assets/
    ├── images/             # Field illustrations
    └── Facemiller.ico      # Application icon
```

## Notes

- G-code output is validated before generation
- All parameters must be explicitly set (no silent defaults)
- Images and config are bundled in the executable
- External `assets/` folder can override bundled resources

## Version

Current version: **1.0.0**

# FaceMilling - CNC Facemilling Program Generator

A simple Python TKinter application for generating CNC facemilling programs for composite materials processing.

## Project Structure

```
FaceMilling/
├── main.py                 # Main entry point
├── config.py              # Configuration management
├── config.json            # Configuration file (auto-created)
├── create_images.py       # Script to generate dummy images
├── ui/
│   ├── __init__.py
│   ├── widgets.py         # Custom TKinter widgets (NumericInputFrame)
│   └── main_window.py     # Main application window
├── gcode/
│   ├── __init__.py
│   └── generator.py       # G-code generation logic
└── assets/
    └── images/            # Illustration images (auto-created)
```

## Features

- **Simple UI**: Clean TKinter interface with organized input sections
- **Input Validation**: Built-in numeric input validation (float/int)
- **Configuration Management**: Persistent settings saved to config.json
- **Custom Widgets**: Reusable NumericInputFrame widget with label and validation
- **G-code Generation**: Converts parameters to CNC G-code programs
- **Field Illustrations**: Display images based on focused input field
- **Portable**: Can be built to EXE with PyInstaller

## Installation

1. Ensure Python 3.8+ is installed
2. Install required packages:
```bash
pip install pillow
```

3. Run the application:
```bash
python main.py
```

## Usage

### Running the Application

```bash
python main.py
```

### Creating Illustration Images

The application includes a script to generate dummy placeholder images:

```bash
python create_images.py
```

This creates PNG images for each input field in `assets/images/`.

### Input Sections

#### Position
- Reference position (Table, G55, G56, G57)
- X and Y coordinates

#### Stock
- Stock dimensions (X, Y, Z)
- Finished Z height

#### Roughing
- Tool number and strategy
- Depth of cut and leave for finishing
- Width of cut
- RPM and feedrate

#### Finishing
- Tool number and strategy
- Width of cut
- RPM and feedrate

### Posting a Program

1. Fill in all required parameters
2. Click the **POST PROGRAM** button
3. The program will:
   - Display parameters in the terminal
   - Generate G-code
   - Save to file with timestamp (e.g., `program_20260204_143025`)

### Configuration

Configuration is stored in `config.json` with default values for all parameters. Modify this file to change default values, or they will be updated when you adjust values in the UI.

## Building to EXE

To create a portable EXE file using PyInstaller:

```bash
pip install pyinstaller

pyinstaller --onefile --windowed --icon=icon.ico main.py
```

The EXE will be created in the `dist/` directory.

## Customization

### Adding New Input Fields

1. Edit [ui/main_window.py](ui/main_window.py#L1) to add new NumericInputFrame widgets
2. Update [config.py](config.py#L1) DEFAULT_CONFIG dictionary
3. Add corresponding illustration image to `assets/images/`

### Modifying G-code Generation

Edit [gcode/generator.py](gcode/generator.py#L1) to customize the G-code output.

### Changing UI Layout

Edit [ui/main_window.py](ui/main_window.py#L1) to reorganize sections or styling.

## Notes

- All input validation is performed automatically
- Empty fields are validated before posting
- G-code files are saved without extension
- Terminal output shows collected parameters and generated G-code
- Configuration is automatically created on first run

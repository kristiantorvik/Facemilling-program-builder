"""
G-code generator for FaceMilling operations.
Handles conversion of input parameters to CNC G-code programs.
"""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from gcode.validator import InputValidator
from gcode.path_calculator import SpiralPathCalculator


class GCodeGenerator:
    """Generates G-code programs from facemilling parameters."""
    
    def __init__(self):
        """Initialize the G-code generator."""
        pass
    
    def generate_program(self, parameters: Dict[str, Any]) -> str:
        """
        Generate G-code program from input parameters.
        
        Args:
            parameters: Dictionary containing all input parameters
                       organized by section (position, stock, roughing, finishing)
        
        Returns:
            G-code program as string
            
        Raises:
            ValueError: If validation fails
        """
        # Validate all inputs first
        is_valid, error_msg = InputValidator.validate(parameters)
        if not is_valid:
            raise ValueError(f"Validation failed: {error_msg}")
        
        # Create path calculator and generate paths
        calculator = SpiralPathCalculator(parameters)
        
        # For now, build the program with structure
        gcode_output = self._create_header(parameters)
        gcode_output += self._create_program_body(parameters, calculator)
        gcode_output += self._create_footer()
        
        return gcode_output
    
    def _create_header(self, parameters: Dict[str, Any]) -> str:
        """Create the header section of the G-code program."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stock = parameters["stock"]
        position = parameters["position"]
        machine_settings = parameters["machine_settings"]
        
        header = f"""(*******************************)
(======FaceMilling Program======)
(===Date: {timestamp}===)
(*******************************)
(==========Stock Size===========)
(X={stock.get('x_size', 0)}mm, Y={stock.get('y_size', 0)}mm, Z={stock.get('z_size', 0)}mm)
(*******************************)
(======Finished Z: {stock.get('finished_z_height', 0)}mm======)
(*******************************)

"""
        
        # Add position offset block if using Table reference
        if position["reference"] == "Table":
            table_x = machine_settings["table_reference_x"]
            table_y = machine_settings["table_reference_y"]
            table_z = machine_settings["table_reference_z"]
            offset_x = table_x + position["x"]
            offset_y = table_y + position["y"]
            
            header += f"""(Setting G55 according to table offset)
#5241 = {offset_x}
#5242 = {offset_y}
#5243 = {table_z}

"""
            # Initial refrence return
            header += f"G28 G91 Z0\n\n"
        
        return header
    def _create_program_body(self, parameters: Dict[str, Any], calculator: SpiralPathCalculator) -> str:
        """Create the main body of the G-code program."""
        output = ""
        
        # Roughing operation
        if not parameters["only_finish"]:
            output += self._create_roughing_section(parameters, calculator)
        
        # Finishing operation
        output += self._create_finishing_section(parameters, calculator)
        
        return output
    
    def _create_roughing_section(self, parameters: Dict[str, Any], calculator: SpiralPathCalculator) -> str:
        """Create roughing operation section."""
        output = ""
        roughing = parameters["roughing"]
        refrence = parameters["position"]["reference"]

        output += "\nN1 (Roughing)\n"
        output += f"M06 T{roughing['tool_number']}\n"

        if refrence == "Table":
            output += f"G55\n"
        elif refrence == "G55":
            output += f"G55\n"
        elif refrence == "G56":
            output += f"G56\n"
        elif refrence == "G57":
            output += f"G57\n"
        
        output += f"G5.1 Q1 R5\n" # Enable semi-precision contouring mode
        output += f"G0 G90 B0 C0\n" # Initial ensure B & C axes are zeroed
        output += f"M32 (Clamp C)\nM34 (Clamp B)\n"
        output += f"M3 S{roughing['rpm']}\n"

        
        # Calculate spiral passes
        depth_levels = calculator.calculate_spiral_passes(is_roughing=True)

        # Get rapid position and clearance
        rapid_x = depth_levels[0].passes[0][0].x
        rapid_y = depth_levels[0].passes[0][0].y
        clearance = calculator.get_total_clearance_height()
        
        output += f"G0 X{rapid_x} Y{rapid_y}\n"
        output += f"G43 H{roughing['tool_number']} Z{clearance}\n"
        
        # Add coolant ON codes
        coolant_dict = parameters.get("coolant", {})
        for coolant_name, m_codes in coolant_dict.items():
            output += f"M{m_codes['on_code']} (Turn on {coolant_name})\n"
        
        
        for level in depth_levels:
            output += f"(Depth: {level.z_depth}mm)\n"
            for pass_num, pass_points in enumerate(level.passes):
                for i, point in enumerate(pass_points):
                    if i == 0:
                        output += f"G0 X{point.x} Y{point.y}\n"
                        output += f"G1 Z{point.z} F{point.feed}\n" # Plunge to depth at plunge-feedrate
                    elif i == 1:
                        output += f"G1 X{point.z} Y{point.y} F{point.feed}\n" # First move after plunge, ensure feedrate is set
                    else:
                        if point.arc:
                            output += f"G2 X{point.x} Y{point.y} R{point.arc_radius}\n"
                        else:
                            output += f"G1 X{point.x} Y{point.y}\n"
            output += f"G0 Z{clearance}\n"
        
        # Add coolant OFF codes
        for coolant_name, m_codes in coolant_dict.items():
            output += f"M{m_codes['off_code']} (Turn off {coolant_name})\n"
        
        output += "M5\n"
        output += "G28 G91 Z0\n"
        return output
    
    def _create_finishing_section(self, parameters: Dict[str, Any], calculator: SpiralPathCalculator) -> str:
        """Create finishing operation section."""
        output = ""
        finishing = parameters["finishing"]
        refrence = parameters["position"]["reference"]

        output += "\nN2 (Finishing)\n"
        output += "M1\n"  # Optional stop for tool change
        output += f"M06 T{finishing['tool_number']}\n"
        if refrence == "Table":
            output += f"G55\n"
        elif refrence == "G55":
            output += f"G55\n"
        elif refrence == "G56":
            output += f"G56\n"
        elif refrence == "G57":
            output += f"G57\n"

        output += f"G5.1 Q1 R5\n" # Enable semi-precision contouring mode
        output += f"G0 G90 B0 C0\n" # Initial ensure B & C axes are zeroed
        output += f"M32 (Clamp C)\nM34 (Clamp B)\n"
        output += f"M3 S{finishing['rpm']}\n"
        
        # Calculate spiral passes (single pass for finishing)
        depth_levels = calculator.calculate_spiral_passes(is_roughing=False)

        # Get rapid position and clearance
        rapid_x = depth_levels[0].passes[0][0].x
        rapid_y = depth_levels[0].passes[0][0].y
        clearance = calculator.get_total_clearance_height()
        
        output += f"G0 X{rapid_x} Y{rapid_y}\n"
        output += f"G43 H{finishing['tool_number']} Z{clearance}\n"
        
        # Add coolant ON codes
        coolant_dict = parameters.get("coolant", {})
        for coolant_name, m_codes in coolant_dict.items():
            output += f"M{m_codes['on_code']} (Turn on {coolant_name})\n"
        
        
        for level in depth_levels:
            for pass_num, pass_points in enumerate(level.passes):
                for i, point in enumerate(pass_points):
                    if i == 0:
                        output += f"G0 X{point.x} Y{point.y}\n"
                        output += f"G1 Z{point.z} F{point.feed}\n" # Plunge to depth at plunge-feedrate
                    elif i == 1:
                        output += f"G1 X{point.z} Y{point.y} F{point.feed}\n" # First move after plunge, ensure feedrate is set
                    else:
                        if point.arc:
                            # G2 is clockwise arc
                            output += f"G2 X{point.x} Y{point.y} R{point.arc_radius}\n"
                        else:
                            output += f"G1 X{point.x} Y{point.y}\n"
        
        output += f"G0 Z{clearance}\n"
        
        # Add coolant OFF codes
        for coolant_name, m_codes in coolant_dict.items():
            output += f"M{m_codes['off_code']} (Turn off {coolant_name})\n"
        
        output += "M5\n"
        return output
    
    def _create_footer(self) -> str:
        """Create the footer section of the G-code program."""
        footer = """\nG49
G28 G91 Z0
G28 G91 X0 Y0
M30
%
"""
        return footer
    
    def save_program(self, program: str, filename: str) -> bool:
        """
        Save G-code program to file without extension.
        
        Args:
            program: G-code program string
            filename: Output filename (without extension)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove any extension if provided
            base = filename
            if '.' in filename:
                base = filename.split('.')[0]

            # If output_dir provided as attribute, use it; otherwise current dir
            output_dir = getattr(self, 'output_dir', None)
            if output_dir:
                out_path = Path(output_dir) / base
            else:
                out_path = Path(base)

            # Ensure directory exists
            if out_path.parent and not out_path.parent.exists():
                out_path.parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, 'w') as f:
                f.write(program)

            print(f"G-code program saved to: {out_path}")
            return True
        except Exception as e:
            print(f"Error saving G-code program: {e}")
            return False


def generate_gcode(parameters: Dict[str, Any]) -> str:
    """
    Convenience function to generate G-code.
    
    Args:
        parameters: Dictionary containing all input parameters
        
    Returns:
        G-code program as string
    """
    generator = GCodeGenerator()
    return generator.generate_program(parameters)

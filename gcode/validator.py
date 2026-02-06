"""
Input validation for G-code generation.
Ensures all parameters are valid before processing.
"""

from typing import Dict, Any, Tuple


class InputValidator:
    """Validates all input parameters for G-code generation."""
    
    # Validation ranges
    CORNER_RADIUS_MIN = 1.0
    CORNER_RADIUS_MAX = 25.0
    TOOL_DIAMETER_MIN = 5.0
    TOOL_DIAMETER_MAX = 300.0
    RPM_MIN = 800
    RPM_MAX = 20000
    FEEDRATE_MIN = 100
    FEEDRATE_MAX = 15000
    plunge_feedrate_MIN = 100
    plunge_feedrate_MAX = 15000
    STOCK_SIZE_MIN = 50.0
    STOCK_SIZE_MAX = 1000.0
    CLEARANCE_MIN = 5.0
    CLEARANCE_MAX = 500.0
    DEPTH_CUT_MIN = 0.1
    DEPTH_CUT_MAX = 100.0
    
    @staticmethod
    def validate(parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate all input parameters.
        
        Args:
            parameters: Dictionary containing all parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Require top-level sections to be present
        required_sections = ["position", "stock", "finishing", "machine_settings", "only_finish"]
        for sec in required_sections:
            if sec not in parameters:
                return False, f"Missing top-level section: {sec}"

        # Validate position section
        is_valid, msg = InputValidator._validate_position(parameters["position"])
        if not is_valid:
            return is_valid, msg

        # Validate stock section
        is_valid, msg = InputValidator._validate_stock(parameters["stock"])
        if not is_valid:
            return is_valid, msg

        # Validate roughing section (if not only_finish)
        if not parameters["only_finish"]:
            if "roughing" not in parameters:
                return False, "Missing top-level section: roughing"
            is_valid, msg = InputValidator._validate_roughing(parameters["roughing"])
            if not is_valid:
                return is_valid, msg

        # Validate finishing section
        is_valid, msg = InputValidator._validate_finishing(parameters["finishing"])
        if not is_valid:
            return is_valid, msg

        # Validate machine settings
        is_valid, msg = InputValidator._validate_machine_settings(parameters["machine_settings"])
        if not is_valid:
            return is_valid, msg
        
        # Validate coolant M-codes (must be dict of coolant names to M-codes)
        if "coolant" in parameters:
            coolant_dict = parameters["coolant"]
            if not isinstance(coolant_dict, dict):
                return False, "Coolant must be a dictionary of selected coolants"
            
            for coolant_name, m_codes in coolant_dict.items():
                if not isinstance(m_codes, dict):
                    return False, f"Coolant '{coolant_name}' M-codes must be a dictionary"
                if "on_code" not in m_codes or "off_code" not in m_codes:
                    return False, f"Coolant '{coolant_name}' must have 'on_code' and 'off_code' M-codes"
                
                on_code = m_codes["on_code"]
                off_code = m_codes["off_code"]
                
                if not isinstance(on_code, int) or on_code < 0:
                    return False, f"Coolant '{coolant_name}' on_code must be a positive integer, got {on_code}"
                if not isinstance(off_code, int) or off_code < 0:
                    return False, f"Coolant '{coolant_name}' off_code must be a positive integer, got {off_code}"
        
        # Validate interdependencies
        is_valid, msg = InputValidator._validate_interdependencies(parameters)
        if not is_valid:
            return is_valid, msg
        
        return True, ""
    
    @staticmethod
    def _validate_position(position: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate position parameters."""
        ref = position.get("reference")
        if ref not in ["Table", "G55", "G56", "G57"]:
            return False, "Position reference must be one of: Table, G55, G56, G57"
        
        x = position.get("x")
        y = position.get("y")
        
        if x is None or y is None:
            return False, "Position X and Y are required"
        
        return True, ""
    
    @staticmethod
    def _validate_stock(stock: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate stock parameters."""
        x_size = stock.get("x_size")
        y_size = stock.get("y_size")
        z_size = stock.get("z_size")
        finished_z = stock.get("finished_z_height")
        offset = stock.get("stock_offset")
        
        # Check all required fields exist
        if any(v is None for v in [x_size, y_size, z_size, finished_z, offset]):
            return False, "Stock section missing required fields"
        
        # Check ranges
        if not (InputValidator.STOCK_SIZE_MIN <= x_size <= InputValidator.STOCK_SIZE_MAX):
            return False, f"Stock X size must be between {InputValidator.STOCK_SIZE_MIN} and {InputValidator.STOCK_SIZE_MAX}mm"
        
        if not (InputValidator.STOCK_SIZE_MIN <= y_size <= InputValidator.STOCK_SIZE_MAX):
            return False, f"Stock Y size must be between {InputValidator.STOCK_SIZE_MIN} and {InputValidator.STOCK_SIZE_MAX}mm"
        
        if not (InputValidator.STOCK_SIZE_MIN <= z_size <= InputValidator.STOCK_SIZE_MAX):
            return False, f"Stock Z size must be between {InputValidator.STOCK_SIZE_MIN} and {InputValidator.STOCK_SIZE_MAX}mm"
        
        if not (0 <= finished_z < z_size):
            return False, "Finished Z height must be between 0 and Z size"
        
        if z_size <= finished_z:
            return False, "Z Size must be greater than Finished Z Height"
        
        if offset < 0:
            return False, "Stock offset cannot be negative"
        
        return True, ""
    
    @staticmethod
    def _validate_roughing(roughing: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate roughing parameters."""
        tool_num = roughing.get("tool_number")
        tool_dia = roughing.get("tool_diameter")
        depth = roughing.get("depth_of_cut")
        leave = roughing.get("leave_for_finishing")
        width = roughing.get("width_of_cut")
        rpm = roughing.get("rpm")
        feedrate = roughing.get("feedrate")
        
        # Check all required fields exist
        if any(v is None for v in [tool_num, tool_dia, depth, leave, width, rpm, feedrate]):
            return False, "Roughing section missing required fields"
        
        if tool_num < 0:
            return False, "Roughing tool number must be positive"
        
        if not (InputValidator.TOOL_DIAMETER_MIN <= tool_dia <= InputValidator.TOOL_DIAMETER_MAX):
            return False, f"Roughing tool diameter must be between {InputValidator.TOOL_DIAMETER_MIN} and {InputValidator.TOOL_DIAMETER_MAX}mm"
        
        if not (InputValidator.DEPTH_CUT_MIN <= depth <= InputValidator.DEPTH_CUT_MAX):
            return False, f"Roughing depth of cut must be between {InputValidator.DEPTH_CUT_MIN} and {InputValidator.DEPTH_CUT_MAX}mm"
        
        if leave < 0:
            return False, "Roughing leave for finishing cannot be negative"
        
        if width > tool_dia:
            return False, f"Roughing width of cut must be at most tool diameter ({tool_dia}mm)"
        
        if not (InputValidator.RPM_MIN <= rpm <= InputValidator.RPM_MAX):
            return False, f"Roughing RPM must be between {InputValidator.RPM_MIN} and {InputValidator.RPM_MAX}"
        
        if not (InputValidator.FEEDRATE_MIN <= feedrate <= InputValidator.FEEDRATE_MAX):
            return False, f"Roughing feedrate must be between {InputValidator.FEEDRATE_MIN} and {InputValidator.FEEDRATE_MAX}mm/min"
        
        return True, ""
    
    @staticmethod
    def _validate_finishing(finishing: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate finishing parameters."""
        tool_num = finishing.get("tool_number")
        tool_dia = finishing.get("tool_diameter")
        width = finishing.get("width_of_cut")
        rpm = finishing.get("rpm")
        feedrate = finishing.get("feedrate")
        
        # Check all required fields exist
        if any(v is None for v in [tool_num, tool_dia, width, rpm, feedrate]):
            return False, "Finishing section missing required fields"
        
        if tool_num < 0:
            return False, "Finishing tool number must be positive"
        
        if not (InputValidator.TOOL_DIAMETER_MIN <= tool_dia <= InputValidator.TOOL_DIAMETER_MAX):
            return False, f"Finishing tool diameter must be between {InputValidator.TOOL_DIAMETER_MIN} and {InputValidator.TOOL_DIAMETER_MAX}mm"
        
        if width > tool_dia:
            return False, f"Finishing width of cut must be at most tool diameter ({tool_dia}mm)"
        
        if not (InputValidator.RPM_MIN <= rpm <= InputValidator.RPM_MAX):
            return False, f"Finishing RPM must be between {InputValidator.RPM_MIN} and {InputValidator.RPM_MAX}"
        
        if not (InputValidator.FEEDRATE_MIN <= feedrate <= InputValidator.FEEDRATE_MAX):
            return False, f"Finishing feedrate must be between {InputValidator.FEEDRATE_MIN} and {InputValidator.FEEDRATE_MAX}mm/min"
        
        return True, ""
    
    @staticmethod
    def _validate_machine_settings(settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate machine settings."""
        corner_radius = settings.get("corner_radius")
        clearance = settings.get("clearance_height")
        lead_in = settings.get("lead_in_length")
        plungefeed = settings.get("plunge_feedrate")
        
        if corner_radius is None:
            return False, "Machine settings missing corner_radius"
        
        if not (InputValidator.CORNER_RADIUS_MIN <= corner_radius <= InputValidator.CORNER_RADIUS_MAX):
            return False, f"Corner radius must be between {InputValidator.CORNER_RADIUS_MIN} and {InputValidator.CORNER_RADIUS_MAX}mm"
        
        if clearance is None:
            return False, "Machine settings missing clearance_height"
        
        if not (InputValidator.CLEARANCE_MIN <= clearance <= InputValidator.CLEARANCE_MAX):
            return False, f"Clearance height must be between {InputValidator.CLEARANCE_MIN} and {InputValidator.CLEARANCE_MAX}mm"
        
        if plungefeed is None:
            return False, "Machine settings missing plunge_feedrate"

        try:
            plunge_val = float(plungefeed)
        except Exception:
            return False, "Plunge feed must be a number"

        if not (InputValidator.plunge_feedrate_MIN <= plunge_val <= InputValidator.plunge_feedrate_MAX):
            return False, f"Plunge feed must be between {InputValidator.plunge_feedrate_MIN} and {InputValidator.plunge_feedrate_MAX}mm/min"
        
        if lead_in is None:
            return False, "Machine settings missing lead_in_length"
        
        if lead_in < 0:
            return False, "Lead-in length cannot be negative"
        
        return True, ""
    
    @staticmethod
    def _validate_interdependencies(parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate interdependencies between sections."""
        stock = parameters["stock"]
        roughing = parameters.get("roughing", {})
        only_finish = parameters["only_finish"]

        z_size = stock["z_size"]
        finished_z = stock["finished_z_height"]

        # Only validate roughing interdependencies if not only_finish
        if not only_finish:
            # roughing must exist by earlier validation
            leave = roughing["leave_for_finishing"]

            # Check if depth of cut is reasonable
            material_to_remove = z_size - finished_z - leave
            if material_to_remove <= 0:
                return False, "Leave for finishing must be less than total material to remove"
            
        return True, ""

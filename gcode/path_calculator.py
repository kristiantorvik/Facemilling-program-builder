"""
Spiral milling path calculator.
Computes toolpaths for face milling operations using rectangular spiral strategy.
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class ToolPathPoint:
    """Represents a point in the toolpath."""
    x: float
    y: float
    z: float
    feed: int = 0
    rapid: bool = False
    arc: bool = False  # True if this point is an arc endpoint
    arc_radius: float = 0.0


@dataclass
class DepthLevel:
    """Represents all passes at a particular depth."""
    z_depth: float
    passes: List[List[ToolPathPoint]]


class SpiralPathCalculator:
    """Calculates rectangular spiral milling toolpaths."""
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        Initialize calculator with parameters.
        
        Args:
            parameters: Dictionary containing all parameters
        """
        self.parameters = parameters
        # Sections are required and must be validated by the InputValidator
        self.stock = parameters["stock"]
        self.roughing = parameters["roughing"]
        self.finishing = parameters["finishing"]
        self.machine_settings = parameters["machine_settings"]
        self.position = parameters["position"]
        self.only_finish = parameters["only_finish"]
        
        # Extract position reference and offsets
        self.position_reference = self.position["reference"]
        self.position_x_offset = self.position["x"]
        self.position_y_offset = self.position["y"]
        
        # Extract key values
        # Stock values (required)
        self.stock_x = self.stock["x_size"]
        self.stock_y = self.stock["y_size"]
        self.stock_z = self.stock["z_size"]
        self.finished_z = self.stock["finished_z_height"]
        self.stock_offset = self.stock["stock_offset"]
        
        # Position offsets are applied in _generate_rectangular_spiral for non-Table modes
        # Table mode offsets are handled separately in the G-code header

        # Machine settings (required)
        self.corner_radius = round(self.machine_settings["corner_radius"])
        self.clearance_height = self.machine_settings["clearance_height"]
        self.lead_in = self.machine_settings["lead_in_length"]
        self.last_cut_overlap = self.machine_settings["last_cut_overlap"]
    
    def calculate_spiral_passes(self, is_roughing: bool = True) -> List[DepthLevel]:
        """
        Calculate all spiral passes for roughing or finishing.
        Returns a list of depth levels, each containing complete spiral paths.
        
        Args:
            is_roughing: True for roughing passes, False for finishing
            
        Returns:
            List of DepthLevel objects; each contains z_depth and passes (list of point lists)
        """
        if is_roughing and self.only_finish:
            return []
        
        params = self.roughing if is_roughing else self.finishing
        # Require parameters to be present; validator must ensure these keys exist.
        tool_diameter = params["tool_diameter"]
        tool_radius = tool_diameter / 2.0
        
        if is_roughing:
            depth_of_cut = params["depth_of_cut"]
            leave = params["leave_for_finishing"]
            width_of_cut = params["width_of_cut"]
            start_z = self.stock_z
            end_z = self.finished_z + leave
            feedrate = params["feedrate"]
            plunge_feedrate = self.machine_settings["plunge_feedrate"]
        else:
            leave = 0
            width_of_cut = params["width_of_cut"]
            start_z = self.finished_z + (self.roughing["leave_for_finishing"] if not self.only_finish else 0)
            end_z = self.finished_z
            feedrate = params["feedrate"]
            plunge_feedrate = self.machine_settings["plunge_feedrate"]
            depth_of_cut = start_z - end_z
        
        # Calculate depth levels
        depth_levels = []
        current_z = start_z
        
        while current_z > end_z:
            next_z = max(current_z - depth_of_cut, end_z)
            depth_levels.append(next_z)
            current_z = next_z
        
        # For each depth level, generate complete spiral
        all_spirals = []
        for z_depth in depth_levels:
            spiral_points = self._generate_rectangular_spiral(
                tool_radius, width_of_cut, z_depth, feedrate, plunge_feedrate, is_roughing, last_cut_overlap=self.last_cut_overlap
            )
            # Wrap in DepthLevel with passes as list of point lists
            all_spirals.append(DepthLevel(
                z_depth=z_depth,
                passes=[spiral_points]  # Single spiral is one "pass" containing all points
            ))
        
        return all_spirals
    
    def _generate_rectangular_spiral(
        self,
        tool_radius: float,
        width_of_cut: float,
        z_depth: float,
        feedrate: int,
        plunge_feedrate: int,
        is_roughing: bool,
        last_cut_overlap: float
    ) -> List[ToolPathPoint]:
        """
        Generate a complete rectangular spiral at one depth using simple loop logic.
        Clockwise spiral: UP, RIGHT, DOWN (short), LEFT to next lap, repeat.
        
        Args:
            tool_radius: Tool radius in mm
            width_of_cut: Maximum width of cut per pass (stepover)
            z_depth: Z depth for this spiral
            feedrate: Feed rate for spiral moves
            is_roughing: True for roughing (affects starting position)
            
        Returns:
            List of ToolPathPoints representing the complete spiral
        """
        points = []
        
        # Work area bounds
        x_min = -self.stock_offset
        y_min = -self.stock_offset
        x_max = self.stock_x + self.stock_offset
        y_max = self.stock_y + self.stock_offset
        
        # Stock left to machine
        x_stock_left = x_max - x_min
        y_stock_left = y_max - y_min

        # Apply position offsets for G55/G56/G57 modes
        # Table mode offsets are applied in G-code header, not here
        if self.position_reference != "Table":
            x_min += self.position_x_offset
            y_min += self.position_y_offset
            x_max += self.position_x_offset
            y_max += self.position_y_offset
        
        # Get corner radius
        corner_r = float(self.corner_radius)
        
        # Calculate optimal stepover
        stepover = self._calculate_stepover(x_min, y_min, x_max, y_max, width_of_cut, last_cut_overlap)
        
        # Rapid approach from outside
        start_x = x_max + self.lead_in + tool_radius
        start_y = y_min - tool_radius + stepover
        points.append(ToolPathPoint(
            x=round(start_x, 1), y=round(start_y, 1), z=z_depth,
            feed=plunge_feedrate, rapid=True
        ))
        
        
        # Starting position for first lap
        current_x_min = x_min - tool_radius
        current_y_min = y_min - tool_radius
        current_x_max = x_max + tool_radius
        current_y_max = y_max + tool_radius

        # Feed to bottom-left corner of first lap
        points.append(ToolPathPoint(
            x=round(current_x_min + stepover + corner_r, 1), y=round(current_y_min + stepover, 1), z=z_depth,
            feed=feedrate, rapid=False
        ))

        # Stock update and extend last pass if it is the last cut
        y_stock_left -= stepover
        if y_stock_left < 0:
            points.append(ToolPathPoint(
                x=round(current_x_min + stepover + tool_radius, 1), y=round(current_y_min + stepover, 1), z=z_depth,
                feed=feedrate, rapid=False
            ))
            return points  # finished machining stock
        
        spiral_stage = 1

        while current_x_max - current_x_min > tool_radius * 2 and \
              current_y_max - current_y_min > tool_radius * 2:
            
            # Step inward for next iteration
            current_x_min += stepover
            current_y_min += stepover
            current_x_max -= stepover
            current_y_max -= stepover


            # Arc at bottom-left
            points.append(ToolPathPoint(
                x=round(current_x_min, 1), 
                y=round(current_y_min + corner_r, 1), 
                z=z_depth, feed=feedrate, arc=True, arc_radius=corner_r
            ))
            # ===== UP the left edge =====
            points.append(ToolPathPoint(
                x=round(current_x_min, 1), 
                y=round(current_y_max - corner_r, 1), 
                z=z_depth, feed=feedrate
            ))
            # Stock update and extend last pass if it is the last cut
            x_stock_left -= stepover
            if x_stock_left < 0:
                points.append(ToolPathPoint(
                x=round(current_x_min, 1), 
                y=round(current_y_max + tool_radius, 1), 
                z=z_depth, feed=feedrate
                ))
                break  # finished machining stock


            # Arc at top-left
            points.append(ToolPathPoint(
                x=round(current_x_min + corner_r, 1), 
                y=round(current_y_max, 1), 
                z=z_depth, feed=feedrate, arc=True, arc_radius=corner_r
            ))
            
            # ===== RIGHT across top =====
            points.append(ToolPathPoint(
                x=round(current_x_max - corner_r, 1), 
                y=round(current_y_max, 1), 
                z=z_depth, feed=feedrate
            ))
            # Stock update and extend last pass if it is the last cut
            y_stock_left -= stepover
            if y_stock_left < 0:
                points.append(ToolPathPoint(
                x=round(current_x_max + tool_radius, 1), 
                y=round(current_y_max, 1), 
                z=z_depth, feed=feedrate
                ))
                break  # finished machining stock


            # Arc at top-right
            points.append(ToolPathPoint(
                x=round(current_x_max, 1), 
                y=round(current_y_max - corner_r, 1), 
                z=z_depth, feed=feedrate, arc=True, arc_radius=corner_r
            ))

            # ===== DOWN the right edge ====
            points.append(ToolPathPoint(
                    x=round(current_x_max, 1), 
                    y=round(current_y_min + stepover + corner_r, 1), 
                    z=z_depth, feed=feedrate
            ))
            # Stock update and extend last pass if it is the last cut
            x_stock_left -= stepover
            if x_stock_left < 0:
                points.append(ToolPathPoint(
                x=round(current_x_max, 1), 
                y=round(current_y_min - tool_radius, 1), 
                z=z_depth, feed=feedrate
                ))
                break  # finished machining stock



            # Arc at bottom-right
            points.append(ToolPathPoint(
                x=round(current_x_max - corner_r, 1), 
                y=round(current_y_min + stepover, 1), 
                z=z_depth, feed=feedrate, arc=True, arc_radius=corner_r
            ))
            # ===== ACROSS the bottom =====
            points.append(ToolPathPoint(
                x=round(current_x_min + stepover + corner_r, 1), 
                y=round(current_y_min + stepover, 1), 
                z=z_depth, feed=feedrate
            ))
            # Stock update and extend last pass if it is the last cut
            y_stock_left -= stepover
            if y_stock_left < 0:
                points.append(ToolPathPoint(
                x=round(current_x_min + stepover - tool_radius, 1), 
                y=round(current_y_min + stepover, 1), 
                z=z_depth, feed=feedrate
                ))
                break  # finished machining stock

        return points
    

    def _calculate_stepover(
        self,
        x_min: float,
        y_min: float,
        x_max: float,
        y_max: float,
        width_of_cut: float,
        last_cut_overlap: float
    ) -> float:
        """
        Calculate optimal stepover to not exceed width_of_cut.
        Ensures last cut has proper overlap.
        
        Args:
            x_min, y_min, x_max, y_max: Work area bounds
            width_of_cut: Maximum stepover allowed
            
        Returns:
            Optimal stepover in mm
        """
        width = x_max - x_min
        height = y_max - y_min
        
        # Estimate number of passes needed
        # We want stepover <= width_of_cut
        # And ensure last pass overlaps by last_cut_overlap
        number_of_cuts =   ((min(width, height) + last_cut_overlap) // width_of_cut) + 1
        
        if number_of_cuts == 0:
            stepover = width
        else:
            stepover = ((min(width, height) + last_cut_overlap) / (number_of_cuts ))
        return round(stepover, 1)
    
    
    def get_total_clearance_height(self) -> float:
        """Get absolute clearance height from table."""
        return round(self.stock_z + self.clearance_height, 3)

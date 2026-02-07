"""
Configuration management for FaceMilling application.
Handles loading and saving settings from/to config file.
"""

import json
import sys
import os
from pathlib import Path
from typing import Any, Dict

# Default configuration values
DEFAULT_CONFIG = {
    "defaults": {
        "position": {
            "reference": "Table",  # Options: "Table", "G55", "G56", "G57"
            "x": 0.0,
            "y": 0.0
        },
        "stock": {
            "x_size": 400.0,
            "y_size": 300.0,
            "z_size": 150.0,
            "finished_z_height": 140.0
        },
        "roughing": {
            "tool_number": 55,
            "tool_diameter": 63.0,
            "depth_of_cut": 5.0,
            "leave_for_finishing": 1.0,
            "width_of_cut": 30.0,
            "rpm": 6500,
            "feedrate": 7000
        },
        "finishing": {
            "tool_number": 1,
            "tool_diameter": 80.0,
            "width_of_cut": 53.0,
            "rpm": 4000,
            "feedrate": 3000
        }
    },
    "machine_settings": {
        "table_reference_x": -2600.0,   
        "table_reference_y": -1500.0,
        "table_reference_z": -1171.193,
        "clearance_height": 50.0,
        "plunge_feedrate": 500.0,
        "lead_in_length": 10.0,
        "output_path": ".",
        "corner_radius": 4.0,
        "last_cut_overlap": 10.0,
        "program_name": "FACEMILLING",
        "append_timestamp": True
    },
    "coolant_options": {
        "Air": {
            "on_code": 81,
            "off_code": 82
        },
        "Internal air": {
            "on_code": 79,
            "off_code": 80
        },
        "Cold air": {
            "on_code": 83,
            "off_code": 84
        },
        "Oil Mist": {
            "on_code": 8,
            "off_code": 9
        }
    }
}


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize config manager.
        
        Args:
            config_file: Path to the configuration file
        """
        # Resolve config file path - support both dev and exe environments
        self._bundled_path = None
        if getattr(sys, 'frozen', False):
            # Running as compiled exe (PyInstaller)
            # The bundled config (read-only) lives in sys._MEIPASS
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass:
                self._bundled_path = Path(meipass) / config_file

            # External config lives next to the executable and is writable
            self.config_file = Path(sys.executable).parent / config_file
        else:
            # Running as Python script - look in current directory first
            config_path = Path(config_file)
            if config_path.exists():
                self.config_file = config_path
            else:
                # Fall back to script directory
                self.config_file = Path(__file__).parent / config_file
        
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file or use defaults."""
        # If running frozen, prefer bundled config, but allow external override
        if getattr(sys, 'frozen', False):
            # Load bundled config if available
            if self._bundled_path and self._bundled_path.exists():
                try:
                    with open(self._bundled_path, 'r', encoding='utf-8') as f:
                        self.config = json.load(f)
                except Exception:
                    self.config = DEFAULT_CONFIG.copy()
            else:
                self.config = DEFAULT_CONFIG.copy()

            # If an external config exists next to the exe, use it to override
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        external = json.load(f)
                        # Merge external over loaded config
                        if isinstance(external, dict):
                            self.config.update(external)
                except Exception:
                    # Ignore external load errors and keep bundled/default config
                    pass
            else:
                # No external config yet: write the loaded (bundled/default) config out
                try:
                    self.save_config()
                except Exception:
                    pass
        else:
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        self.config = json.load(f)
                except Exception:
                    self.config = DEFAULT_CONFIG.copy()
            else:
                self.config = DEFAULT_CONFIG.copy()
                self.save_config()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            pass
    
    def get(self, section: str, key: str) -> Any:
        """
        Get a configuration value strictly.

        Raises KeyError if section or key is missing. Validator/UI should ensure
        required config entries exist before use.
        """
        if section not in self.config:
            raise KeyError(f"Config section '{section}' not found")
        if key not in self.config[section]:
            raise KeyError(f"Config key '{key}' not found in section '{section}'")
        return self.config[section][key]
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: New value
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section strictly.

        Raises KeyError if section is missing.
        """
        if section not in self.config:
            raise KeyError(f"Config section '{section}' not found")
        return self.config[section]
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration dictionary."""
        return self.config.copy()


# Global config instance
_config_manager = None


def get_config_manager(config_file: str = "config.json") -> ConfigManager:
    """
    Get or create the global config manager instance.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager

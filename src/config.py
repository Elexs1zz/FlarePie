import json
import os
from datetime import datetime
from typing import Dict, Any, List

class Config:

    def __init__(self, config_file: str = "flarepie_config.json"):
        self.config_file = config_file
        self.default_config = {
            "theme": {
                "primary_color": "#0D1B2A",
                "secondary_color": "#1B263B", 
                "accent_color": "#415A77",
                "text_color": "#E0E1DD",
                "success_color": "#4CAF50",
                "warning_color": "#FF9800",
                "error_color": "#F44336"
            },
            "simulation": {
                "default_fuel_type": "RP1",
                "default_chamber_pressure": 7000000,
                "default_combustion_temp": 3500,
                "default_initial_altitude": 0,
                "default_total_mass": 10000,
                "default_propellant_mass": 8000,
                "default_mass_flow_rate": 250,
                "default_time_step": 0.1,
                "default_reference_area": 1.0,
                "max_simulation_time": 300,
                "real_time_interval": 0.25
            },
            "visualization": {
                "animation_fps": 24,
                "chart_style": "dark_background",
                "enable_3d_plots": True,
                "enable_real_time_metrics": True,
                "auto_save_plots": True
            },
            "export": {
                "default_format": "csv",
                "auto_save_results": True,
                "include_timestamp": True,
                "compression_enabled": False
            },
            "logging": {
                "level": "INFO",
                "file_rotation": True,
                "max_file_size": "10MB",
                "backup_count": 5
            },
            "performance": {
                "multiprocessing_enabled": True,
                "cache_enabled": True,
                "max_cache_size": 100
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return self.default_config
        return self.default_config
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def reset_to_defaults(self):
        self.config = self.default_config.copy()
        self.save_config()

# Global configuration instance
config = Config() 
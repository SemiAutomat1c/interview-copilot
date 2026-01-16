"""
Configuration loader for Interview Copilot.
Handles loading and validating config.json
"""
import json
import os
from typing import Dict, Any


class ConfigLoader:
    """Loads and validates application configuration."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to config.json file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dictionary containing configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is malformed
            ValueError: If required fields are missing
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\\n"
                "Please create config.json from the template."
            )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in {self.config_path}: {e}",
                e.doc, e.pos
            )
        
        # Validate required fields
        self._validate()
        
        return self.config
    
    def _validate(self) -> None:
        """
        Validate that required configuration fields exist.
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            "my_profile",
            "job_context",
            "system_instruction",
            "ollama_settings"
        ]
        
        missing_fields = [
            field for field in required_fields 
            if field not in self.config
        ]
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}"
            )
        
        # Validate ollama_settings
        ollama_required = ["model", "temperature", "max_tokens"]
        ollama_settings = self.config.get("ollama_settings", {})
        
        missing_ollama = [
            field for field in ollama_required
            if field not in ollama_settings
        ]
        
        if missing_ollama:
            raise ValueError(
                f"Missing required ollama_settings fields: {', '.join(missing_ollama)}"
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def get_ollama_settings(self) -> Dict[str, Any]:
        """Get Ollama-specific settings."""
        return self.config.get("ollama_settings", {})
    
    def get_gui_settings(self) -> Dict[str, Any]:
        """Get GUI-specific settings."""
        defaults = {
            "window_width": 800,
            "window_height": 400,
            "font_size": 18,
            "auto_clear_timeout": 30,
            "position": "second_monitor"
        }
        
        user_settings = self.config.get("gui_settings", {})
        defaults.update(user_settings)
        
        return defaults

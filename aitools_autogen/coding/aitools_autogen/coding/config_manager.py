

### Configuration Manager

# The `Configuration Manager` manages user preferences and analyzer configurations, allowing users to customize the analysis process.


# filename: aitools_autogen/coding/config_manager.py

from typing import Dict, Any
import json

class ConfigManager:
    """
    Manages configuration settings for the code analysis tool.
    """
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from a JSON file.

        Returns:
            Dict[str, Any]: The loaded configuration.
        """
        try:
            with open(self.config_path, 'r') as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            return {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key (str): The configuration key.
            default (Any): The default value if the key is not found.

        Returns:
            Any: The configuration value.
        """
        return self.config.get(key, default)
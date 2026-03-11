"""
Configuration Management
Handles saving and loading configuration
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE = 'config/.fabric_converter_config.json'


class ConfigManager:
    def __init__(self):
        os.makedirs('config', exist_ok=True)

    def get_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def save_config(self, config):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise

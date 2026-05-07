"""
Configuration Manager for the Hoymiles Application

Handles loading, validating, and providing access to application configuration
from multiple sources (environment variables, config files, defaults).

Example usage:
    from config_manager import ConfigManager

    config = ConfigManager()
    config.load_from_env()
    config.load_from_file("config.json")

    hoymiles_user = config.get("HOYMILES_USER")
    mqtt_host = config.get("MQTT_HOST", default="localhost")
"""

import json
import logging
import os
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Configuration loading or validation error."""


class ConfigManager:
    """
    Centralized configuration management.

    Supports loading from environment variables, JSON files, and provides
    defaults for common settings.
    """

    # Default configuration values
    DEFAULTS = {
        # Hoymiles API
        "HOYMILES_USER": "",
        "HOYMILES_PASSWORD": "",
        "HOYMILES_PLANT_ID": "",
        "USE_ESTAR": False,
        "EXPERIMENTAL_CUSTOM_API_URLS": False,
        "API_GATEWAY_BASE_URL": "",
        "API_VERSIONED_BASE_URL": "",
        "API_COOKIE_DOMAIN": "",
        "DEBUG_FORCE_API_VERSION": False,
        "DEBUG_API_VERSION": "",
        # MQTT
        "MQTT_HOST": "localhost",
        "MQTT_PORT": 1883,
        "MQTT_USER": "",
        "MQTT_PASS": "",
        "MQTT_TLS": False,
        "MQTT_TLS_PORT": 8883,
        "MQTT_TLS_CERT": "",
        # Application
        "MQTT_PUBLISH_TOPIC": "home/solar",
        "MQTT_DISCOVERY_PREFIX": "homeassistant",
        "MQTT_NODE_ID": "hoymiles",
        "HA_EXPIRE_TIME": 600,
        # Data fetching
        "GET_DATA_INTERVAL": 480,  # seconds
        "HASS_INTERVAL": 300,  # seconds
        "READ_METER_DATA": True,  # Publish BMS/meter data if available
        # Token refresh
        "AUTO_UPDATE_TOKEN": False,
        "TOKEN_REFRESH_INTERVAL": 72000,  # 20h
        # Logging
        "LOG_LEVEL": "INFO",
        "DEVELOPERS_MODE": False,
    }

    # Required configuration keys
    REQUIRED_KEYS = [
        "HOYMILES_USER",
        "HOYMILES_PASSWORD",
        "HOYMILES_PLANT_ID",
        "MQTT_HOST",
        "MQTT_USER",
        "MQTT_PASS",
    ]

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the configuration manager.

        Args:
            logger: Logger instance (optional)
        """
        self.config: dict[str, Any] = dict(self.DEFAULTS)
        self.logger = logger or logging.getLogger(__name__)

    def load_from_env(self, prefix: str = "") -> "ConfigManager":
        """
        Load configuration from environment variables.

        Args:
            prefix: Optional prefix for environment variables

        Returns:
            Self for method chaining
        """
        for key in self.DEFAULTS.keys():
            env_key = f"{prefix}{key}" if prefix else key
            if env_key in os.environ:
                value = os.environ[env_key]
                # Convert string booleans
                if self.DEFAULTS[key] is False or self.DEFAULTS[key] is True:
                    self.config[key] = value.lower() in ("true", "1", "yes", "on")
                # Convert string integers
                elif isinstance(self.DEFAULTS[key], int):
                    try:
                        self.config[key] = int(value)
                    except ValueError:
                        self.logger.warning(f"Cannot convert {env_key} to int: {value}")
                else:
                    self.config[key] = value
                self.logger.debug(f"Loaded {key} from environment")
        return self

    def load_from_file(self, file_path: str) -> "ConfigManager":
        """
        Load configuration from a JSON file.

        Args:
            file_path: Path to JSON configuration file

        Returns:
            Self for method chaining

        Raises:
            ConfigError: If file cannot be read or parsed
        """
        path = Path(file_path)
        if not path.exists():
            raise ConfigError(f"Configuration file not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle nested "options" key (from Home Assistant)
                if "options" in data:
                    data = data["options"]
                self.config.update(data)
                self.logger.info(f"Loaded configuration from {file_path}")
        except json.JSONDecodeError as err:
            raise ConfigError(f"Invalid JSON in {file_path}: {err}")
        except Exception as err:
            raise ConfigError(f"Error loading {file_path}: {err}")

        return self

    def load_from_dict(self, config_dict: dict[str, Any]) -> "ConfigManager":
        """
        Load configuration from a dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Self for method chaining
        """
        self.config.update(config_dict)
        return self

    def get(self, key: str, default: Any | None = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if default is None and key in self.DEFAULTS:
            default = self.DEFAULTS[key]
        return self.config.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        """Get configuration as integer."""
        value = self.get(key, default)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return int(value) if value is not None else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get configuration as boolean."""
        value = self.get(key, default)
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def get_str(self, key: str, default: str = "") -> str:
        """Get configuration as string."""
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_list(self, key: str, default: list[Any] | None = None) -> list[Any]:
        """Get configuration as list."""
        value = self.get(key, default)
        if isinstance(value, str):
            import re

            return [item.strip() for item in re.split(r"[,:]", value) if item.strip()]
        return list(value) if value is not None else (default or [])

    def get_all(self) -> dict[str, Any]:
        """Get all configuration."""
        return dict(self.config)

    def validate(self, required_keys: list[str] | None = None) -> bool:
        """
        Validate that all required keys are present and non-empty.

        Args:
            required_keys: List of required keys (uses class default if None)

        Returns:
            True if all required keys are present

        Raises:
            ConfigError: If required keys are missing or empty
        """
        keys_to_check = required_keys or self.REQUIRED_KEYS
        missing = []

        for key in keys_to_check:
            if key not in self.config or not self.config[key]:
                missing.append(key)

        if missing:
            raise ConfigError(f"Missing required configuration: {', '.join(missing)}")

        return True

    def set(self, key: str, value: Any) -> "ConfigManager":
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value

        Returns:
            Self for method chaining
        """
        self.config[key] = value
        self.logger.debug(
            f"Set {key} = {value if key != 'HOYMILES_PASSWORD' else '***'}"
        )
        return self

    def reset_to_defaults(self) -> "ConfigManager":
        """
        Reset all configuration to defaults.

        Returns:
            Self for method chaining
        """
        self.config = dict(self.DEFAULTS)
        return self

    def __repr__(self) -> str:
        """String representation with sensitive data redacted."""
        config_copy = dict(self.config)
        for sensitive_key in ["HOYMILES_PASSWORD", "MQTT_PASS", "MQTT_TLS_CERT"]:
            if sensitive_key in config_copy:
                config_copy[sensitive_key] = "***"
        return f"ConfigManager({config_copy})"


def load_config(
    env_prefix: str = "",
    config_file: str | None = None,
    logger: logging.Logger | None = None,
) -> ConfigManager:
    """
    Convenience function to load configuration from multiple sources.

    Loads in order:
    1. Defaults
    2. Environment variables (with optional prefix)
    3. Configuration file (if provided)

    Args:
        env_prefix: Prefix for environment variables
        config_file: Path to JSON configuration file
        logger: Logger instance

    Returns:
        Configured ConfigManager instance

    Raises:
        ConfigError: If configuration loading fails
    """
    config = ConfigManager(logger=logger)
    config.load_from_env(prefix=env_prefix)
    if config_file:
        config.load_from_file(config_file)
    return config

"""
Home Assistant MQTT Publisher using ha-mqtt-discoverable

This module provides a wrapper around ha-mqtt-discoverable that integrates
seamlessly with our SensorRegistry architecture.

Installation:
    pip install ha-mqtt-discoverable

Benefits:
- Automatic MQTT discovery protocol compliance
- Handles availability management with LWT
- Prevents duplicate state publications
- Full Home Assistant integration
- Well-tested and maintained

Example:
    from config_manager import ConfigManager
    from sensor_registry import SensorRegistry
    from mqtt_publisher_hass import HASSMQTTPublisher

    config = ConfigManager()
    registry = SensorRegistry()

    publisher = HASSMQTTPublisher(config, logger=logger)
    publisher.publish_discovery("plant", "plant_1", registry.get_sensors("plant"))
    publisher.publish_data("plant_1", {"real_power": 5000})
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

try:
    from ha_mqtt_discoverable import DeviceInfo, Settings
    from ha_mqtt_discoverable.sensors import (
        BinarySensor,
        BinarySensorInfo,
        Number,
        NumberInfo,
        Sensor,
        SensorInfo,
        Switch,
        SwitchInfo,
    )

    HASS_AVAILABLE = True
except ImportError:
    HASS_AVAILABLE = False

from .sensor_registry import ComponentType, SensorDefinition


@dataclass
class DeviceData:
    """Information about a device for HA."""

    device_id: str
    device_name: str
    manufacturer: str = "Hoymiles"
    model: str = ""
    firmware_version: str = ""
    hw_version: str = ""


class HASSMQTTPublisher:
    """
    Home Assistant MQTT Discovery Publisher using ha-mqtt-discoverable library.

    This publisher uses the well-tested ha-mqtt-discoverable library for
    reliable Home Assistant integration.
    """

    def __init__(
        self,
        config: dict[str, Any],
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the HA MQTT publisher.

        Args:
            config: Configuration dictionary with keys:
                - mqtt_host: MQTT broker hostname
                - mqtt_port: MQTT broker port (default: 1883)
                - mqtt_user: MQTT username
                - mqtt_pass: MQTT password
                - mqtt_tls: Use TLS (default: False)
                - mqtt_publish_topic: Base topic for data
                - mqtt_discovery_prefix: HA discovery prefix (default: homeassistant)
                - ha_expire_time: Sensor expiry time
            logger: Logger instance
        """
        if not HASS_AVAILABLE:
            raise ImportError(
                "ha-mqtt-discoverable not installed. Install with: "
                "pip install ha-mqtt-discoverable"
            )

        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Initialize ha-mqtt-discoverable settings
        self.mqtt_settings = self._create_mqtt_settings()

        # Store entity instances for state management
        self.entities: dict[str, Any] = {}

    def _create_mqtt_settings(self) -> Settings:
        """Create ha-mqtt-discoverable MQTT settings."""
        mqtt_config = {
            "host": self.config.get("MQTT_HOST", "localhost"),
            "port": self.config.get("MQTT_PORT", 1883),
            "username": self.config.get("MQTT_USER", ""),
            "password": self.config.get("MQTT_PASS", ""),
            "keepalive": 60,
            "state_prefix": "hoymiles",
        }

        # Add TLS if enabled
        if self.config.get("MQTT_TLS", False):
            mqtt_config["tls_insecure"] = True

        return Settings.MQTT(**mqtt_config)

    def publish_discovery(
        self,
        device_type: str,
        device_id: str,
        device_name: str,
        sensors: dict[str, SensorDefinition],
        device_info: dict[str, Any] | None = None,
        manufacturer: str = "Hoymiles",
    ) -> int:
        """
        Publish Home Assistant discovery messages for a device.

        Args:
            device_type: Type of device (e.g., "plant", "dtu")
            device_id: Unique device identifier
            device_name: Human-readable device name
            sensors: Dictionary of sensor_key -> SensorDefinition
            device_info: Additional device info
            manufacturer: Device manufacturer

        Returns:
            Number of entities published
        """
        if device_info is None:
            device_info = {}

        published = 0

        # Create device info for HA
        self.logger.debug(
            f"Creating device info for {device_id} with type {device_type}, device_name {device_name}, and additional info {device_info}"
        )
        device = DeviceInfo(
            name=device_name,
            identifiers=f"hoymiles_{device_id}",
            manufacturer=manufacturer,
            model=device_type,
            **device_info,
        )

        # Create discovery settings
        base_topic = self.config.get("MQTT_PUBLISH_TOPIC", "home/solar")
        discovery_prefix = self.config.get("MQTT_DISCOVERY_PREFIX", "homeassistant")

        for sensor_key, sensor_def in sensors.items():
            try:
                unique_id = f"{device_id}_{sensor_key}"

                # Convert sensor definition to HA entity
                entity = self._create_entity(
                    sensor_def=sensor_def,
                    unique_id=unique_id,
                    device=device,
                    discovery_prefix=discovery_prefix,
                    base_topic=base_topic,
                    device_id=device_id,
                )

                if entity:
                    # Store for later state updates
                    self.entities[unique_id] = entity

                    # Write discovery
                    if hasattr(entity, "write_config"):
                        entity.write_config()

                    self.logger.debug(f"Published discovery: {unique_id}")
                    published += 1

            except Exception as err:
                self.logger.error(
                    f"Error publishing discovery for {device_id}.{sensor_key}: {err}"
                )

        return published

    def _create_entity(
        self,
        sensor_def: SensorDefinition,
        unique_id: str,
        device: DeviceInfo,
        discovery_prefix: str,
        base_topic: str,
        device_id: str,
    ) -> Any | None:
        """
        Create a ha-mqtt-discoverable entity from sensor definition.

        Args:
            sensor_def: SensorDefinition instance
            unique_id: Unique entity ID
            device: Device info
            discovery_prefix: Discovery prefix
            base_topic: Base topic
            device_id: Device ID

        Returns:
            Entity instance or None
        """
        entity_topic = f"{base_topic}/{device_id}"
        state_topic = f"{entity_topic}/state"
        command_topic = f"{base_topic}/command/{device_id}"

        # Map sensor component to HA entity
        if sensor_def.component_type == ComponentType.SENSOR:
            return self._create_sensor_entity(
                sensor_def, unique_id, device, discovery_prefix, state_topic
            )

        elif sensor_def.component_type == ComponentType.BINARY_SENSOR:
            return self._create_binary_sensor_entity(
                sensor_def, unique_id, device, discovery_prefix, state_topic
            )

        elif sensor_def.component_type == ComponentType.SWITCH:
            return self._create_switch_entity(
                sensor_def,
                unique_id,
                device,
                discovery_prefix,
                state_topic,
                command_topic,
            )

        elif sensor_def.component_type == ComponentType.NUMBER:
            return self._create_number_entity(
                sensor_def,
                unique_id,
                device,
                discovery_prefix,
                state_topic,
                command_topic,
            )

        else:
            self.logger.warning(
                f"Unsupported component type: {sensor_def.component_type}"
            )
            return None

    def _create_sensor_entity(
        self,
        sensor_def: SensorDefinition,
        unique_id: str,
        device: DeviceInfo,
        discovery_prefix: str,
        state_topic: str,
    ) -> Sensor | None:
        """Create a sensor entity."""
        try:
            sensor_info = SensorInfo(
                name=sensor_def.name,
                unique_id=unique_id,
                unit_of_measurement=sensor_def.unit_of_measurement or None,
                device_class=sensor_def.device_class.value
                if sensor_def.device_class
                else None,
                state_class=sensor_def.state_class.value
                if sensor_def.state_class
                else None,
                icon=sensor_def.icon or None,
                device=device,
            )

            settings = Settings(
                mqtt=self.mqtt_settings,
                entity=sensor_info,
                discovery_prefix=discovery_prefix,
            )

            return Sensor(settings)
        except Exception as err:
            self.logger.error(f"Error creating sensor entity: {err}")
            return None

    def _create_binary_sensor_entity(
        self,
        sensor_def: SensorDefinition,
        unique_id: str,
        device: DeviceInfo,
        discovery_prefix: str,
        state_topic: str,
    ) -> BinarySensor | None:
        """Create a binary sensor entity."""
        try:
            sensor_info = BinarySensorInfo(
                name=sensor_def.name,
                unique_id=unique_id,
                device_class=sensor_def.device_class.value
                if sensor_def.device_class
                else None,
                icon=sensor_def.icon or None,
                device=device,
            )

            settings = Settings(
                mqtt=self.mqtt_settings,
                entity=sensor_info,
                discovery_prefix=discovery_prefix,
            )

            return BinarySensor(settings)
        except Exception as err:
            self.logger.error(f"Error creating binary sensor entity: {err}")
            return None

    def _create_switch_entity(
        self,
        sensor_def: SensorDefinition,
        unique_id: str,
        device: DeviceInfo,
        discovery_prefix: str,
        state_topic: str,
        command_topic: str,
    ) -> Switch | None:
        """Create a switch entity."""
        try:
            switch_info = SwitchInfo(
                name=sensor_def.name,
                unique_id=unique_id,
                icon=sensor_def.icon or None,
                device=device,
            )

            settings = Settings(
                mqtt=self.mqtt_settings,
                entity=switch_info,
                discovery_prefix=discovery_prefix,
            )

            return Switch(settings)
        except Exception:
            self.logger.exception("Error creating switch entity")
            return None

    def _create_number_entity(
        self,
        sensor_def: SensorDefinition,
        unique_id: str,
        device: DeviceInfo,
        discovery_prefix: str,
        state_topic: str,
        command_topic: str,
    ) -> Number | None:
        """Create a number entity."""
        try:
            number_info = NumberInfo(
                name=sensor_def.name,
                unique_id=unique_id,
                min=sensor_def.min_value,
                max=sensor_def.max_value,
                unit_of_measurement=sensor_def.unit_of_measurement or None,
                icon=sensor_def.icon or None,
                device=device,
            )

            settings = Settings(
                mqtt=self.mqtt_settings,
                entity=number_info,
                discovery_prefix=discovery_prefix,
            )

            return Number(settings)
        except Exception as err:
            self.logger.error(f"Error creating number entity: {err}")
            return None

    def publish_data(
        self,
        device_id: str,
        data: dict[str, Any],
        sensor_key_map: dict[str, str] | None = None,
        include_timestamp: bool = False,
    ) -> int:
        """
        Publish sensor data to Home Assistant.

        Args:
            device_id: Device ID
            data: Dictionary of sensor_key -> value
            sensor_key_map: Optional mapping of sensor keys to entity unique IDs

        Returns:
            Number of successfully published values
        """
        published = 0

        if include_timestamp:
            data = dict(data)
            data["publish_time"] = datetime.now(tz=timezone.utc).isoformat()

        for key, value in data.items():
            if value is None:
                continue

            # Find the entity for this key
            if sensor_key_map and key in sensor_key_map:
                entity_id = sensor_key_map[key]
            else:
                entity_id = f"{device_id}_{key}"

            # Publish to the entity
            if entity_id in self.entities:
                try:
                    entity = self.entities[entity_id]

                    # Set state based on entity type
                    if hasattr(entity, "set_state"):
                        entity.set_state(value)
                    elif hasattr(entity, "set_value"):
                        entity.set_value(value)
                    elif hasattr(entity, "update_state"):
                        entity.update_state(value)

                    published += 1
                except Exception:
                    self.logger.exception(f"Error publishing {entity_id}")
            else:
                # Entity not created, publish directly
                self.logger.debug(f"Entity {entity_id} not found, skipping")

        return published

    def publish_availability(self, status: str = "online") -> int:
        """Backward-compatible availability API used by the application."""
        self.set_availability(status == "online")
        return 1

    def set_availability(self, available: bool = True) -> None:
        """
        Set availability status for all entities.

        Args:
            available: True for online, False for offline
        """
        for entity in self.entities.values():
            try:
                if hasattr(entity, "set_availability"):
                    entity.set_availability(available)
            except Exception:
                self.logger.exception("Error setting availability")

    def disconnect(self) -> None:
        """Disconnect and clean up."""
        try:
            for entity in self.entities.values():
                if hasattr(entity, "disconnect"):
                    entity.disconnect()
            self.logger.info("MQTT publisher disconnected")
        except Exception:
            self.logger.exception("Error disconnecting")


# Backward compatibility wrapper
class HAMQTTPublisher(HASSMQTTPublisher):
    """
    Backward compatible alias for HASSMQTTPublisher.

    This allows existing code to work without changes:

    Old code:
        from mqtt_publisher import HAMQTTPublisher
        publisher = HAMQTTPublisher(config)

    New code (same interface):
        from mqtt_publisher_hass import HAMQTTPublisher
        publisher = HAMQTTPublisher(config)
    """

    def __init__(self, mqtt_client_or_config, config=None, logger=None):
        """Accept both old and new constructor styles.

        Supported forms:
        - HAMQTTPublisher(config, logger=logger)
        - HAMQTTPublisher(mqtt_client, config, logger)
        """
        actual_config = mqtt_client_or_config if config is None else config
        super().__init__(actual_config, logger=logger)

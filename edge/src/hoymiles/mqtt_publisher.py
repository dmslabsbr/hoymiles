"""
Generic MQTT Publisher for Home Assistant Discovery

This module provides a clean abstraction for publishing sensor data and device
discovery messages to Home Assistant via MQTT using the Discovery protocol.

Example usage:
    from mqtt_publisher import HAMQTTPublisher
    from sensor_registry import SensorRegistry, ComponentType

    publisher = HAMQTTPublisher(mqtt_client, config)
    registry = SensorRegistry()

    # Publish discovery config
    publisher.publish_discovery(
        device_id="plant_1",
        device_name="Solar Plant",
        sensors=registry.get_sensors("plant")
    )

    # Publish sensor data
    publisher.publish_data(
        device_type="plant",
        device_id="plant_1",
        data={"real_power": 5000, "today_eq": 12.5}
    )
"""

import json
import logging
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt

from .sensor_registry import ComponentType, SensorDefinition


class HAMQTTPublisher:
    """
    Home Assistant MQTT Discovery Publisher.

    Handles publishing of device discovery messages and sensor data
    to Home Assistant via MQTT broker.
    """

    def __init__(
        self,
        mqtt_client: mqtt.Client,
        config: dict[str, Any],
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the MQTT Publisher.

        Args:
            mqtt_client: Connected paho-mqtt Client instance
            config: Configuration dictionary with keys:
                - mqtt_publish_topic: Base topic for data (e.g., "home/solar")
                - mqtt_discovery_prefix: HA discovery prefix (default: "homeassistant")
                - mqtt_node_id: Node ID (default: "hoymiles")
                - ha_expire_time: Sensor expiry time in seconds
            logger: Logger instance (optional)
        """
        self.client = mqtt_client
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        self.publish_topic = config.get("mqtt_publish_topic", "home/solar")
        self.discovery_prefix = config.get("mqtt_discovery_prefix", "homeassistant")
        self.node_id = config.get("mqtt_node_id", "hoymiles")
        self.expire_time = config.get("ha_expire_time", 600)

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
            device_type: Type of device (e.g., "plant", "dtu", "micro")
            device_id: Unique device identifier
            device_name: Human-readable device name
            sensors: Dictionary of sensor_key -> SensorDefinition
            device_info: Additional device information (model, firmware, etc.)
            manufacturer: Device manufacturer name

        Returns:
            Total number of successfully published messages
        """
        if device_info is None:
            device_info = {}

        published = 0
        device_identifiers = f"hoymiles_{device_id}"

        # Build device information for discovery
        device_dict = {
            "identifiers": [device_identifiers],
            "name": device_name,
            "manufacturer": manufacturer,
            "model": device_type,
            "via_device": device_id,
        }
        device_dict.update(device_info)

        for sensor_key, sensor_def in sensors.items():
            try:
                published += self._publish_sensor_discovery(
                    device_type=device_type,
                    device_id=device_id,
                    sensor_key=sensor_key,
                    sensor_def=sensor_def,
                    device_info=device_dict,
                )
            except Exception as err:
                self.logger.error(
                    f"Error publishing discovery for {device_id}.{sensor_key}: {err}"
                )

        return published

    def _publish_sensor_discovery(
        self,
        device_type: str,
        device_id: str,
        sensor_key: str,
        sensor_def: SensorDefinition,
        device_info: dict[str, Any],
    ) -> int:
        """
        Publish discovery message for a single sensor.

        Args:
            device_type: Type of device
            device_id: Device ID
            sensor_key: Sensor key
            sensor_def: SensorDefinition instance
            device_info: Device information dictionary

        Returns:
            1 if published successfully, 0 otherwise
        """
        component = sensor_def.component_type.value
        unique_id = f"{device_id}_{sensor_key}"

        # Build the discovery topic
        discovery_topic = (
            f"{self.discovery_prefix}/{component}/{self.node_id}/{unique_id}/config"
        )

        # Build the discovery payload
        payload = self._build_discovery_payload(
            sensor_def=sensor_def,
            unique_id=unique_id,
            device_id=device_id,
            device_info=device_info,
            component=component,
        )

        # Publish the discovery message
        ret = self.client.publish(discovery_topic, json.dumps(payload))

        if ret[0] == mqtt.MQTT_ERR_SUCCESS:
            self.logger.debug(f"Published discovery: {discovery_topic}")
            return 1
        else:
            self.logger.error(f"Failed to publish discovery: {discovery_topic}")
            return 0

    def _build_discovery_payload(
        self,
        sensor_def: SensorDefinition,
        unique_id: str,
        device_id: str,
        device_info: dict[str, Any],
        component: str,
    ) -> dict[str, Any]:
        """
        Build a Home Assistant discovery payload for a sensor.

        Args:
            sensor_def: SensorDefinition instance
            unique_id: Unique sensor ID
            device_id: Device ID
            device_info: Device information
            component: Component type

        Returns:
            Dictionary representing the discovery payload
        """
        # Common payload fields
        payload = {
            "name": sensor_def.name,
            "unique_id": unique_id,
            "availability_mode": "latest",
            "availability_topic": f"{self.publish_topic}/availability",
            "payload_available": "online",
            "payload_not_available": "offline",
            "device": device_info,
        }

        # Add value template and state topic
        if sensor_def.component_type != ComponentType.SWITCH:
            payload["state_topic"] = f"{self.publish_topic}/{device_id}"
            if sensor_def.value_template:
                payload["value_template"] = (
                    f"{{{{ value_json.{sensor_def.value_template} }}}}"
                )

        # Add component-specific fields
        if component == ComponentType.SENSOR.value:
            if sensor_def.unit_of_measurement:
                payload["unit_of_measurement"] = sensor_def.unit_of_measurement
            if sensor_def.device_class and sensor_def.device_class.value:
                payload["device_class"] = sensor_def.device_class.value
            if sensor_def.state_class:
                payload["state_class"] = sensor_def.state_class.value
            payload["expire_after"] = self.expire_time

        elif component == ComponentType.BINARY_SENSOR.value:
            if sensor_def.device_class and sensor_def.device_class.value:
                payload["device_class"] = sensor_def.device_class.value
            payload["payload_on"] = "ON"
            payload["payload_off"] = "OFF"

        elif component == ComponentType.NUMBER.value:
            if sensor_def.min_value is not None:
                payload["min"] = sensor_def.min_value
            if sensor_def.max_value is not None:
                payload["max"] = sensor_def.max_value
            if sensor_def.unit_of_measurement:
                payload["unit_of_measurement"] = sensor_def.unit_of_measurement
            payload["command_topic"] = (
                f"{self.publish_topic}/command/{device_id}/{sensor_key}"
            )

        elif component == ComponentType.SWITCH.value:
            payload["command_topic"] = (
                f"{self.publish_topic}/command/{device_id}/{sensor_key}"
            )
            payload["state_on"] = "ON"
            payload["state_off"] = "OFF"

        # Add icon if defined
        if sensor_def.icon:
            payload["icon"] = sensor_def.icon

        return payload

    def publish_data(
        self,
        device_id: str,
        data: dict[str, Any],
        include_timestamp: bool = True,
    ) -> int:
        """
        Publish sensor data for a device.

        Args:
            device_id: Device ID
            data: Dictionary of sensor_key -> value
            include_timestamp: Whether to include publish timestamp

        Returns:
            1 if published successfully, 0 otherwise
        """
        if include_timestamp:
            data = dict(data)  # Create a copy
            data["publish_time"] = datetime.now().isoformat()

        topic = f"{self.publish_topic}/{device_id}"
        ret = self.client.publish(topic, json.dumps(data))

        if ret[0] == mqtt.MQTT_ERR_SUCCESS:
            self.logger.debug(f"Published data to {topic}")
            return 1
        else:
            self.logger.error(f"Failed to publish data to {topic}")
            return 0

    def publish_availability(self, status: str = "online") -> int:
        """
        Publish availability status.

        Args:
            status: "online" or "offline"

        Returns:
            1 if published successfully, 0 otherwise
        """
        topic = f"{self.publish_topic}/availability"
        ret = self.client.publish(topic, status)

        if ret[0] == mqtt.MQTT_ERR_SUCCESS:
            self.logger.debug(f"Published availability: {status}")
            return 1
        else:
            self.logger.error("Failed to publish availability")
            return 0

"""
Centralized Sensor Registry System

This module provides a declarative way to define sensors for different device types.
Sensors are grouped by component type (sensor, binary_sensor, switch, number) and
can be easily extended without modifying the MQTT publisher or main application.

Example usage:
    from sensor_registry import SensorRegistry, SensorDefinition

    # Get registry
    registry = SensorRegistry()

    # Get sensors for a device type
    plant_sensors = registry.get_sensors("plant")
    dtu_sensors = registry.get_sensors("dtu")

    # Get specific sensor definition
    power_sensor = registry.get_sensor("plant", "real_power")
"""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ComponentType(Enum):
    """Home Assistant component types for MQTT discovery."""

    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"
    SWITCH = "switch"
    NUMBER = "number"


class StateClass(Enum):
    """Home Assistant state classes for sensors."""

    MEASUREMENT = "measurement"
    TOTAL_INCREASING = "total_increasing"


class DeviceClass(Enum):
    """Home Assistant device classes."""

    POWER = "power"
    ENERGY = "energy"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    CONNECTIVITY = "connectivity"
    TIMESTAMP = "timestamp"
    NONE = None


@dataclass
class SensorDefinition:
    """
    Defines a sensor's metadata and MQTT discovery properties.

    Attributes:
        key: Unique identifier for the sensor (used in data payload)
        name: Human-readable sensor name
        component_type: Home Assistant component type
        unit_of_measurement: Unit (e.g., "W", "kWh", "%")
        device_class: Home Assistant device class
        state_class: State class (measurement, total_increasing, etc.)
        icon: MDI icon name
        value_template: Template to extract value from data (e.g., "real_power")
        min_value: Minimum value (for number component)
        max_value: Maximum value (for number component)
        enabled_by_default: Whether sensor is enabled by default
    """

    key: str
    name: str
    component_type: ComponentType
    unit_of_measurement: str = ""
    device_class: DeviceClass | None = None
    state_class: StateClass | None = None
    icon: str = ""
    value_template: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    enabled_by_default: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        data = asdict(self)
        # Convert enums to strings
        if isinstance(data["component_type"], ComponentType):
            data["component_type"] = data["component_type"].value
        if data["device_class"] and isinstance(data["device_class"], DeviceClass):
            data["device_class"] = (
                data["device_class"].value if data["device_class"].value else ""
            )
        if data["state_class"] and isinstance(data["state_class"], StateClass):
            data["state_class"] = data["state_class"].value

        # Remove None values and empty strings
        return {k: v for k, v in data.items() if v is not None and v != ""}


class SensorRegistry:
    """
    Central registry for all sensor definitions.
    Provides methods to query and retrieve sensor configurations.
    """

    def __init__(self):
        """Initialize the sensor registry with default definitions."""
        self._sensors: dict[str, dict[str, SensorDefinition]] = {}
        self._load_default_sensors()

    def register_sensor(self, device_type: str, sensor: SensorDefinition) -> None:
        """
        Register a new sensor definition.

        Args:
            device_type: Type of device (e.g., "plant", "dtu", "micro", "bms")
            sensor: SensorDefinition instance
        """
        if device_type not in self._sensors:
            self._sensors[device_type] = {}
        self._sensors[device_type][sensor.key] = sensor

    def register_sensors(
        self, device_type: str, sensors: list[SensorDefinition]
    ) -> None:
        """
        Register multiple sensor definitions.

        Args:
            device_type: Type of device
            sensors: List of SensorDefinition instances
        """
        for sensor in sensors:
            self.register_sensor(device_type, sensor)

    def get_sensor(self, device_type: str, sensor_key: str) -> SensorDefinition | None:
        """
        Get a specific sensor definition.

        Args:
            device_type: Type of device
            sensor_key: Unique sensor key

        Returns:
            SensorDefinition or None if not found
        """
        return self._sensors.get(device_type, {}).get(sensor_key)

    def get_sensors(self, device_type: str) -> dict[str, SensorDefinition]:
        """
        Get all sensors for a device type.

        Args:
            device_type: Type of device

        Returns:
            Dictionary of sensor_key -> SensorDefinition
        """
        return self._sensors.get(device_type, {})

    def get_sensors_by_component(
        self, device_type: str, component_type: ComponentType
    ) -> dict[str, SensorDefinition]:
        """
        Get sensors of a specific component type.

        Args:
            device_type: Type of device
            component_type: ComponentType to filter by

        Returns:
            Dictionary of sensor_key -> SensorDefinition
        """
        sensors = self.get_sensors(device_type)
        return {
            key: sensor
            for key, sensor in sensors.items()
            if sensor.component_type == component_type
        }

    def get_device_types(self) -> list[str]:
        """Get all registered device types."""
        return list(self._sensors.keys())

    def _load_default_sensors(self) -> None:
        """Load default sensor definitions."""
        # Plant sensors
        plant_sensors = [
            SensorDefinition(
                key="real_power",
                name="Real Power",
                component_type=ComponentType.SENSOR,
                device_class=DeviceClass.POWER,
                state_class=StateClass.MEASUREMENT,
                unit_of_measurement="W",
                icon="mdi:solar-power",
                value_template="real_power",
            ),
            SensorDefinition(
                key="real_power_kw",
                name="Real Power (kW)",
                component_type=ComponentType.SENSOR,
                device_class=DeviceClass.POWER,
                state_class=StateClass.MEASUREMENT,
                unit_of_measurement="kW",
                icon="mdi:solar-power",
                value_template="real_power_kw",
            ),
            SensorDefinition(
                key="today_eq",
                name="Today Energy",
                component_type=ComponentType.SENSOR,
                device_class=DeviceClass.ENERGY,
                state_class=StateClass.TOTAL_INCREASING,
                unit_of_measurement="kWh",
                icon="mdi:lightning-bolt",
                value_template="today_eq",
            ),
            SensorDefinition(
                key="month_eq",
                name="Month Energy",
                component_type=ComponentType.SENSOR,
                device_class=DeviceClass.ENERGY,
                state_class=StateClass.TOTAL_INCREASING,
                unit_of_measurement="kWh",
                icon="mdi:lightning-bolt",
                value_template="month_eq",
            ),
            SensorDefinition(
                key="year_eq",
                name="Year Energy",
                component_type=ComponentType.SENSOR,
                device_class=DeviceClass.ENERGY,
                state_class=StateClass.TOTAL_INCREASING,
                unit_of_measurement="kWh",
                icon="mdi:lightning-bolt",
                value_template="year_eq",
            ),
            SensorDefinition(
                key="total_eq",
                name="Total Energy",
                component_type=ComponentType.SENSOR,
                device_class=DeviceClass.ENERGY,
                state_class=StateClass.TOTAL_INCREASING,
                unit_of_measurement="kWh",
                icon="mdi:lightning-bolt",
                value_template="total_eq",
            ),
            SensorDefinition(
                key="array_size",
                name="Array Size",
                component_type=ComponentType.SENSOR,
                device_class=DeviceClass.POWER,
                unit_of_measurement="W",
                icon="mdi:solar-panel",
                value_template="array_size",
            ),
            SensorDefinition(
                key="array_size_kW",
                name="Array Size (kW)",
                component_type=ComponentType.SENSOR,
                device_class=DeviceClass.POWER,
                unit_of_measurement="kW",
                icon="mdi:solar-panel",
                value_template="array_size_kW",
            ),
            SensorDefinition(
                key="power_ratio",
                name="Power Ratio",
                component_type=ComponentType.SENSOR,
                state_class=StateClass.MEASUREMENT,
                unit_of_measurement="%",
                icon="mdi:percent",
                value_template="power_ratio",
            ),
            SensorDefinition(
                key="co2_emission_reduction",
                name="CO2 Emission Reduction",
                component_type=ComponentType.SENSOR,
                unit_of_measurement="t",
                icon="mdi:molecule-co2",
                state_class=StateClass.TOTAL_INCREASING,
                value_template="co2_emission_reduction",
            ),
            SensorDefinition(
                key="last_data_time",
                name="Last Data Time",
                component_type=ComponentType.SENSOR,
                device_class=DeviceClass.TIMESTAMP,
                icon="mdi:clock",
                value_template="last_data_time",
            ),
        ]
        self.register_sensors("plant", plant_sensors)

        # DTU sensors
        dtu_sensors = [
            SensorDefinition(
                key="connect",
                name="Connected",
                component_type=ComponentType.BINARY_SENSOR,
                device_class=DeviceClass.CONNECTIVITY,
                icon="mdi:solar-panel",
                value_template="connect",
            ),
        ]
        self.register_sensors("dtu", dtu_sensors)

        # Microinverter sensors
        micro_sensors = [
            SensorDefinition(
                key="connect",
                name="Connected",
                component_type=ComponentType.BINARY_SENSOR,
                device_class=DeviceClass.CONNECTIVITY,
                icon="mdi:power-plug",
                value_template="connect",
            ),
            SensorDefinition(
                key="alarm_code",
                name="Alarm Code",
                component_type=ComponentType.SENSOR,
                icon="mdi:alert",
                value_template="alarm_code",
            ),
            SensorDefinition(
                key="alarm_string",
                name="Alarm String",
                component_type=ComponentType.SENSOR,
                icon="mdi:alert-circle",
                value_template="alarm_string",
            ),
        ]
        self.register_sensors("micro", micro_sensors)

        # BMS sensors
        bms_sensors = [
            SensorDefinition(
                key="connect",
                name="Connected",
                component_type=ComponentType.BINARY_SENSOR,
                device_class=DeviceClass.CONNECTIVITY,
                icon="mdi:battery",
                value_template="connect",
            ),
            SensorDefinition(
                key="alarm_code",
                name="Alarm Code",
                component_type=ComponentType.SENSOR,
                icon="mdi:alert",
                value_template="alarm_code",
            ),
            SensorDefinition(
                key="reserve_soc",
                name="Reserve SOC",
                component_type=ComponentType.NUMBER,
                unit_of_measurement="%",
                icon="mdi:battery-low",
                value_template="reserve_soc",
                min_value=0,
                max_value=100,
            ),
            SensorDefinition(
                key="max_power",
                name="Max Power",
                component_type=ComponentType.NUMBER,
                device_class=DeviceClass.POWER,
                unit_of_measurement="%",
                icon="mdi:power-plug",
                value_template="max_power",
                min_value=0,
                max_value=100,
            ),
        ]
        self.register_sensors("bms", bms_sensors)

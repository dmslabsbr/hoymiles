"""
Practical Examples for Using the Refactored Architecture

This module provides ready-to-use examples for common tasks.
"""

# ============================================================================
# Example 1: Basic Configuration Loading
# ============================================================================


def example_config_loading():
    """Load configuration from environment and file."""
    from config_manager import ConfigManager

    config = ConfigManager()
    config.load_from_env()  # Load from environment variables
    config.load_from_file("config.json")  # Override with file

    # Access values with type conversion
    mqtt_host = config.get_str("MQTT_HOST")
    mqtt_port = config.get_int("MQTT_PORT", default=1883)
    mqtt_tls = config.get_bool("MQTT_TLS", default=False)

    # Validate required keys
    try:
        config.validate()
        print("✓ Configuration is valid")
    except Exception as err:
        print(f"✗ Configuration error: {err}")

    return config


# ============================================================================
# Example 2: Registry and Sensor Definition
# ============================================================================


def example_sensor_registry():
    """Work with centralized sensor definitions."""
    from sensor_registry import (
        ComponentType,
        DeviceClass,
        SensorDefinition,
        SensorRegistry,
        StateClass,
    )

    registry = SensorRegistry()

    # Get all sensors for a device type
    plant_sensors = registry.get_sensors("plant")
    print(f"Plant has {len(plant_sensors)} sensors")

    # Get sensors by component type
    binary_sensors = registry.get_sensors_by_component(
        "plant", ComponentType.BINARY_SENSOR
    )

    # Get specific sensor
    power_sensor = registry.get_sensor("plant", "real_power")
    if power_sensor:
        print(f"Sensor: {power_sensor.name} ({power_sensor.unit_of_measurement})")

    # Add custom sensor
    registry.register_sensor(
        "plant",
        SensorDefinition(
            key="efficiency_ratio",
            name="Efficiency Ratio",
            component_type=ComponentType.SENSOR,
            device_class=DeviceClass.ENERGY,
            state_class=StateClass.MEASUREMENT,
            unit_of_measurement="%",
            icon="mdi:percent",
        ),
    )

    return registry


# ============================================================================
# Example 3: Data Transformation Pipeline
# ============================================================================


def example_data_pipeline():
    """Create and execute a data transformation pipeline."""
    from data_pipeline import (
        CalculatedFieldTransformer,
        DataPipeline,
        FilterNullTransformer,
        RoundTransformer,
        TypeCastTransformer,
    )

    # Create pipeline
    pipeline = DataPipeline()

    # Add transformers in order
    pipeline.add_transformer(
        TypeCastTransformer(
            {
                "real_power": float,
                "today_eq": float,
            }
        )
    )

    # Calculate derived values
    pipeline.add_transformer(
        CalculatedFieldTransformer(
            {
                "real_power_kw": lambda d: d.get("real_power", 0) / 1000,
                "power_ratio": lambda d: (
                    (d.get("real_power", 0) / d.get("array_size", 1)) * 100
                    if d.get("array_size")
                    else 0
                ),
            }
        )
    )

    # Round values
    pipeline.add_transformer(
        RoundTransformer(
            {
                "real_power_kw": 3,
                "power_ratio": 2,
            }
        )
    )

    # Remove null values
    pipeline.add_transformer(FilterNullTransformer())

    # Execute pipeline
    raw_data = {
        "real_power": 5234,
        "array_size": 8000,
        "today_eq": 12.456,
        "error_field": None,
    }

    transformed = pipeline.execute(raw_data)
    print(f"Input: {raw_data}")
    print(f"Output: {transformed}")

    return transformed


# ============================================================================
# Example 4: Custom Data Transformer
# ============================================================================


def example_custom_transformer():
    """Create and use a custom data transformer."""
    from datetime import datetime

    from data_pipeline import DataPipeline, DataTransformer

    class TimeStampTransformer(DataTransformer):
        """Add timestamp to data."""

        def transform(self, data):
            data["timestamp"] = datetime.now().isoformat()
            return data

    class AlarmLevelTransformer(DataTransformer):
        """Convert alarm codes to severity levels."""

        ALARM_LEVELS = {
            0: "info",
            1: "warning",
            2: "error",
            3: "critical",
        }

        def transform(self, data):
            if "alarm_code" in data:
                code = data["alarm_code"]
                data["alarm_level"] = self.ALARM_LEVELS.get(code, "unknown")
            return data

        def validate(self, data):
            return "alarm_code" in data

    # Use custom transformers
    pipeline = DataPipeline()
    pipeline.add_transformer(TimeStampTransformer())
    pipeline.add_transformer(AlarmLevelTransformer())

    result = pipeline.execute({"alarm_code": 2, "device": "DTU_123"})
    print(f"Result: {result}")

    return result


# ============================================================================
# Example 5: MQTT Publisher and Home Assistant Discovery
# ============================================================================


def example_mqtt_publisher():
    """Publish sensor data and discovery messages."""
    import paho.mqtt.client as mqtt
    from mqtt_publisher import HAMQTTPublisher
    from sensor_registry import SensorRegistry

    # Setup MQTT client
    client = mqtt.Client("hoymiles_example")

    # Note: In real usage, you'd connect first
    # client.connect("localhost", 1883)
    # client.loop_start()

    config = {
        "mqtt_publish_topic": "home/solar",
        "mqtt_discovery_prefix": "homeassistant",
        "mqtt_node_id": "hoymiles",
        "ha_expire_time": 600,
    }

    publisher = HAMQTTPublisher(client, config)
    registry = SensorRegistry()

    # Publish discovery for plant sensors
    published = publisher.publish_discovery(
        device_type="plant",
        device_id="plant_001",
        device_name="Main Solar Plant",
        sensors=registry.get_sensors("plant"),
        device_info={
            "firmware_version": "1.0.0",
            "hw_version": "v2",
        },
    )
    print(f"Published {published} discovery messages")

    # Publish sensor data
    sensor_data = {
        "real_power": 4500,
        "today_eq": 15.3,
        "total_eq": 1250.5,
        "array_size": 8000,
    }

    result = publisher.publish_data(
        device_id="plant_001",
        data=sensor_data,
        include_timestamp=True,
    )
    print(f"Published data: {result}")


# ============================================================================
# Example 6: Complete Application with All Components
# ============================================================================


def example_complete_application():
    """Demonstrate complete workflow."""
    import paho.mqtt.client as mqtt
    from config_manager import ConfigManager
    from data_pipeline import CalculatedFieldTransformer, DataPipeline, RoundTransformer
    from mqtt_publisher import HAMQTTPublisher
    from sensor_registry import SensorRegistry

    # 1. Load configuration
    config = ConfigManager()
    config.load_from_dict(
        {
            "MQTT_HOST": "localhost",
            "MQTT_PORT": 1883,
            "MQTT_USER": "user",
            "MQTT_PASS": "pass",
            "MQTT_PUBLISH_TOPIC": "home/solar",
            "MQTT_DISCOVERY_PREFIX": "homeassistant",
            "MQTT_NODE_ID": "hoymiles",
            "HA_EXPIRE_TIME": 600,
        }
    )
    print("✓ Configuration loaded")

    # 2. Setup sensor registry
    registry = SensorRegistry()
    print(f"✓ Registry has {len(registry.get_devices())} device types")

    # 3. Create data transformation pipeline
    pipeline = DataPipeline()
    pipeline.add_transformer(
        CalculatedFieldTransformer(
            {
                "power_kw": lambda d: d.get("power", 0) / 1000,
            }
        )
    )
    pipeline.add_transformer(RoundTransformer({"power_kw": 2}))
    print("✓ Pipeline created with 2 transformers")

    # 4. Setup MQTT
    mqtt_client = mqtt.Client("hoymiles_app")
    publisher = HAMQTTPublisher(mqtt_client, config.get_all())
    print("✓ MQTT publisher initialized")

    # 5. Process sample data
    raw_data = {
        "power": 5234,
        "temperature": 32.5,
        "status": "running",
    }

    transformed = pipeline.execute(raw_data)
    print(f"✓ Data transformed: {transformed}")

    print("\n✓ Complete workflow demonstration finished!")


# ============================================================================
# Example 7: Conditional Transformations
# ============================================================================


def example_conditional_transformation():
    """Use conditional transformations based on device state."""
    from data_pipeline import ConditionalTransformer, DataPipeline

    # Define predicates and transformations
    pipeline = DataPipeline()

    pipeline.add_transformer(
        ConditionalTransformer(
            predicates={
                "is_daytime": lambda d: d.get("real_power", 0) > 500,
                "is_nighttime": lambda d: d.get("real_power", 0) <= 500,
            },
            transformations={
                "is_daytime": lambda d: {
                    **d,
                    "mode": "generation",
                    "efficiency_weight": 1.0,
                },
                "is_nighttime": lambda d: {
                    **d,
                    "mode": "standby",
                    "efficiency_weight": 0.0,
                },
            },
        )
    )

    # Test daytime
    daytime_data = pipeline.execute({"real_power": 5000})
    print(f"Daytime: {daytime_data}")

    # Test nighttime
    pipeline.clear()
    pipeline.add_transformer(
        ConditionalTransformer(
            predicates={
                "is_daytime": lambda d: d.get("real_power", 0) > 500,
                "is_nighttime": lambda d: d.get("real_power", 0) <= 500,
            },
            transformations={
                "is_daytime": lambda d: {
                    **d,
                    "mode": "generation",
                    "efficiency_weight": 1.0,
                },
                "is_nighttime": lambda d: {
                    **d,
                    "mode": "standby",
                    "efficiency_weight": 0.0,
                },
            },
        )
    )
    nighttime_data = pipeline.execute({"real_power": 100})
    print(f"Nighttime: {nighttime_data}")


# ============================================================================
# Example 8: Error Handling in Pipelines
# ============================================================================


def example_error_handling():
    """Handle errors gracefully in data pipelines."""
    import logging

    from data_pipeline import DataPipeline, TypeCastTransformer

    logger = logging.getLogger(__name__)

    pipeline = DataPipeline(logger=logger)

    # Add error handler
    def log_error(error, data):
        logger.error(f"Pipeline error: {error} with data: {data}")

    pipeline.add_error_handler(log_error)

    # Add transformer that might fail
    pipeline.add_transformer(TypeCastTransformer({"power": int, "efficiency": float}))

    # Test with invalid data
    try:
        result = pipeline.execute(
            {"power": "not_a_number", "efficiency": 0.95}, skip_on_error=True
        )
        print(f"Result (skip errors): {result}")
    except Exception as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    print("=" * 70)
    print("EXAMPLE 1: Configuration Loading")
    print("=" * 70)
    try:
        example_config_loading()
    except Exception as e:
        print(f"Note: {e}")

    print("\n" + "=" * 70)
    print("EXAMPLE 2: Sensor Registry")
    print("=" * 70)
    example_sensor_registry()

    print("\n" + "=" * 70)
    print("EXAMPLE 3: Data Pipeline")
    print("=" * 70)
    example_data_pipeline()

    print("\n" + "=" * 70)
    print("EXAMPLE 4: Custom Transformer")
    print("=" * 70)
    example_custom_transformer()

    print("\n" + "=" * 70)
    print("EXAMPLE 5: MQTT Publisher")
    print("=" * 70)
    example_mqtt_publisher()

    print("\n" + "=" * 70)
    print("EXAMPLE 6: Complete Application")
    print("=" * 70)
    example_complete_application()

    print("\n" + "=" * 70)
    print("EXAMPLE 7: Conditional Transformations")
    print("=" * 70)
    example_conditional_transformation()

    print("\n" + "=" * 70)
    print("EXAMPLE 8: Error Handling")
    print("=" * 70)
    example_error_handling()

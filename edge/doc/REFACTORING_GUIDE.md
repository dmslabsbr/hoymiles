# REFACTORING GUIDE - Hoymiles Edge Application Architecture

This document explains the new modular architecture and how to use it.

## Overview

The refactored architecture separates concerns into independent, composable modules:

1. **sensor_registry.py** - Centralized sensor definitions
2. **config_manager.py** - Configuration management  
3. **data_pipeline.py** - Data transformation pipeline
4. **mqtt_publisher.py** - MQTT Home Assistant discovery publisher
5. **application.py** - Example application using new architecture

## Architecture Principles

### 1. Separation of Concerns

- **API Layer** (cloud_api.py) - Only handles API communication
- **Data Layer** (data_pipeline.py) - Transforms raw data
- **MQTT Layer** (mqtt_publisher.py) - Only publishes to MQTT
- **Config Layer** (config_manager.py) - Centralized configuration
- **Sensor Layer** (sensor_registry.py) - Sensor definitions

### 2. Composability

Each component can be used independently or combined:

```python
# Use just the registry
registry = SensorRegistry()
plant_sensors = registry.get_sensors("plant")

# Use just the config manager
config = ConfigManager()
config.load_from_env()
mqtt_host = config.get("MQTT_HOST")

# Use just the data pipeline
pipeline = DataPipeline()
pipeline.add_transformer(ScaleTransformer({"power": 0.001}))
transformed = pipeline.execute(raw_data)
```

### 3. Extensibility

Add new sensors without modifying existing code:

```python
from sensor_registry import SensorRegistry, SensorDefinition, ComponentType, DeviceClass

registry = SensorRegistry()
registry.register_sensor("plant", SensorDefinition(
    key="custom_metric",
    name="Custom Metric",
    component_type=ComponentType.SENSOR,
    device_class=DeviceClass.ENERGY,
    unit_of_measurement="kWh",
    icon="mdi:lightning-bolt",
    value_template="custom_metric",
))
```

### 4. Testability

Each module can be tested in isolation with mock objects.

## Module Reference

### SensorRegistry (sensor_registry.py)

Centralized definition of all sensors for each device type.

**Key Methods:**

- `register_sensor(device_type, sensor_def)` - Register a sensor
- `get_sensors(device_type)` - Get all sensors for a device type
- `get_sensors_by_component(device_type, component_type)` - Filter by component
- `get_sensor(device_type, sensor_key)` - Get a specific sensor

**Example:**

```python
from sensor_registry import SensorRegistry, ComponentType

registry = SensorRegistry()

# Get all plant sensors
plant_sensors = registry.get_sensors("plant")

# Get only sensors for Home Assistant
sensor_sensors = registry.get_sensors_by_component("plant", ComponentType.SENSOR)
binary_sensors = registry.get_sensors_by_component("plant", ComponentType.BINARY_SENSOR)

# Get specific sensor
real_power = registry.get_sensor("plant", "real_power")
print(f"{real_power.name}: {real_power.unit_of_measurement}")
```

### ConfigManager (config_manager.py)

Centralized configuration management with validation.

**Key Methods:**

- `load_from_env(prefix)` - Load from environment variables
- `load_from_file(path)` - Load from JSON file
- `load_from_dict(dict)` - Load from dictionary
- `get(key, default)` - Get configuration value
- `validate()` - Validate required keys exist

**Example:**

```python
from config_manager import ConfigManager, load_config

# Method 1: Step by step
config = ConfigManager()
config.load_from_env()
config.load_from_file("config.json")
config.validate()

# Method 2: All at once
config = load_config(config_file="config.json")

# Get values
user = config.get_str("HOYMILES_USER")
port = config.get_int("MQTT_PORT", default=1883)
use_tls = config.get_bool("MQTT_TLS", default=False)

# Get all
all_config = config.get_all()
```

### DataPipeline (data_pipeline.py)

Composable data transformation pipeline.

**Built-in Transformers:**

- `FilterKeysTransformer` - Keep only specific keys
- `RenameKeysTransformer` - Rename dictionary keys
- `TypeCastTransformer` - Cast values to types
- `ScaleTransformer` - Multiply numeric values
- `RoundTransformer` - Round to decimals
- `CalculatedFieldTransformer` - Add calculated fields
- `FilterNullTransformer` - Remove null/empty values
- `ConditionalTransformer` - Apply transformations conditionally

**Example:**

```python
from data_pipeline import (
    DataPipeline,
    CalculatedFieldTransformer,
    RoundTransformer,
    FilterNullTransformer,
)

pipeline = DataPipeline()

# Convert W to kW
pipeline.add_transformer(CalculatedFieldTransformer({
    "power_kw": lambda d: d.get("power", 0) / 1000,
}))

# Round to 3 decimals
pipeline.add_transformer(RoundTransformer({
    "power_kw": 3,
    "efficiency": 2,
}))

# Remove null values
pipeline.add_transformer(FilterNullTransformer())

# Execute
result = pipeline.execute({
    "power": 5000,
    "efficiency": None,
})
# Result: {"power": 5000, "power_kw": 5.0}
```

**Custom Transformer:**

```python
from data_pipeline import DataTransformer

class MyCustomTransformer(DataTransformer):
    def transform(self, data):
        # Modify data here
        data["timestamp"] = datetime.now().isoformat()
        return data
    
    def validate(self, data):
        # Validate input
        return "required_field" in data

pipeline.add_transformer(MyCustomTransformer())
```

### HAMQTTPublisher (mqtt_publisher.py)

Publishes Home Assistant Discovery messages and sensor data.

**Key Methods:**

- `publish_discovery()` - Publish device discovery
- `publish_data()` - Publish sensor data
- `publish_availability()` - Publish online/offline status

**Example:**

```python
from mqtt_publisher import HAMQTTPublisher
from sensor_registry import SensorRegistry
import paho.mqtt.client as mqtt

# Setup
client = mqtt.Client()
client.connect("localhost", 1883)
client.loop_start()

config = {
    "mqtt_publish_topic": "home/solar",
    "mqtt_discovery_prefix": "homeassistant",
    "mqtt_node_id": "hoymiles",
    "ha_expire_time": 600,
}

publisher = HAMQTTPublisher(client, config)
registry = SensorRegistry()

# Publish discovery
publisher.publish_discovery(
    device_type="plant",
    device_id="plant_1",
    device_name="Solar Plant",
    sensors=registry.get_sensors("plant"),
    device_info={"firmware": "1.0"},
)

# Publish data
publisher.publish_data(
    device_id="plant_1",
    data={"real_power": 5000, "today_eq": 12.5},
    include_timestamp=True,
)

# Publish availability
publisher.publish_availability("online")
```

## Migration Guide

### From Old Code to New Architecture

**Before (Old):**

```python
# Scattered configuration
mqtt_host = os.environ.get("MQTT_HOST")
hoymiles_user = config["HOYMILES_USER"]

# Mixed concerns in one function
def monta_publica_topico(mqtt_h, component, s_dict, var_comuns):
    # Config, templates, MQTT publishing all mixed
    pass

# Data transformation scattered
adjusted_data = adjust_solar_data(solar_data)
# ... more transformations

# Hard-coded sensor definitions
mqtt_h.public(topic, json_hass["sensor"])
```

**After (New):**

```python
from config_manager import ConfigManager
from sensor_registry import SensorRegistry
from mqtt_publisher import HAMQTTPublisher
from data_pipeline import DataPipeline

# Centralized configuration
config = ConfigManager()
config.load_from_env()
mqtt_host = config.get_str("MQTT_HOST")

# Separate pipelines for different data types
plant_pipeline = DataPipeline()
plant_pipeline.add_transformer(CalculatedFieldTransformer(...))

# Compose discovery easily
publisher.publish_discovery(
    device_type="plant",
    device_id="plant_1",
    sensors=registry.get_sensors("plant"),
)

# Transform and publish
transformed_data = plant_pipeline.execute(solar_data)
publisher.publish_data(device_id="plant_1", data=transformed_data)
```

## Advanced Usage

### Adding Custom Sensors at Runtime

```python
from sensor_registry import SensorDefinition, ComponentType, DeviceClass, StateClass

registry = SensorRegistry()

# Add custom sensor for specific plant
registry.register_sensor("plant", SensorDefinition(
    key="custom_efficiency",
    name="Custom Efficiency",
    component_type=ComponentType.SENSOR,
    device_class=DeviceClass.ENERGY,
    state_class=StateClass.MEASUREMENT,
    unit_of_measurement="%",
    icon="mdi:percent",
    value_template="custom_efficiency",
))
```

### Creating Multi-Stage Data Pipelines

```python
class Stage1Transformer(DataTransformer):
    def transform(self, data):
        # Fetch additional data
        data["timestamp"] = datetime.now().isoformat()
        return data

class Stage2Transformer(DataTransformer):
    def transform(self, data):
        # Apply business logic
        data["efficiency"] = calculate_efficiency(data)
        return data

pipeline = DataPipeline()
pipeline.add_transformer(Stage1Transformer())
pipeline.add_transformer(Stage2Transformer())

result = pipeline.execute(raw_data)
```

### Conditional Data Transformations

```python
from data_pipeline import ConditionalTransformer

pipeline = DataPipeline()

# Apply transformations based on conditions
pipeline.add_transformer(ConditionalTransformer(
    predicates={
        "is_daytime": lambda d: d.get("real_power", 0) > 100,
    },
    transformations={
        "is_daytime": lambda d: {**d, "mode": "generation"},
    }
))
```

## Configuration File Examples

### config.json

```json
{
  "HOYMILES_USER": "user@example.com",
  "HOYMILES_PASSWORD": "password",
  "HOYMILES_PLANT_ID": "12345",
  "MQTT_HOST": "192.168.1.100",
  "MQTT_PORT": 1883,
  "MQTT_USER": "mqtt_user",
  "MQTT_PASS": "mqtt_password",
  "MQTT_TLS": false,
  "MQTT_PUBLISH_TOPIC": "home/solar",
  "GET_DATA_INTERVAL": 480,
  "HASS_INTERVAL": 300,
  "LOG_LEVEL": "INFO"
}
```

```bash
export HOYMILES_USER="user@example.com"
export HOYMILES_PASSWORD="password"
export HOYMILES_PLANT_ID="12345"
export MQTT_HOST="192.168.1.100"
export MQTT_USER="mqtt_user"
export MQTT_PASS="mqtt_password"
```

## Testing

### Unit Testing with Mocks

```python
import unittest
from unittest.mock import Mock, MagicMock
from sensor_registry import SensorRegistry
from mqtt_publisher import HAMQTTPublisher

class TestMQTTPublisher(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.config = {
            "mqtt_publish_topic": "home/solar",
            "mqtt_discovery_prefix": "homeassistant",
            "mqtt_node_id": "test",
        }
        self.publisher = HAMQTTPublisher(self.mock_client, self.config)
        self.registry = SensorRegistry()
    
    def test_publish_discovery(self):
        result = self.publisher.publish_discovery(
            device_type="plant",
            device_id="test_1",
            device_name="Test Plant",
            sensors=self.registry.get_sensors("plant"),
        )
        # Verify it publishes multiple messages
        assert self.mock_client.publish.called
```

## Benefits of New Architecture

1. **Maintainability**: Clear separation of concerns
2. **Extensibility**: Add new sensors without modifying existing code
3. **Composability**: Mix and match components
4. **Testability**: Each module can be tested independently
5. **Reusability**: Components can be used in different applications
6. **Flexibility**: Configuration from multiple sources
7. **Scalability**: Easy to add multiple plants, devices, sensors
8. **Documentation**: Self-documenting through type hints and docstrings

## Summary

The refactored architecture provides a solid foundation for building and maintaining
the Hoymiles to Home Assistant integration. The modular design makes it easy to:

- Add new sensors or modify existing ones
- Change data transformation logic
- Customize MQTT discovery messages
- Manage configuration from multiple sources
- Test components in isolation
- Extend functionality without breaking existing code

Start with the `application.py` example and customize it for your needs.
"""

# Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   cd edge
   pip install -r requirements.txt
   ```

2. **Create configuration file (`config.json`):**
   ```json
   {
     "HOYMILES_USER": "your_email@example.com",
     "HOYMILES_PASSWORD": "your_password",
     "HOYMILES_PLANT_ID": "12345",
     "MQTT_HOST": "192.168.1.100",
     "MQTT_PORT": 1883,
     "MQTT_USER": "mqtt_user",
     "MQTT_PASS": "mqtt_password",
     "MQTT_TLS": false,
     "MQTT_PUBLISH_TOPIC": "home/solar",
     "MQTT_DISCOVERY_PREFIX": "homeassistant",
     "MQTT_NODE_ID": "hoymiles",
     "GET_DATA_INTERVAL": 480,
     "HASS_INTERVAL": 300,
     "LOG_LEVEL": "INFO"
   }
   ```

## Usage

### Option 1: Run the Example Application
```bash
python src/hoymiles/application.py
```

### Option 2: Use Individual Components
```python
# config_manager.py
from config_manager import ConfigManager
config = ConfigManager()
config.load_from_env()

# sensor_registry.py
from sensor_registry import SensorRegistry
registry = SensorRegistry()
plant_sensors = registry.get_sensors("plant")

# data_pipeline.py
from data_pipeline import DataPipeline, CalculatedFieldTransformer
pipeline = DataPipeline()
pipeline.add_transformer(CalculatedFieldTransformer({...}))

# mqtt_publisher.py
from mqtt_publisher import HAMQTTPublisher
publisher = HAMQTTPublisher(mqtt_client, config)
publisher.publish_discovery(...)
publisher.publish_data(...)
```

### Option 3: Run Examples
```bash
python src/hoymiles/examples.py
```

## Common Tasks

### Add a New Sensor
1. Open `src/hoymiles/sensor_registry.py`
2. Add to `_load_default_sensors()` method:
   ```python
   SensorDefinition(
       key="new_sensor",
       name="New Sensor",
       component_type=ComponentType.SENSOR,
       ...
   )
   ```
3. Restart application - discovery will automatically publish new sensor

### Modify Data Transformation
1. Edit `application.py` or create custom pipeline
2. Add transformers:
   ```python
   pipeline.add_transformer(MyCustomTransformer())
   ```

### Change MQTT Settings
Update `config.json`:
```json
{
  "MQTT_HOST": "new.host.com",
  "MQTT_PUBLISH_TOPIC": "custom/topic",
  ...
}
```

### Add Custom Configuration
```python
config.load_from_dict({
    "CUSTOM_SETTING": "value"
})
custom_value = config.get("CUSTOM_SETTING")
```

## Troubleshooting

### MQTT Connection Failed
- Check `MQTT_HOST` and `MQTT_PORT` in config
- Verify MQTT broker is running
- Check `MQTT_USER` and `MQTT_PASS` credentials

### API Authentication Failed
- Verify `HOYMILES_USER` and `HOYMILES_PASSWORD`
- Check if account is active
- Verify `HOYMILES_PLANT_ID` is correct

### Sensors Not Showing in Home Assistant
- Check `MQTT_DISCOVERY_PREFIX` matches HA setting
- Verify data is being published: `mosquitto_sub -h localhost -t "home/solar/#"`
- Check Home Assistant MQTT integration is configured

### Data Not Updating
- Check `GET_DATA_INTERVAL` value (in seconds)
- Verify API connection with: `python test_api.py`
- Check application logs: set `LOG_LEVEL` to "DEBUG"

## Documentation Files

- **ARCHITECTURE.md** - Complete architecture overview
- **REFACTORING_GUIDE.md** - Detailed refactoring guide with examples
- **examples.py** - Practical code examples
- **test_refactoring.py** - Unit test templates

## Next Steps

1. Read **ARCHITECTURE.md** for overview
2. Check **examples.py** for usage patterns
3. Customize **application.py** for your needs
4. Deploy and enjoy automated solar data in Home Assistant!

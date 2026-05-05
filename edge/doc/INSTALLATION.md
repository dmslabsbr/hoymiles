# Installation & Deployment Guide

## 🚀 Quick Installation

### Prerequisites
- Python 3.8+
- pip or conda
- MQTT broker (mosquitto recommended)

### Option 1: Minimal Installation (Custom MQTT)

```bash
# Clone and setup
git clone https://github.com/dmslabsbr/hoymiles.git
cd hoymiles/edge

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python src/hoymiles/application.py
```

**Configuration:**
```bash
# Create .env file
cat > .env << EOF
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USER=your_user
MQTT_PASS=your_pass
HOYMILES_API_KEY=your_api_key
HOYMILES_DEVICE_ID=your_device_id
EOF
```

### Option 2: Production Installation (Library Version) ⭐ RECOMMENDED

```bash
# Clone and setup
git clone https://github.com/dmslabsbr/hoymiles.git
cd hoymiles/edge

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with library support
pip install paho-mqtt>=1.6.1 ha-mqtt-discoverable>=0.24.0 requests>=2.28.0

# Or from file
echo "ha-mqtt-discoverable>=0.24.0" >> requirements-prod.txt
pip install -r requirements-prod.txt

# Run with library version
python src/hoymiles/application.py
```

**Configuration:** Same as above

## 📝 Configuration

### Environment Variables

Create a `.env` file:

```bash
# MQTT Configuration
MQTT_HOST=192.168.1.100
MQTT_PORT=1883
MQTT_USER=home_assistant
MQTT_PASS=secure_password
MQTT_TLS=false

# MQTT Topic Configuration
MQTT_PUBLISH_TOPIC=home/solar
MQTT_DISCOVERY_PREFIX=homeassistant

# Hoymiles API Configuration
HOYMILES_API_KEY=your_api_key_from_cloud
HOYMILES_DEVICE_ID=your_device_id

# Node ID for MQTT
HA_SITE_NAME=Home
```

### Configuration File

Alternatively, use `config.json`:

```json
{
  "mqtt_host": "192.168.1.100",
  "mqtt_port": 1883,
  "mqtt_user": "home_assistant",
  "mqtt_pass": "secure_password",
  "mqtt_publish_topic": "home/solar",
  "mqtt_discovery_prefix": "homeassistant",
  "hoymiles_api_key": "your_api_key",
  "hoymiles_device_id": "your_device_id",
  "ha_site_name": "Home"
}
```

## 🐳 Docker Installation

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/hoymiles ./hoymiles

# Run application
CMD ["python", "-m", "hoymiles.application"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  hoymiles:
    build: .
    restart: unless-stopped
    environment:
      MQTT_HOST: mosquitto
      MQTT_PORT: 1883
      MQTT_USER: ${MQTT_USER}
      MQTT_PASS: ${MQTT_PASS}
      HOYMILES_API_KEY: ${HOYMILES_API_KEY}
      HOYMILES_DEVICE_ID: ${HOYMILES_DEVICE_ID}
    depends_on:
      - mosquitto
    networks:
      - solar

  mosquitto:
    image: eclipse-mosquitto:latest
    restart: unless-stopped
    ports:
      - "1883:1883"
    volumes:
      - mosquitto_data:/mosquitto/data
    networks:
      - solar

volumes:
  mosquitto_data:

networks:
  solar:
```

## 🔧 Systemd Service

Create `/etc/systemd/system/hoymiles.service`:

```ini
[Unit]
Description=Hoymiles Solar Gateway
After=network.target mosquitto.service

[Service]
Type=simple
User=hoymiles
WorkingDirectory=/home/hoymiles/hoymiles/edge
Environment="PATH=/home/hoymiles/hoymiles/edge/venv/bin"
ExecStart=/home/hoymiles/hoymiles/edge/venv/bin/python src/hoymiles/application.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable hoymiles
sudo systemctl start hoymiles
sudo systemctl status hoymiles
```

View logs:

```bash
sudo journalctl -u hoymiles -f
```

## 🏠 Home Assistant Integration

### 1. Enable MQTT Integration

Go to Settings → Devices & Services → Create Automation → MQTT

Configure:
- Broker: Your MQTT broker IP
- Port: 1883
- Username: your_user
- Password: your_pass

### 2. Discovery Automatic

Once the Hoymiles application publishes, sensors appear automatically in Home Assistant.

### 3. Verify in HA

- Settings → Devices & Services → MQTT
- Search for "Hoymiles" devices
- Sensors should appear under "Climate", "Energy", etc.

## 🧪 Testing

### Test Configuration

```bash
source venv/bin/activate
python -c "
from config_manager import ConfigManager
config = ConfigManager()
config.load_from_env()
print('Config loaded:', config.get_all())
"
```

### Test MQTT Connection

```bash
python -c "
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect('192.168.1.100', 1883, 60)
client.loop_start()
import time
time.sleep(2)
print('Connected!' if client.is_connected() else 'Failed!')
client.disconnect()
"
```

### Test Application

```bash
python src/hoymiles/application.py
```

Watch logs (Ctrl+C to stop):

```bash
tail -f logs/hoymiles.log
```

## 📊 Monitoring

### Log Files

```
logs/
  hoymiles.log      - Main application log
  mqtt.log          - MQTT broker logs
```

### MQTT Monitor

Subscribe to all topics:

```bash
mosquitto_sub -h localhost -u user -P pass -v -t "home/solar/#"
```

### Health Check

```bash
curl http://localhost:8080/health  # If enabled
```

## 🐛 Troubleshooting

### MQTT Connection Issues

```bash
# Check MQTT broker is running
mosquitto_status

# Check firewall
sudo ufw allow 1883

# Test connection
mosquitto_pub -h localhost -u user -P pass -t test -m "hello"
mosquitto_sub -h localhost -u user -P pass -t test
```

### API Connection Issues

```bash
# Test Hoymiles API
python -c "
from src.hoymiles.cloud_api import CloudApi
api = CloudApi('API_KEY', 'DEVICE_ID')
print(api.fetch_data())
"
```

### No Sensors in Home Assistant

1. Check MQTT connected: `Settings → Devices & Services → MQTT`
2. Check discovery messages: `mosquitto_sub -h localhost -t "homeassistant/#"`
3. Restart HA: `Settings → System → Restart`

## 📈 Upgrading

### From Old Code

1. Backup old code
2. Update config keys (see MIGRATION.md)
3. Install new version
4. Update systemd service
5. Restart service

```bash
sudo systemctl restart hoymiles
```

## 🔐 Security

### Recommendations

1. **Use strong MQTT passwords**
2. **Enable TLS**: `MQTT_TLS=true`
3. **Limit firewall**: Only allow local network
4. **Use API tokens**: Never hardcode API keys
5. **Enable HA authentication**: Always use passwords

### TLS Setup

```bash
# Generate self-signed cert
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout mosquitto.key -out mosquitto.crt

# Copy to mosquitto config
sudo cp mosquitto.crt mosquitto.key /etc/mosquitto/certs/

# Update configuration
MQTT_TLS=true
MQTT_CERT=/path/to/mosquitto.crt
```

## 📦 Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Configuration file created
- [ ] MQTT broker running and accessible
- [ ] Hoymiles API key and device ID verified
- [ ] Application started successfully
- [ ] MQTT topics publishing
- [ ] Home Assistant discovering sensors
- [ ] Systemd service configured (optional)
- [ ] Logs monitored
- [ ] Backups configured

## 📞 Support

### Resources
- [GitHub Issues](https://github.com/dmslabsbr/hoymiles/issues)
- [Documentation](REFACTORING_GUIDE.md)
- [Examples](src/hoymiles/examples.py)

### Getting Help
1. Check logs: `journalctl -u hoymiles -f`
2. Enable debug: `LOG_LEVEL=DEBUG`
3. Open issue with logs and config (no secrets!)

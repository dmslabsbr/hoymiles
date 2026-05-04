#!/usr/bin/with-contenv bashio
set -euo pipefail

bashio::log.green "Starting Hoymiles Edge add-on container..."

# Required Hoymiles credentials from add-on options.
export HOYMILES_USER="$(bashio::config 'HOYMILES_USER')"
export HOYMILES_PASSWORD="$(bashio::config 'HOYMILES_PASSWORD')"
export HOYMILES_PLANT_ID="$(bashio::config 'HOYMILES_PLANT_ID')"
export USE_ESTAR="$(bashio::config 'USE_ESTAR')"
export EXPERIMENTAL_CUSTOM_API_URLS="$(bashio::config 'EXPERIMENTAL_CUSTOM_API_URLS')"
export API_GATEWAY_BASE_URL="$(bashio::config 'API_GATEWAY_BASE_URL')"
export API_VERSIONED_BASE_URL="$(bashio::config 'API_VERSIONED_BASE_URL')"
export API_COOKIE_DOMAIN="$(bashio::config 'API_COOKIE_DOMAIN')"
export DEBUG_FORCE_API_VERSION="$(bashio::config 'DEBUG_FORCE_API_VERSION')"
export DEBUG_API_VERSION="$(bashio::config 'DEBUG_API_VERSION')"

# Edge app settings.
export LOG_LEVEL="$(bashio::config 'LOG_LEVEL')"
export DEVELOPERS_MODE="$(bashio::config 'DEVELOPERS_MODE')"
export MQTT_DISCOVERY_PREFIX="$(bashio::config 'MQTT_DISCOVERY_PREFIX')"
export MQTT_NODE_ID="$(bashio::config 'MQTT_NODE_ID')"
export HA_EXPIRE_TIME="$(bashio::config 'HA_EXPIRE_TIME')"
export GET_DATA_INTERVAL="$(bashio::config 'GET_DATA_INTERVAL')"
export HASS_INTERVAL="$(bashio::config 'HASS_INTERVAL')"
export AUTO_UPDATE_TOKEN="$(bashio::config 'Auto_update_token')"

# MQTT credentials: internal broker by default, optional external override.
if bashio::config.true 'External_MQTT_Server'; then
    export MQTT_HOST="$(bashio::config 'MQTT_Host')"
    export MQTT_USER="$(bashio::config 'MQTT_User')"
    export MQTT_PASS="$(bashio::config 'MQTT_Pass')"
else
    export MQTT_HOST="$(bashio::services mqtt 'host')"
    export MQTT_USER="$(bashio::services mqtt 'username')"
    export MQTT_PASS="$(bashio::services mqtt 'password')"
fi

export MQTT_TLS="$(bashio::config 'MQTT_TLS')"
export MQTT_TLS_PORT="$(bashio::config 'MQTT_TLS_PORT')"

# Ensure both package-style and local imports resolve for current module layout.
export PYTHONPATH="/app/src:/app/src/hoymiles:${PYTHONPATH:-}"

cd /app/src/hoymiles
exec python3 application.py

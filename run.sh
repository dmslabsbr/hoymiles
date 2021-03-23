#!/usr/bin/with-contenv bashio
set +u

CONFIG_PATH=/data/options.json
SYSTEM_USER=/data/system_user.json

bashio::log.red "Exporting config data"

export HOYMILES_USER=$(jq --raw-output '.HOYMILES_USER' $CONFIG_PATH)
export HOYMILES_PASSWORD=$(jq --raw-output '.HOYMILES_PASSWORD' $CONFIG_PATH)
export HOYMILES_PLANT_ID=$(jq --raw-output '.HOYMILES_PLANT_ID' $CONFIG_PATH)
export MQTT_HOST=$(jq --raw-output '.MQTT_HOST' $CONFIG_PATH)
export MQTT_USER=$(jq --raw-output '.MQTT_USER' $CONFIG_PATH)
export MQTT_PASSWORD=$(jq --raw-output '.MQTT_PASSWORD' $CONFIG_PATH)
export DEVELOPERS_MODE=$(jq --raw-output '.DEVELOPERS_MODE' $CONFIG_PATH)

bashio::log.blue "PATH: "
pwd

if [ -e "secrets.ini" ]; then
    bashio::log.info "secrets.ini exists!"
fi

if [ -e "/data/secrets.ini" ]; then
    bashio::log.info "/data/secrets.ini exists!"
else
    bashio::log.info "/data/secrets.ini not exists!"
    if [ -e "/secrets.ini" ]; then
        bashio::log.info "Copying..."
        cp /secrets.ini /data 
    fi    
fi

bashio::log.blue "dmslabs - Home Assistant HoyMiles Solar Data Gateway Add-on"
python3 ../hoymiles.py
echo "Run Webserver"
python3 -m http.server 8000
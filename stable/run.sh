#!/usr/bin/with-contenv bashio
set +u

bashio::log.green "Starting add-on container..."
date

CONFIG_PATH=/data/options.json
SYSTEM_USER=/data/system_user.json

mkdir -p /data/templates
cp /*.html /data/templates

ls -la /data/templates

mkdir -p /data/jsons
cp /*.json /data/jsons
cp /micro_* /data/jsons

ls -la /data/jsons

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

export HASS_USERNAME=$(bashio::config 'username')
bashio::log.info "${HASS_USERNAME}"
export HASS_TIMEZONE=$(bashio::info 'timezone')
bashio::log.info "${HASS_TIMEZONE}"

export HASS_TIMEZONE_2=$(bashio::info "timezone")
bashio::log.info "${HASS_TIMEZONE_2}"

bashio::log.blue "dmslabs - Home Assistant HoyMiles Solar Data Gateway Add-on"

python3 ../hoymiles.py

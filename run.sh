#!/usr/bin/with-contenv bashio
set +u

CONFIG_PATH=/data/options.json
SYSTEM_USER=/data/system_user.json

bashio::log.red "Exporting config data"

export ID=$(jq --raw-output '.ID' $CONFIG_PATH)
export USER=$(jq --raw-output '.USER' $CONFIG_PATH)
export PASS=$(jq --raw-output '.PASS' $CONFIG_PATH)


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

bashio::log.blue "Home Assistant Hoymiles Solar Painel Add-on - dmslabs"
python3 ../hoymiles.py
echo "Run Webserver"
python3 -m http.server 8000
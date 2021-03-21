<img src="https://github.com/dmslabsbr/hoymiles/raw/logo.png" alt="" width="200" />


# HoyMiles Solar Data Gateway Add-on
Application to read Hoymiles Gateway Solar Data

I developed this program to integrade my solar system data to the [Home Assistant](https://www.home-assistant.io/) Application through an add-on.

But you can use the application without using the Home Assistant. You just need a machine that runs Python3.


# Instructions

<img align="center" src="https://github.com/dmslabsbr/smsUps/raw/master/hass.io.png" alt="" width="30" /> [Home Assistant add-on instructions](DOCS.md)


Before run you need to install:
   https://github.com/eclipse/paho.mqtt.python  ***and***
   https://github.com/psf/requests


```bash
git clone https://github.com/dmslabsbr/hoymiles.git
cd hoymiles
python3 -m venv ./hoymiles/
source ./bin/activate
pip3 install paho-mqtt
pip3 install requests
```

My solar panels communicate with the internet using a DTU-W100 gateway.

<img src="https://github.com/dmslabsbr/hoymiles/raw/icon.png" alt="" width="200" />

But it will probably work with any device that uses the [global.hoymiles.com](https://global.hoymiles.com/) Website


## PS:
I invite everyone to help in the this tool development.
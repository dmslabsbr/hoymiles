# <img align="center" src="https://github.com/dmslabsbr/smsUps/raw/master/img/hass.io.png" alt="" width="60" />  HoyMiles Solar Data Gateway Add-on instructions. 

## 1 - Add a new repository

#### a) Inside *supervisor* tab, choice *Add-on store*.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/hass1.png" alt="Hass.io screen Add a new repository." width="500" /> 

#### b) Add the **URL** (https://github.com/dmslabsbr/hoymiles) of the repository and then press "**Add**". 

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/hass2.png" alt="Hass.io screen Add a new repository." width="500" /> 

#### c) A new card for the repository will appear.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/hass3.png" alt="Hass.io screen Add a new repository." width="400" /> 

#### d) Click on the repository and proceed with add-on installation.

<img src="https://github.com/dmslabsbr/smsUps/raw/master/img/hass4.png" alt="Hass.io screen Add a new repository." width="200" /> 

#### e) Before the 1st use you must configure the add-on, in the Configuration tab. Where:


- In HOYMILES_USER, HOYMILES_PASSWORD and HOYMILES_PLANT_ID you need to enter your S-Miles Cloud login data.

- In MQTT_HOST, MQTT_USER and MQTT_PASS fields you need to enter your MQTT server access data.


## Example:

<img src="https://github.com/dmslabsbr/hoymiles/raw/master/img/Hass2.png" alt="Hass.io screen Add a new repository." width="200" /> 

<img src="https://github.com/dmslabsbr/hoymiles/raw/master/img/Hass3.png" alt="Hass.io screen Add a new repository." width="200" /> 

You can now use your Hoymiles data in your Home Assistant.

You **must have** an *MQTT server*.

Mosquito MQTT Server Add-on Install Instructions: https://github.com/home-assistant/addons/blob/master/mosquitto/DOCS.md